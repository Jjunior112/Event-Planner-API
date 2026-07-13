from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import QuoteStatus
from app.models.supplier_quote import SupplierQuote


class SupplierQuoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, quote_id: UUID, event_id: UUID) -> SupplierQuote | None:
        result = await self.session.execute(
            select(SupplierQuote)
            .options(
                selectinload(SupplierQuote.category),
                selectinload(SupplierQuote.supplier),
            )
            .where(
                SupplierQuote.id == quote_id,
                SupplierQuote.event_id == event_id,
                SupplierQuote.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_event(self, event_id: UUID) -> list[SupplierQuote]:
        result = await self.session.execute(
            select(SupplierQuote)
            .options(
                selectinload(SupplierQuote.category),
                selectinload(SupplierQuote.supplier),
            )
            .where(
                SupplierQuote.event_id == event_id,
                SupplierQuote.deleted_at.is_(None),
            )
            .order_by(SupplierQuote.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        event_id: UUID,
        category_id: UUID,
        supplier_id: UUID,
        amount,
        description: str | None = None,
    ) -> SupplierQuote:
        quote = SupplierQuote(
            event_id=event_id,
            category_id=category_id,
            supplier_id=supplier_id,
            amount=amount,
            description=description,
            status=QuoteStatus.PENDING,
        )
        self.session.add(quote)
        await self.session.flush()
        await self.session.refresh(quote)
        return quote
