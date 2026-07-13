from app.constants.plan_limits import PLAN_LIMITS
from app.models.workspace import Workspace
from app.schemas.plan import (
    PlanLimitsResponse,
    PlanUsageResponse,
    WorkspacePlanResponse,
)
from app.services.plan_limit_service import PlanLimitService


class PlanService:
    def __init__(self, limit_service: PlanLimitService) -> None:
        self.limit_service = limit_service

    async def get_workspace_plan(self, workspace: Workspace) -> WorkspacePlanResponse:
        limits = PLAN_LIMITS[workspace.plan]
        usage = await self.limit_service.get_usage(workspace)

        return WorkspacePlanResponse(
            plan=workspace.plan,
            plan_status=workspace.plan_status,
            limits=PlanLimitsResponse(
                max_events=limits.max_events,
                max_members=limits.max_members,
                max_storage_mb=limits.max_storage_mb,
            ),
            usage=PlanUsageResponse(**usage),
            subscription_current_period_end=(
                workspace.subscription_current_period_end.isoformat()
                if workspace.subscription_current_period_end
                else None
            ),
        )
