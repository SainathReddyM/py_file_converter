from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.api.v1.routers.conversion import router as v1_conversion_router
from app.api.v1.schemas.response_schema import ErrorResponse
from app.core.config import settings
from app.utils.custom_exceptions import AppException

# Initialize the FastAPI app with settings from config
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
)

# --- Global Exception Handlers ---
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handles custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.message,
            details=exc.details
        ).model_dump()
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handles unexpected exceptions."""
    # In a production environment, you would log the exception details.
    # For security, do not return the internal exception message to the client.
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            message="An unexpected internal server error occurred.",
            details="Please contact support."
        ).model_dump()
    )

# --- Include API Routers ---
# This includes all endpoints from the conversion router under /api/v1
app.include_router(
    v1_conversion_router,
    prefix=f"{settings.API_PREFIX}/v1/conversion",
    tags=["V1 - Conversion"]
)

# --- Root Endpoint for Health Check ---
@app.get("/", tags=["Health Check"])
def read_root():
    """A simple health check endpoint."""
    return {"status": "ok", "message": f"Welcome to {settings.APP_TITLE} v{settings.APP_VERSION}"}