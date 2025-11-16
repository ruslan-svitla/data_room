import logging
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.security import generate_uuid
from app.models.document import Document, DocumentShare, DocumentVersion
from app.schemas.document import (
    DocumentCreate,
    DocumentShareCreate,
    DocumentShareUpdate,
    DocumentUpdate,
)
from app.services.base import BaseService

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
        async with open(file_path, "wb") as f:
            await f.write(content)

        return file_path

    async def get_file(self, filename: str) -> Path:
        """Get file from local filesystem."""
        file_path = os.path.join(self.upload_folder, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        return Path(file_path)

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


class DocumentService(BaseService[Document, DocumentCreate, DocumentUpdate]):
    """Service for document operations"""

    def __init__(self, model):
        super().__init__(model)
        # Get the appropriate storage provider based on environment
        from app.utils.storage_factory import get_storage_provider

        self.storage = get_storage_provider()

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

    async def get_multi_by_owner(
        self,
        db: AsyncSession,
        *,
        owner_id: str,
        skip: int = 0,
        limit: int = 100,
        folder_id: str | None = None,
    ) -> list[Document]:
        """Get documents by owner with optional folder filter"""
        query = select(self.model).filter(
            Document.owner_id == owner_id, Document.is_deleted == False
        )
        if folder_id is not None:
            query = query.filter(Document.folder_id == folder_id)
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def get_shared_with_user(
        self, db: AsyncSession, *, user_id: str, skip: int = 0, limit: int = 100
    ) -> list[Document]:
        """Get documents shared with a user"""
        query = (
            select(Document)
            .join(DocumentShare, DocumentShare.document_id == Document.id)
            .filter(DocumentShare.user_id == user_id, Document.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def create_with_file(
        self,
        db: AsyncSession,
        *,
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
        filename = f"{doc_id}{extension}"

        # Save file using storage provider
        file_path = await self.storage.save_file(file, filename)

        # Detect file type
        file_type = (
            file.content_type
            or mimetypes.guess_type(file_path)[0]
            or "application/octet-stream"
        )

        # Create document record
        db_obj = Document(
            id=doc_id,
            name=obj_in.name,
            description=obj_in.description,
            folder_id=obj_in.folder_id,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            owner_id=owner_id,
            is_public=obj_in.is_public,
            is_deleted=False,
        )
        db.add(db_obj)

        # Create initial version
        version = DocumentVersion(
            id=generate_uuid(),
            document_id=doc_id,
            version_number=1,
            file_path=file_path,
            file_size=file_size,
            created_by=owner_id,
        )
        db.add(version)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def create_version(
        self,
        db: AsyncSession,
        *,
        document_id: str,
        file: UploadFile,
        file_content: bytes,
        file_size: int,
        user_id: str,
    ) -> DocumentVersion:
        """Create a new version of a document"""
        # Get latest version number
        query = (
            select(DocumentVersion)
            .filter(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.desc())
        )
        result = await db.execute(query)
        latest_version = result.scalars().first()

        version_number = (latest_version.version_number + 1) if latest_version else 1

        # Generate unique ID and filename
        version_id = generate_uuid()
        extension = os.path.splitext(file.filename)[1] if file.filename else ""
        filename = f"{document_id}_v{version_number}{extension}"

        # Save file using storage provider
        file_path = await self.storage.save_file(file, filename)

        # Create version record
        version = DocumentVersion(
            id=version_id,
            document_id=document_id,
            version_number=version_number,
            file_path=file_path,
            file_size=file_size,
            created_by=user_id,
        )
        db.add(version)

        # Update document record with new file info
        result = await db.execute(select(Document).filter(Document.id == document_id))
        document = result.scalars().first()
        document.file_path = file_path
        document.file_size = file_size

        await db.commit()
        await db.refresh(version)
        return version

    async def get_versions(
        self, db: AsyncSession, *, document_id: str
    ) -> list[DocumentVersion]:
        """Get all versions of a document"""
        query = (
            select(DocumentVersion)
            .filter(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    # Document sharing functions
    async def create_share(
        self, db: AsyncSession, *, obj_in: DocumentShareCreate
    ) -> DocumentShare:
        """Create a document share"""
        db_obj = DocumentShare(
            id=generate_uuid(),
            document_id=obj_in.document_id,
            user_id=obj_in.user_id,
            can_edit=obj_in.can_edit,
            can_delete=obj_in.can_delete,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_share(
        self, db: AsyncSession, *, document_id: str, user_id: str
    ) -> DocumentShare | None:
        """Get a document share by document and user"""
        query = select(DocumentShare).filter(
            DocumentShare.document_id == document_id, DocumentShare.user_id == user_id
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_share_by_id(
        self, db: AsyncSession, *, id: str
    ) -> DocumentShare | None:
        """Get a document share by ID"""
        query = select(DocumentShare).filter(DocumentShare.id == id)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_shares(
        self, db: AsyncSession, *, document_id: str
    ) -> list[DocumentShare]:
        """Get all shares for a document"""
        query = select(DocumentShare).filter(DocumentShare.document_id == document_id)
        result = await db.execute(query)
        return result.scalars().all()

    async def update_share(
        self, db: AsyncSession, *, db_obj: DocumentShare, obj_in: DocumentShareUpdate
    ) -> DocumentShare:
        """Update a document share"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove_share(self, db: AsyncSession, *, id: str) -> DocumentShare:
        """Remove a document share"""
        result = await db.execute(select(DocumentShare).filter(DocumentShare.id == id))
        obj = result.scalars().first()
        await db.delete(obj)
        await db.commit()
        return obj

    async def remove_document_and_files(self, db: AsyncSession, *, id: str) -> Document:
        """Remove a document and its physical files

        This method performs both soft delete in the database and physical deletion of files.

        Args:
            db: Database session
            id: Document ID

        Returns:
            Document: The updated document object with is_deleted=True
        """
        # First get the document and all its versions
        result = await db.execute(select(self.model).filter(self.model.id == id))
        document = result.scalars().first()
        if not document:
            return None

        # Get all versions to delete their files
        versions = await self.get_versions(db, document_id=id)

        # Delete all version files (including the current one which may also be in versions)
        deleted_files = []
        for version in versions:
            if await self._delete_file_from_filesystem(version.file_path):
                deleted_files.append(version.file_path)

        # Also delete the current document file if it's not in versions
        if document.file_path not in deleted_files:
            await self._delete_file_from_filesystem(document.file_path)

        # Perform soft delete in database
        document.is_deleted = True
        db.add(document)
        await db.commit()
        await db.refresh(document)

        return document

    async def is_shared_with_user(
        self, db: AsyncSession, *, document_id: str, user_id: str
    ) -> bool:
        """Check if a document is shared with a user"""
        share = await self.get_share(db, document_id=document_id, user_id=user_id)
        return share is not None

    async def can_edit(
        self, db: AsyncSession, *, document_id: str, user_id: str
    ) -> bool:
        """Check if a user can edit a document"""
        share = await self.get_share(db, document_id=document_id, user_id=user_id)
        return share is not None and share.can_edit

    async def can_delete(
        self, db: AsyncSession, *, document_id: str, user_id: str
    ) -> bool:
        """Check if a user can delete a document"""
        share = await self.get_share(db, document_id=document_id, user_id=user_id)
        return share is not None and share.can_delete

    async def create_document(
        self,
        db: AsyncSession,
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
        db_obj = Document(
            id=doc_id,
            name=name,
            description=description,
            folder_id=folder_id,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            owner_id=user_id,
            is_public=is_public,
            is_deleted=False,
        )
        db.add(db_obj)

        # Create initial version
        version = DocumentVersion(
            id=generate_uuid(),
            document_id=doc_id,
            version_number=1,
            file_path=file_path,
            file_size=file_size,
            created_by=user_id,
        )
        db.add(version)

        await db.commit()
        await db.refresh(db_obj)
        return doc_id


# Create a singleton instance
document_service = DocumentService(Document)
