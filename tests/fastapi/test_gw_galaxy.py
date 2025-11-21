"""
Test GW galaxy endpoints with real requests to the FastAPI application.
Tests use specific data from test-data.sql.
"""

import os
import requests
import pytest
from fastapi import status

# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1_PREFIX = "/api/v1"


class TestGWGalaxyEndpoints:
    """Test class for GW galaxy-related API endpoints."""

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

    # Test timestamps (based on test data)
    test_timestamp = "2019-04-25T08:18:05.123456"

    def test_get_event_galaxies_no_params(self):
        """Test getting event galaxies without proper parameters."""
        response = requests.get(
            self.get_url("/event_galaxies"), headers={"api_token": self.admin_token}
        )

        # Should fail with 422 - Missing required parameter
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_event_galaxies_with_graceid(self):
        """Test getting event galaxies with valid graceid."""
        for graceid in self.KNOWN_GRACEIDS:
            response = requests.get(
                self.get_url("/event_galaxies"),
                params={"graceid": graceid},
                headers={"api_token": self.admin_token},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
            # Note: Test may pass even if empty list - depends on test data

    def test_get_event_galaxies_with_invalid_timesent(self):
        """Test getting event galaxies with invalid timestamp."""
        response = requests.get(
            self.get_url("/event_galaxies"),
            params={
                "graceid": self.KNOWN_GRACEIDS[0],
                "timesent_stamp": "invalid-timestamp",
            },
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Error parsing date" in response.json()["message"]

    def test_get_event_galaxies_with_nonexistent_timesent(self):
        """Test getting event galaxies with timestamp that doesn't match any alert."""
        response = requests.get(
            self.get_url("/event_galaxies"),
            params={
                "graceid": self.KNOWN_GRACEIDS[0],
                "timesent_stamp": "2099-01-01T12:00:00.000000",  # Future date
            },
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid 'timesent_stamp' for event" in response.json()["message"]

    def test_get_event_galaxies_with_score_filters(self):
        """Test getting event galaxies with score filters."""
        graceid = self.KNOWN_GRACEIDS[0]

        # First try to post some galaxies to ensure test data
        self.post_test_galaxy_data(graceid)

        # Now query with score filters
        response = requests.get(
            self.get_url("/event_galaxies"),
            params={"graceid": graceid, "score_gt": 0.5, "score_lt": 1.0},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

        # Check that all returned galaxies have scores in the specified range
        for galaxy in data:
            if "score" in galaxy:
                assert 0.5 <= galaxy["score"] <= 1.0

    def test_post_event_galaxies(self):
        """Test posting event galaxies."""
        graceid = self.KNOWN_GRACEIDS[0]
        response = self.post_test_galaxy_data(graceid)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "Successful adding of" in data["message"]
        assert graceid in data["message"]
        assert "List ID:" in data["message"]
        assert len(data["errors"]) == 0
        assert len(data["warnings"]) == 0

    def test_post_event_galaxies_with_doi(self):
        """Test posting event galaxies with DOI request."""
        graceid = self.KNOWN_GRACEIDS[0]

        # Get timestamp from a valid alert
        alert_response = requests.get(
            self.get_url("/query_alerts"),
            params={"graceid": graceid},
            headers={"api_token": self.admin_token},
        )

        if alert_response.status_code != 200 or len(alert_response.json()) == 0:
            pytest.skip(f"No alerts found for {graceid} in test data")

        alert = alert_response.json()[0]
        timesent_stamp = alert.get("timesent")

        if not timesent_stamp:
            pytest.skip(
                f"Alert for {graceid} does not have timesent field in test data"
            )

        # Create galaxy data with DOI request
        galaxy_data = {
            "graceid": graceid,
            "timesent_stamp": timesent_stamp,
            "groupname": "Test Group",
            "reference": "Test Reference",
            "request_doi": True,
            "creators": [{"name": "Test Author", "affiliation": "Test University"}],
            "galaxies": [
                {
                    "name": "NGC 123",
                    "ra": 123.456,
                    "dec": -12.345,
                    "score": 0.9,
                    "rank": 1,
                    "info": {"redshift": 0.01},
                },
                {
                    "name": "NGC 456",
                    "position": "POINT(45.678 -67.890)",
                    "score": 0.8,
                    "rank": 2,
                    "info": {"redshift": 0.02},
                },
            ],
        }

        response = requests.post(
            self.get_url("/event_galaxies"),
            json=galaxy_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "Successful adding of" in data["message"]
        # Note: DOI creation might fail in test environment

    def test_post_event_galaxies_with_invalid_data(self):
        """Test posting event galaxies with invalid data."""
        graceid = self.KNOWN_GRACEIDS[0]

        # Get timestamp from a valid alert
        alert_response = requests.get(
            self.get_url("/query_alerts"),
            params={"graceid": graceid},
            headers={"api_token": self.admin_token},
        )

        if alert_response.status_code != 200 or len(alert_response.json()) == 0:
            pytest.skip(f"No alerts found for {graceid} in test data")

        alert = alert_response.json()[0]
        timesent_stamp = alert.get("timesent")

        if not timesent_stamp:
            pytest.skip(
                f"Alert for {graceid} does not have timesent field in test data"
            )

        # Create galaxy data with invalid galaxy position
        galaxy_data = {
            "graceid": graceid,
            "timesent_stamp": timesent_stamp,
            "galaxies": [
                {
                    "name": "Invalid Galaxy",
                    # Missing both position and ra/dec
                    "score": 0.9,
                    "rank": 1,
                }
            ],
        }

        response = requests.post(
            self.get_url("/event_galaxies"),
            json=galaxy_data,
            headers={"api_token": self.admin_token},
        )

        # Should return 200 but with errors
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_remove_event_galaxies(self):
        """Test removing event galaxies."""
        # First post some galaxies to get a list ID
        graceid = self.KNOWN_GRACEIDS[0]
        post_response = self.post_test_galaxy_data(graceid)

        if post_response.status_code != 200:
            pytest.skip("Failed to post test galaxy data")

        post_data = post_response.json()
        list_id = int(post_data["message"].split("List ID: ")[1].strip())

        # Now try to delete them
        response = requests.delete(
            self.get_url("/remove_event_galaxies"),
            params={"listid": list_id},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "Successfully deleted your galaxy list" in data["message"]

        # Verify deletion by trying to get the galaxies
        get_response = requests.get(
            self.get_url("/event_galaxies"),
            params={"graceid": graceid, "listid": list_id},
            headers={"api_token": self.admin_token},
        )

        assert get_response.status_code == status.HTTP_200_OK
        data = get_response.json()
        assert len(data) == 0  # Should be empty after deletion

    def test_remove_event_galaxies_unauthorized(self):
        """Test that user can only remove their own galaxy lists."""
        # First post some galaxies with admin token
        graceid = self.KNOWN_GRACEIDS[0]
        post_response = self.post_test_galaxy_data(graceid)

        if post_response.status_code != 200:
            pytest.skip("Failed to post test galaxy data")

        post_data = post_response.json()
        list_id = int(post_data["message"].split("List ID: ")[1].strip())

        # Now try to delete them with a different user token
        response = requests.delete(
            self.get_url("/remove_event_galaxies"),
            params={"listid": list_id},
            headers={"api_token": self.user_token},  # Different user
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert (
            "You can only delete information related to your API token"
            in response.json()["message"]
        )

    def test_remove_nonexistent_event_galaxies(self):
        """Test trying to remove nonexistent event galaxies."""
        response = requests.delete(
            self.get_url("/remove_event_galaxies"),
            params={"listid": 99999},  # Nonexistent ID
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No galaxies found" in response.json()["message"]

    def test_get_glade_galaxies_no_params(self):
        """Test getting GLADE galaxies without parameters."""
        response = requests.get(
            self.get_url("/glade"), headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should return some galaxies from GLADE catalog
        assert len(data) > 0

    def test_get_glade_galaxies_by_position(self):
        """Test getting GLADE galaxies near a position."""
        response = requests.get(
            self.get_url("/glade"),
            params={"ra": 123.456, "dec": -12.345},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should return galaxies sorted by distance from the specified position

    def test_get_glade_galaxies_by_name(self):
        """Test getting GLADE galaxies by name."""
        response = requests.get(
            self.get_url("/glade"),
            params={"name": "NGC"},  # Common prefix for galaxy names
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

        # Should return galaxies with names containing "NGC"
        if len(data) > 0:
            for galaxy in data:
                # Check if any of the name fields contain "NGC"
                has_name_match = False
                for name_field in [
                    "_2mass_name",
                    "gwgc_name",
                    "hyperleda_name",
                    "sdssdr12_name",
                ]:
                    if (
                        name_field in galaxy
                        and galaxy[name_field]
                        and "NGC" in galaxy[name_field]
                    ):
                        has_name_match = True
                        break
                assert has_name_match

    def test_public_read_access(self):
        """Test authentication requirements for GW galaxy endpoints."""
        # GLADE endpoint requires authentication (returns user-specific catalog access)
        response = requests.get(self.get_url("/glade"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
            
        # Test event_galaxies endpoint - also requires authentication
        response = requests.get(self.get_url("/event_galaxies?graceid=S190425z"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def post_test_galaxy_data(self, graceid):
        """Helper method to post test galaxy data."""
        # Get timestamp from a valid alert
        alert_response = requests.get(
            self.get_url("/query_alerts"),
            params={"graceid": graceid},
            headers={"api_token": self.admin_token},
        )

        if alert_response.status_code != 200 or len(alert_response.json()) == 0:
            pytest.skip(f"No alerts found for {graceid} in test data")

        alert = alert_response.json()[0]
        timesent_stamp = alert.get("timesent")

        if not timesent_stamp:
            pytest.skip(
                f"Alert for {graceid} does not have timesent field in test data"
            )

        # Create test galaxy data
        galaxy_data = {
            "graceid": graceid,
            "timesent_stamp": timesent_stamp,
            "groupname": "Test Group",
            "reference": "Test Reference",
            "galaxies": [
                {
                    "name": "Test Galaxy 1",
                    "ra": 123.456,
                    "dec": -12.345,
                    "score": 0.9,
                    "rank": 1,
                    "info": {"redshift": 0.01},
                },
                {
                    "name": "Test Galaxy 2",
                    "position": "POINT(45.678 -67.890)",
                    "score": 0.8,
                    "rank": 2,
                    "info": {"redshift": 0.02},
                },
                {
                    "name": "Test Galaxy 3",
                    "ra": 200.123,
                    "dec": 30.456,
                    "score": 0.7,
                    "rank": 3,
                    "info": {"redshift": 0.03},
                },
            ],
        }

        print(f"Galaxy data for {graceid}: {galaxy_data} - POSTing...")
        return requests.post(
            self.get_url("/event_galaxies"),
            json=galaxy_data,
            headers={"api_token": self.admin_token},
        )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
