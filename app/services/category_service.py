from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.enums import WorkspaceRole
from app.models.event import Event
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.workspace import WorkspaceAuth


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CategoryRepository(session)

    async def create_defaults_for_event(self, event: Event) -> list[Category]:
        return await self.repo.create_defaults(event.id)

    async def list(self, event: Event) -> list[CategoryResponse]:
        categories = await self.repo.list_by_event(event.id)
        return [self._to_response(c) for c in categories]

    async def create(self, event: Event, data: CategoryCreate) -> CategoryResponse:
        category = await self.repo.create(
            event_id=event.id,
            name=data.name,
            sort_order=data.sort_order,
            allocated_budget=data.allocated_budget,
        )
        return self._to_response(category)

    async def get(self, event: Event, category_id: UUID) -> CategoryResponse:
        category = await self._get_or_404(event.id, category_id)
        return self._to_response(category)

    async def update(
        self,
        event: Event,
        category_id: UUID,
        data: CategoryUpdate,
    ) -> CategoryResponse:
        category = await self._get_or_404(event.id, category_id)

        if data.name is not None:
            category.name = data.name
        if data.sort_order is not None:
            category.sort_order = data.sort_order
        if data.allocated_budget is not None:
            category.allocated_budget = data.allocated_budget

        await self.session.flush()
        await self.session.refresh(category)
        return self._to_response(category)

    async def delete(
        self,
        auth: WorkspaceAuth,
        event: Event,
        category_id: UUID,
    ) -> None:
        self._require_roles(auth, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)
        category = await self._get_or_404(event.id, category_id)
        category.soft_delete()

    async def _get_or_404(self, event_id: UUID, category_id: UUID) -> Category:
        category = await self.repo.get_by_id(category_id, event_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        return category

    @staticmethod
    def _require_roles(auth: WorkspaceAuth, *roles: WorkspaceRole) -> None:
        if auth.membership.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action",
            )

    @staticmethod
    def _to_response(category: Category) -> CategoryResponse:
        return CategoryResponse(
            id=category.id,
            event_id=category.event_id,
            name=category.name,
            sort_order=category.sort_order,
            allocated_budget=category.allocated_budget,
            spent_balance=category.spent_balance,
            remaining_balance=category.remaining_balance,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )
