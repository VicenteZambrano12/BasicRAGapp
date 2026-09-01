import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient

from src.api.Endpoint.chat_endpoint import router as chat_router
from src.api.Endpoint.create_system_endpoint import router as create_system_router
from src.api.Endpoint.home_endpoint import router as home_router
from src.config.config_loader import config
from src.utils.create_system import get_embeddings
from src.utils.redis_funcs import graph_config_cache, graph_instance_cache


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[STARTUP] ========== INITIALIZING APPLICATION ==========")

    logger.info("[STARTUP] Loading embeddings model...")
    try:
        get_embeddings()
        logger.info("[STARTUP] Embeddings model loaded successfully")
    except Exception as exc:
        logger.error(f"[STARTUP] Failed to load embeddings model: {exc}", exc_info=True)

    logger.info("[STARTUP] Testing Qdrant connection...")
    try:
        qdrant_host = config("QDRANT_HOST") if config("QDRANT_HOST") else "qdrant"
        qdrant_port = int(config("QDRANT_PORT")) if config("QDRANT_PORT") else 6333

        test_client = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=5)
        collections = test_client.get_collections()
        logger.info(
            f"[STARTUP] Qdrant connected successfully ({len(collections.collections)} collections)"
        )
    except Exception as exc:
        logger.error(f"[STARTUP] Failed to connect to Qdrant: {exc}", exc_info=True)

    logger.info("[STARTUP] ========== APPLICATION READY ==========")
    yield

    logger.info("[SHUTDOWN] Cleaning up resources...")
    graph_instance_cache.clear()
    graph_config_cache.clear()


app = FastAPI(
    title="PAUHelper",
    description="PAUHelper web API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.environ["AZURE_OPENAI_API_KEY"] = config("AZURE_OPENAI_API_KEY")

app.include_router(home_router)
app.include_router(create_system_router)
app.include_router(chat_router)
