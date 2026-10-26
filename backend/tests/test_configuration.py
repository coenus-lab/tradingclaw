import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize("field", ["DATABASE_URL", "JWT_SECRET", "ENCRYPTION_KEY"])
def test_required_secret_missing(monkeypatch, field):
    monkeypatch.delenv(field, raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("value", [
    "", "not-a-url", "postgresql://db/tradingclaw",
    "postgresql://postgres:secure-long-password@db/tradingclaw",
    "postgresql+psycopg2://app:postgres@db/tradingclaw",
    "postgresql://app:%70ostgres@db/tradingclaw",
    "postgresql://replace_with_non_default_user:long-password@db/tradingclaw",
    "postgresql://app:replace_with_a_long_random_password@db/tradingclaw",
])
def test_invalid_database_configuration(value):
    with pytest.raises(ValidationError, match="database_url"):
        Settings(_env_file=None, database_url=value)


@pytest.mark.parametrize("value", ["", "supersecret", "x" * 31, " " * 32,
                                      "replace_with_at_least_32_random_characters"])
def test_invalid_jwt_configuration(value):
    with pytest.raises(ValidationError, match="jwt_secret"):
        Settings(_env_file=None, jwt_secret=value)


@pytest.mark.parametrize("value", ["", "replace_with_fernet_key", "not-a-fernet-key"])
def test_invalid_fernet_configuration(value):
    with pytest.raises(ValidationError, match="encryption_key"):
        Settings(_env_file=None, encryption_key=value)


def test_valid_configuration():
    settings = Settings(_env_file=None,
                        database_url="postgresql://app:long-random-password@db/tradingclaw",
                        jwt_secret="0123456789abcdef" * 4)
    assert settings.database_url.startswith("postgresql://app:")
