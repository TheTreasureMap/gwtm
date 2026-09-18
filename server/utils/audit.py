"""Audit logging for privileged actions and authenticated requests."""

import json
import logging
from datetime import datetime

from server.db.database import db_session
from server.db.models.users import UserActions

logger = logging.getLogger("gwtm.audit")

# public.useractions column widths.
IPADDRESS_MAX = 50
METHOD_MAX = 24

# Bodies larger than this are not recorded.
MAX_BODY_BYTES = 16384


def log_admin_action(
    user, action: str, target: str, *, admin_override: bool, **details
):
    """Record a privileged action against a resource.

    admin_override marks an action taken on a record the user does not own,
    which only admins are permitted to do.

    Values are repr'd so that names containing spaces stay parseable as
    key=value pairs.
    """
    fields = {
        "action": action,
        "target": target,
        "userid": user.id,
        "username": getattr(user, "username", None),
        "admin_override": admin_override,
        **details,
    }
    logger.info(" ".join(f"{key}={value!r}" for key, value in fields.items()))


def client_ip(request):
    """Client address, preferring the first hop in X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:IPADDRESS_MAX]
    if request.client:
        return request.client.host[:IPADDRESS_MAX]
    return None


def request_body_json(request):
    """The request's JSON body as a dict or list, or None.

    Reads the body FastAPI has already buffered onto the request. A sync
    dependency cannot await the stream itself, and re-reading it would
    consume it before the endpoint sees it.
    """
    body = getattr(request, "_body", None)
    if not body or len(body) > MAX_BODY_BYTES:
        return None
    if "application/json" not in request.headers.get("content-type", ""):
        return None
    try:
        value = json.loads(body)
    except ValueError:
        return None
    return value if isinstance(value, (dict, list)) else None


def _redact_credentials(body):
    """Mask api_token in a request body before it's persisted.

    The deprecated api_token-in-body auth fallback means a real credential
    can legitimately be part of an authenticated request's own body, don't
    write it to the audit trail in plaintext.
    """
    if isinstance(body, dict) and "api_token" in body:
        return {**body, "api_token": "[redacted]"}
    return body


def record_user_action(user, request):
    """Write a public.useractions row for an authenticated request.

    Uses its own session so a failed write cannot leave the request's own
    transaction unusable, and swallows every error: failing to record an
    action must never fail the action itself.
    """
    try:
        with db_session() as session:
            session.add(
                UserActions(
                    userid=user.id,
                    ipaddress=client_ip(request),
                    url=str(request.url),
                    time=datetime.now(),
                    jsonvals=_redact_credentials(request_body_json(request)),
                    method=request.method[:METHOD_MAX],
                )
            )
            session.commit()
    except Exception:
        logger.warning("Failed to record user action", exc_info=True)
