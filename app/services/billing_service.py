import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.core.config import get_settings
from app.models.enums import PlanStatus, WorkspacePlan, WorkspaceRole
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
        plan: WorkspacePlan,
    ) -> dict:
        if plan == WorkspacePlan.FREE:
            raise HTTPException(400, "Cannot checkout free plan")

        return await self._create_stripe_checkout(auth, plan)

    async def cancel_workspace_subscription(self, auth: WorkspaceAuth) -> None:
        self._require_billing_manager(auth)
        workspace = auth.workspace

        if workspace.plan == WorkspacePlan.FREE:
            raise HTTPException(400, "Workspace já está no plano Free")

        if workspace.stripe_subscription_id:
            if not self.settings.stripe_secret_key:
                raise HTTPException(503, "Stripe não configurado")

            import stripe

            stripe.api_key = self.settings.stripe_secret_key
            try:
                stripe.Subscription.cancel(workspace.stripe_subscription_id)
            except stripe.error.InvalidRequestError as exc:
                logger.warning(
                    "Stripe subscription cancel failed for %s: %s",
                    workspace.stripe_subscription_id,
                    exc,
                )

        workspace.plan = WorkspacePlan.FREE
        workspace.plan_status = PlanStatus.CANCELED
        workspace.stripe_subscription_id = None
        workspace.subscription_current_period_end = None
        await self.session.flush()
        logger.info("Assinatura cancelada para workspace %s", workspace.id)

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
        if not price_id:
            raise HTTPException(503, f"Stripe price ID não configurado para o plano {plan.value}")

        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{self.settings.frontend_url}/w/{workspace.id}/billing?success=true",
            cancel_url=f"{self.settings.frontend_url}/w/{workspace.id}/billing?canceled=true",
            metadata={"workspace_id": str(workspace.id), "plan": plan.value},
            client_reference_id=str(workspace.id),
            subscription_data={
                "metadata": {
                    "workspace_id": str(workspace.id),
                    "plan": plan.value,
                }
            },
        )
        return {"checkout_url": session.url, "provider": "stripe"}

    async def handle_stripe_webhook(self, request: Request) -> dict:
        if not self.settings.stripe_webhook_secret:
            raise HTTPException(503, "Stripe webhook não configurado")
        if not self.settings.stripe_secret_key:
            raise HTTPException(503, "Stripe não configurado")

        import stripe

        stripe.api_key = self.settings.stripe_secret_key
        payload = await request.body()
        sig = request.headers.get("stripe-signature", "")

        try:
            stripe_event = stripe.Webhook.construct_event(
                payload, sig, self.settings.stripe_webhook_secret
            )
        except Exception as exc:
            logger.warning("Stripe webhook signature validation failed: %s", exc)
            raise HTTPException(400, f"Webhook inválido: {exc}") from exc

        event = self._stripe_dict(stripe_event)
        event_type = event.get("type", "unknown")
        logger.info("Stripe webhook received: %s", event_type)

        try:
            if event_type == "checkout.session.completed":
                checkout_session = self._stripe_dict(event.get("data", {}).get("object"))
                metadata = self._stripe_dict(checkout_session.get("metadata"))
                workspace_id_raw = (
                    metadata.get("workspace_id")
                    or checkout_session.get("client_reference_id")
                )
                plan_name = metadata.get("plan")

                if not workspace_id_raw:
                    logger.warning(
                        "checkout.session.completed sem workspace_id: metadata=%s ref=%s",
                        metadata,
                        checkout_session.get("client_reference_id"),
                    )
                    return {"received": True}

                await self._activate_plan(
                    workspace_id=UUID(str(workspace_id_raw)),
                    plan=self._resolve_plan(plan_name),
                    stripe_customer_id=self._stripe_id(checkout_session.get("customer")),
                    stripe_subscription_id=self._stripe_id(
                        checkout_session.get("subscription")
                    ),
                )
            elif event_type == "customer.subscription.deleted":
                subscription = self._stripe_dict(event.get("data", {}).get("object"))
                await self._cancel_subscription(
                    stripe_subscription_id=self._stripe_id(subscription.get("id"))
                )
        except Exception:
            logger.exception("Stripe webhook processing failed for event %s", event_type)
            raise

        return {"received": True}

    @staticmethod
    def _stripe_dict(value: object | None) -> dict:
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        to_dict = getattr(value, "to_dict", None)
        if callable(to_dict):
            return to_dict()
        return {}

    @staticmethod
    def _stripe_id(value: object | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            raw_id = value.get("id")
            return str(raw_id) if raw_id is not None else None
        to_dict = getattr(value, "to_dict", None)
        if callable(to_dict):
            raw_id = to_dict().get("id")
            return str(raw_id) if raw_id is not None else None
        return str(value)

    def _resolve_plan(self, plan_name: str | None) -> WorkspacePlan:
        if plan_name in PLAN_MAP:
            return PLAN_MAP[plan_name]
        return WorkspacePlan.STARTER

    async def _get_workspace(self, workspace_id: UUID) -> Workspace | None:
        result = await self.session.execute(
            select(Workspace)
            .where(
                Workspace.id == workspace_id,
                Workspace.deleted_at.is_(None),
            )
            .options(noload(Workspace.members))
        )
        return result.scalar_one_or_none()

    async def _activate_plan(
        self,
        workspace_id: UUID,
        plan: WorkspacePlan,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None,
    ) -> None:
        workspace = await self._get_workspace(workspace_id)
        if not workspace:
            logger.warning("Workspace %s não encontrado para ativação de plano", workspace_id)
            return

        workspace.plan = plan
        workspace.plan_status = PlanStatus.ACTIVE
        if stripe_customer_id:
            workspace.stripe_customer_id = stripe_customer_id
        if stripe_subscription_id:
            workspace.stripe_subscription_id = stripe_subscription_id
        workspace.subscription_current_period_end = datetime.now(UTC)
        await self.session.flush()
        logger.info("Plano %s ativado para workspace %s", plan.value, workspace_id)

    async def _cancel_subscription(
        self,
        stripe_subscription_id: str | None = None,
    ) -> None:
        if not stripe_subscription_id:
            return
        result = await self.session.execute(
            select(Workspace)
            .where(
                Workspace.stripe_subscription_id == stripe_subscription_id,
                Workspace.deleted_at.is_(None),
            )
            .options(noload(Workspace.members))
        )
        workspace = result.scalar_one_or_none()
        if workspace:
            workspace.plan = WorkspacePlan.FREE
            workspace.plan_status = PlanStatus.CANCELED
            workspace.stripe_subscription_id = None
            workspace.subscription_current_period_end = None
            await self.session.flush()

    @staticmethod
    def _require_billing_manager(auth: WorkspaceAuth) -> None:
        if auth.membership.role not in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN):
            raise HTTPException(
                403,
                "Apenas owner ou admin pode gerenciar a assinatura",
            )
