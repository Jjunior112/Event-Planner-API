from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import InstallmentStatus, PaymentStatus, WorkspaceRole
from app.models.event import Event
from app.models.payment import Payment, PaymentInstallment
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.payment import (
    InstallmentResponse,
    PaymentCreate,
    PaymentResponse,
    PaymentUpdate,
)
from app.schemas.workspace import WorkspaceAuth
from app.services.audit_service import AuditService


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PaymentRepository(session)
        self.category_repo = CategoryRepository(session)
        self.supplier_repo = SupplierRepository(session)
        self.audit = AuditService(session)

    async def create(
        self,
        auth: WorkspaceAuth,
        event: Event,
        user: User,
        data: PaymentCreate,
    ) -> PaymentResponse:
        if data.category_id:
            cat = await self.category_repo.get_by_id(data.category_id, event.id)
            if cat is None:
                raise HTTPException(404, "Category not found in this event")

        if data.supplier_id:
            sup = await self.supplier_repo.get_by_id(
                data.supplier_id, auth.workspace.id
            )
            if sup is None:
                raise HTTPException(404, "Supplier not found in this workspace")

        installments_total = sum(i.amount for i in data.installments)
        if installments_total != data.total_amount:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Installments total must match payment total_amount",
            )

        payment = await self.repo.create(
            event_id=event.id,
            title=data.title,
            description=data.description,
            category_id=data.category_id,
            supplier_id=data.supplier_id,
            total_amount=data.total_amount,
            status=PaymentStatus.PENDING,
        )

        for inst in data.installments:
            installment = PaymentInstallment(
                payment_id=payment.id,
                amount=inst.amount,
                due_date=inst.due_date,
                status=InstallmentStatus.PENDING,
            )
            self.session.add(installment)

        await self.session.flush()
        payment = await self.repo.get_by_id(payment.id, event.id)
        await self.audit.log(
            auth.workspace.id,
            user,
            "payment",
            payment.id,
            "created",
            {"title": data.title, "total_amount": str(data.total_amount)},
        )
        return self._to_response(payment)

    async def list(self, event: Event) -> list[PaymentResponse]:
        payments = await self.repo.list_by_event(event.id)
        return [self._to_response(p) for p in payments]

    async def get(self, event: Event, payment_id: UUID) -> PaymentResponse:
        payment = await self._get_or_404(event.id, payment_id)
        return self._to_response(payment)

    async def update(
        self,
        event: Event,
        payment_id: UUID,
        data: PaymentUpdate,
    ) -> PaymentResponse:
        payment = await self._get_or_404(event.id, payment_id)

        if data.title is not None:
            payment.title = data.title
        if data.description is not None:
            payment.description = data.description

        await self.session.flush()
        await self.session.refresh(payment)
        return self._to_response(payment)

    async def mark_installment_paid(
        self,
        auth: WorkspaceAuth,
        event: Event,
        user: User,
        payment_id: UUID,
        installment_id: UUID,
    ) -> PaymentResponse:
        self._require_roles(auth, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)
        payment = await self._get_or_404(event.id, payment_id)
        installment = await self.repo.get_installment(installment_id, payment.id)
        if installment is None:
            raise HTTPException(404, "Installment not found")

        if installment.status == InstallmentStatus.PAID:
            return self._to_response(payment)

        installment.status = InstallmentStatus.PAID
        installment.paid_at = datetime.now(UTC)
        self._recalculate_payment_status(payment)

        await self.session.flush()
        payment = await self.repo.get_by_id(payment.id, event.id)
        await self.audit.log(
            auth.workspace.id,
            user,
            "payment_installment",
            installment.id,
            "paid",
            {"amount": str(installment.amount)},
        )
        return self._to_response(payment)

    async def delete(
        self,
        auth: WorkspaceAuth,
        event: Event,
        payment_id: UUID,
    ) -> None:
        self._require_roles(auth, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)
        payment = await self._get_or_404(event.id, payment_id)
        payment.soft_delete()
        for inst in payment.installments:
            inst.soft_delete()

    async def _get_or_404(self, event_id: UUID, payment_id: UUID) -> Payment:
        payment = await self.repo.get_by_id(payment_id, event_id)
        if payment is None:
            raise HTTPException(404, "Payment not found")
        return payment

    @staticmethod
    def _recalculate_payment_status(payment: Payment) -> None:
        active = [i for i in payment.installments if i.deleted_at is None]
        if not active:
            payment.status = PaymentStatus.PENDING
            return
        paid = [i for i in active if i.status == InstallmentStatus.PAID]
        if len(paid) == len(active):
            payment.status = PaymentStatus.PAID
        elif len(paid) > 0:
            payment.status = PaymentStatus.PARTIAL
        else:
            payment.status = PaymentStatus.PENDING

    @staticmethod
    def _require_roles(auth: WorkspaceAuth, *roles: WorkspaceRole) -> None:
        if auth.membership.role not in roles:
            raise HTTPException(403, "Insufficient permissions")

    @staticmethod
    def _to_response(payment: Payment) -> PaymentResponse:
        installments = [
            InstallmentResponse.model_validate(i)
            for i in payment.installments
            if i.deleted_at is None
        ]
        return PaymentResponse(
            id=payment.id,
            event_id=payment.event_id,
            category_id=payment.category_id,
            supplier_id=payment.supplier_id,
            title=payment.title,
            description=payment.description,
            total_amount=payment.total_amount,
            status=payment.status,
            installments=installments,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )
