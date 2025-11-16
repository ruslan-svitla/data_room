"""Test data factories for creating test objects"""

import io
from datetime import datetime
from typing import Optional

from fastapi import UploadFile

from app.core.security import generate_uuid, get_password_hash
from app.models.document import Document, DocumentShare
from app.models.user import User


def create_test_user(
    email: str = "testuser@example.com",
    password: str = "testpassword",
    full_name: str = "Test User",
    is_active: bool = True,
    user_id: str | None = None,
) -> User:
    """
    Create a test user object

    Args:
        email: User email
        password: User password (will be hashed)
        full_name: User's full name
        is_active: Whether user is active
        user_id: Optional user ID (generated if not provided)

    Returns:
        User object
    """
    return User(
        id=user_id or generate_uuid(),
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        is_active=is_active,
        created_at=datetime.now(),
    )


def create_test_document(
    name: str = "test_document.pdf",
    owner_id: str = None,
    file_path: str = "uploads/test_file.pdf",
    file_type: str = "application/pdf",
    file_size: int = 1024,
    description: str | None = None,
    folder_id: str | None = None,
    is_public: bool = False,
    is_deleted: bool = False,
    document_id: str | None = None,
) -> Document:
    """
    Create a test document object

    Args:
        name: Document name
        owner_id: Owner user ID
        file_path: Path to file in storage
        file_type: MIME type
        file_size: File size in bytes
        description: Optional description
        folder_id: Optional folder ID
        is_public: Whether document is public
        is_deleted: Whether document is deleted
        document_id: Optional document ID (generated if not provided)

    Returns:
        Document object
    """
    return Document(
        id=document_id or generate_uuid(),
        name=name,
        owner_id=owner_id or generate_uuid(),
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        description=description,
        folder_id=folder_id,
        is_public=is_public,
        is_deleted=is_deleted,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def create_test_file(
    filename: str = "test_file.txt",
    content: bytes = b"Test file content",
    content_type: str = "text/plain",
) -> UploadFile:
    """
    Create a test UploadFile object

    Args:
        filename: File name
        content: File content as bytes
        content_type: MIME type

    Returns:
        UploadFile object
    """
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
        headers={"content-type": content_type},
    )


def create_test_share(
    document_id: str,
    user_id: str,
    can_edit: bool = False,
    can_delete: bool = False,
    share_id: str | None = None,
) -> DocumentShare:
    """
    Create a test document share object

    Args:
        document_id: Document ID
        user_id: User ID to share with
        can_edit: Whether user can edit
        can_delete: Whether user can delete
        share_id: Optional share ID (generated if not provided)

    Returns:
        DocumentShare object
    """
    return DocumentShare(
        id=share_id or generate_uuid(),
        document_id=document_id,
        user_id=user_id,
        can_edit=can_edit,
        can_delete=can_delete,
        created_at=datetime.now(),
    )
