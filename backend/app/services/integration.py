import hashlib
import io
import json
import logging
import os
import uuid
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.integration import ExternalIntegration
from app.schemas.integration import (
    ExternalIntegrationCreate,
    ExternalIntegrationUpdate,
    GoogleDriveFile,
)
from app.services.base import BaseService
from app.services.document_dynamodb_service import document_service


# Helper function to ensure datetime objects have timezone information
def ensure_timezone_aware(dt):
    """Convert naive datetime to timezone-aware datetime with UTC timezone"""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            # If parsing fails, return as is (or could raise/return None)
            # But for now, let's assume it might be handled downstream or raise AttributeError later
            return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrationService(
    BaseService[
        ExternalIntegration, ExternalIntegrationCreate, ExternalIntegrationUpdate
    ]
):
    """Service for managing external integrations"""

    async def get_by_user_and_provider(
        self, db: AsyncSession, user_id: str, provider: str
    ) -> ExternalIntegration | None:
        """Get integration by user ID and provider"""
        logger.info(f"Looking for integration: user_id={user_id}, provider={provider}")
        integrations = await db.filter(
            ExternalIntegration, user_id=user_id, provider=provider
        )
        integration = integrations[0] if integrations else None

        logger.info(f"Integration found: {integration is not None}")
        if integration:
            logger.info(
                f"Integration details: id={integration.id}, provider_email={integration.provider_email}"
            )
        return integration

    async def delete_by_user_and_provider(
        self, db: AsyncSession, user_id: str, provider: str
    ) -> None:
        """Delete integration by user ID and provider"""
        integrations = await db.filter(
            ExternalIntegration, user_id=user_id, provider=provider
        )
        for integration in integrations:
            await db.delete(integration)
        await db.commit()


class GoogleDriveService:
    """Service for Google Drive integration"""

    @staticmethod
    def get_authorization_url(state: str) -> str:
        """Generate the Google OAuth2 authorization URL"""
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(settings.GOOGLE_AUTH_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,  # Used to maintain state between request and callback
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}?{query_string}"

    @staticmethod
    async def exchange_code_for_token(code: str) -> dict[str, Any]:
        """Exchange authorization code for access token"""
        token_url = "https://oauth2.googleapis.com/token"

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"Failed to exchange code: {error_text}")

                token_data = await response.json()
                return token_data

    @staticmethod
    async def get_user_info(access_token: str) -> dict[str, Any]:
        """Get user info from Google API"""
        url = "https://www.googleapis.com/userinfo/v2/me"

        headers = {"Authorization": f"Bearer {access_token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"Failed to get user info: {error_text}")

                user_data = await response.json()
                return user_data

    @staticmethod
    def _credentials_from_db_model(integration: ExternalIntegration) -> Credentials:
        """Create Google credentials object from database model"""
        return Credentials(
            token=integration.access_token,
            refresh_token=integration.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=settings.GOOGLE_AUTH_SCOPES,
        )

    @staticmethod
    async def _refresh_token_if_needed(
        db: AsyncSession, integration: ExternalIntegration
    ) -> ExternalIntegration:
        """Refresh token if expired"""
        now = datetime.now(UTC)

        # If token expiry is not set
        if not integration.token_expiry:
            needs_refresh = True
        else:
            # Ensure token_expiry is timezone-aware for comparison
            token_expiry = ensure_timezone_aware(integration.token_expiry)
            needs_refresh = token_expiry <= now
            print(
                f"[DEBUG] Token comparison: token_expiry={token_expiry}, now={now}, needs_refresh={needs_refresh}"
            )

        # If token needs refresh
        if needs_refresh:
            if not integration.refresh_token:
                raise ValueError(
                    "Refresh token not available. User needs to re-authenticate."
                )

            print(
                f"[DEBUG] Refreshing token: current token_expiry={integration.token_expiry}, now={now}"
            )

            token_url = "https://oauth2.googleapis.com/token"

            params = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": integration.refresh_token,
                "grant_type": "refresh_token",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"Failed to refresh token: {error_text}")

                    token_data = await response.json()

                    # Update the integration record
                    integration.access_token = token_data["access_token"]
                    # Calculate expiry time
                    expires_in = token_data.get(
                        "expires_in", 3600
                    )  # Default to 1 hour if not provided
                    integration.token_expiry = now + timedelta(seconds=expires_in)

                    db.add(integration)
                    await db.commit()
                    await db.refresh(integration)

        return integration

    async def list_files(
        self,
        db: AsyncSession,
        integration: ExternalIntegration,
        folder_id: str | None = None,
        page_token: str | None = None,
        page_size: int = 100,
    ) -> tuple[list[GoogleDriveFile], str | None]:
        """List files from Google Drive"""
        # Refresh token if needed
        integration = await self._refresh_token_if_needed(db, integration)

        # Create credentials and build service
        credentials = self._credentials_from_db_model(integration)
        drive_service = build("drive", "v3", credentials=credentials)

        # Prepare query
        query = "trashed = false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        else:
            # For root level, only show files that are directly in the root
            query += " and 'root' in parents"

        # Execute request
        fields = "nextPageToken, files(id, name, mimeType, size, webViewLink, thumbnailLink, modifiedTime, createdTime, parents)"

        response = (
            drive_service.files()
            .list(
                q=query,
                spaces="drive",
                fields=fields,
                pageToken=page_token,
                pageSize=page_size,
                orderBy="name",
            )
            .execute()
        )

        # Process results
        files = []
        for item in response.get("files", []):
            is_folder = item["mimeType"] == "application/vnd.google-apps.folder"

            try:
                modified_time = None
                if item.get("modifiedTime"):
                    modified_time = ensure_timezone_aware(
                        datetime.fromisoformat(
                            item.get("modifiedTime").replace("Z", "+00:00")
                        )
                    )

                created_time = None
                if item.get("createdTime"):
                    created_time = ensure_timezone_aware(
                        datetime.fromisoformat(
                            item.get("createdTime").replace("Z", "+00:00")
                        )
                    )

                files.append(
                    GoogleDriveFile(
                        id=item["id"],
                        name=item["name"],
                        mime_type=item["mimeType"],
                        size=int(item.get("size", 0)) if item.get("size") else None,
                        web_view_link=item.get("webViewLink"),
                        thumbnail_link=item.get("thumbnailLink"),
                        modified_time=modified_time,
                        created_time=created_time,
                        parents=item.get("parents", []),
                        is_folder=is_folder,
                    )
                )
            except Exception as e:
                print(f"[ERROR] Error processing file {item.get('name')}: {str(e)}")
                # Continue with other files

        next_page_token = response.get("nextPageToken")

        # Sort the files to show folders first, then regular files
        files.sort(key=lambda f: (0 if f.is_folder else 1, f.name.lower()))

        return files, next_page_token

    async def get_file_metadata(
        self, db: AsyncSession, integration: ExternalIntegration, file_id: str
    ) -> GoogleDriveFile:
        """Get metadata for a specific file"""
        # Refresh token if needed
        integration = await self._refresh_token_if_needed(db, integration)

        # Create credentials and build service
        credentials = self._credentials_from_db_model(integration)
        drive_service = build("drive", "v3", credentials=credentials)

        # Execute request
        fields = "id, name, mimeType, size, webViewLink, webContentLink, thumbnailLink, md5Checksum, modifiedTime, createdTime, parents, exportLinks"

        file = drive_service.files().get(fileId=file_id, fields=fields).execute()

        is_folder = file["mimeType"] == "application/vnd.google-apps.folder"

        modified_time = None
        if file.get("modifiedTime"):
            modified_time = ensure_timezone_aware(
                datetime.fromisoformat(file.get("modifiedTime").replace("Z", "+00:00"))
            )

        created_time = None
        if file.get("createdTime"):
            created_time = ensure_timezone_aware(
                datetime.fromisoformat(file.get("createdTime").replace("Z", "+00:00"))
            )

        return GoogleDriveFile(
            id=file["id"],
            name=file["name"],
            mime_type=file["mimeType"],
            size=int(file.get("size", 0)) if file.get("size") else None,
            web_view_link=file.get("webViewLink"),
            web_content_link=file.get("webContentLink"),
            thumbnail_link=file.get("thumbnailLink"),
            md5_checksum=file.get("md5Checksum"),
            modified_time=modified_time,
            created_time=created_time,
            parents=file.get("parents", []),
            is_folder=is_folder,
            export_links=file.get("exportLinks"),
        )

    async def download_file(
        self, db: AsyncSession, integration: ExternalIntegration, file_id: str
    ) -> tuple[bytes, str, str]:
        """Download a file from Google Drive"""
        # Refresh token if needed
        integration = await self._refresh_token_if_needed(db, integration)

        # Get file metadata first
        file_metadata = await self.get_file_metadata(db, integration, file_id)

        # Create credentials and build service
        credentials = self._credentials_from_db_model(integration)
        drive_service = build("drive", "v3", credentials=credentials)

        # For Google Docs, Sheets, etc., export in appropriate format
        if file_metadata.mime_type.startswith("application/vnd.google-apps"):
            if file_metadata.mime_type == "application/vnd.google-apps.document":
                export_mime_type = "application/pdf"
                file_extension = ".pdf"
            elif file_metadata.mime_type == "application/vnd.google-apps.spreadsheet":
                export_mime_type = (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                file_extension = ".xlsx"
            elif file_metadata.mime_type == "application/vnd.google-apps.presentation":
                export_mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                file_extension = ".pptx"
            elif file_metadata.mime_type == "application/vnd.google-apps.drawing":
                export_mime_type = "image/png"
                file_extension = ".png"
            else:
                # Default to PDF for other Google Workspace documents
                export_mime_type = "application/pdf"
                file_extension = ".pdf"

            # Ensure filename ends with appropriate extension
            filename = file_metadata.name
            if not filename.endswith(file_extension):
                filename = f"{filename}{file_extension}"

            mime_type = export_mime_type

            # Try to use exportLinks if available (more reliable)
            if (
                file_metadata.export_links
                and export_mime_type in file_metadata.export_links
            ):
                download_url = file_metadata.export_links[export_mime_type]
                logger.info(f"Downloading via exportLink: {download_url}")

                headers = {"Authorization": f"Bearer {integration.access_token}"}
                async with aiohttp.ClientSession() as session:
                    async with session.get(download_url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            raise ValueError(
                                f"Failed to download file via export link: {resp.status} - {error_text}"
                            )
                        file_content = await resp.read()

                logger.info(f"Downloaded file {filename} ({len(file_content)} bytes)")

                # Validate content
                if len(file_content) == 0:
                    raise ValueError("Downloaded content is empty")

                # Check for HTML error page
                if file_content[:100].strip().lower().startswith(
                    b"<!doctype html"
                ) or file_content[:100].strip().lower().startswith(b"<html"):
                    error_snippet = file_content[:200].decode("utf-8", errors="ignore")
                    raise ValueError(
                        f"Downloaded content appears to be HTML (likely an error page): {error_snippet}"
                    )

                # Check for ZIP header if it's an XLSX file
                if filename.endswith(".xlsx") and not file_content.startswith(
                    b"PK\x03\x04"
                ):
                    # Log warning but don't fail, as it might be some other format or encrypted
                    logger.warning(
                        f"File {filename} does not start with ZIP header (PK\\x03\\x04). First bytes: {file_content[:10].hex()}"
                    )

                return file_content, mime_type, filename

            # Fallback to export_media if no link
            request = drive_service.files().export_media(
                fileId=file_id, mimeType=export_mime_type
            )
        else:
            # For regular files, download directly
            mime_type = file_metadata.mime_type
            filename = file_metadata.name

            # Use get_media with acknowledgeAbuse=True to handle potential virus scan warnings
            request = drive_service.files().get_media(
                fileId=file_id, acknowledgeAbuse=True
            )

        # Download the file
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        file_content = fh.getvalue()
        logger.info(f"Downloaded file {filename} ({len(file_content)} bytes)")

        # Validate content
        if len(file_content) == 0:
            raise ValueError("Downloaded content is empty")

        # Check for HTML error page
        if file_content[:100].strip().lower().startswith(
            b"<!doctype html"
        ) or file_content[:100].strip().lower().startswith(b"<html"):
            error_snippet = file_content[:200].decode("utf-8", errors="ignore")
            raise ValueError(
                f"Downloaded content appears to be HTML (likely an error page): {error_snippet}"
            )

        # Verify MD5 checksum if available (only for regular files, not exports)
        if file_metadata.md5_checksum:
            md5_hash = hashlib.md5(file_content).hexdigest()
            if md5_hash != file_metadata.md5_checksum:
                raise ValueError(
                    f"MD5 checksum mismatch for {filename}. Expected {file_metadata.md5_checksum}, got {md5_hash}"
                )
            logger.info(f"MD5 checksum verified for {filename}")

        return file_content, mime_type, filename

    async def import_file(
        self,
        db: AsyncSession,
        user_id: str,
        integration: ExternalIntegration,
        file_id: str,
        folder_id: str | None = None,
    ) -> str:
        """Import a file from Google Drive into the data room"""
        # Download file content
        file_content, mime_type, file_name = await self.download_file(
            db, integration, file_id
        )

        # Save file using document service (which uses storage provider)
        unique_filename = f"{uuid.uuid4()}-{file_name}"
        file_path = await document_service.save_content(
            file_content, unique_filename, mime_type
        )

        # Get file size
        file_size = len(file_content)

        # Create document using document service
        document_id = await document_service.create_document(
            user_id=user_id,
            name=file_name,
            description=f"Imported from Google Drive - {datetime.now()}",
            file_path=file_path,
            file_type=mime_type,
            file_size=file_size,
            folder_id=folder_id,
        )

        return document_id

    async def import_folder(
        self,
        db: AsyncSession,
        user_id: str,
        integration: ExternalIntegration,
        folder_id: str,
        parent_folder_id: str | None = None,
        max_depth: int = 5,
    ) -> dict[str, Any]:
        """Import a folder and its contents recursively from Google Drive"""
        if max_depth <= 0:
            return {
                "status": "max_depth_reached",
                "folder_id": folder_id,
                "imported_files": 0,
                "imported_folders": 0,
                "skipped_items": 1,
            }

        # Get folder metadata
        folder_metadata = await self.get_file_metadata(db, integration, folder_id)
        if not folder_metadata.is_folder:
            raise ValueError(f"The item with ID {folder_id} is not a folder")

        from app.services.folder import folder_service

        # Create a corresponding folder in the data room
        local_folder = await folder_service.create(
            db=db,
            user_id=user_id,
            name=folder_metadata.name,
            parent_id=parent_folder_id,
        )

        # List all items in the Google Drive folder
        items, _ = await self.list_files(db, integration, folder_id)

        imported_files = 0
        imported_folders = 0
        skipped_items = 0

        # Process each item
        for item in items:
            try:
                if item.is_folder:
                    # Recursively import folders
                    result = await self.import_folder(
                        db=db,
                        user_id=user_id,
                        integration=integration,
                        folder_id=item.id,
                        parent_folder_id=local_folder.id,
                        max_depth=max_depth - 1,
                    )
                    imported_folders += 1 + result["imported_folders"]
                    imported_files += result["imported_files"]
                    skipped_items += result["skipped_items"]
                else:
                    # Import file
                    await self.import_file(
                        db=db,
                        user_id=user_id,
                        integration=integration,
                        file_id=item.id,
                        folder_id=local_folder.id,
                    )
                    imported_files += 1
            except Exception as e:
                # Log error but continue importing other items
                print(f"Error importing {item.name}: {str(e)}")
                skipped_items += 1

        return {
            "status": "success",
            "folder_id": local_folder.id,
            "imported_files": imported_files,
            "imported_folders": imported_folders,
            "skipped_items": skipped_items,
        }

    async def get_storage_usage(
        self, db: AsyncSession, integration: ExternalIntegration
    ) -> dict[str, Any]:
        """Get Google Drive storage usage information"""
        # Refresh token if needed
        integration = await self._refresh_token_if_needed(db, integration)

        # Create credentials and build service
        credentials = self._credentials_from_db_model(integration)
        drive_service = build("drive", "v3", credentials=credentials)

        # Get storage information about the user
        about = drive_service.about().get(fields="storageQuota").execute()

        storage_quota = about.get("storageQuota", {})

        limit = int(storage_quota.get("limit", 0)) if storage_quota.get("limit") else 0
        usage = int(storage_quota.get("usage", 0)) if storage_quota.get("usage") else 0
        usage_in_drive = (
            int(storage_quota.get("usageInDrive", 0))
            if storage_quota.get("usageInDrive")
            else 0
        )
        usage_in_trash = (
            int(storage_quota.get("usageInTrash", 0))
            if storage_quota.get("usageInTrash")
            else 0
        )

        # Calculate usage percentage
        usage_percent = (usage / limit * 100) if limit > 0 else 0

        return {
            "total_storage": limit,
            "used_storage": usage,
            "drive_storage": usage_in_drive,
            "trash_storage": usage_in_trash,
            "usage_percent": usage_percent,
        }

    async def search_files(
        self,
        db: AsyncSession,
        integration: ExternalIntegration,
        query: str,
        page_token: str | None = None,
        page_size: int = 100,
    ) -> tuple[list[GoogleDriveFile], str | None]:
        """Search for files in Google Drive"""
        # Refresh token if needed
        integration = await self._refresh_token_if_needed(db, integration)

        # Create credentials and build service
        credentials = self._credentials_from_db_model(integration)
        drive_service = build("drive", "v3", credentials=credentials)

        # Build search query
        search_query = f"fullText contains '{query}' and trashed = false"

        # Execute request
        fields = "nextPageToken, files(id, name, mimeType, size, webViewLink, thumbnailLink, modifiedTime, createdTime, parents)"

        response = (
            drive_service.files()
            .list(
                q=search_query,
                spaces="drive",
                fields=fields,
                pageToken=page_token,
                pageSize=page_size,
                # Removed invalid 'orderBy="relevance"' parameter
            )
            .execute()
        )

        # Process results
        files = []
        for item in response.get("files", []):
            is_folder = item["mimeType"] == "application/vnd.google-apps.folder"

            try:
                modified_time = None
                if item.get("modifiedTime"):
                    modified_time = ensure_timezone_aware(
                        datetime.fromisoformat(
                            item.get("modifiedTime").replace("Z", "+00:00")
                        )
                    )

                created_time = None
                if item.get("createdTime"):
                    created_time = ensure_timezone_aware(
                        datetime.fromisoformat(
                            item.get("createdTime").replace("Z", "+00:00")
                        )
                    )

                files.append(
                    GoogleDriveFile(
                        id=item["id"],
                        name=item["name"],
                        mime_type=item["mimeType"],
                        size=int(item.get("size", 0)) if item.get("size") else None,
                        web_view_link=item.get("webViewLink"),
                        thumbnail_link=item.get("thumbnailLink"),
                        modified_time=modified_time,
                        created_time=created_time,
                        parents=item.get("parents", []),
                        is_folder=is_folder,
                    )
                )
            except Exception as e:
                print(
                    f"[ERROR] Error processing search result {item.get('name')}: {str(e)}"
                )
                # Continue with other files

        next_page_token = response.get("nextPageToken")

        return files, next_page_token


integration_service = IntegrationService(ExternalIntegration)
google_drive_service = GoogleDriveService()
