from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_event import CalendarEvent
from app.models.event import Event
from app.repositories.calendar_repository import CalendarRepository
from app.schemas.calendar import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventUpdate,
)


class CalendarService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CalendarRepository(session)

    async def list(self, event: Event) -> list[CalendarEventResponse]:
        items = await self.repo.list_by_event(event.id)
        return [CalendarEventResponse.model_validate(i) for i in items]

    async def create(
        self,
        event: Event,
        data: CalendarEventCreate,
    ) -> CalendarEventResponse:
        cal = await self.repo.create(
            event_id=event.id,
            title=data.title,
            description=data.description,
            start_at=data.start_at,
            end_at=data.end_at,
            all_day=data.all_day,
        )
        return CalendarEventResponse.model_validate(cal)

    async def get(self, event: Event, cal_id: UUID) -> CalendarEventResponse:
        cal = await self._get_or_404(event.id, cal_id)
        return CalendarEventResponse.model_validate(cal)

    async def update(
        self,
        event: Event,
        cal_id: UUID,
        data: CalendarEventUpdate,
    ) -> CalendarEventResponse:
        cal = await self._get_or_404(event.id, cal_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(cal, field, value)

        await self.session.flush()
        await self.session.refresh(cal)
        return CalendarEventResponse.model_validate(cal)

    async def delete(self, event: Event, cal_id: UUID) -> None:
        cal = await self._get_or_404(event.id, cal_id)
        cal.soft_delete()

    async def _get_or_404(self, event_id: UUID, cal_id: UUID) -> CalendarEvent:
        cal = await self.repo.get_by_id(cal_id, event_id)
        if cal is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Calendar event not found",
            )
        return cal
