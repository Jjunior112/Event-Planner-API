from dataclasses import dataclass

from app.models.enums import WorkspacePlan


@dataclass(frozen=True)
class PlanLimits:
    max_events: int
    max_members: int
    max_storage_mb: int


PLAN_LIMITS: dict[WorkspacePlan, PlanLimits] = {
    WorkspacePlan.FREE: PlanLimits(max_events=1, max_members=3, max_storage_mb=50),
    WorkspacePlan.STARTER: PlanLimits(max_events=5, max_members=10, max_storage_mb=500),
    WorkspacePlan.PREMIUM: PlanLimits(max_events=-1, max_members=-1, max_storage_mb=5000),
}

PLAN_PRICES_BRL: dict[WorkspacePlan, int] = {
    WorkspacePlan.FREE: 0,
    WorkspacePlan.STARTER: 4900,
    WorkspacePlan.PREMIUM: 14900,
}


def is_unlimited(value: int) -> bool:
    return value < 0
