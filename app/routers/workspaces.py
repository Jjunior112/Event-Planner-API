from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_workspace
from app.models.user import User
from app.schemas.workspace import (
    WorkspaceAuth,
    WorkspaceCreate,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
    WorkspaceMemberUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    service = WorkspaceService(session)
    return await service.create(current_user, data)


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[WorkspaceResponse]:
    service = WorkspaceService(session)
    return await service.list_for_user(current_user)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    service = WorkspaceService(session)
    return await service.get(auth)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    data: WorkspaceUpdate,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    service = WorkspaceService(session)
    return await service.update(auth, data)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = WorkspaceService(session)
    await service.delete(auth)


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
async def list_members(
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> list[WorkspaceMemberResponse]:
    service = WorkspaceService(session)
    return await service.list_members(auth)


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    data: WorkspaceMemberCreate,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> WorkspaceMemberResponse:
    service = WorkspaceService(session)
    return await service.add_member(auth, data)


@router.patch(
    "/{workspace_id}/members/{member_id}",
    response_model=WorkspaceMemberResponse,
)
async def update_member(
    member_id: UUID,
    data: WorkspaceMemberUpdate,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> WorkspaceMemberResponse:
    service = WorkspaceService(session)
    return await service.update_member(auth, member_id, data)


@router.delete(
    "/{workspace_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_member(
    member_id: UUID,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = WorkspaceService(session)
    await service.remove_member(auth, member_id)
