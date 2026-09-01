"""Endpoint that initializes and caches a graph for a given session context."""

import logging
from typing import Dict
from fastapi import APIRouter, HTTPException

from src.api.DataClasses.create_system_request import CreateSystemRequest
from src.utils.create_system import create_system
from src.utils.redis_funcs import (
    get_cache_key,
    graph_instance_cache,
    get_or_create_graph,
    load_graph_config_from_cache,
    save_graph_config_to_cache,
)


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/create_system", response_model=Dict[str, str])
async def create_system_endpoint(data: CreateSystemRequest):
    """Create or recover a graph instance and persist its configuration."""

    session_id, category, subject = data.session_id, data.category, data.subject
    cache_key = get_cache_key(session_id, category, subject)

    logger.info(f"[CREATE_SYSTEM] ========== Request for: {cache_key} ==========")

    cached_config = load_graph_config_from_cache(cache_key)

    if not cached_config:
        logger.info(f"[CREATE_SYSTEM] Creating new system for {category}-{subject}")
        try:
            logger.info("[CREATE_SYSTEM] Initializing graph...")
            graph = create_system(subject=subject, community=category)
            graph_instance_cache[cache_key] = graph
            logger.info("[CREATE_SYSTEM] Graph initialized successfully")
            save_graph_config_to_cache(cache_key, category, subject)
        except Exception as exc:
            logger.error(f"[CREATE_SYSTEM] Error: {exc}")
            raise HTTPException(status_code=500, detail=str(exc))
    else:
        get_or_create_graph(cache_key, category, subject)

    return {
        "response": f"¡Hola! ¿Cómo puedo ayudarte a estudiar tu examen de {subject}?"
    }
