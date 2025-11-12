from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Folder(Base):
    """Folder model for organizing documents"""

    __tablename__ = "folders"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    parent_id = Column(String, ForeignKey("folders.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="folders")
    documents = relationship("Document", back_populates="folder")
    subfolders = relationship("Folder", backref="parent", remote_side=[id])
    shares = relationship(
        "FolderShare", back_populates="folder", cascade="all, delete-orphan"
    )


class FolderShare(Base):
    """Folder sharing model"""

    __tablename__ = "folder_shares"

    id = Column(String, primary_key=True, index=True)
    folder_id = Column(String, ForeignKey("folders.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    folder = relationship("Folder", back_populates="shares")
    user = relationship("User", back_populates="shared_folders")
