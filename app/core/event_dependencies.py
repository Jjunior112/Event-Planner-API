from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_workspace
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.schemas.workspace import WorkspaceAuth


async def get_current_event(
    event_id: UUID,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> Event:
    repo = EventRepository(session)
    event = await repo.get_by_id(event_id, auth.workspace.id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event
