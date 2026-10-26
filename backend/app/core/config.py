from cryptography.fernet import Fernet
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


def is_placeholder(value: str) -> bool:
    return value.strip().lower().startswith("replace_with_")


class Settings(BaseSettings):
    app_name: str = "Behavioral Risk OS API"
    database_url: str
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str
    encryption_key: str
    kraken_demo_base_url: str = "https://demo-futures.kraken.com/derivatives/api/v3"
    kraken_prod_base_url: str = "https://futures.kraken.com/derivatives/api/v3"
    inactivity_timeout_seconds: int = 900

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def reject_default_database_credentials(cls, value: str) -> str:
        try:
            url = make_url(value)
        except ArgumentError as exc:
            raise ValueError("DATABASE_URL must be a valid database URL") from exc
        if url.get_backend_name() == "postgresql":
            if not url.username or not url.password:
                raise ValueError("DATABASE_URL requires explicit PostgreSQL credentials")
            if (
                url.username.lower() == "postgres"
                or is_placeholder(url.username)
                or url.password.lower() in {"postgres", "password", "change-me", "supersecret"}
                or is_placeholder(url.password)
            ):
                raise ValueError("DATABASE_URL must use non-default PostgreSQL credentials")
        return value

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if len(value.strip()) < 32 or is_placeholder(value):
            raise ValueError("JWT_SECRET must be a non-default value of at least 32 characters")
        return value

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, value: str) -> str:
        try:
            Fernet(value.encode())
        except (TypeError, ValueError) as exc:
            raise ValueError("ENCRYPTION_KEY must be a valid Fernet key") from exc
        return value


settings = Settings()
