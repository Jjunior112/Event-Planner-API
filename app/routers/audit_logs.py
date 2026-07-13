from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_workspace
from app.schemas.audit_log import AuditLogResponse
from app.schemas.workspace import WorkspaceAuth
from app.services.audit_log_service import AuditLogService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/audit-logs",
    tags=["Audit"],
)


@router.get("", response_model=list[AuditLogResponse])
async def list_audit_logs(
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AuditLogResponse]:
    service = AuditLogService(session)
    return await service.list(auth, limit, offset)
