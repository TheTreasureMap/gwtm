"""
Test event endpoints with real requests to the FastAPI application.
Tests use specific data from test-data.sql.
"""
import os
import requests
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
    KNOWN_GRACEIDS = ['S190425z', 'S190426c', 'MS230101a', 'GW190521', 'MS190425a']

    def test_get_candidate_events_no_params(self):
        """Test getting candidate events without any parameters."""
        response = requests.get(
            self.get_url("/candidate/event"),
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should return candidates that exist in test data
        for candidate in data:
            assert "id" in candidate
            assert "candidate_name" in candidate

    def test_get_candidate_events_by_user_id(self):
        """Test getting candidate events filtered by user ID."""
        response = requests.get(
            self.get_url("/candidate/event"),
            params={"user_id": 1},  # Admin user ID
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # All returned candidates should be submitted by user 1
        for candidate in data:
            assert candidate["submitterid"] == 1

    def test_post_candidate_event(self):
        """Test creating a new candidate event."""
        candidate_data = {
            "graceid": "S190425z",  # Using a known GraceID
            "candidate_name": "Test Candidate Event",
            "ra": 123.456,
            "dec": -12.345
        }

        response = requests.post(
            self.get_url("/candidate/event"),
            json=candidate_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "id" in data
        assert "Candidate created successfully" in data["message"]
        assert isinstance(data["id"], int)

        # Store the candidate ID for later tests
        self.candidate_id = data["id"]

    def test_update_candidate_event(self):
        """Test updating an existing candidate event."""
        # First create a candidate to update
        if not hasattr(self, 'candidate_id'):
            self.test_post_candidate_event()

        update_data = {
            "graceid": "S190425z",
            "candidate_name": "Updated Candidate Event",
            "ra": 124.567,
            "dec": -13.456
        }

        response = requests.put(
            self.get_url(f"/candidate/event/{self.candidate_id}"),
            json=update_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "Candidate updated successfully" in data["message"]

        # Verify the update worked
        response = requests.get(
            self.get_url("/candidate/event"),
            params={"id": self.candidate_id},
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["candidate_name"] == "Updated Candidate Event"
        # ra and dec may be in position property, we validate them separately if available
        if "ra" in data[0]:
            assert abs(data[0]["ra"] - 124.567) < 0.001
        if "dec" in data[0]:
            assert abs(data[0]["dec"] - (-13.456)) < 0.001

    def test_delete_candidate_event(self):
        """Test deleting a candidate event."""
        # First create a candidate to delete
        if not hasattr(self, 'candidate_id'):
            self.test_post_candidate_event()

        response = requests.delete(
            self.get_url(f"/candidate/event/{self.candidate_id}"),
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "Candidate deleted successfully" in data["message"]

        # Verify the candidate was deleted
        response = requests.get(
            self.get_url("/candidate/event"),
            params={"id": self.candidate_id},
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0  # Should be empty

    def test_post_candidate_event_as_different_user(self):
        """Test creating a candidate event as a different user."""
        candidate_data = {
            "graceid": "S190425z",  # Required field
            "candidate_name": "User Test Candidate",
            "ra": 130.456,
            "dec": -15.345
        }

        response = requests.post(
            self.get_url("/candidate/event"),
            json=candidate_data,
            headers={"api_token": self.user_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "id" in data

        # Store this candidate ID
        self.user_candidate_id = data["id"]

        # Verify the user ID is correct
        response = requests.get(
            self.get_url("/candidate/event"),
            params={"id": self.user_candidate_id},
            headers={"api_token": self.user_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["submitterid"] == 2  # User token corresponds to user ID 2

    def test_update_candidate_event_unauthorized(self):
        """Test updating a candidate event created by a different user."""
        # First create a candidate as admin
        candidate_data = {
            "graceid": "S190425z",  # Required field
            "candidate_name": "Admin Candidate",
            "ra": 140.456,
            "dec": -20.345
        }

        response = requests.post(
            self.get_url("/candidate/event"),
            json=candidate_data,
            headers={"api_token": self.admin_token}
        )

        admin_candidate_id = response.json()["id"]

        # Try to update as regular user
        update_data = {
            "graceid": "S190425z",  # Required field 
            "candidate_name": "Hijacked Candidate"
        }

        response = requests.put(
            self.get_url(f"/candidate/event/{admin_candidate_id}"),
            json=update_data,
            headers={"api_token": self.user_token}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["message"]

    def test_delete_candidate_event_unauthorized(self):
        """Test deleting a candidate event created by a different user."""
        # First create a candidate as admin
        candidate_data = {
            "graceid": "S190425z",  # Required field
            "candidate_name": "Admin Protected Candidate",
            "ra": 150.456,
            "dec": -25.345
        }

        response = requests.post(
            self.get_url("/candidate/event"),
            json=candidate_data,
            headers={"api_token": self.admin_token}
        )

        admin_candidate_id = response.json()["id"]

        # Try to delete as regular user
        response = requests.delete(
            self.get_url(f"/candidate/event/{admin_candidate_id}"),
            headers={"api_token": self.user_token}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["message"]

    def test_candidate_event_unauthorized_access(self):
        """Test that unauthorized requests are rejected."""
        # Request without API token
        response = requests.get(self.get_url("/candidate/event"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Request with invalid API token
        response = requests.get(
            self.get_url("/candidate/event"),
            headers={"api_token": self.invalid_token}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_candidate_events_with_different_tokens(self):
        """Test access with different valid API tokens."""
        # All authenticated users should be able to read candidates
        for token in [self.admin_token, self.user_token, self.scientist_token]:
            response = requests.get(
                self.get_url("/candidate/event"),
                headers={"api_token": token}
            )
            assert response.status_code == status.HTTP_200_OK

    def test_post_candidate_event_missing_required_fields(self):
        """Test creating a candidate event with missing required fields."""
        incomplete_data = {
            "candidate_name": "Incomplete Candidate",
            # Missing graceid, ra, dec
        }

        response = requests.post(
            self.get_url("/candidate/event"),
            json=incomplete_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST  # Validation error
        assert 'missing' in response.json()['errors'][0]['params']['type']
        assert 'graceid' in response.json()['errors'][0]['params']['field']

    def test_update_candidate_event_nonexistent(self):
        """Test updating a non-existent candidate event."""
        update_data = {
            "graceid": "S190425z",  # Required field
            "candidate_name": "NonExistent Candidate"
        }

        response = requests.put(
            self.get_url("/candidate/event/99999"),  # Non-existent ID
            json=update_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Candidate not found" in response.json()["message"]

    def test_delete_candidate_event_nonexistent(self):
        """Test deleting a non-existent candidate event."""
        response = requests.delete(
            self.get_url("/candidate/event/99999"),  # Non-existent ID
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Candidate not found" in response.json()["message"]


class TestEventAPIValidation:
    """Test validation of event API endpoints."""

    admin_token = "test_token_admin_001"

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    def test_invalid_ra_dec(self):
        """Test creating candidate event with invalid ra/dec values."""
        invalid_data = {
            "graceid": "S190425z",  # Required field
            "candidate_name": "Invalid Coordinates",
            "ra": "not-a-number",
            "dec": "also-not-a-number"
        }

        response = requests.post(
            self.get_url("/candidate/event"),
            json=invalid_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST  # Validation error
        errors = response.json()["errors"]
        assert any("ra" in str(e) for e in errors)
        assert any("dec" in str(e) for e in errors)

    def test_out_of_range_coordinates(self):
        """Test creating candidate event with out-of-range coordinates."""
        invalid_data = {
            "graceid": "S190425z",  # Required field
            "candidate_name": "Out of Range Coordinates",
            "ra": 400.0,  # RA should be 0-360
            "dec": -100.0  # Dec should be -90 to +90
        }

        response = requests.post(
            self.get_url("/candidate/event"),
            json=invalid_data,
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST  # Validation error
        errors = response.json()["errors"]
        assert any("ra" in str(e) for e in errors) or any("dec" in str(e) for e in errors)


class TestEventAPIIntegration:
    """Integration tests for event API workflows."""

    admin_token = "test_token_admin_001"

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    def test_complete_event_workflow(self):
        """Test complete workflow: create, read, update, delete candidate event."""
        # Step 1: Create candidate event
        create_data = {
            "graceid": "S190425z",  # Required field
            "candidate_name": "Workflow Test Candidate",
            "ra": 160.0,
            "dec": -30.0
        }

        create_response = requests.post(
            self.get_url("/candidate/event"),
            json=create_data,
            headers={"api_token": self.admin_token}
        )

        assert create_response.status_code == status.HTTP_200_OK
        candidate_id = create_response.json()["id"]

        # Step 2: Read the candidate
        read_response = requests.get(
            self.get_url("/candidate/event"),
            params={"id": candidate_id},
            headers={"api_token": self.admin_token}
        )

        assert read_response.status_code == status.HTTP_200_OK
        candidate_data = read_response.json()[0]
        assert candidate_data["candidate_name"] == "Workflow Test Candidate"
        if "ra" in candidate_data:
            assert candidate_data["ra"] == 160.0
        if "dec" in candidate_data:
            assert candidate_data["dec"] == -30.0

        # Step 3: Update the candidate
        update_data = {
            "graceid": "S190425z",  # Required field
            "candidate_name": "Updated Workflow Candidate"
        }

        update_response = requests.put(
            self.get_url(f"/candidate/event/{candidate_id}"),
            json=update_data,
            headers={"api_token": self.admin_token}
        )

        assert update_response.status_code == status.HTTP_200_OK
        assert "Candidate updated successfully" in update_response.json()["message"]

        # Verify the update
        verify_response = requests.get(
            self.get_url("/candidate/event"),
            params={"id": candidate_id},
            headers={"api_token": self.admin_token}
        )

        updated_data = verify_response.json()[0]
        assert updated_data["candidate_name"] == "Updated Workflow Candidate"
        # Original fields should be unchanged
        if "ra" in updated_data:
            assert updated_data["ra"] == 160.0
        if "dec" in updated_data:
            assert updated_data["dec"] == -30.0

        # Step 4: Delete the candidate
        delete_response = requests.delete(
            self.get_url(f"/candidate/event/{candidate_id}"),
            headers={"api_token": self.admin_token}
        )

        assert delete_response.status_code == status.HTTP_200_OK
        assert "Candidate deleted successfully" in delete_response.json()["message"]

        # Verify deletion
        verify_deletion = requests.get(
            self.get_url("/candidate/event"),
            params={"id": candidate_id},
            headers={"api_token": self.admin_token}
        )

        assert verify_deletion.status_code == status.HTTP_200_OK
        assert len(verify_deletion.json()) == 0  # Should be empty

    def test_multiple_candidate_events_for_same_user(self):
        """Test creating multiple candidate events for the same user."""
        # Create several candidates
        candidate_ids = []
        for i in range(3):
            data = {
                "graceid": "S190425z",  # Required field
                "candidate_name": f"Multi Test Candidate {i}",
                "ra": 170.0 + i,
                "dec": -40.0 - i
            }

            response = requests.post(
                self.get_url("/candidate/event"),
                json=data,
                headers={"api_token": self.admin_token}
            )

            assert response.status_code == status.HTTP_200_OK
            candidate_ids.append(response.json()["id"])

        # Verify all candidates were created for the admin user
        response = requests.get(
            self.get_url("/candidate/event"),
            params={"user_id": 1},  # Admin user ID
            headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        candidates = response.json()
        
        # Check if all our created candidates are in the response
        created_candidates = [c for c in candidates if c["id"] in candidate_ids]
        assert len(created_candidates) == 3

        # Clean up
        for candidate_id in candidate_ids:
            requests.delete(
                self.get_url(f"/candidate/event/{candidate_id}"),
                headers={"api_token": self.admin_token}
            )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
