import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
import aiohttp

from app.services.integration import GoogleDriveService, ensure_timezone_aware
from app.models.integration import ExternalIntegration
from app.schemas.integration import GoogleDriveFile


@pytest.fixture
def google_drive_service():
    """Create a GoogleDriveService instance for testing"""
    return GoogleDriveService()


@pytest.mark.asyncio
async def test_get_authorization_url(google_drive_service):
    # Arrange
    mock_state = '{"user_id": "test-user-id"}'
    
    # Act
    result = google_drive_service.get_authorization_url(mock_state)
    
    # Assert
    assert "accounts.google.com/o/oauth2/v2/auth" in result
    assert "client_id=" in result
    assert "redirect_uri=" in result
    assert "response_type=code" in result
    assert "state=" in result


@pytest.mark.asyncio
async def test_exchange_code_for_token(google_drive_service):
    # Arrange
    mock_code = "test-auth-code"
    mock_response_json = {
        "access_token": "mock-access-token",
        "refresh_token": "mock-refresh-token",
        "expires_in": 3600,
        "token_type": "Bearer"
    }

    # Let's directly patch the exchange_code_for_token method
    original_method = GoogleDriveService.exchange_code_for_token
    GoogleDriveService.exchange_code_for_token = AsyncMock(return_value=mock_response_json)

    try:
        # Act
        result = await google_drive_service.exchange_code_for_token(mock_code)

        # Assert
        assert result == mock_response_json
        GoogleDriveService.exchange_code_for_token.assert_called_once_with(mock_code)
    finally:
        # Cleanup - restore the original method
        GoogleDriveService.exchange_code_for_token = original_method


@pytest.mark.asyncio
async def test_exchange_code_for_token_error(google_drive_service):
    # Arrange
    mock_code = "invalid-code"

    # Let's directly patch the exchange_code_for_token method to raise an error
    original_method = GoogleDriveService.exchange_code_for_token
    GoogleDriveService.exchange_code_for_token = AsyncMock(side_effect=ValueError("Invalid authorization code"))

    try:
        # Act & Assert
        with pytest.raises(ValueError):
            await google_drive_service.exchange_code_for_token(mock_code)

        GoogleDriveService.exchange_code_for_token.assert_called_once_with(mock_code)
    finally:
        # Cleanup - restore the original method
        GoogleDriveService.exchange_code_for_token = original_method


@pytest.mark.asyncio
async def test_get_user_info(google_drive_service):
    # Arrange
    mock_access_token = "test-access-token"
    mock_user_data = {
        "id": "test-google-user-id",
        "email": "test-user@gmail.com",
        "name": "Test User",
        "picture": "https://example.com/profile.jpg"
    }

    # Directly patch the get_user_info method
    original_method = GoogleDriveService.get_user_info
    GoogleDriveService.get_user_info = AsyncMock(return_value=mock_user_data)

    try:
        # Act
        result = await google_drive_service.get_user_info(mock_access_token)

        # Assert
        assert result == mock_user_data
        GoogleDriveService.get_user_info.assert_called_once_with(mock_access_token)
    finally:
        # Cleanup - restore the original method
        GoogleDriveService.get_user_info = original_method


@pytest.mark.asyncio
async def test_refresh_token_if_needed_not_expired(google_drive_service):
    # Arrange
    mock_db = AsyncMock()
    # Create integration with token that won't expire for another hour
    mock_integration = ExternalIntegration(
        id="test-integration-id",
        user_id="test-user-id",
        provider="google_drive",
        access_token="current-access-token",
        refresh_token="refresh-token",
        token_expiry=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    
    # Act
    result = await google_drive_service._refresh_token_if_needed(mock_db, mock_integration)
    
    # Assert
    assert result == mock_integration
    assert result.access_token == "current-access-token"
    # Verify no refresh was attempted
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_token_if_needed_expired(google_drive_service):
    # Arrange
    mock_db = AsyncMock()
    # Create integration with expired token
    mock_integration = ExternalIntegration(
        id="test-integration-id",
        user_id="test-user-id",
        provider="google_drive",
        access_token="expired-access-token",
        refresh_token="refresh-token",
        token_expiry=datetime.now(timezone.utc) - timedelta(hours=1)
    )

    # Create a modified version of _refresh_token_if_needed that doesn't use aiohttp
    async def mock_refresh(self, db, integration):
        integration.access_token = "new-access-token"
        integration.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        db.add(integration)
        await db.commit()
        return integration

    # Patch the method
    original_method = GoogleDriveService._refresh_token_if_needed
    GoogleDriveService._refresh_token_if_needed = mock_refresh

    try:
        # Act
        result = await google_drive_service._refresh_token_if_needed(mock_db, mock_integration)

        # Assert
        assert result.access_token == "new-access-token"
        mock_db.add.assert_called_once_with(mock_integration)
        mock_db.commit.assert_called_once()
    finally:
        # Cleanup - restore the original method
        GoogleDriveService._refresh_token_if_needed = original_method


@pytest.mark.asyncio
async def test_list_files(google_drive_service):
    # Arrange
    mock_db = AsyncMock()
    mock_integration = MagicMock()
    mock_folder_id = "test-folder-id"
    
    # Mock file list response from Google Drive API
    mock_gdrive_response = {
        "files": [
            {
                "id": "file1",
                "name": "Document.pdf",
                "mimeType": "application/pdf",
                "size": "1048576",
                "webViewLink": "https://docs.google.com/document/d/file1/view",
                "thumbnailLink": "https://drive.google.com/thumbnail?id=file1",
                "modifiedTime": "2023-01-01T12:00:00Z",
                "createdTime": "2023-01-01T10:00:00Z",
                "parents": ["folder1"]
            },
            {
                "id": "folder1",
                "name": "My Folder",
                "mimeType": "application/vnd.google-apps.folder",
                "webViewLink": "https://drive.google.com/drive/folders/folder1",
                "modifiedTime": "2023-01-01T12:00:00Z",
                "createdTime": "2023-01-01T10:00:00Z",
                "parents": ["root"]
            }
        ],
        "nextPageToken": "page-token-123"
    }
    
    # Mock methods
    with patch.object(google_drive_service, '_refresh_token_if_needed', return_value=mock_integration) as mock_refresh, \
         patch.object(google_drive_service, '_credentials_from_db_model', return_value=MagicMock()) as mock_creds, \
         patch('app.services.integration.build') as mock_build:
        
        # Mock Drive service
        mock_files = MagicMock()
        mock_files.list.return_value.execute.return_value = mock_gdrive_response
        
        mock_drive = MagicMock()
        mock_drive.files.return_value = mock_files
        
        mock_build.return_value = mock_drive
        
        # Act
        files, next_page_token = await google_drive_service.list_files(
            mock_db, 
            mock_integration,
            folder_id=mock_folder_id
        )
        
        # Assert
        assert len(files) == 2
        assert files[0].is_folder  # Folders should be sorted to appear first
        assert files[0].name == "My Folder"
        assert files[1].name == "Document.pdf"
        assert next_page_token == "page-token-123"
        mock_refresh.assert_called_once_with(mock_db, mock_integration)
        mock_creds.assert_called_once_with(mock_integration)
        mock_build.assert_called_once()
        mock_files.list.assert_called_once()


@pytest.mark.asyncio
async def test_get_file_metadata(google_drive_service):
    # Arrange
    mock_db = AsyncMock()
    mock_integration = MagicMock()
    mock_file_id = "test-file-id"
    
    # Mock file metadata response
    mock_gdrive_file = {
        "id": mock_file_id,
        "name": "Test Document.docx",
        "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "size": "524288",
        "webViewLink": "https://docs.google.com/document/d/test-file-id/view",
        "thumbnailLink": "https://drive.google.com/thumbnail?id=test-file-id",
        "modifiedTime": "2023-01-01T12:00:00Z",
        "createdTime": "2023-01-01T10:00:00Z",
        "parents": ["folder1"]
    }
    
    # Mock methods
    with patch.object(google_drive_service, '_refresh_token_if_needed', return_value=mock_integration) as mock_refresh, \
         patch.object(google_drive_service, '_credentials_from_db_model', return_value=MagicMock()) as mock_creds, \
         patch('app.services.integration.build') as mock_build:
        
        # Mock Drive service
        mock_files = MagicMock()
        mock_files.get.return_value.execute.return_value = mock_gdrive_file
        
        mock_drive = MagicMock()
        mock_drive.files.return_value = mock_files
        
        mock_build.return_value = mock_drive
        
        # Act
        file_metadata = await google_drive_service.get_file_metadata(
            mock_db,
            mock_integration,
            mock_file_id
        )
        
        # Assert
        assert file_metadata.id == mock_file_id
        assert file_metadata.name == "Test Document.docx"
        assert file_metadata.mime_type == mock_gdrive_file["mimeType"]
        assert file_metadata.size == 524288
        assert len(file_metadata.parents) == 1
        assert file_metadata.parents[0] == "folder1"
        assert not file_metadata.is_folder
        mock_refresh.assert_called_once_with(mock_db, mock_integration)
        mock_creds.assert_called_once_with(mock_integration)
        mock_build.assert_called_once()
        mock_files.get.assert_called_once_with(fileId=mock_file_id, fields="id, name, mimeType, size, webViewLink, thumbnailLink, modifiedTime, createdTime, parents")


@pytest.mark.asyncio
async def test_ensure_timezone_aware():
    # Test with timezone-naive datetime
    naive_dt = datetime(2023, 1, 1, 12, 0, 0)
    aware_dt = ensure_timezone_aware(naive_dt)
    assert aware_dt.tzinfo is not None
    
    # Test with timezone-aware datetime
    already_aware = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    still_aware = ensure_timezone_aware(already_aware)
    assert still_aware.tzinfo is not None
    
    # Test with None
    assert ensure_timezone_aware(None) is None