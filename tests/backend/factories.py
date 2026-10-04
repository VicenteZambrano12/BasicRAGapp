"""Lightweight stand-ins for LangChain/LangGraph objects used across the tests."""

from typing import Any, Dict, Iterable, List


class FakeDocument:
    """Mimics a langchain_core Document: only ``metadata`` is read by the app."""

    def __init__(self, **metadata: Any) -> None:
        self.metadata: Dict[str, Any] = metadata


class FakeMessage:
    """Mimics a LangChain message: ``type`` ("ai"/"human") plus ``content``."""

    def __init__(self, message_type: str, content: Any = "") -> None:
        self.type = message_type
        self.content = content


class FakeGraph:
    """Mimics a compiled LangGraph, replaying pre-built steps from ``stream()``."""

    def __init__(self, steps: Iterable[Dict[str, Any]]) -> None:
        self._steps = list(steps)
        self.streamed_states: List[Dict[str, Any]] = []

    def stream(self, state: Dict[str, Any], stream_mode: str = "values"):
        self.streamed_states.append(state)
        yield from self._steps


def answer_graph(answer: str = "42", documents: List[FakeDocument] | None = None) -> FakeGraph:
    """Build a graph whose final step yields ``answer`` and the given documents."""
    return FakeGraph(
        [
            {"messages": [FakeMessage("human", "question")], "documents": []},
            {"messages": [FakeMessage("ai", answer)], "documents": documents or []},
        ]
    )
