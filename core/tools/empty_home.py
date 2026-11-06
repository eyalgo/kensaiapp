"""empty_home.py — the environment a test runs in when it may see nothing of the owner's home.

The rule is `core/doctrine/engineering/testing_doctrine.md` § *A test reads nothing of the machine
it runs on*. Two places give a test an empty home, and both take the environment from here so they
cannot drift apart: `pytest_guardrails.py` guard 7, for every Python test under `core/`, and
`gate_suite.py`, for a product's whole suite run on the owner's Mac, in any language. A suite run
in a container or the macOS guest already has a home that is not the owner's.

`HOME` and `USERPROFILE` point at the empty folder, and every `XDG_*` folder is dropped, because
each of them defaults under the home and a test reads through them as readily as through `HOME`.

**What is carried across is the toolchain, and nothing a test reads.** `uv`, `cargo`, `rustup`,
`npm` and Playwright each keep their tools and caches under the home by default. Given an empty home
they would download every Python, Rust toolchain, package and browser again — or, for Playwright,
fail at once: it does not fetch a browser it cannot find, so an end-to-end suite errors on every case
for a reason that has nothing to do with the test. Each one's own setting is pinned to
where it already resolves, so the tool finds what it has; an explicit setting the caller already has
wins. A test that reads one of those folders itself is still caught by the commit-time check
(`check_test_isolation.py`).
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path

__version__ = "1.1.0"


def toolchain_dirs(
    environ: Mapping[str, str], home: Path, platform: str = sys.platform
) -> dict[str, str]:
    """Where each toolchain keeps its tools and caches, resolved against the real `home` before it
    is replaced: the caller's own setting if it has one, else the tool's default on `platform`."""
    cache = Path(environ.get("XDG_CACHE_HOME") or home / ".cache")
    data = Path(environ.get("XDG_DATA_HOME") or home / ".local" / "share")
    defaults = {
        "UV_CACHE_DIR": cache / "uv",
        "UV_PYTHON_INSTALL_DIR": data / "uv" / "python",
        "CARGO_HOME": home / ".cargo",
        "RUSTUP_HOME": home / ".rustup",
        "npm_config_cache": home / ".npm",
        "PLAYWRIGHT_BROWSERS_PATH": _playwright_browsers(environ, home, cache, platform),
    }
    return {name: environ.get(name) or str(default) for name, default in defaults.items()}


def _playwright_browsers(environ: Mapping[str, str], home: Path, cache: Path, platform: str) -> Path:
    """Playwright's default browser folder: the user's cache folder on each system it supports."""
    if platform == "darwin":
        return home / "Library" / "Caches" / "ms-playwright"
    if platform == "win32":
        return Path(environ.get("LOCALAPPDATA") or home / "AppData" / "Local") / "ms-playwright"
    return cache / "ms-playwright"


def changes(environ: Mapping[str, str], real_home: Path, empty: Path) -> tuple[dict[str, str], list[str]]:
    """What to set and what to drop so a process started under `environ` sees `empty` as its home:
    `(set, unset)`."""
    to_set = {**toolchain_dirs(environ, real_home), "HOME": str(empty), "USERPROFILE": str(empty)}
    to_unset = sorted(name for name in environ if name.startswith("XDG_"))
    return to_set, to_unset
