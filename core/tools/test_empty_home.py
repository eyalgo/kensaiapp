"""Tests for `empty_home.py`: the toolchain folders a test's empty home carries across.

Every home here is made up, so nothing of the machine running the tests is read.
"""
from __future__ import annotations

from pathlib import Path

import empty_home

HOME = Path("/made-up/home")


def test_playwright_browsers_are_carried_from_the_macos_cache():
    dirs = empty_home.toolchain_dirs({}, HOME, platform="darwin")
    assert dirs["PLAYWRIGHT_BROWSERS_PATH"] == "/made-up/home/Library/Caches/ms-playwright"


def test_playwright_browsers_are_carried_from_the_linux_cache():
    dirs = empty_home.toolchain_dirs({}, HOME, platform="linux")
    assert dirs["PLAYWRIGHT_BROWSERS_PATH"] == "/made-up/home/.cache/ms-playwright"


def test_playwright_browsers_follow_the_linux_cache_setting():
    dirs = empty_home.toolchain_dirs({"XDG_CACHE_HOME": "/made-up/cache"}, HOME, platform="linux")
    assert dirs["PLAYWRIGHT_BROWSERS_PATH"] == "/made-up/cache/ms-playwright"


def test_playwright_browsers_are_carried_from_the_windows_local_app_data():
    dirs = empty_home.toolchain_dirs({"LOCALAPPDATA": "/made-up/local"}, HOME, platform="win32")
    assert dirs["PLAYWRIGHT_BROWSERS_PATH"] == str(Path("/made-up/local") / "ms-playwright")


def test_a_playwright_setting_the_caller_has_wins():
    environ = {"PLAYWRIGHT_BROWSERS_PATH": "/opt/browsers"}
    dirs = empty_home.toolchain_dirs(environ, HOME, platform="darwin")
    assert dirs["PLAYWRIGHT_BROWSERS_PATH"] == "/opt/browsers"


def test_the_empty_home_sets_the_browser_folder_beside_the_other_toolchains(tmp_path):
    to_set, _ = empty_home.changes({}, HOME, tmp_path)
    assert to_set["HOME"] == str(tmp_path)
    assert to_set["PLAYWRIGHT_BROWSERS_PATH"].startswith("/made-up/home/")
    assert to_set["UV_CACHE_DIR"] == "/made-up/home/.cache/uv"
