"""
Instrument API tests using regular HTTP requests.
These tests hit the actual API endpoints running on the server.
"""
import pytest
import requests
import os
from server.core.enums.instrument_type import instrument_type
from fastapi import status

# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1_PREFIX = "/api/v1"


class TestInstrumentAPI:
    """Test suite for instrument-related API endpoints using HTTP requests."""

    # Test API tokens from test data
    admin_token = "test_token_admin_001"
    user_token = "test_token_user_002"
    scientist_token = "test_token_sci_003"
    invalid_token = "invalid_token_123"

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    def test_get_all_instruments(self):
        """Test getting all instruments without filters."""
        response = requests.get(
            self.get_url("/instruments"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        instruments = response.json()
        assert len(instruments) == 3  # We have 3 test instruments
        assert all("id" in inst for inst in instruments)
        assert all("instrument_name" in inst for inst in instruments)

    def test_get_instrument_by_id(self):
        """Test getting a specific instrument by ID."""
        response = requests.get(
            self.get_url("/instruments?id=1"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        instruments = response.json()
        assert len(instruments) == 1
        assert instruments[0]["id"] == 1
        assert instruments[0]["instrument_name"] == "Test Optical Telescope"
        assert instruments[0]["nickname"] == "TOT"

    def test_get_instruments_by_ids(self):
        """Test getting multiple instruments by IDs."""
        response = requests.get(
            self.get_url("/instruments?ids=[1,2]"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        instruments = response.json()
        assert len(instruments) == 2
        ids = [inst["id"] for inst in instruments]
        assert 1 in ids
        assert 2 in ids

    def test_get_instruments_by_name_filter(self):
        """Test getting instruments by name filter."""
        response = requests.get(
            self.get_url("/instruments?name=Optical"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        instruments = response.json()
        assert len(instruments) == 1
        assert "Optical" in instruments[0]["instrument_name"]

    def test_get_instruments_by_type(self):
        """Test getting instruments by type."""
        response = requests.get(
            self.get_url(f"/instruments?type={instrument_type.photometric.value}"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        instruments = response.json()
        # We have 2 photometric instruments
        assert len(instruments) == 2
        assert all(inst["instrument_type"] == instrument_type.photometric.value for inst in instruments)

    def test_get_instruments_with_invalid_ids_format(self):
        """Test error handling for invalid IDs format."""
        response = requests.get(
            self.get_url("/instruments?ids=invalid"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid ids format" in response.json()["message"]

    def test_get_instruments_without_auth(self):
        """Test that authentication is required."""
        response = requests.get(self.get_url("/instruments"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "API token is required" in response.json()["message"]

    def test_get_instruments_with_invalid_token(self):
        """Test with invalid API token."""
        response = requests.get(
            self.get_url("/instruments"),
            headers={"api_token": self.invalid_token}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid API token" in response.json()["message"]

    def test_get_footprints_all(self):
        """Test getting all footprints."""
        response = requests.get(
            self.get_url("/footprints"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        footprints = response.json()
        assert len(footprints) == 3  # We have 3 test footprints
        assert all("id" in fp for fp in footprints)
        assert all("instrumentid" in fp for fp in footprints)
        assert all("footprint" in fp for fp in footprints)

    def test_get_footprints_by_id(self):
        """Test getting footprints for a specific instrument ID."""
        response = requests.get(
            self.get_url("/footprints?id=1"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        footprints = response.json()
        assert len(footprints) == 1
        assert footprints[0]["instrumentid"] == 1
        # Check that footprint is returned as WKT string
        assert "POLYGON" in footprints[0]["footprint"]

    def test_get_footprints_by_name(self):
        """Test getting footprints by instrument name."""
        response = requests.get(
            self.get_url("/footprints?name=Optical"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        footprints = response.json()
        assert len(footprints) == 1
        assert footprints[0]["instrumentid"] == 1

    def test_create_instrument(self):
        """Test creating a new instrument."""
        new_instrument = {
            "instrument_name": "New Test Telescope",
            "nickname": "NTT",
            "instrument_type": instrument_type.photometric.value
        }
        response = requests.post(
            self.get_url("/instruments"),
            json=new_instrument,
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        created = response.json()
        assert created["instrument_name"] == new_instrument["instrument_name"]
        assert created["nickname"] == new_instrument["nickname"]
        assert created["instrument_type"] == new_instrument["instrument_type"]
        assert created["submitterid"] == 1  # Admin user ID
        assert "id" in created
        assert "datecreated" in created

        # Store the created instrument ID for cleanup in other tests
        self._created_instrument_id = created["id"]

    def test_create_instrument_as_different_user(self):
        """Test creating an instrument as a different user."""
        new_instrument = {
            "instrument_name": "User Test Telescope",
            "nickname": "UTT",
            "instrument_type": instrument_type.spectroscopic.value
        }
        response = requests.post(
            self.get_url("/instruments"),
            json=new_instrument,
            headers={"api_token": self.user_token}
        )
        assert response.status_code == status.HTTP_200_OK
        created = response.json()
        assert created["submitterid"] == 2  # Test user ID

    def test_create_instrument_without_auth(self):
        """Test that authentication is required for creation."""
        new_instrument = {
            "instrument_name": "Unauthorized Telescope",
            "nickname": "UT",
            "instrument_type": instrument_type.photometric.value
        }
        response = requests.post(
            self.get_url("/instruments"),
            json=new_instrument
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_footprint(self):
        """Test creating a new footprint for an instrument."""
        # First, create an instrument to add footprint to
        new_instrument = {
            "instrument_name": "Footprint Test Telescope 5535",
            "nickname": "FTT 5535",
            "instrument_type": instrument_type.photometric.value
        }
        inst_response = requests.post(
            self.get_url("/instruments"),
            json=new_instrument,
            headers={"api_token": self.admin_token}
        )
        assert inst_response.status_code == status.HTTP_200_OK
        instrument_id = inst_response.json()["id"]

        # Now create a footprint
        new_footprint = {
            "instrumentid": instrument_id,
            "footprint": "POLYGON((-3 -3, 3 -3, 3 3, -3 3, -3 -3))"
        }
        response = requests.post(
            self.get_url("/footprints"),
            json=new_footprint,
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        created = response.json()
        assert created["instrumentid"] == instrument_id
        assert "POLYGON" in created["footprint"]

    def test_create_footprint_for_nonexistent_instrument(self):
        """Test creating footprint for non-existent instrument."""
        new_footprint = {
            "instrumentid": 9999,  # Non-existent ID
            "footprint": "POLYGON((-1 -1, 1 -1, 1 1, -1 1, -1 -1))"
        }
        response = requests.post(
            self.get_url("/footprints"),
            json=new_footprint,
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["message"]

    def test_create_footprint_for_others_instrument(self):
        """Test that users can't add footprints to instruments they don't own."""
        # Try to add footprint to instrument with ID 1 (owned by admin) using user token
        new_footprint = {
            "instrumentid": 1,
            "footprint": "POLYGON((-1 -1, 1 -1, 1 1, -1 1, -1 -1))"
        }
        response = requests.post(
            self.get_url("/footprints"),
            json=new_footprint,
            headers={"api_token": self.user_token}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "don't have permission" in response.json()["message"]

    def test_create_footprint_without_auth(self):
        """Test that authentication is required for footprint creation."""
        new_footprint = {
            "instrumentid": 1,
            "footprint": "POLYGON((-1 -1, 1 -1, 1 1, -1 1, -1 -1))"
        }
        response = requests.post(
            self.get_url("/footprints"),
            json=new_footprint
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_instruments_with_complex_query(self):
        """Test complex query combining multiple filters."""
        # First create some test data
        photometric_instruments = [
            {"instrument_name": f"Photometric {i}", "nickname": f"P{i}",
             "instrument_type": instrument_type.photometric.value}
            for i in range(2)
        ]
        for inst in photometric_instruments:
            requests.post(self.get_url("/instruments"), json=inst, headers={"api_token": self.admin_token})

        # Query by type and name pattern
        response = requests.get(
            self.get_url(f"/instruments?type={instrument_type.photometric.value}&name=Photometric"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        instruments = response.json()
        assert len(instruments) >= 2  # At least the ones we just created
        assert all("Photometric" in inst["instrument_name"] for inst in instruments)

    def test_instrument_data_format(self):
        """Test that instrument data is returned in the correct format."""
        response = requests.get(
            self.get_url("/instruments?id=1"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        instrument = response.json()[0]

        # Check all required fields are present
        required_fields = ["id", "instrument_name", "instrument_type", "datecreated", "submitterid"]
        for field in required_fields:
            assert field in instrument

        # Check data types
        assert isinstance(instrument["id"], int)
        assert isinstance(instrument["instrument_name"], str)
        assert isinstance(instrument["instrument_type"], int)
        assert isinstance(instrument["submitterid"], int)

        # Optional fields
        if "nickname" in instrument:
            assert isinstance(instrument["nickname"], str)

    def test_footprint_data_format(self):
        """Test that footprint data is returned in the correct format."""
        response = requests.get(
            self.get_url("/footprints?id=1"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        footprint = response.json()[0]

        # Check all required fields
        required_fields = ["id", "instrumentid", "footprint"]
        for field in required_fields:
            assert field in footprint

        # Check data types
        assert isinstance(footprint["id"], int)
        assert isinstance(footprint["instrumentid"], int)
        assert isinstance(footprint["footprint"], str)
        assert footprint["footprint"].startswith("POLYGON")


class TestInstrumentAPIValidation:
    """Test validation of instrument API endpoints."""

    admin_token = "test_token_admin_001"

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    def test_invalid_instrument_type(self):
        """Test creating instrument with invalid type."""
        invalid_instrument = {
            "instrument_name": "Invalid Type Telescope",
            "nickname": "ITT",
            "instrument_type": 999  # Invalid type
        }
        response = requests.post(
            self.get_url("/instruments"),
            json=invalid_instrument,
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST  # Validation error
        assert "Input should be" in response.json()['errors'][0]['message']

    def test_missing_required_fields(self):
        """Test creating instrument with missing required fields."""
        incomplete_instrument = {
            "nickname": "ITT"
            # Missing instrument_name and instrument_type
        }
        response = requests.post(
            self.get_url("/instruments"),
            json=incomplete_instrument,
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_fields = [field['params']['field'] for field in response.json()['errors']]
        assert "instrument_name" in str(error_fields)
        assert "instrument_type" in str(error_fields)

    def test_invalid_footprint_format(self):
        """Test creating footprint with invalid WKT format."""
        invalid_footprint = {
            "instrumentid": 1,
            "footprint": "INVALID WKT STRING"
        }
        response = requests.post(
            self.get_url("/footprints"),
            json=invalid_footprint,
            headers={"api_token": self.admin_token}
        )
        # This should fail at the database level
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid WKT format" in response.json()['errors'][0]['message']

    def test_empty_name_filter(self):
        """Test behavior with empty name filter."""
        response = requests.get(
            self.get_url("/instruments?name="),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        # Should return all instruments since empty filter matches all
        instruments = response.json()
        assert len(instruments) >= 3  # At least our test instruments


class TestInstrumentAPIPermissions:
    """Test permission-related aspects of instrument API endpoints."""

    admin_token = "test_token_admin_001"
    user_token = "test_token_user_002"
    scientist_token = "test_token_sci_003"

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    def test_all_users_can_read_instruments(self):
        """Test that all users can read instruments."""
        for token in [self.admin_token, self.user_token, self.scientist_token]:
            response = requests.get(
                self.get_url("/instruments"),
                headers={"api_token": token}
            )
            assert response.status_code == status.HTTP_200_OK

    def test_all_users_can_read_footprints(self):
        """Test that all users can read footprints."""
        for token in [self.admin_token, self.user_token, self.scientist_token]:
            response = requests.get(
                self.get_url("/footprints"),
                headers={"api_token": token}
            )
            assert response.status_code == status.HTTP_200_OK

    def test_all_users_can_create_instruments(self):
        """Test that all authenticated users can create instruments."""
        for i, token in enumerate([self.admin_token, self.user_token, self.scientist_token]):
            instrument = {
                "instrument_name": f"User{i} Telescope",
                "nickname": f"U{i}T",
                "instrument_type": instrument_type.photometric.value
            }
            response = requests.post(
                self.get_url("/instruments"),
                json=instrument,
                headers={"api_token": token}
            )
            assert response.status_code == status.HTTP_200_OK

    def test_footprint_creation_permission(self):
        """Test that users can only add footprints to their own instruments."""
        # Create an instrument as user
        instrument = {
            "instrument_name": "User Owned Telescope",
            "nickname": "UOT",
            "instrument_type": instrument_type.photometric.value
        }
        response = requests.post(
            self.get_url("/instruments"),
            json=instrument,
            headers={"api_token": self.user_token}
        )
        assert response.status_code == status.HTTP_200_OK
        user_instrument_id = response.json()["id"]

        # User should be able to add footprint to their own instrument
        footprint = {
            "instrumentid": user_instrument_id,
            "footprint": "POLYGON((-1 -1, 1 -1, 1 1, -1 1, -1 -1))"
        }
        response = requests.post(
            self.get_url("/footprints"),
            json=footprint,
            headers={"api_token": self.user_token}
        )
        assert response.status_code == status.HTTP_200_OK

        # Admin should NOT be able to add footprint to user's instrument
        response = requests.post(
            self.get_url("/footprints"),
            json=footprint,
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestInstrumentAPIIntegration:
    """Integration tests that test complete workflows."""

    admin_token = "test_token_admin_001"

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    def test_complete_instrument_creation_workflow(self):
        """Test complete workflow of creating instrument and adding footprints."""
        # Step 1: Create instrument
        new_instrument = {
            "instrument_name": "Integration Test Telescope",
            "nickname": "ITT",
            "instrument_type": instrument_type.photometric.value
        }
        response = requests.post(
            self.get_url("/instruments"),
            json=new_instrument,
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        instrument = response.json()
        instrument_id = instrument["id"]

        # Step 2: Verify instrument was created
        response = requests.get(
            self.get_url(f"/instruments?id={instrument_id}"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1
        assert response.json()[0]["instrument_name"] == new_instrument["instrument_name"]

        # Step 3: Add footprint to instrument
        footprint = {
            "instrumentid": instrument_id,
            "footprint": "POLYGON((-2 -2, 2 -2, 2 2, -2 2, -2 -2))"
        }
        response = requests.post(
            self.get_url("/footprints"),
            json=footprint,
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        created_footprint = response.json()

        # Step 4: Verify footprint was created
        response = requests.get(
            self.get_url(f"/footprints?id={instrument_id}"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        footprints = response.json()
        assert len(footprints) == 1
        assert footprints[0]["instrumentid"] == instrument_id
        assert "POLYGON" in footprints[0]["footprint"]

    def test_query_instruments_by_multiple_criteria(self):
        """Test querying instruments with multiple filters."""
        # Create test instruments
        test_instruments = [
            {"instrument_name": "Multi Test Optical 1", "nickname": "MTO1",
             "instrument_type": instrument_type.photometric.value},
            {"instrument_name": "Multi Test Optical 2", "nickname": "MTO2",
             "instrument_type": instrument_type.photometric.value},
            {"instrument_name": "Multi Test Spectro", "nickname": "MTS",
             "instrument_type": instrument_type.spectroscopic.value}
        ]

        created_ids = []
        for inst in test_instruments:
            response = requests.post(
                self.get_url("/instruments"),
                json=inst,
                headers={"api_token": self.admin_token}
            )
            assert response.status_code == status.HTTP_200_OK
            created_ids.append(response.json()["id"])

        # Query by type
        response = requests.get(
            self.get_url(f"/instruments?type={instrument_type.photometric.value}"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        photometric_insts = response.json()
        assert len([inst for inst in photometric_insts if inst["id"] in created_ids]) == 2

        # Query by name pattern
        response = requests.get(
            self.get_url("/instruments?name=Multi Test"),
            headers={"api_token": self.admin_token}
        )
        assert response.status_code == status.HTTP_200_OK
        named_insts = response.json()
        assert len([inst for inst in named_insts if inst["id"] in created_ids]) >= 3


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
