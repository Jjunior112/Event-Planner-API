from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plan_exceptions import require_write_access
from app.models.enums import WorkspaceRole
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventCreate, EventResponse, EventUpdate
from app.schemas.workspace import WorkspaceAuth
from app.services.category_service import CategoryService
from app.services.plan_limit_service import PlanLimitService


class EventService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = EventRepository(session)

    async def create(self, auth: WorkspaceAuth, data: EventCreate) -> EventResponse:
        require_write_access(auth)
        limit_service = PlanLimitService(self.session)
        await limit_service.check_events_limit(auth.workspace)

        event = await self.repo.create(
            workspace_id=auth.workspace.id,
            name=data.name,
            description=data.description,
            event_date=data.event_date,
            location=data.location,
            budget=data.budget,
        )
        category_service = CategoryService(self.session)
        await category_service.create_defaults_for_event(event)
        return EventResponse.model_validate(event)

    async def list(self, auth: WorkspaceAuth) -> list[EventResponse]:
        events = await self.repo.list_by_workspace(auth.workspace.id)
        return [EventResponse.model_validate(e) for e in events]

    async def get(self, auth: WorkspaceAuth, event_id: UUID) -> EventResponse:
        event = await self._get_event_or_404(auth.workspace.id, event_id)
        return EventResponse.model_validate(event)

    async def update(
        self,
        auth: WorkspaceAuth,
        event_id: UUID,
        data: EventUpdate,
    ) -> EventResponse:
        require_write_access(auth)
        event = await self._get_event_or_404(auth.workspace.id, event_id)

        if data.name is not None:
            event.name = data.name
        if data.description is not None:
            event.description = data.description
        if data.event_date is not None:
            event.event_date = data.event_date
        if data.location is not None:
            event.location = data.location
        if data.budget is not None:
            event.budget = data.budget

        await self.session.flush()
        await self.session.refresh(event)
        return EventResponse.model_validate(event)

    async def delete(self, auth: WorkspaceAuth, event_id: UUID) -> None:
        self._require_roles(auth, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)
        event = await self._get_event_or_404(auth.workspace.id, event_id)
        event.soft_delete()

    async def _get_event_or_404(self, workspace_id: UUID, event_id: UUID) -> Event:
        event = await self.repo.get_by_id(event_id, workspace_id)
        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        return event

    @staticmethod
    def _require_roles(auth: WorkspaceAuth, *roles: WorkspaceRole) -> None:
        if auth.membership.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action",
            )
