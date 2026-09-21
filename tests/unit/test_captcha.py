"""Unit tests for Turnstile verification. The Cloudflare call is faked."""

import asyncio

import httpx
import pytest
from fastapi import HTTPException

from server.utils import captcha

REQUEST = httpx.Request("POST", captcha.VERIFY_URL)


def make_client(response=None, error=None, posts=None):
    """Build a stand-in for httpx.AsyncClient that returns `response` or raises `error`."""

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, data):
            if posts is not None:
                posts.append((url, data))
            if error:
                raise error
            return response

    return FakeAsyncClient


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setattr(captcha.settings, "TURNSTILE_SECRET_KEY", "test-secret")


def verify(token):
    return asyncio.run(captcha.verify_captcha(token))


def test_skips_when_secret_unset(monkeypatch):
    monkeypatch.setattr(captcha.settings, "TURNSTILE_SECRET_KEY", "")
    monkeypatch.setattr(captcha.httpx, "AsyncClient", make_client(error=AssertionError))
    assert verify(None) is None


@pytest.mark.parametrize("token", [None, ""])
def test_missing_token_is_rejected(secret, token):
    with pytest.raises(HTTPException) as exc:
        verify(token)
    assert exc.value.status_code == 400


def test_rejected_token_is_400(secret, monkeypatch):
    response = httpx.Response(
        200,
        json={"success": False, "error-codes": ["invalid-input-response"]},
        request=REQUEST,
    )
    monkeypatch.setattr(captcha.httpx, "AsyncClient", make_client(response))
    with pytest.raises(HTTPException) as exc:
        verify("bad-token")
    assert exc.value.status_code == 400


def test_accepted_token_posts_secret_and_token(secret, monkeypatch):
    posts = []
    response = httpx.Response(200, json={"success": True}, request=REQUEST)
    monkeypatch.setattr(
        captcha.httpx, "AsyncClient", make_client(response, posts=posts)
    )
    assert verify("good-token") is None
    assert posts == [
        (captcha.VERIFY_URL, {"secret": "test-secret", "response": "good-token"})
    ]


@pytest.mark.parametrize(
    "client",
    [
        make_client(error=httpx.ConnectTimeout("timeout")),
        make_client(httpx.Response(502, request=REQUEST)),
        make_client(httpx.Response(200, content=b"<html>", request=REQUEST)),
        make_client(httpx.Response(200, content=b"[1]", request=REQUEST)),
        make_client(httpx.Response(200, content=b"null", request=REQUEST)),
    ],
    ids=["timeout", "5xx", "non-json", "json-list", "json-null"],
)
def test_provider_failure_fails_closed_with_503(secret, monkeypatch, client):
    monkeypatch.setattr(captcha.httpx, "AsyncClient", client)
    with pytest.raises(HTTPException) as exc:
        verify("any-token")
    assert exc.value.status_code == 503


@pytest.mark.parametrize("code", ["invalid-input-secret", "internal-error"])
def test_secret_or_provider_error_codes_are_503_not_400(secret, monkeypatch, code):
    response = httpx.Response(
        200, json={"success": False, "error-codes": [code]}, request=REQUEST
    )
    monkeypatch.setattr(captcha.httpx, "AsyncClient", make_client(response))
    with pytest.raises(HTTPException) as exc:
        verify("any-token")
    assert exc.value.status_code == 503


def test_malformed_error_codes_are_treated_as_a_rejection(secret, monkeypatch):
    response = httpx.Response(
        200, json={"success": False, "error-codes": {"a": 1}}, request=REQUEST
    )
    monkeypatch.setattr(captcha.httpx, "AsyncClient", make_client(response))
    with pytest.raises(HTTPException) as exc:
        verify("any-token")
    assert exc.value.status_code == 400
