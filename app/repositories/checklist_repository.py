from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.checklist_item import ChecklistItem


class ChecklistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, item_id: UUID, event_id: UUID) -> ChecklistItem | None:
        result = await self.session.execute(
            select(ChecklistItem)
            .options(selectinload(ChecklistItem.responsible_user))
            .where(
                ChecklistItem.id == item_id,
                ChecklistItem.event_id == event_id,
                ChecklistItem.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_event(self, event_id: UUID) -> list[ChecklistItem]:
        result = await self.session.execute(
            select(ChecklistItem)
            .options(selectinload(ChecklistItem.responsible_user))
            .where(
                ChecklistItem.event_id == event_id,
                ChecklistItem.deleted_at.is_(None),
            )
            .order_by(ChecklistItem.sort_order.asc(), ChecklistItem.created_at.asc())
        )
        return list(result.scalars().all())

    async def create(self, event_id: UUID, **kwargs) -> ChecklistItem:
        item = ChecklistItem(event_id=event_id, **kwargs)
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item
