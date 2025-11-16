from typing import Any, Dict, List, Optional

from app.core.security import generate_uuid, get_password_hash, verify_password
from app.db.dynamodb_session import DynamoDBSession
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.base import BaseService


class UserService(BaseService[User, UserCreate, UserUpdate]):
    """Service for user operations"""

    async def get_by_email(self, db: DynamoDBSession, *, email: str) -> User | None:
        """Get user by email"""
        table = db.dynamodb.Table(db.tables.get("users"))
        response = table.scan(
            FilterExpression="email = :email",
            ExpressionAttributeValues={":email": email},
        )
        items = response.get("Items", [])
        if not items:
            return None

        # Create User object from the first matching item
        return User(**items[0])

    async def get_by_google_id(
        self, db: DynamoDBSession, *, google_id: str
    ) -> User | None:
        """Get user by Google ID"""
        table = db.dynamodb.Table(db.tables.get("users"))
        response = table.scan(
            FilterExpression="google_id = :google_id",
            ExpressionAttributeValues={":google_id": google_id},
        )
        items = response.get("Items", [])
        if not items:
            return None

        # Create User object from the first matching item
        return User(**items[0])

    async def create_or_update_google_user(
        self, db: DynamoDBSession, *, google_user_info: dict
    ) -> User:
        """Create or update a user from Google OAuth data"""
        # Check if user with google_id exists
        google_id = google_user_info["id"]

        existing_user = await self.get_by_google_id(db, google_id=google_id)
        if existing_user:
            # Update the existing user with any new info
            update_data = {}
            if google_user_info.get("name") and not existing_user.full_name:
                update_data["full_name"] = google_user_info.get("name")

            if update_data:
                await self.update(db, db_obj=existing_user, obj_in=update_data)

            return existing_user

        # Check if user exists by email
        email = google_user_info.get("email")
        if not email:
            raise ValueError("Google user info must contain an email address")

        existing_user_by_email = await self.get_by_email(db, email=email)
        if existing_user_by_email:
            # Link the Google account to the existing user
            update_data = {"google_id": google_id, "auth_provider": "google"}
            existing_user = await self.update(
                db, db_obj=existing_user_by_email, obj_in=update_data
            )
            return existing_user

        # Create a new user
        username = email.split("@")[0]  # Use part before @ as username
        base_username = username

        # Make sure username is unique
        counter = 1
        while await self.get_by_username(db, username=username):
            username = f"{base_username}{counter}"
            counter += 1

        new_user = User(
            id=generate_uuid(),
            email=email,
            username=username,
            full_name=google_user_info.get("name") or "",
            is_active=True,
            is_superuser=False,
            auth_provider="google",
            google_id=google_id,
            hashed_password=None,  # No password for Google users
        )

        await db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user

    async def get_by_username(
        self, db: DynamoDBSession, *, username: str
    ) -> User | None:
        """Get user by username"""
        table = db.dynamodb.Table(db.tables.get("users"))
        response = table.scan(
            FilterExpression="username = :username",
            ExpressionAttributeValues={":username": username},
        )
        items = response.get("Items", [])
        if not items:
            return None

        # Create User object from the first matching item
        return User(**items[0])

    async def create(self, db: DynamoDBSession, *, obj_in: UserCreate) -> User:
        """Create a new user"""
        db_obj = User(
            id=generate_uuid(),
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password)
            if hasattr(obj_in, "password") and obj_in.password
            else None,
            full_name=obj_in.full_name,
            is_active=True,
            is_superuser=False,
            auth_provider=obj_in.auth_provider
            if hasattr(obj_in, "auth_provider")
            else "local",
        )
        await db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: DynamoDBSession,
        *,
        db_obj: User,
        obj_in: UserUpdate | dict[str, Any],
    ) -> User:
        """Update user"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    async def authenticate(
        self, db: DynamoDBSession, *, email_or_username: str, password: str
    ) -> User | None:
        """Authenticate user by email/username and password"""
        # First try to find by email
        user = await self.get_by_email(db, email=email_or_username)
        # If not found, try by username
        if not user:
            user = await self.get_by_username(db, username=email_or_username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """Check if user is active"""
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """Check if user is superuser"""
        return user.is_superuser


# Create a singleton instance
user_service = UserService(User)
