"""behave_run.py — Behave run on a throwaway copy of a repository, and nothing about what its
outcomes mean.

WHY THIS EXISTS
    QA's red is judged by running it (`chain_development.qa_red_verdict`), and the station after
    that one runs every scenario on the final code. Both need the same thing: a fresh clone of the
    product's repository at a commit, `uv run --locked behave` in its scenario folder, and the
    clone gone once the report is read. That one responsibility sits here so neither caller carries
    it, and so what an outcome means stays with the caller that judges it.

WHAT IT GIVES BACK
    A `BehaveReport` per run: Behave's own `(location, status)` pairs in the order it reports
    them, or the reason it reported none. The status word is Behave's and the set is open, so it is
    handed back as a string and never mapped.

WHAT IT LEAVES AS IT FOUND IT
    The source repository, every worktree of it and the temporary directory's parent. Every git
    call names the clone or the source with `-C`, `uv` runs with the clone's scenario folder as its
    working directory, and the clone is removed by `shutil.rmtree` in a `finally`, never by a shell
    `cd` into it. The clone is `git clone`, not `git archive`: an archive drops the history a
    product's own checks may read (`core/roles/CROSS_ROLE.md` § *Every seat*).

WHAT IT IMPORTS
    No other tool.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

__version__ = "1.0.0"

BEHAVE_COMMAND = ("uv", "run", "--locked", "behave")
COMMAND_TEXT = " ".join(BEHAVE_COMMAND)
EXIT_NO_EXECUTABLE = 127
NO_OUTPUT = "no output"
SHORT_HASH_LENGTH = 7
SCENARIO_TYPE = "scenario"
Outcomes = tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class BehaveReport:
    """What one Behave run gave back: the outcomes it reported, or why it reported none. Exactly
    one of the two is set."""

    outcomes: Outcomes | None = None
    unavailable: str | None = None

    def __post_init__(self) -> None:
        if (self.outcomes is None) == (self.unavailable is None):
            raise ValueError("a report holds outcomes or the reason there are none, and not both")


class _Source(Enum):
    COMMIT = "commit"
    TREE = "tree"


@dataclass(frozen=True)
class Overlay:
    """The scenario folder as a commit holds it, or as a working tree holds it."""

    source: _Source
    where: str

    @classmethod
    def commit(cls, sha: str) -> Overlay:
        return cls(_Source.COMMIT, sha)

    @classmethod
    def tree(cls, worktree: str) -> Overlay:
        return cls(_Source.TREE, worktree)


def _first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def _unavailable(exit_status: int, printed: str) -> str:
    return f"{COMMAND_TEXT}, exit {exit_status}, {printed or NO_OUTPUT}"


def _relative_location(location: str, scenario_folder: Path) -> str:
    """Behave's `features/<file>.feature:<line>`, relative to the scenario folder."""
    path, _, line = location.rpartition(":")
    if Path(path).is_absolute():
        path = Path(path).relative_to(scenario_folder).as_posix()
    return f"{path}:{line}"


def _read_outcomes(report_file: Path, scenario_folder: Path) -> Outcomes | None:
    """The `(location, status)` of every scenario in Behave's JSON report, in report order, or
    `None` when there is no report to read."""
    try:
        features = json.loads(report_file.read_text(encoding="utf-8"))
        return tuple(
            (_relative_location(element["location"], scenario_folder), element["status"])
            for feature in features
            for element in feature.get("elements", [])
            if element.get("type") == SCENARIO_TYPE
        )
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _git(*arguments: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *arguments], cwd=cwd, capture_output=True, text=True, check=False)


def _git_failure(base: str, done: subprocess.CompletedProcess[str]) -> str | None:
    """Why the throwaway copy at `base` could not be made, or `None` when `done` succeeded."""
    if done.returncode == 0:
        return None
    printed = _first_line(done.stderr or done.stdout) or NO_OUTPUT
    return (f"the throwaway copy at {base[:SHORT_HASH_LENGTH]} could not be made, "
            f"exit {done.returncode}, {printed}")


class ThrowawayBehave:
    """Runs Behave on a clone of a repository made for the run and removed after it. The
    temporary directory is made under `temp_parent`, the system's when it is `None`."""

    def __init__(self, *, temp_parent: str | None = None) -> None:
        self._temp_parent = temp_parent

    def base_and_red(self, *, repo: str, base: str, folder: str, red: Overlay | None,
                     environ: dict[str, str]) -> tuple[BehaveReport, BehaveReport | None]:
        """The report for the scenario folder as `base` holds it and, when `red` is given and the
        base run reported, the report for the folder as `red` holds it. `folder` is relative to
        the repository root; `environ` is what `uv` is run with."""
        scratch = Path(tempfile.mkdtemp(dir=self._temp_parent))
        try:
            return self._reports(scratch, repo, base, folder, red, environ)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

    def _reports(self, scratch: Path, repo: str, base: str, folder: str, red: Overlay | None,
                 environ: dict[str, str]) -> tuple[BehaveReport, BehaveReport | None]:
        clone = scratch / "repo"
        failure = self._clone_at(repo, base, clone, scratch)
        if failure is not None:
            return BehaveReport(unavailable=failure), None
        base_report = self._behave(clone, folder, scratch / "base.json", environ)
        if red is None or base_report.unavailable is not None:
            return base_report, None
        failure = self._overlay(clone, folder, red)
        if failure is not None:
            return base_report, BehaveReport(unavailable=failure)
        return base_report, self._behave(clone, folder, scratch / "red.json", environ)

    def _clone_at(self, repo: str, base: str, clone: Path, scratch: Path) -> str | None:
        cloned = _git("clone", "--quiet", repo, str(clone), cwd=scratch)
        failure = _git_failure(base, cloned)
        if failure is not None:
            return failure
        return _git_failure(base, _git("-C", str(clone), "checkout", "--quiet", base))

    def _behave(self, clone: Path, folder: str, report_file: Path,
                environ: dict[str, str]) -> BehaveReport:
        scenario_folder = clone / folder
        if not scenario_folder.is_dir():
            return BehaveReport(unavailable=f"{COMMAND_TEXT}, no scenario folder at {folder}")
        try:
            done = subprocess.run(
                [*BEHAVE_COMMAND, "--format", "json", "--outfile", str(report_file)],
                cwd=scenario_folder, env=environ, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, check=False)
        except FileNotFoundError:
            return BehaveReport(unavailable=_unavailable(EXIT_NO_EXECUTABLE,
                                                         "uv: command not found"))
        outcomes = _read_outcomes(report_file, scenario_folder)
        if outcomes is not None:
            return BehaveReport(outcomes=outcomes)
        if not any(scenario_folder.glob("features/**/*.feature")):
            return BehaveReport(outcomes=())
        return BehaveReport(unavailable=_unavailable(done.returncode, _first_line(done.stdout)))

    def _overlay(self, clone: Path, folder: str, red: Overlay) -> str | None:
        """Replace the scenario folder in the clone with the folder as `red` holds it. Only
        tracked files go and only listed ones come, so `.venv` and caches never travel."""
        listed = _git("-C", str(clone), "ls-files", "-z", "--", folder)
        failure = _git_failure(red.where, listed)
        if failure is not None:
            return failure
        for name in filter(None, listed.stdout.split("\0")):
            (clone / name).unlink(missing_ok=True)
        if red.source is _Source.COMMIT:
            return _git_failure(red.where, _git("-C", str(clone), "checkout", "--quiet", red.where,
                                                 "--", folder))
        return self._copy_tree(clone, folder, Path(red.where))

    def _copy_tree(self, clone: Path, folder: str, worktree: Path) -> str | None:
        listed = _git("-C", str(worktree), "ls-files", "-z", "--cached", "--others",
                      "--exclude-standard", "--", folder)
        failure = _git_failure(str(worktree), listed)
        if failure is not None:
            return failure
        for name in filter(None, listed.stdout.split("\0")):
            if (worktree / name).is_file():
                (clone / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(worktree / name, clone / name)
        return None
