"""Health and cache status endpoint for quick service checks."""

import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status
from src.utils.cache import REDIS_ENABLED, graph_config_cache, graph_instance_cache
from vector_db.manager import get_qdrant_client


router = APIRouter()
logger = logging.getLogger(__name__)

# Short enough that polling clients (see the frontend's useChatStore health
# poll) retry quickly instead of piling up slow requests while the on-demand
# Qdrant VM (infra/modules/qdrant_vm) is still booting after an idle shutdown.
QDRANT_HEALTH_CHECK_TIMEOUT_SECONDS = 3


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="Check API health",
    description="Return service status and the current graph cache diagnostics.",
    response_description="Current service health and cache status.",
)
async def home() -> Dict[str, Any]:
    """Return service health and in-memory cache diagnostics.

    Returns 503 while Qdrant is unreachable (e.g. the on-demand demo VM is
    still starting up after being woken by the public starter Cloud
    Function) so frontend health polling keeps showing a loading state
    instead of a false "ready".
    """

    try:
        get_qdrant_client(timeout=QDRANT_HEALTH_CHECK_TIMEOUT_SECONDS).get_collections()
    except Exception:
        logger.warning(
            "Qdrant not reachable yet; reporting unhealthy",
            exc_info=True,
            extra={"event": "qdrant_health_check_failed"},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Qdrant is starting up. This can take up to a minute after being idle.",
        )

    return {
        "message": "PAUHelper is running",
        "redis_enabled": REDIS_ENABLED,
        "cached_configs": len(graph_config_cache),
        "cached_instances": len(graph_instance_cache),
    }
