"""Helpers for idempotent PostgreSQL enum creation in Alembic migrations."""

from alembic import op
from sqlalchemy.dialects import postgresql


def create_enum_if_not_exists(name: str, values: list[str]) -> None:
    """Create a PostgreSQL ENUM safely (works with asyncpg; checkfirst does not)."""
    values_sql = ", ".join(f"'{value}'" for value in values)
    op.execute(
        f"DO $$ BEGIN "
        f"CREATE TYPE {name} AS ENUM ({values_sql}); "
        f"EXCEPTION WHEN duplicate_object THEN null; "
        f"END $$;"
    )


def pg_enum(name: str, values: list[str]) -> postgresql.ENUM:
    """Reference an existing PostgreSQL ENUM without emitting CREATE TYPE."""
    return postgresql.ENUM(*values, name=name, create_type=False)


def drop_enum_if_exists(name: str) -> None:
    op.execute(f"DROP TYPE IF EXISTS {name}")
