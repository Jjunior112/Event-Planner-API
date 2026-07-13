from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import QuoteStatus, WorkspaceRole
from app.models.event import Event
from app.models.supplier_quote import SupplierQuote
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.supplier_quote_repository import SupplierQuoteRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.supplier_quote import (
    SupplierQuoteCreate,
    SupplierQuoteResponse,
    SupplierQuoteStatusUpdate,
    SupplierQuoteUpdate,
)
from app.schemas.workspace import WorkspaceAuth
from app.services.audit_service import AuditService

ALLOWED_TRANSITIONS: dict[QuoteStatus, set[QuoteStatus]] = {
    QuoteStatus.PENDING: {QuoteStatus.APPROVED, QuoteStatus.REJECTED},
    QuoteStatus.APPROVED: {QuoteStatus.REJECTED},
    QuoteStatus.REJECTED: {QuoteStatus.APPROVED},
}


class SupplierQuoteService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = SupplierQuoteRepository(session)
        self.category_repo = CategoryRepository(session)
        self.supplier_repo = SupplierRepository(session)
        self.audit = AuditService(session)

    async def create(
        self,
        event: Event,
        data: SupplierQuoteCreate,
    ) -> SupplierQuoteResponse:
        category = await self.category_repo.get_by_id(data.category_id, event.id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found in this event",
            )

        supplier = await self.supplier_repo.get_by_id(
            data.supplier_id,
            event.workspace_id,
        )
        if supplier is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found in this workspace",
            )

        quote = await self.repo.create(
            event_id=event.id,
            category_id=data.category_id,
            supplier_id=data.supplier_id,
            amount=data.amount,
            description=data.description,
        )
        quote.category = category
        quote.supplier = supplier
        return self._to_response(quote)

    async def list(self, event: Event) -> list[SupplierQuoteResponse]:
        quotes = await self.repo.list_by_event(event.id)
        return [self._to_response(q) for q in quotes]

    async def get(self, event: Event, quote_id: UUID) -> SupplierQuoteResponse:
        quote = await self._get_or_404(event.id, quote_id)
        return self._to_response(quote)

    async def update(
        self,
        event: Event,
        quote_id: UUID,
        data: SupplierQuoteUpdate,
    ) -> SupplierQuoteResponse:
        quote = await self._get_or_404(event.id, quote_id)

        if quote.status != QuoteStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending quotes can be updated",
            )

        if data.amount is not None:
            quote.amount = data.amount
        if data.description is not None:
            quote.description = data.description

        await self.session.flush()
        await self.session.refresh(quote)
        return self._to_response(quote)

    async def update_status(
        self,
        auth: WorkspaceAuth,
        event: Event,
        user: User,
        quote_id: UUID,
        data: SupplierQuoteStatusUpdate,
    ) -> SupplierQuoteResponse:
        self._require_roles(auth, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)

        quote = await self._get_or_404(event.id, quote_id)
        new_status = data.status

        if new_status == quote.status:
            return self._to_response(quote)

        allowed = ALLOWED_TRANSITIONS.get(quote.status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from {quote.status.value} to {new_status.value}",
            )

        old_status = quote.status
        await self._apply_balance_change(quote, old_status, new_status)

        quote.status = new_status
        await self.session.flush()
        await self.session.refresh(quote)
        await self.audit.log(
            auth.workspace.id,
            user,
            "supplier_quote",
            quote.id,
            "status_changed",
            {"from": old_status.value, "to": new_status.value, "amount": str(quote.amount)},
        )
        return self._to_response(quote)

    async def delete(
        self,
        auth: WorkspaceAuth,
        event: Event,
        quote_id: UUID,
    ) -> None:
        self._require_roles(auth, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)
        quote = await self._get_or_404(event.id, quote_id)

        if quote.status == QuoteStatus.APPROVED:
            await self._apply_balance_change(
                quote,
                QuoteStatus.APPROVED,
                QuoteStatus.REJECTED,
            )

        quote.soft_delete()

    async def _apply_balance_change(
        self,
        quote: SupplierQuote,
        old_status: QuoteStatus,
        new_status: QuoteStatus,
    ) -> None:
        delta = Decimal("0")

        if old_status != QuoteStatus.APPROVED and new_status == QuoteStatus.APPROVED:
            delta = quote.amount
        elif old_status == QuoteStatus.APPROVED and new_status != QuoteStatus.APPROVED:
            delta = -quote.amount

        if delta != 0:
            category = await self.category_repo.update_spent_balance(
                quote.category_id,
                delta,
            )
            if category is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found",
                )

    async def _get_or_404(self, event_id: UUID, quote_id: UUID) -> SupplierQuote:
        quote = await self.repo.get_by_id(quote_id, event_id)
        if quote is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found",
            )
        return quote

    @staticmethod
    def _require_roles(auth: WorkspaceAuth, *roles: WorkspaceRole) -> None:
        if auth.membership.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action",
            )

    @staticmethod
    def _to_response(quote: SupplierQuote) -> SupplierQuoteResponse:
        return SupplierQuoteResponse(
            id=quote.id,
            event_id=quote.event_id,
            category_id=quote.category_id,
            supplier_id=quote.supplier_id,
            amount=quote.amount,
            description=quote.description,
            status=quote.status,
            category_name=quote.category.name,
            supplier_name=quote.supplier.name,
            created_at=quote.created_at,
            updated_at=quote.updated_at,
        )
