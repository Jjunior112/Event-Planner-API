import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pg_enum
from app.models.category import Category
from app.models.enums import InstallmentStatus, PaymentStatus
from app.models.event import Event
from app.models.supplier import Supplier


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=True,
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        pg_enum(PaymentStatus, "paymentstatus"),
        default=PaymentStatus.PENDING,
        nullable=False,
    )

    event: Mapped["Event"] = relationship(lazy="selectin")
    category: Mapped["Category | None"] = relationship(lazy="selectin")
    supplier: Mapped["Supplier | None"] = relationship(lazy="selectin")
    installments: Mapped[list["PaymentInstallment"]] = relationship(
        back_populates="payment",
        lazy="selectin",
    )


class PaymentInstallment(Base, TimestampMixin):
    __tablename__ = "payment_installments"

    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[InstallmentStatus] = mapped_column(
        pg_enum(InstallmentStatus, "installmentstatus"),
        default=InstallmentStatus.PENDING,
        nullable=False,
    )

    payment: Mapped["Payment"] = relationship(back_populates="installments")
