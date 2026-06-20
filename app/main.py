from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger
from starlette.middleware.cors import CORSMiddleware

from app.core import GlobalDeps
from app.routers import media_router, rag_router
from app.routers import agent_router
from app.routers import tool_router
from app.routers import model_config_router
from app.routers import pipeline_router
from src.rag_processing.hashtag_tagger import get_hashtag_tagger
from src.rag_processing.vector_store import get_embedding_encoder, get_vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Service")

    GlobalDeps.embedding_encoder = get_embedding_encoder()
    GlobalDeps.vector_store = get_vector_store()
    GlobalDeps.hashtag_tagger = get_hashtag_tagger()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(media_router.router)
app.include_router(rag_router.router)
app.include_router(agent_router.router)
app.include_router(tool_router.router)
app.include_router(model_config_router.router)
app.include_router(pipeline_router.router)
