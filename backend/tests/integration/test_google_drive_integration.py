import json
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.models.user import User
from app.models.integration import ExternalIntegration

@pytest.fixture
def mock_user():
    """Create a test user"""
    return User(
        id="test-user-id",
        email="test@example.com",
        is_active=True,
        hashed_password="fakehashed"
    )


@pytest.fixture
def mock_integration():
    """Create a test Google Drive integration"""
    return ExternalIntegration(
        id="test-integration-id",
        user_id="test-user-id",
        provider="google_drive",
        access_token="fake-access-token",
        refresh_token="fake-refresh-token",
        token_expiry=datetime.now(timezone.utc),
        provider_user_id="google-user-id",
        provider_email="google-user@example.com",
    )


@pytest.fixture
def auth_headers():
    """Generate auth headers for testing"""
    return {"Authorization": "Bearer fake_token"}


@pytest.mark.asyncio
async def test_google_drive_start_link(client, app, mock_user):
    """Test the start_google_drive_link endpoint"""
    # Override auth dependency
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch('app.api.api_v1.endpoints.integrations.google_drive_service') as mock_service:
        # Mock the authorization URL
        mock_service.get_authorization_url.return_value = "https://accounts.google.com/o/oauth2/auth?test=1"
        
        # Make request to endpoint
        response = client.post(
            "/api/v1/integrations/google/link",
            headers={"Authorization": "Bearer fake_token"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "https://accounts.google.com" in data["authorization_url"]


@pytest.mark.asyncio
async def test_google_drive_status_connected(client, app, mock_user, mock_integration):
    """Test the get_google_drive_status endpoint when connected"""
    # Override auth dependency
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch('app.api.api_v1.endpoints.integrations.integration_service') as mock_service:
        # Mock the get_by_user_and_provider method
        mock_service.get_by_user_and_provider = AsyncMock(return_value=mock_integration)
        
        # Make request to endpoint
        response = client.get(
            "/api/v1/integrations/google/status",
            headers={"Authorization": "Bearer fake_token"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["user_email"] == "google-user@example.com"


@pytest.mark.asyncio
async def test_google_drive_status_not_connected(client, app, mock_user):
    """Test the get_google_drive_status endpoint when not connected"""
    # Override auth dependency
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch('app.api.api_v1.endpoints.integrations.integration_service') as mock_service:
        # Mock the get_by_user_and_provider method
        mock_service.get_by_user_and_provider = AsyncMock(return_value=None)
        
        # Make request to endpoint
        response = client.get(
            "/api/v1/integrations/google/status",
            headers={"Authorization": "Bearer fake_token"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False


@pytest.mark.asyncio
async def test_disconnect_google_drive(client, app, mock_user):
    """Test the disconnect_google_drive endpoint"""
    # Override auth dependency
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch('app.api.api_v1.endpoints.integrations.integration_service') as mock_service:
        # Mock the delete_by_user_and_provider method
        mock_service.delete_by_user_and_provider = AsyncMock()
        
        # Make request to endpoint
        response = client.delete(
            "/api/v1/integrations/google/disconnect",
            headers={"Authorization": "Bearer fake_token"}
        )
        
        # Verify response
        assert response.status_code == 204
        mock_service.delete_by_user_and_provider.assert_called_once()


@pytest.mark.asyncio
async def test_list_google_drive_files(client, app, mock_user, mock_integration):
    """Test the list_google_drive_files endpoint"""
    # Override auth dependency
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch('app.api.api_v1.endpoints.integrations.integration_service') as mock_int_service, \
         patch('app.api.api_v1.endpoints.integrations.google_drive_service') as mock_drive_service:
        
        # Mock the service methods
        mock_int_service.get_by_user_and_provider = AsyncMock(return_value=mock_integration)
        
        # Mock list_files
        mock_files = [
            {
                "id": "file1",
                "name": "Test File",
                "mime_type": "text/plain",
                "is_folder": False
            }
        ]
        mock_drive_service.list_files = AsyncMock(return_value=(mock_files, None))
        mock_drive_service.get_file_metadata = AsyncMock(return_value=None)
        
        # Make request to endpoint
        response = client.get(
            "/api/v1/integrations/google/files",
            headers={"Authorization": "Bearer fake_token"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "Test File"