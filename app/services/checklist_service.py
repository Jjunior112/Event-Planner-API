from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.checklist_item import ChecklistItem
from app.models.event import Event
from app.repositories.checklist_repository import ChecklistRepository
from app.repositories.workspace_repository import WorkspaceMemberRepository
from app.schemas.checklist import (
    ChecklistItemCreate,
    ChecklistItemResponse,
    ChecklistItemUpdate,
)


class ChecklistService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ChecklistRepository(session)
        self.member_repo = WorkspaceMemberRepository(session)

    async def list(self, event: Event) -> list[ChecklistItemResponse]:
        items = await self.repo.list_by_event(event.id)
        return [self._to_response(i) for i in items]

    async def create(
        self,
        event: Event,
        data: ChecklistItemCreate,
    ) -> ChecklistItemResponse:
        if data.responsible_user_id:
            await self._validate_member(event.workspace_id, data.responsible_user_id)

        item = await self.repo.create(
            event_id=event.id,
            title=data.title,
            description=data.description,
            due_date=data.due_date,
            responsible_user_id=data.responsible_user_id,
            sort_order=data.sort_order,
        )
        if data.responsible_user_id:
            await self.session.refresh(item, ["responsible_user"])
        return self._to_response(item)

    async def get(self, event: Event, item_id: UUID) -> ChecklistItemResponse:
        item = await self._get_or_404(event.id, item_id)
        return self._to_response(item)

    async def update(
        self,
        event: Event,
        item_id: UUID,
        data: ChecklistItemUpdate,
    ) -> ChecklistItemResponse:
        item = await self._get_or_404(event.id, item_id)

        if data.responsible_user_id is not None:
            await self._validate_member(event.workspace_id, data.responsible_user_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)

        await self.session.flush()
        await self.session.refresh(item, ["responsible_user"])
        return self._to_response(item)

    async def delete(self, event: Event, item_id: UUID) -> None:
        item = await self._get_or_404(event.id, item_id)
        item.soft_delete()

    async def _validate_member(self, workspace_id: UUID, user_id: UUID) -> None:
        membership = await self.member_repo.get_membership(workspace_id, user_id)
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Responsible user is not a workspace member",
            )

    async def _get_or_404(self, event_id: UUID, item_id: UUID) -> ChecklistItem:
        item = await self.repo.get_by_id(item_id, event_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Checklist item not found",
            )
        return item

    @staticmethod
    def _to_response(item: ChecklistItem) -> ChecklistItemResponse:
        return ChecklistItemResponse(
            id=item.id,
            event_id=item.event_id,
            title=item.title,
            description=item.description,
            is_completed=item.is_completed,
            due_date=item.due_date,
            responsible_user_id=item.responsible_user_id,
            responsible_user_name=(
                item.responsible_user.full_name if item.responsible_user else None
            ),
            sort_order=item.sort_order,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
