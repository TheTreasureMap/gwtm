"""Password reset tokens and the forgot/reset endpoints. DB and email are faked."""

import asyncio
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from server.config import settings
from server.db.database import get_db
from server.db.models.users import Users
from server.main import app
from server.routes.auth import password_reset
from server.utils import email, tokens

FORGOT_URL = "/api/v1/auth/forgot-password"
RESET_URL = "/api/v1/auth/reset-password"
NEW_PASSWORD = "NewPassw0rd"


def make_user(verified=True):
    user = Users(
        id=42,
        username="alice",
        email="alice@example.com",
        verified=verified,
        api_token="existing-token" if verified else None,
        verification_key=None if verified else "pending",
    )
    user.set_password("OldPassw0rd")
    return user


class FakeQuery:
    def __init__(self, db):
        self.db = db
        self.user = db.user

    def filter(self, *args, **kwargs):
        return self

    def with_for_update(self):
        self.db.locked = True
        return self

    def first(self):
        return self.user


class FakeDB:
    def __init__(self, user=None):
        self.user = user
        self.queries = 0
        self.commits = 0
        self.locked = False

    def query(self, *args, **kwargs):
        self.queries += 1
        return FakeQuery(self)

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass


@pytest.fixture(autouse=True)
def no_captcha(monkeypatch):
    monkeypatch.setattr(settings, "TURNSTILE_SECRET_KEY", "")


@pytest.fixture
def sent(monkeypatch):
    calls = []

    async def fake_send(**kwargs):
        calls.append(kwargs)
        return True

    monkeypatch.setattr(password_reset, "send_password_reset_email", fake_send)
    return calls


def client_for(db):
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.pop(get_db, None)


def expired_reset_token():
    return jwt.encode(
        {
            "uid": 42,
            "purpose": "reset",
            "pwf": "x",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# Tokens


def test_reset_token_round_trips():
    user = make_user()
    token = tokens.generate_reset_token(user.id, user.password_hash)

    user_id, fingerprint = tokens.decode_reset_token(token)

    assert user_id == user.id
    assert tokens.reset_token_matches(fingerprint, user.password_hash)


def test_reset_token_stops_matching_after_password_change():
    user = make_user()
    _, fingerprint = tokens.decode_reset_token(
        tokens.generate_reset_token(user.id, user.password_hash)
    )

    user.set_password(NEW_PASSWORD)

    assert not tokens.reset_token_matches(fingerprint, user.password_hash)


def test_verification_token_is_not_a_reset_token():
    with pytest.raises(jwt.InvalidTokenError):
        tokens.decode_reset_token(tokens.generate_verification_token(42))


def test_expired_reset_token_is_rejected():
    with pytest.raises(jwt.ExpiredSignatureError):
        tokens.decode_reset_token(expired_reset_token())


# Forgot password


def test_forgot_sends_email_for_known_address(sent):
    user = make_user()
    response = client_for(FakeDB(user)).post(FORGOT_URL, json={"email": user.email})

    assert response.status_code == 200
    assert len(sent) == 1
    assert sent[0]["email"] == user.email
    user_id, _ = tokens.decode_reset_token(sent[0]["reset_token"])
    assert user_id == user.id


def test_forgot_gives_same_response_for_unknown_address(sent):
    known = client_for(FakeDB(make_user())).post(FORGOT_URL, json={"email": "alice@example.com"})
    unknown = client_for(FakeDB(None)).post(FORGOT_URL, json={"email": "nobody@example.com"})

    assert unknown.status_code == known.status_code == 200
    assert unknown.json() == known.json()
    assert len(sent) == 1


def test_forgot_requires_captcha_before_any_db_query(monkeypatch, sent):
    monkeypatch.setattr(settings, "TURNSTILE_SECRET_KEY", "test-secret")
    db = FakeDB(make_user())

    response = client_for(db).post(FORGOT_URL, json={"email": "alice@example.com"})

    assert response.status_code == 400
    assert response.json() == {"message": "Captcha verification failed"}
    assert db.queries == 0
    assert sent == []


def test_forgot_rejects_malformed_email_before_any_db_query(sent):
    db = FakeDB(make_user())

    response = client_for(db).post(FORGOT_URL, json={"email": "not-an-email"})

    assert response.status_code == 400
    assert db.queries == 0
    assert sent == []


# Reset password


def reset(db, token, password=NEW_PASSWORD):
    return client_for(db).post(RESET_URL, json={"token": token, "password": password})


def test_reset_sets_new_password():
    user = make_user()
    db = FakeDB(user)

    response = reset(db, tokens.generate_reset_token(user.id, user.password_hash))

    assert response.status_code == 200
    assert user.check_password(NEW_PASSWORD)
    assert user.api_token == "existing-token"
    assert db.commits == 1
    assert db.locked


def test_reset_rotates_api_token_when_asked():
    user = make_user()
    token = tokens.generate_reset_token(user.id, user.password_hash)

    response = client_for(FakeDB(user)).post(
        RESET_URL, json={"token": token, "password": NEW_PASSWORD, "rotate_api_token": True}
    )

    assert response.status_code == 200
    assert user.api_token not in (None, "existing-token")


def test_reset_link_works_only_once():
    user = make_user()
    db = FakeDB(user)
    token = tokens.generate_reset_token(user.id, user.password_hash)

    assert reset(db, token).status_code == 200
    second = reset(db, token, password="Another1pass")

    assert second.status_code == 400
    assert user.check_password(NEW_PASSWORD)


def test_reset_verifies_unverified_account():
    user = make_user(verified=False)

    response = reset(FakeDB(user), tokens.generate_reset_token(user.id, user.password_hash))

    assert response.status_code == 200
    assert user.verified is True
    assert user.verification_key is None
    assert user.api_token


def test_reset_rejects_weak_password():
    user = make_user()
    db = FakeDB(user)

    response = reset(db, tokens.generate_reset_token(user.id, user.password_hash), "weak")

    assert response.status_code == 400
    assert user.check_password("OldPassw0rd")
    assert db.commits == 0


def test_reset_reports_expired_link():
    db = FakeDB(make_user())

    response = reset(db, expired_reset_token())

    assert response.status_code == 400
    assert "expired" in response.json()["message"]
    assert db.queries == 0


def test_reset_rejects_verification_token():
    user = make_user()

    response = reset(FakeDB(user), tokens.generate_verification_token(user.id))

    assert response.status_code == 400
    assert user.check_password("OldPassw0rd")


def test_reset_rejects_unknown_user():
    response = reset(FakeDB(None), tokens.generate_reset_token(99, "whatever"))

    assert response.status_code == 400


# Email


def test_reset_email_escapes_username(monkeypatch):
    sent = {}
    monkeypatch.setattr(email, "RESEND_API_KEY", "key")
    monkeypatch.setattr(email, "_send_resend", lambda to, subject, html, text: sent.update(html=html))

    asyncio.run(email.send_password_reset_email("a@example.com", "<b>bob</b>", "TOKEN"))

    assert "Hi &lt;b&gt;bob&lt;/b&gt;," in sent["html"]
    assert "<b>bob</b>" not in sent["html"]
