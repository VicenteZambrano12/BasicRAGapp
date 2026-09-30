"""Integration tests for the read-only endpoints: health, config, and docs."""

import json
from datetime import timedelta

import pytest

from src.api.Endpoint import config_endpoint, docs_endpoint
from src.utils.cache import graph_config_cache, graph_instance_cache

pytestmark = pytest.mark.integration


class TestHomeEndpoint:
    def test_reports_service_status_and_cache_diagnostics(self, client):
        response = client.get("/api/")

        assert response.status_code == 200
        body = response.json()
        assert body["message"] == "PAUHelper is running"
        assert body["cached_configs"] == 0
        assert body["cached_instances"] == 0
        assert isinstance(body["redis_enabled"], bool)

    def test_cache_counters_track_the_in_process_caches(self, client):
        graph_config_cache["k"] = {"category": "c", "subject": "s"}
        graph_instance_cache["k"] = object()

        body = client.get("/api/").json()

        assert body["cached_configs"] == 1
        assert body["cached_instances"] == 1


class TestConfigEndpoint:
    def test_defaults_to_spanish(self, client):
        body = client.get("/api/config").json()

        assert "Andalucía" in body["communities"]
        assert "Biología" in body["subjects"]

    def test_returns_english_options(self, client):
        body = client.get("/api/config", params={"language": "EN"}).json()

        assert "Biology" in body["subjects"]

    def test_exposes_the_maps_used_by_the_resolvers(self, client):
        body = client.get("/api/config").json()

        assert body["subject_map"]["biology"] == {"label": "Biología", "collection": "biology"}
        assert body["community_map"]["andalucia"] == {"label": "Andalucía", "folder": "Andalucia"}

    @pytest.mark.parametrize("language", ["FR", "es", ""])
    def test_rejects_unsupported_languages(self, client, language):
        response = client.get("/api/config", params={"language": language})

        assert response.status_code == 422
        assert response.json() == {"detail": "Invalid request payload."}

    def test_unreadable_config_file_returns_500(self, client, monkeypatch, tmp_path):
        monkeypatch.setattr(config_endpoint, "CONFIG_DIRECTORY", tmp_path)

        response = client.get("/api/config")

        assert response.status_code == 500
        assert response.json()["detail"] == "Unable to load localized study configuration."

    def test_malformed_config_file_returns_500(self, client, monkeypatch, tmp_path):
        (tmp_path / "es.config.json").write_text("{not json", encoding="utf-8")
        monkeypatch.setattr(config_endpoint, "CONFIG_DIRECTORY", tmp_path)

        assert client.get("/api/config").status_code == 500


class TestDocsEndpoint:
    @pytest.fixture
    def signing(self, monkeypatch):
        """Stub GCS so the endpoint signs a predictable URL, and record the object name."""
        calls = {}

        class FakeBucket:
            def blob(self, object_name):  # pragma: no cover - not reached, signing is stubbed
                return object()

        class FakeClient:
            def bucket(self, name):
                calls["bucket_name"] = name
                return FakeBucket()

        def fake_sign(bucket, object_name, expiration, method="GET"):
            calls["object_name"] = object_name
            calls["expiration"] = expiration
            return f"https://signed.example/{object_name}"

        monkeypatch.setattr(docs_endpoint, "config", lambda key, default=None: "test-bucket")
        monkeypatch.setattr(docs_endpoint, "_get_storage_client", FakeClient)
        monkeypatch.setattr(docs_endpoint, "sign_gcs_url", fake_sign)
        return calls

    @pytest.mark.parametrize(
        ("language", "expected_object"),
        [
            ("ES", "documents/how-it-works-es.pdf"),
            ("EN", "documents/how-it-works-en.pdf"),
        ],
    )
    def test_redirects_to_the_localized_signed_url(self, client, signing, language, expected_object):
        response = client.get(
            "/api/docs/how-it-works",
            params={"language": language},
            follow_redirects=False,
        )

        assert response.status_code == 307
        assert response.headers["location"] == f"https://signed.example/{expected_object}"
        assert signing["object_name"] == expected_object
        assert signing["bucket_name"] == "test-bucket"
        assert signing["expiration"] == timedelta(minutes=15)

    def test_defaults_to_spanish(self, client, signing):
        client.get("/api/docs/how-it-works", follow_redirects=False)

        assert signing["object_name"] == "documents/how-it-works-es.pdf"

    def test_rejects_unsupported_languages(self, client, signing):
        response = client.get("/api/docs/how-it-works", params={"language": "FR"})

        assert response.status_code == 422

    def test_signing_failure_returns_502(self, client, monkeypatch):
        def boom(*args, **kwargs):
            raise RuntimeError("no token creator role")

        monkeypatch.setattr(docs_endpoint, "config", lambda key, default=None: "test-bucket")
        monkeypatch.setattr(docs_endpoint, "_get_storage_client", boom)

        response = client.get("/api/docs/how-it-works", follow_redirects=False)

        assert response.status_code == 502
        assert response.json()["detail"] == "Unable to retrieve the requested document."


def test_config_endpoint_matches_the_shipped_config_files(client):
    """The HTTP payload is the config file itself; guard against accidental drift."""
    body = client.get("/api/config").json()
    on_disk = json.loads(
        (config_endpoint.CONFIG_DIRECTORY / "es.config.json").read_text(encoding="utf-8")
    )

    assert body == on_disk
