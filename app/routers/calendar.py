from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.event_dependencies import get_current_event
from app.models.event import Event
from app.schemas.calendar import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventUpdate,
)
from app.services.calendar_service import CalendarService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/events/{event_id}/calendar",
    tags=["Calendar"],
)


@router.get("", response_model=list[CalendarEventResponse])
async def list_calendar_events(
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> list[CalendarEventResponse]:
    service = CalendarService(session)
    return await service.list(event)


@router.post("", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_event(
    data: CalendarEventCreate,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> CalendarEventResponse:
    service = CalendarService(session)
    return await service.create(event, data)


@router.get("/{cal_id}", response_model=CalendarEventResponse)
async def get_calendar_event(
    cal_id: UUID,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> CalendarEventResponse:
    service = CalendarService(session)
    return await service.get(event, cal_id)


@router.patch("/{cal_id}", response_model=CalendarEventResponse)
async def update_calendar_event(
    cal_id: UUID,
    data: CalendarEventUpdate,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> CalendarEventResponse:
    service = CalendarService(session)
    return await service.update(event, cal_id, data)


@router.delete("/{cal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_event(
    cal_id: UUID,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = CalendarService(session)
    await service.delete(event, cal_id)
