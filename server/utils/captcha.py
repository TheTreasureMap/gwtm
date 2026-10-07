"""Cloudflare Turnstile server-side verification."""

import logging
from typing import Optional

import httpx
from fastapi import HTTPException, status

from server.config import settings

logger = logging.getLogger(__name__)

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TIMEOUT_SECONDS = 3

# Secret or provider faults return 503 so the visitor can retry.
UNAVAILABLE_CODES = ("missing-input-secret", "invalid-input-secret", "internal-error")


def _unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Captcha service unavailable. Please try again.",
    )


def captcha_enabled() -> bool:
    """
    Both keys are required. A lone site key would show a widget nothing checks,
    and a lone secret would enforce with no widget, blocking every submission.
    """
    return bool(settings.TURNSTILE_SITE_KEY and settings.TURNSTILE_SECRET_KEY)


async def verify_captcha(token: Optional[str]) -> None:
    """
    No-op unless captcha_enabled(). Provider errors fail closed so an induced
    outage cannot bypass the check.
    """
    if not captcha_enabled():
        return

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Captcha verification failed",
        )

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.post(
                VERIFY_URL,
                data={"secret": settings.TURNSTILE_SECRET_KEY, "response": token},
            )
            response.raise_for_status()
            result = response.json()
        if not isinstance(result, dict):
            raise ValueError("unexpected siteverify payload")
    except (httpx.HTTPError, ValueError):
        logger.exception("Turnstile verification unavailable")
        raise _unavailable()

    if result.get("success") is True:
        return

    error_codes = result.get("error-codes")
    if not isinstance(error_codes, list):
        error_codes = []

    if any(code in UNAVAILABLE_CODES for code in error_codes):
        logger.error("Turnstile verification unavailable: %s", error_codes)
        raise _unavailable()

    logger.info("Turnstile rejected token: %s", error_codes)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Captcha verification failed",
    )
