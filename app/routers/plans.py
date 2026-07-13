from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_workspace
from app.schemas.plan import WorkspacePlanResponse
from app.schemas.workspace import WorkspaceAuth
from app.services.plan_limit_service import PlanLimitService
from app.services.plan_service import PlanService

router = APIRouter(prefix="/workspaces/{workspace_id}/plan", tags=["Plans"])


@router.get("", response_model=WorkspacePlanResponse)
async def get_workspace_plan(
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> WorkspacePlanResponse:
    limit_service = PlanLimitService(session)
    service = PlanService(limit_service)
    return await service.get_workspace_plan(auth.workspace)
