from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier import Supplier


class SupplierRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, supplier_id: UUID, workspace_id: UUID) -> Supplier | None:
        result = await self.session.execute(
            select(Supplier).where(
                Supplier.id == supplier_id,
                Supplier.workspace_id == workspace_id,
                Supplier.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(self, workspace_id: UUID) -> list[Supplier]:
        result = await self.session.execute(
            select(Supplier)
            .where(
                Supplier.workspace_id == workspace_id,
                Supplier.deleted_at.is_(None),
            )
            .order_by(Supplier.name.asc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        workspace_id: UUID,
        name: str,
        contact_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        notes: str | None = None,
    ) -> Supplier:
        supplier = Supplier(
            workspace_id=workspace_id,
            name=name,
            contact_name=contact_name,
            email=email,
            phone=phone,
            notes=notes,
        )
        self.session.add(supplier)
        await self.session.flush()
        await self.session.refresh(supplier)
        return supplier
