"""User management endpoints with authenticated access and admin-only controls."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRET_KEY_PLACEHOLDERS = {
    "CHANGE_ME_TO_A_LONG_RANDOM_SECRET",
    "changeme",
    "secret",
    "your-secret-key",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    APP_NAME: str = "FraudShield AI"
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    APP_DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # ---- Security ----
    SECRET_KEY: str = Field(..., description="Used to sign JWTs. Must be set via env in real deployments.")

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong_in_production(cls, v: str, info) -> str:
        # APP_ENV is validated separately and may not be in info.data yet
        # depending on field order, so read it defensively via os.environ
        # rather than assuming validation order.
        import os

        app_env = os.environ.get("APP_ENV", "development")
        if app_env != "production":
            return v

        if v in _INSECURE_SECRET_KEY_PLACEHOLDERS:
            raise ValueError(
                "SECRET_KEY is set to a known placeholder value. Generate a real secret with: "
                "python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters in production. Generate one with: "
                "python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        return v
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_HASH_SCHEME: str = "bcrypt"

    # ---- Database ----
    POSTGRES_USER: str = "fraudshield"
    POSTGRES_PASSWORD: str = "fraudshield"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "fraudshield_db"
    DATABASE_URL: PostgresDsn | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str | None, info) -> str:
        if v:
            return v
        data = info.data
        return (
            f"postgresql+psycopg://{data.get('POSTGRES_USER')}:{data.get('POSTGRES_PASSWORD')}"
            f"@{data.get('POSTGRES_HOST')}:{data.get('POSTGRES_PORT')}/{data.get('POSTGRES_DB')}"
        )

    # ---- Redis / Celery ----
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: RedisDsn | None = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, v: str | None, info) -> str:
        if v:
            return v
        data = info.data
        return f"redis://{data.get('REDIS_HOST')}:{data.get('REDIS_PORT')}/{data.get('REDIS_DB')}"

    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # ---- Rate limiting ----
    RATE_LIMIT_PER_MINUTE: int = 60
    # Auth endpoints (login/register) get a stricter limit than the rest of
    # the API -- they're the classic target for credential-stuffing and
    # brute-force attacks, and a legitimate user never needs 60 login
    # attempts a minute.
    AUTH_RATE_LIMIT_PER_MINUTE: int = 10

    # ---- ML ----
    MODEL_ARTIFACT_DIR: str = "app/ml/artifacts"
    DEFAULT_FRAUD_THRESHOLD: float = 0.5

    # ---- Upload limits ----
    # Defends against a malicious or accidental huge CSV exhausting memory
    # or flooding the DB with a single upload -- read in bounded chunks
    # (never buffering more than MAX_CSV_UPLOAD_SIZE_MB+1 in memory) and
    # reject outright if the row count is unreasonable for a single batch.
    MAX_CSV_UPLOAD_SIZE_MB: int = 10
    MAX_CSV_UPLOAD_ROWS: int = 50_000

    # ---- LLM Provider (Analyst AI Assistant) ----
    LLM_PROVIDER: Literal["ollama", "groq", "openai_compatible"] = "ollama"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"

    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    OPENAI_COMPATIBLE_BASE_URL: str | None = None
    OPENAI_COMPATIBLE_API_KEY: str | None = None
    OPENAI_COMPATIBLE_MODEL: str | None = None

    LLM_MAX_TOKENS: int = 800
    LLM_TEMPERATURE: float = 0.2  # low temperature: factual, grounded answers only

    # ---- Logging ----
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — env is read once per process."""
    return Settings()
