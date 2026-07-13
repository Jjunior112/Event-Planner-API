from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import NotificationStatus
from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(
        self,
        notification_id: UUID,
        workspace_id: UUID,
    ) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.workspace_id == workspace_id,
                Notification.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        workspace_id: UUID,
        user_id: UUID,
    ) -> list[Notification]:
        result = await self.session.execute(
            select(Notification)
            .where(
                Notification.workspace_id == workspace_id,
                Notification.user_id == user_id,
                Notification.deleted_at.is_(None),
            )
            .order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_pending_scheduled(self, before: datetime) -> list[Notification]:
        result = await self.session.execute(
            select(Notification)
            .options(selectinload(Notification.user))
            .where(
                Notification.status == NotificationStatus.PENDING,
                Notification.scheduled_at.isnot(None),
                Notification.scheduled_at <= before,
                Notification.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Notification:
        notification = Notification(**kwargs)
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)
        return notification
