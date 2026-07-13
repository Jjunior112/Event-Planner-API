from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.payment import Payment, PaymentInstallment


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, payment_id: UUID, event_id: UUID) -> Payment | None:
        result = await self.session.execute(
            select(Payment)
            .options(selectinload(Payment.installments))
            .where(
                Payment.id == payment_id,
                Payment.event_id == event_id,
                Payment.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_event(self, event_id: UUID) -> list[Payment]:
        result = await self.session.execute(
            select(Payment)
            .options(selectinload(Payment.installments))
            .where(
                Payment.event_id == event_id,
                Payment.deleted_at.is_(None),
            )
            .order_by(Payment.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, event_id: UUID, **kwargs) -> Payment:
        payment = Payment(event_id=event_id, **kwargs)
        self.session.add(payment)
        await self.session.flush()
        await self.session.refresh(payment)
        return payment

    async def get_installment(
        self,
        installment_id: UUID,
        payment_id: UUID,
    ) -> PaymentInstallment | None:
        result = await self.session.execute(
            select(PaymentInstallment).where(
                PaymentInstallment.id == installment_id,
                PaymentInstallment.payment_id == payment_id,
                PaymentInstallment.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()
