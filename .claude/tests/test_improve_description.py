"""Characterization tests for improve_description after the login-based swap.

Interface-invariance pins, no live model call. Each runs in a fresh subprocess
with ``ANTHROPIC_API_KEY`` stripped so the "runs for a login-only user" contract
is checked directly: the module must import with no key present and must not
pull in the ``anthropic`` SDK, and its CLI surface must be unchanged.
"""

import os
import subprocess
import sys
from pathlib import Path

SKILL_EVALS_ROOT = Path(__file__).resolve().parent.parent


def _env_without_key() -> dict:
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)
    return env


def test_improve_description_imports_without_key():
    """Imports with no API key in the environment and never imports anthropic."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import scripts.improve_description, sys; "
            "assert 'anthropic' not in sys.modules, 'anthropic was imported'",
        ],
        cwd=SKILL_EVALS_ROOT,
        env=_env_without_key(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_improve_description_cli_surface():
    """The argparse CLI still parses its documented flags (interface invariance)."""
    result = subprocess.run(
        [sys.executable, "-m", "scripts.improve_description", "--help"],
        cwd=SKILL_EVALS_ROOT,
        env=_env_without_key(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    for flag in ("--eval-results", "--skill-path", "--history", "--model", "--verbose"):
        assert flag in result.stdout
