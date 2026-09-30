"""Unit tests for graph state helpers and the vision/prompt/signing utilities."""

from datetime import timedelta
from importlib import import_module

import pytest
from google.cloud.exceptions import NotFound

from src.utils.chat.image_read import image_read
from src.utils.create_system import prompt_loader as prompt_loader_module
from src.utils.create_system.prompt_loader import load_system_prompt
from src.utils.create_system.state import extract_query_text
from src.utils.gcs_signing import sign_gcs_url
from tests.backend.factories import FakeMessage

# src.utils.chat re-exports the image_read *function*, which shadows the submodule
# of the same name, so the module has to be fetched explicitly for patching.
image_read_module = import_module("src.utils.chat.image_read")


class TestExtractQueryText:
    def test_returns_empty_string_for_missing_message(self):
        assert extract_query_text(None) == ""

    def test_returns_plain_string_content(self):
        assert extract_query_text(FakeMessage("human", "¿Qué es la mitosis?")) == (
            "¿Qué es la mitosis?"
        )

    def test_joins_text_blocks_of_multimodal_content(self):
        message = FakeMessage(
            "human",
            [
                {"type": "text", "text": "describe"},
                {"type": "image_url", "image_url": {"url": "data:..."}},
                {"type": "text", "text": "this"},
            ],
        )
        assert extract_query_text(message) == "describe this"

    def test_returns_empty_string_when_only_non_text_blocks(self):
        message = FakeMessage("human", [{"type": "image_url", "image_url": {}}, "raw"])
        assert extract_query_text(message) == ""

    def test_returns_empty_string_for_unsupported_content(self):
        assert extract_query_text(FakeMessage("human", {"unexpected": True})) == ""


class FakeBlob:
    def __init__(self, text=None, error=None):
        self._text = text
        self._error = error
        self.signed_url_kwargs = None

    def download_as_text(self, encoding="utf-8"):
        if self._error:
            raise self._error
        return self._text

    def generate_signed_url(self, **kwargs):
        self.signed_url_kwargs = kwargs
        return "https://signed.example/object"


class FakeBucket:
    def __init__(self, blob):
        self._blob = blob
        self.requested_object = None

    def blob(self, object_name):
        self.requested_object = object_name
        return self._blob


class TestSignGcsUrl:
    def test_signs_directly_with_key_file_credentials(self, monkeypatch):
        class KeyFileCredentials:
            def sign_bytes(self, message):  # presence of this method is what matters
                return b""

        monkeypatch.setattr("google.auth.default", lambda: (KeyFileCredentials(), "project"))
        blob = FakeBlob()

        url = sign_gcs_url(FakeBucket(blob), "documents/a.pdf", timedelta(minutes=15))

        assert url == "https://signed.example/object"
        assert blob.signed_url_kwargs == {
            "version": "v4",
            "expiration": timedelta(minutes=15),
            "method": "GET",
        }

    def test_signs_via_iam_api_for_attached_service_accounts(self, monkeypatch):
        class AttachedCredentials:
            service_account_email = "app@project.iam.gserviceaccount.com"
            token = "ya29.token"
            refreshed = False

            def refresh(self, request):
                type(self).refreshed = True

        monkeypatch.setattr("google.auth.default", lambda: (AttachedCredentials(), "project"))
        monkeypatch.setattr(
            "src.utils.gcs_signing.google_auth_requests.Request", lambda: object()
        )
        blob = FakeBlob()

        sign_gcs_url(FakeBucket(blob), "documents/a.pdf", timedelta(minutes=5), method="PUT")

        assert AttachedCredentials.refreshed is True
        assert blob.signed_url_kwargs["method"] == "PUT"
        assert blob.signed_url_kwargs["service_account_email"] == (
            "app@project.iam.gserviceaccount.com"
        )
        assert blob.signed_url_kwargs["access_token"] == "ya29.token"


class TestImageRead:
    def test_uses_the_vertex_endpoint_when_configured(self, monkeypatch):
        monkeypatch.setattr(image_read_module, "is_configured", lambda: True)
        monkeypatch.setattr(image_read_module, "vertex_image_read", lambda url: "vertex says")
        monkeypatch.setattr(image_read_module, "gemini_image_read", lambda url: "gemini says")

        assert image_read("https://example.com/a.png") == "vertex says"

    def test_falls_back_to_gemini_when_vertex_fails(self, monkeypatch):
        def boom(url):
            raise RuntimeError("endpoint 503")

        monkeypatch.setattr(image_read_module, "is_configured", lambda: True)
        monkeypatch.setattr(image_read_module, "vertex_image_read", boom)
        monkeypatch.setattr(image_read_module, "gemini_image_read", lambda url: "gemini says")

        assert image_read("https://example.com/a.png") == "gemini says"

    def test_uses_gemini_when_vertex_is_not_configured(self, monkeypatch):
        monkeypatch.setattr(image_read_module, "is_configured", lambda: False)
        monkeypatch.setattr(image_read_module, "gemini_image_read", lambda url: "gemini says")

        assert image_read("https://example.com/a.png") == "gemini says"


class TestLoadSystemPrompt:
    @pytest.fixture
    def gcs(self, monkeypatch):
        """Stub the GCS client and return a setter for the blob it should serve."""
        state = {}

        class FakeClient:
            def bucket(self, name):
                state["bucket_name"] = name
                return state["bucket"]

        monkeypatch.setattr(prompt_loader_module, "config", lambda key, default=None: "test-bucket")
        monkeypatch.setattr(prompt_loader_module, "_get_storage_client", FakeClient)

        def install(blob):
            state["bucket"] = FakeBucket(blob)
            return state

        return install

    def test_reads_the_community_and_subject_specific_object(self, gcs):
        blob = FakeBlob(text="Eres un tutor de Biología")
        state = gcs(blob)

        result = load_system_prompt("Biología", "Andalucía", "biology")

        assert result == "Eres un tutor de Biología"
        assert state["bucket_name"] == "test-bucket"
        assert state["bucket"].requested_object == "prompts/Andalucia/biology_andalucia.txt"

    def test_maps_collection_names_to_camel_case_file_prefixes(self, gcs):
        state = gcs(FakeBlob(text="prompt"))

        load_system_prompt("Historia del Arte", "Comunidad de Madrid", "arthistory")

        assert state["bucket"].requested_object == "prompts/Madrid/artHistory_madrid.txt"

    def test_missing_object_falls_back_to_a_generic_prompt(self, gcs):
        gcs(FakeBlob(error=NotFound("missing")))

        result = load_system_prompt("Biología", "Andalucía", "biology")

        assert "Biología" in result
        assert "Andalucía" in result

    def test_unexpected_errors_also_fall_back(self, gcs):
        gcs(FakeBlob(error=RuntimeError("network")))

        assert load_system_prompt("Física", "Galicia", "physics").startswith("Eres un tutor")
