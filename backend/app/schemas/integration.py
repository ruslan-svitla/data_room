from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr


class ExternalIntegrationBase(BaseModel):
    provider: str
    provider_user_id: str | None = None
    provider_email: EmailStr | None = None


class ExternalIntegrationCreate(ExternalIntegrationBase):
    access_token: str
    refresh_token: str | None = None
    token_expiry: datetime | None = None


class ExternalIntegrationUpdate(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_expiry: datetime | None = None
    provider_user_id: str | None = None
    provider_email: EmailStr | None = None


class ExternalIntegrationInDBBase(ExternalIntegrationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ExternalIntegration(ExternalIntegrationInDBBase):
    pass


class GoogleDriveFile(BaseModel):
    id: str
    name: str
    mime_type: str
    size: int | None = None
    web_view_link: str | None = None
    web_content_link: str | None = None
    thumbnail_link: str | None = None
    md5_checksum: str | None = None
    modified_time: datetime | None = None
    created_time: datetime | None = None
    parents: list[str] = []
    is_folder: bool = False
    export_links: dict[str, str] | None = None


class GoogleDriveAuthState(BaseModel):
    """For tracking authentication state during OAuth flow"""

    user_id: str


class GoogleDriveLinkRequest(BaseModel):
    state: str | None = None  # For CSRF protection


class GoogleDriveImportRequest(BaseModel):
    file_ids: list[str]
    parent_folder_id: str | None = None  # Local folder ID to import into
    max_depth: int | None = 5  # Maximum depth for recursive folder imports
    include_folders: bool | None = True  # Whether to import folders or skip them
