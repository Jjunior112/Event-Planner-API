import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    event_date: date
    location: str | None = Field(default=None, max_length=500)
    budget: Decimal | None = Field(default=None, ge=0)


class EventUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    event_date: date | None = None
    location: str | None = Field(default=None, max_length=500)
    budget: Decimal | None = Field(default=None, ge=0)


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    event_date: date
    location: str | None
    budget: Decimal | None
    created_at: datetime
    updated_at: datetime
