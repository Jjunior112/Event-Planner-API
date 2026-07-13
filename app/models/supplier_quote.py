import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pg_enum
from app.models.category import Category
from app.models.enums import QuoteStatus
from app.models.event import Event
from app.models.supplier import Supplier


class SupplierQuote(Base, TimestampMixin):
    __tablename__ = "supplier_quotes"

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[QuoteStatus] = mapped_column(
        pg_enum(QuoteStatus, "quotestatus"),
        default=QuoteStatus.PENDING,
        nullable=False,
    )

    event: Mapped["Event"] = relationship(lazy="selectin")
    category: Mapped["Category"] = relationship(lazy="selectin")
    supplier: Mapped["Supplier"] = relationship(lazy="selectin")
