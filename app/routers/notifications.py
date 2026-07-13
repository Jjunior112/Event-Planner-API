from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_workspace
from app.models.user import User
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.schemas.workspace import WorkspaceAuth
from app.services.notification_service import NotificationService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/notifications",
    tags=["Notifications"],
)


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    auth: WorkspaceAuth = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    service = NotificationService(session)
    return await service.list_for_user(auth, current_user)


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    data: NotificationCreate,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    service = NotificationService(session)
    return await service.create(auth, data)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    service = NotificationService(session)
    return await service.mark_read(auth, current_user, notification_id)
