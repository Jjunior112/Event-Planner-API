from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_superadmin
from app.models.user import User
from app.schemas.admin import AdminStatsResponse, AdminUserItem, AdminWorkspaceItem
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def admin_stats(
    _: User = Depends(get_superadmin),
    session: AsyncSession = Depends(get_db),
) -> AdminStatsResponse:
    service = AdminService(session)
    return AdminStatsResponse(**await service.get_stats())


@router.get("/workspaces", response_model=list[AdminWorkspaceItem])
async def admin_workspaces(
    _: User = Depends(get_superadmin),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AdminWorkspaceItem]:
    service = AdminService(session)
    items = await service.list_workspaces(limit, offset)
    return [AdminWorkspaceItem(**i) for i in items]


@router.get("/users", response_model=list[AdminUserItem])
async def admin_users(
    _: User = Depends(get_superadmin),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AdminUserItem]:
    service = AdminService(session)
    items = await service.list_users(limit, offset)
    return [AdminUserItem(**i) for i in items]
