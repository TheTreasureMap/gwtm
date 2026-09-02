"""Signed verification token generation and decoding."""

from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError  # noqa: F401 — re-exported for callers

from server.config import settings

EMAIL_TOKEN_EXPIRE_HOURS = 24
_VERIFICATION_KEY_MAX_LEN = 128


def generate_verification_token(user_id: int) -> str:
    """Return a signed JWT that expires in 24 hours, encoding the user's ID.

    Uses JWT_SECRET_KEY so tokens survive pod restarts and rolling deploys.
    Raises RuntimeError if the generated token exceeds the verification_key
    column limit, so failures are loud rather than silently truncated by the DB.
    """
    payload = {
        "uid": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=EMAIL_TOKEN_EXPIRE_HOURS),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    if len(token) > _VERIFICATION_KEY_MAX_LEN:
        raise RuntimeError(
            f"Generated verification JWT ({len(token)} chars) exceeds the "
            f"verification_key column limit of {_VERIFICATION_KEY_MAX_LEN} chars"
        )
    return token


def decode_verification_token(token: str) -> int:
    """Decode a verification token and return the user ID.

    Raises:
        ExpiredSignatureError: token is structurally valid but past its expiry.
        InvalidTokenError: token is malformed, has an invalid signature, or
            contains a non-integer uid claim.
    """
    payload = jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    try:
        return int(payload["uid"])
    except (ValueError, TypeError, KeyError) as exc:
        raise InvalidTokenError("uid claim is missing or not a valid integer") from exc
