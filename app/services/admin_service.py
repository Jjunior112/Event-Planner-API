from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PlanStatus, WorkspacePlan
from app.models.user import User
from app.models.workspace import Workspace
from app.repositories.workspace_repository import WorkspaceRepository


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_stats(self) -> dict:
        users = await self.session.execute(
            select(func.count(User.id)).where(User.deleted_at.is_(None))
        )
        workspaces = await self.session.execute(
            select(func.count(Workspace.id)).where(Workspace.deleted_at.is_(None))
        )
        active_subs = await self.session.execute(
            select(func.count(Workspace.id)).where(
                Workspace.deleted_at.is_(None),
                Workspace.plan != WorkspacePlan.FREE,
                Workspace.plan_status == PlanStatus.ACTIVE,
            )
        )
        by_plan = await self.session.execute(
            select(Workspace.plan, func.count(Workspace.id))
            .where(Workspace.deleted_at.is_(None))
            .group_by(Workspace.plan)
        )
        return {
            "total_users": users.scalar() or 0,
            "total_workspaces": workspaces.scalar() or 0,
            "active_subscriptions": active_subs.scalar() or 0,
            "workspaces_by_plan": {
                plan.value: count for plan, count in by_plan.all()
            },
        }

    async def list_workspaces(self, limit: int = 50, offset: int = 0) -> list[dict]:
        result = await self.session.execute(
            select(Workspace)
            .where(Workspace.deleted_at.is_(None))
            .order_by(Workspace.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        workspaces = result.scalars().all()
        return [
            {
                "id": str(ws.id),
                "name": ws.name,
                "plan": ws.plan.value,
                "plan_status": ws.plan_status.value,
                "storage_used_bytes": ws.storage_used_bytes,
                "created_at": ws.created_at.isoformat(),
            }
            for ws in workspaces
        ]

    async def list_users(self, limit: int = 50, offset: int = 0) -> list[dict]:
        result = await self.session.execute(
            select(User)
            .where(User.deleted_at.is_(None))
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        users = result.scalars().all()
        return [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "is_active": u.is_active,
                "is_superadmin": u.is_superadmin,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ]
