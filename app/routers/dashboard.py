from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.event_dependencies import get_current_event
from app.models.event import Event
from app.schemas.dashboard import EventDashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/events/{event_id}/dashboard",
    tags=["Dashboard"],
)


@router.get("", response_model=EventDashboardResponse)
async def get_event_dashboard(
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> EventDashboardResponse:
    service = DashboardService(session)
    return await service.get_event_dashboard(event)
