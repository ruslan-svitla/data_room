"""
Document service using DynamoDB for data storage.
This replaces the SQLAlchemy-based document service.
"""

import logging
import mimetypes
import os
from datetime import datetime
from typing import List, Optional

from fastapi import UploadFile

from app.core.config import settings
from app.core.security import generate_uuid
from app.models.document import Document, DocumentShare, DocumentVersion
from app.schemas.document import (
    DocumentCreate,
    DocumentShareCreate,
    DocumentShareUpdate,
    DocumentUpdate,
)
from app.services.dynamodb_service import DynamoDBService

# Configure logger
logger = logging.getLogger(__name__)


class FileSystemStorage:
    """Local filesystem storage adapter.
    Used for local development and testing.
    """

    def __init__(self, upload_folder: str = None):
        """Initialize with upload folder path."""
        self.upload_folder = upload_folder or settings.UPLOAD_FOLDER
        # Ensure upload folder exists
        os.makedirs(self.upload_folder, exist_ok=True)

    async def save_file(self, file: UploadFile, filename: str | None = None) -> str:
        """Save file to local filesystem."""
        if not filename:
            filename = file.filename

        file_path = os.path.join(self.upload_folder, filename)

        # Save file to disk - using async file operations
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        return file_path

    async def delete_file(self, filename: str) -> bool:
        """Delete file from local filesystem."""
        file_path = os.path.join(self.upload_folder, filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File not found during deletion: {file_path}")
                return True  # Return True if file doesn't exist (already deleted)
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False


class DocumentDynamoDBService(
    DynamoDBService[Document, DocumentCreate, DocumentUpdate]
):
    """Service for document operations using DynamoDB"""

    def __init__(self):
        super().__init__(Document, settings.DYNAMODB_DOCUMENTS_TABLE)
        # Get the appropriate storage provider
        from app.utils.storage_factory import get_storage_provider

        self.storage = get_storage_provider()

        # Initialize services for related tables
        self.document_version_service = DocumentVersionDynamoDBService()
        self.document_share_service = DocumentShareDynamoDBService()

    async def _delete_file_from_filesystem(self, file_path: str) -> bool:
        """Delete a file from the storage

        Args:
            file_path: Path to the file to delete

        Returns:
            bool: True if the file was deleted or didn't exist, False if an error occurred
        """
        try:
            # Extract filename from path
            filename = os.path.basename(file_path)
            return await self.storage.delete_file(filename)
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False

    def get_download_url(self, file_path: str) -> str | None:
        """Get a download URL for the file (e.g., presigned S3 URL)"""
        # Extract filename from path
        filename = os.path.basename(file_path)
        return self.storage.get_presigned_url(filename)

    async def get_multi_by_owner(
        self,
        owner_id: str,
        skip: int = 0,
        limit: int = 100,
        folder_id: str = None,
    ) -> list[Document]:
        """Get documents by owner with optional folder filter"""

        # Build filters
        filters = {
            "owner_id": owner_id,
            "is_deleted": "false",  # Boolean stored as string
        }

        if folder_id:
            filters["folder_id"] = folder_id

        # Use the GSI to efficiently query by owner
        return await self.get_by_index(
            index_name="OwnerIndex",
            key_name="owner_id",
            key_value=owner_id,
            range_key_name="is_deleted",
            range_key_value="false",
            skip=skip,
            limit=limit,
        )

    async def get_shared_with_user(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> list[Document]:
        """Get documents shared with a user"""
        # First get all document shares for this user
        shares = await self.document_share_service.get_by_index(
            index_name="UserSharesIndex",
            key_name="user_id",
            key_value=user_id,
            skip=skip,
            limit=limit,
        )

        if not shares:
            return []

        # Get all the documents that are shared and not deleted
        documents = []
        for share in shares:
            doc = await self.get(share.document_id)
            if doc and not doc.is_deleted:  # doc.is_deleted will be a boolean here
                documents.append(doc)

        return documents

    async def save_content(
        self, content: bytes, filename: str, content_type: str = None
    ) -> str:
        """Save content using the storage provider"""
        return await self.storage.save_content(content, filename, content_type)

    async def create_document(
        self,
        *,
        user_id: str,
        name: str,
        description: str,
        file_path: str,
        file_type: str,
        file_size: int,
        folder_id: str = None,
        is_public: bool = False,
    ) -> str:
        """Create a document from an existing file"""
        # Generate unique ID
        doc_id = generate_uuid()

        # Create document record
        document_data = {
            "id": doc_id,
            "name": name,
            "description": description,
            "folder_id": folder_id,
            "file_path": file_path,
            "file_type": file_type,
            "file_size": file_size,
            "owner_id": user_id,
            "is_public": is_public,
            "is_deleted": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        document = Document.from_dict(document_data)
        await self.create(document_data)

        # Create initial version
        version_data = {
            "id": generate_uuid(),
            "document_id": doc_id,
            "version_number": 1,
            "file_path": file_path,
            "file_size": file_size,
            "created_by": user_id,
            "created_at": datetime.now().isoformat(),
        }

        await self.document_version_service.create(version_data)

        return doc_id

    async def create_with_file(
        self,
        obj_in: DocumentCreate,
        file: UploadFile,
        file_content: bytes,
        file_size: int,
        owner_id: str,
    ) -> Document:
        """Create a document with an uploaded file"""
        # Generate unique ID and filename
        doc_id = generate_uuid()
        extension = os.path.splitext(file.filename)[1] if file.filename else ""
        file_path = os.path.join(settings.get_upload_path(), f"{doc_id}{extension}")

        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Detect file type
        file_type = (
            file.content_type
            or mimetypes.guess_type(file_path)[0]
            or "application/octet-stream"
        )

        # Create document record
        document_data = obj_in.model_dump()
        document_data.update(
            {
                "id": doc_id,
                "file_path": file_path,
                "file_type": file_type,
                "file_size": file_size,
                "owner_id": owner_id,
                "is_deleted": False,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
        )

        document = Document.from_dict(document_data)
        await self.create(document_data)

        # Create initial version
        version_data = {
            "document_id": doc_id,
            "version_number": 1,
            "file_path": file_path,
            "file_size": file_size,
            "created_by": owner_id,
        }

        await self.document_version_service.create(version_data)

        return document

    async def create_version(
        self,
        document_id: str,
        file: UploadFile,
        file_content: bytes,
        file_size: int,
        user_id: str,
    ) -> DocumentVersion:
        """Create a new version of a document"""
        # Get latest version number
        versions = await self.document_version_service.get_by_index(
            index_name="DocumentVersionsIndex",
            key_name="document_id",
            key_value=document_id,
            skip=0,
            limit=1,
        )

        version_number = (versions[0].version_number + 1) if versions else 1

        # Generate unique ID and filename
        version_id = generate_uuid()
        extension = os.path.splitext(file.filename)[1] if file.filename else ""
        file_path = os.path.join(
            settings.get_upload_path(), f"{document_id}_v{version_number}{extension}"
        )

        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Create version record
        version_data = {
            "id": version_id,
            "document_id": document_id,
            "version_number": version_number,
            "file_path": file_path,
            "file_size": file_size,
            "created_by": user_id,
            "created_at": datetime.now().isoformat(),
        }

        version = DocumentVersion.from_dict(version_data)
        await self.document_version_service.create(version_data)

        # Update document record with new file info
        document = await self.get(document_id)
        if document:
            document.file_path = file_path
            document.file_size = file_size
            document.updated_at = datetime.now()

            await self.update(document_id, document.to_dict())

        return version

    async def get_versions(self, document_id: str) -> list[DocumentVersion]:
        """Get all versions of a document"""
        return await self.document_version_service.get_by_index(
            index_name="DocumentVersionsIndex",
            key_name="document_id",
            key_value=document_id,
        )

    # Document sharing functions
    async def create_share(self, obj_in: DocumentShareCreate) -> DocumentShare:
        """Create a document share"""
        share_data = obj_in.model_dump()
        share_data["id"] = generate_uuid()

        # Add timestamps
        now = datetime.now().isoformat()
        share_data["created_at"] = now

        share = DocumentShare.from_dict(share_data)
        await self.document_share_service.create(share_data)
        return share

    async def get_share(
        self, document_id: str, user_id: str
    ) -> DocumentShare | None:
        """Get a document share by document and user"""
        # Since we don't have a composite key in our GSI, we need to fetch all shares
        # for the document and filter
        shares = await self.document_share_service.get_by_index(
            index_name="DocumentIndex", key_name="document_id", key_value=document_id
        )

        # Filter shares for the specific user
        for share in shares:
            if share.user_id == user_id:
                return share

        return None

    async def get_share_by_id(self, id: str) -> DocumentShare | None:
        """Get a document share by ID"""
        return await self.document_share_service.get(id)

    async def get_shares(self, document_id: str) -> list[DocumentShare]:
        """Get all shares for a document"""
        return await self.document_share_service.get_by_index(
            index_name="DocumentIndex", key_name="document_id", key_value=document_id
        )

    async def update_share(
        self, db_obj: DocumentShare, obj_in: DocumentShareUpdate
    ) -> DocumentShare:
        """Update a document share"""
        update_data = obj_in.model_dump(exclude_unset=True)
        share = await self.document_share_service.update(db_obj.id, update_data)
        return share

    async def remove_share(self, id: str) -> bool:
        """Remove a document share"""
        return await self.document_share_service.delete(id)

    async def remove_document_and_files(self, id: str) -> Document | None:
        """Remove a document and its physical files

        This method performs both soft delete in the database and physical deletion of files.

        Args:
            id: Document ID

        Returns:
            Document: The updated document object with is_deleted=True
        """
        # First get the document
        document = await self.get(id)
        if not document:
            return None

        # Get all versions to delete their files
        versions = await self.get_versions(id)

        # Delete all version files
        deleted_files = []
        for version in versions:
            if await self._delete_file_from_filesystem(version.file_path):
                deleted_files.append(version.file_path)

        # Also delete the current document file if it's not in versions
        if document.file_path not in deleted_files:
            await self._delete_file_from_filesystem(document.file_path)

        # Perform soft delete in database by updating is_deleted flag
        document.is_deleted = True
        document.updated_at = datetime.now()

        # Update the document
        await self.update(id, {"is_deleted": True})

        return document

    async def is_shared_with_user(self, document_id: str, user_id: str) -> bool:
        """Check if a document is shared with a user"""
        share = await self.get_share(document_id=document_id, user_id=user_id)
        return share is not None

    async def can_edit(self, document_id: str, user_id: str) -> bool:
        """Check if a user can edit a document"""
        share = await self.get_share(document_id=document_id, user_id=user_id)
        return share is not None and share.can_edit

    async def can_delete(self, document_id: str, user_id: str) -> bool:
        """Check if a user can delete a document"""
        share = await self.get_share(document_id=document_id, user_id=user_id)
        return share is not None and share.can_delete

    async def get_total_imported_documents_and_storage(
        self, owner_id: str
    ) -> tuple[int, int]:
        """
        Returns (count, total_storage_bytes) for all non-deleted documents owned by user.
        """
        docs = await self.get_multi_by_owner(owner_id=owner_id, skip=0, limit=1000)
        count = len(docs)
        total_storage = sum(doc.file_size for doc in docs if not doc.is_deleted)
        return count, total_storage


class DocumentVersionDynamoDBService(DynamoDBService[DocumentVersion, dict, dict]):
    """Service for document version operations using DynamoDB"""

    def __init__(self):
        super().__init__(DocumentVersion, settings.DYNAMODB_DOCUMENT_VERSIONS_TABLE)


class DocumentShareDynamoDBService(
    DynamoDBService[DocumentShare, DocumentShareCreate, DocumentShareUpdate]
):
    """Service for document share operations using DynamoDB"""

    def __init__(self):
        super().__init__(DocumentShare, settings.DYNAMODB_DOCUMENT_SHARES_TABLE)


# Create singleton instances
document_service = DocumentDynamoDBService()
document_version_service = DocumentVersionDynamoDBService()
document_share_service = DocumentShareDynamoDBService()
