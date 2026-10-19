"""The guards the hook suite inherits from `core/tools/pytest_guardrails.py`.

`.claude/hooks/` is one of the three folders the launchers project's test command runs, beside
`core/launchers/` and `core/tools/`, and a guard reaches a folder's tests only by being imported
into that folder's `conftest.py`. So this suite checks the effect of each import where one is owed.

The Ollama guard is owed because the change that made `ollama` a provider promised that every suite
under the card's test command runs with `KENSAIAPP_OLLAMA_URL` pointed at an endpoint the test
controls, or at one where nothing listens — never the owner's live server at
`http://localhost:11434`.
"""

from __future__ import annotations

import os
import socket
import urllib.parse

import pytest


def test_the_ollama_address_points_where_nothing_listens():
    address = urllib.parse.urlsplit(os.environ.get("KENSAIAPP_OLLAMA_URL", ""))

    assert address.scheme == "http"
    assert address.hostname == "127.0.0.1"
    with pytest.raises(ConnectionRefusedError):
        socket.create_connection((address.hostname, address.port), timeout=5).close()
