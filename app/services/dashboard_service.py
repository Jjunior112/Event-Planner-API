from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import (
    CategoryFinancialSummary,
    EventDashboardResponse,
    PaymentSummary,
    QuoteStatusSummary,
)


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = DashboardRepository(session)

    async def get_event_dashboard(self, event: Event) -> EventDashboardResponse:
        categories = await self.repo.get_categories(event.id)
        quote_data = await self.repo.get_quote_summary(event.id)
        payment_data = await self.repo.get_payment_summary(event.id)
        checklist_total, checklist_completed = await self.repo.get_checklist_counts(
            event.id
        )
        calendar_upcoming = await self.repo.get_upcoming_calendar_count(event.id)

        total_allocated = sum(
            (c.allocated_budget or Decimal("0")) for c in categories
        )
        total_spent = sum(c.spent_balance for c in categories)

        total_remaining = None
        if event.budget is not None:
            total_remaining = event.budget - total_spent

        category_summaries = [
            CategoryFinancialSummary(
                id=c.id,
                name=c.name,
                allocated_budget=c.allocated_budget,
                spent_balance=c.spent_balance,
                remaining_balance=c.remaining_balance,
            )
            for c in categories
        ]

        return EventDashboardResponse(
            event_id=event.id,
            event_name=event.name,
            event_date=event.event_date,
            total_budget=event.budget,
            total_allocated=total_allocated,
            total_spent=total_spent,
            total_remaining=total_remaining,
            quotes=QuoteStatusSummary(**quote_data),
            payments=PaymentSummary(**payment_data),
            categories=category_summaries,
            checklist_total=checklist_total,
            checklist_completed=checklist_completed,
            calendar_upcoming=calendar_upcoming,
        )
