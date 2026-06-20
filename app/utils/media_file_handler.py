import tempfile
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.models.media_processing.internal import MediaFile


async def save_to_temp(file: UploadFile) -> MediaFile:
    file_id = str(uuid.uuid4())
    suffix = Path(file.filename).suffix.lower()
    temp_path = Path(tempfile.gettempdir()) / f"{file_id}{suffix}"
    contents = await file.read()
    temp_path.write_bytes(contents)
    return MediaFile(file_id=file_id, original_filename=file.filename, temp_path=temp_path)
