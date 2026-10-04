"""Unit tests for the chat/create_system orchestration helpers."""

import pytest
from fastapi import HTTPException

from src.system.chat import ensure_graph_available as ensure_module
from src.system.chat.ensure_graph_available import ensure_graph_available
from src.system.chat.update_memory_and_log import update_memory_and_log
from src.system.create_system import ensure_cached_graph as ensure_cached_module
from src.system.create_system import initialize_and_cache_graph as initialize_module
from src.system.create_system.build_create_system_response import build_create_system_response
from src.system.create_system.ensure_cached_graph import ensure_cached_graph
from src.system.create_system.initialize_and_cache_graph import initialize_and_cache_graph
from src.utils.cache import graph_instance_cache, load_graph_config_from_cache


class TestEnsureGraphAvailable:
    def test_rejects_chat_before_create_system(self, monkeypatch):
        monkeypatch.setattr(ensure_module, "load_graph_config_from_cache", lambda key: None)

        with pytest.raises(HTTPException) as exc_info:
            ensure_graph_available("k", "Andalucía", "Biología")

        assert exc_info.value.status_code == 400
        assert "Call /create_system first" in exc_info.value.detail

    def test_returns_the_cached_graph(self, monkeypatch):
        sentinel = object()
        monkeypatch.setattr(ensure_module, "load_graph_config_from_cache", lambda key: {"a": 1})
        monkeypatch.setattr(ensure_module, "get_or_create_graph", lambda *args: sentinel)

        assert ensure_graph_available("k", "Andalucía", "Biología") is sentinel

    def test_graph_construction_failure_becomes_500(self, monkeypatch):
        def boom(*args):
            raise RuntimeError("qdrant unreachable")

        monkeypatch.setattr(ensure_module, "load_graph_config_from_cache", lambda key: {"a": 1})
        monkeypatch.setattr(ensure_module, "get_or_create_graph", boom)

        with pytest.raises(HTTPException) as exc_info:
            ensure_graph_available("k", "Andalucía", "Biología")

        assert exc_info.value.status_code == 500
        assert "qdrant unreachable" in exc_info.value.detail


class TestInitializeAndCacheGraph:
    def test_caches_instance_and_config(self, monkeypatch):
        sentinel = object()
        monkeypatch.setattr(initialize_module, "create_system", lambda subject, community: sentinel)

        initialize_and_cache_graph("k", "Andalucía", "Biología")

        assert graph_instance_cache["k"] is sentinel
        assert load_graph_config_from_cache("k") == {
            "category": "Andalucía",
            "subject": "Biología",
        }

    def test_propagates_construction_errors(self, monkeypatch):
        def boom(subject, community):
            raise RuntimeError("bad collection")

        monkeypatch.setattr(initialize_module, "create_system", boom)

        with pytest.raises(RuntimeError):
            initialize_and_cache_graph("k", "Andalucía", "Biología")

        assert "k" not in graph_instance_cache


def test_ensure_cached_graph_warms_the_instance_cache(monkeypatch):
    calls = []
    monkeypatch.setattr(
        ensure_cached_module, "get_or_create_graph", lambda *args: calls.append(args)
    )

    ensure_cached_graph("k", "Andalucía", "Biología")

    assert calls == [("k", "Andalucía", "Biología")]


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        ("ES", "¡Hola! ¿Cómo puedo ayudarte a estudiar tu examen de Biología?"),
        ("EN", "Hello! How can I help you study for your Biología exam?"),
    ],
)
def test_build_create_system_response(language, expected):
    assert build_create_system_response("Biología", language) == {"response": expected}


class StubTokenCounter:
    def count_text(self, text):
        return len(text.split())


class TestUpdateMemoryAndLog:
    def test_persists_the_turn(self, monkeypatch):
        calls = []
        monkeypatch.setattr(
            "src.system.chat.update_memory_and_log.update_conversation_memory",
            lambda *args: calls.append(args),
        )

        update_memory_and_log(StubTokenCounter(), "k", "question", "answer", 10, 2)

        assert calls == [("k", "question", "answer")]

    @pytest.mark.parametrize(
        ("user_content", "response"),
        [("", "answer"), ("question", ""), ("", "")],
    )
    def test_skips_persisting_incomplete_turns(self, monkeypatch, user_content, response):
        calls = []
        monkeypatch.setattr(
            "src.system.chat.update_memory_and_log.update_conversation_memory",
            lambda *args: calls.append(args),
        )

        update_memory_and_log(StubTokenCounter(), "k", user_content, response, 10, 2)

        assert calls == []

    def test_memory_failures_do_not_break_the_turn(self, monkeypatch):
        def boom(*args):
            raise ConnectionError("redis down")

        monkeypatch.setattr(
            "src.system.chat.update_memory_and_log.update_conversation_memory", boom
        )

        update_memory_and_log(StubTokenCounter(), "k", "question", "answer", 10, 2)
