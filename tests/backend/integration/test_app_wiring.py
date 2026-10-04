"""Integration tests for the request-logging middleware and the global exception handlers."""

import pytest

from src.api.Endpoint import chat_endpoint, home_endpoint

pytestmark = pytest.mark.integration

CORRELATION_ID_HEADER = "X-Request-ID"


@pytest.fixture(autouse=True)
def qdrant_reachable(monkeypatch):
    """These tests exercise middleware/error handling, not Qdrant connectivity; stub it as up."""

    class FakeQdrantClient:
        def get_collections(self):
            return object()

    monkeypatch.setattr(home_endpoint, "get_qdrant_client", lambda timeout=None: FakeQdrantClient())


class TestCorrelationIdPropagation:
    def test_generates_a_correlation_id_when_none_is_sent(self, client):
        response = client.get("/api/")

        assert response.headers[CORRELATION_ID_HEADER]

    def test_echoes_the_incoming_correlation_id(self, client):
        response = client.get("/api/", headers={CORRELATION_ID_HEADER: "client-supplied-id"})

        assert response.headers[CORRELATION_ID_HEADER] == "client-supplied-id"

    def test_each_request_gets_a_distinct_generated_id(self, client):
        first = client.get("/api/").headers[CORRELATION_ID_HEADER]
        second = client.get("/api/").headers[CORRELATION_ID_HEADER]

        assert first != second

    def test_the_header_is_exposed_to_browsers_via_cors(self, client):
        response = client.get("/api/", headers={"Origin": "https://app.example"})

        assert "X-Request-ID" in response.headers["access-control-expose-headers"]
        assert response.headers["access-control-allow-origin"] == "https://app.example"

    def test_the_header_is_set_on_error_responses_too(self, client):
        response = client.get("/api/config", params={"language": "FR"})

        assert response.status_code == 422
        assert response.headers[CORRELATION_ID_HEADER]


class TestExceptionHandlers:
    def test_unhandled_errors_are_masked_as_a_generic_500(self, lenient_client, monkeypatch):
        def boom(data):
            raise RuntimeError("database password is hunter2")

        monkeypatch.setattr(chat_endpoint, "execute_chat", boom)

        response = lenient_client.post("/api/chat", json={"session_id": "s1", "query": "q"})

        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error."}
        assert "hunter2" not in response.text

    def test_validation_errors_do_not_leak_the_payload_shape(self, client):
        response = client.post("/api/chat", json={"query": 123})

        assert response.status_code == 422
        assert response.json() == {"detail": "Invalid request payload."}

    def test_http_exceptions_keep_their_status_and_detail(self, client):
        response = client.post("/api/chat", json={"session_id": "s1", "query": "q"})

        assert response.status_code == 400
        assert "Call /create_system first" in response.json()["detail"]


def test_unknown_routes_return_404(client):
    assert client.get("/api/does-not-exist").status_code == 404
