import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ShareLink
from app.schemas.sharing import ShareCreate, ShareResponse, ShareUpdate
from app.services.auth import get_current_user, hash_password, require_editor, require_manager, verify_password

router = APIRouter(prefix="/api/shares", tags=["sharing"])


def _share_to_response(share: ShareLink) -> dict:
    return {
        "id": share.id,
        "token": share.token,
        "asset_id": share.asset_id,
        "collection_id": share.collection_id,
        "expires_at": share.expires_at,
        "permissions": share.permissions,
        "is_active": share.is_active,
        "access_count": share.access_count,
        "created_at": share.created_at,
        "share_url": f"/share/{share.token}",
    }


@router.post("/", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
async def create_share(
    body: ShareCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    if not body.asset_id and not body.collection_id:
        raise HTTPException(
            status_code=400,
            detail="Either asset_id or collection_id is required",
        )

    token = secrets.token_urlsafe(32)
    pw_hash = hash_password(body.password) if body.password else None

    share = ShareLink(
        token=token,
        asset_id=body.asset_id,
        collection_id=body.collection_id,
        expires_at=body.expires_at,
        password_hash=pw_hash,
        permissions=body.permissions,
        is_active=True,
        created_by=UUID(current_user["sub"]),
        access_count=0,
    )
    db.add(share)
    await db.flush()
    await db.refresh(share)
    return _share_to_response(share)


@router.get("/{token}/access")
async def access_share(
    token: str,
    password: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ShareLink).where(ShareLink.token == token)
    )
    share = result.scalar_one_or_none()
    if not share or not share.is_active:
        raise HTTPException(status_code=404, detail="Share link not found")

    if share.expires_at and share.expires_at.replace(
        tzinfo=timezone.utc
    ) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Share link has expired")

    if share.password_hash:
        if not password or not verify_password(password, share.password_hash):
            raise HTTPException(status_code=403, detail="Invalid password")

    share.access_count += 1

    return {
        "asset_id": str(share.asset_id) if share.asset_id else None,
        "collection_id": str(share.collection_id) if share.collection_id else None,
        "permissions": share.permissions,
        "access_count": share.access_count,
    }


@router.put("/{share_id}", response_model=ShareResponse)
async def update_share(
    share_id: UUID,
    body: ShareUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(ShareLink).where(ShareLink.id == share_id)
    )
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    if str(share.created_by) != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    if body.expires_at is not None:
        share.expires_at = body.expires_at
    if body.password is not None:
        share.password_hash = hash_password(body.password) if body.password else None
    if body.permissions is not None:
        share.permissions = body.permissions
    if body.is_active is not None:
        share.is_active = body.is_active

    await db.flush()
    await db.refresh(share)
    return _share_to_response(share)


@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share(
    share_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_manager),
):
    result = await db.execute(
        select(ShareLink).where(ShareLink.id == share_id)
    )
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    if str(share.created_by) != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    share.is_active = False
