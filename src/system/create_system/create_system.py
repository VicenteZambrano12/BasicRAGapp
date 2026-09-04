"""Root create-system orchestration function used by the endpoint layer."""

import logging
from typing import Dict

from fastapi import HTTPException

from src.api.DataClasses.create_system_request import CreateSystemRequest
from src.system.create_system.build_create_system_response import build_create_system_response
from src.system.create_system.ensure_cached_graph import ensure_cached_graph
from src.system.create_system.initialize_and_cache_graph import initialize_and_cache_graph
from src.system.others.cache_key import build_cache_key
from src.utils.redis_funcs import load_graph_config_from_cache


logger = logging.getLogger(__name__)


def execute_create_system(data: CreateSystemRequest) -> Dict[str, str]:
    """Create or recover a graph session and return its welcome response."""
    session_id = data.session_id
    category = data.category
    subject = data.subject
    cache_key = build_cache_key(session_id, category, subject)

    logger.info(f"[CREATE_SYSTEM] ========== Request for: {cache_key} ==========")

    cached_config = load_graph_config_from_cache(cache_key)

    if not cached_config:
        logger.info(f"[CREATE_SYSTEM] Creating new system for {category}-{subject}")
        try:
            initialize_and_cache_graph(cache_key, category, subject)
        except Exception as exc:
            logger.error(f"[CREATE_SYSTEM] Error: {exc}")
            raise HTTPException(status_code=500, detail=str(exc))
    else:
        ensure_cached_graph(cache_key, category, subject)

    return build_create_system_response(subject, data.language)
