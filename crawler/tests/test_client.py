import pytest

from crawler.app.client import JsonHttpClient


class FakeResponse:
    def __init__(self, payload=None, status_error=None, json_error=None):
        self._payload = payload
        self._status_error = status_error
        self._json_error = json_error

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error

    def json(self):
        if self._json_error:
            raise self._json_error
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, timeout):
        self.calls.append((url, timeout))
        return self.response


def test_fetch_json_returns_payload():
    session = FakeSession(FakeResponse(payload={"products": []}))
    client = JsonHttpClient(session=session, timeout_seconds=3)

    payload = client.fetch_json("https://dummyjson.com/products")

    assert payload == {"products": []}
    assert session.calls == [("https://dummyjson.com/products", 3)]


def test_fetch_json_wraps_request_errors():
    session = FakeSession(FakeResponse(status_error=RuntimeError("boom")))
    client = JsonHttpClient(session=session, timeout_seconds=3)

    with pytest.raises(RuntimeError, match="https://dummyjson.com/products"):
        client.fetch_json("https://dummyjson.com/products")


def test_fetch_json_rejects_non_object_payload():
    session = FakeSession(FakeResponse(payload=[{"id": 1}]))
    client = JsonHttpClient(session=session, timeout_seconds=3)

    with pytest.raises(ValueError, match="JSON object"):
        client.fetch_json("https://dummyjson.com/products")
