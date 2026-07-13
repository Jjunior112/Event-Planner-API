from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AuditLogRepository(session)

    async def log(
        self,
        workspace_id: UUID,
        user: User,
        entity_type: str,
        entity_id: UUID,
        action: str,
        changes: dict[str, Any] | None = None,
    ) -> None:
        await self.repo.create(
            workspace_id=workspace_id,
            user_id=user.id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changes=changes,
        )
