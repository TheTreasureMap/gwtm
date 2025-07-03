"""
Test event endpoints with real requests to the FastAPI application.
Tests use specific data from test-data.sql.
"""

import os
import requests
from datetime import datetime
import pytest
from fastapi import status

# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1_PREFIX = "/api/v1"


class TestEventEndpoints:
    """Test class for event-related API endpoints."""

    # Test API tokens from test data
    admin_token = "test_token_admin_001"
    user_token = "test_token_user_002"
    scientist_token = "test_token_sci_003"
    invalid_token = "invalid_token_123"

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    # Known GraceIDs from test data
    KNOWN_GRACEIDS = ["S190425z", "S190426c", "MS230101a", "GW190521", "MS190425a"]

    def test_query_alerts_no_params(self):
        """Test querying alerts without any parameters."""
        response = requests.get(
            self.get_url("/query_alerts"), headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should return alerts that exist in test data
        assert len(data) > 0
        for alert in data:
            assert "id" in alert
            assert "graceid" in alert

    def test_query_alerts_by_graceid(self):
        """Test querying alerts filtered by graceid."""
        response = requests.get(
            self.get_url("/query_alerts"),
            params={"graceid": "S190425z"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # All returned alerts should have the specified graceid
        for alert in data:
            assert alert["graceid"] == "S190425z"

    def test_query_alerts_by_alert_type(self):
        """Test querying alerts filtered by alert type."""
        response = requests.get(
            self.get_url("/query_alerts"),
            params={"alert_type": "Initial"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # All returned alerts should have the specified alert_type
        for alert in data:
            assert alert["alert_type"] == "Initial"

    def test_query_alerts_by_graceid_and_alert_type(self):
        """Test querying alerts filtered by both graceid and alert type."""
        response = requests.get(
            self.get_url("/query_alerts"),
            params={"graceid": "S190425z", "alert_type": "Initial"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # All returned alerts should match both filters
        for alert in data:
            assert alert["graceid"] == "S190425z"
            assert alert["alert_type"] == "Initial"

    def test_post_alert(self):
        """Test posting a new alert (admin only)."""
        alert_data = {
            "graceid": "TEST123",
            "alert_type": "Initial",
            "role": "test",
            "observing_run": "O4",
            "far": 1.5e-8,
            "group": "CBC",
            "timesent": "2025-05-01T12:00:00.000Z",
            "time_of_signal": "2025-05-01T11:58:20.000Z",
            "description": "Test event for API testing",
            "distance": 200.0,
            "distance_error": 50.0,
            "prob_bns": 0.8,
            "prob_nsbh": 0.15,
            "prob_bbh": 0.03,
            "prob_terrestrial": 0.02,
        }

        response = requests.post(
            self.get_url("/post_alert"),
            json=alert_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["graceid"] == alert_data["graceid"]
        assert data["alert_type"] == alert_data["alert_type"]
        assert data["prob_bns"] == alert_data["prob_bns"]

    def test_post_alert_unauthorized(self):
        """Test that non-admin users cannot post alerts."""
        alert_data = {
            "graceid": "TEST456",
            "alert_type": "Initial",
            "role": "test",
            "observing_run": "O4",
        }

        response = requests.post(
            self.get_url("/post_alert"),
            json=alert_data,
            headers={"api_token": self.user_token},
        )

        assert response.status_code == 403
        assert "admin" in response.json()["message"].lower()

    def test_get_gw_skymap(self):
        """Test getting a skymap FITS file."""
        response = requests.get(
            self.get_url("/gw_skymap"),
            params={"graceid": "S190425z"},
            headers={"api_token": self.admin_token},
        )

        # Even if the file doesn't exist in test data, we should get a valid response
        assert response.status_code in [200, 404]
        if response.status_code == status.HTTP_200_OK:
            assert response.headers["Content-Type"] == "application/fits"
        else:
            assert "Error in retrieving skymap file" in response.json()["message"]

    def test_get_gw_contour(self):
        """Test getting alert contour data."""
        response = requests.get(
            self.get_url("/gw_contour"),
            params={"graceid": "S190425z"},
            headers={"api_token": self.admin_token},
        )

        # Even if the file doesn't exist in test data, we should get a valid response
        assert response.status_code in [200, 404]
        if response.status_code == status.HTTP_200_OK:
            assert response.headers["Content-Type"] == "application/json"
        else:
            assert "Error in retrieving Contour file" in response.json()["message"]

    def test_get_grb_moc_file(self):
        """Test getting GRB MOC file."""
        response = requests.get(
            self.get_url("/grb_moc_file"),
            params={"graceid": "S190425z", "instrument": "gbm"},
            headers={"api_token": self.admin_token},
        )

        # Even if the file doesn't exist in test data, we should get a valid response
        assert response.status_code in [200, 404]
        if response.status_code == status.HTTP_200_OK:
            assert response.headers["Content-Type"] == "application/json"
        else:
            assert "MOC file" in response.json()["message"]

    def test_get_grb_moc_file_invalid_instrument(self):
        """Test getting GRB MOC file with invalid instrument."""
        response = requests.get(
            self.get_url("/grb_moc_file"),
            params={"graceid": "S190425z", "instrument": "invalid"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Valid instruments are" in response.json()["message"]

    def test_del_test_alerts(self):
        """Test deleting test alerts (admin only)."""
        # First create a test alert that should be deleted
        alert_data = {
            "graceid": f"MS{datetime.now().strftime('%y%m%d')}test",
            "alert_type": "Initial",
            "role": "test",
            "observing_run": "O4",
        }

        # Create the test alert
        create_response = requests.post(
            self.get_url("/post_alert"),
            json=alert_data,
            headers={"api_token": self.admin_token},
        )
        assert create_response.status_code == status.HTTP_200_OK

        # Now try to delete test alerts
        response = requests.post(
            self.get_url("/del_test_alerts"), headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Successfully deleted test alerts" in response.json()["message"]

    def test_del_test_alerts_unauthorized(self):
        """Test that non-admin users cannot delete test alerts."""
        response = requests.post(
            self.get_url("/del_test_alerts"), headers={"api_token": self.user_token}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "admin" in response.json()["message"].lower()

    def test_event_api_unauthorized_access(self):
        """Test that unauthorized requests are rejected."""
        # Request without API token
        response = requests.get(self.get_url("/query_alerts"))
        assert response.status_code == 401

        # Request with invalid API token
        response = requests.get(
            self.get_url("/query_alerts"), headers={"api_token": self.invalid_token}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_event_api_with_different_tokens(self):
        """Test access with different valid API tokens."""
        # All authenticated users should be able to query alerts
        for token in [self.admin_token, self.user_token, self.scientist_token]:
            response = requests.get(
                self.get_url("/query_alerts"), headers={"api_token": token}
            )
            assert response.status_code == status.HTTP_200_OK


class TestEventAPIValidation:
    """Test validation of event API endpoints."""

    admin_token = "test_token_admin_001"

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    def test_post_alert_missing_required_fields(self):
        """Test creating alert with missing required fields."""
        incomplete_alert = {
            "graceid": "TEST789"
            # Missing alert_type, role, etc.
        }

        response = requests.post(
            self.get_url("/post_alert"),
            json=incomplete_alert,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_detail = response.json()["errors"]
        missing_fields = [field["params"]["field"] for field in error_detail]
        assert "alert_type" in str(missing_fields)
        assert "role" in str(missing_fields)

    def test_post_alert_invalid_values(self):
        """Test creating alert with invalid field values."""
        invalid_alert = {
            "graceid": "TEST999",
            "alert_type": "Initial",
            "role": "test",
            "observing_run": "O4",
            "prob_bns": 1.5,  # Invalid probability > 1
            "prob_nsbh": -0.2,  # Invalid negative probability
        }

        response = requests.post(
            self.get_url("/post_alert"),
            json=invalid_alert,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_detail = response.json()["errors"]
        assert "prob_bns" in str(error_detail) or "prob_nsbh" in str(error_detail)

    def test_get_skymap_without_graceid(self):
        """Test getting skymap without providing graceid."""
        response = requests.get(
            self.get_url("/gw_skymap"), headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "graceid" in str(response.json()["errors"][0])

    def test_get_grb_moc_without_params(self):
        """Test getting GRB MOC file without required parameters."""
        # Missing instrument
        response = requests.get(
            self.get_url("/grb_moc_file"),
            params={"graceid": "S190425z"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "instrument" in str(response.json()["errors"][0])

        # Missing graceid
        response = requests.get(
            self.get_url("/grb_moc_file"),
            params={"instrument": "gbm"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "graceid" in str(response.json()["errors"][0])


class TestEventAPIIntegration:
    """Integration tests for event API endpoints."""

    admin_token = "test_token_admin_001"

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    def test_create_query_alert_workflow(self):
        """Test complete workflow: create, query, and fetch data for an alert."""
        # Step 1: Create new alert
        event_time = datetime.now().isoformat()
        unique_id = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}"

        alert_data = {
            "graceid": unique_id,
            "alert_type": "Initial",
            "role": "test",
            "observing_run": "O4",
            "far": 2.5e-8,
            "group": "CBC",
            "timesent": event_time,
            "time_of_signal": event_time,
            "description": "Integration test event",
            "distance": 150.0,
            "distance_error": 30.0,
            "prob_bns": 0.75,
            "prob_nsbh": 0.15,
            "prob_bbh": 0.05,
            "prob_terrestrial": 0.05,
        }

        create_response = requests.post(
            self.get_url("/post_alert"),
            json=alert_data,
            headers={"api_token": self.admin_token},
        )
        assert create_response.status_code == status.HTTP_200_OK
        created_alert = create_response.json()
        assert created_alert["graceid"] == unique_id

        # Step 2: Query the created alert
        query_response = requests.get(
            self.get_url("/query_alerts"),
            params={"graceid": unique_id},
            headers={"api_token": self.admin_token},
        )
        assert query_response.status_code == status.HTTP_200_OK
        queried_alerts = query_response.json()
        assert len(queried_alerts) == 1
        assert queried_alerts[0]["graceid"] == unique_id
        assert queried_alerts[0]["prob_bns"] == alert_data["prob_bns"]

        # Step 3: Clean up - delete the test alert using del_test_alerts
        delete_response = requests.post(
            self.get_url("/del_test_alerts"), headers={"api_token": self.admin_token}
        )
        assert delete_response.status_code == status.HTTP_200_OK

        # Step 4: Verify deletion
        verify_response = requests.get(
            self.get_url("/query_alerts"),
            params={"graceid": unique_id},
            headers={"api_token": self.admin_token},
        )
        assert verify_response.status_code == status.HTTP_200_OK
        assert len(verify_response.json()) == 0  # Should be empty

    def test_multiple_alerts_same_event(self):
        """Test creating and querying multiple alerts for the same event."""
        # Create base event ID
        event_id = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}_MULTI"

        # Create initial alert
        initial_alert = {
            "graceid": event_id,
            "alert_type": "Initial",
            "role": "test",
            "observing_run": "O4",
            "description": "Multi-alert test - Initial",
        }
        response = requests.post(
            self.get_url("/post_alert"),
            json=initial_alert,
            headers={"api_token": self.admin_token},
        )
        assert response.status_code == status.HTTP_200_OK

        # Create update alert for same event
        update_alert = {
            "graceid": event_id,
            "alert_type": "Update",
            "role": "test",
            "observing_run": "O4",
            "description": "Multi-alert test - Update",
        }
        response = requests.post(
            self.get_url("/post_alert"),
            json=update_alert,
            headers={"api_token": self.admin_token},
        )
        assert response.status_code == status.HTTP_200_OK

        # Query all alerts for this event
        query_response = requests.get(
            self.get_url("/query_alerts"),
            params={"graceid": event_id},
            headers={"api_token": self.admin_token},
        )
        assert query_response.status_code == status.HTTP_200_OK
        alerts = query_response.json()
        assert len(alerts) == 2

        # Verify we have both alert types
        alert_types = [alert["alert_type"] for alert in alerts]
        assert "Initial" in alert_types
        assert "Update" in alert_types

        # Clean up
        requests.post(
            self.get_url("/del_test_alerts"), headers={"api_token": self.admin_token}
        )


class TestEventSpecificData:
    """Test event endpoints with specific test data values."""

    BASE_URL = f"{API_BASE_URL}{API_V1_PREFIX}"
    admin_token = "test_token_admin_001"

    def test_known_event_s190425z(self):
        """Test querying the known S190425z event from test data."""
        headers = {"api_token": self.admin_token}

        response = requests.get(
            f"{self.BASE_URL}/query_alerts",
            params={"graceid": "S190425z"},
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        alerts = response.json()
        assert len(alerts) > 0

        # Check expected fields in first alert
        alert = alerts[0]
        assert alert["graceid"] == "S190425z"
        assert "alert_type" in alert
        assert "far" in alert
        assert "time_of_signal" in alert

        # Verify classification info is present
        has_probs = any(
            key in alert
            for key in ["prob_bns", "prob_nsbh", "prob_bbh", "prob_terrestrial"]
        )
        assert has_probs

    def test_query_by_alert_properties(self):
        """Test querying events with BNS classification."""
        headers = {"api_token": self.admin_token}

        # First get all alerts
        response = requests.get(f"{self.BASE_URL}/query_alerts", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        all_alerts = response.json()

        # Filter for BNS candidates (prob_bns > 0.9)
        bns_candidates = [
            alert
            for alert in all_alerts
            if alert.get("prob_bns") is not None and alert.get("prob_bns") > 0.9
        ]

        if bns_candidates:
            # Test querying one specific BNS candidate
            sample_bns = bns_candidates[0]
            response = requests.get(
                f"{self.BASE_URL}/query_alerts",
                params={"graceid": sample_bns["graceid"]},
                headers=headers,
            )

            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert len(result) > 0
            assert result[0]["graceid"] == sample_bns["graceid"]
            assert result[0]["prob_bns"] > 0.9


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
