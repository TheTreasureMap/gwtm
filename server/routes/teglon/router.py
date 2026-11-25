"""Fetch suggested pointings and coverage-adjusted contours from the Teglon API for the browser.

The browser calls these routes rather than Teglon itself, so Teglon's bearer token stays on the
server and gwtm can check login and resolve event names before asking Teglon.

The whole feature is switched by TEGLON_API_URL. When it is empty only `status_router` is
registered, which tells the frontend to hide every Teglon control; the proxy routes do not exist.
Teglon's status codes and JSON bodies are passed through unchanged, since the frontend acts on
Teglon's own messages and run fields (for example a 404 carrying a setup run's task_id).
"""

import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from server.auth.auth import get_current_user
from server.config import settings
from server.core.enums.instrumenttype import InstrumentType
from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.db.models.instrument import Instrument

status_router = APIRouter(prefix="/teglon", tags=["teglon"])
router = APIRouter(
    prefix="/teglon", tags=["teglon"], dependencies=[Depends(get_current_user)]
)

TASK_ID = re.compile(r"^[A-Za-z0-9-]{1,64}$")

# The browser gives up after 30 s, so a slow Teglon must fail before that. Teglon does its
# heavy work in background runs, so its routes normally answer in well under a second.
TIMEOUT = httpx.Timeout(20.0, connect=5.0)


def teglon_enabled() -> bool:
    return bool(settings.TEGLON_API_URL)


@status_router.get("/status")
def status():
    return {"enabled": teglon_enabled()}


def resolve_graceid(db: Session, graceid: str) -> str:
    """The event's graceid, accepting an alternate id (GW190425 -> S190425z)."""
    alert = db.query(GWAlert).filter(GWAlert.graceid == graceid).first()
    if not alert:
        alert = db.query(GWAlert).filter(GWAlert.alternateid == graceid).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert.graceid


def check_instrument(db: Session, instrument_id: int) -> None:
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    if instrument.instrument_type != InstrumentType.photometric:
        raise HTTPException(
            status_code=400,
            detail="Teglon only suggests pointings for photometric instruments",
        )


def forward(method: str, path: str, params: dict) -> JSONResponse:
    try:
        resp = httpx.request(
            method,
            settings.TEGLON_API_URL.rstrip("/") + path,
            params=params,
            headers={"Authorization": "Bearer " + settings.TEGLON_API_TOKEN},
            timeout=TIMEOUT,
        )
    except httpx.TimeoutException:
        return JSONResponse(
            {"message": "Teglon did not respond in time"}, status_code=504
        )
    except httpx.HTTPError:
        return JSONResponse({"message": "Teglon is unavailable"}, status_code=502)
    try:
        body = resp.json()
    except ValueError:
        return JSONResponse(
            {"message": "Teglon returned an unexpected response"}, status_code=502
        )
    return JSONResponse(body, status_code=resp.status_code)


@router.get("/suggested_pointings")
def suggested_pointings(
    graceid: str,
    instrument_id: int,
    exclude_planned: bool = False,
    db: Session = Depends(get_db),
):
    graceid = resolve_graceid(db, graceid)
    check_instrument(db, instrument_id)
    return forward(
        "GET",
        "/suggested_pointings",
        {
            "graceid": graceid,
            "instrument_id": instrument_id,
            "exclude_planned": str(exclude_planned).lower(),
        },
    )


@router.post("/planned_runs")
def start_planned_run(graceid: str, instrument_id: int, db: Session = Depends(get_db)):
    graceid = resolve_graceid(db, graceid)
    check_instrument(db, instrument_id)
    return forward(
        "POST", "/planned_runs", {"graceid": graceid, "instrument_id": instrument_id}
    )


@router.get("/planned_runs/{task_id}")
def planned_run_status(task_id: str):
    if not TASK_ID.match(task_id):
        raise HTTPException(status_code=400, detail="Invalid task id")
    return forward("GET", "/planned_runs/" + task_id, {})


@router.get("/contours")
def contours(
    graceid: str,
    include_planned: bool = Query(False),
    db: Session = Depends(get_db),
):
    graceid = resolve_graceid(db, graceid)
    return forward(
        "GET",
        "/contours",
        {"graceid": graceid, "include_planned": str(include_planned).lower()},
    )
