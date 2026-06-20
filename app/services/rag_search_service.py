from app.models.rag.search import RAGSearchResponse, StepTimings
from src.rag_processing.rag_searcher import RAGSearcher


class RAGSearchService:

    def search(self, query: str, k: int, similarity_threshold: float, media_id: str | None = None) -> RAGSearchResponse:
        output = RAGSearcher(k=k, similarity_threshold=similarity_threshold, media_id=media_id).search(query)
        return RAGSearchResponse(
            query=query,
            total_chunks=len(output.results),
            timings=StepTimings(
                vector_store_ms=output.vector_store_ms,
                similarity_search_ms=output.similarity_search_ms,
                dedup_ms=output.dedup_ms,
                semantic_dedup_ms=output.semantic_dedup_ms,
                total_ms=output.total_ms,
            ),
            results=output.results,
        )
