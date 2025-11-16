import json
from datetime import timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.google_auth import GoogleAuthRequest, GoogleUserInfo
from app.services.user import user_service


class GoogleAuthService:
    """Service for Google authentication"""

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"
    GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"

    async def verify_token(self, id_token: str) -> dict:
        """
        Verify a Google ID token and get user info
        """
        async with httpx.AsyncClient() as client:
            print("[DEBUG] Verifying Google ID token with Google API")

            # Verify token with Google
            params = {"id_token": id_token}
            response = await client.get(self.GOOGLE_TOKEN_INFO_URL, params=params)

            if response.status_code != 200:
                print(f"[ERROR] Google token verification failed: {response.text}")
                raise ValueError(f"Invalid Google ID token: {response.text}")

            token_info = response.json()

            # Verify audience
            if token_info.get("aud") != settings.GOOGLE_CLIENT_ID:
                raise ValueError("Invalid audience for Google token")

            return token_info

    async def get_user_info(self, access_token: str) -> dict:
        """
        Get user info using Google access token
        """
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(self.GOOGLE_USER_INFO_URL, headers=headers)

            if response.status_code != 200:
                raise ValueError(f"Failed to get user info: {response.text}")

            return response.json()

    async def verify_and_process(
        self, db: AsyncSession, auth_request: GoogleAuthRequest
    ) -> dict:
        """
        Verify token and create or update user
        """
        # First verify the ID token
        try:
            token_info = await self.verify_token(auth_request.id_token)
            print(f"[DEBUG] Google token verified for email: {token_info.get('email')}")

            # Get more detailed user info
            user_info = {}
            if auth_request.access_token:
                try:
                    user_info = await self.get_user_info(auth_request.access_token)
                    print(
                        f"[DEBUG] Retrieved Google user info: {user_info.get('name')} ({user_info.get('email')})"
                    )
                except Exception as error:
                    print(f"[WARNING] Could not get detailed user info: {error}")
                    # Fall back to token info
                    user_info = token_info
            else:
                # Use token info
                user_info = token_info

            # Validate required fields
            if not user_info.get("sub") and not user_info.get("id"):
                raise ValueError("Google user ID missing from token info")

            # Create a standardized user info dict
            google_user = {
                "id": user_info.get("sub") or user_info.get("id"),
                "email": user_info.get("email"),
                "verified_email": user_info.get("email_verified") == "true"
                or user_info.get("verified_email") is True,
                "name": user_info.get("name"),
                "given_name": user_info.get("given_name"),
                "family_name": user_info.get("family_name"),
                "picture": user_info.get("picture"),
                "locale": user_info.get("locale"),
            }

            # Create or update user
            user = await user_service.create_or_update_google_user(
                db, google_user_info=google_user
            )

            # Generate JWT token
            access_token_expires = timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            access_token = create_access_token(
                subject=user.id, expires_delta=access_token_expires
            )

            return {
                "access_token": access_token,
                "token_type": "bearer",
            }
        except Exception as e:
            print(f"[ERROR] Google auth error: {str(e)}")
            raise


# Create a singleton instance
google_auth_service = GoogleAuthService()
