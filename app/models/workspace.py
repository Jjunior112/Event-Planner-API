import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pg_enum
from app.models.enums import PlanStatus, WorkspacePlan, WorkspaceRole

if TYPE_CHECKING:
    from app.models.user import User


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    plan: Mapped[WorkspacePlan] = mapped_column(
        pg_enum(WorkspacePlan, "workspaceplan"),
        default=WorkspacePlan.FREE,
        nullable=False,
    )
    plan_status: Mapped[PlanStatus] = mapped_column(
        pg_enum(PlanStatus, "planstatus"),
        default=PlanStatus.ACTIVE,
        nullable=False,
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mercadopago_subscription_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    storage_used_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    subscription_current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    members: Mapped[list["WorkspaceMember"]] = relationship(
        back_populates="workspace",
        lazy="selectin",
    )


class WorkspaceMember(Base, TimestampMixin):
    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    role: Mapped[WorkspaceRole] = mapped_column(
        pg_enum(WorkspaceRole, "workspacerole"),
        nullable=False,
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(lazy="selectin")
