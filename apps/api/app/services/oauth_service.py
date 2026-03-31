from typing import Optional
from datetime import datetime, timezone
import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.user import User
from app.models.oauth_account import OAuthAccount


class OAuthService:
    @staticmethod
    def get_google_auth_url(state: str) -> str:
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.oauth_redirect_url,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"

    @staticmethod
    def get_github_auth_url(state: str) -> str:
        params = {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.oauth_redirect_url,
            "scope": "read:user user:email",
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://github.com/login/oauth/authorize?{query}"

    @staticmethod
    async def exchange_google_code(code: str) -> dict:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.oauth_redirect_url,
                    "grant_type": "authorization_code",
                },
            )
            token_data = token_response.json()

            access_token = token_data.get("access_token")
            if not token_response.is_success or not access_token:
                raise HTTPException(status_code=400, detail="Google authentication failed")

            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if not user_response.is_success:
                raise HTTPException(status_code=400, detail="Google user profile lookup failed")

            return {**token_data, "user_info": user_response.json()}

    @staticmethod
    async def exchange_github_code(code: str) -> dict:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "code": code,
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                },
                headers={"Accept": "application/json"},
            )
            token_data = token_response.json()

            access_token = token_data.get("access_token")
            if not token_response.is_success or not access_token:
                raise HTTPException(status_code=400, detail="GitHub authentication failed")

            user_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if not user_response.is_success:
                raise HTTPException(status_code=400, detail="GitHub user profile lookup failed")

            return {**token_data, "user_info": user_response.json()}

    @staticmethod
    async def get_or_create_user(
        db: AsyncSession, provider: str, oauth_data: dict
    ) -> User:
        user_info = oauth_data["user_info"]

        if provider == "google":
            provider_user_id = user_info["id"]
            email = user_info["email"]
            name = user_info.get("name", email.split("@")[0])
            avatar_url = user_info.get("picture")
        else:  # github
            provider_user_id = str(user_info["id"])
            email = user_info.get("email") or f"{user_info['login']}@github.local"
            name = user_info.get("name") or user_info["login"]
            avatar_url = user_info.get("avatar_url")

        result = await db.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
        )
        oauth_account = result.scalar_one_or_none()

        if oauth_account:
            result = await db.execute(select(User).where(User.id == oauth_account.user_id))
            user = result.scalar_one()
            user.last_login_at = datetime.now(timezone.utc)
            user.avatar_url = avatar_url
        else:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if not user:
                user = User(
                    email=email,
                    name=name,
                    password_hash="",
                    avatar_url=avatar_url,
                    oauth_provider=provider,
                    last_login_at=datetime.now(timezone.utc),
                )
                db.add(user)
                await db.flush()

            oauth_account = OAuthAccount(
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_user_id,
                access_token=oauth_data.get("access_token"),
                refresh_token=oauth_data.get("refresh_token"),
            )
            db.add(oauth_account)

        await db.commit()
        await db.refresh(user)
        return user
