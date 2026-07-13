from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import WorkspaceRole
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.repositories.workspace_repository import (
    WorkspaceMemberRepository,
    WorkspaceRepository,
)
from app.schemas.workspace import (
    WorkspaceAuth,
    WorkspaceCreate,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
    WorkspaceMemberUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)


class WorkspaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.workspace_repo = WorkspaceRepository(session)
        self.member_repo = WorkspaceMemberRepository(session)

    async def create(self, user: User, data: WorkspaceCreate) -> WorkspaceResponse:
        workspace = await self.workspace_repo.create(
            name=data.name,
            description=data.description,
        )
        await self.member_repo.create(
            workspace_id=workspace.id,
            user_id=user.id,
            role=WorkspaceRole.OWNER,
        )
        return WorkspaceResponse.model_validate(workspace)

    async def list_for_user(self, user: User) -> list[WorkspaceResponse]:
        workspaces = await self.workspace_repo.list_by_user(user.id)
        return [WorkspaceResponse.model_validate(w) for w in workspaces]

    async def get(self, auth: WorkspaceAuth) -> WorkspaceResponse:
        return WorkspaceResponse.model_validate(auth.workspace)

    async def update(
        self,
        auth: WorkspaceAuth,
        data: WorkspaceUpdate,
    ) -> WorkspaceResponse:
        self._require_roles(auth, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)

        workspace = auth.workspace
        if data.name is not None:
            workspace.name = data.name
        if data.description is not None:
            workspace.description = data.description

        await self.session.flush()
        await self.session.refresh(workspace)
        return WorkspaceResponse.model_validate(workspace)

    async def delete(self, auth: WorkspaceAuth) -> None:
        self._require_roles(auth, WorkspaceRole.OWNER)
        auth.workspace.soft_delete()

    async def list_members(self, auth: WorkspaceAuth) -> list[WorkspaceMemberResponse]:
        members = await self.member_repo.list_by_workspace(auth.workspace.id)
        return [self._to_member_response(m) for m in members]

    async def add_member(
        self,
        auth: WorkspaceAuth,
        data: WorkspaceMemberCreate,
    ) -> WorkspaceMemberResponse:
        self._require_roles(auth, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)

        if data.role == WorkspaceRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign owner role directly. Transfer ownership instead.",
            )

        from app.services.plan_limit_service import PlanLimitService

        limit_service = PlanLimitService(self.session)
        await limit_service.check_members_limit(auth.workspace)

        target_user = await self.member_repo.get_user_by_email(data.email)
        if target_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        existing = await self.member_repo.get_membership(
            auth.workspace.id,
            target_user.id,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this workspace",
            )

        member = await self.member_repo.create(
            workspace_id=auth.workspace.id,
            user_id=target_user.id,
            role=data.role,
        )
        member.user = target_user
        return self._to_member_response(member)

    async def update_member(
        self,
        auth: WorkspaceAuth,
        member_id: UUID,
        data: WorkspaceMemberUpdate,
    ) -> WorkspaceMemberResponse:
        self._require_roles(auth, WorkspaceRole.OWNER)

        member = await self._get_member_in_workspace(auth.workspace.id, member_id)

        if member.role == WorkspaceRole.OWNER and data.role != WorkspaceRole.OWNER:
            owners = await self.member_repo.count_owners(auth.workspace.id)
            if owners <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot change role of the last owner",
                )

        if data.role == WorkspaceRole.OWNER and member.role != WorkspaceRole.OWNER:
            auth.membership.role = WorkspaceRole.ADMIN

        member.role = data.role
        await self.session.flush()
        await self.session.refresh(member)
        return self._to_member_response(member)

    async def remove_member(self, auth: WorkspaceAuth, member_id: UUID) -> None:
        self._require_roles(auth, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)

        member = await self._get_member_in_workspace(auth.workspace.id, member_id)

        if member.user_id == auth.membership.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove yourself. Leave the workspace instead.",
            )

        if member.role == WorkspaceRole.OWNER:
            owners = await self.member_repo.count_owners(auth.workspace.id)
            if owners <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last owner",
                )

        if (
            auth.membership.role == WorkspaceRole.ADMIN
            and member.role == WorkspaceRole.ADMIN
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admins cannot remove other admins",
            )

        member.soft_delete()

    async def _get_member_in_workspace(
        self,
        workspace_id: UUID,
        member_id: UUID,
    ) -> WorkspaceMember:
        member = await self.member_repo.get_by_id(member_id)
        if member is None or member.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            )
        return member

    @staticmethod
    def _require_roles(auth: WorkspaceAuth, *roles: WorkspaceRole) -> None:
        if auth.membership.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action",
            )

    @staticmethod
    def _to_member_response(member: WorkspaceMember) -> WorkspaceMemberResponse:
        return WorkspaceMemberResponse(
            id=member.id,
            workspace_id=member.workspace_id,
            user_id=member.user_id,
            role=member.role,
            user_email=member.user.email,
            user_full_name=member.user.full_name,
            created_at=member.created_at,
        )
