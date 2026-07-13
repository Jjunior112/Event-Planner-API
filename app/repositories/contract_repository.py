from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contract import Contract


class ContractRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, contract_id: UUID, event_id: UUID) -> Contract | None:
        result = await self.session.execute(
            select(Contract).where(
                Contract.id == contract_id,
                Contract.event_id == event_id,
                Contract.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_event(self, event_id: UUID) -> list[Contract]:
        result = await self.session.execute(
            select(Contract)
            .where(
                Contract.event_id == event_id,
                Contract.deleted_at.is_(None),
            )
            .order_by(Contract.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, event_id: UUID, **kwargs) -> Contract:
        contract = Contract(event_id=event_id, **kwargs)
        self.session.add(contract)
        await self.session.flush()
        await self.session.refresh(contract)
        return contract
