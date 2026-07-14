from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_workspace
from app.models.enums import WorkspacePlan
from app.schemas.plan import CheckoutRequest, CheckoutResponse
from app.schemas.workspace import WorkspaceAuth
from app.services.billing_service import BillingService

router = APIRouter(prefix="/workspaces/{workspace_id}/billing", tags=["Billing"])


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    data: CheckoutRequest,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    if data.plan not in (WorkspacePlan.STARTER, WorkspacePlan.PREMIUM):
        raise HTTPException(400, "Plano inválido para checkout")
    service = BillingService(session)
    result = await service.create_checkout(auth, data.plan)
    return CheckoutResponse(**result)


webhooks_router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@webhooks_router.post("/stripe")
async def stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> dict:
    service = BillingService(session)
    return await service.handle_stripe_webhook(request)
