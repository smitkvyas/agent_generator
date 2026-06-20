from pathlib import Path

from loguru import logger

import io

from PIL import Image
import pytesseract

from app.models.media_processing.internal import ImageProcessingResult, MediaFile, PDFProcessingResult
from app.models.media_processing.status import ProcessingStatus
from app.repo.media_processing_repo import MediaProcessingRepo
from src.pdf_processing.pdf_processor import PDFProcessor
from src.rag_processing import image_chunker, pdf_chunker


class MediaProcessingService:

    def process_media(self, media_file: MediaFile) -> None:
        repo = MediaProcessingRepo()
        try:
            repo.update_status(media_file.file_id, ProcessingStatus.PROCESSING)
            ext = Path(media_file.original_filename).suffix.lower()
            if ext == ".pdf":
                self._process_pdf(media_file, repo)
            elif ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}:
                self._process_image(media_file, repo)
            else:
                raise ValueError(f"{ext} is not supported yet")
            repo.update_status(media_file.file_id, ProcessingStatus.COMPLETED)
        except Exception as e:
            logger.error(f"Processing failed for {media_file.original_filename}: {e}")
            repo.update_status(media_file.file_id, ProcessingStatus.FAILED, error=str(e))
        finally:
            media_file.delete()

    def _process_pdf(self, media_file: MediaFile, repo: MediaProcessingRepo) -> None:
        with PDFProcessor(str(media_file.temp_path)) as processor:
            images = processor.extract_images()
            result = PDFProcessingResult(
                original_filename=media_file.original_filename,
                page_count=processor.get_page_count(),
                text=processor.extract_text(),
                metadata=processor.extract_metadata(),
                images=images,
            )

        ocr_parts = []
        for img in images:
            try:
                ocr_text = pytesseract.image_to_string(Image.open(io.BytesIO(img["image_bytes"])))
                if ocr_text.strip():
                    ocr_parts.append(ocr_text)
            except Exception as e:
                logger.warning(f"OCR failed for image on page {img.get('page_number')}: {e}")

        if ocr_parts:
            result.text = result.text + "\n" + "\n".join(ocr_parts)

        for step in pdf_chunker.chunk_and_store(result, media_id=media_file.file_id):
            repo.update_status(media_file.file_id, ProcessingStatus[step])

    def _process_image(self, media_file: MediaFile, repo: MediaProcessingRepo) -> None:
        text = pytesseract.image_to_string(Image.open(media_file.temp_path))
        result = ImageProcessingResult(
            original_filename=media_file.original_filename,
            text=text,
        )
        for step in image_chunker.chunk_and_store(result, media_id=media_file.file_id):
            repo.update_status(media_file.file_id, ProcessingStatus[step])
