"""The stamped seedbed README is the template's output, and every live one must still be it.

Intent source: the change's `tl_instruction.md` Task 4b — *"Derive the substitution from the
stamper, not by eye. Read how `stamp_project.py` renders `journey_nemawashi_template.md` and
reproduce exactly that, so the next scaffold of a fresh project produces a file identical to
these."* A stamped README is the template's output rather than a separate fact
(`single_source.md`), so a template edit that does not reach the files it already stamped is
drift, not a deferral.

Why this file exists at all: Task 4b was **added by owner amendment** mid-change, because
`core/tools/test_spawn_satellite.py` holds exactly this guard for the *instance* seedbed README
(*"the next template edit that drifts from the file it stamps goes red here rather than shipping
into a spawn"*) and it went red on the template edit — while the eleven **project** seedbed
READMEs, stamped from the sibling template by this scaffolder, were guarded by nothing and drifted
silently. This is that guard, on this side of the pair.

The oracle is stamped-against-live, not stamped-against-template: comparing the scaffolder's output
to the template it just read proves only that the scaffolder can copy a file, and would have stayed
green through the whole drift this test exists to catch.

Reading the host repo's own `system/projects/` is a read, never a write — the same standing the
`conftest` already gives `--core`'s template reads, and the expectation for "the file it stamps"
can only come from the files it stamped.
"""

from pathlib import Path

import pytest

_INSTANCE_ROOT = Path(__file__).resolve().parents[6]
_PROJECTS = _INSTANCE_ROOT / "system" / "projects"

SEED_DATE = "2026-01-02"
README = Path("journey") / "nemawashi" / "README.md"


def _live_projects() -> list[str]:
    """Every managed project, discovered the way `journey_status.scan` discovers one — a
    directory under `system/projects/` that holds a `journey/`. Discovered rather than listed
    so a project scaffolded after this change is guarded from the day it exists.
    """
    if not _PROJECTS.is_dir():
        return []
    return sorted(
        entry.name
        for entry in _PROJECTS.iterdir()
        if entry.is_dir() and (entry / "journey").is_dir()
    )


@pytest.mark.parametrize("name", _live_projects())
def test_stamped_seedbed_readme_is_byte_identical_to_the_live_projects_own(run, name):
    """Scaffolding a project of the same name reproduces that project's seedbed README exactly.

    Byte-identity, not a keyword match: the substitution is the stamper's own
    (`<project>`/`<name>`/`<scope>` → the project name), so scaffolding under the live project's
    own name needs no substitution on either side and any difference at all is drift.
    """
    result = run(
        name,
        "--placement", "internal",
        "--execution-type", "headless",
        "--test-command", "pytest tests/",
        "--date", SEED_DATE,
    )
    assert result.returncode == 0, result.stderr

    stamped = (Path(run.root) / "system" / "projects" / name / README).read_text(encoding="utf-8")
    live = (_PROJECTS / name / README).read_text(encoding="utf-8")

    assert stamped == live, (
        f"{name}'s stamped seedbed README has drifted from what the scaffolder produces today — "
        "re-stamp it from core/templates/journey_nemawashi_template.md"
    )
