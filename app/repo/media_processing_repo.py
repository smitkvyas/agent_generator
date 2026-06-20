import json
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from app.models.media_processing.internal import MediaFile
from app.models.media_processing.status import MediaProcessingStatus, ProcessingStatus
from app.utils.env_utils import Env

_DEFAULT_STATUS_PATH = "./data/media_status.json"


def _status_file() -> Path:
    return Path(Env.get("MEDIA_STATUS_PATH", _DEFAULT_STATUS_PATH))


def _read_all() -> dict:
    path = _status_file()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as e:
        logger.error(f"Failed to read status file: {e}")
        return {}


def _write_all(data: dict) -> None:
    path = _status_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


class MediaProcessingRepo:

    def create(self, media_file: MediaFile) -> MediaProcessingStatus:
        now = datetime.now(timezone.utc)
        entry = MediaProcessingStatus(
            file_id=media_file.file_id,
            original_filename=media_file.original_filename,
            status=ProcessingStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        data = _read_all()
        data[media_file.file_id] = entry.model_dump(mode="json")
        _write_all(data)
        return entry

    def update_status(
        self,
        file_id: str,
        status: ProcessingStatus,
        error: str | None = None,
    ) -> None:
        data = _read_all()
        if file_id not in data:
            logger.warning(f"update_status called for unknown file_id {file_id}")
            return
        data[file_id]["status"] = status.value
        data[file_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        if error is not None:
            data[file_id]["error"] = error
        _write_all(data)

    def get(self, file_id: str) -> MediaProcessingStatus | None:
        data = _read_all()
        entry = data.get(file_id)
        if entry is None:
            return None
        return MediaProcessingStatus(**entry)

    def get_all(self) -> list[MediaProcessingStatus]:
        data = _read_all()
        return [MediaProcessingStatus(**v) for v in data.values()]
