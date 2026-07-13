import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.enums import (
    NotificationChannel,
    NotificationStatus,
    NotificationType,
    WorkspaceRole,
)
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.repositories.workspace_repository import WorkspaceMemberRepository
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.schemas.workspace import WorkspaceAuth

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = NotificationRepository(session)
        self.member_repo = WorkspaceMemberRepository(session)
        self.settings = get_settings()

    async def list_for_user(
        self,
        auth: WorkspaceAuth,
        user: User,
    ) -> list[NotificationResponse]:
        notifications = await self.repo.list_by_user(auth.workspace.id, user.id)
        return [NotificationResponse.model_validate(n) for n in notifications]

    async def create(
        self,
        auth: WorkspaceAuth,
        data: NotificationCreate,
    ) -> NotificationResponse:
        self._require_roles(auth, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)
        membership = await self.member_repo.get_membership(
            auth.workspace.id, data.user_id
        )
        if membership is None:
            raise HTTPException(400, "Target user is not a workspace member")

        notification = await self.repo.create(
            workspace_id=auth.workspace.id,
            user_id=data.user_id,
            type=data.type,
            channel=data.channel,
            title=data.title,
            message=data.message,
            scheduled_at=data.scheduled_at,
            status=NotificationStatus.PENDING,
        )

        if data.channel == NotificationChannel.EMAIL and data.scheduled_at is None:
            await self._send_email(notification)

        return NotificationResponse.model_validate(notification)

    async def mark_read(
        self,
        auth: WorkspaceAuth,
        user: User,
        notification_id: UUID,
    ) -> NotificationResponse:
        notification = await self.repo.get_by_id(notification_id, auth.workspace.id)
        if notification is None:
            raise HTTPException(404, "Notification not found")
        if notification.user_id != user.id:
            raise HTTPException(403, "Not your notification")

        notification.status = NotificationStatus.READ
        await self.session.flush()
        await self.session.refresh(notification)
        return NotificationResponse.model_validate(notification)

    async def process_pending(self) -> int:
        """Processa notificações agendadas pendentes. Retorna quantidade enviada."""
        pending = await self.repo.list_pending_scheduled(datetime.now(UTC))
        sent = 0
        for notification in pending:
            if notification.channel == NotificationChannel.EMAIL:
                success = await self._send_email(notification)
                if success:
                    sent += 1
            else:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.now(UTC)
                sent += 1
        await self.session.flush()
        return sent

    async def _send_email(self, notification) -> bool:
        if not self.settings.smtp_enabled:
            logger.info(
                "SMTP disabled — notification %s queued as sent (stub)",
                notification.id,
            )
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(UTC)
            return True

        try:
            import smtplib
            from email.mime.text import MIMEText

            msg = MIMEText(notification.message)
            msg["Subject"] = notification.title
            msg["From"] = self.settings.smtp_from_email
            msg["To"] = notification.user.email

            with smtplib.SMTP(
                self.settings.smtp_host, self.settings.smtp_port
            ) as server:
                if self.settings.smtp_use_tls:
                    server.starttls()
                if self.settings.smtp_user and self.settings.smtp_password:
                    server.login(self.settings.smtp_user, self.settings.smtp_password)
                server.send_message(msg)

            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(UTC)
            return True
        except Exception:
            logger.exception("Failed to send email for notification %s", notification.id)
            notification.status = NotificationStatus.FAILED
            return False

    @staticmethod
    def _require_roles(auth: WorkspaceAuth, *roles: WorkspaceRole) -> None:
        if auth.membership.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
