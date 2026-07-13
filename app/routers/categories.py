from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_workspace
from app.core.event_dependencies import get_current_event
from app.models.event import Event
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.workspace import WorkspaceAuth
from app.services.category_service import CategoryService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/events/{event_id}/categories",
    tags=["Categories"],
)


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> list[CategoryResponse]:
    service = CategoryService(session)
    return await service.list(event)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    service = CategoryService(session)
    return await service.create(event, data)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    service = CategoryService(session)
    return await service.get(event, category_id)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    service = CategoryService(session)
    return await service.update(event, category_id, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = CategoryService(session)
    await service.delete(auth, event, category_id)
