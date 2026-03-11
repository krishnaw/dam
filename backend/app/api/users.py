from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import RefreshToken, User
from app.schemas.user import LoginResponse, TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_google_login_url,
    get_or_create_google_user,
    hash_password,
    require_admin,
    verify_google_token,
    verify_password,
)

router = APIRouter(tags=["auth"])


@router.post(
    "/api/auth/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    # Check for existing user
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    access_token = create_access_token(user.id, user.role.value)
    refresh_token_value = create_refresh_token()

    refresh = RefreshToken(
        user_id=user.id,
        token=refresh_token_value,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(refresh)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
        user=UserResponse.model_validate(user),
    )


@router.post("/api/auth/login", response_model=LoginResponse)
async def login(
    body: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token(user.id, user.role.value)
    refresh_token_value = create_refresh_token()

    refresh = RefreshToken(
        user_id=user.id,
        token=refresh_token_value,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(refresh)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
        user=UserResponse.model_validate(user),
    )


@router.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_tokens(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == refresh_token)
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if token_record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        await db.delete(token_record)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Load user
    user_result = await db.execute(
        select(User).where(User.id == token_record.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Rotate tokens
    await db.delete(token_record)
    new_access = create_access_token(user.id, user.role.value)
    new_refresh = create_refresh_token()

    db.add(
        RefreshToken(
            user_id=user.id,
            token=new_refresh,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
    )

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


# ---------------------------------------------------------------------------
# Google OAuth endpoints
# ---------------------------------------------------------------------------


@router.get("/api/auth/google/login")
async def google_login():
    """Return Google OAuth URL for frontend to redirect to."""
    return {"url": get_google_login_url()}


class GoogleCallbackBody(BaseModel):
    code: str


@router.post("/api/auth/google/callback", response_model=TokenResponse)
async def google_callback(
    body: GoogleCallbackBody,
    db: AsyncSession = Depends(get_db),
):
    """Exchange Google auth code for JWT tokens."""
    try:
        google_info = await verify_google_token(body.code)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to verify Google authorization code",
        )

    user = await get_or_create_google_user(db, google_info)
    access_token = create_access_token(user.id, user.role.value)
    refresh_token_value = create_refresh_token()

    refresh = RefreshToken(
        user_id=user.id,
        token=refresh_token_value,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(refresh)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
    )


# ---------------------------------------------------------------------------
# User endpoints
# ---------------------------------------------------------------------------


@router.get("/api/users/me", response_model=UserResponse)
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(User).where(User.id == UUID(current_user["sub"]))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/api/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    result = await db.execute(select(User).order_by(User.created_at))
    return result.scalars().all()
