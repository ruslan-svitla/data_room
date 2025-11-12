import json
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.integration import (
    ExternalIntegration,
    ExternalIntegrationCreate,
    GoogleDriveAuthState,
    GoogleDriveFile,
    GoogleDriveImportRequest,
    GoogleDriveLinkRequest,
)
from app.services.integration import google_drive_service, integration_service

router = APIRouter()


@router.post("/google/link", status_code=status.HTTP_200_OK)
async def start_google_drive_link(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: GoogleDriveLinkRequest = None,
) -> Dict[str, Any]:
    """
    Start the Google Drive linking process by generating an authorization URL
    """
    # Generate state parameter for CSRF protection and to store user ID
    state_data = GoogleDriveAuthState(user_id=current_user.id)
    state = json.dumps(state_data.model_dump())
    
    # Generate authorization URL
    auth_url = google_drive_service.get_authorization_url(state)
    
    return {"authorization_url": auth_url}


@router.get("/google/callback")
async def google_drive_callback(
    *,
    db: AsyncSession = Depends(get_db),
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    request: Request,
) -> Any:
    print(f"[DEBUG] Processing Google OAuthCallback - State: {state}")
    print(f"[DEBUG] Processing Google OAuthCallback - Code: {code}")
    """
    Handle the OAuth callback from Google
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error during Google authentication: {error}",
        )

    try:
        # Decode state parameter
        print(f"[DEBUG] Processing Google OAuthCallback - State: {state}")
        state_data = GoogleDriveAuthState(**json.loads(state))
        user_id = state_data.user_id
        print(f"[DEBUG] User ID from state: {user_id}")

        # Verify user exists in database
        from app.models.user import User
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalars().first()
        if not user:
            print(f"[ERROR] User with ID {user_id} not found in database")
            raise ValueError(f"User with ID {user_id} not found")
        print(f"[DEBUG] User found: {user.email}")

        # Exchange code for tokens
        print("[DEBUG] Exchanging code for token...")
        token_data = await google_drive_service.exchange_code_for_token(code)
        print(f"[DEBUG] Token exchange successful: {token_data.keys()}")

        # Verify we received the expected tokens
        if 'access_token' not in token_data:
            raise ValueError("No access token received from Google")

        # Get user info from Google
        print("[DEBUG] Fetching user info from Google...")
        user_info = await google_drive_service.get_user_info(token_data["access_token"])
        print(f"[DEBUG] Google user info retrieved: {user_info.get('email')}")

        # Check if integration already exists for this user
        print(f"[DEBUG] Checking for existing integration for user {user_id}...")
        existing_integration = await integration_service.get_by_user_and_provider(
            db, user_id, "google_drive"
        )
        print(f"[DEBUG] Existing integration found: {existing_integration is not None}")

        # Process token data
        token_expiry = None
        if "expires_in" in token_data:
            from datetime import datetime, timedelta, timezone
            token_expiry = datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])
            print(f"[DEBUG] Token will expire at: {token_expiry}")

        # Create or update the integration record
        try:
            if existing_integration:
                print(f"[DEBUG] Updating existing integration for {user_info.get('email')}")
                # Fix: Ensure token_expiry is a proper datetime object
                integration_update = {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token", existing_integration.refresh_token),
                    "token_expiry": token_expiry,  # This should be a proper datetime object
                    "provider_user_id": user_info.get("id"),
                    "provider_email": user_info.get("email"),
                }
                await integration_service.update(
                    db, db_obj=existing_integration, obj_in=integration_update
                )
                print(f"[DEBUG] Integration updated successfully")
            else:
                print(f"[DEBUG] Creating new integration for {user_info.get('email')}")
                # Fix: Use a dictionary directly instead of the Pydantic model to avoid any serialization issues
                integration_create = {
                    "provider": "google_drive",
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "token_expiry": token_expiry,  # This should be a proper datetime object
                    "provider_user_id": user_info.get("id"),
                    "provider_email": user_info.get("email"),
                }
                try:
                    print(f"[DEBUG] Token expiry type before create: {type(token_expiry)}")
                    new_integration = await integration_service.create_with_id(
                        db, obj_in=integration_create, id=str(uuid.uuid4()), user_id=user_id
                    )
                except Exception as create_error:
                    print(f"[ERROR] Failed to create integration: {str(create_error)}")
                    import traceback
                    print(traceback.format_exc())
                    raise
                print(f"[DEBUG] New integration created with ID: {new_integration.id}")

            # Commit the transaction explicitly
            await db.commit()
            print(f"[DEBUG] Database transaction committed")

            # Verify the integration was saved
            saved_integration = await integration_service.get_by_user_and_provider(
                db, user_id, "google_drive"
            )
            if saved_integration:
                print(f"[DEBUG] Integration verified in database: {saved_integration.provider_email}")
            else:
                print(f"[ERROR] Failed to save integration to database")

        except Exception as db_error:
            print(f"[ERROR] Database operation failed: {str(db_error)}")
            await db.rollback()
            raise

        # Redirect to the Google Auth callback page
        frontend_url = settings.BACKEND_CORS_ORIGINS[0] if settings.BACKEND_CORS_ORIGINS else "http://localhost:3000"
        return RedirectResponse(f"{frontend_url}/auth/google/callback")

    except Exception as e:
        print(f"[ERROR] Error in Google OAuth callback: {str(e)}")
        # Redirect to the auth callback page with error parameter
        frontend_url = settings.BACKEND_CORS_ORIGINS[0] if settings.BACKEND_CORS_ORIGINS else "http://localhost:3000"
        return RedirectResponse(f"{frontend_url}/auth/google/callback?error={str(e)}")


@router.get("/google/status", response_model=Dict[str, Any])
async def get_google_drive_status(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get the current Google Drive integration status for the user
    """
    print(f"[DEBUG] Checking Google Drive status for user: {current_user.email} (ID: {current_user.id})")
    integration = await integration_service.get_by_user_and_provider(
        db, current_user.id, "google_drive"
    )

    if integration:
        print(f"[DEBUG] Found integration for {current_user.email}: {integration.provider_email}")
        return {
            "connected": True,
            "user_email": integration.provider_email,
            "user_id": integration.provider_user_id,
            "connected_at": integration.created_at,
            "last_updated": integration.updated_at,
        }

    print(f"[DEBUG] No integration found for user: {current_user.email}")
    return {"connected": False, "user_email": None}


@router.delete("/google/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_google_drive(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Disconnect Google Drive integration
    """
    await integration_service.delete_by_user_and_provider(
        db, current_user.id, "google_drive"
    )


@router.get("/google/files", response_model=Dict[str, Any])
async def list_google_drive_files(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    folder_id: Optional[str] = Query(None),
    page_token: Optional[str] = Query(None),
    page_size: int = Query(100, gt=0, le=1000),
) -> Dict[str, Any]:
    """
    List files from Google Drive
    """
    integration = await integration_service.get_by_user_and_provider(
        db, current_user.id, "google_drive"
    )

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google Drive integration not found. Please connect your account first.",
        )

    try:
        files, next_page_token = await google_drive_service.list_files(
            db, integration, folder_id, page_token, page_size
        )

        # Get current folder metadata if a folder_id is provided
        current_folder = None
        parent_folders = []
        if folder_id:
            try:
                current_folder = await google_drive_service.get_file_metadata(
                    db, integration, folder_id
                )

                # If the current folder has parents, get the parent folder metadata
                if current_folder.parents and current_folder.parents[0]:
                    parent_folder = await google_drive_service.get_file_metadata(
                        db, integration, current_folder.parents[0]
                    )
                    parent_folders = [parent_folder]
            except Exception as folder_error:
                print(f"Error fetching folder metadata: {str(folder_error)}")
                # Continue even if folder metadata cannot be fetched

        return {
            "files": files,
            "next_page_token": next_page_token,
            "current_folder": current_folder,
            "parent_folders": parent_folders,
            "is_root": folder_id is None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching Google Drive files: {str(e)}",
        )


@router.get("/google/files/{file_id}", response_model=GoogleDriveFile)
async def get_google_drive_file(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file_id: str,
) -> GoogleDriveFile:
    """
    Get a specific Google Drive file's metadata
    """
    integration = await integration_service.get_by_user_and_provider(
        db, current_user.id, "google_drive"
    )
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google Drive integration not found. Please connect your account first.",
        )
    
    try:
        file_metadata = await google_drive_service.get_file_metadata(
            db, integration, file_id
        )
        return file_metadata
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching Google Drive file metadata: {str(e)}",
        )


@router.post("/google/import", status_code=status.HTTP_200_OK)
async def import_google_drive_files(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    import_request: GoogleDriveImportRequest,
) -> Dict[str, Any]:
    """
    Import files from Google Drive into the data room
    """
    integration = await integration_service.get_by_user_and_provider(
        db, current_user.id, "google_drive"
    )
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google Drive integration not found. Please connect your account first.",
        )
    
    try:
        imported_document_ids = []
        imported_folder_ids = []
        skipped_items = []
        
        for file_id in import_request.file_ids:
            # Check if the file is a folder
            file_metadata = await google_drive_service.get_file_metadata(
                db, integration, file_id
            )
            
            if file_metadata.is_folder:
                # Skip folders if not requested
                if not import_request.include_folders:
                    skipped_items.append({
                        "id": file_id,
                        "name": file_metadata.name,
                        "error": "Folder import skipped based on user request"
                    })
                    continue
                
                # Import folder recursively
                result = await google_drive_service.import_folder(
                    db, 
                    current_user.id,
                    integration, 
                    file_id,
                    import_request.parent_folder_id,
                    max_depth=import_request.max_depth
                )
                imported_folder_ids.append(result["folder_id"])
            else:
                # Import the file
                try:
                    document_id = await google_drive_service.import_file(
                        db, 
                        current_user.id,
                        integration, 
                        file_id,
                        import_request.parent_folder_id
                    )
                    imported_document_ids.append(document_id)
                except Exception as e:
                    skipped_items.append({
                        "id": file_id,
                        "name": file_metadata.name,
                        "error": str(e)
                    })
        
        return {
            "imported_document_ids": imported_document_ids,
            "imported_folder_ids": imported_folder_ids,
            "skipped_items": skipped_items,
            "total_documents_imported": len(imported_document_ids),
            "total_folders_imported": len(imported_folder_ids),
            "total_skipped": len(skipped_items)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing Google Drive files: {str(e)}",
        )


@router.get("/google/storage", status_code=status.HTTP_200_OK)
async def get_google_drive_storage(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get Google Drive storage usage information
    """
    integration = await integration_service.get_by_user_and_provider(
        db, current_user.id, "google_drive"
    )
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google Drive integration not found. Please connect your account first.",
        )
    
    try:
        storage_info = await google_drive_service.get_storage_usage(db, integration)
        return storage_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching Google Drive storage information: {str(e)}",
        )


@router.get("/google/search", status_code=status.HTTP_200_OK)
async def search_google_drive(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    query: str = Query(..., description="Search query"),
    page_token: Optional[str] = Query(None),
    page_size: int = Query(100, gt=0, le=1000),
) -> Dict[str, Any]:
    """
    Search for files in Google Drive
    """
    integration = await integration_service.get_by_user_and_provider(
        db, current_user.id, "google_drive"
    )

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google Drive integration not found. Please connect your account first.",
        )

    try:
        files, next_page_token = await google_drive_service.search_files(
            db, integration, query, page_token, page_size
        )

        return {
            "files": files,
            "next_page_token": next_page_token,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching Google Drive: {str(e)}",
        )


@router.get("/google/api-status", status_code=status.HTTP_200_OK)
async def check_google_api_credentials():
    """
    Check if Google Drive API credentials are valid
    """
    try:
        # Re-read the environment variables to ensure we have the most recent values
        # Note: This is important to reload from .env file when testing
        import os
        from dotenv import load_dotenv

        # Force reload the environment variables
        load_dotenv('.env', override=True)
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

        return {"valid": True}

        print(f"[DEBUG] Loaded Google Client ID: {client_id[:5]}... (checking validity)")

        # Check if the required environment variables are set
        if not client_id or not client_secret:
            return {"valid": False, "message": "Google API credentials are not configured."}

        # Verify that the credentials are correctly formatted
        if not client_id.strip() or not client_secret.strip():
            return {"valid": False, "message": "Google API credentials are not properly configured."}

        # Actually verify the credentials with Google API
        try:
            # Use the google_drive_service to verify the credentials
            # We'll create a simple test request to Google's discovery service
            import httpx

            # Simple validation by attempting to access Google's OAuth server
            url = f"https://oauth2.googleapis.com/tokeninfo?client_id={client_id}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5.0)

                # Check if we got a successful response
                if response.status_code == 200:
                    return {"valid": True}
                else:
                    error_info = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    error_message = error_info.get('error_description', 'Invalid client ID or secret')
                    return {"valid": False, "message": f"Google API credentials are invalid: {error_message}"}

        except Exception as api_error:
            print(f"[ERROR] Failed to validate Google credentials with API: {str(api_error)}")
            return {"valid": False, "message": f"Failed to validate Google credentials: {str(api_error)}"}

        return {"valid": True}
    except Exception as e:
        print(f"[ERROR] Exception in check_google_api_credentials: {str(e)}")
        return {"valid": False, "message": f"Error validating Google API credentials: {str(e)}"}