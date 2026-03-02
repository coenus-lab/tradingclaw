from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Behavioral Risk OS API"
    database_url: str = "postgresql://postgres:postgres@db:5432/tradingclaw"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "change-me"
    encryption_key: str = ""  # base64 Fernet key
    kraken_demo_base_url: str = "https://demo-futures.kraken.com/derivatives/api/v3"
    kraken_prod_base_url: str = "https://futures.kraken.com/derivatives/api/v3"
    inactivity_timeout_seconds: int = 900

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
