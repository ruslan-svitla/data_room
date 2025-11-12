from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.schemas.folder import Folder, FolderCreate, FolderUpdate
from app.services.folder import folder_service

router = APIRouter()


@router.post("", response_model=Folder)
async def create_folder(
    *,
    db: AsyncSession = Depends(deps.get_db),
    folder_in: FolderCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new folder
    """
    if folder_in.parent_id:
        parent_folder = await folder_service.get(db=db, id=folder_in.parent_id)
        if not parent_folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parent folder not found"
            )

        # Check if user has access to parent folder
        if parent_folder.owner_id != current_user.id:
            if not await folder_service.can_edit(
                db=db, folder_id=folder_in.parent_id, user_id=current_user.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to create a folder here",
                )

    folder = await folder_service.create(
        db=db, obj_in=folder_in, owner_id=current_user.id
    )
    return folder


@router.get("", response_model=list[Folder])
async def read_folders(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    parent_id: str | None = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve folders for current user
    """
    folders = await folder_service.get_multi_by_owner(
        db=db, owner_id=current_user.id, skip=skip, limit=limit, parent_id=parent_id
    )
    return folders


@router.get("/shared", response_model=list[Folder])
async def read_shared_folders(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve folders shared with current user
    """
    folders = await folder_service.get_shared_with_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return folders


@router.get("/{id}", response_model=Folder)
async def read_folder(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get folder by ID
    """
    folder = await folder_service.get(db=db, id=id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )

    if folder.owner_id != current_user.id:
        # Check if folder is shared with user
        if not await folder_service.is_shared_with_user(
            db=db, folder_id=id, user_id=current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this folder",
            )

    return folder


@router.put("/{id}", response_model=Folder)
async def update_folder(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: str,
    folder_in: FolderUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update folder by ID
    """
    folder = await folder_service.get(db=db, id=id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )

    # Check ownership or edit permission
    if folder.owner_id != current_user.id:
        if not await folder_service.can_edit(
            db=db, folder_id=id, user_id=current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this folder",
            )

    # If changing parent_id, check permissions for the new parent folder
    if folder_in.parent_id and folder_in.parent_id != folder.parent_id:
        parent_folder = await folder_service.get(db=db, id=folder_in.parent_id)
        if not parent_folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parent folder not found"
            )

        # Check if user has access to new parent folder
        if parent_folder.owner_id != current_user.id:
            if not await folder_service.can_edit(
                db=db, folder_id=folder_in.parent_id, user_id=current_user.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to move folder to this location",
                )

    folder = await folder_service.update(db=db, db_obj=folder, obj_in=folder_in)
    return folder


@router.delete("/{id}", response_model=Folder)
async def delete_folder(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete folder by ID (soft delete)
    """
    folder = await folder_service.get(db=db, id=id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )

    # Check ownership or delete permission
    if folder.owner_id != current_user.id:
        if not await folder_service.can_delete(
            db=db, folder_id=id, user_id=current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete this folder",
            )

    folder = await folder_service.remove(db=db, id=id)
    return folder
