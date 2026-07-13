from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_workspace
from app.schemas.event import EventCreate, EventResponse, EventUpdate
from app.schemas.workspace import WorkspaceAuth
from app.services.event_service import EventService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/events",
    tags=["Events"],
)


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> EventResponse:
    service = EventService(session)
    return await service.create(auth, data)


@router.get("", response_model=list[EventResponse])
async def list_events(
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> list[EventResponse]:
    service = EventService(session)
    return await service.list(auth)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> EventResponse:
    service = EventService(session)
    return await service.get(auth, event_id)


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    data: EventUpdate,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> EventResponse:
    service = EventService(session)
    return await service.update(auth, event_id, data)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = EventService(session)
    await service.delete(auth, event_id)
