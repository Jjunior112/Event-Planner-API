from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_workspace
from app.core.event_dependencies import get_current_event
from app.models.event import Event
from app.models.user import User
from app.schemas.supplier_quote import (
    SupplierQuoteCreate,
    SupplierQuoteResponse,
    SupplierQuoteStatusUpdate,
    SupplierQuoteUpdate,
)
from app.schemas.workspace import WorkspaceAuth
from app.services.supplier_quote_service import SupplierQuoteService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/events/{event_id}/quotes",
    tags=["Quotes"],
)


@router.post("", response_model=SupplierQuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    data: SupplierQuoteCreate,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> SupplierQuoteResponse:
    service = SupplierQuoteService(session)
    return await service.create(event, data)


@router.get("", response_model=list[SupplierQuoteResponse])
async def list_quotes(
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> list[SupplierQuoteResponse]:
    service = SupplierQuoteService(session)
    return await service.list(event)


@router.get("/{quote_id}", response_model=SupplierQuoteResponse)
async def get_quote(
    quote_id: UUID,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> SupplierQuoteResponse:
    service = SupplierQuoteService(session)
    return await service.get(event, quote_id)


@router.patch("/{quote_id}", response_model=SupplierQuoteResponse)
async def update_quote(
    quote_id: UUID,
    data: SupplierQuoteUpdate,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> SupplierQuoteResponse:
    service = SupplierQuoteService(session)
    return await service.update(event, quote_id, data)


@router.patch("/{quote_id}/status", response_model=SupplierQuoteResponse)
async def update_quote_status(
    quote_id: UUID,
    data: SupplierQuoteStatusUpdate,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    event: Event = Depends(get_current_event),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SupplierQuoteResponse:
    service = SupplierQuoteService(session)
    return await service.update_status(auth, event, current_user, quote_id, data)


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(
    quote_id: UUID,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = SupplierQuoteService(session)
    await service.delete(auth, event, quote_id)
