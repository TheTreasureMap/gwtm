"""Signed verification token generation and decoding."""

from datetime import datetime, timedelta, timezone

import jwt

from server.config import settings

EMAIL_TOKEN_EXPIRE_HOURS = 24


def generate_verification_token(user_id: int) -> str:
    """Return a signed JWT that expires in 24 hours, encoding the user's ID."""
    payload = {
        "uid": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=EMAIL_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_verification_token(token: str) -> int:
    """Decode a verification token and return the user ID.

    Raises:
        ExpiredSignatureError: token is structurally valid but past its expiry.
        InvalidTokenError: token is malformed or has an invalid signature.
    """
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    return int(payload["uid"])
