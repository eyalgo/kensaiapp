"""The server way in: send an HTTP request and give a step the response, through `httpx`."""

from __future__ import annotations

import httpx

TIMEOUT_SECONDS = 10.0


def request_page(url: str) -> httpx.Response:
    """GET `url` and give back the response."""
    return httpx.get(url, timeout=TIMEOUT_SECONDS)
