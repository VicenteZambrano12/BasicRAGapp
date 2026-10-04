"""Integration tests for POST /api/chat."""

import pytest

from src.system.chat import build_sources as build_sources_module
from src.system.chat import chat as chat_module
from src.system.create_system import initialize_and_cache_graph as initialize_module
from src.utils.cache import graph_instance_cache
from tests.backend.factories import FakeDocument, FakeGraph, FakeMessage, answer_graph

pytestmark = pytest.mark.integration

SESSION = {"session_id": "test-session-1", "category": "Andalucía", "subject": "Biología"}
CACHE_KEY = "test-session-1:Andalucía:Biología"

PNG_PIXEL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


class GraphHolder:
    """Keeps the scripted graph reachable and swappable after it has been cached."""

    def __init__(self, graph):
        self.graph = graph

    def replace(self, graph):
        self.graph = graph
        graph_instance_cache[CACHE_KEY] = graph


@pytest.fixture
def graph(monkeypatch):
    """Serve a scripted graph to both /create_system and /chat."""
    holder = GraphHolder(answer_graph("La fotosíntesis es..."))

    def fake_create_system(subject, community):
        return holder.graph

    monkeypatch.setattr(initialize_module, "create_system", fake_create_system)
    monkeypatch.setattr(
        "src.utils.create_system.create_system", fake_create_system, raising=False
    )
    monkeypatch.setattr(
        build_sources_module,
        "_sign_url",
        lambda bucket_name, object_name: f"https://signed.example/{object_name}",
    )
    return holder


@pytest.fixture
def initialized(client, graph):
    client.post("/api/create_system", json={**SESSION, "language": "ES"})
    return graph


def test_rejects_chat_before_create_system(client, graph):
    response = client.post("/api/chat", json={**SESSION, "query": "¿Qué es la mitosis?"})

    assert response.status_code == 400
    assert "Call /create_system first" in response.json()["detail"]


def test_returns_the_assistant_answer(client, initialized):
    response = client.post("/api/chat", json={**SESSION, "query": "¿Qué es la fotosíntesis?"})

    assert response.status_code == 200
    assert response.json() == {"response": "La fotosíntesis es...", "sources": []}


def test_returns_deduplicated_signed_sources(client, initialized):
    initialized.replace(answer_graph(
        "Respuesta",
        documents=[
            FakeDocument(
                relative_path="biology/cells.pdf",
                bucket_name="bucket",
                object_name="documents/biology/cells.pdf",
                file_name="cells.pdf",
                page_number=4,
            ),
            FakeDocument(
                relative_path="biology/cells.pdf",
                bucket_name="bucket",
                object_name="documents/biology/cells.pdf",
                file_name="cells.pdf",
                page_number=9,
            ),
        ],
    ))

    body = client.post("/api/chat", json={**SESSION, "query": "pregunta"}).json()

    assert body["sources"] == [
        {
            "doc_id": "biology/cells.pdf",
            "file_name": "cells.pdf",
            "page": 4,
            "url": "https://signed.example/documents/biology/cells.pdf",
        }
    ]


def test_language_instruction_is_passed_to_the_graph(client, initialized):
    client.post("/api/chat", json={**SESSION, "query": "question", "language": "EN"})

    streamed = initialized.graph.streamed_states[-1]
    assert streamed["messages"][0] == {"role": "system", "content": "Always respond in English."}
    assert streamed["messages"][-1] == {
        "role": "user",
        "content": [{"type": "text", "text": "question"}],
    }


def test_requires_a_query_or_an_image(client, initialized):
    response = client.post("/api/chat", json=SESSION)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Either query or image (with image_type) must be provided"
    )


def test_image_is_attached_and_described(client, initialized, monkeypatch):
    monkeypatch.setattr(chat_module, "image_read", lambda url: "a labelled cell diagram")

    response = client.post(
        "/api/chat",
        json={**SESSION, "query": "¿Qué ves?", "image": PNG_PIXEL, "image_type": "base64"},
    )

    assert response.status_code == 200
    streamed = initialized.graph.streamed_states[-1]
    user_content = streamed["messages"][-1]["content"]
    assert user_content[1]["type"] == "image_url"
    assert user_content[1]["image_url"]["url"] == PNG_PIXEL
    system_messages = [m["content"] for m in streamed["messages"] if m["role"] == "system"]
    assert any("a labelled cell diagram" in message for message in system_messages)


def test_image_description_failure_degrades_gracefully(client, initialized, monkeypatch):
    def boom(url):
        raise RuntimeError("vision quota exceeded")

    monkeypatch.setattr(chat_module, "image_read", boom)

    response = client.post(
        "/api/chat",
        json={**SESSION, "query": "¿Qué ves?", "image": PNG_PIXEL, "image_type": "base64"},
    )

    assert response.status_code == 200
    streamed = initialized.graph.streamed_states[-1]
    system_messages = [m["content"] for m in streamed["messages"] if m["role"] == "system"]
    assert any("Image: [processed]" in message for message in system_messages)


def test_invalid_image_url_returns_400(client, initialized):
    response = client.post(
        "/api/chat",
        json={**SESSION, "query": "q", "image": "ftp://example.com/a.png", "image_type": "url"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "URL must start with http:// or https://"


def test_graph_without_an_answer_returns_500(client, initialized):
    initialized.replace(FakeGraph([{"messages": [FakeMessage("human", "q")]}]))

    response = client.post("/api/chat", json={**SESSION, "query": "pregunta"})

    assert response.status_code == 500
    assert response.json()["detail"] == "No response generated"


def test_unexpected_graph_failure_returns_500(client, initialized):
    class ExplodingGraph:
        def stream(self, state, stream_mode="values"):
            raise RuntimeError("model unavailable")

    initialized.replace(ExplodingGraph())

    response = client.post("/api/chat", json={**SESSION, "query": "pregunta"})

    assert response.status_code == 500
    assert "model unavailable" in response.json()["detail"]


@pytest.mark.parametrize("payload", [{}, {"query": "q"}, {"session_id": "s1", "language": "FR"}])
def test_invalid_payloads_are_rejected(client, payload):
    response = client.post("/api/chat", json=payload)

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request payload."}
