from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.document import DocumentShare, DocumentShareCreate, DocumentShareUpdate
from app.schemas.folder import FolderShare, FolderShareCreate, FolderShareUpdate
from app.services.document import document_service
from app.services.folder import folder_service
from app.services.user import user_service

router = APIRouter()


# Document Sharing
@router.post("/documents", response_model=DocumentShare)
def share_document(
    *,
    db: Session = Depends(deps.get_db),
    share_in: DocumentShareCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Share a document with another user
    """
    document = document_service.get(db=db, id=share_in.document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Check if user is owner or has share permission
    if document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to share this document",
        )

    # Check if target user exists
    user = user_service.get(db=db, id=share_in.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if document is already shared with this user
    existing_share = document_service.get_share(
        db=db, document_id=share_in.document_id, user_id=share_in.user_id
    )
    if existing_share:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is already shared with this user",
        )

    share = document_service.create_share(db=db, obj_in=share_in)
    return share


@router.get("/documents", response_model=list[DocumentShare])
def list_document_shares(
    *,
    db: Session = Depends(deps.get_db),
    document_id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    List all users a document is shared with
    """
    document = document_service.get(db=db, id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Check if user is owner
    if document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view shares for this document",
        )

    shares = document_service.get_shares(db=db, document_id=document_id)
    return shares


@router.put("/documents/{share_id}", response_model=DocumentShare)
def update_document_share(
    *,
    db: Session = Depends(deps.get_db),
    share_id: str,
    share_in: DocumentShareUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update document share permissions
    """
    share = document_service.get_share_by_id(db=db, id=share_id)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Share not found"
        )

    document = document_service.get(db=db, id=share.document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Check if user is owner
    if document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update share for this document",
        )

    share = document_service.update_share(db=db, db_obj=share, obj_in=share_in)
    return share


@router.delete("/documents/{share_id}", response_model=DocumentShare)
def delete_document_share(
    *,
    db: Session = Depends(deps.get_db),
    share_id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Remove document sharing
    """
    share = document_service.get_share_by_id(db=db, id=share_id)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Share not found"
        )

    document = document_service.get(db=db, id=share.document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Check if user is owner
    if document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete share for this document",
        )

    share = document_service.remove_share(db=db, id=share_id)
    return share


# Folder Sharing
@router.post("/folders", response_model=FolderShare)
def share_folder(
    *,
    db: Session = Depends(deps.get_db),
    share_in: FolderShareCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Share a folder with another user
    """
    folder = folder_service.get(db=db, id=share_in.folder_id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )

    # Check if user is owner or has share permission
    if folder.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to share this folder",
        )

    # Check if target user exists
    user = user_service.get(db=db, id=share_in.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if folder is already shared with this user
    existing_share = folder_service.get_share(
        db=db, folder_id=share_in.folder_id, user_id=share_in.user_id
    )
    if existing_share:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder is already shared with this user",
        )

    share = folder_service.create_share(db=db, obj_in=share_in)
    return share


@router.get("/folders", response_model=list[FolderShare])
def list_folder_shares(
    *,
    db: Session = Depends(deps.get_db),
    folder_id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    List all users a folder is shared with
    """
    folder = folder_service.get(db=db, id=folder_id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )

    # Check if user is owner
    if folder.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view shares for this folder",
        )

    shares = folder_service.get_shares(db=db, folder_id=folder_id)
    return shares


@router.put("/folders/{share_id}", response_model=FolderShare)
def update_folder_share(
    *,
    db: Session = Depends(deps.get_db),
    share_id: str,
    share_in: FolderShareUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update folder share permissions
    """
    share = folder_service.get_share_by_id(db=db, id=share_id)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Share not found"
        )

    folder = folder_service.get(db=db, id=share.folder_id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )

    # Check if user is owner
    if folder.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update share for this folder",
        )

    share = folder_service.update_share(db=db, db_obj=share, obj_in=share_in)
    return share


@router.delete("/folders/{share_id}", response_model=FolderShare)
def delete_folder_share(
    *,
    db: Session = Depends(deps.get_db),
    share_id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Remove folder sharing
    """
    share = folder_service.get_share_by_id(db=db, id=share_id)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Share not found"
        )

    folder = folder_service.get(db=db, id=share.folder_id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )

    # Check if user is owner
    if folder.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete share for this folder",
        )

    share = folder_service.remove_share(db=db, id=share_id)
    return share
