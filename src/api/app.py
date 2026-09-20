"""FastAPI composition root: startup lifecycle, middleware, and route registration."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.Endpoint.chat_endpoint import router as chat_router
from src.api.Endpoint.config_endpoint import router as config_router
from src.api.Endpoint.create_system_endpoint import router as create_system_router
from src.api.Endpoint.home_endpoint import router as home_router
from src.api.middleware.logging_middleware import RequestLoggingMiddleware
from src.utils.cache import graph_config_cache, graph_instance_cache
from src.utils.create_system import get_embeddings
from src.utils.observability.logger import configure_logging
from vector_db.manager import get_qdrant_client

# Built frontend assets, produced by the frontend Docker build stage.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend_dist"


configure_logging()
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
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Log malformed request payloads as WARNING and return a 422 response."""

    logger.warning(
        "Request validation failed",
        extra={"path": request.url.path, "errors": exc.errors()},
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request payload."},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Log known HTTP errors and return their original status code/detail."""

    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={"path": request.url.path, "status_code": exc.status_code},
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions: log full traceback, hide details from the client."""

    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"path": request.url.path},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error."},
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
