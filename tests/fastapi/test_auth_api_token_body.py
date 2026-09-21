"""Tests for the deprecated api_token-in-JSON-body auth fallback."""

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

    def test_valid_token_in_body_authenticates_and_warns(self):
        response = requests.post(GROUPS_URL, json=_group_body(api_token=self.user_token))
        assert response.status_code == status.HTTP_201_CREATED, response.text
        assert "x-deprecation-warning" in response.headers

    def test_invalid_token_in_body_rejected(self):
        response = requests.post(GROUPS_URL, json=_group_body(api_token="not-a-real-token"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nul_in_body_token_rejected_not_a_server_error(self):
        response = requests.post(GROUPS_URL, json=_group_body(api_token="a\x00b"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_no_token_anywhere_rejected(self):
        response = requests.post(GROUPS_URL, json=_group_body())
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_header_takes_precedence_over_body_and_does_not_warn(self):
        response = requests.post(
            GROUPS_URL,
            headers={"api_token": self.user_token},
            json=_group_body(api_token="garbage"),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "x-deprecation-warning" not in response.headers

    def test_body_token_works_on_endpoint_that_parses_its_own_body(self):
        response = requests.post(
            f"{API_BASE_URL}/ajax_grade_calculator",
            json={"api_token": self.user_token, "pointing_ids": [1]},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        assert "x-deprecation-warning" in response.headers
