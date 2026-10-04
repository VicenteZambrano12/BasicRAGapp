"""Unit tests for src.system.chat.build_sources."""

import pytest

from src.system.chat import build_sources as build_sources_module
from src.system.chat.build_sources import build_sources
from tests.backend.factories import FakeDocument

OMIT = object()


@pytest.fixture
def signed_urls(monkeypatch):
    """Replace GCS signing with a deterministic stub and record every call."""
    calls = []

    def fake_sign(bucket_name, object_name):
        calls.append((bucket_name, object_name))
        return f"https://signed.example/{bucket_name}/{object_name}"

    monkeypatch.setattr(build_sources_module, "_sign_url", fake_sign)
    return calls


def make_chunk(relative_path="biology/cells.pdf", **overrides):
    metadata = {
        "relative_path": relative_path,
        "bucket_name": "bucket",
        "object_name": "documents/biology/cells.pdf",
        "file_name": "cells.pdf",
        "page_number": 3,
    }
    if relative_path is not OMIT:
        metadata["object_name"] = f"documents/{relative_path}"
    for key, value in {"relative_path": relative_path, **overrides}.items():
        if value is OMIT:
            metadata.pop(key, None)
        else:
            metadata[key] = value
    return FakeDocument(**metadata)


def test_maps_metadata_onto_source_doc(signed_urls):
    sources = build_sources([make_chunk()])

    assert len(sources) == 1
    source = sources[0]
    assert source.doc_id == "biology/cells.pdf"
    assert source.file_name == "cells.pdf"
    assert source.page == 3
    assert source.url == "https://signed.example/bucket/documents/biology/cells.pdf"


def test_deduplicates_chunks_keeping_the_first_page_seen(signed_urls):
    sources = build_sources(
        [
            make_chunk(page_number=3),
            make_chunk(page_number=9),
            make_chunk(relative_path="biology/genetics.pdf", file_name="genetics.pdf"),
        ]
    )

    assert [s.doc_id for s in sources] == ["biology/cells.pdf", "biology/genetics.pdf"]
    assert sources[0].page == 3
    assert len(signed_urls) == 2


@pytest.mark.parametrize("missing_field", ["relative_path", "bucket_name", "object_name"])
def test_skips_chunks_with_incomplete_metadata(signed_urls, missing_field):
    assert build_sources([make_chunk(**{missing_field: OMIT})]) == []
    assert signed_urls == []


def test_skips_chunks_whose_url_cannot_be_signed(monkeypatch):
    def failing_sign(bucket_name, object_name):
        raise RuntimeError("no credentials")

    monkeypatch.setattr(build_sources_module, "_sign_url", failing_sign)

    assert build_sources([make_chunk()]) == []


def test_file_name_falls_back_to_doc_id(signed_urls):
    sources = build_sources([make_chunk(file_name=OMIT)])
    assert sources[0].file_name == "biology/cells.pdf"


def test_page_is_optional(signed_urls):
    sources = build_sources([make_chunk(page_number=OMIT)])
    assert sources[0].page is None


def test_empty_input_returns_empty_list(signed_urls):
    assert build_sources([]) == []
