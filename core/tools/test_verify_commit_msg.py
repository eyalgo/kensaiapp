"""Characterization tests for `verify_commit_msg.py` — the pure commit-msg
checker that presence-checks the required trailer keys for a commit or merge
op and never edits the message file. Exercises the script as a subprocess
against a real throwaway git repo, the same real-git-ops pattern
`test_commit_builder.py` uses — `git rev-parse --verify MERGE_HEAD` needs a
real repo to answer truthfully, so the merge tests put a real repo into a
`--no-ff` merge (stopped before commit, via `--no-commit`) to set `MERGE_HEAD`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "verify_commit_msg.py"

COMMIT_MESSAGE_PASSING = (
    "developer: task 1 — the verifier\n"
    "\n"
    "Implements the checker.\n"
    "\n"
    "Shukuba: commit-msg-verifier — progress: builds it\n"
    "Role: Developer\n"
    "Surface: Claude Code\n"
    "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>\n"
)

# The non-required Skill-Version: trailer (commit_builder.py, added 2026-07-09)
# is not in REQUIRED_TRAILERS — the presence-checker ignores any line whose
# key isn't required, so this message must still pass.
COMMIT_MESSAGE_PASSING_WITH_SKILL_VERSION = (
    "developer: task 1 — the verifier\n"
    "\n"
    "Implements the checker.\n"
    "\n"
    "Shukuba: commit-msg-verifier — progress: builds it\n"
    "Role: Developer\n"
    "Surface: Claude Code\n"
    "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>\n"
    "Skill-Version: development-implementation@1.7.0 " + "a" * 40 + "\n"
)

COMMIT_MESSAGE_NO_TRAILERS = "no trailers here\n"

COMMIT_MESSAGE_MISSING_SURFACE_ONLY = (
    "developer: task — thing\n"
    "\n"
    "Role: Developer\n"
)

COMMIT_MESSAGE_NO_DIRECTIONAL = (
    "developer: task 1 — the verifier\n"
    "\n"
    "Role: Developer\n"
    "Surface: Claude Code\n"
)

# A key that appears only mid-line in prose, never as a line-beginning trailer,
# does NOT count as present — the intent defines presence as "a message line
# beginning with the trailer key", not a substring anywhere in the message.
# Here `Role:` occurs only inside a body sentence; `Surface:` is a real trailer.
COMMIT_MESSAGE_ROLE_ONLY_IN_PROSE = (
    "developer: task 1 — the verifier\n"
    "\n"
    "This body mentions the Role: field in passing but sets no trailer.\n"
    "\n"
    "Surface: Claude Code\n"
)

MERGE_MESSAGE_PASSING = (
    "merge: feature → main — bring in the feature\n"
    "\n"
    "-> abc1234 feature: add a thing\n"
    "\n"
    "Merge-Authorized: PM — manual\n"
    "Surface: Claude Code\n"
    "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>\n"
)

MERGE_MESSAGE_NO_TRAILERS = "merge: feature → main — bring in the feature\n"


def _init_repo(path: Path) -> str:
    """Init a throwaway git repo with a first commit; return its branch name."""

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    git("init", "-q")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.com")
    git("config", "commit.gpgsign", "false")
    (path / "seed.txt").write_text("seed\n")
    git("add", "seed.txt")
    git("commit", "-q", "-m", "seed")
    return git("rev-parse", "--abbrev-ref", "HEAD")


def _start_merge_leaving_merge_head(path: Path, main_branch: str) -> None:
    """Create a feature branch with a divergent commit and begin a `--no-ff`
    merge that stops before committing (`--no-commit`), leaving `MERGE_HEAD`
    set — exactly the state `verify_commit_msg.py`'s op-detection reads."""

    def git(*args: str) -> None:
        subprocess.run(
            ["git", "-C", str(path), *args],
            check=True, capture_output=True, text=True,
        )

    git("checkout", "-q", "-b", "feature")
    (path / "feature.txt").write_text("feature\n")
    git("add", "feature.txt")
    git("commit", "-q", "-m", "feature: add a thing")
    git("checkout", "-q", main_branch)
    git("merge", "--no-ff", "--no-commit", "feature")


def _run_checker(repo: Path, message: str) -> subprocess.CompletedProcess:
    msg_file = repo / "COMMIT_EDITMSG"
    msg_file.write_text(message)
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(msg_file)],
        cwd=str(repo),
        capture_output=True, text=True,
    )


def test_passes_builder_made_commit(tmp_path):
    # COMMIT_MESSAGE_PASSING carries no Skill-Version: line — this also
    # proves the trailer is non-required (Task 5's "passes WITHOUT the
    # line" case; no separate test, this one already pins it).
    assert "Skill-Version:" not in COMMIT_MESSAGE_PASSING
    _init_repo(tmp_path)
    proc = _run_checker(tmp_path, COMMIT_MESSAGE_PASSING)
    assert proc.returncode == 0


def test_verify_passes_with_skill_version_line(tmp_path):
    # The extra, non-required Skill-Version: line is ignored by the
    # presence-check — Role:/Surface: are what gate the commit.
    _init_repo(tmp_path)
    proc = _run_checker(tmp_path, COMMIT_MESSAGE_PASSING_WITH_SKILL_VERSION)
    assert proc.returncode == 0


def test_blocks_trailer_less_commit(tmp_path):
    _init_repo(tmp_path)
    proc = _run_checker(tmp_path, COMMIT_MESSAGE_NO_TRAILERS)
    assert proc.returncode != 0
    assert "Role:" in proc.stderr
    assert "Surface:" in proc.stderr


def test_never_rewrites_the_message(tmp_path):
    _init_repo(tmp_path)
    msg_file = tmp_path / "COMMIT_EDITMSG"
    msg_file.write_text(COMMIT_MESSAGE_NO_TRAILERS)
    before = msg_file.read_bytes()

    subprocess.run(
        [sys.executable, str(SCRIPT), str(msg_file)],
        cwd=str(tmp_path), capture_output=True, text=True,
    )

    assert msg_file.read_bytes() == before


def test_directional_trailer_never_blocks(tmp_path):
    _init_repo(tmp_path)
    proc = _run_checker(tmp_path, COMMIT_MESSAGE_NO_DIRECTIONAL)
    assert proc.returncode == 0


def test_key_present_only_in_prose_does_not_count(tmp_path):
    # `Role:` appears only inside a body sentence, never at the start of a line,
    # so it is NOT a present trailer. Presence is line-start, not substring:
    # the commit must still block, naming Role: as missing. This red-lines if
    # the presence check ever weakens from `line.startswith(key)` to `key in line`.
    _init_repo(tmp_path)
    proc = _run_checker(tmp_path, COMMIT_MESSAGE_ROLE_ONLY_IN_PROSE)
    assert proc.returncode != 0
    assert "Role:" in proc.stderr


def test_passes_builder_made_merge(tmp_path):
    main_branch = _init_repo(tmp_path)
    _start_merge_leaving_merge_head(tmp_path, main_branch)
    proc = _run_checker(tmp_path, MERGE_MESSAGE_PASSING)
    assert proc.returncode == 0


def test_blocks_trailer_less_merge(tmp_path):
    main_branch = _init_repo(tmp_path)
    _start_merge_leaving_merge_head(tmp_path, main_branch)
    proc = _run_checker(tmp_path, MERGE_MESSAGE_NO_TRAILERS)
    assert proc.returncode != 0
    assert "Merge-Authorized:" in proc.stderr
    assert "Surface:" in proc.stderr


def test_block_guidance_names_missing_trailers(tmp_path):
    # Only Surface: is missing (Role: present) — proves the guidance names
    # precisely the missing key(s), not a blanket list, and points to the
    # single sources (the builder / commit_format.md) for how to fix it.
    _init_repo(tmp_path)
    proc = _run_checker(tmp_path, COMMIT_MESSAGE_MISSING_SURFACE_ONLY)
    assert proc.returncode != 0
    assert "Surface:" in proc.stderr
    assert "Role:" not in proc.stderr
    assert "commit_builder.py" in proc.stderr or "commit_format.md" in proc.stderr


def _complete_the_merge(path: Path) -> None:
    """Finish the `--no-commit` merge so `MERGE_HEAD` is gone.

    This is the state `git commit --amend` on a merge presents to the hook, and
    it is indistinguishable from an ordinary commit made straight after a merge:
    measured 2026-09-05, both show `MERGE_HEAD` absent, `GIT_REFLOG_ACTION`
    empty, and `HEAD` carrying two parents.
    """
    subprocess.run(
        ["git", "-C", str(path), "commit", "-q", "--no-verify", "-m", "merge: feature → main"],
        check=True, capture_output=True, text=True,
    )


def test_an_amended_merge_is_checked_as_a_merge(tmp_path):
    """`ea557199` on `main` could not be repaired: amending it dropped
    `MERGE_HEAD`, so the checker demanded `Role:` — a trailer a merge must not
    carry — and the only ways past were `--no-verify` or a wrong trailer."""
    main_branch = _init_repo(tmp_path)
    _start_merge_leaving_merge_head(tmp_path, main_branch)
    _complete_the_merge(tmp_path)
    proc = _run_checker(tmp_path, MERGE_MESSAGE_PASSING)
    assert proc.returncode == 0, proc.stderr
    assert "Role:" not in proc.stderr


def test_an_amended_merge_missing_its_own_trailers_is_still_blocked(tmp_path):
    """The repair path must not become an escape from checking.

    Known limit, stated rather than hidden: a message with no trailers at all
    cannot be classified *by* its trailers, so this one is checked against the
    commit set and the guidance names `Role:`. It is still blocked, which is the
    property that matters; only the guidance is off, and only for a message that
    carries nothing to go on.
    """
    main_branch = _init_repo(tmp_path)
    _start_merge_leaving_merge_head(tmp_path, main_branch)
    _complete_the_merge(tmp_path)
    proc = _run_checker(tmp_path, MERGE_MESSAGE_NO_TRAILERS)
    assert proc.returncode != 0


def test_an_ordinary_commit_after_a_merge_is_still_a_commit(tmp_path):
    """The case git state cannot distinguish from an amend. It must keep the
    commit rules, so the fix may not simply treat a two-parent HEAD as a merge."""
    main_branch = _init_repo(tmp_path)
    _start_merge_leaving_merge_head(tmp_path, main_branch)
    _complete_the_merge(tmp_path)
    proc = _run_checker(tmp_path, COMMIT_MESSAGE_NO_TRAILERS)
    assert proc.returncode != 0
    assert "Role:" in proc.stderr
