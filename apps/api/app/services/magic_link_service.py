from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.magic_link import MagicLink
from app.models.user import User


class MagicLinkService:
    @staticmethod
    async def create_magic_link(db: AsyncSession, email: str) -> str:
        token = MagicLink.generate_token()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        magic_link = MagicLink(
            email=email,
            token=token,
            expires_at=expires_at,
        )
        db.add(magic_link)
        await db.commit()
        return token

    @staticmethod
    async def verify_magic_link(db: AsyncSession, token: str) -> User:
        result = await db.execute(
            select(MagicLink).where(MagicLink.token == token)
        )
        magic_link = result.scalar_one_or_none()

        if not magic_link:
            raise ValueError("Invalid token")

        if magic_link.used_at:
            raise ValueError("Token already used")

        if datetime.now(timezone.utc) > magic_link.expires_at:
            raise ValueError("Token expired")

        result = await db.execute(
            select(User).where(User.email == magic_link.email)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email=magic_link.email,
                name=magic_link.email.split("@")[0],
                password_hash="",
                last_login_at=datetime.now(timezone.utc),
            )
            db.add(user)
        else:
            user.last_login_at = datetime.now(timezone.utc)

        magic_link.used_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
        return user
