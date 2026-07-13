import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CategoryFinancialSummary(BaseModel):
    id: uuid.UUID
    name: str
    allocated_budget: Decimal | None
    spent_balance: Decimal
    remaining_balance: Decimal | None


class QuoteStatusSummary(BaseModel):
    pending: int
    approved: int
    rejected: int
    pending_amount: Decimal
    approved_amount: Decimal


class PaymentSummary(BaseModel):
    total_payments: Decimal
    total_paid: Decimal
    total_pending: Decimal
    overdue_installments: int


class EventDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: uuid.UUID
    event_name: str
    event_date: date
    total_budget: Decimal | None
    total_allocated: Decimal
    total_spent: Decimal
    total_remaining: Decimal | None
    quotes: QuoteStatusSummary
    payments: PaymentSummary
    categories: list[CategoryFinancialSummary]
    checklist_total: int
    checklist_completed: int
    calendar_upcoming: int
