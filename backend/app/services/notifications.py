import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Notification


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: uuid.UUID,
        notification_type: str,
        message: str,
        asset_id: uuid.UUID | None = None,
        data: dict | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            message=message,
            asset_id=asset_id,
            data=data,
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def get_user_notifications(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)  # noqa: E712
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def mark_read(
        self, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        stmt = (
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .values(is_read=True)
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .values(is_read=True)
        )
        result = await self.db.execute(stmt)
        return result.rowcount

    async def notify_review_submitted(
        self,
        asset_id: uuid.UUID,
        reviewer_ids: list[uuid.UUID],
        submitter_name: str,
    ) -> list[Notification]:
        notifications = []
        for reviewer_id in reviewer_ids:
            n = await self.create(
                user_id=reviewer_id,
                notification_type="review_submitted",
                message=f"{submitter_name} submitted an asset for review",
                asset_id=asset_id,
            )
            notifications.append(n)
        return notifications

    async def notify_approved(
        self,
        asset_id: uuid.UUID,
        user_id: uuid.UUID,
        approver_name: str,
    ) -> Notification:
        return await self.create(
            user_id=user_id,
            notification_type="approved",
            message=f"{approver_name} approved your asset",
            asset_id=asset_id,
        )

    async def notify_comment(
        self,
        asset_id: uuid.UUID,
        mentioned_user_ids: list[uuid.UUID],
        commenter_name: str,
    ) -> list[Notification]:
        notifications = []
        for user_id in mentioned_user_ids:
            n = await self.create(
                user_id=user_id,
                notification_type="mention",
                message=f"{commenter_name} mentioned you in a comment",
                asset_id=asset_id,
            )
            notifications.append(n)
        return notifications
