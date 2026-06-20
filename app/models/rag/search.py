from pydantic import BaseModel

from src.rag_processing.rag_searcher import SearchResult


class StepTimings(BaseModel):
    vector_store_ms: float
    similarity_search_ms: float
    dedup_ms: float
    semantic_dedup_ms: float
    total_ms: float


class RAGSearchResponse(BaseModel):
    query: str
    total_chunks: int
    timings: StepTimings
    results: list[SearchResult]


class MediaChunksResponse(BaseModel):
    media_id: str
    total_chunks: int
    chunks: list[SearchResult]
