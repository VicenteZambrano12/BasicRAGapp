"""Unit tests for src.system.chat.build_image_url."""

import pytest
from fastapi import HTTPException

from src.system.chat.build_image_url import build_image_url


class TestDataUrlInput:
    def test_preserves_declared_mime_type(self):
        result = build_image_url("data:image/png;base64,AAAA", "base64")
        assert result == "data:image/png;base64,AAAA"

    def test_ignores_non_image_mime_and_defaults_to_jpeg(self):
        result = build_image_url("data:application/pdf;base64,AAAA", "base64")
        assert result == "data:image/jpeg;base64,AAAA"

    def test_strips_extra_data_url_parameters(self):
        result = build_image_url("data:image/webp;charset=utf-8;base64,AAAA", "base64")
        assert result == "data:image/webp;base64,AAAA"


class TestRawBase64Input:
    @pytest.mark.parametrize(
        ("payload", "expected_mime"),
        [
            ("iVBORw0KGgoAAA", "image/png"),
            ("/9j/4AAQSkZJRg", "image/jpeg"),
            ("R0lGODlhAQABAA", "image/gif"),
            ("UklGRiQAAABXRU", "image/webp"),
            ("ZZZZunknownZZZ", "image/jpeg"),
        ],
    )
    def test_detects_mime_type_from_magic_prefix(self, payload, expected_mime):
        assert build_image_url(payload, "base64") == f"data:{expected_mime};base64,{payload}"


class TestUrlInput:
    @pytest.mark.parametrize("url", ["http://example.com/a.png", "https://example.com/a.png"])
    def test_accepts_http_and_https(self, url):
        assert build_image_url(url, "url") == url

    @pytest.mark.parametrize("url", ["ftp://example.com/a.png", "example.com/a.png", ""])
    def test_rejects_non_http_urls(self, url):
        with pytest.raises(HTTPException) as exc_info:
            build_image_url(url, "url")
        assert exc_info.value.status_code == 400


def test_unknown_image_type_is_rejected():
    with pytest.raises(HTTPException) as exc_info:
        build_image_url("whatever", "gif")
    assert exc_info.value.status_code == 400
    assert "gif" in exc_info.value.detail
