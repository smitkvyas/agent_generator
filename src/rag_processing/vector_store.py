from datetime import datetime

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from loguru import logger

from app.core import GlobalDeps
from app.utils.env_utils import Env
from src.rag_processing.rag_config import EMBEDDING_ENCODER_MODEL


def get_embedding_encoder():
    start_time = datetime.now()
    logger.info("Downloading Huggingface Model")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_ENCODER_MODEL,
                                       model_kwargs={"device": "cpu"}, encode_kwargs={"batch_size": 32}, )
    logger.info(f"Download completed in {datetime.now() - start_time} seconds")
    return embeddings


def get_vector_store(embedding_encoder=None, file_path: str = None):
    embedding_encoder = GlobalDeps.embedding_encoder if embedding_encoder is None else embedding_encoder
    try:
        logger.info(f"Loading Faiss DB from path {file_path}")
        _vector_store = FAISS.load_local(
            Env.get("FAISS_DIR_PATH") if file_path is None else file_path,
            embedding_encoder,
            allow_dangerous_deserialization=True,
        )
        logger.info("Faiss DB loaded successfully")
        return _vector_store
    except Exception as e:
        logger.error(f"Faiss DB not loaded for path {file_path}. Error: {e}")
    return None


def get_all_metadata(vector_store):
    """Retrieve metadata for all documents in the vector store."""
    all_metadata = [doc.metadata for doc in vector_store.docstore._dict.values()]
    return all_metadata


def get_all_active_docs_by(vector_store, keyword: str, country: str = None, keyword_env: str = None):
    """Retrieve all active documents matching a specific keyword from the vector store."""
    matched_docs = []
    for doc_id, doc in vector_store.docstore._dict.items():
        logger.debug(f"Checking doc_id: {doc_id}, metadata: {doc.metadata}")
        if doc.metadata.get("keyword") == keyword and doc.metadata.get("country", "") == country and doc.metadata.get(
                "is_active", True) and (doc.metadata.get("env", "") == keyword_env):
            matched_docs.append((doc_id, doc))
    return matched_docs


def get_all_keywords(vector_store):
    """Retrieve all unique keywords from the document metadata in the vector store."""
    all_docs = get_all_metadata(vector_store)  # For debugging purposes
    keywords = set()
    for metadata in all_docs:
        keyword = metadata.get("keyword")
        if keyword and metadata.get("is_active", True):
            keywords.add(keyword)
    return list(keywords)


def get_all_by_pharse_id(vector_store, phrase_id: str):
    """Retrieve all documents matching a specific phrase_id from the vector store."""
    matched_docs = []
    for doc_id, doc in vector_store.docstore._dict.items():
        if doc.metadata.get("phrase_id") == phrase_id:
            matched_docs.append((doc_id, doc))
    return matched_docs
