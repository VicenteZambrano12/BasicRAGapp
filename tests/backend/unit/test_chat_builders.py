"""Unit tests for the pure chat message/state builders."""

import pytest

from src.system.chat.build_chat_state import build_chat_state
from src.system.chat.build_memory_user_content import build_memory_user_content
from src.system.chat.build_message_content import build_message_content


class TestBuildMessageContent:
    def test_empty_query_produces_no_content(self):
        content, memory = build_message_content("")
        assert content == []
        assert memory == ""

    def test_text_query_becomes_a_text_block(self):
        content, memory = build_message_content("¿Qué es la fotosíntesis?")
        assert content == [{"type": "text", "text": "¿Qué es la fotosíntesis?"}]
        assert memory == "Q: ¿Qué es la fotosíntesis?"

    def test_memory_snippet_is_truncated_to_100_chars(self):
        query = "x" * 250
        content, memory = build_message_content(query)
        assert content[0]["text"] == query
        assert memory == f"Q: {'x' * 100}"


class TestBuildChatState:
    def test_minimal_state_has_instruction_then_user_message(self):
        state = build_chat_state(
            message_content=[{"type": "text", "text": "hola"}],
            intermediate_memory="",
            memory_summary="",
            recent_turns=[],
            language_instruction="Responde siempre en español.",
        )
        assert state["messages"] == [
            {"role": "system", "content": "Responde siempre en español."},
            {"role": "user", "content": [{"type": "text", "text": "hola"}]},
        ]

    def test_visual_context_and_summary_are_injected_as_system_messages(self):
        state = build_chat_state(
            message_content=[],
            intermediate_memory="Image: a cell diagram",
            memory_summary="Earlier we covered mitosis",
            recent_turns=[],
        )
        system_contents = [m["content"] for m in state["messages"] if m["role"] == "system"]
        assert "Visual context extracted: Image: a cell diagram" in system_contents
        assert "Previous context summary: Earlier we covered mitosis" in system_contents

    def test_recent_turns_expand_to_alternating_roles_in_order(self):
        state = build_chat_state(
            message_content=[{"type": "text", "text": "now"}],
            intermediate_memory="",
            memory_summary="",
            recent_turns=[
                {"user": "q1", "ai": "a1"},
                {"user": "q2", "ai": "a2"},
            ],
        )
        assert [(m["role"], m["content"]) for m in state["messages"][1:-1]] == [
            ("user", "q1"),
            ("assistant", "a1"),
            ("user", "q2"),
            ("assistant", "a2"),
        ]

    def test_current_message_is_always_last(self):
        state = build_chat_state(
            message_content=[{"type": "text", "text": "last"}],
            intermediate_memory="ctx",
            memory_summary="sum",
            recent_turns=[{"user": "q", "ai": "a"}],
        )
        assert state["messages"][-1] == {
            "role": "user",
            "content": [{"type": "text", "text": "last"}],
        }


class TestBuildMemoryUserContent:
    @pytest.mark.parametrize(
        ("query", "has_image", "intermediate", "expected"),
        [
            ("q", True, "Image: chart", "Image: chart"),
            ("q", True, "", "q"),
            ("q", False, "Image: chart", "q"),
            ("", True, "", ""),
            ("", False, "", ""),
        ],
    )
    def test_selects_expected_memory_payload(self, query, has_image, intermediate, expected):
        assert build_memory_user_content(query, has_image, intermediate) == expected
