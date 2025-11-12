from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base schema for user data"""

    email: EmailStr | None = None
    username: str | None = None
    is_active: bool | None = True
    full_name: str | None = None


class UserCreate(UserBase):
    """Schema for creating a user"""

    email: EmailStr
    username: str
    password: str


class UserUpdate(UserBase):
    """Schema for updating a user"""

    password: str | None = None


class UserInDBBase(UserBase):
    """Base schema for user data retrieved from DB"""

    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class User(UserInDBBase):
    """Schema for complete user info (returned to client)"""

    pass


class UserInDB(UserInDBBase):
    """Schema for user with password hash (internal use)"""

    hashed_password: str
