"""Unit tests for token resolution in get_current_user."""

import asyncio
import json

import pytest
from fastapi import HTTPException

from server.auth import auth
from server.utils.audit import MAX_BODY_BYTES
from tests.unit.test_audit import FakeUser, make_request


class FakeQuery:
    """Returns whatever the fake session was primed with, recording filters."""

    def __init__(self, result, filters):
        self.result = result
        self.filters = filters

    def filter(self, *args, **kwargs):
        self.filters.extend(args)
        return self

    def first(self):
        return self.result


class FakeDB:
    def __init__(self, result):
        self.result = result
        self.queries = 0
        self.filters = []

    def query(self, *args, **kwargs):
        self.queries += 1
        return FakeQuery(self.result, self.filters)


@pytest.fixture
def recorded(monkeypatch):
    """Capture calls to record_user_action instead of writing to the database."""
    calls = []
    monkeypatch.setattr(
        auth, "record_user_action", lambda user, request: calls.append((user, request))
    )
    return calls


def json_request(body, content_length=None, **kwargs):
    headers = {"Content-Type": "application/json"}
    if content_length is not None:
        headers["Content-Length"] = str(content_length)
    return make_request(method="POST", headers=headers, body=body, **kwargs)


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

    def test_body_token_resolves_user_and_flags_deprecation(self, recorded, caplog):
        user = FakeUser()
        request = json_request(b'{"api_token": "valid"}')
        db = FakeDB(user)

        result = auth.get_current_user(
            request=request, api_token=None, jwt_token=None, db=db
        )

        assert result is user
        assert db.filters[0].right.value == "valid"
        assert request.state.deprecated_body_token is True
        assert "Deprecated api_token-in-body" in caplog.text

    def test_unknown_body_token_raises_401_without_flag(self, recorded):
        request = json_request(b'{"api_token": "nope"}')

        with pytest.raises(HTTPException) as excinfo:
            auth.get_current_user(
                request=request, api_token=None, jwt_token=None, db=FakeDB(None)
            )

        assert excinfo.value.status_code == 401
        assert not hasattr(request.state, "deprecated_body_token")

    def test_body_token_beyond_audit_size_cap_still_authenticates(self, recorded):
        user = FakeUser()
        body = json.dumps({"api_token": "valid", "pad": "x" * MAX_BODY_BYTES}).encode()

        result = auth.get_current_user(
            request=json_request(body), api_token=None, jwt_token=None, db=FakeDB(user)
        )

        assert result is user

    def test_body_over_auth_cap_is_not_inspected(self, recorded):
        body = json.dumps(
            {"api_token": "valid", "pad": "x" * auth.MAX_BODY_TOKEN_BYTES}
        ).encode()
        db = FakeDB(FakeUser())

        with pytest.raises(HTTPException) as excinfo:
            auth.get_current_user(
                request=json_request(body), api_token=None, jwt_token=None, db=db
            )

        assert excinfo.value.status_code == 401
        assert db.queries == 0

    @pytest.mark.parametrize(
        "token", [[1, 2], {"a": 1}, 12345, "", "\x00", "a\x00b", "\ud800", "tökén"]
    )
    def test_invalid_body_token_raises_401_before_reaching_the_db(self, recorded, token):
        """The DB driver raises on these (a 500), so they must never be queried."""
        body = json.dumps({"api_token": token}).encode()
        db = FakeDB(FakeUser())

        with pytest.raises(HTTPException) as excinfo:
            auth.get_current_user(
                request=json_request(body), api_token=None, jwt_token=None, db=db
            )

        assert excinfo.value.status_code == 401
        assert db.queries == 0


class TestBufferBodyForTokenFallback:
    def test_body_buffered_by_the_dependency_is_seen_by_get_current_user(self, recorded):
        user = FakeUser()
        body = b'{"api_token": "valid"}'
        request = json_request(body, content_length=len(body), pre_buffered=False)

        asyncio.run(auth.buffer_body_for_token_fallback(request))
        result = auth.get_current_user(
            request=request, api_token=None, jwt_token=None, db=FakeDB(user)
        )

        assert result is user

    def test_body_over_cap_is_not_read(self):
        request = json_request(
            b'{"api_token": "valid"}',
            content_length=auth.MAX_BODY_TOKEN_BYTES + 1,
            pre_buffered=False,
        )

        asyncio.run(auth.buffer_body_for_token_fallback(request))

        assert not hasattr(request, "_body")
