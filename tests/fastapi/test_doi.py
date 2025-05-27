"""
Test DOI-related endpoints with real requests to the FastAPI application.
Tests use specific data from test-data.sql.
"""
import os
import requests
import json
import datetime
from typing import Dict, Any, List, Optional
import pytest
from fastapi import status

# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1_PREFIX = "/api/v1"


class TestDOIEndpoints:
    """Test class for DOI-related API endpoints."""

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
    
    def create_test_pointing(self, graceid):
        """Helper method to create a test pointing."""
        pointing_data = {
            "graceid": graceid,
            "pointing": {
                "ra": 123.456,
                "dec": -12.345,
                "instrumentid": 1,
                "depth": 20.5,
                "depth_unit": "ab_mag",
                "time": "2023-01-01T12:00:00.000000",
                "status": "completed",
                "band": "r"
            }
        }
        
        response = requests.post(
            self.get_url("/pointings"),
            json=pointing_data,
            headers={"api_token": self.admin_token}
        )
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Failed to create test pointing: {response.text}")
        
        return response.json()["pointing_ids"][0]

    def test_request_doi_with_single_id(self):
        """Test requesting a DOI with a single pointing ID."""
        # First create a test pointing
        pointing_id = self.create_test_pointing(self.KNOWN_GRACEIDS[0])
        
        # Now request a DOI for it
        doi_data = {
            "id": pointing_id,
            "creators": [
                {
                    "name": "Test Author",
                    "affiliation": "Test Institution"
                }
            ]
        }
        
        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "DOI_URL" in data
        assert data["DOI_URL"] is not None

    def test_request_doi_with_multiple_ids(self):
        """Test requesting a DOI with multiple pointing IDs."""
        # Create multiple test pointings
        pointing_ids = []
        for _ in range(2):
            pointing_id = self.create_test_pointing(self.KNOWN_GRACEIDS[0])
            pointing_ids.append(pointing_id)
        
        # Now request a DOI for them
        doi_data = {
            "ids": pointing_ids,
            "creators": [
                {
                    "name": "Test Author",
                    "affiliation": "Test Institution"
                }
            ]
        }
        
        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "DOI_URL" in data
        assert data["DOI_URL"] is not None

    def test_request_doi_with_graceid(self):
        """Test requesting a DOI with a graceid."""
        graceid = self.KNOWN_GRACEIDS[0]
        
        # Create multiple test pointings for the same graceid
        for _ in range(2):
            self.create_test_pointing(graceid)
        
        # Now request a DOI for all pointings with this graceid
        doi_data = {
            "graceid": graceid,
            "creators": [
                {
                    "name": "Test Author",
                    "affiliation": "Test Institution"
                }
            ]
        }
        
        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "DOI_URL" in data
        assert data["DOI_URL"] is not None

    def test_request_doi_with_existing_url(self):
        """Test requesting a DOI with an existing DOI URL."""
        # First create a test pointing
        pointing_id = self.create_test_pointing(self.KNOWN_GRACEIDS[0])
        
        # Now request a DOI with an existing URL
        doi_data = {
            "id": pointing_id,
            "doi_url": "https://doi.org/10.5281/zenodo.example",
            "creators": [
                {
                    "name": "Test Author",
                    "affiliation": "Test Institution"
                }
            ]
        }
        
        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "DOI_URL" in data
        assert data["DOI_URL"] == "https://doi.org/10.5281/zenodo.example"

    def test_request_doi_with_doi_group_id(self):
        """Test requesting a DOI with a DOI group ID."""
        # First create a test pointing
        pointing_id = self.create_test_pointing(self.KNOWN_GRACEIDS[0])
        
        # Get DOI author groups for the user
        response = requests.get(
            self.get_url("/doi_author_groups"),
            headers={"api_token": self.admin_token}
        )
        
        if response.status_code != status.HTTP_200_OK or len(response.json()) == 0:
            pytest.skip("No DOI author groups available for testing")
        
        group_id = response.json()[0]["id"]
        
        # Now request a DOI with the group ID
        doi_data = {
            "id": pointing_id,
            "doi_group_id": group_id
        }
        
        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token}
        )
        
        # If the group has valid authors, this should succeed
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "DOI_URL" in data
            assert data["DOI_URL"] is not None
        else:
            # The group might not have valid authors in test data
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid doi_group_id" in response.json()["detail"]

    def test_request_doi_without_creators(self):
        """Test requesting a DOI without specifying creators."""
        # First create a test pointing
        pointing_id = self.create_test_pointing(self.KNOWN_GRACEIDS[0])
        
        # Now request a DOI without specifying creators
        doi_data = {
            "id": pointing_id
        }
        
        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "DOI_URL" in data
        assert data["DOI_URL"] is not None

    def test_request_doi_with_invalid_creators(self):
        """Test requesting a DOI with invalid creators."""
        # First create a test pointing
        pointing_id = self.create_test_pointing(self.KNOWN_GRACEIDS[0])
        
        # Now request a DOI with invalid creators (missing affiliation)
        doi_data = {
            "id": pointing_id,
            "creators": [
                {
                    "name": "Test Author"
                    # Missing affiliation
                }
            ]
        }
        
        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name and affiliation are required" in response.json()["detail"]

    def test_request_doi_with_insufficient_params(self):
        """Test requesting a DOI with insufficient parameters."""
        # Request a DOI without any identifier
        doi_data = {
            "creators": [
                {
                    "name": "Test Author",
                    "affiliation": "Test Institution"
                }
            ]
        }
        
        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient filter parameters" in response.json()["detail"]

    def test_request_doi_for_others_pointings(self):
        """Test that user can only request DOIs for their own pointings."""
        # First create a test pointing as admin
        pointing_id = self.create_test_pointing(self.KNOWN_GRACEIDS[0])
        
        # Now try to request a DOI for it as a different user
        doi_data = {
            "id": pointing_id,
            "creators": [
                {
                    "name": "Test Author",
                    "affiliation": "Test Institution"
                }
            ]
        }
        
        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.user_token}  # Different user
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No pointings to give DOI" in response.json()["detail"]

    def test_get_doi_pointings(self):
        """Test getting all pointings with DOIs."""
        # First create a pointing and give it a DOI
        pointing_id = self.create_test_pointing(self.KNOWN_GRACEIDS[0])
        
        doi_data = {
            "id": pointing_id,
            "creators": [
                {
                    "name": "Test Author",
                    "affiliation": "Test Institution"
                }
            ]
        }
        
        doi_response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token}
        )
        
        assert doi_response.status_code == status.HTTP_200_OK
        
        # Now get all DOI pointings
        response = requests.get(
            self.get_url("/doi_pointings"),
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "pointings" in data
        assert isinstance(data["pointings"], list)
        
        # The newly created pointing should be in the list
        pointing_ids = [p["id"] for p in data["pointings"]]
        assert pointing_id in pointing_ids

    def test_get_doi_author_groups(self):
        """Test getting DOI author groups."""
        response = requests.get(
            self.get_url("/doi_author_groups"),
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        
        # Each group should have an id and name
        for group in data:
            assert "id" in group
            assert "name" in group

    def test_get_doi_authors(self):
        """Test getting DOI authors for a group."""
        # First get available groups
        groups_response = requests.get(
            self.get_url("/doi_author_groups"),
            headers={"api_token": self.admin_token}
        )
        
        if groups_response.status_code != status.HTTP_200_OK or len(groups_response.json()) == 0:
            pytest.skip("No DOI author groups available for testing")
        
        group_id = groups_response.json()[0]["id"]
        
        # Now get authors for this group
        response = requests.get(
            self.get_url(f"/doi_authors/{group_id}"),
            headers={"api_token": self.admin_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        
        # Each author should have name and affiliation
        for author in data:
            assert "name" in author
            assert "affiliation" in author
            assert "author_groupid" in author
            assert author["author_groupid"] == group_id

    def test_get_doi_authors_for_others_group(self):
        """Test that user can only access their own DOI author groups."""
        # First get available groups for admin
        groups_response = requests.get(
            self.get_url("/doi_author_groups"),
            headers={"api_token": self.admin_token}
        )
        
        if groups_response.status_code != status.HTTP_200_OK or len(groups_response.json()) == 0:
            pytest.skip("No DOI author groups available for testing")
        
        group_id = groups_response.json()[0]["id"]
        
        # Now try to get authors for this group as a different user
        response = requests.get(
            self.get_url(f"/doi_authors/{group_id}"),
            headers={"api_token": self.user_token}  # Different user
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "You don't have permission" in response.json()["detail"]

    def test_authentication_required(self):
        """Test that authentication is required for all endpoints."""
        endpoints = [
            "/doi_pointings",
            "/doi_author_groups"
        ]
        
        for endpoint in endpoints:
            response = requests.get(self.get_url(endpoint))
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            
        # Test POST endpoint
        response = requests.post(
            self.get_url("/request_doi"),
            json={"id": 1}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])