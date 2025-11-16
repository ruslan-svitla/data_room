import os
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, RedirectResponse

from app.api import deps
from app.core.config import settings
from app.db.dynamodb_session import DynamoDBSession
from app.models.user import User
from app.schemas.document import (
    Document,
    DocumentCreate,
    DocumentUpdate,
    DocumentVersion,
)

# Import the DynamoDB-based document service instead of SQLAlchemy version
from app.services.document_dynamodb_service import document_service

router = APIRouter()


@router.post("", response_model=Document)
async def create_document(
    *,
    db: DynamoDBSession = Depends(deps.get_db),
    name: str = Form(...),
    description: str | None = Form(None),
    folder_id: str | None = Form(None),
    is_public: bool = Form(False),
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new document with uploaded file
    """
    document_in = DocumentCreate(
        name=name, description=description, folder_id=folder_id, is_public=is_public
    )

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

    # Check file size
    file_size = 0
    contents = await file.read()
    file_size = len(contents)
    await file.seek(0)

    if file_size > settings.MAX_CONTENT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum limit of {settings.MAX_CONTENT_LENGTH} bytes",
        )

    document = await document_service.create_with_file(
        obj_in=document_in,
        file=file,
        file_content=contents,
        file_size=file_size,
        owner_id=current_user.id,
    )
    return document


@router.get("", response_model=list[Document])
async def read_documents(
    db: DynamoDBSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    folder_id: str | None = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve documents for current user
    """
    documents = await document_service.get_multi_by_owner(
        owner_id=current_user.id, skip=skip, limit=limit, folder_id=folder_id
    )
    return documents


@router.get("/shared", response_model=list[Document])
async def read_shared_documents(
    db: DynamoDBSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve documents shared with current user
    """
    documents = await document_service.get_shared_with_user(
        user_id=current_user.id, skip=skip, limit=limit
    )
    return documents


@router.get("/{id}", response_model=Document)
async def read_document(
    *,
    db: DynamoDBSession = Depends(deps.get_db),
    id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get document by ID
    """
    document = await document_service.get(id=id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if document.owner_id != current_user.id:
        # Check if document is shared with user or is public
        if not document.is_public and not await document_service.is_shared_with_user(
            document_id=id, user_id=current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this document",
            )

    return document


@router.put("/{id}", response_model=Document)
async def update_document(
    *,
    db: DynamoDBSession = Depends(deps.get_db),
    id: str,
    document_in: DocumentUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update document by ID
    """
    document = await document_service.get(id=id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Check ownership or edit permission
    if document.owner_id != current_user.id:
        if not await document_service.can_edit(document_id=id, user_id=current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this document",
            )

    document = await document_service.update(id=id, obj_in=document_in)
    return document


@router.delete("/{id}", response_model=Document)
async def delete_document(
    *,
    db: DynamoDBSession = Depends(deps.get_db),
    id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete document by ID (soft delete)
    """
    try:
        document = await document_service.get(id=id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        # Check ownership or delete permission
        if document.owner_id != current_user.id:
            if not await document_service.can_delete(
                document_id=id, user_id=current_user.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to delete this document",
                )

        # Perform deletion with physical file removal
        document = await document_service.remove_document_and_files(id=id)

        # Create response manually to avoid SQLAlchemy async issues
        response_data = {
            "id": document.id,
            "name": document.name,
            "description": document.description,
            "file_path": document.file_path,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "owner_id": document.owner_id,
            "folder_id": document.folder_id,
            "is_deleted": True,
            "is_public": document.is_public,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        }

        return response_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}",
        )


@router.get("/{id}/download")
async def download_document(
    *,
    db: DynamoDBSession = Depends(deps.get_db),
    id: str,
    stream: bool = False,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get download URL for document.
    If stream=True, redirects to the file or streams it directly.
    """
    document = await document_service.get(id=id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Check access permission
    if document.owner_id != current_user.id and not document.is_public:
        if not await document_service.is_shared_with_user(
            document_id=id, user_id=current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to download this document",
            )

    file_path = document.file_path

    # Try to get a presigned URL (for S3)
    download_url = document_service.get_download_url(file_path)

    if stream:
        if download_url:
            return RedirectResponse(url=download_url)

        # Fallback to local file serving
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found on server"
            )

        # Always use application/octet-stream to force download behavior
        return FileResponse(
            file_path,
            media_type="application/octet-stream",
            filename=document.name,
            headers={"Content-Disposition": f"attachment; filename={document.name}"},
        )

    # Return JSON with download URL
    if download_url:
        return {"download_url": download_url}
    else:
        # For local files, return a URL that calls this endpoint with stream=True
        # We use a relative URL here
        return {"download_url": f"/api/v1/documents/{id}/download?stream=true"}


@router.post("/{id}/upload-new-version", response_model=DocumentVersion)
async def upload_new_version(
    *,
    db: DynamoDBSession = Depends(deps.get_db),
    id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload a new version of a document
    """
    document = await document_service.get(id=id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Check ownership or edit permission
    if document.owner_id != current_user.id:
        if not await document_service.can_edit(document_id=id, user_id=current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this document",
            )

    # Check file size
    file_size = 0
    contents = await file.read()
    file_size = len(contents)
    await file.seek(0)

    if file_size > settings.MAX_CONTENT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum limit of {settings.MAX_CONTENT_LENGTH} bytes",
        )

    version = await document_service.create_version(
        document_id=id,
        file=file,
        file_content=contents,
        file_size=file_size,
        user_id=current_user.id,
    )
    return version


@router.get("/{id}/versions", response_model=list[DocumentVersion])
async def get_document_versions(
    *,
    db: DynamoDBSession = Depends(deps.get_db),
    id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all versions of a document
    """
    document = await document_service.get(id=id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Check access permission
    if document.owner_id != current_user.id and not document.is_public:
        if not await document_service.is_shared_with_user(
            document_id=id, user_id=current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this document",
            )

    versions = await document_service.get_versions(document_id=id)
    return versions
