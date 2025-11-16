from datetime import datetime
from typing import Optional

from app.core.security import generate_uuid
from app.db.base_class import Base


class ExternalIntegration(Base):
    """External integration credentials model"""

    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id", generate_uuid())
        self.user_id: str = kwargs.get("user_id")
        self.provider: str = kwargs.get("provider")  # "google_drive", etc.
        self.access_token: str = kwargs.get("access_token")
        self.refresh_token: str | None = kwargs.get("refresh_token")
        self.token_expiry: datetime | None = kwargs.get("token_expiry")
        self.provider_user_id: str | None = kwargs.get(
            "provider_user_id"
        )  # ID in the external system
        self.provider_email: str | None = kwargs.get(
            "provider_email"
        )  # Email in the external system
        self.created_at: datetime = kwargs.get("created_at", datetime.now())
        self.updated_at: datetime | None = kwargs.get("updated_at")

    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now()
