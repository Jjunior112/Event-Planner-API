import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import NotificationChannel, NotificationStatus, NotificationType


class NotificationCreate(BaseModel):
    user_id: uuid.UUID
    type: NotificationType = NotificationType.GENERAL
    channel: NotificationChannel = NotificationChannel.IN_APP
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1)
    scheduled_at: datetime | None = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    type: NotificationType
    channel: NotificationChannel
    title: str
    message: str
    status: NotificationStatus
    scheduled_at: datetime | None
    sent_at: datetime | None
    created_at: datetime
