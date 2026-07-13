from fastapi import HTTPException, status

from app.models.enums import WorkspacePlan
from app.schemas.workspace import WorkspaceAuth


class PlanLimitExceeded(HTTPException):
    def __init__(self, limit_type: str, plan: WorkspacePlan, message: str) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "plan_limit_exceeded",
                "limit_type": limit_type,
                "current_plan": plan.value,
                "message": message,
            },
        )


def require_write_access(auth: WorkspaceAuth) -> None:
    from app.models.enums import WorkspaceRole

    if auth.membership.role == WorkspaceRole.VIEWER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewers have read-only access",
        )
