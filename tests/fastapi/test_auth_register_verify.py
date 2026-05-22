"""
Tests for the registration / email-verification / login flow.

Uses live HTTP requests against the FastAPI server (matching the rest of the
suite). Reads `verification_key` directly from the DB via SessionLocal when
the test needs the token that would normally arrive by email.
"""

import os
import uuid

import pytest
import requests
from fastapi import status

from server.db.database import SessionLocal
from server.db.models.users import Users


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Endpoint paths (auth_router has prefix /auth, mounted under /api/v1).
REGISTER_URL = f"{API_BASE_URL}/api/v1/auth/register"
LOGIN_URL = f"{API_BASE_URL}/api/v1/auth/login"
VERIFY_URL = f"{API_BASE_URL}/api/v1/auth/verify-email"
PUBLIC_RESEND_URL = f"{API_BASE_URL}/api/v1/auth/resend-verification"


def _fresh_credentials() -> dict:
    """Return a unique, valid registration payload."""
    suffix = uuid.uuid4().hex[:10]
    return {
        "username": f"testuser_{suffix}",
        "email": f"test_{suffix}@example.com",
        "password": "Test1234!",
        "first_name": "Test",
        "last_name": "User",
    }


def _fetch_user(email: str) -> Users:
    """Read a user row directly from the DB."""
    with SessionLocal() as db:
        return db.query(Users).filter(Users.email == email).first()


@pytest.fixture
def new_user() -> dict:
    """
    Register a fresh user and return the credentials used (including username
    and email). The user starts unverified.
    """
    creds = _fresh_credentials()
    response = requests.post(REGISTER_URL, json=creds)
    assert response.status_code == status.HTTP_200_OK, response.text
    return creds


class TestRegister:
    def test_register_returns_verification_required(self):
        creds = _fresh_credentials()
        response = requests.post(REGISTER_URL, json=creds)

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["email"] == creds["email"]
        assert body["verification_required"] is True

    def test_register_persists_user_as_unverified_with_token(self, new_user):
        user = _fetch_user(new_user["email"])
        assert user is not None
        assert user.verified is False
        assert user.verification_key is not None
        assert len(user.verification_key) > 20  # secrets.token_urlsafe(32) ~ 43 chars

    def test_register_duplicate_email_rejected(self, new_user):
        # Reuse the same email with a different username
        dup = _fresh_credentials()
        dup["email"] = new_user["email"]
        response = requests.post(REGISTER_URL, json=dup)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.json()["detail"].lower()

    def test_register_duplicate_username_rejected(self, new_user):
        dup = _fresh_credentials()
        dup["username"] = new_user["username"]
        response = requests.post(REGISTER_URL, json=dup)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.json()["detail"].lower()


class TestLoginVerification:
    def test_login_unverified_user_returns_401(self, new_user):
        response = requests.post(
            LOGIN_URL,
            json={"username": new_user["username"], "password": new_user["password"]},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "not verified" in response.json()["detail"].lower()

    def test_login_verified_seeded_user_succeeds(self):
        # Seeded testuser in test-data.sql is verified=true.
        # Password is documented in tests/test-data.sql.pw line 32.
        response = requests.post(
            LOGIN_URL, json={"username": "testuser", "password": "test123"}
        )

        assert response.status_code == status.HTTP_200_OK, response.text
        body = response.json()
        assert "access_token" in body
        assert body["user"]["verified"] is True

    def test_full_flow_register_verify_login(self, new_user):
        # Pull the token straight from the DB (in real life this arrives by email).
        user = _fetch_user(new_user["email"])
        token = user.verification_key

        # Verify
        response = requests.post(VERIFY_URL, json={"verification_token": token})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["verified"] is True

        # Account row should reflect the change
        user_after = _fetch_user(new_user["email"])
        assert user_after.verified is True
        assert user_after.verification_key is None

        # Now login should succeed
        response = requests.post(
            LOGIN_URL,
            json={"username": new_user["username"], "password": new_user["password"]},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user"]["verified"] is True


class TestVerifyEmail:
    def test_invalid_token_returns_400(self):
        response = requests.post(
            VERIFY_URL, json={"verification_token": "not-a-real-token"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid" in response.json()["detail"].lower()


class TestPublicResend:
    """
    Validates H1: the public resend endpoint must return the same response for
    non-existent / unverified / already-verified emails so anonymous callers
    can't enumerate which addresses are registered or verified.
    """

    def _post(self, email: str) -> requests.Response:
        # email is a query parameter on this endpoint.
        return requests.post(PUBLIC_RESEND_URL, params={"email": email})

    def test_same_response_across_account_states(self, new_user):
        # State A: never-registered email
        nonexistent_email = f"never_seen_{uuid.uuid4().hex[:10]}@example.com"
        # State B: registered, still unverified (the new_user fixture)
        unverified_email = new_user["email"]
        # State C: registered and verified — verify the new_user first
        verify_user = _fetch_user(unverified_email)
        # Use a *separate* registered user for the verified state so the
        # unverified-state assertion can use new_user as-is.
        creds = _fresh_credentials()
        requests.post(REGISTER_URL, json=creds).raise_for_status()
        token = _fetch_user(creds["email"]).verification_key
        requests.post(VERIFY_URL, json={"verification_token": token}).raise_for_status()
        verified_email = creds["email"]

        responses = {
            "nonexistent": self._post(nonexistent_email),
            "unverified": self._post(unverified_email),
            "verified": self._post(verified_email),
        }

        # All three must return the same status code and body shape; only the
        # echoed `email` field differs (since the caller supplied it).
        for label, resp in responses.items():
            assert resp.status_code == status.HTTP_200_OK, (
                f"{label} returned {resp.status_code}: {resp.text}"
            )
            body = resp.json()
            assert body["verification_required"] is True
            assert (
                "if an account with this email exists" in body["message"].lower()
            ), f"{label} message leaks state: {body['message']}"

        # And the message must be byte-identical across states
        messages = {label: r.json()["message"] for label, r in responses.items()}
        assert len(set(messages.values())) == 1, (
            f"Response messages differ across account states (enumeration risk): {messages}"
        )

    def test_resend_regenerates_verification_key(self, new_user):
        token_before = _fetch_user(new_user["email"]).verification_key
        assert token_before is not None

        response = self._post(new_user["email"])
        assert response.status_code == status.HTTP_200_OK

        token_after = _fetch_user(new_user["email"]).verification_key
        assert token_after is not None
        assert token_after != token_before
