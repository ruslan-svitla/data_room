from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import generate_uuid
from app.models.folder import Folder, FolderShare
from app.schemas.folder import (
    FolderCreate,
    FolderShareCreate,
    FolderShareUpdate,
    FolderUpdate,
)
from app.services.base import BaseService


class FolderService(BaseService[Folder, FolderCreate, FolderUpdate]):
    """Service for folder operations"""

    async def create(
        self, db: AsyncSession, *, obj_in: FolderCreate, owner_id: str
    ) -> Folder:
        """Create a new folder"""
        db_obj = Folder(
            id=generate_uuid(),
            name=obj_in.name,
            description=obj_in.description,
            parent_id=obj_in.parent_id,
            owner_id=owner_id,
            is_deleted=False,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_multi_by_owner(
        self,
        db: AsyncSession,
        *,
        owner_id: str,
        skip: int = 0,
        limit: int = 100,
        parent_id: str | None = None,
    ) -> list[Folder]:
        """Get folders by owner with optional parent filter"""
        query = select(self.model).filter(
            Folder.owner_id == owner_id, Folder.is_deleted == False
        )
        if parent_id is not None:
            query = query.filter(Folder.parent_id == parent_id)
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def get_shared_with_user(
        self, db: AsyncSession, *, user_id: str, skip: int = 0, limit: int = 100
    ) -> list[Folder]:
        """Get folders shared with a user"""
        query = (
            select(Folder)
            .join(FolderShare, FolderShare.folder_id == Folder.id)
            .filter(FolderShare.user_id == user_id, Folder.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_children(self, db: AsyncSession, *, folder_id: str) -> list[Folder]:
        """Get child folders of a folder"""
        query = select(Folder).filter(
            Folder.parent_id == folder_id, Folder.is_deleted == False
        )
        result = await db.execute(query)
        return result.scalars().all()

    # Folder sharing functions
    async def create_share(
        self, db: AsyncSession, *, obj_in: FolderShareCreate
    ) -> FolderShare:
        """Create a folder share"""
        db_obj = FolderShare(
            id=generate_uuid(),
            folder_id=obj_in.folder_id,
            user_id=obj_in.user_id,
            can_edit=obj_in.can_edit,
            can_delete=obj_in.can_delete,
            can_share=obj_in.can_share,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_share(
        self, db: AsyncSession, *, folder_id: str, user_id: str
    ) -> FolderShare | None:
        """Get a folder share by folder and user"""
        query = select(FolderShare).filter(
            FolderShare.folder_id == folder_id, FolderShare.user_id == user_id
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_share_by_id(self, db: AsyncSession, *, id: str) -> FolderShare | None:
        """Get a folder share by ID"""
        query = select(FolderShare).filter(FolderShare.id == id)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_shares(
        self, db: AsyncSession, *, folder_id: str
    ) -> list[FolderShare]:
        """Get all shares for a folder"""
        query = select(FolderShare).filter(FolderShare.folder_id == folder_id)
        result = await db.execute(query)
        return result.scalars().all()

    async def update_share(
        self, db: AsyncSession, *, db_obj: FolderShare, obj_in: FolderShareUpdate
    ) -> FolderShare:
        """Update a folder share"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove_share(self, db: AsyncSession, *, id: str) -> FolderShare:
        """Remove a folder share"""
        result = await db.execute(select(FolderShare).filter(FolderShare.id == id))
        obj = result.scalars().first()
        await db.delete(obj)
        await db.commit()
        return obj

    async def is_shared_with_user(
        self, db: AsyncSession, *, folder_id: str, user_id: str
    ) -> bool:
        """Check if a folder is shared with a user"""
        share = await self.get_share(db, folder_id=folder_id, user_id=user_id)
        return share is not None

    async def can_edit(self, db: AsyncSession, *, folder_id: str, user_id: str) -> bool:
        """Check if a user can edit a folder"""
        share = await self.get_share(db, folder_id=folder_id, user_id=user_id)
        return share is not None and share.can_edit

    async def can_delete(
        self, db: AsyncSession, *, folder_id: str, user_id: str
    ) -> bool:
        """Check if a user can delete a folder"""
        share = await self.get_share(db, folder_id=folder_id, user_id=user_id)
        return share is not None and share.can_delete

    async def can_share(
        self, db: AsyncSession, *, folder_id: str, user_id: str
    ) -> bool:
        """Check if a user can share a folder"""
        share = await self.get_share(db, folder_id=folder_id, user_id=user_id)
        return share is not None and share.can_share


# Create a singleton instance
folder_service = FolderService(Folder)
