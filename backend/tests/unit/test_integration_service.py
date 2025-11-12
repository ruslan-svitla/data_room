import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.integration import IntegrationService
from app.models.integration import ExternalIntegration


@pytest.fixture
def integration_service():
    """Create an IntegrationService instance for testing"""
    return IntegrationService(ExternalIntegration)


@pytest.mark.asyncio
async def test_get_by_user_and_provider_found(integration_service):
    # Arrange
    mock_db = AsyncMock()
    mock_user_id = "test-user-id"
    mock_provider = "google_drive"
    
    mock_integration = ExternalIntegration(
        id="test-integration-id",
        user_id=mock_user_id,
        provider=mock_provider,
        access_token="test-token",
        provider_email="user@example.com"
    )
    
    # Mock the database query execution
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_integration
    mock_db.execute.return_value = mock_result
    
    # Act
    with patch('app.services.integration.select') as mock_select:
        result = await integration_service.get_by_user_and_provider(
            mock_db, mock_user_id, mock_provider
        )
    
    # Assert
    assert result is not None
    assert result.id == "test-integration-id"
    assert result.user_id == mock_user_id
    assert result.provider == mock_provider
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_user_and_provider_not_found(integration_service):
    # Arrange
    mock_db = AsyncMock()
    mock_user_id = "test-user-id"
    mock_provider = "google_drive"
    
    # Mock the database query execution returning None
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    
    # Act
    with patch('app.services.integration.select') as mock_select:
        result = await integration_service.get_by_user_and_provider(
            mock_db, mock_user_id, mock_provider
        )
    
    # Assert
    assert result is None
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_delete_by_user_and_provider(integration_service):
    # Arrange
    mock_db = AsyncMock()
    mock_user_id = "test-user-id"
    mock_provider = "google_drive"
    
    # Act
    with patch('app.services.integration.delete') as mock_delete:
        await integration_service.delete_by_user_and_provider(
            mock_db, mock_user_id, mock_provider
        )
    
    # Assert
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()