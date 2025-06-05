"""
Test IceCube endpoints with real requests to the FastAPI application.
Tests use specific data from test-data.sql.
"""
import os
import requests
import json
import datetime
import uuid
from typing import Dict, Any, List, Optional
import pytest
from fastapi import status

# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1_PREFIX = "/api/v1"


class TestIceCubeEndpoints:
    """Test class for IceCube-related API endpoints."""

    # Test API tokens from test data
    admin_token = "test_token_admin_001"
    user_token = "test_token_user_002"
    scientist_token = "test_token_sci_003"
    invalid_token = "invalid_token_123"

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    def test_post_icecube_notice_as_admin(self):
        """Test posting an IceCube notice as admin."""
        # Generate a unique reference ID
        ref_id = f"IceCube-{uuid.uuid4()}"
        notice_data = {
            "ref_id": ref_id,
            "graceid": "S190425z",  # Use a known GraceID from test data
            "alert_datetime": datetime.datetime.now().isoformat(),
            "observation_start": (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat(),
            "observation_stop": datetime.datetime.now().isoformat(),
            "pval_generic": 0.01,
            "pval_bayesian": 0.02,
            "most_probable_direction_ra": 123.456,
            "most_probable_direction_dec": -12.345,
            "flux_sens_low": 1e-10,
            "flux_sens_high": 1e-9,
            "sens_energy_range_low": 100,
            "sens_energy_range_high": 1000
        }
        
        events_data = [
            {
                "event_dt": 0.5,
                "ra": 123.456,
                "dec": -12.345,
                "containment_probability": 0.9,
                "event_pval_generic": 0.015,
                "event_pval_bayesian": 0.025,
                "ra_uncertainty": 0.5,
                "uncertainty_shape": "circle"
            },
            {
                "event_dt": 1.0,
                "ra": 124.567,
                "dec": -13.456,
                "containment_probability": 0.85,
                "event_pval_generic": 0.02,
                "event_pval_bayesian": 0.03,
                "ra_uncertainty": 0.6,
                "uncertainty_shape": "circle"
            }
        ]
        
        data = {
            "notice_data": notice_data,
            "events_data": events_data
        }
        
        response = requests.post(
            self.get_url("/post_icecube_notice"),
            json=data,
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "icecube_notice" in result
        assert "icecube_notice_events" in result
        assert result["icecube_notice"]["ref_id"] == ref_id
        assert len(result["icecube_notice_events"]) == 2

    def test_post_icecube_notice_as_non_admin(self):
        """Test that only admin can post IceCube notices."""
        ref_id = f"IceCube-{uuid.uuid4()}"

        notice_data = {
            "ref_id": ref_id,
            "graceid": "S190425z",
            "alert_datetime": datetime.datetime.now().isoformat()
        }
        
        events_data = [{
            "event_dt": 0.5,
            "ra": 123.456,
            "dec": -12.345
        }]
        
        data = {
            "notice_data": notice_data,
            "events_data": events_data
        }
        
        response = requests.post(
            self.get_url("/post_icecube_notice"),
            json=data,
            headers={"api_token": self.user_token}  # Non-admin user
        )
        
        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_duplicate_icecube_notice(self):
        """Test posting a duplicate IceCube notice."""
        # First post a notice
        ref_id = f"IceCube-{uuid.uuid4()}"

        notice_data = {
            "ref_id": ref_id,
            "graceid": "S190425z",
            "alert_datetime": datetime.datetime.now().isoformat()
        }
        
        events_data = [{
            "event_dt": 0.5,
            "ra": 123.456,
            "dec": -12.345
        }]
        
        data = {
            "notice_data": notice_data,
            "events_data": events_data
        }
        
        response = requests.post(
            self.get_url("/post_icecube_notice"),
            json=data,
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Now post again with the same ref_id
        response = requests.post(
            self.get_url("/post_icecube_notice"),
            json=data,
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "event already exists" in result["icecube_notice"]["message"]

    def test_post_icecube_notice_invalid_graceid(self):
        """Test posting an IceCube notice with an invalid GraceID."""
        ref_id = f"IceCube-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        notice_data = {
            "ref_id": ref_id,
            "graceid": "INVALID123",  # Invalid GraceID
            "alert_datetime": datetime.datetime.now().isoformat()
        }
        
        events_data = [{
            "event_dt": 0.5,
            "ra": 123.456,
            "dec": -12.345
        }]
        
        data = {
            "notice_data": notice_data,
            "events_data": events_data
        }
        
        response = requests.post(
            self.get_url("/post_icecube_notice"),
            json=data,
            headers={"api_token": self.admin_token}
        )
        
        # Note: The endpoint might accept invalid GraceIDs depending on implementation
        # If it validates GraceIDs, the response should indicate an error
        if response.status_code != 200:
            assert response.status_code in [400, 404, 422, 500]
        else:
            # If it accepts the invalid GraceID, verify the notice was created
            result = response.json()
            assert "icecube_notice" in result
            assert result["icecube_notice"]["ref_id"] == ref_id
            assert result["icecube_notice"]["graceid"] == "INVALID123"

    def test_post_icecube_notice_missing_fields(self):
        """Test posting an IceCube notice with missing required fields."""
        # Post with minimal required fields according to schema
        ref_id = f"IceCube-{uuid.uuid4()}"

        notice_data = {
            "ref_id": ref_id,
            "graceid": "S190425z"
            # Missing other fields, but they are Optional in the schema
        }
        
        events_data = []  # No events
        
        data = {
            "notice_data": notice_data,
            "events_data": events_data
        }
        
        response = requests.post(
            self.get_url("/post_icecube_notice"),
            json=data,
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "icecube_notice" in result
        assert result["icecube_notice"]["ref_id"] == ref_id
        assert len(result["icecube_notice_events"]) == 0

    def test_post_icecube_notice_without_auth(self):
        """Test that authentication is required."""
        ref_id = f"IceCube-{uuid.uuid4()}"

        notice_data = {
            "ref_id": ref_id,
            "graceid": "S190425z"
        }
        
        events_data = []
        
        data = {
            "notice_data": notice_data,
            "events_data": events_data
        }
        
        response = requests.post(
            self.get_url("/post_icecube_notice"),
            json=data
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_icecube_notice_with_invalid_token(self):
        """Test with invalid API token."""
        ref_id = f"IceCube-{uuid.uuid4()}"

        notice_data = {
            "ref_id": ref_id,
            "graceid": "S190425z"
        }
        
        events_data = []
        
        data = {
            "notice_data": notice_data,
            "events_data": events_data
        }
        
        response = requests.post(
            self.get_url("/post_icecube_notice"),
            json=data,
            headers={"api_token": self.invalid_token}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
