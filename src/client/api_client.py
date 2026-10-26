"""
Thin HTTP client wrapper around the `requests` library.

Provides a consistent interface for all API calls made in the test suite:
- Centralizes base URL and default headers in one place
- Captures response time on every request for performance assertions
- Raises on unexpected HTTP errors only when callers opt in via `raise_for_status`
- Keeps test code clean — tests describe *what* to verify, not *how* to call HTTP
"""

import logging
import time
from typing import Any

import requests
from requests import Response, Session

logger = logging.getLogger(__name__)


class APIClient:
    """Reusable HTTP client for a single base URL.

    Args:
        base_url: Root URL prepended to every relative path.
        timeout: Default request timeout in seconds (can be overridden per call).
        headers: Default headers merged into every request.
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 10,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session: Session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        if headers:
            self.session.headers.update(headers)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        """Combine base URL with a path segment."""
        return f"{self.base_url}/{path.lstrip('/')}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        raise_for_status: bool = False,
        **kwargs: Any,
    ) -> Response:
        """Execute an HTTP request and attach elapsed_ms to the response.

        Args:
            method: HTTP verb (GET, POST, PUT, PATCH, DELETE).
            path: URL path relative to base_url.
            raise_for_status: When True, raise HTTPError for 4xx/5xx responses.
            **kwargs: Forwarded directly to requests.Session.request().

        Returns:
            requests.Response with an extra `.elapsed_ms` float attribute.
        """
        url = self._url(path)
        kwargs.setdefault("timeout", self.timeout)

        logger.info("%s %s | params=%s body=%s", method, url, kwargs.get("params"), kwargs.get("json"))

        start = time.perf_counter()
        response = self.session.request(method, url, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Attach measured latency so tests can assert on it without re-parsing headers
        response.elapsed_ms = elapsed_ms  # type: ignore[attr-defined]

        logger.info(
            "%s %s -> %d (%.0f ms)",
            method,
            url,
            response.status_code,
            elapsed_ms,
        )

        if raise_for_status:
            response.raise_for_status()

        return response

    # ------------------------------------------------------------------
    # Public HTTP methods
    # ------------------------------------------------------------------

    def get(self, path: str, params: dict | None = None, **kwargs: Any) -> Response:
        """Send a GET request."""
        return self._request("GET", path, params=params, **kwargs)

    def post(self, path: str, json: dict | None = None, **kwargs: Any) -> Response:
        """Send a POST request with a JSON body."""
        return self._request("POST", path, json=json, **kwargs)

    def put(self, path: str, json: dict | None = None, **kwargs: Any) -> Response:
        """Send a PUT request with a JSON body."""
        return self._request("PUT", path, json=json, **kwargs)

    def patch(self, path: str, json: dict | None = None, **kwargs: Any) -> Response:
        """Send a PATCH request with a JSON body."""
        return self._request("PATCH", path, json=json, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Response:
        """Send a DELETE request."""
        return self._request("DELETE", path, **kwargs)

    def close(self) -> None:
        """Close the underlying requests session and release connections."""
        self.session.close()
