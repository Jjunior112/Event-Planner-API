from functools import lru_cache

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
