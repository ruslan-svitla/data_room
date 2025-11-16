import io
import os
import sys
from collections.abc import AsyncGenerator, Generator
from datetime import timedelta

import boto3
import pytest
import pytest_asyncio
from fastapi import FastAPI, UploadFile
from fastapi.testclient import TestClient
from moto import mock_aws

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.dynamodb_session import DynamoDBSession
from app.db.session import get_db
from app.main import create_application
from app.models.user import User
from app.services.user import user_service


@pytest.fixture(scope="function")
def mock_aws_services():
    """
    Mock AWS services (DynamoDB and S3) for all tests
    """
    # Set environment variables for mocked AWS
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"

    with mock_aws():
        # Create DynamoDB resource
        dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)

        # Create Users table
        dynamodb.create_table(
            TableName=settings.DYNAMODB_USERS_TABLE,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "email", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "EmailIndex",
                    "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        # Create Documents table
        dynamodb.create_table(
            TableName=settings.DYNAMODB_DOCUMENTS_TABLE,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "owner_id", "AttributeType": "S"},
                {"AttributeName": "is_deleted", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "OwnerIndex",
                    "KeySchema": [
                        {"AttributeName": "owner_id", "KeyType": "HASH"},
                        {"AttributeName": "is_deleted", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        # Create Folders table
        dynamodb.create_table(
            TableName=settings.DYNAMODB_FOLDERS_TABLE,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "owner_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "OwnerIndex",
                    "KeySchema": [{"AttributeName": "owner_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        # Create Integrations table
        dynamodb.create_table(
            TableName=settings.DYNAMODB_INTEGRATIONS_TABLE,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "user_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "UserIndex",
                    "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        # Create Document Shares table
        dynamodb.create_table(
            TableName=settings.DYNAMODB_DOCUMENT_SHARES_TABLE,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "document_id", "AttributeType": "S"},
                {"AttributeName": "user_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "DocumentIndex",
                    "KeySchema": [{"AttributeName": "document_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                },
                {
                    "IndexName": "UserSharesIndex",
                    "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                },
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        # Create Document Versions table
        dynamodb.create_table(
            TableName=settings.DYNAMODB_DOCUMENT_VERSIONS_TABLE,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "document_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "DocumentVersionsIndex",
                    "KeySchema": [{"AttributeName": "document_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        # Create S3 bucket
        s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
        )
        s3_client.create_bucket(Bucket=settings.S3_BUCKET)

        yield


@pytest_asyncio.fixture
async def db(mock_aws_services) -> AsyncGenerator[DynamoDBSession, None]:
    """
    Create a DynamoDB session for testing
    """
    # Create DynamoDB session
    session = DynamoDBSession()
    yield session


@pytest.fixture(scope="function")
def app(db: DynamoDBSession) -> Generator[FastAPI, None, None]:
    """
    Create a fresh database on each test case.
    """
    app = create_application()

    # Override get_db dependency
    async def override_get_db():
        try:
            yield db
        finally:
            pass  # No need to close DynamoDB session

    app.dependency_overrides[get_db] = override_get_db

    yield app

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """
    Create a test client for testing API endpoints.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def mock_s3(mock_aws_services):
    """
    Get S3 client for testing (depends on mock_aws_services)
    """
    s3_client = boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )
    return s3_client


@pytest_asyncio.fixture
async def test_user(db: DynamoDBSession) -> User:
    """
    Create a test user for authentication testing
    """
    from app.schemas.user import UserCreate

    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="testpassword123",
        full_name="Test User",
    )

    # Create user using the service
    user = await user_service.create(db, obj_in=user_data)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """
    Generate authentication headers with JWT token for test user
    """
    access_token = create_access_token(
        subject=test_user.id, expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_file() -> UploadFile:
    """
    Create a sample file for upload testing
    """
    file_content = b"This is a test file content for unit testing."
    return UploadFile(
        filename="test_document.txt",
        file=io.BytesIO(file_content),
        headers={"content-type": "text/plain"},
    )


@pytest.fixture
def sample_pdf_file() -> UploadFile:
    """
    Create a sample PDF file for upload testing
    """
    # Minimal valid PDF content
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 4 0 R\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000262 00000 n\n0000000341 00000 n\ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n431\n%%EOF"
    return UploadFile(
        filename="test_document.pdf",
        file=io.BytesIO(pdf_content),
        headers={"content-type": "application/pdf"},
    )
