"""workspace plans, viewer role, superadmin

Revision ID: 012_workspace_plans
Revises: 011_create_notifications
Create Date: 2026-07-12 20:58:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.migration_enums import create_enum_if_not_exists, drop_enum_if_exists, pg_enum

revision: str = "012_workspace_plans"
down_revision: Union[str, None] = "011_create_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE workspacerole ADD VALUE IF NOT EXISTS 'viewer'")

    create_enum_if_not_exists("workspaceplan", ["free", "starter", "premium"])
    create_enum_if_not_exists(
        "planstatus", ["active", "past_due", "canceled", "trialing"]
    )

    op.add_column(
        "users",
        sa.Column("is_superadmin", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.add_column(
        "workspaces",
        sa.Column(
            "plan",
            pg_enum("workspaceplan", ["free", "starter", "premium"]),
            nullable=False,
            server_default="free",
        ),
    )
    op.add_column(
        "workspaces",
        sa.Column(
            "plan_status",
            pg_enum("planstatus", ["active", "past_due", "canceled", "trialing"]),
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column(
        "workspaces",
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "workspaces",
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "workspaces",
        sa.Column("mercadopago_subscription_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "workspaces",
        sa.Column("storage_used_bytes", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.add_column(
        "workspaces",
        sa.Column("subscription_current_period_end", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workspaces", "subscription_current_period_end")
    op.drop_column("workspaces", "storage_used_bytes")
    op.drop_column("workspaces", "mercadopago_subscription_id")
    op.drop_column("workspaces", "stripe_subscription_id")
    op.drop_column("workspaces", "stripe_customer_id")
    op.drop_column("workspaces", "plan_status")
    op.drop_column("workspaces", "plan")
    op.drop_column("users", "is_superadmin")
    drop_enum_if_exists("planstatus")
    drop_enum_if_exists("workspaceplan")
