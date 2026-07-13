from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import WorkspaceRole
from app.models.supplier import Supplier
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate
from app.schemas.workspace import WorkspaceAuth


class SupplierService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = SupplierRepository(session)

    async def create(self, auth: WorkspaceAuth, data: SupplierCreate) -> SupplierResponse:
        supplier = await self.repo.create(
            workspace_id=auth.workspace.id,
            name=data.name,
            contact_name=data.contact_name,
            email=str(data.email) if data.email else None,
            phone=data.phone,
            notes=data.notes,
        )
        return SupplierResponse.model_validate(supplier)

    async def list(self, auth: WorkspaceAuth) -> list[SupplierResponse]:
        suppliers = await self.repo.list_by_workspace(auth.workspace.id)
        return [SupplierResponse.model_validate(s) for s in suppliers]

    async def get(self, auth: WorkspaceAuth, supplier_id: UUID) -> SupplierResponse:
        supplier = await self._get_or_404(auth.workspace.id, supplier_id)
        return SupplierResponse.model_validate(supplier)

    async def update(
        self,
        auth: WorkspaceAuth,
        supplier_id: UUID,
        data: SupplierUpdate,
    ) -> SupplierResponse:
        supplier = await self._get_or_404(auth.workspace.id, supplier_id)

        if data.name is not None:
            supplier.name = data.name
        if data.contact_name is not None:
            supplier.contact_name = data.contact_name
        if data.email is not None:
            supplier.email = str(data.email)
        if data.phone is not None:
            supplier.phone = data.phone
        if data.notes is not None:
            supplier.notes = data.notes

        await self.session.flush()
        await self.session.refresh(supplier)
        return SupplierResponse.model_validate(supplier)

    async def delete(self, auth: WorkspaceAuth, supplier_id: UUID) -> None:
        self._require_roles(auth, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)
        supplier = await self._get_or_404(auth.workspace.id, supplier_id)
        supplier.soft_delete()

    async def _get_or_404(self, workspace_id: UUID, supplier_id: UUID) -> Supplier:
        supplier = await self.repo.get_by_id(supplier_id, workspace_id)
        if supplier is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found",
            )
        return supplier

    @staticmethod
    def _require_roles(auth: WorkspaceAuth, *roles: WorkspaceRole) -> None:
        if auth.membership.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action",
            )
