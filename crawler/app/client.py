from typing import Any, Protocol

import requests


class HttpSession(Protocol):
    def get(self, url: str, timeout: float):
        ...


class JsonHttpClient:
    def __init__(self, session: HttpSession | None = None, timeout_seconds: float = 10):
        self._session = session or requests.Session()
        self._timeout_seconds = timeout_seconds

    def fetch_json(self, url: str) -> dict[str, Any]:
        try:
            response = self._session.get(url, timeout=self._timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch JSON from {url}: {exc}") from exc

        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object from {url}")

        return payload
