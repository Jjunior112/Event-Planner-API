from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.event_dependencies import get_current_event
from app.models.event import Event
from app.schemas.checklist import (
    ChecklistItemCreate,
    ChecklistItemResponse,
    ChecklistItemUpdate,
)
from app.services.checklist_service import ChecklistService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/events/{event_id}/checklist",
    tags=["Checklist"],
)


@router.get("", response_model=list[ChecklistItemResponse])
async def list_checklist(
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> list[ChecklistItemResponse]:
    service = ChecklistService(session)
    return await service.list(event)


@router.post("", response_model=ChecklistItemResponse, status_code=status.HTTP_201_CREATED)
async def create_checklist_item(
    data: ChecklistItemCreate,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> ChecklistItemResponse:
    service = ChecklistService(session)
    return await service.create(event, data)


@router.get("/{item_id}", response_model=ChecklistItemResponse)
async def get_checklist_item(
    item_id: UUID,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> ChecklistItemResponse:
    service = ChecklistService(session)
    return await service.get(event, item_id)


@router.patch("/{item_id}", response_model=ChecklistItemResponse)
async def update_checklist_item(
    item_id: UUID,
    data: ChecklistItemUpdate,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> ChecklistItemResponse:
    service = ChecklistService(session)
    return await service.update(event, item_id, data)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checklist_item(
    item_id: UUID,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = ChecklistService(session)
    await service.delete(event, item_id)
