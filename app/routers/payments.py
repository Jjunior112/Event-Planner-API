from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_workspace
from app.core.event_dependencies import get_current_event
from app.models.event import Event
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentUpdate
from app.schemas.workspace import WorkspaceAuth
from app.services.payment_service import PaymentService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/events/{event_id}/payments",
    tags=["Payments"],
)


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    event: Event = Depends(get_current_event),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    service = PaymentService(session)
    return await service.create(auth, event, current_user, data)


@router.get("", response_model=list[PaymentResponse])
async def list_payments(
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> list[PaymentResponse]:
    service = PaymentService(session)
    return await service.list(event)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    service = PaymentService(session)
    return await service.get(event, payment_id)


@router.patch("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: UUID,
    data: PaymentUpdate,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    service = PaymentService(session)
    return await service.update(event, payment_id, data)


@router.patch("/{payment_id}/installments/{installment_id}/pay", response_model=PaymentResponse)
async def pay_installment(
    payment_id: UUID,
    installment_id: UUID,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    event: Event = Depends(get_current_event),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    service = PaymentService(session)
    return await service.mark_installment_paid(
        auth, event, current_user, payment_id, installment_id
    )


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: UUID,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = PaymentService(session)
    await service.delete(auth, event, payment_id)
