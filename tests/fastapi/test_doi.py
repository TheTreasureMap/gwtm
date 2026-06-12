import os
import requests
import datetime
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
    KNOWN_GRACEIDS = ["S190425z", "S190426c", "MS230101a", "GW190521", "MS190425a"]

    def create_completed_pointing(self, graceid, token):
        """Helper method to create a completed pointing that's eligible for DOI."""
        pointing_data = {
            "graceid": graceid,
            "pointing": {
                "ra": 123.456
                + (
                    datetime.datetime.now().microsecond / 1000000
                ),  # Add some randomness
                "dec": -12.345 + (datetime.datetime.now().microsecond / 1000000),
                "instrumentid": 1,
                "depth": 20.5,
                "depth_unit": "ab_mag",
                "time": datetime.datetime.now().isoformat(),
                "status": "completed",  # This is crucial - must be completed
                "pos_angle": 0.0,
                "band": "r",
            },
        }

        response = requests.post(
            self.get_url("/pointings"), json=pointing_data, headers={"api_token": token}
        )

        if response.status_code != status.HTTP_200_OK:
            pytest.fail(f"Failed to create test pointing: {response.text}")

        return response.json()["pointing_ids"][0]

    @pytest.mark.skip(reason="Skipping test that requires external Zenodo API calls")
    def test_request_doi_with_single_id(self):
        """Test requesting a DOI with a single pointing ID."""
        # First create a completed pointing
        pointing_id = self.create_completed_pointing(
            self.KNOWN_GRACEIDS[0], self.admin_token
        )

        # Now request a DOI for it
        doi_data = {
            "id": pointing_id,
            "creators": [{"name": "Test Author", "affiliation": "Test Institution"}],
        }

        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "DOI_URL" in data

    @pytest.mark.skip(reason="Skipping test that requires external Zenodo API calls")
    def test_request_doi_with_multiple_ids(self):
        """Test requesting a DOI with multiple pointing IDs."""
        # Create multiple completed pointings
        pointing_ids = []
        for _ in range(2):
            pointing_id = self.create_completed_pointing(
                self.KNOWN_GRACEIDS[0], self.admin_token
            )
            pointing_ids.append(pointing_id)

        # Now request a DOI for them
        doi_data = {
            "ids": pointing_ids,
            "creators": [{"name": "Test Author", "affiliation": "Test Institution"}],
        }

        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "DOI_URL" in data

    @pytest.mark.skip(reason="Skipping test that requires external Zenodo API calls")
    def test_request_doi_with_graceid(self):
        """Test requesting a DOI with a graceid."""
        graceid = self.KNOWN_GRACEIDS[0]

        # Create multiple completed pointings for the same graceid
        for _ in range(2):
            self.create_completed_pointing(graceid, self.admin_token)

        # Now request a DOI for all pointings with this graceid
        doi_data = {
            "graceid": graceid,
            "creators": [{"name": "Test Author", "affiliation": "Test Institution"}],
        }

        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "DOI_URL" in data

    @pytest.mark.skip(reason="Skipping test that requires external Zenodo API calls")
    def test_request_doi_with_existing_url(self):
        """Test requesting a DOI with an existing DOI URL."""
        # First create a completed pointing
        pointing_id = self.create_completed_pointing(
            self.KNOWN_GRACEIDS[0], self.admin_token
        )

        # Now request a DOI with an existing URL
        doi_data = {
            "id": pointing_id,
            "doi_url": "https://doi.org/10.5281/zenodo.example",
            "creators": [{"name": "Test Author", "affiliation": "Test Institution"}],
        }

        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "DOI_URL" in data
        assert data["DOI_URL"] == "https://doi.org/10.5281/zenodo.example"

    @pytest.mark.skip(reason="Skipping test that requires external Zenodo API calls")
    def test_request_doi_with_doi_group_id(self):
        """Test requesting a DOI with a DOI group ID."""
        # First create a completed pointing
        pointing_id = self.create_completed_pointing(
            self.KNOWN_GRACEIDS[0], self.admin_token
        )

        # Get DOI author groups for the user
        response = requests.get(
            self.get_url("/doi_author_groups"), headers={"api_token": self.admin_token}
        )

        if response.status_code != status.HTTP_200_OK or len(response.json()) == 0:
            pytest.skip("No DOI author groups available for testing")

        group_id = response.json()[0]["id"]

        # Now request a DOI with the group ID
        doi_data = {"id": pointing_id, "doi_group_id": group_id}

        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token},
        )

        # If the group has valid authors, this should succeed
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "DOI_URL" in data
        else:
            # The group might not have valid authors in test data
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "validation error" in response.json()["message"]

    @pytest.mark.skip(reason="Skipping test that requires external Zenodo API calls")
    def test_request_doi_without_creators(self):
        """Test requesting a DOI without specifying creators."""
        # First create a completed pointing
        pointing_id = self.create_completed_pointing(
            self.KNOWN_GRACEIDS[0], self.admin_token
        )

        # Now request a DOI without specifying creators
        doi_data = {"id": pointing_id}

        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "DOI_URL" in data

    def test_request_doi_with_invalid_creators(self):
        """Test requesting a DOI with invalid creators."""
        # First create a completed pointing
        pointing_id = self.create_completed_pointing(
            self.KNOWN_GRACEIDS[0], self.admin_token
        )

        # Now request a DOI with invalid creators (missing affiliation)
        doi_data = {
            "id": pointing_id,
            "creators": [
                {
                    "name": "Test Author"
                    # Missing affiliation
                }
            ],
        }

        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Request validation error" in response.json()["message"]

    def test_request_doi_with_insufficient_params(self):
        """Test requesting a DOI with insufficient parameters."""
        # Request a DOI without any identifier
        doi_data = {
            "creators": [{"name": "Test Author", "affiliation": "Test Institution"}]
        }

        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Request validation error" in response.json()["message"]

    def test_request_doi_for_others_pointings(self):
        """Test that user can only request DOIs for their own pointings."""
        # First create a completed pointing as admin
        pointing_id = self.create_completed_pointing(
            self.KNOWN_GRACEIDS[0], self.admin_token
        )

        # Now try to request a DOI for it as a different user
        doi_data = {
            "id": pointing_id,
            "creators": [{"name": "Test Author", "affiliation": "Test Institution"}],
        }

        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.user_token},  # Different user
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No valid pointings found for DOI request" in response.json()["message"]

    def test_request_doi_for_planned_pointing(self):
        """Test that DOI cannot be requested for planned pointings."""
        # Create a planned pointing (not completed)
        pointing_data = {
            "graceid": self.KNOWN_GRACEIDS[0],
            "pointing": {
                "ra": 123.456,
                "dec": -12.345,
                "instrumentid": 1,
                "depth": 20.5,
                "depth_unit": "ab_mag",
                "time": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).isoformat(),
                "status": "planned",  # Not completed
                "band": "r",
            },
        }

        response = requests.post(
            self.get_url("/pointings"),
            json=pointing_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        pointing_id = response.json()["pointing_ids"][0]

        # Now try to request a DOI for the planned pointing
        doi_data = {
            "id": pointing_id,
            "creators": [{"name": "Test Author", "affiliation": "Test Institution"}],
        }

        response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No valid pointings found for DOI request" in response.json()["message"]

    @pytest.mark.skip(reason="Skipping test that requires external Zenodo API calls")
    def test_get_doi_pointings(self):
        """Test getting all pointings with DOIs."""
        # First create a completed pointing
        pointing_id = self.create_completed_pointing(
            self.KNOWN_GRACEIDS[0], self.admin_token
        )

        # Request a DOI for the pointing (will likely fail in test environment, but endpoint should work)
        doi_data = {
            "id": pointing_id,
            "creators": [{"name": "Test Author", "affiliation": "Test Institution"}],
        }

        # Request a DOI for the pointing
        doi_response = requests.post(
            self.get_url("/request_doi"),
            json=doi_data,
            headers={"api_token": self.admin_token},
        )

        assert doi_response.status_code == status.HTTP_200_OK

        # In test environment, DOI creation may fail, but endpoint should still work
        doi_data_result = doi_response.json()
        assert "DOI_URL" in doi_data_result
        assert "WARNINGS" in doi_data_result

        # Now get all DOI pointings
        response = requests.get(
            self.get_url("/doi_pointings"), headers={"api_token": self.admin_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "pointings" in data
        assert isinstance(data["pointings"], list)

        # In test environment, DOI creation may fail, so pointing may not have DOI
        # Just verify the endpoint works and returns the expected structure
        pointing_ids = [p["id"] for p in data["pointings"]]

        # If DOI was successfully created, the pointing should be in the list
        # If not, that's also acceptable in test environment
        if doi_data_result.get("DOI_URL"):
            assert pointing_id in pointing_ids
        else:
            # DOI creation failed (expected in test), so pointing won't be in DOI list
            # This is acceptable - we've verified the endpoints work correctly
            pass

    def test_get_doi_author_groups(self):
        """Test getting DOI author groups."""
        response = requests.get(
            self.get_url("/doi_author_groups"), headers={"api_token": self.admin_token}
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
            self.get_url("/doi_author_groups"), headers={"api_token": self.admin_token}
        )

        if (
            groups_response.status_code != status.HTTP_200_OK
            or len(groups_response.json()) == 0
        ):
            pytest.skip("No DOI author groups available for testing")

        group_id = groups_response.json()[0]["id"]

        # Now get authors for this group
        response = requests.get(
            self.get_url(f"/doi_authors/{group_id}"),
            headers={"api_token": self.admin_token},
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
            self.get_url("/doi_author_groups"), headers={"api_token": self.admin_token}
        )

        if (
            groups_response.status_code != status.HTTP_200_OK
            or len(groups_response.json()) == 0
        ):
            pytest.skip("No DOI author groups available for testing")

        group_id = groups_response.json()[0]["id"]

        # Now try to get authors for this group as a different user
        response = requests.get(
            self.get_url(f"/doi_authors/{group_id}"),
            headers={"api_token": self.user_token},  # Different user
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "You don't have permission" in response.json()["message"]

    def test_authentication_patterns(self):
        """Test authentication requirements for different endpoint types."""
        # All DOI endpoints require authentication as they return user-specific data
        protected_endpoints = ["/doi_pointings", "/doi_author_groups"]
        
        for endpoint in protected_endpoints:
            response = requests.get(self.get_url(endpoint))
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # POST endpoints require authentication
        response = requests.post(self.get_url("/request_doi"), json={"id": 1})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDOIAuthorGroupCRUD:
    """Test create / read / update / delete for DOI author groups."""

    admin_token = "test_token_admin_001"
    user_token = "test_token_user_002"

    def get_url(self, endpoint):
        return f"{API_BASE_URL}{API_V1_PREFIX}{endpoint}"

    def _auth(self, token):
        return {"api_token": token}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_group(self, name="Test Group", authors=None, token=None):
        """Create a group and return the response."""
        if authors is None:
            authors = [{"name": "Alice Smith", "affiliation": "MIT"}]
        token = token or self.admin_token
        return requests.post(
            self.get_url("/doi_author_groups"),
            json={"name": name, "authors": authors},
            headers=self._auth(token),
        )

    def _delete_group(self, group_id, token=None):
        token = token or self.admin_token
        requests.delete(
            self.get_url(f"/doi_author_groups/{group_id}"),
            headers=self._auth(token),
        )

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def test_create_group_returns_201_with_correct_fields(self):
        response = self._create_group("Create Test Group")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Create Test Group"
        assert "id" in data
        self._delete_group(data["id"])

    def test_create_group_with_full_author_fields(self):
        authors = [{"name": "Bob Jones", "affiliation": "Caltech",
                    "orcid": "0000-0001-2345-6789", "gnd": "gnd123"}]
        response = self._create_group("Full Fields Group", authors=authors)
        assert response.status_code == status.HTTP_201_CREATED
        group_id = response.json()["id"]

        authors_resp = requests.get(
            self.get_url(f"/doi_authors/{group_id}"),
            headers=self._auth(self.admin_token),
        )
        assert authors_resp.status_code == status.HTTP_200_OK
        author = authors_resp.json()[0]
        assert author["orcid"] == "0000-0001-2345-6789"
        assert author["gnd"] == "gnd123"
        self._delete_group(group_id)

    def test_create_group_multiple_authors(self):
        authors = [
            {"name": "Author One", "affiliation": "Uni A"},
            {"name": "Author Two", "affiliation": "Uni B"},
            {"name": "Author Three", "affiliation": "Uni C"},
        ]
        response = self._create_group("Multi-Author Group", authors=authors)
        assert response.status_code == status.HTTP_201_CREATED
        group_id = response.json()["id"]

        authors_resp = requests.get(
            self.get_url(f"/doi_authors/{group_id}"),
            headers=self._auth(self.admin_token),
        )
        assert len(authors_resp.json()) == 3
        self._delete_group(group_id)

    def test_create_group_unauthenticated_returns_401(self):
        response = requests.post(
            self.get_url("/doi_author_groups"),
            json={"name": "Should Fail", "authors": []},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    def test_created_group_appears_in_list(self):
        response = self._create_group("List Test Group")
        group_id = response.json()["id"]

        list_resp = requests.get(
            self.get_url("/doi_author_groups"),
            headers=self._auth(self.admin_token),
        )
        assert list_resp.status_code == status.HTTP_200_OK
        ids = [g["id"] for g in list_resp.json()]
        assert group_id in ids
        self._delete_group(group_id)

    def test_groups_not_visible_to_other_users(self):
        """A group created by admin should not appear in another user's list."""
        response = self._create_group("Admin Private Group")
        group_id = response.json()["id"]

        list_resp = requests.get(
            self.get_url("/doi_author_groups"),
            headers=self._auth(self.user_token),
        )
        assert list_resp.status_code == status.HTTP_200_OK
        ids = [g["id"] for g in list_resp.json()]
        assert group_id not in ids
        self._delete_group(group_id)

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def test_update_group_name(self):
        group_id = self._create_group("Original Name").json()["id"]

        update_resp = requests.put(
            self.get_url(f"/doi_author_groups/{group_id}"),
            json={"name": "Updated Name", "authors": [
                {"name": "Alice Smith", "affiliation": "MIT"}
            ]},
            headers=self._auth(self.admin_token),
        )
        assert update_resp.status_code == status.HTTP_200_OK
        assert update_resp.json()["name"] == "Updated Name"
        self._delete_group(group_id)

    def test_update_adds_and_removes_authors(self):
        """Update should sync authors: add new ones, delete removed ones."""
        group_id = self._create_group(
            "Sync Test",
            authors=[{"name": "Keep Me", "affiliation": "Uni A"},
                     {"name": "Remove Me", "affiliation": "Uni B"}],
        ).json()["id"]

        # Fetch existing author ids
        existing = requests.get(
            self.get_url(f"/doi_authors/{group_id}"),
            headers=self._auth(self.admin_token),
        ).json()
        keep_id = next(a["id"] for a in existing if a["name"] == "Keep Me")

        # Update: keep one, drop the other, add a new one
        update_resp = requests.put(
            self.get_url(f"/doi_author_groups/{group_id}"),
            json={"name": "Sync Test", "authors": [
                {"id": keep_id, "name": "Keep Me", "affiliation": "Uni A"},
                {"name": "New Author", "affiliation": "Uni C"},
            ]},
            headers=self._auth(self.admin_token),
        )
        assert update_resp.status_code == status.HTTP_200_OK

        final = requests.get(
            self.get_url(f"/doi_authors/{group_id}"),
            headers=self._auth(self.admin_token),
        ).json()
        names = {a["name"] for a in final}
        assert "Keep Me" in names
        assert "New Author" in names
        assert "Remove Me" not in names
        self._delete_group(group_id)

    def test_update_another_users_group_returns_404(self):
        """user_token should not be able to update admin's group."""
        group_id = self._create_group("Admin Group").json()["id"]

        resp = requests.put(
            self.get_url(f"/doi_author_groups/{group_id}"),
            json={"name": "Hijacked", "authors": []},
            headers=self._auth(self.user_token),
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        self._delete_group(group_id)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def test_delete_group_removes_it_from_list(self):
        group_id = self._create_group("Delete Me").json()["id"]

        del_resp = requests.delete(
            self.get_url(f"/doi_author_groups/{group_id}"),
            headers=self._auth(self.admin_token),
        )
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT

        list_resp = requests.get(
            self.get_url("/doi_author_groups"),
            headers=self._auth(self.admin_token),
        )
        ids = [g["id"] for g in list_resp.json()]
        assert group_id not in ids

    def test_delete_cascades_to_authors(self):
        """After group deletion, its authors should be inaccessible."""
        group_id = self._create_group("Cascade Delete").json()["id"]

        requests.delete(
            self.get_url(f"/doi_author_groups/{group_id}"),
            headers=self._auth(self.admin_token),
        )

        # Fetching authors for a deleted (non-existent) group returns 403
        resp = requests.get(
            self.get_url(f"/doi_authors/{group_id}"),
            headers=self._auth(self.admin_token),
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_another_users_group_returns_404(self):
        group_id = self._create_group("Protected Group").json()["id"]

        resp = requests.delete(
            self.get_url(f"/doi_author_groups/{group_id}"),
            headers=self._auth(self.user_token),
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        self._delete_group(group_id)  # cleanup

    def test_delete_unauthenticated_returns_401(self):
        group_id = self._create_group("Auth Delete Test").json()["id"]

        resp = requests.delete(self.get_url(f"/doi_author_groups/{group_id}"))
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        self._delete_group(group_id)  # cleanup
