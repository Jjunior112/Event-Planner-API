from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.default_categories import DEFAULT_CATEGORIES
from app.models.category import Category


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, category_id: UUID, event_id: UUID) -> Category | None:
        result = await self.session.execute(
            select(Category).where(
                Category.id == category_id,
                Category.event_id == event_id,
                Category.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_event(self, event_id: UUID) -> list[Category]:
        result = await self.session.execute(
            select(Category)
            .where(
                Category.event_id == event_id,
                Category.deleted_at.is_(None),
            )
            .order_by(Category.sort_order.asc(), Category.name.asc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        event_id: UUID,
        name: str,
        sort_order: int = 0,
        allocated_budget: Decimal | None = None,
    ) -> Category:
        category = Category(
            event_id=event_id,
            name=name,
            sort_order=sort_order,
            allocated_budget=allocated_budget,
        )
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def create_defaults(self, event_id: UUID) -> list[Category]:
        categories = []
        for item in DEFAULT_CATEGORIES:
            category = Category(
                event_id=event_id,
                name=str(item["name"]),
                sort_order=int(item["sort_order"]),
            )
            self.session.add(category)
            categories.append(category)
        await self.session.flush()
        for category in categories:
            await self.session.refresh(category)
        return categories

    async def update_spent_balance(
        self,
        category_id: UUID,
        delta: Decimal,
    ) -> Category | None:
        result = await self.session.execute(
            select(Category).where(
                Category.id == category_id,
                Category.deleted_at.is_(None),
            )
        )
        category = result.scalar_one_or_none()
        if category is None:
            return None
        category.spent_balance += delta
        await self.session.flush()
        await self.session.refresh(category)
        return category
