from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, event_id: UUID, workspace_id: UUID) -> Event | None:
        result = await self.session.execute(
            select(Event).where(
                Event.id == event_id,
                Event.workspace_id == workspace_id,
                Event.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(self, workspace_id: UUID) -> list[Event]:
        result = await self.session.execute(
            select(Event)
            .where(
                Event.workspace_id == workspace_id,
                Event.deleted_at.is_(None),
            )
            .order_by(Event.event_date.asc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        workspace_id: UUID,
        name: str,
        event_date,
        description: str | None = None,
        location: str | None = None,
        budget: Decimal | None = None,
    ) -> Event:
        event = Event(
            workspace_id=workspace_id,
            name=name,
            description=description,
            event_date=event_date,
            location=location,
            budget=budget,
        )
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event
