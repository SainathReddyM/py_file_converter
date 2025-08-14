from pydantic import BaseModel
from typing import TypeVar, Generic, Optional

T = TypeVar('T')

class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response model."""
    status: str = "success"
    data: Optional[T] = None

class ErrorResponse(BaseModel):
    """Standard error response model."""
    status: str = "error"
    message: str
    details: Optional[str] = None
