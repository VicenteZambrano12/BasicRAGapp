"""Health and cache status endpoint for quick service checks."""

from typing import Any, Dict
from fastapi import APIRouter
from src.utils.redis_funcs import REDIS_ENABLED, graph_config_cache, graph_instance_cache


router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def home():
    """Return service health and in-memory cache diagnostics."""

    return {
        "message": "PAUHelper is running",
        "redis_enabled": REDIS_ENABLED,
        "cached_configs": len(graph_config_cache),
        "cached_instances": len(graph_instance_cache),
    }
