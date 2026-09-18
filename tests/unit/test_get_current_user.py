"""Unit tests for token resolution in get_current_user."""

import pytest
from fastapi import HTTPException, Response

from server.auth import auth
from tests.unit.test_audit import FakeUser, make_request


class FakeQuery:
    """Returns whatever the fake session was primed with."""

    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class FakeDB:
    def __init__(self, result):
        self.result = result
        self.queries = 0

    def query(self, *args, **kwargs):
        self.queries += 1
        return FakeQuery(self.result)


@pytest.fixture
def recorded(monkeypatch):
    """Capture calls to record_user_action instead of writing to the database."""
    calls = []
    monkeypatch.setattr(
        auth, "record_user_action", lambda user, request: calls.append((user, request))
    )
    return calls


class TestGetCurrentUser:
    def test_api_token_header_resolves_user(self, recorded):
        user = FakeUser()
        request = make_request()

        result = auth.get_current_user(
            request=request, api_token="valid", jwt_token=None, db=FakeDB(user)
        )

        assert result is user
        assert recorded == [(user, request)]

    def test_bearer_value_falls_back_to_api_token(self, recorded):
        user = FakeUser()

        result = auth.get_current_user(
            request=make_request(),
            api_token=None,
            jwt_token="an-opaque-api-token",
            db=FakeDB(user),
        )

        assert result is user
        assert len(recorded) == 1

    def test_no_token_raises_401(self, recorded):
        with pytest.raises(HTTPException) as excinfo:
            auth.get_current_user(
                request=make_request(), api_token=None, jwt_token=None, db=FakeDB(None)
            )

        assert excinfo.value.status_code == 401
        assert recorded == []

    def test_unknown_token_raises_401(self, recorded):
        with pytest.raises(HTTPException) as excinfo:
            auth.get_current_user(
                request=make_request(),
                api_token="nope",
                jwt_token=None,
                db=FakeDB(None),
            )

        assert excinfo.value.status_code == 401
        assert recorded == []

    def test_body_token_resolves_user_and_warns(self, recorded):
        user = FakeUser()
        request = make_request(
            method="POST",
            headers={"Content-Type": "application/json"},
            body=b'{"api_token": "valid"}',
        )
        response = Response()

        result = auth.get_current_user(
            request=request, response=response, api_token=None, jwt_token=None, db=FakeDB(user)
        )

        assert result is user
        assert "X-Deprecation-Warning" in response.headers

    def test_header_token_sets_no_deprecation_warning(self, recorded):
        response = Response()

        auth.get_current_user(
            request=make_request(),
            response=response,
            api_token="valid",
            jwt_token=None,
            db=FakeDB(FakeUser()),
        )

        assert "X-Deprecation-Warning" not in response.headers

    def test_non_string_body_token_raises_401_not_a_db_error(self, recorded):
        """A non-string api_token in the body must be rejected before it ever
        reaches a query, not passed through to the DB driver (which chokes on
        binding a list/dict as a scalar parameter)."""
        request = make_request(
            method="POST",
            headers={"Content-Type": "application/json"},
            body=b'{"api_token": [1, 2]}',
        )
        db = FakeDB(None)

        with pytest.raises(HTTPException) as excinfo:
            auth.get_current_user(request=request, api_token=None, jwt_token=None, db=db)

        assert excinfo.value.status_code == 401
        assert db.queries == 0

    def test_missing_response_does_not_crash_body_token_path(self, recorded):
        """get_current_user is called directly (no response) throughout this
        file; the deprecated body-token path must tolerate that too."""
        user = FakeUser()
        request = make_request(
            method="POST",
            headers={"Content-Type": "application/json"},
            body=b'{"api_token": "valid"}',
        )

        result = auth.get_current_user(
            request=request, api_token=None, jwt_token=None, db=FakeDB(user)
        )

        assert result is user
