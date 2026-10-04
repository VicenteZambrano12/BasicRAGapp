"""Integration tests for POST /api/create_system."""

import pytest

from src.system.create_system import initialize_and_cache_graph as initialize_module
from src.utils.cache import graph_instance_cache, load_graph_config_from_cache

pytestmark = pytest.mark.integration

PAYLOAD = {
    "session_id": "test-session-1",
    "category": "Andalucía",
    "subject": "Biología",
    "language": "ES",
}


@pytest.fixture
def built_graphs(monkeypatch):
    """Replace real graph construction (Qdrant + Vertex) with a recording stub."""
    calls = []

    def fake_create_system(subject, community):
        calls.append({"subject": subject, "community": community})
        return object()

    monkeypatch.setattr(initialize_module, "create_system", fake_create_system)
    monkeypatch.setattr(
        "src.utils.create_system.create_system", fake_create_system, raising=False
    )
    return calls


def test_returns_the_localized_welcome_message(client, built_graphs):
    response = client.post("/api/create_system", json=PAYLOAD)

    assert response.status_code == 200
    assert response.json() == {
        "response": "¡Hola! ¿Cómo puedo ayudarte a estudiar tu examen de Biología?"
    }


def test_returns_the_english_welcome_message(client, built_graphs):
    response = client.post("/api/create_system", json={**PAYLOAD, "language": "EN"})

    assert response.json() == {
        "response": "Hello! How can I help you study for your Biología exam?"
    }


def test_builds_the_graph_for_the_requested_subject_and_community(client, built_graphs):
    client.post("/api/create_system", json=PAYLOAD)

    assert built_graphs == [{"subject": "Biología", "community": "Andalucía"}]
    assert load_graph_config_from_cache("test-session-1:Andalucía:Biología") == {
        "category": "Andalucía",
        "subject": "Biología",
    }


def test_repeated_calls_reuse_the_cached_graph(client, built_graphs):
    client.post("/api/create_system", json=PAYLOAD)
    client.post("/api/create_system", json=PAYLOAD)

    assert len(built_graphs) == 1


def test_a_different_subject_gets_its_own_graph(client, built_graphs):
    client.post("/api/create_system", json=PAYLOAD)
    client.post("/api/create_system", json={**PAYLOAD, "subject": "Física"})

    assert len(built_graphs) == 2
    assert "test-session-1:Andalucía:Física" in graph_instance_cache


def test_graph_construction_failure_returns_500(client, monkeypatch):
    def boom(subject, community):
        raise RuntimeError("Qdrant collection missing")

    monkeypatch.setattr(initialize_module, "create_system", boom)

    response = client.post("/api/create_system", json=PAYLOAD)

    assert response.status_code == 500
    assert response.json()["detail"] == "Qdrant collection missing"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"category": "Andalucía"},
        {"session_id": "s1", "language": "FR"},
    ],
)
def test_invalid_payloads_are_rejected(client, payload):
    response = client.post("/api/create_system", json=payload)

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request payload."}


def test_optional_fields_fall_back_to_defaults(client, built_graphs):
    response = client.post("/api/create_system", json={"session_id": "s1"})

    assert response.status_code == 200
    assert built_graphs == [{"subject": "General", "community": "Community"}]
