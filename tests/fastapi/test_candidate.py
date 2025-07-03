"""
Test candidate endpoints with real requests to the FastAPI application.
Tests use specific data from test-data.sql.
"""

import os
import requests
import json
from datetime import datetime
import pytest
from fastapi import status

# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1_PREFIX = "/api/v1"


class TestCandidateEndpoints:
    """Test class for candidate-related API endpoints."""

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

    def test_get_candidates_no_params(self):
        """Test getting candidates without any parameters."""
        response = requests.get(
            self.get_url("/candidate"), headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should return candidates that exist in test data
        for candidate in data:
            assert "id" in candidate
            assert "candidate_name" in candidate
            assert "graceid" in candidate

    def test_get_candidate_by_id(self):
        """Test getting a specific candidate by ID."""
        # First create a candidate to ensure we have one
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "Test_SN_001",
                "ra": 123.456,
                "dec": -12.345,
                "discovery_date": "2019-04-25T12:00:00.000000",
                "discovery_magnitude": 21.5,
                "magnitude_unit": "ab_mag",
                "magnitude_bandpass": "r",
            },
        }

        create_response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )
        assert create_response.status_code == status.HTTP_200_OK
        candidate_id = create_response.json()["candidate_ids"][0]

        # Now get it by ID
        response = requests.get(
            self.get_url("/candidate"),
            params={"id": candidate_id},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == candidate_id
        assert data[0]["candidate_name"] == "Test_SN_001"

    def test_get_candidates_by_graceid(self):
        """Test getting candidates filtered by graceid."""
        response = requests.get(
            self.get_url("/candidate"),
            params={"graceid": "S190425z"},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # All returned candidates should have the specified graceid
        for candidate in data:
            assert candidate["graceid"] == "S190425z"

    def test_get_candidates_by_multiple_ids(self):
        """Test getting candidates filtered by multiple IDs."""
        # First create a couple of candidates
        candidate_ids = []
        for i in range(2):
            candidate_data = {
                "graceid": "S190425z",
                "candidate": {
                    "candidate_name": f"Test_Multi_{i}",
                    "ra": 123.456 + i,
                    "dec": -12.345 + i,
                    "discovery_date": "2019-04-25T12:00:00.000000",
                    "discovery_magnitude": 21.5 + i,
                    "magnitude_unit": "ab_mag",
                    "magnitude_bandpass": "r",
                },
            }

            create_response = requests.post(
                self.get_url("/candidate"),
                json=candidate_data,
                headers={"api_token": self.admin_token},
            )
            assert create_response.status_code == status.HTTP_200_OK
            candidate_ids.extend(create_response.json()["candidate_ids"])

        # Now get them by IDs
        ids_param = json.dumps(candidate_ids)  # JSON array format
        response = requests.get(
            self.get_url("/candidate"),
            params={"ids": ids_param},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        returned_ids = [c["id"] for c in data]
        for cid in candidate_ids:
            assert cid in returned_ids

    def test_get_candidates_by_user_id(self):
        """Test getting candidates filtered by user ID."""
        response = requests.get(
            self.get_url("/candidate"),
            params={"userid": 1},  # Admin user ID
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # All returned candidates should be submitted by user 1
        for candidate in data:
            assert candidate["submitterid"] == 1

    def test_get_candidates_by_date_range(self):
        """Test getting candidates filtered by discovery date range."""
        response = requests.get(
            self.get_url("/candidate"),
            params={
                "discovery_date_after": "2019-04-01T00:00:00.000000",
                "discovery_date_before": "2019-05-01T00:00:00.000000",
            },
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Check that returned candidates are within the date range
        for candidate in data:
            if candidate.get("discovery_date"):
                discovery_date = datetime.fromisoformat(
                    candidate["discovery_date"].replace("Z", "+00:00")
                )
                assert datetime(2019, 4, 1) <= discovery_date <= datetime(2019, 5, 1)

    def test_get_candidates_by_magnitude_range(self):
        """Test getting candidates filtered by magnitude range."""
        response = requests.get(
            self.get_url("/candidate"),
            params={"discovery_magnitude_gt": 20.0, "discovery_magnitude_lt": 23.0},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Check that returned candidates are within the magnitude range
        for candidate in data:
            if candidate.get("discovery_magnitude"):
                mag = candidate["discovery_magnitude"]
                assert 20.0 < mag < 23.0

    def test_post_single_candidate(self):
        """Test posting a single candidate."""
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_2019abc",
                "ra": 150.789,
                "dec": -25.456,
                "discovery_date": "2019-04-25T14:30:00.000000",
                "discovery_magnitude": 22.1,
                "magnitude_unit": "ab_mag",
                "magnitude_bandpass": "g",
                "tns_name": "2019abc",
                "tns_url": "https://www.wis-tns.org/object/2019abc",
                "associated_galaxy": "NGC1234",
                "associated_galaxy_redshift": 0.05,
                "associated_galaxy_distance": 200.5,
            },
        }

        response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "candidate_ids" in data
        assert len(data["candidate_ids"]) == 1
        assert isinstance(data["candidate_ids"][0], int)
        assert len(data.get("ERRORS", [])) == 0

    def test_post_multiple_candidates(self):
        """Test posting multiple candidates."""
        candidate_data = {
            "graceid": "S190425z",
            "candidates": [
                {
                    "candidate_name": "SN_2019def",
                    "ra": 155.123,
                    "dec": -30.789,
                    "discovery_date": "2019-04-25T15:00:00.000000",
                    "discovery_magnitude": 21.8,
                    "magnitude_unit": "ab_mag",
                    "magnitude_bandpass": "r",
                },
                {
                    "candidate_name": "SN_2019ghi",
                    "ra": 160.456,
                    "dec": -35.123,
                    "discovery_date": "2019-04-25T16:00:00.000000",
                    "discovery_magnitude": 22.3,
                    "magnitude_unit": "ab_mag",
                    "magnitude_bandpass": "i",
                },
            ],
        }

        response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "candidate_ids" in data
        assert len(data["candidate_ids"]) == 2
        assert len(data.get("ERRORS", [])) == 0

    def test_post_candidate_with_position_string(self):
        """Test posting candidate with position as WKT string."""
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_2019jkl",
                "position": "POINT(165.789 40.123)",
                "discovery_date": "2019-04-25T17:00:00.000000",
                "discovery_magnitude": 21.5,
                "magnitude_unit": "ab_mag",
                "magnitude_bandpass": "V",
            },
        }

        response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["candidate_ids"]) == 1
        assert len(data.get("ERRORS", [])) == 0

    def test_post_candidate_with_spectral_regime(self):
        """Test posting candidate with wavelength regime."""
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_2019mno",
                "ra": 170.456,
                "dec": 45.789,
                "discovery_date": "2019-04-25T18:00:00.000000",
                "discovery_magnitude": 20.9,
                "magnitude_unit": "ab_mag",
                "wavelength_regime": [4000, 7000],
                "wavelength_unit": "angstrom",
            },
        }

        response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["candidate_ids"]) == 1
        assert len(data.get("ERRORS", [])) == 0

    def test_post_candidate_invalid_graceid(self):
        """Test posting candidate with invalid graceid."""
        candidate_data = {
            "graceid": "INVALID_GID",
            "candidate": {
                "candidate_name": "SN_Invalid",
                "ra": 123.456,
                "dec": -12.345,
                "discovery_date": "2019-04-25T12:00:00.000000",
                "discovery_magnitude": 21.5,
                "magnitude_unit": "ab_mag",
            },
        }

        response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid 'graceid'" in response.json()["message"]

    def test_post_candidate_missing_required_fields(self):
        """Test posting candidate with missing required fields."""
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_Incomplete",
                "ra": 123.456,
                "dec": -12.345,
                # Missing discovery_date and discovery_magnitude
                "magnitude_unit": "ab_mag",
            },
        }

        response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        missing_fields = [
            field["params"]["field"] for field in response.json()["errors"]
        ]
        assert "discovery_date" in str(missing_fields)
        assert "discovery_magnitude" in str(missing_fields)

    def test_post_candidate_invalid_position(self):
        """Test posting candidate with invalid position data."""
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_BadPos",
                # Missing both position and ra/dec
                "discovery_date": "2019-04-25T12:00:00.000000",
                "discovery_magnitude": 21.5,
                "magnitude_unit": "ab_mag",
            },
        }

        response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()["errors"][0]["message"]
        assert "Either position or both ra and dec must be provided" in data

    def test_put_candidate(self):
        """Test updating an existing candidate."""
        # First create a candidate
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_ToUpdate",
                "ra": 175.123,
                "dec": -50.456,
                "discovery_date": "2019-04-25T19:00:00.000000",
                "discovery_magnitude": 22.0,
                "magnitude_unit": "ab_mag",
                "magnitude_bandpass": "B",
            },
        }

        create_response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )
        assert create_response.status_code == status.HTTP_200_OK
        candidate_id = create_response.json()["candidate_ids"][0]

        # Now update it
        update_data = {
            "id": candidate_id,
            "candidate": {
                "candidate_name": "SN_Updated",
                "discovery_magnitude": 21.5,
                "tns_name": "2019updated",
                "associated_galaxy": "NGC5678",
            },
        }

        response = requests.put(
            self.get_url("/candidate"),
            json=update_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "candidate" in data
        assert data["candidate"]["candidate_name"] == "SN_Updated"
        assert data["candidate"]["discovery_magnitude"] == 21.5

    def test_put_candidate_nonexistent(self):
        """Test updating a non-existent candidate."""
        update_data = {
            "id": 99999,  # Non-existent ID
            "candidate": {"candidate_name": "SN_NotFound", "discovery_magnitude": 21.5},
        }

        response = requests.put(
            self.get_url("/candidate"),
            json=update_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No candidate found" in response.json()["message"]

    def test_put_candidate_unauthorized(self):
        """Test updating another user's candidate."""
        # Create candidate as admin
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_AdminOwned",
                "ra": 180.789,
                "dec": -55.123,
                "discovery_date": "2019-04-25T20:00:00.000000",
                "discovery_magnitude": 21.7,
                "magnitude_unit": "ab_mag",
            },
        }

        create_response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )
        assert create_response.status_code == status.HTTP_200_OK
        candidate_id = create_response.json()["candidate_ids"][0]

        # Try to update as different user
        update_data = {
            "id": candidate_id,
            "candidate": {"candidate_name": "SN_Hijacked"},
        }

        response = requests.put(
            self.get_url("/candidate"),
            json=update_data,
            headers={"api_token": self.user_token},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Unable to alter" in response.json()["message"]

    def test_delete_candidate_single(self):
        """Test deleting a single candidate."""
        # First create a candidate
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_ToDelete",
                "ra": 185.456,
                "dec": -60.789,
                "discovery_date": "2019-04-25T21:00:00.000000",
                "discovery_magnitude": 23.1,
                "magnitude_unit": "ab_mag",
            },
        }

        create_response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )
        assert create_response.status_code == status.HTTP_200_OK
        candidate_id = create_response.json()["candidate_ids"][0]

        # Now delete it
        response = requests.delete(
            self.get_url("/candidate"),
            json={"id": candidate_id},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Successfully deleted" in data["message"]
        assert candidate_id in data["deleted_ids"]

    def test_delete_candidate_multiple(self):
        """Test deleting multiple candidates."""
        # First create multiple candidates
        candidate_ids = []
        for i in range(3):
            candidate_data = {
                "graceid": "S190425z",
                "candidate": {
                    "candidate_name": f"SN_MultiDelete_{i}",
                    "ra": 190.0 + i,
                    "dec": -65.0 - i,
                    "discovery_date": "2019-04-25T22:00:00.000000",
                    "discovery_magnitude": 22.5 + i * 0.1,
                    "magnitude_unit": "ab_mag",
                },
            }

            create_response = requests.post(
                self.get_url("/candidate"),
                json=candidate_data,
                headers={"api_token": self.admin_token},
            )
            assert create_response.status_code == status.HTTP_200_OK
            candidate_ids.extend(create_response.json()["candidate_ids"])

        # Now delete them
        ids_param = json.dumps(candidate_ids)
        response = requests.delete(
            self.get_url("/candidate"),
            json={"ids": candidate_ids},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Successfully deleted" in data["message"]
        assert len(data["deleted_ids"]) == 3
        for cid in candidate_ids:
            assert cid in data["deleted_ids"]

    def test_delete_candidate_nonexistent(self):
        """Test deleting a non-existent candidate."""
        response = requests.delete(
            self.get_url("/candidate"),
            json={"id": 99999},
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No candidate found" in response.json()["message"]

    def test_delete_candidate_unauthorized(self):
        """Test deleting another user's candidate."""
        # Create candidate as admin
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_AdminProtected",
                "ra": 195.123,
                "dec": -70.456,
                "discovery_date": "2019-04-25T23:00:00.000000",
                "discovery_magnitude": 21.2,
                "magnitude_unit": "ab_mag",
            },
        }

        create_response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )
        assert create_response.status_code == status.HTTP_200_OK
        candidate_id = create_response.json()["candidate_ids"][0]

        # Try to delete as different user
        response = requests.delete(
            self.get_url("/candidate"),
            json={"id": candidate_id},
            headers={"api_token": self.user_token},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Unauthorized" in response.json()["message"]

    def test_candidate_unauthorized_access(self):
        """Test that unauthorized requests are rejected."""
        # Request without API token
        response = requests.get(self.get_url("/candidate"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Request with invalid API token
        response = requests.get(
            self.get_url("/candidate"), headers={"api_token": self.invalid_token}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_candidates_with_different_tokens(self):
        """Test access with different valid API tokens."""
        # All authenticated users should be able to read candidates
        for token in [self.admin_token, self.user_token, self.scientist_token]:
            response = requests.get(
                self.get_url("/candidate"), headers={"api_token": token}
            )
            assert response.status_code == status.HTTP_200_OK

    def test_post_candidate_with_different_users(self):
        """Test creating candidates as different users."""
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_UserSubmitted",
                "ra": 200.456,
                "dec": -75.789,
                "discovery_date": "2019-04-26T00:00:00.000000",
                "discovery_magnitude": 22.8,
                "magnitude_unit": "ab_mag",
            },
        }

        # Submit as regular user
        response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.user_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["candidate_ids"]) == 1

        # Verify the submitter ID by getting the candidate back
        candidate_id = data["candidate_ids"][0]
        get_response = requests.get(
            self.get_url("/candidate"),
            params={"id": candidate_id},
            headers={"api_token": self.user_token},
        )
        assert get_response.status_code == status.HTTP_200_OK
        candidate = get_response.json()[0]
        assert candidate["submitterid"] == 2  # User token corresponds to user ID 2


class TestCandidateAPIValidation:
    """Test validation of candidate API endpoints."""

    admin_token = "test_token_admin_001"

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    def test_invalid_magnitude_unit(self):
        """Test creating candidate with invalid magnitude unit."""
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_InvalidUnit",
                "ra": 123.456,
                "dec": -12.345,
                "discovery_date": "2019-04-25T12:00:00.000000",
                "discovery_magnitude": 21.5,
                "magnitude_unit": "invalid_unit",
            },
        }

        response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Invalid magnitude unit" in response.json()["errors"][0]["message"]

    def test_invalid_date_format(self):
        """Test creating candidate with invalid date format."""
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_BadDate",
                "ra": 123.456,
                "dec": -12.345,
                "discovery_date": "invalid-date-format",
                "discovery_magnitude": 21.5,
                "magnitude_unit": "ab_mag",
            },
        }

        response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert (
            "Invalid discovery_date format" in response.json()["errors"][0]["message"]
        )

    def test_missing_position_data(self):
        """Test creating candidate without position or coordinates."""
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_NoPos",
                # No position, ra, or dec
                "discovery_date": "2019-04-25T12:00:00.000000",
                "discovery_magnitude": 21.5,
                "magnitude_unit": "ab_mag",
            },
        }

        response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "Either position or both ra and dec must be provided"
            in response.json()["errors"][0]["message"]
        )


class TestCandidateAPIIntegration:
    """Integration tests for candidate API workflows."""

    admin_token = "test_token_admin_001"

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    def test_complete_candidate_workflow(self):
        """Test complete workflow: create, read, update, delete candidate."""
        # Step 1: Create candidate
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_WorkflowTest",
                "ra": 205.789,
                "dec": -80.123,
                "discovery_date": "2019-04-26T01:00:00.000000",
                "discovery_magnitude": 21.9,
                "magnitude_unit": "ab_mag",
                "magnitude_bandpass": "r",
            },
        }

        create_response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )
        assert create_response.status_code == status.HTTP_200_OK
        candidate_id = create_response.json()["candidate_ids"][0]

        # Step 2: Read candidate
        get_response = requests.get(
            self.get_url("/candidate"),
            params={"id": candidate_id},
            headers={"api_token": self.admin_token},
        )
        assert get_response.status_code == status.HTTP_200_OK
        candidate = get_response.json()[0]
        assert candidate["candidate_name"] == "SN_WorkflowTest"

        # Step 3: Update candidate
        update_data = {
            "id": candidate_id,
            "candidate": {
                "discovery_magnitude": 21.5,
                "tns_name": "2019workflow",
                "associated_galaxy": "NGC_Workflow",
            },
        }
        update_response = requests.put(
            self.get_url("/candidate"),
            json=update_data,
            headers={"api_token": self.admin_token},
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["candidate"]["discovery_magnitude"] == 21.5

        # Step 4: Delete candidate
        delete_response = requests.delete(
            self.get_url("/candidate"),
            json={"id": candidate_id},
            headers={"api_token": self.admin_token},
        )
        assert delete_response.status_code == status.HTTP_200_OK
        assert candidate_id in delete_response.json()["deleted_ids"]

        # Step 5: Verify deletion
        verify_response = requests.get(
            self.get_url("/candidate"),
            params={"id": candidate_id},
            headers={"api_token": self.admin_token},
        )
        assert verify_response.status_code == status.HTTP_200_OK
        assert len(verify_response.json()) == 0  # Should be empty

    def test_bulk_operations(self):
        """Test bulk creation and deletion of candidates."""
        # Bulk create
        candidates_data = {
            "graceid": "S190425z",
            "candidates": [
                {
                    "candidate_name": f"SN_Bulk_{i}",
                    "ra": 210.0 + i,
                    "dec": -85.0 - i,
                    "discovery_date": "2019-04-26T02:00:00.000000",
                    "discovery_magnitude": 22.0 + i * 0.1,
                    "magnitude_unit": "ab_mag",
                }
                for i in range(5)
            ],
        }

        create_response = requests.post(
            self.get_url("/candidate"),
            json=candidates_data,
            headers={"api_token": self.admin_token},
        )
        assert create_response.status_code == status.HTTP_200_OK
        candidate_ids = create_response.json()["candidate_ids"]
        assert len(candidate_ids) == 5

        # Bulk delete
        delete_response = requests.delete(
            self.get_url("/candidate"),
            json={"ids": candidate_ids},
            headers={"api_token": self.admin_token},
        )
        assert delete_response.status_code == status.HTTP_200_OK
        assert len(delete_response.json()["deleted_ids"]) == 5

    def test_candidate_with_all_optional_fields(self):
        """Test creating candidate with all optional fields."""
        candidate_data = {
            "graceid": "S190425z",
            "candidate": {
                "candidate_name": "SN_Complete",
                "ra": 215.456,
                "dec": 85.789,
                "discovery_date": "2019-04-26T03:00:00.000000",
                "discovery_magnitude": 20.5,
                "magnitude_unit": "ab_mag",
                "magnitude_bandpass": "V",
                "magnitude_central_wave": 5500.0,
                "magnitude_bandwidth": 1000.0,
                "tns_name": "2019complete",
                "tns_url": "https://www.wis-tns.org/object/2019complete",
                "associated_galaxy": "NGC_Complete",
                "associated_galaxy_redshift": 0.1,
                "associated_galaxy_distance": 450.5,
            },
        }

        response = requests.post(
            self.get_url("/candidate"),
            json=candidate_data,
            headers={"api_token": self.admin_token},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["candidate_ids"]) == 1
        assert len(response.json().get("ERRORS", [])) == 0

        # Verify all fields were set correctly
        candidate_id = response.json()["candidate_ids"][0]
        get_response = requests.get(
            self.get_url("/candidate"),
            params={"id": candidate_id},
            headers={"api_token": self.admin_token},
        )
        candidate = get_response.json()[0]
        assert candidate["tns_name"] == "2019complete"
        assert candidate["associated_galaxy"] == "NGC_Complete"
        assert candidate["associated_galaxy_redshift"] == 0.1


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
