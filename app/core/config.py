#This file will use Pydantic to load, validate, and provide settings to the rest of the application.

from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    APP_TITLE: str = "File Converter API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    TEMP_FILE_DIR: str = "temp_files"

    class Config:
        env_file = ".env"

settings = Settings()

# Ensure the temporary directory exists
os.makedirs(settings.TEMP_FILE_DIR, exist_ok=True)

