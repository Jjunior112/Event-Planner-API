from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_workspace
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate
from app.schemas.workspace import WorkspaceAuth
from app.services.supplier_service import SupplierService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/suppliers",
    tags=["Suppliers"],
)


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    data: SupplierCreate,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> SupplierResponse:
    service = SupplierService(session)
    return await service.create(auth, data)


@router.get("", response_model=list[SupplierResponse])
async def list_suppliers(
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> list[SupplierResponse]:
    service = SupplierService(session)
    return await service.list(auth)


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: UUID,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> SupplierResponse:
    service = SupplierService(session)
    return await service.get(auth, supplier_id)


@router.patch("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: UUID,
    data: SupplierUpdate,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> SupplierResponse:
    service = SupplierService(session)
    return await service.update(auth, supplier_id, data)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: UUID,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = SupplierService(session)
    await service.delete(auth, supplier_id)
