
class AppException(Exception):
    """Base application exception."""
    def __init__(self, status_code: int, message: str, details: str = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(message)

class ConversionError(AppException):
     """Custom exception for file conversion failures."""
     def __init__(self, details: str):
        super().__init__(
            status_code=422,  # 422 Unprocessable Entity
            message="File conversion failed.",
            details=details
        )
    
class FileValidationError(AppException):
    """Custom exception for file validation failures."""
    def __init__(self, details: str):
        super().__init__(
            status_code=400, # 400 Bad Request
            message="Invalid file provided.",
            details=details
        )