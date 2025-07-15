"""Celestial calculations router."""

from fastapi import APIRouter
from .sun_moon import router as sun_moon_router

router = APIRouter()

# Include all celestial calculation routes
router.include_router(sun_moon_router)