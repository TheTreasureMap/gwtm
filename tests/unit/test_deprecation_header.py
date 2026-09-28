"""Unit tests for the deprecation-warning middleware."""

from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from server.auth.auth import BODY_TOKEN_DEPRECATION_WARNING
from server.main import deprecation_warning_header


def make_client():
    app = FastAPI()
    app.middleware("http")(deprecation_warning_header)

    @app.get("/flagged")
    def flagged(request: Request):
        request.state.deprecated_body_token = True
        return Response("a Response returned directly")

    @app.get("/plain")
    def plain():
        return Response("ok")

    return TestClient(app)


def test_header_added_when_flagged():
    response = make_client().get("/flagged")
    assert response.headers["X-Deprecation-Warning"] == BODY_TOKEN_DEPRECATION_WARNING


def test_no_header_when_not_flagged():
    assert "X-Deprecation-Warning" not in make_client().get("/plain").headers
