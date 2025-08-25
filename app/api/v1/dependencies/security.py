# app/api/v1/dependencies/security.py (Improved Version)

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import API_KEYS_LIST

# Set auto_error=True to let FastAPI handle the missing header error automatically
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    """
    Dependency function to validate the API key.
    Relies on auto_error=True to handle missing key.
    Checks if the provided key is in the valid list.
    """
    # We no longer need to check `if not api_key`, as FastAPI does it for us now.
    if api_key not in API_KEYS_LIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key."
        )
    return api_key