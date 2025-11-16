from pydantic import BaseModel, EmailStr


class GoogleAuthResponse(BaseModel):
    """Schema for Google Authentication response"""

    access_token: str
    token_type: str
    id_token: str | None = None


class GoogleUserInfo(BaseModel):
    """Schema for Google User Info"""

    id: str
    email: EmailStr
    verified_email: bool | None = None
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    picture: str | None = None
    locale: str | None = None


class GoogleAuthRequest(BaseModel):
    """Schema for receiving Google auth token from frontend"""

    id_token: str
    access_token: str | None = None
