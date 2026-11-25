"""The Teglon proxy: switched off by an empty TEGLON_API_URL, and a pass-through when on."""

from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from server.auth.auth import get_current_user
from server.config import settings
from server.core.enums.instrumenttype import InstrumentType
from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.db.models.instrument import Instrument
from server.routes.teglon import router as teglon

ALERT = SimpleNamespace(graceid="S190425z", alternateid="GW190425")
PHOTOMETRIC = SimpleNamespace(id=47, instrument_type=InstrumentType.photometric)
SPECTROSCOPIC = SimpleNamespace(id=48, instrument_type=InstrumentType.spectroscopic)


class FakeQuery:
    """Supports query(Model).filter(Model.column == value).first()."""

    def __init__(self, rows):
        self.rows = rows

    def filter(self, condition):
        column, value = condition.left.key, condition.right.value
        return FakeQuery([r for r in self.rows if getattr(r, column, None) == value])

    def first(self):
        return self.rows[0] if self.rows else None


class FakeDB:
    tables = {GWAlert: [ALERT], Instrument: [PHOTOMETRIC, SPECTROSCOPIC]}

    def query(self, model):
        return FakeQuery(self.tables[model])


class FakeTeglon:
    """Stands in for httpx.request and records what would have been sent to Teglon."""

    def __init__(self):
        self.calls = []
        self.response = httpx.Response(200, json={"pointings": []})

    def __call__(self, method, url, params=None, headers=None, timeout=None):
        self.calls.append(
            SimpleNamespace(method=method, url=url, params=params, headers=headers)
        )
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@pytest.fixture
def fake_teglon(monkeypatch):
    fake = FakeTeglon()
    monkeypatch.setattr(teglon.httpx, "request", fake)
    monkeypatch.setattr(settings, "TEGLON_API_URL", "https://teglon.example/")
    monkeypatch.setattr(settings, "TEGLON_API_TOKEN", "tok")
    return fake


def app_with_teglon(logged_in=True):
    app = FastAPI()
    app.include_router(teglon.status_router, prefix="/api/v1")
    app.include_router(teglon.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = FakeDB

    def user():
        if not logged_in:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return SimpleNamespace(id=1)

    app.dependency_overrides[get_current_user] = user
    return TestClient(app)


# --- switched off ----------------------------------------------------------------------------


def test_off_by_default_hides_the_feature():
    from server.main import app

    assert settings.TEGLON_API_URL == ""
    client = TestClient(app)
    assert client.get("/api/v1/teglon/status").json() == {"enabled": False}
    paths = {route.path for route in app.routes}
    assert "/api/v1/teglon/suggested_pointings" not in paths
    assert "/api/v1/teglon/contours" not in paths


# --- switched on -----------------------------------------------------------------------------


def test_status_reports_enabled(fake_teglon):
    assert app_with_teglon().get("/api/v1/teglon/status").json() == {"enabled": True}


def test_passes_teglon_status_and_body_through(fake_teglon):
    body = {"message": "Teglon is setting up this instrument", "task_id": "abc-1"}
    fake_teglon.response = httpx.Response(404, json=body)
    resp = app_with_teglon().get(
        "/api/v1/teglon/suggested_pointings",
        params={"graceid": "GW190425", "instrument_id": 47, "exclude_planned": "true"},
    )
    assert (resp.status_code, resp.json()) == (404, body)
    call = fake_teglon.calls[0]
    assert call.url == "https://teglon.example/suggested_pointings"
    assert call.params == {
        "graceid": "S190425z",
        "instrument_id": 47,
        "exclude_planned": "true",
    }
    assert call.headers == {"Authorization": "Bearer tok"}


def test_planned_run_is_posted(fake_teglon):
    fake_teglon.response = httpx.Response(
        202, json={"task_id": "t-1", "state": "PENDING"}
    )
    resp = app_with_teglon().post(
        "/api/v1/teglon/planned_runs",
        params={"graceid": "S190425z", "instrument_id": 47},
    )
    assert resp.status_code == 202
    assert fake_teglon.calls[0].method == "POST"


@pytest.mark.parametrize(
    "path, params, status",
    [
        (
            "/api/v1/teglon/suggested_pointings",
            {"graceid": "S000000x", "instrument_id": 47},
            404,
        ),
        (
            "/api/v1/teglon/suggested_pointings",
            {"graceid": "S190425z", "instrument_id": 999},
            404,
        ),
        (
            "/api/v1/teglon/suggested_pointings",
            {"graceid": "S190425z", "instrument_id": 48},
            400,
        ),
        ("/api/v1/teglon/planned_runs/bad id!", {}, 400),
    ],
)
def test_bad_requests_never_reach_teglon(fake_teglon, path, params, status):
    assert app_with_teglon().get(path, params=params).status_code == status
    assert fake_teglon.calls == []


def test_requires_login(fake_teglon):
    resp = app_with_teglon(logged_in=False).get(
        "/api/v1/teglon/contours", params={"graceid": "S190425z"}
    )
    assert resp.status_code == 401
    assert fake_teglon.calls == []


@pytest.mark.parametrize("upstream", [401, 403])
def test_teglon_auth_failure_is_not_a_401(fake_teglon, upstream):
    fake_teglon.response = httpx.Response(upstream, json={"message": "Unauthorized"})
    resp = app_with_teglon().get(
        "/api/v1/teglon/contours", params={"graceid": "S190425z"}
    )
    assert resp.status_code == 502
    assert resp.json() == {"message": "Teglon rejected gwtm's service token"}


@pytest.mark.parametrize(
    "failure, status",
    [
        (httpx.ConnectError("refused"), 502),
        (httpx.ReadTimeout("slow"), 504),
        (httpx.Response(502, text="<html>Bad Gateway</html>"), 502),
    ],
)
def test_teglon_failures_become_json(fake_teglon, failure, status):
    fake_teglon.response = failure
    resp = app_with_teglon().get(
        "/api/v1/teglon/contours", params={"graceid": "S190425z"}
    )
    assert resp.status_code == status
    assert "message" in resp.json()
