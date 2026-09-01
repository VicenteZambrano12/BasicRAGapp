"""Endpoint that initializes and caches a graph for a given session context."""

from typing import Dict
from fastapi import APIRouter

from src.api.DataClasses.create_system_request import CreateSystemRequest
from src.system.create_system.create_system import execute_create_system


router = APIRouter()


@router.post("/create_system", response_model=Dict[str, str])
async def create_system_endpoint(data: CreateSystemRequest):
    """Create or recover a graph instance and persist its configuration."""
    return execute_create_system(data)
