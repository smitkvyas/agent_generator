from collections.abc import Generator

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from loguru import logger

from app.core import GlobalDeps
from app.models.media_processing.internal import PDFProcessingResult
from app.utils.env_utils import Env
from src.rag_processing.hashtag_tagger import tag_chunk
from src.rag_processing.rag_config import PDF_CHUNK_SIZE, PDF_CHUNK_OVERLAP


def chunk_and_store(result: PDFProcessingResult, media_id: str | None = None) -> Generator[str, None, None]:
    yield "CHUNKING"
    chunks = _build_chunks(result, media_id=media_id)
    if not chunks:
        logger.warning(f"No chunks produced for {result.original_filename}")
        return

    logger.info(f"Created {len(chunks)} chunks from {result.original_filename}")

    yield "STORING"
    vector_store = _load_or_create(chunks)

    faiss_dir = Env.get("FAISS_DIR_PATH", required=True)
    vector_store.save_local(faiss_dir)
    logger.info(f"Vector store saved to {faiss_dir}")

    GlobalDeps.vector_store = vector_store


def _build_chunks(result: PDFProcessingResult, media_id: str | None = None) -> list[Document]:
    metadata = {
        "source": result.original_filename,
        "page_count": result.page_count,
        **{k: v for k, v in result.metadata.items() if v},
    }
    if media_id is not None:
        metadata["media_id"] = media_id

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=PDF_CHUNK_SIZE,
        chunk_overlap=PDF_CHUNK_OVERLAP,
    )
    chunks = splitter.create_documents(texts=[result.text], metadatas=[metadata])
    for chunk in chunks:
        hashtags = tag_chunk(chunk.page_content)
        if hashtags:
            chunk.metadata["hashtags"] = hashtags
    return chunks


def _load_or_create(chunks: list[Document]) -> FAISS:
    # get_vector_store in vector_store.py returns None when the FAISS file doesn't
    # exist yet — FAISS cannot be initialised empty, so creation always needs
    # documents and is handled here rather than in that utility function.
    encoder = GlobalDeps.embedding_encoder
    faiss_dir = Env.get("FAISS_DIR_PATH")

    if faiss_dir:
        try:
            store = FAISS.load_local(
                faiss_dir,
                encoder,
                allow_dangerous_deserialization=True,
            )
            logger.info("Existing FAISS store loaded — appending new chunks")
            store.add_documents(chunks)
            return store
        except Exception:
            logger.info("No existing FAISS store found — creating new one")

    return FAISS.from_documents(chunks, encoder)
