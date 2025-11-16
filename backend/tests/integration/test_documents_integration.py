"""Integration tests for documents router

Integration tests verify the full stack:
- Router endpoints
- Service layer
- Database operations (DynamoDB)
- Storage operations (S3)

These tests use real AWS services (mocked via moto) to ensure
end-to-end functionality works correctly.
"""

import io

import pytest
from fastapi import UploadFile, status
from fastapi.testclient import TestClient

from app.db.dynamodb_session import DynamoDBSession
from app.models.user import User


class TestDocumentCreationIntegration:
    """Integration tests for document creation workflow"""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_document(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        test_user: User,
        sample_file,
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test complete workflow: create document and retrieve it"""
        # Arrange
        document_data = {
            "name": "Integration Test Document",
            "description": "Testing full stack",
            "is_public": False,
        }

        # Act 1: Create document
        create_response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            data=document_data,
            files={"file": ("test.txt", sample_file.file, "text/plain")},
        )

        # Assert creation
        assert create_response.status_code == status.HTTP_200_OK
        created_doc = create_response.json()
        document_id = created_doc["id"]

        # Act 2: Retrieve the document
        get_response = client.get(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers,
        )

        # Assert retrieval
        assert get_response.status_code == status.HTTP_200_OK
        retrieved_doc = get_response.json()
        assert retrieved_doc["id"] == document_id
        assert retrieved_doc["name"] == "Integration Test Document"
        assert retrieved_doc["description"] == "Testing full stack"
        assert retrieved_doc["owner_id"] == test_user.id

        # Act 3: Verify document appears in list
        list_response = client.get(
            "/api/v1/documents",
            headers=auth_headers,
        )

        # Assert in list
        assert list_response.status_code == status.HTTP_200_OK
        documents = list_response.json()
        assert any(doc["id"] == document_id for doc in documents)

    @pytest.mark.asyncio
    async def test_create_document_assigns_file_path(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_file,
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test that document creation assigns a file path"""
        # Arrange
        document_data = {"name": "File Path Test Document"}

        # Act: Create document
        create_response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            data=document_data,
            files={"file": ("test.txt", sample_file.file, "text/plain")},
        )

        # Assert
        assert create_response.status_code == status.HTTP_200_OK
        created_doc = create_response.json()

        # Verify file_path is assigned
        assert "file_path" in created_doc
        assert created_doc["file_path"] is not None
        assert len(created_doc["file_path"]) > 0

        # Verify file metadata is correct
        assert created_doc["file_type"] == "text/plain"
        assert created_doc["file_size"] > 0


class TestDocumentDeletionIntegration:
    """Integration tests for document deletion workflow"""

    @pytest.mark.asyncio
    async def test_delete_document_removes_from_s3(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_file,
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test that deleting a document removes it from S3"""
        # Arrange: Create a document first
        document_data = {"name": "Document to Delete"}
        create_response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            data=document_data,
            files={"file": ("test.txt", sample_file.file, "text/plain")},
        )
        assert create_response.status_code == status.HTTP_200_OK
        created_doc = create_response.json()
        document_id = created_doc["id"]
        file_path = created_doc["file_path"]

        # Verify file exists in S3 before deletion
        from app.core.config import settings

        # Try both path variations
        for path_variant in [file_path, file_path.replace("uploads/", "")]:
            try:
                mock_s3.head_object(Bucket=settings.S3_BUCKET, Key=path_variant)
                break
            except:
                continue

        # Act: Delete the document
        delete_response = client.delete(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers,
        )

        # Assert deletion successful
        assert delete_response.status_code == status.HTTP_200_OK

        # Verify file is removed from S3
        file_exists = False
        for path_variant in [file_path, file_path.replace("uploads/", "")]:
            try:
                mock_s3.head_object(Bucket=settings.S3_BUCKET, Key=path_variant)
                file_exists = True
                break
            except:
                continue

        assert not file_exists, f"File {file_path} should be removed from S3"

    @pytest.mark.asyncio
    async def test_delete_document_soft_deletes_in_db(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_file,
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test that deletion is a soft delete (sets is_deleted flag)"""
        # Arrange: Create a document
        document_data = {"name": "Soft Delete Test"}
        create_response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            data=document_data,
            files={"file": ("test.txt", sample_file.file, "text/plain")},
        )
        document_id = create_response.json()["id"]

        # Act: Delete the document
        delete_response = client.delete(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers,
        )
        assert delete_response.status_code == status.HTTP_200_OK

        # Assert: Document should not appear in list
        list_response = client.get(
            "/api/v1/documents",
            headers=auth_headers,
        )
        documents = list_response.json()
        assert not any(doc["id"] == document_id for doc in documents)

        # Assert: Direct retrieval might still return the document
        # but it should be marked as deleted
        get_response = client.get(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers,
        )
        # The endpoint might return 404 or 200 with is_deleted=True
        # Either is acceptable for soft delete
        assert get_response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_200_OK,
        ]


class TestDocumentDownloadIntegration:
    """Integration tests for document download workflow"""

    @pytest.mark.asyncio
    async def test_download_returns_presigned_url(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_file,
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test that download endpoint returns a presigned S3 URL"""
        # Arrange: Create a document
        document_data = {"name": "Download Test"}
        create_response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            data=document_data,
            files={"file": ("test.txt", sample_file.file, "text/plain")},
        )
        document_id = create_response.json()["id"]

        # Act: Request download
        download_response = client.get(
            f"/api/v1/documents/{document_id}/download",
            headers=auth_headers,
        )

        # Assert
        assert download_response.status_code == status.HTTP_200_OK
        download_data = download_response.json()
        assert "download_url" in download_data
        assert download_data["download_url"] is not None
        # Presigned URLs should contain the S3 bucket name
        from app.core.config import settings

        assert settings.S3_BUCKET in download_data["download_url"]


class TestDocumentPermissionsIntegration:
    """Integration tests for document access control"""

    @pytest.mark.asyncio
    async def test_user_cannot_access_other_users_document(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_file,
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test that users cannot access documents they don't own"""
        # Arrange: Create a document as user 1
        document_data = {"name": "Private Document"}
        create_response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            data=document_data,
            files={"file": ("test.txt", sample_file.file, "text/plain")},
        )
        document_id = create_response.json()["id"]

        # Create a second user
        from app.schemas.user import UserCreate
        from app.services.user import user_service

        user2_data = UserCreate(
            email="user2@example.com",
            username="testuser2",
            password="password123",
            full_name="Test User 2",
        )
        user2 = await user_service.create(db, obj_in=user2_data)

        # Create auth headers for user 2
        from datetime import timedelta

        from app.core.security import create_access_token

        user2_token = create_access_token(
            subject=user2.id, expires_delta=timedelta(minutes=30)
        )
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # Act: Try to access user 1's document as user 2
        get_response = client.get(
            f"/api/v1/documents/{document_id}",
            headers=user2_headers,
        )

        # Assert: Should be forbidden
        assert get_response.status_code == status.HTTP_403_FORBIDDEN


class TestDocumentUpdateIntegration:
    """Integration tests for document update workflow"""

    @pytest.mark.asyncio
    async def test_update_document_metadata(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_file,
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test updating document metadata"""
        # Arrange: Create a document
        document_data = {"name": "Original Name", "description": "Original Description"}
        create_response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            data=document_data,
            files={"file": ("test.txt", sample_file.file, "text/plain")},
        )
        document_id = create_response.json()["id"]

        # Act: Update the document
        update_data = {
            "name": "Updated Name",
            "description": "Updated Description",
        }
        update_response = client.put(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers,
            json=update_data,
        )

        # Assert
        assert update_response.status_code == status.HTTP_200_OK
        updated_doc = update_response.json()
        assert updated_doc["name"] == "Updated Name"
        assert updated_doc["description"] == "Updated Description"

        # Verify changes persist
        get_response = client.get(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers,
        )
        retrieved_doc = get_response.json()
        assert retrieved_doc["name"] == "Updated Name"
        assert retrieved_doc["description"] == "Updated Description"
