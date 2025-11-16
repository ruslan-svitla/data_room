import os
from typing import Optional

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Data Room API"

    # Environment
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # CORS settings - allowing all origins as CORS will be handled by API Gateway
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://d18zp2ou2cdphe.cloudfront.net",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # JWT settings
    SECRET_KEY: str = "change_this_in_production_environment"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Removed SQL Database settings

    # Storage settings
    UPLOAD_FOLDER: str = "uploads"
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB

    # AWS settings
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_SESSION_TOKEN: str | None = None
    AWS_ENDPOINT_URL: str | None = None
    S3_BUCKET: str | None = "data-room-fs-dev"

    # DynamoDB Tables
    DYNAMODB_USERS_TABLE: str | None = "DataRoom-Users-dev"
    DYNAMODB_DOCUMENTS_TABLE: str | None = "DataRoom-Documents-dev"
    DYNAMODB_FOLDERS_TABLE: str | None = "DataRoom-Folders-dev"
    DYNAMODB_INTEGRATIONS_TABLE: str | None = "DataRoom-Integrations-dev"
    DYNAMODB_DOCUMENT_SHARES_TABLE: str | None = "DataRoom-DocumentShares-dev"
    DYNAMODB_FOLDER_SHARES_TABLE: str | None = "DataRoom-FolderShares-dev"
    DYNAMODB_DOCUMENT_VERSIONS_TABLE: str | None = "DataRoom-DocumentVersions-dev"

    USE_DYNAMODB: bool = True  # Always use DynamoDB now
    IS_LAMBDA: bool = os.environ.get("AWS_EXECUTION_ENV", "").startswith("AWS_Lambda_")

    # Frontend URL for redirects
    FRONTEND_URL: str | None = None

    @field_validator("FRONTEND_URL", mode="before")
    def set_frontend_url(cls, v: str | None) -> str:
        if v:
            return v
        if os.environ.get("AWS_EXECUTION_ENV", "").startswith("AWS_Lambda_"):
            return "https://d18zp2ou2cdphe.cloudfront.net"
        return "http://localhost:3000"

    # Google Drive Integration
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str | None = None

    @field_validator("GOOGLE_REDIRECT_URI", mode="before")
    def set_google_redirect_uri(cls, v: str | None) -> str:
        if v:
            return v
        if os.environ.get("AWS_EXECUTION_ENV", "").startswith("AWS_Lambda_"):
            return "https://74i0semps4.execute-api.us-east-1.amazonaws.com/dev/api/v1/integrations/google/callback"
        return "http://localhost:8000/api/v1/integrations/google/callback"

    GOOGLE_AUTH_SCOPES: list[str] = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str | None = None  # Set to a directory path to enable file logging

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

    def get_upload_path(self) -> str:
        """Return the appropriate upload path based on environment"""
        # For Lambda, use /tmp which is the only writable location
        if self.IS_LAMBDA:
            return "/tmp/uploads"
        return self.UPLOAD_FOLDER


settings = Settings()
