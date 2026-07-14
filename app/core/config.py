import json
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Event Planner API"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = (
        "postgresql+asyncpg://event_planner:event_planner@localhost:5432/event_planner"
    )

    cors_origins: list[str] = ["http://localhost:3000"]
    cors_origin_regex: str | None = r"https://.*\.vercel\.app"

    jwt_secret_key: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 24 hours

    upload_dir: str = "uploads/contracts"

    smtp_enabled: bool = False
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@eventplanner.local"
    smtp_use_tls: bool = True

    frontend_url: str = "http://localhost:3000"

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_starter_price_id: str = ""
    stripe_premium_price_id: str = ""

    mercadopago_access_token: str = ""
    mercadopago_webhook_secret: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if value is None:
            return ["http://localhost:3000"]

        if isinstance(value, list):
            return [str(origin).strip().rstrip("/") for origin in value if str(origin).strip()]

        if isinstance(value, str):
            raw = value.strip().strip('"').strip("'")
            if not raw:
                return []

            if raw.startswith("["):
                parsed = json.loads(raw)
                if not isinstance(parsed, list):
                    raise ValueError("CORS_ORIGINS must be a JSON array")
                return [str(origin).strip().rstrip("/") for origin in parsed if str(origin).strip()]

            if "," in raw:
                return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]

            return [raw.rstrip("/")]

        raise ValueError("CORS_ORIGINS has an invalid format")

    @field_validator("cors_origin_regex", mode="before")
    @classmethod
    def normalize_cors_origin_regex(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip().strip('"').strip("'")
            return cleaned or None
        return value

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        url = value.strip().strip('"').strip("'")
        if not url:
            raise ValueError("DATABASE_URL must not be empty")

        if url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        if "sslmode=require" in url:
            url = url.replace("sslmode=require", "ssl=require")

        if "channel_binding=require" in url:
            url = url.replace("&channel_binding=require", "").replace(
                "channel_binding=require&", ""
            ).replace("channel_binding=require", "")

        return url.rstrip("&").rstrip("?")


@lru_cache
def get_settings() -> Settings:
    return Settings()
