"""Unit tests for token resolution in get_current_user."""

import pytest
from fastapi import HTTPException

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
