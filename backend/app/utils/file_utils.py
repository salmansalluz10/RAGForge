import os
import re
import uuid
from pathlib import Path
from fastapi import HTTPException, status
from app.core.config import settings

ALLOWED_EXTENSIONS = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
}


def sanitize_filename(filename: str) -> str:
    """
    Remove path traversal sequences and dangerous characters.
    Preserve base name and extension.
    """
    # Strip directory components (handles both Windows \ and Unix /)
    base = os.path.basename(filename)
    # Strip any null bytes or control characters
    base = re.sub(r"[\x00-\x1f\x7f]", "", base)
    # Strip leading/trailing dots or spaces
    base = base.strip(". ")
    if not base:
        base = "unnamed_document"
    return base


def get_file_extension(filename: str) -> str:
    """Extract and validate file extension."""
    parts = filename.rsplit(".", 1)
    if len(parts) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has no extension. Allowed extensions are: pdf, docx, txt.",
        )
    ext = parts[1].lower().strip()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Allowed types: PDF, DOCX, TXT.",
        )
    return ext


def generate_unique_filename(extension: str) -> str:
    """Generate a collision-resistant unique filename."""
    return f"{uuid.uuid4().hex}.{extension}"


def get_upload_dir() -> Path:
    """Ensure upload directory exists and return Path object."""
    upload_path = Path(settings.UPLOAD_DIR).resolve()
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def get_storage_path(stored_filename: str) -> Path:
    """Get absolute path for a stored file, preventing directory traversal."""
    upload_dir = get_upload_dir()
    clean_filename = os.path.basename(stored_filename)
    dest_path = (upload_dir / clean_filename).resolve()
    
    # Path traversal check
    if not str(dest_path).startswith(str(upload_dir)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Illegal file path detected.",
        )
    return dest_path


def remove_stored_file(stored_filename: str) -> None:
    """Safely delete stored file from disk if it exists."""
    try:
        path = get_storage_path(stored_filename)
        if path.exists() and path.is_file():
            path.unlink()
    except Exception:
        # Avoid crashing if file is already deleted
        pass
