from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        workspace_id: UUID,
        user_id: UUID,
        entity_type: str,
        entity_id: UUID,
        action: str,
        changes: dict[str, Any] | None = None,
    ) -> AuditLog:
        log = AuditLog(
            workspace_id=workspace_id,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changes=changes,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_by_workspace(
        self,
        workspace_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        result = await self.session.execute(
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .where(AuditLog.workspace_id == workspace_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
