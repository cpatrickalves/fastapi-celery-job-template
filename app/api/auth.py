"""
API Key Authentication Module

This module provides header-based API key authentication for FastAPI endpoints
using the X-API-Key header scheme.
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.settings import settings

# Initialize the API key header scheme
api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="API Key Authentication",
    description="Enter your API key in the X-API-Key header",
    auto_error=True,
)


def get_api_keys() -> set[str]:
    """Load valid API keys from settings.

    Returns:
        Set of valid API keys configured in the environment.
    """
    if settings.API_KEYS:
        return {k.strip() for k in settings.API_KEYS.split(",") if k.strip()}
    return set()


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Dependency that validates the API key from X-API-Key header.

    Args:
        api_key: The API key extracted from the X-API-Key header.

    Returns:
        The validated API key.

    Raises:
        HTTPException: 401 if the API key is invalid.
        HTTPException: 500 if API key authentication is not configured.
    """
    valid_keys = get_api_keys()

    if not valid_keys:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key authentication not configured",
        )

    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return api_key
