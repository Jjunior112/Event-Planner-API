from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import WorkspaceRole
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit_log import AuditLogResponse
from app.schemas.workspace import WorkspaceAuth


class AuditLogService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = AuditLogRepository(session)

    async def list(
        self,
        auth: WorkspaceAuth,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLogResponse]:
        self._require_roles(auth, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)
        logs = await self.repo.list_by_workspace(auth.workspace.id, limit, offset)
        return [
            AuditLogResponse(
                id=log.id,
                workspace_id=log.workspace_id,
                user_id=log.user_id,
                user_email=log.user.email,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                action=log.action,
                changes=log.changes,
                created_at=log.created_at,
            )
            for log in logs
        ]

    @staticmethod
    def _require_roles(auth: WorkspaceAuth, *roles: WorkspaceRole) -> None:
        if auth.membership.role not in roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action",
            )
