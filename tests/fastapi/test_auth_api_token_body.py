"""
Tests for the deprecated api_token-in-JSON-body auth fallback.

Uses POST /api/v1/doi_author_groups as the auth vehicle: it needs auth and
already declares a JSON body, which is what makes the fallback reachable at
all (see the comment in server/auth/auth.py, request_body_json only sees a
body FastAPI has already parsed for the endpoint's own use, so a body-less
endpoint like /admin/fixdata can never authenticate this way).
"""

import os
import uuid
import requests
from fastapi import status

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
GROUPS_URL = f"{API_BASE_URL}/api/v1/doi_author_groups"


def _group_body(**extra):
    return {"name": f"body-auth-test-{uuid.uuid4().hex[:8]}", "authors": [], **extra}


class TestApiTokenInBody:
    user_token = "test_token_user_002"

    def test_valid_token_in_body_authenticates(self):
        response = requests.post(GROUPS_URL, json=_group_body(api_token=self.user_token))
        assert response.status_code == status.HTTP_201_CREATED, response.text

    def test_valid_token_in_body_sets_deprecation_header(self):
        response = requests.post(GROUPS_URL, json=_group_body(api_token=self.user_token))
        assert "x-deprecation-warning" in response.headers

    def test_header_auth_does_not_set_deprecation_header(self):
        response = requests.post(
            GROUPS_URL, headers={"api_token": self.user_token}, json=_group_body()
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "x-deprecation-warning" not in response.headers

    def test_invalid_token_in_body_rejected(self):
        response = requests.post(GROUPS_URL, json=_group_body(api_token="not-a-real-token"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_no_token_anywhere_rejected(self):
        response = requests.post(GROUPS_URL, json=_group_body())
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_header_takes_precedence_over_body(self):
        response = requests.post(
            GROUPS_URL,
            headers={"api_token": self.user_token},
            json=_group_body(api_token="garbage"),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "x-deprecation-warning" not in response.headers

    def test_body_token_ignored_on_endpoint_with_no_body_schema(self):
        """/admin/fixdata declares no body, so FastAPI never buffers one for
        get_current_user to read, api_token in the JSON body can't authenticate
        there even though it works for body-bearing endpoints above."""
        response = requests.post(
            f"{API_BASE_URL}/api/v1/admin/fixdata", json={"api_token": "test_token_admin_001"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
