"""Characterization tests for run_loop after the login-based swap.

Interface-invariance pins, no live model call. run_loop is the entry point for
the whole optimization loop, so its "no key needed" contract is the proof-of-done
at import level: it must import with no ``ANTHROPIC_API_KEY`` and must not pull
in the ``anthropic`` SDK, and its CLI (with the required ``--model``) is unchanged.
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


def test_run_loop_imports_without_key():
    """Imports with no API key in the environment and never imports anthropic."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import scripts.run_loop, sys; "
            "assert 'anthropic' not in sys.modules, 'anthropic was imported'",
        ],
        cwd=SKILL_EVALS_ROOT,
        env=_env_without_key(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_run_loop_cli_surface():
    """The argparse CLI still requires --model and parses its documented flags."""
    result = subprocess.run(
        [sys.executable, "-m", "scripts.run_loop", "--help"],
        cwd=SKILL_EVALS_ROOT,
        env=_env_without_key(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    for flag in ("--eval-set", "--skill-path", "--holdout", "--model"):
        assert flag in result.stdout
