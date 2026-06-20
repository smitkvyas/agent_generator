from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MediaFile:
    file_id: str
    original_filename: str
    temp_path: Path

    def delete(self) -> None:
        if self.temp_path.exists():
            self.temp_path.unlink()


@dataclass
class PDFProcessingResult:
    original_filename: str
    page_count: int
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    images: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ImageProcessingResult:
    original_filename: str
    text: str
