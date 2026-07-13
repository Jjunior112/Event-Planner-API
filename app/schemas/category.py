import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sort_order: int = Field(default=0, ge=0)
    allocated_budget: Decimal | None = Field(default=None, ge=0)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    sort_order: int | None = Field(default=None, ge=0)
    allocated_budget: Decimal | None = Field(default=None, ge=0)


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    name: str
    sort_order: int
    allocated_budget: Decimal | None
    spent_balance: Decimal
    remaining_balance: Decimal | None
    created_at: datetime
    updated_at: datetime
