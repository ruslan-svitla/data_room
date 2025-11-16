from datetime import datetime
from typing import Optional

from app.core.security import generate_uuid
from app.db.base_class import Base


class Folder(Base):
    """Folder model for organizing documents"""

    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id", generate_uuid())
        self.name: str = kwargs.get("name")
        self.description: str | None = kwargs.get("description")
        self.owner_id: str = kwargs.get("owner_id")
        self.parent_id: str | None = kwargs.get("parent_id")
        self.is_deleted: bool = kwargs.get("is_deleted", False)
        self.created_at: datetime = kwargs.get("created_at", datetime.now())
        self.updated_at: datetime | None = kwargs.get("updated_at")

    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now()


class FolderShare(Base):
    """Folder sharing model"""

    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id", generate_uuid())
        self.folder_id: str = kwargs.get("folder_id")
        self.user_id: str = kwargs.get("user_id")
        self.can_edit: bool = kwargs.get("can_edit", False)
        self.can_delete: bool = kwargs.get("can_delete", False)
        self.can_share: bool = kwargs.get("can_share", False)
        self.created_at: datetime = kwargs.get("created_at", datetime.now())
        self.updated_at: datetime | None = kwargs.get("updated_at")

    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now()
