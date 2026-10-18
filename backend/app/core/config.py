from cryptography.fernet import Fernet
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
        if "postgresql://postgres:postgres@" in value:
            raise ValueError("DATABASE_URL must not use the default postgres/postgres credentials")
        return value

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if len(value) < 32 or value in {"change-me", "supersecret"}:
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
