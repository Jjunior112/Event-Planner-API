"""create supplier_quotes table

Revision ID: 006_create_supplier_quotes
Revises: 005_create_suppliers
Create Date: 2026-07-12 20:42:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.migration_enums import create_enum_if_not_exists, drop_enum_if_exists, pg_enum

revision: str = "006_create_supplier_quotes"
down_revision: Union[str, None] = "005_create_suppliers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    create_enum_if_not_exists("quotestatus", ["pending", "approved", "rejected"])

    op.create_table(
        "supplier_quotes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("supplier_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            pg_enum("quotestatus", ["pending", "approved", "rejected"]),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_supplier_quotes_event_id"),
        "supplier_quotes",
        ["event_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_supplier_quotes_category_id"),
        "supplier_quotes",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_supplier_quotes_supplier_id"),
        "supplier_quotes",
        ["supplier_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_supplier_quotes_supplier_id"),
        table_name="supplier_quotes",
    )
    op.drop_index(
        op.f("ix_supplier_quotes_category_id"),
        table_name="supplier_quotes",
    )
    op.drop_index(
        op.f("ix_supplier_quotes_event_id"),
        table_name="supplier_quotes",
    )
    op.drop_table("supplier_quotes")
    drop_enum_if_exists("quotestatus")
