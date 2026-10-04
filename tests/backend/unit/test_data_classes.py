"""Unit tests for the API request/response Pydantic models."""

import pytest
from pydantic import ValidationError

from src.api.DataClasses.chat_request import ChatRequest
from src.api.DataClasses.chat_response import ChatResponse, SourceDoc
from src.api.DataClasses.create_system_request import CreateSystemRequest


class TestChatRequest:
    def test_applies_documented_defaults(self):
        request = ChatRequest(session_id="s1")

        assert request.query == ""
        assert request.image is None
        assert request.image_type == "url"
        assert request.category == "Community"
        assert request.subject == "General"
        assert request.language == "ES"

    def test_session_id_is_required(self):
        with pytest.raises(ValidationError):
            ChatRequest()

    @pytest.mark.parametrize("language", ["FR", "es", ""])
    def test_rejects_unsupported_languages(self, language):
        with pytest.raises(ValidationError):
            ChatRequest(session_id="s1", language=language)


class TestCreateSystemRequest:
    def test_applies_documented_defaults(self):
        request = CreateSystemRequest(session_id="s1")

        assert request.category == "Community"
        assert request.subject == "General"
        assert request.language == "ES"

    def test_session_id_is_required(self):
        with pytest.raises(ValidationError):
            CreateSystemRequest(category="Andalucía")


class TestChatResponse:
    def test_sources_default_to_an_empty_list(self):
        response = ChatResponse(response="hello")

        assert response.sources == []

    def test_each_response_gets_its_own_sources_list(self):
        first = ChatResponse()
        first.sources.append(SourceDoc(doc_id="a", file_name="a.pdf", url="https://x"))

        assert ChatResponse().sources == []

    def test_source_doc_page_is_optional(self):
        source = SourceDoc(doc_id="a", file_name="a.pdf", url="https://x")

        assert source.page is None

    @pytest.mark.parametrize("missing", ["doc_id", "file_name", "url"])
    def test_source_doc_required_fields(self, missing):
        payload = {"doc_id": "a", "file_name": "a.pdf", "url": "https://x"}
        payload.pop(missing)

        with pytest.raises(ValidationError):
            SourceDoc(**payload)
