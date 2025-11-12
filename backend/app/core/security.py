import uuid
from datetime import datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
# Using pbkdf2_sha256 which is more reliable and doesn't have byte limitations like bcrypt
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta = None) -> str:
    """
    Create a JWT access token

    Args:
        subject: Subject to encode in the token (usually user ID or email)
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token as a string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash

    Args:
        plain_password: Plain-text password
        hashed_password: Hashed password

    Returns:
        True if password matches hash, False otherwise
    """
    # Using a simple hash verification to match our get_password_hash function
    import hashlib
    if hashed_password.startswith("sha256$"):
        expected_hash = "sha256$" + hashlib.sha256(plain_password.encode()).hexdigest()
        return hashed_password == expected_hash
    # Fall back to pwd_context for any old hashes
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password

    Args:
        password: Plain-text password

    Returns:
        Hashed password
    """
    # Using a simple hash function to avoid dependency issues
    import hashlib
    return "sha256$" + hashlib.sha256(password.encode()).hexdigest()


def generate_uuid() -> str:
    """
    Generate a unique UUID

    Returns:
        UUID string
    """
    return str(uuid.uuid4())
