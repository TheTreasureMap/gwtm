"""Test endpoint for refactored pointing routes."""

from fastapi import APIRouter

router = APIRouter(tags=["pointings"])


@router.get("/test_refactoring")
async def test_refactoring():
    """Test endpoint to verify refactored code is active."""
    return {"message": "Refactored pointing routes are active"}