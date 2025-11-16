from datetime import datetime
from typing import Optional

from app.core.security import generate_uuid
from app.db.base_class import Base


class Document(Base):
    """Document model"""

    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id", generate_uuid())
        self.name: str = kwargs.get("name")
        self.description: str | None = kwargs.get("description")
        self.file_path: str = kwargs.get("file_path")
        self.file_type: str = kwargs.get("file_type")
        self.file_size: int = kwargs.get("file_size", 0)
        self.owner_id: str = kwargs.get("owner_id")
        self.folder_id: str | None = kwargs.get("folder_id")
        self.is_deleted: bool = kwargs.get("is_deleted", False)
        self.is_public: bool = kwargs.get("is_public", False)
        self.created_at: datetime = kwargs.get("created_at", datetime.now())
        self.updated_at: datetime | None = kwargs.get("updated_at", datetime.now())

    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now()


class DocumentVersion(Base):
    """Document version model for version control"""

    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id", generate_uuid())
        self.document_id: str = kwargs.get("document_id")
        self.version_number: int = kwargs.get("version_number")
        self.file_path: str = kwargs.get("file_path")
        self.file_size: int = kwargs.get("file_size", 0)
        self.created_at: datetime = kwargs.get("created_at", datetime.now())
        self.created_by: str = kwargs.get("created_by")


class DocumentShare(Base):
    """Document sharing model"""

    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id", generate_uuid())
        self.document_id: str = kwargs.get("document_id")
        self.user_id: str = kwargs.get("user_id")
        self.can_edit: bool = kwargs.get("can_edit", False)
        self.can_delete: bool = kwargs.get("can_delete", False)
        self.created_at: datetime = kwargs.get("created_at", datetime.now())
        self.updated_at: datetime | None = kwargs.get("updated_at")

    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now()
