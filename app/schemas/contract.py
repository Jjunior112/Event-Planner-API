import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    supplier_id: uuid.UUID | None
    title: str
    original_filename: str
    file_size: int
    mime_type: str
    created_at: datetime
    updated_at: datetime


class ContractUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    supplier_id: uuid.UUID | None = None
