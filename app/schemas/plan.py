from pydantic import BaseModel

from app.models.enums import BillingProvider, PlanStatus, WorkspacePlan


class PlanLimitsResponse(BaseModel):
    max_events: int
    max_members: int
    max_storage_mb: int


class PlanUsageResponse(BaseModel):
    events_count: int
    members_count: int
    storage_used_bytes: int


class WorkspacePlanResponse(BaseModel):
    plan: WorkspacePlan
    plan_status: PlanStatus
    limits: PlanLimitsResponse
    usage: PlanUsageResponse
    subscription_current_period_end: str | None = None


class CheckoutRequest(BaseModel):
    provider: BillingProvider
    plan: WorkspacePlan


class CheckoutResponse(BaseModel):
    checkout_url: str
    provider: str
