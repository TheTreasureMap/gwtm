"""
Test GW alert endpoints with real requests to the FastAPI application.
Tests use specific data from test-data.sql.
"""
import os
import requests
import json
import io
import datetime
from typing import Dict, Any, List, Optional
import pytest
from fastapi import status

# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1_PREFIX = "/api/v1"


class TestGWAlertEndpoints:
    """Test class for GW alert-related API endpoints."""

    # Test API tokens from test data
    admin_token = "test_token_admin_001"
    user_token = "test_token_user_002"
    scientist_token = "test_token_sci_003"
    invalid_token = "invalid_token_123"

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    # Known GraceIDs from test data
    KNOWN_GRACEIDS = ['S190425z', 'S190426c', 'GW190521']

    def test_query_alerts_no_params(self):
        """Test querying alerts without any parameters."""
        response = requests.get(
            self.get_url("/query_alerts"),
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should return all alerts in test data
        assert len(data) >= 4  # At least our known graceids

    def test_query_alerts_by_graceid(self):
        """Test querying alerts by graceid."""
        for graceid in self.KNOWN_GRACEIDS:
            response = requests.get(
                self.get_url("/query_alerts"),
                params={"graceid": graceid},
                headers={"api_token": self.admin_token}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            # All returned alerts should have the specified graceid
            for alert in data:
                assert alert["graceid"] == graceid

    def test_query_alerts_by_alert_type(self):
        """Test querying alerts by alert type."""
        # Test for common alert types
        alert_types = ["Initial", "Update", "Retraction"]
        
        for alert_type in alert_types:
            response = requests.get(
                self.get_url("/query_alerts"),
                params={"alert_type": alert_type},
                headers={"api_token": self.admin_token}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
            
            # Skip if no alerts of this type in test data
            if len(data) > 0:
                # All returned alerts should have the specified alert_type
                for alert in data:
                    assert alert["alert_type"] == alert_type

    def test_query_alerts_graceid_and_alert_type(self):
        """Test querying alerts by both graceid and alert type."""
        response = requests.get(
            self.get_url("/query_alerts"),
            params={"graceid": "S190425z", "alert_type": "Initial"},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        
        # Skip if no matching alerts in test data
        if len(data) > 0:
            # All returned alerts should match both parameters
            for alert in data:
                assert alert["graceid"] == "S190425z"
                assert alert["alert_type"] == "Initial"

    def test_query_alerts_without_auth(self):
        """Test that authentication is required."""
        response = requests.get(self.get_url("/query_alerts"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_query_alerts_with_invalid_token(self):
        """Test with invalid API token."""
        response = requests.get(
            self.get_url("/query_alerts"),
            headers={"api_token": self.invalid_token}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_alert_as_admin(self):
        """Test posting a new GW alert as admin."""
        alert_data = {
            "graceid": f"TEST{datetime.datetime.now().strftime('%y%m%d%H%M%S')}",
            "alternateid": "",
            "role": "test",
            "observing_run": "O4",
            "description": "Test alert creation",
            "alert_type": "Initial",
            "far": 1e-9,
            "group": "CBC",
            "detectors": "H1,L1",
            "prob_hasns": 0.95,
            "prob_hasremenant": 0.9,
            "prob_bns": 0.8,
            "prob_nsbh": 0.1,
            "prob_bbh": 0.05,
            "prob_terrestrial": 0.05,
            "skymap_fits_url": "https://example.com/skymap.fits",
            "avgra": 123.456,
            "avgdec": -12.345,
            "time_of_signal": datetime.datetime.now().isoformat(),
            "distance": 100.0,
            "distance_error": 10.0
        }

        response = requests.post(
            self.get_url("/post_alert"),
            json=alert_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "graceid" in data
        assert data["graceid"] == alert_data["graceid"]
        assert data["role"] == "test"
        assert data["alert_type"] == "Initial"

    def test_post_alert_as_non_admin(self):
        """Test that only admin can post alerts."""
        alert_data = {
            "graceid": f"TEST{datetime.datetime.now().strftime('%y%m%d%H%M%S')}",
            "role": "test",
            "alert_type": "Initial"
        }

        response = requests.post(
            self.get_url("/post_alert"),
            json=alert_data,
            headers={"api_token": self.user_token}  # Non-admin user
        )

        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_gw_skymap(self):
        """Test getting a GW skymap FITS file."""
        for graceid in self.KNOWN_GRACEIDS:
            response = requests.get(
                self.get_url("/gw_skymap"),
                params={"graceid": graceid},
                headers={"api_token": self.admin_token}
            )

            # If skymap exists, should return 200, otherwise 404
            if response.status_code == status.HTTP_200_OK:
                # Should return binary data with FITS header
                assert response.headers["Content-Type"] == "application/fits"
                assert response.headers["Content-Disposition"].startswith("attachment; filename=")
                assert len(response.content) > 0
                break  # Found a valid skymap, no need to try others
            else:
                # Graceid might not have a skymap in test data
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "Error in retrieving skymap file" in response.json()["message"]

    def test_get_gw_contour(self):
        """Test getting GW contour data."""
        for graceid in self.KNOWN_GRACEIDS:
            response = requests.get(
                self.get_url("/gw_contour"),
                params={"graceid": graceid},
                headers={"api_token": self.admin_token}
            )

            # If contour exists, should return 200, otherwise 404
            if response.status_code == status.HTTP_200_OK:
                # Should return JSON data
                assert response.headers["Content-Type"] == "application/json"
                # Try to parse as JSON to confirm it's valid
                try:
                    json_data = response.json()
                    assert isinstance(json_data, dict)
                except json.JSONDecodeError:
                    # If it's not valid JSON, the test should fail
                    assert False, "Response is not valid JSON"
                break  # Found a valid contour, no need to try others
            else:
                # Graceid might not have a contour in test data
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "Error in retrieving Contour file" in response.json()["message"]

    def test_get_grb_moc_file(self):
        """Test getting a GRB MOC file."""
        instruments = ["gbm", "lat", "bat"]
        
        for graceid in self.KNOWN_GRACEIDS:
            for instrument in instruments:
                response = requests.get(
                    self.get_url("/grb_moc_file"),
                    params={"graceid": graceid, "instrument": instrument},
                    headers={"api_token": self.admin_token}
                )

                # If MOC file exists, should return 200, otherwise 404
                if response.status_code == status.HTTP_200_OK:
                    # Should return JSON data
                    assert response.headers["Content-Type"] == "application/json"
                    # Try to parse as JSON to confirm it's valid
                    try:
                        json_data = response.json()
                        assert isinstance(json_data, dict)
                    except json.JSONDecodeError:
                        # If it's not valid JSON, the test should fail
                        assert False, "Response is not valid JSON"
                    return  # Found a valid MOC file, test is complete
        
        # If we get here, no MOC files were found for any graceid/instrument combination
        # This is expected in test data, so we'll skip this test
        pytest.skip("No GRB MOC files found in test data")

    def test_get_grb_moc_file_invalid_instrument(self):
        """Test getting a GRB MOC file with invalid instrument."""
        response = requests.get(
            self.get_url("/grb_moc_file"),
            params={"graceid": "S190425z", "instrument": "invalid"},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Valid instruments are in ['gbm', 'lat', 'bat']" in response.json()["message"]


    def test_del_test_alerts_as_non_admin(self):
        """Test that only admin can delete test alerts."""
        response = requests.post(
            self.get_url("/del_test_alerts"),
            headers={"api_token": self.user_token}  # Non-admin user
        )

        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_alerts_with_different_tokens(self):
        """Test alert queries with different valid API tokens."""
        # All authenticated users should be able to query alerts
        for token in [self.admin_token, self.user_token, self.scientist_token]:
            response = requests.get(
                self.get_url("/query_alerts"),
                headers={"api_token": token}
            )
            assert response.status_code == status.HTTP_200_OK

    def test_alert_data_format(self):
        """Test that alert data is returned in the correct format."""
        response = requests.get(
            self.get_url("/query_alerts"),
            params={"graceid": "S190425z"},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        alerts = response.json()
        
        if len(alerts) == 0:
            pytest.skip("No alerts found for S190425z in test data")
            
        alert = alerts[0]
        
        # Check required fields
        required_fields = ["id", "graceid", "alert_type", "datecreated", "role"]
        for field in required_fields:
            assert field in alert

        # Check data types
        assert isinstance(alert["id"], int)
        assert isinstance(alert["graceid"], str)
        assert isinstance(alert["alert_type"], str)
        
        # Make sure time fields are parseable as ISO 8601
        for time_field in ["datecreated", "time_of_signal", "timesent"]:
            if time_field in alert and alert[time_field]:
                try:
                    datetime.datetime.fromisoformat(alert[time_field].replace("Z", "+00:00"))
                except ValueError:
                    assert False, f"Time field {time_field} is not in ISO 8601 format"



if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
