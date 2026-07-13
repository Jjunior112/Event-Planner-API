from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_event import CalendarEvent


class CalendarRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, cal_id: UUID, event_id: UUID) -> CalendarEvent | None:
        result = await self.session.execute(
            select(CalendarEvent).where(
                CalendarEvent.id == cal_id,
                CalendarEvent.event_id == event_id,
                CalendarEvent.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_event(self, event_id: UUID) -> list[CalendarEvent]:
        result = await self.session.execute(
            select(CalendarEvent)
            .where(
                CalendarEvent.event_id == event_id,
                CalendarEvent.deleted_at.is_(None),
            )
            .order_by(CalendarEvent.start_at.asc())
        )
        return list(result.scalars().all())

    async def create(self, event_id: UUID, **kwargs) -> CalendarEvent:
        cal = CalendarEvent(event_id=event_id, **kwargs)
        self.session.add(cal)
        await self.session.flush()
        await self.session.refresh(cal)
        return cal
