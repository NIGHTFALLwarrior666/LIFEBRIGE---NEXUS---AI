"""Configuration module for LifeBridge AI."""

import os
from typing import Set

class Settings:
    """Application settings read strictly from environment variables."""

    # Google Gemini Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    
    # Server / Cloud Run Configuration
    # Cloud Run injects PORT and requires listening on 0.0.0.0
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))

    # Security & Input Validation Limits
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB maximum
    MAX_TEXT_LENGTH: int = 10000  # 10,000 characters limit for prompt text

    ALLOWED_IMAGE_TYPES: Set[str] = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    ALLOWED_AUDIO_TYPES: Set[str] = {
        "audio/wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/mp4",
        "audio/ogg",
        "audio/webm",
        "audio/x-m4a",
        "audio/m4a",
    }

    @property
    def ALLOWED_MIME_TYPES(self) -> Set[str]:
        return self.ALLOWED_IMAGE_TYPES | self.ALLOWED_AUDIO_TYPES

    @property
    def has_gemini_key(self) -> bool:
        return bool(self.GEMINI_API_KEY)


settings = Settings()
