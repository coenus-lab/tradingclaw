import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import create_token, decrypt_secret, encrypt_secret
from app.models.entities import ApiCredential, User


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(str(user.id))}"}


def test_sensitive_route_requires_authentication(client, users):
    trader, _, _ = users
    response = client.get(f"/v1/users/{trader.id}/events")
    assert response.status_code == 401


def test_registration_creates_trader_not_admin(client, db_session):
    response = client.post(
        "/v1/auth/register",
        json={"email": "new@example.test", "password": "correct-horse-battery-staple"},
    )
    assert response.status_code == 200
    assert db_session.query(User).filter(User.email == "new@example.test").one().role == "trader"


def test_trader_cannot_read_another_users_data(client, users):
    trader, other, _ = users
    response = client.get(f"/v1/users/{other.id}/events", headers=auth(trader))
    assert response.status_code == 403


def test_admin_can_read_another_users_data(client, users):
    trader, _, admin = users
    response = client.get(f"/v1/users/{trader.id}/events", headers=auth(admin))
    assert response.status_code == 200


def test_admin_routes_reject_traders(client, users):
    trader, _, admin = users
    assert client.get("/v1/admin/policies", headers=auth(trader)).status_code == 403
    assert client.get("/v1/admin/policies", headers=auth(admin)).status_code == 200


def test_credentials_are_bound_to_authenticated_user(client, db_session, users):
    trader, other, _ = users
    response = client.post(
        "/v1/credentials",
        headers=auth(trader),
        json={"environment": "demo", "api_key": "key", "api_secret": "secret"},
    )
    assert response.status_code == 200
    saved = db_session.query(ApiCredential).one()
    assert saved.user_id == trader.id
    assert decrypt_secret(saved.api_secret_encrypted) == "secret"

    spoof = client.post(
        "/v1/credentials",
        headers=auth(trader),
        json={"user_id": other.id, "environment": "demo", "api_key": "key", "api_secret": "secret"},
    )
    assert spoof.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"orderType": "mkt", "symbol": "PI_XBTUSD", "size": 1, "leverage": 2},
        {"orderType": "mkt", "symbol": "PI_XBTUSD", "size": 1, "leverage": 2, "risk_at_stop_pct": 0.8, "unexpected": True},
        {"orderType": "bogus", "symbol": "PI_XBTUSD", "size": 1, "leverage": 2, "risk_at_stop_pct": 0.8},
        {"orderType": "lmt", "symbol": "PI_XBTUSD", "size": 1, "leverage": 2, "risk_at_stop_pct": 0.8},
        {"orderType": "stp", "symbol": "PI_XBTUSD", "size": 1, "leverage": 2, "risk_at_stop_pct": 0.8},
    ],
)
def test_kraken_order_rejects_missing_or_unknown_risk_fields(client, users, payload):
    trader, _, _ = users
    response = client.post(f"/v1/kraken/{trader.id}/order", headers=auth(trader), json=payload)
    assert response.status_code == 422


def test_environment_must_be_explicitly_demo_or_prod(client, users):
    trader, _, _ = users
    response = client.get(f"/v1/kraken/{trader.id}/positions?environment=production", headers=auth(trader))
    assert response.status_code == 422


def test_secret_configuration_fails_closed():
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql://postgres:postgres@db:5432/tradingclaw",
            jwt_secret="supersecret",
            encryption_key="",
        )


def test_encryption_uses_persistent_configured_key():
    ciphertext = encrypt_secret("kraken-secret")
    assert decrypt_secret(ciphertext) == "kraken-secret"
