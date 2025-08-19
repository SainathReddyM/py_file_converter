#This file will use Pydantic to load, validate, and provide settings to the rest of the application.
from pydantic.v1 import validator
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    APP_TITLE: str = "File Converter API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    TEMP_FILE_DIR: str = "temp_files"

    # --- THIS IS THE LINE YOU ARE LIKELY MISSING ---
    LIBREOFFICE_PATH: str

    @validator("LIBREOFFICE_PATH")
    def validate_libreoffice_path(cls, v):
        if not os.path.exists(v):
            raise ValueError(f"LibreOffice path does not exist: {v}. Please check your .env file.")
        return v

    class Config:
        env_file = ".env"

settings = Settings()

# Ensure the temporary directory exists
os.makedirs(settings.TEMP_FILE_DIR, exist_ok=True)

