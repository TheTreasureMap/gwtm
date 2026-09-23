"""Signed email-link token generation and decoding."""

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

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


RESET_TOKEN_EXPIRE_HOURS = 1
# User-facing wording of the expiry, for the email and the API response.
RESET_TOKEN_EXPIRY_TEXT = (
    f"{RESET_TOKEN_EXPIRE_HOURS} hour{'' if RESET_TOKEN_EXPIRE_HOURS == 1 else 's'}"
)
_RESET_PURPOSE = "reset"


def _password_fingerprint(password_hash: str) -> str:
    """Short keyed digest of the stored hash.

    Embedding it in a reset token makes the token single use: once the password
    changes, the fingerprint no longer matches and every outstanding link dies.
    """
    return hmac.new(
        settings.JWT_SECRET_KEY.encode(), (password_hash or "").encode(), hashlib.sha256
    ).hexdigest()[:16]


def generate_reset_token(user_id: int, password_hash: str) -> str:
    """Return a signed JWT for a password reset link, valid for one hour."""
    payload = {
        "uid": user_id,
        "purpose": _RESET_PURPOSE,
        "pwf": _password_fingerprint(password_hash),
        "exp": datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_reset_token(token: str) -> tuple[int, str]:
    """Decode a reset token and return (user_id, password fingerprint).

    Verification tokens carry no purpose claim, so they are rejected here.

    Raises:
        ExpiredSignatureError: token is past its expiry.
        InvalidTokenError: malformed, bad signature, or not a reset token.
    """
    payload = jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    if payload.get("purpose") != _RESET_PURPOSE or not isinstance(payload.get("pwf"), str):
        raise InvalidTokenError("not a password reset token")
    try:
        return int(payload["uid"]), payload["pwf"]
    except (ValueError, TypeError, KeyError) as exc:
        raise InvalidTokenError("uid claim is missing or not a valid integer") from exc


def reset_token_matches(fingerprint: str, password_hash: str) -> bool:
    return hmac.compare_digest(fingerprint, _password_fingerprint(password_hash))
