"""Unit tests for audit recording."""

import json

import pytest
from starlette.requests import Request

from server.utils import audit


def make_request(
    method="GET",
    path="/api/v1/pointings",
    query=b"",
    headers=None,
    client=("10.0.0.9", 51234),
    body=None,
):
    """Build a Starlette Request without going through the server."""
    raw_headers = [
        (key.lower().encode(), value.encode()) for key, value in (headers or {}).items()
    ]
    request = Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "query_string": query,
            "headers": raw_headers,
            "client": client,
            "scheme": "https",
            "server": ("treasuremap.space", 443),
        }
    )
    if body is not None:
        # FastAPI buffers the body onto the request before dependencies run.
        request._body = body
    return request


class TestClientIP:
    def test_prefers_first_forwarded_hop(self):
        request = make_request(headers={"X-Forwarded-For": "203.0.113.5, 10.0.0.1"})
        assert audit.client_ip(request) == "203.0.113.5"

    def test_falls_back_to_peer_address(self):
        assert audit.client_ip(make_request()) == "10.0.0.9"

    def test_truncates_to_column_width(self):
        request = make_request(headers={"X-Forwarded-For": "x" * 80})
        assert len(audit.client_ip(request)) == audit.IPADDRESS_MAX

    def test_none_without_client(self):
        assert audit.client_ip(make_request(client=None)) is None


class TestRequestBodyJSON:
    def test_reads_buffered_json_object(self):
        request = make_request(
            method="POST",
            headers={"Content-Type": "application/json"},
            body=b'{"graceid": "S190425z"}',
        )
        assert audit.request_body_json(request) == {"graceid": "S190425z"}

    def test_reads_json_array(self):
        request = make_request(
            method="POST",
            headers={"Content-Type": "application/json"},
            body=b"[1, 2]",
        )
        assert audit.request_body_json(request) == [1, 2]

    def test_none_when_no_body(self):
        assert audit.request_body_json(make_request()) is None

    def test_none_for_form_encoded(self):
        request = make_request(
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body=b"username=a&password=b",
        )
        assert audit.request_body_json(request) is None

    def test_none_for_oversized_body(self):
        oversized = json.dumps({"blob": "x" * audit.MAX_BODY_BYTES}).encode()
        request = make_request(
            method="POST",
            headers={"Content-Type": "application/json"},
            body=oversized,
        )
        assert audit.request_body_json(request) is None

    def test_none_for_malformed_json(self):
        request = make_request(
            method="POST",
            headers={"Content-Type": "application/json"},
            body=b"{not json",
        )
        assert audit.request_body_json(request) is None

    def test_none_for_scalar_json(self):
        request = make_request(
            method="POST",
            headers={"Content-Type": "application/json"},
            body=b'"just a string"',
        )
        assert audit.request_body_json(request) is None


class FakeSession:
    def __init__(self, fail_on_commit=False):
        self.added = []
        self.committed = False
        self.fail_on_commit = fail_on_commit

    def add(self, row):
        self.added.append(row)

    def commit(self):
        if self.fail_on_commit:
            raise RuntimeError("database is down")
        self.committed = True


@pytest.fixture
def captured_session(monkeypatch):
    """Swap the audit module's session factory for an in-memory double."""
    from contextlib import contextmanager

    session = FakeSession()

    @contextmanager
    def fake_db_session():
        yield session

    monkeypatch.setattr(audit, "db_session", fake_db_session)
    return session


class FakeUser:
    id = 370
    username = "kwynn"


class TestRecordUserAction:
    def test_writes_expected_row(self, captured_session):
        request = make_request(
            method="POST",
            path="/api/v1/pointings",
            headers={
                "Content-Type": "application/json",
                "X-Forwarded-For": "203.0.113.5",
            },
            body=b'{"graceid": "S190425z"}',
        )

        audit.record_user_action(FakeUser(), request)

        assert captured_session.committed
        (row,) = captured_session.added
        assert row.userid == 370
        assert row.ipaddress == "203.0.113.5"
        assert row.url == "https://treasuremap.space/api/v1/pointings"
        assert row.method == "POST"
        assert row.jsonvals == {"graceid": "S190425z"}
        assert row.time is not None

    def test_records_query_string_in_url(self, captured_session):
        request = make_request(query=b"graceid=S190425z&status=completed")
        audit.record_user_action(FakeUser(), request)
        (row,) = captured_session.added
        assert row.url.endswith("?graceid=S190425z&status=completed")

    def test_write_failure_does_not_propagate(self, monkeypatch, caplog):
        from contextlib import contextmanager

        @contextmanager
        def failing_db_session():
            yield FakeSession(fail_on_commit=True)

        monkeypatch.setattr(audit, "db_session", failing_db_session)

        audit.record_user_action(FakeUser(), make_request())

        assert "Failed to record user action" in caplog.text
