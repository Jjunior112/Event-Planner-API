import logging
from datetime import UTC, datetime
from uuid import UUID

import httpx
from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.plan_limits import PLAN_PRICES_BRL
from app.core.config import get_settings
from app.models.enums import BillingProvider, PlanStatus, WorkspacePlan
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceAuth

logger = logging.getLogger(__name__)

PLAN_MAP = {
    "starter": WorkspacePlan.STARTER,
    "premium": WorkspacePlan.PREMIUM,
}


class BillingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()

    async def create_checkout(
        self,
        auth: WorkspaceAuth,
        provider: BillingProvider,
        plan: WorkspacePlan,
    ) -> dict:
        if plan == WorkspacePlan.FREE:
            raise HTTPException(400, "Cannot checkout free plan")

        if provider == BillingProvider.STRIPE:
            return await self._create_stripe_checkout(auth, plan)
        return await self._create_mercadopago_checkout(auth, plan)

    async def _create_stripe_checkout(
        self,
        auth: WorkspaceAuth,
        plan: WorkspacePlan,
    ) -> dict:
        if not self.settings.stripe_secret_key:
            raise HTTPException(503, "Stripe não configurado")

        import stripe

        stripe.api_key = self.settings.stripe_secret_key
        workspace = auth.workspace

        price_id = (
            self.settings.stripe_starter_price_id
            if plan == WorkspacePlan.STARTER
            else self.settings.stripe_premium_price_id
        )

        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{self.settings.frontend_url}/w/{workspace.id}/billing?success=true",
            cancel_url=f"{self.settings.frontend_url}/w/{workspace.id}/billing?canceled=true",
            metadata={"workspace_id": str(workspace.id), "plan": plan.value},
            client_reference_id=str(workspace.id),
        )
        return {"checkout_url": session.url, "provider": "stripe"}

    async def _create_mercadopago_checkout(
        self,
        auth: WorkspaceAuth,
        plan: WorkspacePlan,
    ) -> dict:
        if not self.settings.mercadopago_access_token:
            raise HTTPException(503, "Mercado Pago não configurado")

        workspace = auth.workspace
        amount = PLAN_PRICES_BRL[plan] / 100

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.mercadopago.com/checkout/preferences",
                headers={
                    "Authorization": f"Bearer {self.settings.mercadopago_access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "items": [
                        {
                            "title": f"Event Planner - Plano {plan.value}",
                            "quantity": 1,
                            "unit_price": amount,
                            "currency_id": "BRL",
                        }
                    ],
                    "metadata": {
                        "workspace_id": str(workspace.id),
                        "plan": plan.value,
                    },
                    "back_urls": {
                        "success": f"{self.settings.frontend_url}/w/{workspace.id}/billing?success=true",
                        "failure": f"{self.settings.frontend_url}/w/{workspace.id}/billing?canceled=true",
                    },
                    "auto_return": "approved",
                },
            )
            if response.status_code >= 400:
                logger.error("MP checkout error: %s", response.text)
                raise HTTPException(502, "Erro ao criar checkout Mercado Pago")

            data = response.json()
            return {
                "checkout_url": data.get("init_point"),
                "provider": "mercadopago",
            }

    async def handle_stripe_webhook(self, request: Request) -> dict:
        if not self.settings.stripe_webhook_secret:
            raise HTTPException(503, "Stripe webhook não configurado")

        import stripe

        stripe.api_key = self.settings.stripe_secret_key
        payload = await request.body()
        sig = request.headers.get("stripe-signature", "")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig, self.settings.stripe_webhook_secret
            )
        except Exception as exc:
            raise HTTPException(400, f"Webhook inválido: {exc}") from exc

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            await self._activate_plan(
                workspace_id=UUID(session["metadata"]["workspace_id"]),
                plan=PLAN_MAP.get(session["metadata"]["plan"], WorkspacePlan.STARTER),
                stripe_customer_id=session.get("customer"),
                stripe_subscription_id=session.get("subscription"),
            )
        elif event["type"] == "customer.subscription.deleted":
            sub = event["data"]["object"]
            await self._cancel_subscription(stripe_subscription_id=sub["id"])

        return {"received": True}

    async def handle_mercadopago_webhook(self, data: dict) -> dict:
        if data.get("type") != "payment":
            return {"received": True}

        payment_id = data.get("data", {}).get("id")
        if not payment_id:
            return {"received": True}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.mercadopago.com/v1/payments/{payment_id}",
                headers={
                    "Authorization": f"Bearer {self.settings.mercadopago_access_token}",
                },
            )
            if response.status_code >= 400:
                return {"received": True}

            payment = response.json()
            if payment.get("status") != "approved":
                return {"received": True}

            metadata = payment.get("metadata", {})
            workspace_id = metadata.get("workspace_id")
            plan_name = metadata.get("plan", "starter")
            if workspace_id:
                await self._activate_plan(
                    workspace_id=UUID(workspace_id),
                    plan=PLAN_MAP.get(plan_name, WorkspacePlan.STARTER),
                    mercadopago_subscription_id=str(payment_id),
                )

        return {"received": True}

    async def _activate_plan(
        self,
        workspace_id: UUID,
        plan: WorkspacePlan,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None,
        mercadopago_subscription_id: str | None = None,
    ) -> None:
        result = await self.session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        workspace = result.scalar_one_or_none()
        if not workspace:
            return

        workspace.plan = plan
        workspace.plan_status = PlanStatus.ACTIVE
        if stripe_customer_id:
            workspace.stripe_customer_id = stripe_customer_id
        if stripe_subscription_id:
            workspace.stripe_subscription_id = stripe_subscription_id
        if mercadopago_subscription_id:
            workspace.mercadopago_subscription_id = mercadopago_subscription_id
        workspace.subscription_current_period_end = datetime.now(UTC)
        await self.session.flush()

    async def _cancel_subscription(
        self,
        stripe_subscription_id: str | None = None,
    ) -> None:
        if not stripe_subscription_id:
            return
        result = await self.session.execute(
            select(Workspace).where(
                Workspace.stripe_subscription_id == stripe_subscription_id
            )
        )
        workspace = result.scalar_one_or_none()
        if workspace:
            workspace.plan = WorkspacePlan.FREE
            workspace.plan_status = PlanStatus.CANCELED
            await self.session.flush()
