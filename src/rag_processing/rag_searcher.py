from dataclasses import dataclass
from datetime import datetime
from typing import Any

from langchain_community.vectorstores import FAISS
from loguru import logger
from pydantic import BaseModel
from sklearn.metrics.pairwise import cosine_similarity

from app.core import GlobalDeps
from src.rag_processing.rag_config import RAG_SEARCH_K, RAG_SIMILARITY_THRESHOLD
from src.rag_processing.vector_store import get_vector_store


class SearchResult(BaseModel):
    content: str
    score: float
    metadata: dict[str, Any] = {}


@dataclass
class SearchOutput:
    results: list[SearchResult]
    vector_store_ms: float
    similarity_search_ms: float
    dedup_ms: float
    semantic_dedup_ms: float
    total_ms: float


class RAGSearcher:

    def __init__(
        self,
        k: int = RAG_SEARCH_K,
        similarity_threshold: float = RAG_SIMILARITY_THRESHOLD,
        media_id: str | None = None,
    ):
        self.k = k
        self.similarity_threshold = similarity_threshold
        self.media_id = media_id

    def search(self, query: str) -> SearchOutput:
        total_start = datetime.now()
        logger.info(f"Search started | query={query!r} k={self.k} threshold={self.similarity_threshold} media_id={self.media_id!r}")

        t = datetime.now()
        store = self._resolve_vector_store()
        vector_store_ms = (datetime.now() - t).total_seconds() * 1000
        logger.info(f"Vector store resolved in {vector_store_ms:.1f}ms")

        t = datetime.now()
        filter_kwargs = {"filter": {"media_id": self.media_id}} if self.media_id is not None else {}
        docs_with_scores = store.similarity_search_with_score(query, k=self.k, **filter_kwargs)
        docs_with_scores = [(doc, score) for doc, score in docs_with_scores if score <= self.similarity_threshold]
        similarity_search_ms = (datetime.now() - t).total_seconds() * 1000
        logger.info(f"FAISS similarity_search returned {len(docs_with_scores)} docs in {similarity_search_ms:.1f}ms")

        # for doc, score in docs_with_scores:
        #     logger.debug(f"Doc: {doc.page_content} | Score: {score:.4f} | Metadata: {doc.metadata}")

        t = datetime.now()
        # docs_with_scores = self._remove_duplicates(docs_with_scores)
        dedup_ms = (datetime.now() - t).total_seconds() * 1000
        logger.info(f"After dedup: {len(docs_with_scores)} docs ({dedup_ms:.1f}ms)")

        t = datetime.now()
        # docs_with_scores = self._remove_semantically_similar(docs_with_scores, store)
        semantic_dedup_ms = (datetime.now() - t).total_seconds() * 1000
        logger.info(f"After semantic dedup: {len(docs_with_scores)} docs ({semantic_dedup_ms:.1f}ms)")

        total_ms = (datetime.now() - total_start).total_seconds() * 1000
        logger.info(f"Search completed in {total_ms:.1f}ms | {len(docs_with_scores)} chunks returned")

        return SearchOutput(
            results=[
                SearchResult(content=doc.page_content, score=float(score), metadata=doc.metadata)
                for doc, score in docs_with_scores
            ],
            vector_store_ms=vector_store_ms,
            similarity_search_ms=similarity_search_ms,
            dedup_ms=dedup_ms,
            semantic_dedup_ms=semantic_dedup_ms,
            total_ms=total_ms,
        )

    def _resolve_vector_store(self) -> FAISS:
        if GlobalDeps.vector_store is not None:
            logger.debug("Using in-memory vector store from GlobalDeps")
            return GlobalDeps.vector_store
        logger.info("Vector store not in memory — loading from disk")
        store = get_vector_store()
        if store is None:
            raise RuntimeError("Vector store is not available — no documents have been indexed yet")
        GlobalDeps.vector_store = store
        return store

    def _remove_duplicates(self, docs_with_scores: list) -> list:
        seen: set[str] = set()
        unique = []
        for doc, score in docs_with_scores:
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                unique.append((doc, score))
        return unique

    def _remove_semantically_similar(self, docs_with_scores: list, store: FAISS) -> list:
        if len(docs_with_scores) <= 1:
            return docs_with_scores

        # Build content -> FAISS integer ID from the store's own mapping — no re-encoding needed
        t = datetime.now()
        content_to_faiss_id = {
            store.docstore._dict[str_id].page_content: int_id
            for int_id, str_id in store.index_to_docstore_id.items()
            if str_id in store.docstore._dict
        }
        logger.debug(f"FAISS ID mapping built in {datetime.now() - t}")

        index = store.index if not callable(store.index) else store._index

        t = datetime.now()
        faiss_ids = [content_to_faiss_id[doc.page_content] for doc, _ in docs_with_scores
                     if doc.page_content in content_to_faiss_id]
        all_embeddings = [index.reconstruct(i) for i in faiss_ids]
        logger.debug(f"Reconstructed {len(all_embeddings)} embeddings from FAISS index in {datetime.now() - t}")

        sim_matrix = cosine_similarity(all_embeddings)

        kept: list[int] = []
        removed: set[int] = set()

        for i in range(len(faiss_ids)):
            if i in removed:
                continue
            kept.append(i)
            for j in range(i + 1, len(faiss_ids)):
                if sim_matrix[i][j] > self.similarity_threshold:
                    removed.add(j)

        logger.debug(f"Semantic dedup removed {len(removed)} docs")
        return [docs_with_scores[i] for i in kept]