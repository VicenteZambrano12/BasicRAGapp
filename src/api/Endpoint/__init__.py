"""Endpoint modules that register the API route handlers."""

from src.api.Endpoint.home_endpoint import router as home_router
from src.api.Endpoint.create_system_endpoint import router as create_system_router
from src.api.Endpoint.chat_endpoint import router as chat_router
from src.api.Endpoint.config_endpoint import router as config_router
