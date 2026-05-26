"""
Tests for the registration / email-verification / login flow.

All tests use HTTP only. The two unverified test users (seeded in
tests/test-data.sql) have known verification tokens so no direct DB
access is needed.
"""

import os
import uuid

import pytest
import requests
from fastapi import status


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

REGISTER_URL = f"{API_BASE_URL}/api/v1/auth/register"
LOGIN_URL = f"{API_BASE_URL}/api/v1/auth/login"
VERIFY_URL = f"{API_BASE_URL}/api/v1/auth/verify-email"
PUBLIC_RESEND_URL = f"{API_BASE_URL}/api/v1/auth/resend-verification"

# Pre-seeded in tests/test-data.sql — used for the full verify→login flow.
SEEDED_UNVERIFIED_USERNAME = "unverified_user"
SEEDED_UNVERIFIED_EMAIL = "unverified@test.com"
SEEDED_UNVERIFIED_PASSWORD = "Unverified1!"
SEEDED_UNVERIFIED_TOKEN = "test_verification_token_seeded_001"

# Separate pre-seeded user kept unverified for resend tests.
SEEDED_RESEND_EMAIL = "resend@test.com"
SEEDED_RESEND_TOKEN = "test_verification_token_seeded_002"

# Already-verified seeded user — used wherever a verified account is needed.
SEEDED_VERIFIED_USERNAME = "testuser"
SEEDED_VERIFIED_PASSWORD = "test123"
SEEDED_VERIFIED_EMAIL = "test@test.com"


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


@pytest.fixture
def new_user() -> dict:
    """Register a fresh user and return the credentials. The user starts unverified."""
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

    def test_register_blocks_login_until_verified(self, new_user):
        response = requests.post(
            LOGIN_URL,
            json={"username": new_user["username"], "password": new_user["password"]},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_register_duplicate_email_rejected(self, new_user):
        dup = _fresh_credentials()
        dup["email"] = new_user["email"]
        response = requests.post(REGISTER_URL, json=dup)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.json()["message"].lower()

    def test_register_duplicate_username_rejected(self, new_user):
        dup = _fresh_credentials()
        dup["username"] = new_user["username"]
        response = requests.post(REGISTER_URL, json=dup)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.json()["message"].lower()


class TestLoginVerification:
    def test_login_unverified_user_returns_401(self, new_user):
        response = requests.post(
            LOGIN_URL,
            json={"username": new_user["username"], "password": new_user["password"]},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "not verified" in response.json()["message"].lower()

    def test_login_verified_seeded_user_succeeds(self):
        response = requests.post(
            LOGIN_URL,
            json={"username": SEEDED_VERIFIED_USERNAME, "password": SEEDED_VERIFIED_PASSWORD},
        )

        assert response.status_code == status.HTTP_200_OK, response.text
        body = response.json()
        assert "access_token" in body
        assert body["user"]["verified"] is True

    def test_full_flow_verify_login(self):
        # Uses the pre-seeded unverified_user with a known token (no email needed).
        response = requests.post(VERIFY_URL, json={"verification_token": SEEDED_UNVERIFIED_TOKEN})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["verified"] is True

        response = requests.post(
            LOGIN_URL,
            json={"username": SEEDED_UNVERIFIED_USERNAME, "password": SEEDED_UNVERIFIED_PASSWORD},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user"]["verified"] is True


class TestVerifyEmail:
    def test_invalid_token_returns_400(self):
        response = requests.post(
            VERIFY_URL, json={"verification_token": "not-a-real-token"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid" in response.json()["message"].lower()


class TestPublicResend:
    """
    Validates that the public resend endpoint returns the same response for
    non-existent / unverified / already-verified emails.
    """

    def _post(self, email: str) -> requests.Response:
        return requests.post(PUBLIC_RESEND_URL, params={"email": email})

    def test_same_response_across_account_states(self, new_user):
        # State A: never-registered email
        nonexistent_email = f"never_seen_{uuid.uuid4().hex[:10]}@example.com"
        # State B: registered but unverified (fresh user from fixture)
        unverified_email = new_user["email"]
        # State C: already verified (pre-seeded testuser)
        verified_email = SEEDED_VERIFIED_EMAIL

        responses = {
            "nonexistent": self._post(nonexistent_email),
            "unverified": self._post(unverified_email),
            "verified": self._post(verified_email),
        }

        for label, resp in responses.items():
            assert resp.status_code == status.HTTP_200_OK, (
                f"{label} returned {resp.status_code}: {resp.text}"
            )
            body = resp.json()
            assert body["verification_required"] is True
            assert "if an account with this email exists" in body["message"].lower(), (
                f"{label} message leaks state: {body['message']}"
            )

        messages = {label: r.json()["message"] for label, r in responses.items()}
        assert len(set(messages.values())) == 1, (
            f"Response messages differ across account states (enumeration risk): {messages}"
        )

    def test_resend_regenerates_verification_key(self):
        # Trigger a resend for the pre-seeded resend_test_user.
        response = self._post(SEEDED_RESEND_EMAIL)
        assert response.status_code == status.HTTP_200_OK

        # The old known token must now be invalid — proves the key was replaced.
        verify_response = requests.post(
            VERIFY_URL, json={"verification_token": SEEDED_RESEND_TOKEN}
        )
        assert verify_response.status_code == status.HTTP_400_BAD_REQUEST
