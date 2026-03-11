import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import UUID

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from httpx import AsyncClient
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

bearer_scheme = HTTPBearer()


def create_access_token(user_id: UUID, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token() -> str:
    return secrets.token_hex(64)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    payload = verify_token(credentials.credentials)
    if payload.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    return payload


# ---------------------------------------------------------------------------
# Google OAuth helpers
# ---------------------------------------------------------------------------


def get_google_login_url() -> str:
    params = urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    })
    return f"https://accounts.google.com/o/oauth2/v2/auth?{params}"


async def verify_google_token(code: str) -> dict:
    """Exchange Google auth code for user info."""
    async with AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        token_resp.raise_for_status()
        tokens = token_resp.json()

        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        userinfo_resp.raise_for_status()
        return userinfo_resp.json()  # {id, email, name, picture}


async def get_or_create_google_user(db: AsyncSession, google_info: dict):
    """Find or create user from Google profile."""
    from app.models.user import User, UserRole

    # Try to find by google_id first
    result = await db.execute(
        select(User).where(User.google_id == str(google_info["id"]))
    )
    user = result.scalar_one_or_none()
    if user:
        return user

    # Try to find by email
    result = await db.execute(
        select(User).where(User.email == google_info["email"])
    )
    user = result.scalar_one_or_none()
    if user:
        # Link existing account to Google
        user.google_id = str(google_info["id"])
        return user

    # Create new user
    user = User(
        email=google_info["email"],
        full_name=google_info.get("name", google_info["email"]),
        google_id=str(google_info["id"]),
        hashed_password=None,
        role=UserRole.viewer,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Role-based access control
# ---------------------------------------------------------------------------


class RoleChecker:
    """FastAPI dependency for role-based access control."""

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user['role']}' not authorized for this action",
            )
        return user


# Convenience instances
require_admin = RoleChecker(["admin"])
require_manager = RoleChecker(["admin", "manager"])
require_editor = RoleChecker(["admin", "manager", "editor"])
require_reviewer = RoleChecker(["admin", "manager", "editor", "reviewer"])
require_viewer = RoleChecker(["admin", "manager", "editor", "reviewer", "viewer"])
