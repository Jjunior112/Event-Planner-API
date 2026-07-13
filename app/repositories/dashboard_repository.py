from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.checklist_item import ChecklistItem
from app.models.enums import InstallmentStatus, QuoteStatus
from app.models.event import Event
from app.models.payment import Payment, PaymentInstallment
from app.models.supplier_quote import SupplierQuote
from app.models.calendar_event import CalendarEvent
from datetime import datetime, UTC


class DashboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_categories(self, event_id: UUID) -> list[Category]:
        result = await self.session.execute(
            select(Category).where(
                Category.event_id == event_id,
                Category.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def get_quote_summary(self, event_id: UUID) -> dict:
        result = await self.session.execute(
            select(
                SupplierQuote.status,
                func.count(SupplierQuote.id),
                func.coalesce(func.sum(SupplierQuote.amount), 0),
            )
            .where(
                SupplierQuote.event_id == event_id,
                SupplierQuote.deleted_at.is_(None),
            )
            .group_by(SupplierQuote.status)
        )
        summary = {
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "pending_amount": Decimal("0"),
            "approved_amount": Decimal("0"),
        }
        for status, count, amount in result.all():
            key = status.value
            summary[key] = count
            if status == QuoteStatus.PENDING:
                summary["pending_amount"] = Decimal(str(amount))
            elif status == QuoteStatus.APPROVED:
                summary["approved_amount"] = Decimal(str(amount))
        return summary

    async def get_payment_summary(self, event_id: UUID) -> dict:
        payments_result = await self.session.execute(
            select(func.coalesce(func.sum(Payment.total_amount), 0)).where(
                Payment.event_id == event_id,
                Payment.deleted_at.is_(None),
            )
        )
        total_payments = Decimal(str(payments_result.scalar() or 0))

        paid_result = await self.session.execute(
            select(func.coalesce(func.sum(PaymentInstallment.amount), 0))
            .join(Payment, Payment.id == PaymentInstallment.payment_id)
            .where(
                Payment.event_id == event_id,
                Payment.deleted_at.is_(None),
                PaymentInstallment.deleted_at.is_(None),
                PaymentInstallment.status == InstallmentStatus.PAID,
            )
        )
        total_paid = Decimal(str(paid_result.scalar() or 0))

        overdue_result = await self.session.execute(
            select(func.count(PaymentInstallment.id))
            .join(Payment, Payment.id == PaymentInstallment.payment_id)
            .where(
                Payment.event_id == event_id,
                Payment.deleted_at.is_(None),
                PaymentInstallment.deleted_at.is_(None),
                PaymentInstallment.status == InstallmentStatus.PENDING,
                PaymentInstallment.due_date < datetime.now(UTC).date(),
            )
        )
        overdue = overdue_result.scalar() or 0

        return {
            "total_payments": total_payments,
            "total_paid": total_paid,
            "total_pending": total_payments - total_paid,
            "overdue_installments": overdue,
        }

    async def get_checklist_counts(self, event_id: UUID) -> tuple[int, int]:
        total_result = await self.session.execute(
            select(func.count(ChecklistItem.id)).where(
                ChecklistItem.event_id == event_id,
                ChecklistItem.deleted_at.is_(None),
            )
        )
        completed_result = await self.session.execute(
            select(func.count(ChecklistItem.id)).where(
                ChecklistItem.event_id == event_id,
                ChecklistItem.deleted_at.is_(None),
                ChecklistItem.is_completed.is_(True),
            )
        )
        return total_result.scalar() or 0, completed_result.scalar() or 0

    async def get_upcoming_calendar_count(self, event_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count(CalendarEvent.id)).where(
                CalendarEvent.event_id == event_id,
                CalendarEvent.deleted_at.is_(None),
                CalendarEvent.start_at >= datetime.now(UTC),
            )
        )
        return result.scalar() or 0
