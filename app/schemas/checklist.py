import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ChecklistItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    due_date: date | None = None
    responsible_user_id: uuid.UUID | None = None
    sort_order: int = Field(default=0, ge=0)


class ChecklistItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_completed: bool | None = None
    due_date: date | None = None
    responsible_user_id: uuid.UUID | None = None
    sort_order: int | None = Field(default=None, ge=0)


class ChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    title: str
    description: str | None
    is_completed: bool
    due_date: date | None
    responsible_user_id: uuid.UUID | None
    responsible_user_name: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime
