"""End-to-end integration test: create a system, hold a multi-turn conversation, switch subject.

Only the external boundaries (LangGraph construction, GCS URL signing) are stubbed;
routing, validation, orchestration and the conversation-memory cache are all real.
"""

import json

import pytest

from src.api.Endpoint import home_endpoint
from src.system.chat import build_sources as build_sources_module
from src.system.create_system import initialize_and_cache_graph as initialize_module
from src.utils.cache import get_str_field_from_cache, graph_instance_cache
from tests.backend.factories import FakeGraph, FakeMessage

pytestmark = pytest.mark.integration

SESSION_ID = "conversation-session"


@pytest.fixture(autouse=True)
def qdrant_reachable(monkeypatch):
    """This suite exercises conversation flow, not Qdrant connectivity; stub it as up."""

    class FakeQdrantClient:
        def get_collections(self):
            return object()

    monkeypatch.setattr(home_endpoint, "get_qdrant_client", lambda timeout=None: FakeQdrantClient())


class ScriptedGraph:
    """Answers with a canned reply per turn and records the state it was given."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.streamed_states = []

    def stream(self, state, stream_mode="values"):
        self.streamed_states.append(state)
        answer = self.answers.pop(0) if self.answers else "…"
        yield {"messages": [FakeMessage("ai", answer)], "documents": []}


@pytest.fixture
def graphs(monkeypatch):
    """Return the per-(subject, community) graphs built during the test."""
    built = {}

    def fake_create_system(subject, community):
        built[(subject, community)] = ScriptedGraph(
            [f"{subject} answer 1", f"{subject} answer 2"]
        )
        return built[(subject, community)]

    monkeypatch.setattr(initialize_module, "create_system", fake_create_system)
    monkeypatch.setattr(
        "src.utils.create_system.create_system", fake_create_system, raising=False
    )
    monkeypatch.setattr(
        build_sources_module, "_sign_url", lambda bucket, obj: f"https://signed.example/{obj}"
    )
    return built


def test_conversation_memory_is_carried_into_the_next_turn(client, graphs):
    payload = {"session_id": SESSION_ID, "category": "Andalucía", "subject": "Biología"}

    assert client.post("/api/create_system", json=payload).status_code == 200

    first = client.post("/api/chat", json={**payload, "query": "¿Qué es la mitosis?"})
    assert first.json()["response"] == "Biología answer 1"

    second = client.post("/api/chat", json={**payload, "query": "¿Y la meiosis?"})
    assert second.json()["response"] == "Biología answer 2"

    graph = graphs[("Biología", "Andalucía")]
    second_turn_messages = graph.streamed_states[1]["messages"]
    assert {"role": "user", "content": "¿Qué es la mitosis?"} in second_turn_messages
    assert {"role": "assistant", "content": "Biología answer 1"} in second_turn_messages


def test_memory_is_persisted_under_the_session_cache_key(client, graphs):
    payload = {"session_id": SESSION_ID, "category": "Andalucía", "subject": "Biología"}
    client.post("/api/create_system", json=payload)
    client.post("/api/chat", json={**payload, "query": "¿Qué es la mitosis?"})

    stored = json.loads(get_str_field_from_cache(f"{SESSION_ID}:Andalucía:Biología"))

    assert stored["recent"] == [
        {"user": "¿Qué es la mitosis?", "ai": "Biología answer 1"}
    ]


def test_switching_subject_starts_a_separate_conversation(client, graphs):
    biology = {"session_id": SESSION_ID, "category": "Andalucía", "subject": "Biología"}
    physics = {"session_id": SESSION_ID, "category": "Andalucía", "subject": "Física"}

    client.post("/api/create_system", json=biology)
    client.post("/api/chat", json={**biology, "query": "pregunta de biología"})

    client.post("/api/create_system", json=physics)
    response = client.post("/api/chat", json={**physics, "query": "pregunta de física"})

    assert response.json()["response"] == "Física answer 1"
    physics_messages = graphs[("Física", "Andalucía")].streamed_states[0]["messages"]
    assert all("biología" not in str(message["content"]) for message in physics_messages)
    assert {f"{SESSION_ID}:Andalucía:Biología", f"{SESSION_ID}:Andalucía:Física"} <= set(
        graph_instance_cache
    )


def test_health_endpoint_reflects_the_warmed_caches(client, graphs):
    payload = {"session_id": SESSION_ID, "category": "Andalucía", "subject": "Biología"}
    client.post("/api/create_system", json=payload)

    body = client.get("/api/").json()

    assert body["cached_configs"] == 1
    assert body["cached_instances"] == 1


def test_a_failed_turn_does_not_pollute_conversation_memory(client, graphs):
    payload = {"session_id": SESSION_ID, "category": "Andalucía", "subject": "Biología"}
    client.post("/api/create_system", json=payload)

    graph_instance_cache[f"{SESSION_ID}:Andalucía:Biología"] = FakeGraph(
        [{"messages": [FakeMessage("human", "q")]}]
    )
    assert client.post("/api/chat", json={**payload, "query": "pregunta"}).status_code == 500

    assert get_str_field_from_cache(f"{SESSION_ID}:Andalucía:Biología") is None
