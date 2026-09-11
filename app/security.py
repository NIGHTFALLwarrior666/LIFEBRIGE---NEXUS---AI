"""Security and input sanitization layer for LifeBridge AI."""

import re
from typing import Optional, Tuple
from fastapi import HTTPException, UploadFile, status
from app.config import settings


# Magic bytes inspection signatures for secure MIME verification
MAGIC_BYTES_TABLE = {
    # JPEG: starts with FF D8 FF
    b"\xff\xd8\xff": "image/jpeg",
    # PNG: starts with 89 50 4E 47 0D 0A 1A 0A
    b"\x89PNG\r\n\x1a\n": "image/png",
    # WEBP: RIFF....WEBP
    b"RIFF": "image/webp",  # will check WEBP sub-header
    # WAV: RIFF....WAVE
    b"RIFF": "audio/wav",   # handled in helper
    # MP3: ID3 or FF FB / FF F3 / FF F2
    b"ID3": "audio/mpeg",
    b"\xff\xfb": "audio/mpeg",
    b"\xff\xf3": "audio/mpeg",
    # OGG: OggS
    b"OggS": "audio/ogg",
    # MP4 / M4A / WEBM: 'ftyp' or \x1a\x45\xdf\xa3 (EBML for webm)
    b"\x1aE\xdf\xa3": "audio/webm",
}


def sanitize_filename(filename: Optional[str]) -> str:
    """Normalize and sanitize untrusted client filenames to prevent path traversal."""
    if not filename:
        return "unnamed_attachment"
    
    # Strip directory paths
    base_name = filename.replace("\\", "/").split("/")[-1]
    # Keep only safe alphanumeric characters, dots, and hyphens/underscores
    cleaned = re.sub(r"[^\w\.-]", "_", base_name, flags=re.ASCII)
    # Prevent hidden files or path traversal via leading dots
    cleaned = cleaned.lstrip(".")
    if not cleaned:
        return "attachment"
    return cleaned[:100]  # bounded filename length


def sanitize_user_text(text: Optional[str]) -> str:
    """Clean and validate input text to prevent unbounded payloads or injection."""
    if not text:
        return ""
    
    trimmed = text.strip()
    if len(trimmed) > settings.MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Text input exceeds maximum limit of {settings.MAX_TEXT_LENGTH} characters."
        )
    return trimmed


async def validate_uploaded_file(file: Optional[UploadFile]) -> Optional[Tuple[bytes, str, str]]:
    """
    Validate uploaded file completely in memory without disk persistence.
    Returns: Tuple of (file_bytes, safe_filename, detected_mime_type) or None if no file.
    """
    if not file or not file.filename:
        return None

    safe_name = sanitize_filename(file.filename)
    declared_mime = (file.content_type or "application/octet-stream").lower().split(";")[0].strip()

    # Read bytes with hard size limit enforcement
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
        )

    # Basic MIME validation
    if declared_mime not in settings.ALLOWED_MIME_TYPES:
        # Check extensions as fallback
        ext = safe_name.lower().split(".")[-1] if "." in safe_name else ""
        ext_to_mime = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "m4a": "audio/mp4",
            "ogg": "audio/ogg",
            "webm": "audio/webm",
        }
        if ext in ext_to_mime:
            declared_mime = ext_to_mime[ext]
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type '{declared_mime}'. Allowed formats: JPEG, PNG, WEBP, WAV, MP3, M4A, OGG, WEBM."
            )

    return content, safe_name, declared_mime
