from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.plan_limits import PLAN_LIMITS, is_unlimited
from app.core.plan_exceptions import PlanLimitExceeded
from app.models.contract import Contract
from app.models.event import Event
from app.models.workspace import Workspace, WorkspaceMember
from app.repositories.workspace_repository import WorkspaceMemberRepository


class PlanLimitService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.member_repo = WorkspaceMemberRepository(session)

    async def check_events_limit(self, workspace: Workspace) -> None:
        limits = PLAN_LIMITS[workspace.plan]
        if is_unlimited(limits.max_events):
            return

        result = await self.session.execute(
            select(func.count(Event.id)).where(
                Event.workspace_id == workspace.id,
                Event.deleted_at.is_(None),
            )
        )
        count = result.scalar() or 0
        if count >= limits.max_events:
            raise PlanLimitExceeded(
                "events",
                workspace.plan,
                f"Seu plano {workspace.plan.value} permite até {limits.max_events} evento(s). "
                "Faça upgrade para criar mais eventos.",
            )

    async def check_members_limit(self, workspace: Workspace) -> None:
        limits = PLAN_LIMITS[workspace.plan]
        if is_unlimited(limits.max_members):
            return

        result = await self.session.execute(
            select(func.count(WorkspaceMember.id)).where(
                WorkspaceMember.workspace_id == workspace.id,
                WorkspaceMember.deleted_at.is_(None),
            )
        )
        count = result.scalar() or 0
        if count >= limits.max_members:
            raise PlanLimitExceeded(
                "members",
                workspace.plan,
                f"Seu plano {workspace.plan.value} permite até {limits.max_members} membro(s). "
                "Faça upgrade para convidar mais pessoas.",
            )

    async def check_storage_limit(
        self,
        workspace: Workspace,
        additional_bytes: int = 0,
    ) -> None:
        limits = PLAN_LIMITS[workspace.plan]
        max_bytes = limits.max_storage_mb * 1024 * 1024
        if workspace.storage_used_bytes + additional_bytes > max_bytes:
            raise PlanLimitExceeded(
                "storage",
                workspace.plan,
                f"Limite de armazenamento do plano {workspace.plan.value} "
                f"({limits.max_storage_mb} MB) atingido. Faça upgrade para continuar.",
            )

    async def add_storage_usage(self, workspace_id: UUID, bytes_added: int) -> None:
        result = await self.session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        workspace = result.scalar_one_or_none()
        if workspace:
            workspace.storage_used_bytes += bytes_added

    async def remove_storage_usage(self, workspace_id: UUID, bytes_removed: int) -> None:
        result = await self.session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        workspace = result.scalar_one_or_none()
        if workspace:
            workspace.storage_used_bytes = max(
                0, workspace.storage_used_bytes - bytes_removed
            )

    async def get_usage(self, workspace: Workspace) -> dict:
        events_result = await self.session.execute(
            select(func.count(Event.id)).where(
                Event.workspace_id == workspace.id,
                Event.deleted_at.is_(None),
            )
        )
        members_result = await self.session.execute(
            select(func.count(WorkspaceMember.id)).where(
                WorkspaceMember.workspace_id == workspace.id,
                WorkspaceMember.deleted_at.is_(None),
            )
        )
        return {
            "events_count": events_result.scalar() or 0,
            "members_count": members_result.scalar() or 0,
            "storage_used_bytes": workspace.storage_used_bytes,
        }
