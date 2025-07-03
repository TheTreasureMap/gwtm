"""
Test admin endpoints with real requests to the FastAPI application.
Tests use specific data from test-data.sql.
"""

import os
import requests
import pytest
from fastapi import status

# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class TestAdminEndpoints:
    """Test class for admin-related API endpoints."""

    # Test API tokens from test data
    admin_token = "test_token_admin_001"
    user_token = "test_token_user_002"
    scientist_token = "test_token_sci_003"
    invalid_token = "invalid_token_123"

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{endpoint}"

    def test_fixdata_as_admin_get(self):
        """Test the fixdata endpoint with GET as admin."""
        response = requests.get(
            self.get_url("/fixdata"), headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["message"] == "success"

    def test_fixdata_as_admin_post(self):
        """Test the fixdata endpoint with POST as admin."""
        response = requests.post(
            self.get_url("/fixdata"), headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["message"] == "success"

    def test_fixdata_as_non_admin(self):
        """Test that non-admin users cannot use the fixdata endpoint."""
        # Test with regular user token
        response = requests.get(
            self.get_url("/fixdata"), headers={"api_token": self.user_token}
        )

        assert response.status_code == 403

        # Test with scientist token
        response = requests.get(
            self.get_url("/fixdata"), headers={"api_token": self.scientist_token}
        )

        assert response.status_code == 403

    def test_fixdata_without_auth(self):
        """Test that authentication is required for fixdata endpoint."""
        response = requests.get(self.get_url("/fixdata"))
        assert response.status_code == 401

    def test_fixdata_with_invalid_token(self):
        """Test fixdata with invalid API token."""
        response = requests.get(
            self.get_url("/fixdata"), headers={"api_token": self.invalid_token}
        )
        assert response.status_code == 401


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
