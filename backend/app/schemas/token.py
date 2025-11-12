from pydantic import BaseModel


class Token(BaseModel):
    """Schema for access token"""

    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """Schema for token payload"""

    sub: str | None = None
    exp: int | None = None


class TokenData(BaseModel):
    """Schema for token data"""

    email: str
    user_id: str
