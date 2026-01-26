"""
API Router Module

This module sets up the API router and includes all defined endpoints.
It uses FastAPI's APIRouter to group related endpoints and provide a prefix.
"""

from fastapi import APIRouter, Depends

from app.api import endpoint
from app.api.auth import verify_api_key

router = APIRouter()

router.include_router(
    endpoint.router,
    prefix="/jobs",
    dependencies=[Depends(verify_api_key)],
)
