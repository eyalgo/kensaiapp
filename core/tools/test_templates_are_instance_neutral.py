"""A template may not carry a fact about the instance it happens to live in.

WHY THIS EXISTS
    A template's value is not that it saves typing — it is that it *cannot* leak the sibling's
    facts. `ai_responsibility_template.md` has `<scope>`; it is structurally incapable of naming
    another instance's domain. A filled-in file copied from a sibling has no such property, which
    is why `kensaiapp-spawn` v1.0.0 (withdrawn, `f6d5c0a`) carried this instance's trading-domain
    section into a fresh one the moment it was told to "start from the host's".

    That guarantee is worth exactly as much as its weakest template. `spawn-satellite`'s integrity
    pass (`2503e12`) found one that had lost it: `project-templates/setup_seed_template.md` cited
    `system/projects/product-definition/…` — this instance's own project — inside a file
    `project-stamp` stamps into the first seed of every project of every instance. Every
    satellite spawned anywhere inherited it, and nothing failed.

    So the guarantee stops being a habit and becomes a check. Nothing else in the instance counts
    or resolves anything (`system/nemawashi/2026-07-30_core-doctrine-consistency-audit.md`,
    finding 7 and its pattern (c)); this covers one narrow, high-value slice of that gap.

WHAT COUNTS AS A LEAK
    Two shapes, both concrete rather than judgemental:

    - a **known instance name** — every satellite `system/satellites.md` lists and every name its
      § *Names a release must not carry* declares, this host's own among them — anywhere in a
      template, matched whole and without regard to case: a name is the same fact however it is
      capitalised. The names are read from `system/`, which a release does not carry, through
      `check_vendor_neutrality._declared_names`, so this file names none of them and the two checks
      cannot disagree about what a name is;
    - a path naming a **real project of this instance** — `system/projects/<concrete-name>/` —
      as opposed to the placeholder `system/projects/<name>/`, which is exactly what a template
      is supposed to say.

    The project names are read off `system/projects/` at run time rather than hardcoded, so a
    project added tomorrow is covered without anyone remembering to add it here. The instance
    names are read at run time the same way.

    **In a clone with no `system/` there are no names to read**, so both checks are skipped there and
    say why, rather than passing over an empty list — a pass would read as a check that held.

WHAT IS DELIBERATELY NOT A LEAK
    A placeholder (`<name>`, `<project>`, `<instance>`, `<scope>`), and a path into `<CORE>` —
    core is shared by every instance, so naming it names nothing instance-specific.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from check_vendor_neutrality import _declared_names, _name_pattern

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "core" / "templates"
PROJECTS = REPO / "system" / "projects"

ROSTER = REPO / "system" / "satellites.md"

NEEDS_SYSTEM = pytest.mark.skipif(
    not (REPO / "system").is_dir(),
    reason="this clone carries no system/, so there are no instance or project names to check",
)


def _known_instances() -> list[str]:
    """Every name the roster gives — a template naming one has copied a fact from it."""
    return sorted(_declared_names(REPO))


def _templates() -> list[Path]:
    return sorted(p for p in TEMPLATES.rglob("*.md") if p.is_file())


def _real_project_names() -> list[str]:
    if not PROJECTS.is_dir():
        return []
    return sorted(p.name for p in PROJECTS.iterdir() if p.is_dir() and not p.name.startswith("."))


def test_there_are_templates_to_check():
    """Guard the guard: an empty glob would make every test below vacuously pass."""
    assert _templates(), f"no templates found under {TEMPLATES}"
    if (REPO / "system").is_dir():
        assert _real_project_names(), f"no projects found under {PROJECTS}"
    if ROSTER.is_file():
        assert _known_instances(), f"{ROSTER} exists and yields no name"


@NEEDS_SYSTEM
@pytest.mark.parametrize("template", _templates(), ids=lambda p: p.name)
def test_template_names_no_instance(template: Path):
    text = template.read_text(encoding="utf-8")
    hits = [name for name in _known_instances() if _name_pattern(name).search(text)]
    assert not hits, (
        f"{template.relative_to(REPO)} names {hits} — a template must hold the shape, never the "
        f"facts of the instance it happens to sit in."
    )


@NEEDS_SYSTEM
@pytest.mark.parametrize("template", _templates(), ids=lambda p: p.name)
def test_template_names_no_real_project_of_this_instance(template: Path):
    """`system/projects/<name>/` is the shape and is fine; `system/projects/tools/` is a fact."""
    text = template.read_text(encoding="utf-8")
    real = _real_project_names()
    hits = sorted({
        m.group(1)
        for m in re.finditer(r"system/projects/([A-Za-z0-9_.-]+)/", text)
        if m.group(1) in real
    })
    assert not hits, (
        f"{template.relative_to(REPO)} points into this instance's own project(s) {hits}. "
        f"Every instance stamps from this file, so each one would inherit that path. Use the "
        f"placeholder `system/projects/<name>/`, or drop the pointer."
    )
