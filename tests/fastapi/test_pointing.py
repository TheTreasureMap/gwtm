"""
Test pointing endpoints with real requests to the FastAPI application.
Tests use specific data from test-data.sql.
"""
import os
import pytest
import requests

from fastapi import status

# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1_PREFIX = "/api/v1"


class TestPointingEndpoints:
    """Test class for pointing-related API endpoints."""

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

    # Known instrument IDs from test data
    TEST_INSTRUMENTS = {
        1: {"name": "Test Optical Telescope", "nickname": "TOT", "type": "photometric"},
        2: {
            "name": "Test X-ray Observatory",
            "nickname": "TXO",
            "type": "spectroscopic",
        },
        3: {"name": "Mock Radio Dish", "nickname": "MRD", "type": "photometric"},
    }

    def test_get_pointings_no_params(self):
        """Test getting pointings without any parameters."""
        response = requests.get(self.get_url("/pointings"))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should return all pointings
        assert len(data) >= 5  # We have at least 5 pointings from user 1

    def test_get_pointings_by_graceid_s190425z(self):
        """Test getting pointings filtered by graceid S190425z."""
        response = requests.get(
            self.get_url("/pointings"),
            params={"graceid": "S190425z"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # Should find pointings 1 and 2 linked to S190425z

    def test_get_pointings_by_multiple_graceids(self):
        """Test getting pointings filtered by multiple graceids."""
        response = requests.get(
            self.get_url("/pointings"),
            params={"graceids": "S190425z,S190426c"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 4  # Should find pointings from both events

    def test_get_pointing_by_id(self):
        """Test getting a specific pointing by ID."""
        response = requests.get(
            self.get_url("/pointings"),
            params={"id": 1},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["status"] == "completed"
        assert data[0]["band"] == "r"  # band enum value 11 = r

    def test_get_pointings_by_multiple_ids(self):
        """Test getting pointings filtered by multiple IDs."""
        response = requests.get(
            self.get_url("/pointings"),
            params={"ids": "1,2,3"},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # Should find pointings 1, 2, and 3
        pointing_ids = [p["id"] for p in data]
        assert 1 in pointing_ids
        assert 2 in pointing_ids

    def test_get_pointings_by_status_completed(self):
        """Test getting pointings with completed status."""
        """Test getting pointings filtered by multiple IDs."""
        response = requests.get(
            self.get_url("/pointings"),
            params={"status": "completed"},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # All returned pointings should have completed status
        for pointing in data:
            assert pointing.get("status") == "completed"
        assert len(data) >= 2  # Should find pointings 1 and 3

    def test_get_pointings_by_status_planned(self):
        """Test getting pointings with planned status."""
        response = requests.get(
            self.get_url("/pointings"),
            params={"status": "planned"},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # All returned pointings should have planned status
        for pointing in data:
            assert pointing.get("status") == "planned"
        # Should find pointing 2 and others

    def test_get_pointings_by_status_cancelled(self):
        """Test getting pointings with cancelled status."""
        response = requests.get(
            self.get_url("/pointings"),
            params={"status": "cancelled"},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # All returned pointings should have cancelled status
        for pointing in data:
            assert pointing.get("status") == "cancelled"
        # Should find pointing 4

    def test_get_pointings_by_multiple_statuses(self):
        """Test getting pointings filtered by multiple statuses."""
        response = requests.get(
            self.get_url("/pointings"),
            params={"statuses": "completed, planned"},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should include both completed and planned pointings
        statuses = [p.get("status") for p in data]
        assert "completed" in statuses
        assert "planned" in statuses

    def test_get_pointings_by_band_r(self):
        """Test getting pointings filtered by r band."""
        response = requests.get(
            self.get_url("/pointings"),
            params={"band": "r"},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should find pointings with r band (enum 11)
        for pointing in data:
            assert pointing.get("band") == "r"

    def test_get_pointings_by_band_g(self):
        """Test getting pointings filtered by g band."""
        response = requests.get(
            self.get_url("/pointings"),
            params={"band": "g"},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should find pointings with g band (enum 10)
        for pointing in data:
            assert pointing.get("band") == "g"

    def test_get_pointings_by_instrument_id(self):
        """Test getting pointings filtered by instrument ID."""
        response = requests.get(
            self.get_url("/pointings"),
            params={"instrument": 1},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should find pointings using instrument 1 (Test Optical Telescope)
        for pointing in data:
            assert pointing.get("instrumentid") == 1

    def test_get_pointings_by_instrument_name(self):
        """Test getting pointings filtered by instrument name."""
        response = requests.get(
            self.get_url("/pointings"),
            params={"instrument": "Test Optical Telescope"},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should find pointings using the named instrument

    def test_get_pointings_by_user_id(self):
        """Test getting pointings filtered by user ID."""
        response = requests.get(
            self.get_url("/pointings"),
            params={"user": 1},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should find pointings submitted by user 1 (admin)
        for pointing in data:
            assert pointing.get("submitterid") == 1

    def test_get_pointings_by_username(self):
        """Test getting pointings filtered by username."""
        response = requests.get(
            self.get_url("/pointings"),
            params={"user": "admin"},
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should find pointings submitted by admin user

    def test_get_pointings_by_time_range(self):
        """Test getting pointings filtered by time range."""
        response = requests.get(
            self.get_url("/pointings"),
            params={
                "completed_after": "2019-04-25T08:00:00.000000",
                "completed_before": "2019-04-25T15:00:00.000000"
            },
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should find pointings completed within this time range

    def test_get_pointings_by_depth_range(self):
        """Test getting pointings filtered by depth range."""
        response = requests.get(
            self.get_url("/pointings"),
            params={
                "depth_gt": 19.0,  # Greater than 19 mag
                "depth_lt": 22.0,  # Less than 22 mag
                "depth_unit": "ab_mag"
            },
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should find pointings within this depth range
        for pointing in data:
            depth = pointing.get("depth")
            if depth is not None:
                assert 19.0 < depth < 22.0

    def test_post_single_pointing(self):
        """Test posting a single pointing."""

        pointing_data = {
            "graceid": "S190425z",
            "pointing": {
                "ra": 130.456,
                "dec": -15.678,
                "instrumentid": 1,
                "depth": 22.5,
                "depth_unit": "ab_mag",
                "time": "2019-04-25T12:00:00.000000",
                "status": "completed",
                "pos_angle": 0.0,
                "band": "V"
            }
        }

        response = requests.post(
            self.get_url("/pointings"),
            json=pointing_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "pointing_ids" in data
        assert len(data["pointing_ids"]) == 1
        assert isinstance(data["pointing_ids"][0], int)
        # Should have no errors
        assert len(data.get("ERRORS", [])) == 0

    def test_post_multiple_pointings(self):
        """Test posting multiple pointings."""

        pointing_data = {
            "graceid": "S190425z",
            "pointings": [
                {
                    "ra": 135.123,
                    "dec": -20.456,
                    "instrumentid": 1,
                    "depth": 22.5,
                    "depth_unit": "ab_mag",
                    "time": "2019-04-25T12:30:00.000000",
                    "status": "completed",
                    "pos_angle": 0.0,
                    "band": "V"
                },
                {
                    "ra": 140.789,
                    "dec": -25.123,
                    "instrumentid": 2,
                    "depth": 21.0,
                    "depth_unit": "ab_mag",
                    "time": "2019-04-25T13:00:00.000000",
                    "status": "completed",
                    "pos_angle": 45.0,
                    "band": "R"
                }
            ]
        }

        response = requests.post(
            self.get_url("/pointings"),
            json=pointing_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "pointing_ids" in data
        assert len(data["pointing_ids"]) == 2
        # Should have no errors
        assert len(data.get("ERRORS", [])) == 0

    def test_post_planned_pointing(self):
        """Test posting a planned pointing."""

        pointing_data = {
            "graceid": "GW190521",  # Known test graceid
            "pointing": {
                "ra": 145.123,
                "dec": -30.456,
                "instrumentid": 1,
                "depth": 23.5,
                "depth_unit": "ab_mag",
                "time": "2020-05-21T18:00:00.000000",
                "status": "planned",
                "band": "I"
            }
        }

        response = requests.post(
            self.get_url("/pointings"),
            json=pointing_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "pointing_ids" in data
        assert len(data["pointing_ids"]) == 1

        # Store the planned pointing ID for later tests
        self.planned_pointing_id = data["pointing_ids"][0]

    @pytest.mark.skip(reason="Skipping test that requires external Zenodo API calls")
    def test_post_pointing_with_doi_request(self):
        """Test posting a pointing with DOI request."""

        pointing_data = {
            "graceid": "S190425z",
            "pointing": {
                "ra": 160.789,
                "dec": 30.123,
                "instrumentid": 1,
                "depth": 21.5,
                "depth_unit": "ab_mag",
                "time": "2019-04-25T14:00:00.000000",
                "status": "completed",
                "pos_angle": 90.0,
                "band": "g"
            },
            "request_doi": True,
            "creators": [
                {
                    "name": "Test Author",
                    "affiliation": "Test Institution"
                }
            ]
        }

        response = requests.post(
            self.get_url("/pointings"),
            json=pointing_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "pointing_ids" in data
        # Note: DOI creation might not be configured in test environment
        # assert "DOI" in data

    def test_post_pointing_update_planned(self):
        """Test updating a planned pointing to completed."""
        # First, make sure we have a planned pointing
        params = {"id": 8, "status": "planned"}  # Known planned pointing from test data
        response = requests.get(
            self.get_url("/pointings"),
            json=params,
            headers={"api_token": self.admin_token}
        )

        if response.status_code == status.HTTP_200_OK and len(response.json()) > 0:
            # Now update it to completed
            update_data = {
                "graceid": "GW190521",
                "pointing": {
                    "id": 8,
                    "time": "2020-05-22T08:30:00.000000",
                    "pos_angle": 45.0
                }
            }

            response = requests.post(
                self.get_url("/pointings"),
                json=update_data,
                headers={"api_token": self.admin_token}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "pointing_ids" in data
            assert len(data["pointing_ids"]) == 1

    def test_post_pointing_invalid_graceid(self):
        """Test posting pointing with invalid graceid."""

        pointing_data = {
            "graceid": "INVALID123",
            "pointing": {
                "ra": 123.456,
                "dec": -45.678,
                "instrumentid": 1,
                "depth": 22.5,
                "depth_unit": "ab_mag",
                "time": "2019-04-25T12:00:00.000000",
                "status": "completed",
                "pos_angle": 0.0,
                "band": "V"
            }
        }

        response = requests.post(
            self.get_url("/pointings"),
            json=pointing_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid graceid" in response.json().get("message")

    def test_post_pointing_missing_required_fields(self):
        """Test posting pointing with missing required fields."""

        pointing_data = {
            "graceid": "S190425z",
            "pointing": {
                "ra": 123.456,
                "dec": -45.678,
                # Missing instrumentid and band (required for completed observations)
                "depth": 22.5,
                "depth_unit": "ab_mag",
                "time": "2019-04-25T12:00:00.000000",
                "status": "completed"
            }
        }

        response = requests.post(
            self.get_url("/pointings"),
            json=pointing_data,
            headers={"api_token": self.admin_token}
        )

        # With improved Pydantic validation, we now get proper HTTP 400 status codes
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "validation error" in data.get("message", "").lower()
        # Should indicate missing required field (band is caught first by Pydantic)
        assert "band is required" in str(data)

    def test_update_pointing_cancel(self):
        """Test updating pointing status to cancelled."""
        # First create a planned pointing

        pointing_data = {
            "graceid": "S190425z",
            "pointing": {
                "ra": 165.000,
                "dec": 35.000,
                "instrumentid": 1,
                "depth": 24.5,
                "depth_unit": "ab_mag",
                "time": "2019-04-25T17:00:00.000000",
                "status": "planned",
                "band": "u"
            }
        }

        response = requests.post(
            self.get_url("/pointings"),
            json=pointing_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        pointing_id = response.json()["pointing_ids"][0]

        # Now cancel it
        update_data = {"status": "cancelled", "ids": [pointing_id]}

        response = requests.post(
            self.get_url("/update_pointings"),
            json=update_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Updated" in data["message"]
        assert "1" in data["message"]  # Should update 1 pointing

    def test_cancel_all_pointings(self):
        """Test cancelling all pointings for a graceid and instrument."""
        # First create some planned pointings

        for i in range(3):
            pointing_data = {
                "graceid": "S190425z",  # Known test graceid
                "pointing": {
                    "ra": 10.0 + i,
                    "dec": 5.0 + i,
                    "instrumentid": 3,  # Use Mock Radio Dish
                    "depth": 24.0,
                    "depth_unit": "ab_mag",
                    "time": f"2019-04-25T18:{i:02d}:00.000000",
                    "status": "planned",
                    "band": "V"
                }
            }

            response = requests.post(
                self.get_url("/pointings"),
                json=pointing_data,
                headers={"api_token": self.admin_token}
            )

            assert response.status_code == status.HTTP_200_OK

        # Now cancel all for this graceid and instrument
        cancel_data = {
            "graceid": "S190425z",
            "instrumentid": 3
        }

        response = requests.post(
            self.get_url("/cancel_all"),
            json=cancel_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Updated" in data["message"]
        assert "3" in data["message"]  # Should cancel 3 pointings

    @pytest.mark.skip(reason="Skipping test that requires external Zenodo API calls")
    def test_request_doi_for_pointings(self):
        """Test requesting DOI for existing pointings."""
        # First create some completed pointings

        pointing_ids = []

        for i in range(2):
            pointing_data = {
                "graceid": "S190425z",
                "pointing": {
                    "ra": 170.0 + i,
                    "dec": 40.0 + i,
                    "instrumentid": 1,
                    "depth": 23.0,
                    "depth_unit": "ab_mag",
                    "time": f"2019-04-25T19:{i:02d}:00.000000",
                    "status": "completed",
                    "pos_angle": 0.0,
                    "band": "V"
                }
            }

            response = requests.post(
                self.get_url("/pointings"),
                json=pointing_data,
                headers={"api_token": self.admin_token},
            )

            assert response.status_code == status.HTTP_200_OK
            pointing_ids.extend(response.json()["pointing_ids"])

        # Now create new pointing with DOI request for all created pointings
        doi_data = {
            "graceid": "S190425z",
            # Need a pointing or pointings parameter
            "pointing": {
                "ra": 175.0,
                "dec": 45.0,
                "instrumentid": 1,
                "depth": 23.0,
                "depth_unit": "ab_mag",
                "time": "2019-04-25T20:00:00.000000",
                "status": "completed",
                "pos_angle": 0.0,
                "band": "V"
            },
            # DOI-related parameters
            "request_doi": True,
            "creators": [
                {
                    "name": "Test Researcher",
                    "affiliation": "Test University"
                }
            ],
        }

        response = requests.post(
            self.get_url("/pointings"),
            json=doi_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "DOI" in data

    def test_pointing_public_access(self):
        """Test that GET pointings endpoint is publicly accessible."""
        url = self.get_url("/pointings")

        # Request without API token should work
        response = requests.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_pointings_no_auth_required(self):
        """Test that GET pointings works without authentication."""
        url = self.get_url("/pointings")

        # All these should work without authentication
        response = requests.get(url)
        assert response.status_code == status.HTTP_200_OK

        # Test with graceid filter
        response = requests.get(url, params={"graceid": "S190425z"})
        assert response.status_code == status.HTTP_200_OK

        # Test with status filter
        response = requests.get(url, params={"status": "completed"})
        assert response.status_code == status.HTTP_200_OK

    def test_get_pointings_by_specific_coordinates(self):
        """Test getting pointings near specific coordinates from test data."""
        url = self.get_url("/pointings")

        # Test data has pointings around these coordinates
        params = {"ids": "[1]"}  # pointing 1 is at (123.456, -12.345)
        response = requests.get(url, params=params)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0
        # Check that we get back the expected position
        assert "123.456" in data[0]["position"]
        assert "-12.345" in data[0]["position"]


# Additional test class for testing with specific test data values
class TestPointingWithSpecificData:
    """Test pointing functionality using specific values from test data."""

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    TEST_USER_API_TOKEN = "test_token_user_002"

    @classmethod
    def setup_class(cls):
        cls.session = requests.Session()
        cls.headers = {
            "Content-Type": "application/json",
            "api_token": cls.TEST_USER_API_TOKEN
        }

    def test_get_specific_pointing_by_id(self):
        """Test getting pointing 1 specifically."""
        url = self.get_url("/pointings")
        params = {"id": 1}
        response = self.session.get(url, params=params, headers=self.headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        pointing = data[0]

        # Verify specific values from test data
        assert pointing["id"] == 1
        assert pointing["status"] == "completed"
        assert pointing["instrumentid"] == 1
        assert pointing["depth"] == 20.5
        assert pointing["depth_err"] == 0.1
        assert pointing["depth_unit"] == "ab_mag"
        assert pointing["band"] == "r"  # band enum 11 = r
        assert "123.456" in pointing["position"]
        assert "-12.345" in pointing["position"]

    def test_get_specific_pointing_by_graceid_and_instrument(self):
        """Test getting pointings for S190425z with instrument 1."""
        url = self.get_url("/pointings")
        params = {
            "graceid": "S190425z",
            "instrument": "1"
        }
        response = self.session.get(url, params=params, headers=self.headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should find pointings 1 and 2 which are linked to S190425z
        assert len(data) >= 1

    def test_create_pointing_for_existing_graceid(self):
        """Test creating a pointing for an existing graceid."""
        url = self.get_url("/pointings")

        pointing_data = {
            "graceid": "MS230101a",  # Test graceid from test data
            "pointing": {
                "ra": 180.0,
                "dec": 0.0,
                "instrumentid": 1,  # Test Optical Telescope
                "depth": 24.0,
                "depth_unit": "ab_mag",
                "time": "2023-01-01T12:00:00.000000",
                "status": "completed",
                "pos_angle": 0.0,
                "band": "V"
            }
        }

        response = self.session.post(url, json=pointing_data, headers=self.headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "pointing_ids" in data
        assert len(data["pointing_ids"]) == 1
        assert len(data.get("ERRORS", [])) == 0

    @classmethod
    def teardown_class(cls):
        cls.session.close()


class TestPointingDeleteAndPut:
    """Tests for the RESTful DELETE and PUT pointing endpoints."""

    admin_token = "test_token_admin_001"
    user_token = "test_token_user_002"

    def get_url(self, endpoint):
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    def _create_pointing(self, token, graceid="S190425z", ra=50.0, dec=-5.0):
        """Helper to create a pointing and return its ID."""
        data = {
            "graceid": graceid,
            "pointing": {
                "ra": ra,
                "dec": dec,
                "instrumentid": 1,
                "depth": 21.0,
                "depth_unit": "ab_mag",
                "time": "2019-04-25T10:00:00.000000",
                "status": "planned",
                "band": "r",
            },
        }
        response = requests.post(
            self.get_url("/pointings"),
            json=data,
            headers={"api_token": token},
        )
        assert response.status_code == status.HTTP_200_OK
        return response.json()["pointing_ids"][0]

    def test_delete_own_pointing(self):
        """User can delete their own pointing."""
        pid = self._create_pointing(self.admin_token, ra=51.0, dec=-6.0)

        response = requests.delete(
            self.get_url("/pointings"),
            json={"ids": [pid]},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Deleted 1" in response.json()["message"]

        # Verify it's gone
        get_resp = requests.get(self.get_url("/pointings"), params={"id": pid})
        assert get_resp.status_code == status.HTTP_200_OK
        assert get_resp.json() == []

    def test_delete_other_users_pointing_denied(self):
        """Non-admin cannot delete another user's pointing."""
        pid = self._create_pointing(self.admin_token, ra=52.0, dec=-7.0)

        response = requests.delete(
            self.get_url("/pointings"),
            json={"ids": [pid]},
            headers={"api_token": self.user_token},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_pointing(self):
        """Deleting a non-existent ID returns 404."""
        response = requests.delete(
            self.get_url("/pointings"),
            json={"ids": [999999]},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_multiple_pointings(self):
        """User can delete multiple of their own pointings in one call."""
        pid1 = self._create_pointing(self.admin_token, ra=53.0, dec=-8.0)
        pid2 = self._create_pointing(self.admin_token, ra=54.0, dec=-9.0)

        response = requests.delete(
            self.get_url("/pointings"),
            json={"ids": [pid1, pid2]},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Deleted 2" in response.json()["message"]

    def test_put_pointing_update_status(self):
        """User can update their own pointing's status."""
        pid = self._create_pointing(self.admin_token, ra=55.0, dec=-10.0)

        response = requests.put(
            self.get_url(f"/pointings/{pid}"),
            json={"status": "cancelled"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify the status changed
        get_resp = requests.get(self.get_url("/pointings"), params={"id": pid})
        assert get_resp.json()[0]["status"] == "cancelled"

    def test_put_pointing_update_depth_and_band(self):
        """User can update depth and band on their pointing."""
        pid = self._create_pointing(self.admin_token, ra=56.0, dec=-11.0)

        response = requests.put(
            self.get_url(f"/pointings/{pid}"),
            json={"depth": 23.5, "band": "g", "depth_unit": "ab_mag"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK

        get_resp = requests.get(self.get_url("/pointings"), params={"id": pid})
        p = get_resp.json()[0]
        assert p["depth"] == 23.5
        assert p["band"] == "g"

    def test_put_pointing_other_users_denied(self):
        """Non-admin cannot update another user's pointing."""
        pid = self._create_pointing(self.admin_token, ra=57.0, dec=-12.0)

        response = requests.put(
            self.get_url(f"/pointings/{pid}"),
            json={"status": "cancelled"},
            headers={"api_token": self.user_token},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_pointing_nonexistent(self):
        """PUT on a non-existent pointing ID returns 404."""
        response = requests.put(
            self.get_url("/pointings/999999"),
            json={"status": "cancelled"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_pointing_invalid_status(self):
        """PUT with an invalid status value returns 422."""
        pid = self._create_pointing(self.admin_token, ra=58.0, dec=-13.0)

        response = requests.put(
            self.get_url(f"/pointings/{pid}"),
            json={"status": "invalid_status"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_put_pointing_integer_status(self):
        """PUT accepts a numeric status value and converts it to the enum."""
        pid = self._create_pointing(self.admin_token, ra=59.0, dec=-14.0)

        response = requests.put(
            self.get_url(f"/pointings/{pid}"),
            json={"status": 3},  # cancelled
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        get_resp = requests.get(self.get_url("/pointings"), params={"id": pid})
        assert get_resp.json()[0]["status"] == "cancelled"

    def test_put_pointing_empty_body_rejected(self):
        """PUT with no updatable fields returns 400."""
        pid = self._create_pointing(self.admin_token, ra=60.0, dec=-15.0)

        response = requests.put(
            self.get_url(f"/pointings/{pid}"),
            json={},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No updatable fields" in str(response.json())

    def test_put_pointing_position_string(self):
        """PUT accepts a WKT POINT(...) string for position."""
        pid = self._create_pointing(self.admin_token, ra=61.0, dec=-16.0)

        response = requests.put(
            self.get_url(f"/pointings/{pid}"),
            json={"position": "POINT(70.5 -25.5)"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        get_resp = requests.get(self.get_url("/pointings"), params={"id": pid})
        assert "70.5" in get_resp.json()[0]["position"]
        assert "-25.5" in get_resp.json()[0]["position"]

    def test_put_pointing_invalid_position_string(self):
        """PUT with a malformed position string is rejected."""
        pid = self._create_pointing(self.admin_token, ra=62.0, dec=-17.0)

        response = requests.put(
            self.get_url(f"/pointings/{pid}"),
            json={"position": "garbage"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_put_pointing_partial_ra_dec_rejected(self):
        """PUT with only ra (or only dec) is rejected."""
        pid = self._create_pointing(self.admin_token, ra=63.0, dec=-18.0)

        response = requests.put(
            self.get_url(f"/pointings/{pid}"),
            json={"ra": 75.0},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "ra and dec" in str(response.json())

    def test_delete_partial_success_returns_failed_ids(self):
        """Mixed valid/invalid IDs return 200 with deleted_ids and failed_ids."""
        pid = self._create_pointing(self.admin_token, ra=64.0, dec=-19.0)

        response = requests.delete(
            self.get_url("/pointings"),
            json={"ids": [pid, 999999]},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["deleted_ids"] == [pid]
        assert body["failed_ids"] == [999999]
        assert "Deleted 1 of 2" in body["message"]
