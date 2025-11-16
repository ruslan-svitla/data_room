from datetime import datetime
from typing import List, Optional

from app.core.security import generate_uuid
from app.db.base_class import Base


class User(Base):
    """User model"""

    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id", generate_uuid())
        self.email: str = kwargs.get("email")
        self.username: str = kwargs.get("username")
        self.hashed_password: str | None = kwargs.get(
            "hashed_password"
        )  # Nullable for OAuth users
        self.full_name: str | None = kwargs.get("full_name")
        self.is_active: bool = kwargs.get("is_active", True)
        self.is_superuser: bool = kwargs.get("is_superuser", False)
        self.created_at: datetime = kwargs.get("created_at", datetime.now())
        self.updated_at: datetime | None = kwargs.get("updated_at")
        self.auth_provider: str = kwargs.get(
            "auth_provider", "local"
        )  # local, google, etc.
        self.google_id: str | None = kwargs.get("google_id")  # Google user ID

    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create a User instance from a dictionary

        This is useful when deserializing data from DynamoDB
        """
        # Handle type conversions for special fields
        if "created_at" in data and isinstance(data["created_at"], str):
            try:
                data["created_at"] = datetime.fromisoformat(data["created_at"])
            except ValueError:
                pass

        if "updated_at" in data and isinstance(data["updated_at"], str):
            try:
                data["updated_at"] = datetime.fromisoformat(data["updated_at"])
            except ValueError:
                pass

        if "is_active" in data and isinstance(data["is_active"], str):
            data["is_active"] = data["is_active"].lower() == "true"

        if "is_superuser" in data and isinstance(data["is_superuser"], str):
            data["is_superuser"] = data["is_superuser"].lower() == "true"

        return cls(**data)
