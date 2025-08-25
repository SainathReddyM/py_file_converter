# app/core/config.py (Final Version)

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    APP_TITLE: str = "File Converter API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    TEMP_FILE_DIR: str = "temp_files"
    LIBREOFFICE_PATH: str

    # We will now read the API keys as a single, simple string.
    VALID_API_KEYS_STR: str

    class Config:
        env_file = ".env"


# --- MANUAL PARSING ---
# Load the settings from the environment
try:
    settings = Settings()

    # Manually parse the comma-separated string into a list of strings.
    # This is explicit and avoids any Pydantic parsing quirks.
    API_KEYS_LIST: List[str] = [
        key.strip() for key in settings.VALID_API_KEYS_STR.split(',') if key.strip()
    ]

    # Validate the LibreOffice path
    if not os.path.exists(settings.LIBREOFFICE_PATH):
        raise ValueError(f"LibreOffice path does not exist: {settings.LIBREOFFICE_PATH}")

    # Ensure the temporary directory exists
    os.makedirs(settings.TEMP_FILE_DIR, exist_ok=True)

except Exception as e:
    print(f"FATAL: Could not load application settings. Error: {e}")
    exit(1)