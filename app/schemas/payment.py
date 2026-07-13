import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InstallmentStatus, PaymentStatus


class InstallmentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    due_date: date


class PaymentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    total_amount: Decimal = Field(gt=0)
    installments: list[InstallmentCreate] = Field(min_length=1)


class PaymentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class InstallmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    payment_id: uuid.UUID
    amount: Decimal
    due_date: date
    paid_at: datetime | None
    status: InstallmentStatus
    created_at: datetime


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    category_id: uuid.UUID | None
    supplier_id: uuid.UUID | None
    title: str
    description: str | None
    total_amount: Decimal
    status: PaymentStatus
    installments: list[InstallmentResponse]
    created_at: datetime
    updated_at: datetime
