"""FastAPI composition root: startup lifecycle, middleware, and route registration."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.Endpoint.chat_endpoint import router as chat_router
from src.api.Endpoint.config_endpoint import router as config_router
from src.api.Endpoint.create_system_endpoint import router as create_system_router
from src.api.Endpoint.home_endpoint import router as home_router
from src.utils.cache import graph_config_cache, graph_instance_cache
from src.utils.create_system import get_embeddings
from vector_db.manager import get_qdrant_client

# Built frontend assets, produced by the frontend Docker build stage.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend_dist"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load runtime resources on startup and clear volatile caches on shutdown."""

    logger.info("[STARTUP] ========== INITIALIZING APPLICATION ==========")

    logger.info("[STARTUP] Loading embeddings model...")
    try:
        get_embeddings()
        logger.info("[STARTUP] Embeddings model loaded successfully")
    except Exception as exc:
        logger.error(f"[STARTUP] Failed to load embeddings model: {exc}", exc_info=True)

    logger.info("[STARTUP] Testing Qdrant connection...")
    try:
        test_client = get_qdrant_client(timeout=5)
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

app.include_router(home_router, prefix="/api")
app.include_router(config_router, prefix="/api")
app.include_router(create_system_router, prefix="/api")
app.include_router(chat_router, prefix="/api")

# Serve the built frontend (single-container deployment) when present; local
# API-only dev (no frontend_dist) simply skips this block.
if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str) -> FileResponse:
        """Serve static frontend files, falling back to index.html for client-side routes."""

        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
