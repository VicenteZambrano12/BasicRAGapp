"""Unit tests for the Redis-backed (fakeredis in tests) cache layer."""

import json

import pytest

from src.utils.cache import graph_cache, session_memory
from src.utils.cache.conversation_memory import (
    MAX_RECENT_TURNS,
    MAX_SUMMARY_CHARS,
    update_conversation_memory,
)
from src.utils.cache.graph_cache import (
    get_or_create_graph,
    graph_config_cache,
    graph_instance_cache,
    load_graph_config_from_cache,
    save_graph_config_to_cache,
)
from src.utils.cache.redis_client import get_cache_key, redis_client
from src.utils.cache.session_memory import get_str_field_from_cache, set_str_field_to_cache


class TestCacheKey:
    def test_key_is_colon_separated(self):
        assert get_cache_key("s1", "Andalucía", "Biología") == "s1:Andalucía:Biología"

    def test_build_cache_key_delegates_to_get_cache_key(self):
        from src.system.others.cache_key import build_cache_key

        assert build_cache_key("s1", "c", "s") == get_cache_key("s1", "c", "s")


class TestGraphConfigCache:
    def test_save_then_load_roundtrip(self):
        save_graph_config_to_cache("k", "Andalucía", "Biología")

        assert load_graph_config_from_cache("k") == {
            "category": "Andalucía",
            "subject": "Biología",
        }

    def test_load_rehydrates_from_redis_when_process_cache_is_empty(self):
        save_graph_config_to_cache("k", "Andalucía", "Biología")
        graph_config_cache.clear()

        assert load_graph_config_from_cache("k") == {
            "category": "Andalucía",
            "subject": "Biología",
        }
        # The rehydrated value is memoized back into the process-local cache.
        assert "k" in graph_config_cache

    def test_load_returns_none_for_unknown_key(self):
        assert load_graph_config_from_cache("missing") is None

    def test_backend_failures_do_not_propagate(self, monkeypatch):
        def boom(*args, **kwargs):
            raise ConnectionError("redis down")

        monkeypatch.setattr(graph_cache.redis_client, "setex", boom)
        monkeypatch.setattr(graph_cache.redis_client, "get", boom)

        save_graph_config_to_cache("k", "c", "s")
        graph_config_cache.clear()

        assert load_graph_config_from_cache("k") is None


class TestGetOrCreateGraph:
    def test_builds_and_caches_the_graph_once(self, monkeypatch):
        calls = []

        def fake_create_system(subject, community):
            calls.append((subject, community))
            return object()

        monkeypatch.setattr(
            "src.utils.create_system.create_system", fake_create_system, raising=False
        )

        first = get_or_create_graph("k", "Andalucía", "Biología")
        second = get_or_create_graph("k", "Andalucía", "Biología")

        assert first is second
        assert calls == [("Biología", "Andalucía")]
        assert graph_instance_cache["k"] is first


class TestSessionMemory:
    def test_set_then_get_roundtrip(self):
        set_str_field_to_cache("k", '{"summary": "", "recent": []}')
        assert get_str_field_from_cache("k") == '{"summary": "", "recent": []}'

    def test_get_returns_none_when_absent(self):
        assert get_str_field_from_cache("missing") is None

    def test_get_swallows_backend_errors(self, monkeypatch):
        monkeypatch.setattr(
            session_memory.redis_client,
            "get",
            lambda *a, **kw: (_ for _ in ()).throw(ConnectionError("down")),
        )
        assert get_str_field_from_cache("k") is None

    def test_set_swallows_backend_errors(self, monkeypatch):
        monkeypatch.setattr(
            session_memory.redis_client,
            "setex",
            lambda *a, **kw: (_ for _ in ()).throw(ConnectionError("down")),
        )
        set_str_field_to_cache("k", "value")  # must not raise

    def test_entries_expire(self):
        set_str_field_to_cache("k", "value")
        assert 0 < redis_client.ttl("memory:k") <= session_memory.MEMORY_TTL_SECONDS


class TestConversationMemory:
    def _memory(self, cache_key="k"):
        return json.loads(get_str_field_from_cache(cache_key))

    def test_first_turn_is_stored_verbatim(self):
        update_conversation_memory("k", "question", "answer")

        assert self._memory() == {
            "summary": "",
            "recent": [{"user": "question", "ai": "answer"}],
        }

    def test_keeps_only_the_most_recent_turns(self):
        for index in range(MAX_RECENT_TURNS + 2):
            update_conversation_memory("k", f"q{index}", f"a{index}")

        memory = self._memory()
        assert len(memory["recent"]) == MAX_RECENT_TURNS
        assert memory["recent"][0] == {"user": "q2", "ai": "a2"}

    def test_overflowing_turns_are_folded_into_the_summary(self):
        for index in range(MAX_RECENT_TURNS + 1):
            update_conversation_memory("k", f"q{index}", f"a{index}")

        assert self._memory()["summary"] == "Q: q0 | A: a0"

    def test_summary_is_truncated_to_the_configured_limit(self):
        long_text = "x" * 400
        for index in range(MAX_RECENT_TURNS + 30):
            update_conversation_memory("k", f"{long_text}{index}", f"{long_text}{index}")

        assert len(self._memory()["summary"]) <= MAX_SUMMARY_CHARS

    def test_corrupt_memory_is_reset_instead_of_raising(self):
        set_str_field_to_cache("k", "not-json")

        update_conversation_memory("k", "question", "answer")

        assert self._memory() == {
            "summary": "",
            "recent": [{"user": "question", "ai": "answer"}],
        }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, ("", [])),
        ("not-json", ("", [])),
        ('{"summary": "s", "recent": [{"user": "q", "ai": "a"}]}', ("s", [{"user": "q", "ai": "a"}])),
        ("{}", ("", [])),
    ],
)
def test_load_memory_context(monkeypatch, raw, expected):
    from src.system.chat import load_memory_context as module

    monkeypatch.setattr(module, "get_str_field_from_cache", lambda key: raw)

    assert module.load_memory_context("k") == expected
