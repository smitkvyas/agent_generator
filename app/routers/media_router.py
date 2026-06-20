from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from fastapi.params import Depends

from app.core import GlobalDeps
from app.models.rag.search import MediaChunksResponse
from app.repo.media_processing_repo import MediaProcessingRepo
from app.services.media_processing_service import MediaProcessingService
from app.utils.media_file_handler import save_to_temp
from src.rag_processing.rag_searcher import SearchResult

router = APIRouter(prefix="/media", tags=["medias"])


@router.post("/process-for-rag")
async def process_media_for_rag(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    media_processing_service: MediaProcessingService = Depends(),
    repo: MediaProcessingRepo = Depends(),
):
    ext = Path(file.filename).suffix.lower()
    supported = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
    if ext not in supported:
        raise HTTPException(status_code=400, detail=f"{ext} is not supported yet")

    try:
        temp_file = await save_to_temp(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    repo.create(temp_file)
    background_tasks.add_task(media_processing_service.process_media, temp_file)

    return {"file_id": temp_file.file_id, "message": "File received. Processing started in background."}


@router.get("/status")
def get_all_statuses(repo: MediaProcessingRepo = Depends()):
    return repo.get_all()


@router.get("/status/{file_id}")
def get_status(file_id: str, repo: MediaProcessingRepo = Depends()):
    status = repo.get(file_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"No record found for file_id {file_id}")
    return status


@router.get("/{media_id}/chunks", response_model=MediaChunksResponse)
def get_media_chunks(media_id: str, repo: MediaProcessingRepo = Depends()):
    if repo.get(media_id) is None:
        raise HTTPException(status_code=404, detail=f"No record found for media_id {media_id}")

    if GlobalDeps.vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store is not available")

    chunks = [
        SearchResult(content=doc.page_content, score=0.0, metadata=doc.metadata)
        for doc in GlobalDeps.vector_store.docstore._dict.values()
        if doc.metadata.get("media_id") == media_id
    ]

    return MediaChunksResponse(media_id=media_id, total_chunks=len(chunks), chunks=chunks)
