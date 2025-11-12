from datetime import datetime

from pydantic import BaseModel


class FolderBase(BaseModel):
    """Base schema for folder data"""

    name: str | None = None
    description: str | None = None
    parent_id: str | None = None


class FolderCreate(FolderBase):
    """Schema for creating a folder"""

    name: str


class FolderUpdate(FolderBase):
    """Schema for updating a folder"""

    pass


class FolderInDBBase(FolderBase):
    """Base schema for folder data retrieved from DB"""

    id: str
    name: str
    owner_id: str
    created_at: datetime
    updated_at: datetime | None = None
    is_deleted: bool

    class Config:
        from_attributes = True


class Folder(FolderInDBBase):
    """Schema for complete folder info (returned to client)"""

    pass


# Folder Share Schemas
class FolderShareBase(BaseModel):
    """Base schema for folder share data"""

    folder_id: str
    user_id: str
    can_edit: bool | None = False
    can_delete: bool | None = False
    can_share: bool | None = False


class FolderShareCreate(FolderShareBase):
    """Schema for creating a folder share"""

    pass


class FolderShareUpdate(BaseModel):
    """Schema for updating folder share permissions"""

    can_edit: bool | None = None
    can_delete: bool | None = None
    can_share: bool | None = None


class FolderShareInDBBase(FolderShareBase):
    """Base schema for folder share data retrieved from DB"""

    id: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class FolderShare(FolderShareInDBBase):
    """Schema for complete folder share info"""

    pass
