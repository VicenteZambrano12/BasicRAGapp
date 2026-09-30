"""Unit tests for observability: correlation ids, JSON log formatting, token counting."""

import json
import logging

import pytest

from src.utils.observability.logger import (
    CorrelationIdFilter,
    JSONFormatter,
    get_correlation_id,
    reset_correlation_id,
    set_correlation_id,
)
from src.utils.observability.token_counter import TokenCounter, get_token_counter


def make_record(**extra):
    record = logging.LogRecord(
        name="tests",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


class TestCorrelationId:
    def test_generates_an_id_when_none_is_supplied(self):
        value, token = set_correlation_id()
        try:
            assert value
            assert get_correlation_id() == value
        finally:
            reset_correlation_id(token)

    def test_uses_the_incoming_id(self):
        value, token = set_correlation_id("abc-123")
        try:
            assert value == "abc-123"
            assert get_correlation_id() == "abc-123"
        finally:
            reset_correlation_id(token)

    def test_reset_restores_the_previous_value(self):
        outer_value, outer_token = set_correlation_id("outer")
        _, inner_token = set_correlation_id("inner")

        reset_correlation_id(inner_token)
        assert get_correlation_id() == outer_value

        reset_correlation_id(outer_token)
        assert get_correlation_id() is None


class TestCorrelationIdFilter:
    def test_falls_back_to_dash_outside_a_request(self):
        record = make_record()
        assert CorrelationIdFilter().filter(record) is True
        assert record.correlation_id == "-"

    def test_injects_the_active_id(self):
        _, token = set_correlation_id("abc-123")
        try:
            record = make_record()
            CorrelationIdFilter().filter(record)
            assert record.correlation_id == "abc-123"
        finally:
            reset_correlation_id(token)


class TestJSONFormatter:
    def test_emits_a_single_json_line_with_core_fields(self):
        payload = json.loads(JSONFormatter().format(make_record(correlation_id="abc")))

        assert payload["level"] == "INFO"
        assert payload["logger"] == "tests"
        assert payload["message"] == "hello world"
        assert payload["correlation_id"] == "abc"
        assert payload["line"] == 1

    def test_includes_custom_extra_fields(self):
        payload = json.loads(JSONFormatter().format(make_record(event="chat_started", session_id="s1")))

        assert payload["event"] == "chat_started"
        assert payload["session_id"] == "s1"

    def test_defaults_correlation_id_when_the_filter_did_not_run(self):
        payload = json.loads(JSONFormatter().format(make_record()))
        assert payload["correlation_id"] == "-"

    def test_serializes_exception_information(self):
        try:
            raise ValueError("boom")
        except ValueError:
            import sys

            record = make_record()
            record.exc_info = sys.exc_info()

        payload = json.loads(JSONFormatter().format(record))
        assert "ValueError: boom" in payload["exception"]

    def test_non_serializable_values_do_not_break_formatting(self):
        payload = json.loads(JSONFormatter().format(make_record(weird=object())))
        assert isinstance(payload["weird"], str)


class TestTokenCounter:
    @pytest.fixture
    def counter(self):
        return TokenCounter()

    def test_empty_text_costs_nothing(self, counter):
        assert counter.count_text("") == 0

    def test_non_empty_text_costs_at_least_one_token(self, counter):
        assert counter.count_text("hello world") >= 1

    def test_counts_plain_string_messages(self, counter):
        assert counter.count_messages([{"role": "user", "content": "hello world"}])["total"] >= 1

    def test_image_blocks_use_the_flat_estimate(self, counter):
        total = counter.count_messages(
            [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "x"}}]}]
        )["total"]
        assert total == 258

    def test_ignores_unknown_and_malformed_blocks(self, counter):
        total = counter.count_messages(
            [{"role": "user", "content": ["raw string", {"type": "audio"}, None]}]
        )["total"]
        assert total == 0

    def test_ignores_messages_without_content(self, counter):
        assert counter.count_messages([{"role": "user"}, object()])["total"] == 0

    def test_falls_back_to_word_count_without_tiktoken(self, counter):
        counter._encoding = None
        assert counter.count_text("one two three") == 3

    def test_get_token_counter_is_cached(self):
        assert get_token_counter() is get_token_counter()
