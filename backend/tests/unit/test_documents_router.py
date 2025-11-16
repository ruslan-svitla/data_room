"""Unit tests for documents router endpoints"""

import os
import sys

import pytest
from fastapi import status
from fastapi.testclient import TestClient

# Add tests directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.dynamodb_session import DynamoDBSession
from app.models.user import User
from tests.utils.assertions import assert_response_has_keys, assert_status_code
from tests.utils.factories import create_test_file


class TestDocumentCreation:
    """Tests for POST /documents endpoint"""

    @pytest.mark.asyncio
    async def test_create_document_success(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_file,
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test successful document creation with file upload"""
        # Arrange
        document_data = {
            "name": "Test Document",
            "description": "A test document",
            "is_public": False,
        }

        # Act
        response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            data=document_data,
            files={"file": ("test.txt", sample_file.file, "text/plain")},
        )

        # Assert
        assert_status_code(response.status_code, status.HTTP_200_OK)
        data = response.json()
        assert_response_has_keys(
            data, ["id", "name", "file_path", "file_type", "file_size", "owner_id"]
        )
        assert data["name"] == "Test Document"
        assert data["description"] == "A test document"
        assert data["is_public"] is False

    @pytest.mark.asyncio
    async def test_create_document_with_folder(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_file,
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test document creation with folder assignment"""
        # Arrange
        folder_id = "test-folder-id"
        document_data = {
            "name": "Document in Folder",
            "folder_id": folder_id,
        }

        # Act
        response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            data=document_data,
            files={"file": ("test.txt", sample_file.file, "text/plain")},
        )

        # Assert
        assert_status_code(response.status_code, status.HTTP_200_OK)
        data = response.json()
        assert data["folder_id"] == folder_id

    @pytest.mark.asyncio
    async def test_create_public_document(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_file,
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test creating a public document"""
        # Arrange
        document_data = {
            "name": "Public Document",
            "is_public": True,
        }

        # Act
        response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            data=document_data,
            files={"file": ("test.txt", sample_file.file, "text/plain")},
        )

        # Assert
        assert_status_code(response.status_code, status.HTTP_200_OK)
        data = response.json()
        assert data["is_public"] is True

    @pytest.mark.asyncio
    async def test_create_document_file_too_large(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test rejection of oversized file"""
        # Arrange
        large_content = b"x" * (20 * 1024 * 1024)  # 20MB (exceeds 16MB limit)
        large_file = create_test_file(
            filename="large_file.txt",
            content=large_content,
        )

        document_data = {
            "name": "Large Document",
        }

        # Act
        response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            data=document_data,
            files={"file": ("large.txt", large_file.file, "text/plain")},
        )

        # Assert
        assert_status_code(
            response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )

    @pytest.mark.asyncio
    async def test_create_document_unauthenticated(
        self,
        client: TestClient,
        sample_file,
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test rejection of unauthenticated request"""
        # Arrange
        document_data = {
            "name": "Test Document",
        }

        # Act
        response = client.post(
            "/api/v1/documents",
            data=document_data,
            files={"file": ("test.txt", sample_file.file, "text/plain")},
        )

        # Assert
        assert_status_code(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestDocumentListing:
    """Tests for GET /documents endpoint"""

    @pytest.mark.asyncio
    async def test_list_user_documents(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        test_user: User,
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test listing user's documents"""
        # Arrange - Create a document first
        sample_file = create_test_file()
        document_data = {"name": "Test Document"}

        create_response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            data=document_data,
            files={"file": ("test.txt", sample_file.file, "text/plain")},
        )
        assert create_response.status_code == status.HTTP_200_OK

        # Act
        response = client.get(
            "/api/v1/documents",
            headers=auth_headers,
        )

        # Assert
        assert_status_code(response.status_code, status.HTTP_200_OK)
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(doc["name"] == "Test Document" for doc in data)

    @pytest.mark.asyncio
    async def test_list_documents_empty(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        db: DynamoDBSession,
    ):
        """Test listing documents for user with no documents"""
        # Act
        response = client.get(
            "/api/v1/documents",
            headers=auth_headers,
        )

        # Assert
        assert_status_code(response.status_code, status.HTTP_200_OK)
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_documents_with_pagination(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test pagination parameters"""
        # Arrange - Create multiple documents
        for i in range(5):
            sample_file = create_test_file(filename=f"test{i}.txt")
            document_data = {"name": f"Document {i}"}
            client.post(
                "/api/v1/documents",
                headers=auth_headers,
                data=document_data,
                files={"file": (f"test{i}.txt", sample_file.file, "text/plain")},
            )

        # Act
        response = client.get(
            "/api/v1/documents",
            headers=auth_headers,
            params={"skip": 2, "limit": 2},
        )

        # Assert
        assert_status_code(response.status_code, status.HTTP_200_OK)
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2

    @pytest.mark.asyncio
    async def test_list_documents_by_folder(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        mock_s3,
        db: DynamoDBSession,
    ):
        """Test filtering documents by folder_id"""
        # Arrange
        folder_id = "test-folder-123"

        # Create document in folder
        sample_file = create_test_file()
        document_data = {
            "name": "Document in Folder",
            "folder_id": folder_id,
        }
        client.post(
            "/api/v1/documents",
            headers=auth_headers,
            data=document_data,
            files={"file": ("test.txt", sample_file.file, "text/plain")},
        )

        # Create document not in folder
        sample_file2 = create_test_file(filename="test2.txt")
        document_data2 = {"name": "Document Not in Folder"}
        client.post(
            "/api/v1/documents",
            headers=auth_headers,
            data=document_data2,
            files={"file": ("test2.txt", sample_file2.file, "text/plain")},
        )

        # Act
        response = client.get(
            "/api/v1/documents",
            headers=auth_headers,
            params={"folder_id": folder_id},
        )

        # Assert
        assert_status_code(response.status_code, status.HTTP_200_OK)
        data = response.json()
        assert isinstance(data, list)
        # At least one document should be in the specified folder
        folder_docs = [doc for doc in data if doc.get("folder_id") == folder_id]
        assert len(folder_docs) >= 1, (
            f"Expected at least one document in folder {folder_id}"
        )

    @pytest.mark.asyncio
    async def test_list_documents_unauthenticated(
        self,
        client: TestClient,
        db: DynamoDBSession,
    ):
        """Test rejection of unauthenticated request"""
        # Act
        response = client.get("/api/v1/documents")

        # Assert
        assert_status_code(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestSharedDocuments:
    """Tests for GET /documents/shared endpoint"""

    @pytest.mark.asyncio
    async def test_list_shared_documents(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        db: DynamoDBSession,
    ):
        """Test listing documents shared with user"""
        # Act
        response = client.get(
            "/api/v1/documents/shared",
            headers=auth_headers,
        )

        # Assert
        assert_status_code(response.status_code, status.HTTP_200_OK)
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_shared_documents_unauthenticated(
        self,
        client: TestClient,
        db: DynamoDBSession,
    ):
        """Test rejection of unauthenticated request"""
        # Act
        response = client.get("/api/v1/documents/shared")

        # Assert
        assert_status_code(response.status_code, status.HTTP_401_UNAUTHORIZED)
