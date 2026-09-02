"""Consolidated router for all DOI endpoints."""

from fastapi import APIRouter

# Import all individual route modules
from .get_doi_pointings import router as get_doi_pointings_router
from .get_author_groups import router as get_author_groups_router
from .get_authors import router as get_authors_router
from .save_author_group import router as save_author_group_router
from .delete_author_group import router as delete_author_group_router

# Create the main router that includes all DOI routes
router = APIRouter(tags=["DOI"])

# Include all the individual routers
router.include_router(get_doi_pointings_router)
router.include_router(get_author_groups_router)
router.include_router(get_authors_router)
router.include_router(save_author_group_router)
router.include_router(delete_author_group_router)
