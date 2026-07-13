import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import QuoteStatus


class SupplierQuoteCreate(BaseModel):
    category_id: uuid.UUID
    supplier_id: uuid.UUID
    amount: Decimal = Field(gt=0)
    description: str | None = None


class SupplierQuoteUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    description: str | None = None


class SupplierQuoteStatusUpdate(BaseModel):
    status: QuoteStatus


class SupplierQuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    category_id: uuid.UUID
    supplier_id: uuid.UUID
    amount: Decimal
    description: str | None
    status: QuoteStatus
    category_name: str
    supplier_name: str
    created_at: datetime
    updated_at: datetime
