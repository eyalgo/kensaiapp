"""Unit tests of the one address the tracker serves on (layer 1).

Checks SRS FR-1 and FR-2 (the tracker is started by one command and answers only this machine) and
NFR-4. Change spec rules CP-2 and NFDR QC-30 are the ones each test names.
"""

from __future__ import annotations

import ast
import ipaddress
from pathlib import Path

import main

MAIN_SOURCE = Path(main.__file__).read_text(encoding="utf-8")


def test_the_address_host_is_loopback() -> None:
    """QC-30."""
    host, port = main.ADDRESS
    assert ipaddress.ip_address(host).is_loopback
    assert isinstance(port, int) and port == 8017


def test_main_starts_on_that_one_constant() -> None:
    """CP-2: `main` reads no argument and returns `start(ADDRESS, DEFAULT_LOCATION)`."""
    tree = ast.parse(MAIN_SOURCE)
    (main_function,) = [
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"
    ]
    returns = [node for node in ast.walk(main_function) if isinstance(node, ast.Return)]
    assert len(returns) == 1
    call = returns[0].value
    assert isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    assert call.func.id == "start"
    assert [arg.id for arg in call.args if isinstance(arg, ast.Name)] == [
        "ADDRESS",
        "DEFAULT_LOCATION",
    ]
    assert len(call.args) == 2 and call.keywords == []
    assert not any(
        isinstance(node, ast.Attribute) and node.attr == "argv" for node in ast.walk(main_function)
    )


def test_no_other_address_literal_is_in_main() -> None:
    """CP-2: the host and port are written once."""
    assert MAIN_SOURCE.count("127.0.0.1") == 1
    assert MAIN_SOURCE.count("8017") == 1
