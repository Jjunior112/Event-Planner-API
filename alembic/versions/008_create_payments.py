"""create payments and payment_installments tables

Revision ID: 008_create_payments
Revises: 007_checklist_calendar
Create Date: 2026-07-12 20:44:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.migration_enums import create_enum_if_not_exists, drop_enum_if_exists, pg_enum

revision: str = "008_create_payments"
down_revision: Union[str, None] = "007_checklist_calendar"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    create_enum_if_not_exists("paymentstatus", ["pending", "partial", "paid"])
    create_enum_if_not_exists("installmentstatus", ["pending", "paid", "overdue"])

    op.create_table(
        "payments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.Column("supplier_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "status",
            pg_enum("paymentstatus", ["pending", "partial", "paid"]),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_event_id", "payments", ["event_id"])

    op.create_table(
        "payment_installments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("payment_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            pg_enum("installmentstatus", ["pending", "paid", "overdue"]),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_installments_payment_id", "payment_installments", ["payment_id"])


def downgrade() -> None:
    op.drop_index("ix_payment_installments_payment_id", table_name="payment_installments")
    op.drop_table("payment_installments")
    op.drop_index("ix_payments_event_id", table_name="payments")
    op.drop_table("payments")
    drop_enum_if_exists("installmentstatus")
    drop_enum_if_exists("paymentstatus")
