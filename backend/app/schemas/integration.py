from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr


class ExternalIntegrationBase(BaseModel):
    provider: str
    provider_user_id: Optional[str] = None
    provider_email: Optional[EmailStr] = None


class ExternalIntegrationCreate(ExternalIntegrationBase):
    access_token: str
    refresh_token: Optional[str] = None
    token_expiry: Optional[datetime] = None


class ExternalIntegrationUpdate(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expiry: Optional[datetime] = None
    provider_user_id: Optional[str] = None
    provider_email: Optional[EmailStr] = None


class ExternalIntegrationInDBBase(ExternalIntegrationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExternalIntegration(ExternalIntegrationInDBBase):
    pass


class GoogleDriveFile(BaseModel):
    id: str
    name: str
    mime_type: str
    size: Optional[int] = None
    web_view_link: Optional[str] = None
    thumbnail_link: Optional[str] = None
    modified_time: Optional[datetime] = None
    created_time: Optional[datetime] = None
    parents: list[str] = []
    is_folder: bool = False


class GoogleDriveAuthState(BaseModel):
    """For tracking authentication state during OAuth flow"""
    user_id: str


class GoogleDriveLinkRequest(BaseModel):
    state: Optional[str] = None  # For CSRF protection


class GoogleDriveImportRequest(BaseModel):
    file_ids: list[str]
    parent_folder_id: Optional[str] = None  # Local folder ID to import into
    max_depth: Optional[int] = 5  # Maximum depth for recursive folder imports
    include_folders: Optional[bool] = True  # Whether to import folders or skip them