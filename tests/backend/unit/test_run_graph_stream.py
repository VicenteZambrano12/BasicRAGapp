"""Unit tests for src.system.chat.run_graph_stream."""

import pytest
from fastapi import HTTPException

from src.system.chat.run_graph_stream import run_graph_stream
from tests.backend.factories import FakeDocument, FakeGraph, FakeMessage


def test_returns_last_ai_response_step_count_and_documents():
    documents = [FakeDocument(relative_path="a.pdf")]
    graph = FakeGraph(
        [
            {"messages": [FakeMessage("human", "q")], "documents": []},
            {"messages": [FakeMessage("ai", "first")], "documents": documents},
            {"messages": [FakeMessage("ai", "final")]},
        ]
    )

    response, steps, retrieved = run_graph_stream(graph, {"messages": []})

    assert response == "final"
    assert steps == 3
    assert retrieved == documents


def test_forwards_the_chat_state_to_the_graph():
    graph = FakeGraph([{"messages": [FakeMessage("ai", "ok")]}])
    state = {"messages": [{"role": "user", "content": "hi"}]}

    run_graph_stream(graph, state)

    assert graph.streamed_states == [state]


def test_documents_default_to_empty_when_never_emitted():
    graph = FakeGraph([{"messages": [FakeMessage("ai", "ok")]}])

    _, _, documents = run_graph_stream(graph, {})

    assert documents == []


@pytest.mark.parametrize(
    "steps",
    [
        [{"messages": [FakeMessage("human", "q")]}],
        [{"messages": [FakeMessage("ai", "")]}],
    ],
)
def test_missing_assistant_response_raises_500(steps):
    with pytest.raises(HTTPException) as exc_info:
        run_graph_stream(FakeGraph(steps), {})

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "No response generated"
