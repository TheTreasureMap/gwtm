"""Route-level tests that captcha is enforced before any DB work."""

import httpx
import pytest
from fastapi.testclient import TestClient

from server.config import settings
from server.db.database import get_db
from server.main import app
from server.utils import captcha
from tests.unit.test_captcha import REQUEST, make_client

REGISTER_BODY = {
    "email": "new@example.com",
    "username": "newuser",
    "password": "Passw0rdxx",
}
RESEND_BODY = {"email": "nobody@example.com"}


class FakeQuery:
    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return None


class FakeDB:
    """Records queries so tests can assert the DB was never touched."""

    def __init__(self):
        self.queries = 0

    def query(self, *args, **kwargs):
        self.queries += 1
        return FakeQuery()

    def rollback(self):
        pass


@pytest.fixture
def db():
    fake = FakeDB()
    app.dependency_overrides[get_db] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def client(db):
    return TestClient(app)


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setattr(settings, "TURNSTILE_SECRET_KEY", "test-secret")


@pytest.mark.parametrize(
    "path, body",
    [
        ("/api/v1/auth/register", REGISTER_BODY),
        ("/api/v1/register", REGISTER_BODY),
        ("/api/v1/auth/resend-verification", RESEND_BODY),
    ],
)
def test_missing_token_is_rejected_before_any_db_query(secret, client, db, path, body):
    response = client.post(path, json=body)

    assert response.status_code == 400
    assert response.json() == {"message": "Captcha verification failed"}
    assert db.queries == 0


@pytest.mark.parametrize(
    "path, body",
    [
        ("/api/v1/auth/register", REGISTER_BODY),
        ("/api/v1/auth/resend-verification", RESEND_BODY),
    ],
)
def test_oversized_token_is_rejected(secret, client, db, path, body):
    response = client.post(path, json={**body, "turnstile_token": "x" * 2049})

    assert response.status_code == 400
    assert db.queries == 0


def test_resend_with_accepted_token_proceeds(secret, client, monkeypatch):
    ok = httpx.Response(200, json={"success": True}, request=REQUEST)
    monkeypatch.setattr(captcha.httpx, "AsyncClient", make_client(ok))

    response = client.post(
        "/api/v1/auth/resend-verification",
        json={**RESEND_BODY, "turnstile_token": "good-token"},
    )

    assert response.status_code == 200
    assert response.json()["verification_required"] is True


def test_resend_skips_captcha_when_secret_unset(monkeypatch, client):
    monkeypatch.setattr(settings, "TURNSTILE_SECRET_KEY", "")

    response = client.post("/api/v1/auth/resend-verification", json=RESEND_BODY)

    assert response.status_code == 200


def test_resend_no_longer_accepts_email_as_a_query_param(monkeypatch, client):
    monkeypatch.setattr(settings, "TURNSTILE_SECRET_KEY", "")

    response = client.post(
        "/api/v1/auth/resend-verification", params={"email": "a@example.com"}
    )

    assert response.status_code == 400


def test_captcha_config_returns_the_site_key(monkeypatch, client):
    monkeypatch.setattr(settings, "TURNSTILE_SITE_KEY", "site-key")

    response = client.get("/api/v1/auth/captcha-config")

    assert response.status_code == 200
    assert response.json() == {"turnstile_site_key": "site-key"}


def test_captcha_config_is_empty_when_unconfigured(monkeypatch, client):
    monkeypatch.setattr(settings, "TURNSTILE_SITE_KEY", "")

    response = client.get("/api/v1/auth/captcha-config")

    assert response.json() == {"turnstile_site_key": ""}
