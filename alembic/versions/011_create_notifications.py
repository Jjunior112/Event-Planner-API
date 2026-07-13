"""create notifications table

Revision ID: 011_create_notifications
Revises: 010_create_audit_logs
Create Date: 2026-07-12 20:44:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.migration_enums import create_enum_if_not_exists, drop_enum_if_exists, pg_enum

revision: str = "011_create_notifications"
down_revision: Union[str, None] = "010_create_audit_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    create_enum_if_not_exists(
        "notificationtype",
        ["reminder", "payment_due", "quote_status", "general"],
    )
    create_enum_if_not_exists("notificationchannel", ["email", "in_app"])
    create_enum_if_not_exists(
        "notificationstatus",
        ["pending", "sent", "failed", "read"],
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "type",
            pg_enum(
                "notificationtype",
                ["reminder", "payment_due", "quote_status", "general"],
            ),
            nullable=False,
        ),
        sa.Column(
            "channel",
            pg_enum("notificationchannel", ["email", "in_app"]),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "status",
            pg_enum("notificationstatus", ["pending", "sent", "failed", "read"]),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_workspace_id", "notifications", ["workspace_id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_index("ix_notifications_workspace_id", table_name="notifications")
    op.drop_table("notifications")
    drop_enum_if_exists("notificationstatus")
    drop_enum_if_exists("notificationchannel")
    drop_enum_if_exists("notificationtype")
