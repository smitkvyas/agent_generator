from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class ProcessingStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    CHUNKING = "CHUNKING"
    STORING = "STORING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MediaProcessingStatus(BaseModel):
    file_id: str
    original_filename: str
    status: ProcessingStatus
    created_at: datetime
    updated_at: datetime
    error: str | None = None
