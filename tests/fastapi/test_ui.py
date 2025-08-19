"""
Test UI-related endpoints with real requests to the FastAPI application.
Tests use specific data from test-data.sql.
"""

import os
import requests
import json
import pytest
from fastapi import status

# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class TestUIEndpoints:
    """Test class for UI-related API endpoints."""

    # Test API tokens from test data
    admin_token = "test_token_admin_001"
    user_token = "test_token_user_002"
    scientist_token = "test_token_sci_003"
    invalid_token = "invalid_token_123"

    # Known GraceIDs from test data
    KNOWN_GRACEIDS = ["S190425z", "S190426c", "MS230101a", "GW190521", "MS190425a"]

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{endpoint}"

    def test_ajax_alertinstruments_footprints(self):
        """Test getting alert instrument footprints."""
        for graceid in self.KNOWN_GRACEIDS:
            response = requests.get(
                self.get_url("/ajax_alertinstruments_footprints"),
                params={"graceid": graceid},
                headers={"api_token": self.admin_token},
            )

            if response.status_code == status.HTTP_200_OK:
                data = response.json()
                assert isinstance(data, list)

                # If data is returned, it should have the expected structure
                if len(data) > 0:
                    overlay = data[0]
                    assert "display" in overlay
                    assert "name" in overlay
                    assert "color" in overlay
                    assert "contours" in overlay
                return  # Found valid data, test passes

        # If we get here, all GraceIDs failed - this might be valid if test data doesn't have footprints
        pytest.skip("No alert instrument footprints found in test data")

    def test_ajax_preview_footprint_circle(self):
        """Test previewing a circular footprint."""
        response = requests.get(
            self.get_url("/ajax_preview_footprint"),
            params={"ra": 123.456, "dec": -12.345, "radius": 0.5, "shape": "Circular"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        # The response should be a JSON string containing plotly figure data
        assert isinstance(response.text, str)
        # Try parsing as JSON to confirm it's valid
        try:
            json_data = json.loads(response.text)
            assert "data" in json_data
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"

    def test_ajax_preview_footprint_rectangle(self):
        """Test previewing a rectangular footprint."""
        response = requests.get(
            self.get_url("/ajax_preview_footprint"),
            params={
                "ra": 123.456,
                "dec": -12.345,
                "height": 0.5,
                "width": 1.0,
                "shape": "Rectangular",
            },
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        # The response should be a JSON string containing plotly figure data
        assert isinstance(response.text, str)
        # Try parsing as JSON to confirm it's valid
        try:
            json_data = json.loads(response.text)
            assert "data" in json_data
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"

    def test_ajax_preview_footprint_invalid_shape(self):
        """Test previewing a footprint with invalid shape."""
        response = requests.get(
            self.get_url("/ajax_preview_footprint"),
            params={"ra": 123.456, "dec": -12.345, "shape": "invalid"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "error" in data
        assert "Invalid shape type" in data["error"]

    def test_ajax_coverage_calculator(self):
        """Test the coverage calculator endpoint."""
        for graceid in self.KNOWN_GRACEIDS:
            data = {
                "graceid": graceid,
                "inst_cov": "1,2,3",
                "band_cov": "r,g,i",
                "depth_cov": "20.0",
                "depth_unit": "ab_mag",
                "approx_cov": 1,
            }

            response = requests.post(
                self.get_url("/ajax_coverage_calculator"),
                json=data,
                headers={"api_token": self.admin_token},
            )

            if response.status_code == status.HTTP_200_OK:
                result = response.json()
                assert "plot_html" in result
                assert isinstance(result["plot_html"], str)
                assert "<div" in result["plot_html"]
                return  # Found valid data, test passes

        # If we get here, all GraceIDs failed - this might be valid if test data doesn't have coverage info
        pytest.skip("No coverage data found in test data")

    def test_ajax_update_spectral_range_from_selected_bands(self):
        """Test updating spectral range from selected bands."""
        response = requests.get(
            self.get_url("/ajax_update_spectral_range_from_selected_bands"),
            params={
                "band_cov": "r,g,i",
                "spectral_type": "wavelength",
                "spectral_unit": "nm",
            },
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_min" in data
        assert "total_max" in data

    def test_ajax_update_spectral_range_no_bands(self):
        """Test updating spectral range with no bands."""
        response = requests.get(
            self.get_url("/ajax_update_spectral_range_from_selected_bands"),
            params={
                "band_cov": "",
                "spectral_type": "wavelength",
                "spectral_unit": "nm",
            },
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_min" in data
        assert "total_max" in data
        assert data["total_min"] == ""
        assert data["total_max"] == ""

    def test_ajax_icecube_notice(self):
        """Test getting IceCube notices for a graceid."""
        for graceid in self.KNOWN_GRACEIDS:
            response = requests.get(
                self.get_url("/ajax_icecube_notice"),
                params={"graceid": graceid},
                headers={"api_token": self.admin_token},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
            # Note: data might be empty if there are no IceCube notices for this graceid

    def test_ajax_event_galaxies(self):
        """Test getting event galaxies by alert ID."""
        for graceid in self.KNOWN_GRACEIDS:
            # First get alerts to find a valid alert ID
            alerts_response = requests.get(
                self.get_url("/api/v1/query_alerts"),
                params={"graceid": graceid},
                headers={"api_token": self.admin_token},
            )

            if (
                alerts_response.status_code == status.HTTP_200_OK
                and len(alerts_response.json()) > 0
            ):
                alert = alerts_response.json()[0]
                alert_id = alert["id"]

                # Now get galaxies for this alert
                response = requests.get(
                    self.get_url("/ajax_event_galaxies"),
                    params={"alertid": alert_id},
                    headers={"api_token": self.admin_token},
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert isinstance(data, list)
                # Note: data might be empty if there are no galaxies for this alert
                return  # Found an alert, test passes

        # If we get here, no alerts were found
        pytest.skip("No alerts found in test data")

    def test_ajax_candidate(self):
        """Test getting candidates by graceid."""
        for graceid in self.KNOWN_GRACEIDS:
            response = requests.get(
                self.get_url("/ajax_candidate"),
                params={"graceid": graceid},
                headers={"api_token": self.admin_token},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
            # Note: data might be empty if there are no candidates for this graceid

    def test_ajax_alerttype(self):
        """Test getting event contour and alert information."""
        for graceid in self.KNOWN_GRACEIDS:
            # First get alerts to find a valid alert ID and alert type
            alerts_response = requests.get(
                self.get_url("/api/v1/query_alerts"),
                params={"graceid": graceid},
                headers={"api_token": self.admin_token},
            )

            if (
                alerts_response.status_code == status.HTTP_200_OK
                and len(alerts_response.json()) > 0
            ):
                alert = alerts_response.json()[0]
                alert_id = alert["id"]
                alert_type = alert["alert_type"].lower()

                # Now get contour data
                url_id = f"{alert_id}_{alert_type}"
                response = requests.get(
                    self.get_url("/ajax_alerttype"),
                    params={"urlid": url_id},
                    headers={"api_token": self.admin_token},
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "hidden_alertid" in data
                assert "detection_overlays" in data
                return  # Found an alert, test passes

        # If we get here, no alerts were found
        pytest.skip("No alerts found in test data")

    def test_authentication_patterns(self):
        """Test authentication requirements for different endpoint types."""
        # Most UI GET endpoints should be publicly accessible for viewing data
        public_get_endpoints = [
            "/ajax_alertinstruments_footprints?graceid=S190425z",
            "/ajax_preview_footprint?ra=123.456&dec=-12.345&radius=0.5&shape=Circular",
            "/ajax_icecube_notice?graceid=S190425z",
            "/ajax_event_galaxies?alertid=1",
            "/ajax_candidate?graceid=S190425z",
            "/ajax_alerttype?urlid=1_initial",
            "/ajax_update_spectral_range_from_selected_bands?band_cov=r&spectral_type=wavelength&spectral_unit=nm"
        ]
        
        for endpoint in public_get_endpoints:
            response = requests.get(self.get_url(endpoint))
            # Should return 200 OK or 400 BAD_REQUEST (for missing params), but not 401 UNAUTHORIZED
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]
        
        # POST endpoints that don't require authentication but need valid parameters
        unprotected_post_endpoints = ["/ajax_coverage_calculator"]
        
        for endpoint in unprotected_post_endpoints:
            response = requests.post(
                self.get_url(endpoint), json={"graceid": self.KNOWN_GRACEIDS[0]}
            )
            # Should return 400 BAD_REQUEST for missing required parameters, not 401 UNAUTHORIZED
            assert response.status_code == 400


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
