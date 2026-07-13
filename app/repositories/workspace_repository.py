from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import WorkspaceRole
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, workspace_id: UUID) -> Workspace | None:
        result = await self.session.execute(
            select(Workspace).where(
                Workspace.id == workspace_id,
                Workspace.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID) -> list[Workspace]:
        result = await self.session.execute(
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.deleted_at.is_(None),
                Workspace.deleted_at.is_(None),
            )
            .order_by(Workspace.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def create(self, name: str, description: str | None) -> Workspace:
        workspace = Workspace(name=name, description=description)
        self.session.add(workspace)
        await self.session.flush()
        await self.session.refresh(workspace)
        return workspace


class WorkspaceMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_membership(
        self,
        workspace_id: UUID,
        user_id: UUID,
    ) -> WorkspaceMember | None:
        result = await self.session.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, member_id: UUID) -> WorkspaceMember | None:
        result = await self.session.execute(
            select(WorkspaceMember)
            .options(selectinload(WorkspaceMember.user))
            .where(
                WorkspaceMember.id == member_id,
                WorkspaceMember.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(self, workspace_id: UUID) -> list[WorkspaceMember]:
        result = await self.session.execute(
            select(WorkspaceMember)
            .options(selectinload(WorkspaceMember.user))
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.deleted_at.is_(None),
            )
            .order_by(WorkspaceMember.created_at.asc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        workspace_id: UUID,
        user_id: UUID,
        role: WorkspaceRole,
    ) -> WorkspaceMember:
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
        )
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def count_owners(self, workspace_id: UUID) -> int:
        result = await self.session.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == WorkspaceRole.OWNER,
                WorkspaceMember.deleted_at.is_(None),
            )
        )
        return len(result.scalars().all())

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()
