from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import (
    AnyHttpUrl,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors_origins(v: Any) -> list[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | tuple):
        return [str(i) for i in v]
    elif v is None or v == "":
        return []
    return list(v)


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        validate_default=True,
    )

    APP_NAME: str = "CommercePulse"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/commercepulse",
        description="Async PostgreSQL connection URL",
    )
    DATABASE_URL_SYNC: str | None = Field(
        default=None,
        description="Sync PostgreSQL URL for Alembic/Celery (defaults to DATABASE_URL with psycopg2)",
    )

    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    S3_BUCKET: str = "commercepulse-storage"
    S3_ENDPOINT: str = "https://s3.amazonaws.com"
    S3_ACCESS_KEY: SecretStr = Field(default=SecretStr(""))
    S3_SECRET_KEY: SecretStr = Field(default=SecretStr(""))
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = True

    SECRET_KEY: SecretStr = Field(
        default=SecretStr("change-me-in-production"),
        min_length=32,
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, le=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=365)
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = Field(default=1, ge=1, le=168)
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = Field(default=24, ge=1, le=720)
    CSRF_SECRET_KEY: SecretStr = Field(
        default=SecretStr("change-me-csrf-secret-in-production"),
        min_length=16,
    )

    MAIL_USERNAME: str = "apikey"
    MAIL_PASSWORD: SecretStr = Field(default=SecretStr(""))
    MAIL_FROM: EmailStr = Field(default="no-reply@commercepulse.ai")
    MAIL_FROM_NAME: str = "CommercePulse"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.sendgrid.net"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_USE_CREDENTIALS: bool = True
    MAIL_VALIDATE_CERTS: bool = True

    STRIPE_SECRET_KEY: SecretStr = Field(default=SecretStr(""))
    STRIPE_WEBHOOK_SECRET: SecretStr = Field(default=SecretStr(""))
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_PRICE_BASIC: str = ""
    STRIPE_PRICE_PRO: str = ""
    STRIPE_PRICE_ENTERPRISE: str = ""
    STRIPE_API_VERSION: str = "2024-06-20"

    CORS_ORIGINS: Annotated[list[AnyHttpUrl], BeforeValidator(parse_cors_origins)] = Field(
        default_factory=lambda: [],
    )
    CORS_ORIGINS_REGEX: str | None = None

    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=1)
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, ge=1)
    RATE_LIMIT_STORAGE: Literal["memory", "redis"] = "redis"

    SENTRY_DSN: str | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1, ge=0.0, le=1.0)
    SENTRY_PROFILES_SAMPLE_RATE: float = Field(default=0.05, ge=0.0, le=1.0)
    SENTRY_ENVIRONMENT: str | None = None

    DEFAULT_CURRENCY: str = "USD"
    DEFAULT_TIMEZONE: str = "UTC"
    DEFAULT_LOCALE: str = "en_US"
    DEFAULT_DATE_FORMAT: str = "%Y-%m-%d"
    DEFAULT_DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%SZ"

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "console", "text"] = "json"
    LOG_FILE_PATH: str | None = "logs/app.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_BACKUP_COUNT: int = 5

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_ALWAYS_EAGER: bool = False
    CELERY_TASK_SOFT_TIME_LIMIT: int = 300
    CELERY_TASK_TIME_LIMIT: int = 600

    MAX_UPLOAD_SIZE_MB: int = Field(default=50, ge=1, le=500)
    PAGE_SIZE_DEFAULT: int = 20
    PAGE_SIZE_MAX: int = 100

    ANOMALY_DETECTION_SENSITIVITY: float = Field(default=3.0, ge=1.0, le=10.0)
    FORECASTING_DEFAULT_HORIZON_DAYS: int = 90
    FORECASTING_CONFIDENCE_INTERVAL: float = Field(default=0.95, ge=0.5, le=0.99)

    @field_validator("DATABASE_URL_SYNC", mode="before")
    @classmethod
    def build_sync_database_url(cls, v: str | None, info: Any) -> str:
        if v:
            return v
        async_url = info.data.get("DATABASE_URL", "")
        return async_url.replace("+asyncpg", "+psycopg2").replace("postgresql+asyncpg", "postgresql+psycopg2")

    @model_validator(mode="after")
    def validate_environment_settings(self) -> "Settings":
        if self.ENVIRONMENT == Environment.PRODUCTION:
            if self.SECRET_KEY.get_secret_value() in {"change-me-in-production", ""}:
                raise ValueError("SECRET_KEY must be set in production")
            if self.CSRF_SECRET_KEY.get_secret_value() in {"change-me-csrf-secret-in-production", ""}:
                raise ValueError("CSRF_SECRET_KEY must be set in production")
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production")
        return self

    def is_production(self) -> bool:
        return self.ENVIRONMENT == Environment.PRODUCTION

    def is_development(self) -> bool:
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    def is_test(self) -> bool:
        return self.ENVIRONMENT == Environment.TEST


settings = Settings()
