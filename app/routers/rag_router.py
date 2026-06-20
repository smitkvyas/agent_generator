from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.models.rag.search import RAGSearchResponse
from app.services.rag_search_service import RAGSearchService

router = APIRouter(prefix="/rag", tags=["rag"])


class SearchRequest(BaseModel):
    query: str
    k: int = 10
    similarity_threshold: float = 0.9
    media_id: str | None = None


@router.post("/search")
def search(request: SearchRequest, service: RAGSearchService = Depends()) -> RAGSearchResponse:
    try:
        return service.search(
            request.query,
            k=request.k,
            similarity_threshold=request.similarity_threshold,
            media_id=request.media_id,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
