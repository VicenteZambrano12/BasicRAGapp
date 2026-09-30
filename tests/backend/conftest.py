"""Shared fixtures and environment isolation for the backend test suite."""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Set to blank rather than unset: vector_db.manager calls load_dotenv() on import,
# and load_dotenv does not override variables that already exist. This guarantees
# the cache layer falls back to fakeredis instead of a developer's real Redis.
os.environ["REDIS_URL"] = ""
os.environ["REDIS_HOST"] = ""
os.environ.setdefault("GCS_BUCKET_NAME", "test-bucket")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "europe-southwest1")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src.api.app import app  # noqa: E402
from src.utils.cache import graph_config_cache, graph_instance_cache  # noqa: E402
from src.utils.cache.redis_client import redis_client  # noqa: E402


@pytest.fixture(autouse=True)
def reset_caches():
    """Isolate each test from graph/memory state left behind by the previous one."""
    graph_config_cache.clear()
    graph_instance_cache.clear()
    redis_client.flushall()
    yield
    graph_config_cache.clear()
    graph_instance_cache.clear()
    redis_client.flushall()


@pytest.fixture
def client():
    """TestClient that does not run the startup lifespan (no Qdrant/Vertex calls)."""
    return TestClient(app)


@pytest.fixture
def lenient_client():
    """TestClient that returns the 500 response instead of re-raising server errors."""
    return TestClient(app, raise_server_exceptions=False)
