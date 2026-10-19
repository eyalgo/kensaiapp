#!/usr/bin/env python3
"""An instance reads its own journey state as one HTML page.

WHY THIS EXISTS
    An instance's journey state — its 根回し Nemawashi seedbed, its 宿場 Shukuba router, and each
    project's `journey/` — is only visible today by walking folders by hand. Every fact already
    sits on disk (`core/docs/michi_agari.md` owns the model), so nothing needs a service or a
    store: what was missing was a reader. This walks one instance root, builds a data model of
    its journey state, applies the model's own invariants as checks, and renders one
    self-contained HTML page describing that instance and naming every place it has drifted
    from its own model.

    Read-only, always: the walk only reads files, and the render only builds a string. Nothing
    under this module ever writes inside a journey folder or outside the instance it was run
    against — the only write in the whole file is the CLI's own `--out` page.

WHAT IT CHECKS
    Four invariants read straight off `core/docs/michi_agari.md`:

    1. The pick invariant — a seedbed's root holds at most one seed; a root holding more than
       one is a violation. Applies to every seedbed the walk finds, the instance's
       `system/nemawashi/` included — `unpicked/`'s own count is never consulted.
    2. At most one open 宿場 Shukuba station per project.
    3. A station is open only while a 根回し Nemawashi seed is active — an open station against
       `no pick` or `empty` nemawashi state is a violation.
    4. Every active 飛び石 Tobiishi change folder holds a `change_request.md`.

WHAT IT DOES NOT DO
    Fix the drift it finds. Repairing a journey folder is the owning project's call, never this
    tool's — see the plan this module was built from
    (`docs/proposals/archive/journey-status-viewer/ad_hoc_plan.md`) § Scope fence.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

__version__ = "2.4.1"

_CHECKLIST_DONE = re.compile(r"^[ \t]*- \[x\]", re.MULTILINE)
_CHECKLIST_PENDING = re.compile(r"^[ \t]*- \[ \]", re.MULTILINE)
_H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_PRODUCT_PATH = re.compile(r"^\*\*Product path:\*\*\s*(\S+)", re.MULTILINE)


# =========================================================================================
# The model
# =========================================================================================


class NemawashiState(Enum):
    """The seedbed's pick state — a closed set, never a free-form string."""

    ACTIVE = "active"
    NO_PICK = "no pick"
    EMPTY = "empty"


class ShukubaState(Enum):
    """The router's open state — a closed set, never a free-form string."""

    OPEN = "open"
    NONE_OPEN = "none open"


@dataclass(frozen=True)
class InstanceNemawashi:
    """The instance-level seedbed. It carries the same three states as a project's: the pick belongs to
    the seedbed rather than to the project level (`core/docs/michi_agari.md`), and being hand-picked
    changes who moves the file, not what the shape means. No `seed_title`/checklist — the instance seed
    is not walked through stations, so there is no checklist to count."""

    root_seed_count: int
    unpicked_count: int
    trail_count: int
    drop_count: int
    state: NemawashiState


@dataclass(frozen=True)
class InstanceShukuba:
    """The instance-level router — a `trail/` only; never walked, never `open`."""

    trail_count: int


@dataclass(frozen=True)
class NemawashiStatus:
    state: NemawashiState
    seed_title: str | None
    checklist_done: int
    checklist_total: int
    unpicked_count: int
    trail_count: int
    drop_count: int
    root_seed_count: int


@dataclass(frozen=True)
class ShukubaStatus:
    state: ShukubaState
    station_title: str | None
    parked_count: int
    trail_count: int
    open_count: int


@dataclass(frozen=True)
class TobiishiChange:
    name: str
    has_change_request: bool


@dataclass(frozen=True)
class TobiishiStatus:
    changes: list[TobiishiChange]
    trail_count: int
    drop_count: int


@dataclass(frozen=True)
class ProjectStatus:
    name: str
    product_path: str | None
    nemawashi: NemawashiStatus
    shukuba: ShukubaStatus
    tobiishi: TobiishiStatus


@dataclass(frozen=True)
class Violation:
    check: int
    where: str
    message: str


@dataclass(frozen=True)
class InstanceModel:
    name: str
    root: Path
    nemawashi: InstanceNemawashi
    shukuba: InstanceShukuba
    projects: list[ProjectStatus]
    violations: list[Violation]
    generated_at: datetime


# =========================================================================================
# The walk — pure reads, no writes, anywhere
# =========================================================================================


def _md_files(directory: Path) -> list[Path]:
    """`.md` files directly in `directory`, excluding `README.md`. Missing dir → empty list."""
    if not directory.is_dir():
        return []
    return sorted(
        p for p in directory.iterdir() if p.is_file() and p.suffix == ".md" and p.name != "README.md"
    )


def _count_md_files(directory: Path) -> int:
    """`.md` file count directly in `directory` (e.g. `unpicked/`, `trail/`, `parked/`)."""
    if not directory.is_dir():
        return 0
    return len([p for p in directory.iterdir() if p.is_file() and p.suffix == ".md"])


def _is_folder_seed(path: Path) -> bool:
    """A directory counts as a seed only once it holds `seed.md` directly — the one file inside
    it that is ever read as the seed (`kensaiapp_structure.md` § 2)."""
    return path.is_dir() and (path / "seed.md").is_file()


def _seed_entries(directory: Path) -> list[Path]:
    """Every 根回し Nemawashi seed directly in `directory` — a `.md` file (not `README.md`) or a
    folder holding `seed.md`. A folder with no `seed.md` is not a seed. Missing dir → empty list.

    Nemawashi-only: a 宿場 Shukuba station never takes the folder form, so `_md_files` is still
    the whole answer there.
    """
    if not directory.is_dir():
        return []

    def _is_file_seed(p: Path) -> bool:
        return p.is_file() and p.suffix == ".md" and p.name != "README.md"

    return sorted(p for p in directory.iterdir() if _is_file_seed(p) or _is_folder_seed(p))


def _seed_text_path(seed: Path) -> Path:
    """The file that holds a seed's own text — the seed itself for a file-seed, `seed.md` inside
    it for a folder-seed."""
    return seed / "seed.md" if seed.is_dir() else seed


def _count_seeds(directory: Path) -> int:
    """Nemawashi seed count directly in `directory` (e.g. `unpicked/`, `trail/`, `drop/`) — a
    `.md` file or a folder holding `seed.md`, each counted once."""
    return len(_seed_entries(directory))


def _first_h1(text: str) -> str | None:
    match = _H1.search(text)
    return match.group(1) if match else None


def _checklist_counts(text: str) -> tuple[int, int]:
    """`(done, total)` counted from `- [x]` versus `- [ ]` lines, at any indent.

    Leading whitespace is part of the match because a nested item is still an item: every
    define-the-product seed carries four indented under one parent (`core/templates/project-templates/
    setup_seed_template.md`), and a line-start anchor rendered those seeds finished with their
    nested work untouched.
    """
    done = len(_CHECKLIST_DONE.findall(text))
    pending = len(_CHECKLIST_PENDING.findall(text))
    return done, done + pending


def _pick_state(root_seed_count: int, unpicked_count: int) -> NemawashiState:
    """The seedbed's state, from the two counts — the single owner of the rule, read at both levels.

    The root answers whether an idea is active; the pool answers whether there is anything to pick.
    `empty` is therefore the narrow claim that both are bare, not merely that the root is. A root
    holding two or more is `no pick` for the same reason zero is — nothing is elected — and check 1
    reports the violation separately, so the state never has to double as an error.
    """
    if root_seed_count == 1:
        return NemawashiState.ACTIVE
    if root_seed_count == 0 and unpicked_count == 0:
        return NemawashiState.EMPTY
    return NemawashiState.NO_PICK


def _scan_instance_nemawashi(directory: Path) -> InstanceNemawashi:
    root_seed_count = len(_seed_entries(directory))
    unpicked_count = _count_seeds(directory / "unpicked")
    return InstanceNemawashi(
        root_seed_count=root_seed_count,
        unpicked_count=unpicked_count,
        trail_count=_count_seeds(directory / "trail"),
        drop_count=_count_seeds(directory / "drop"),
        state=_pick_state(root_seed_count, unpicked_count),
    )


def _scan_instance_shukuba(directory: Path) -> InstanceShukuba:
    return InstanceShukuba(trail_count=_count_md_files(directory / "trail"))


def _scan_nemawashi(directory: Path) -> NemawashiStatus:
    seeds = _seed_entries(directory)
    unpicked_count = _count_seeds(directory / "unpicked")
    trail_count = _count_seeds(directory / "trail")
    drop_count = _count_seeds(directory / "drop")
    root_seed_count = len(seeds)

    if root_seed_count == 1:
        text = _seed_text_path(seeds[0]).read_text(encoding="utf-8")
        done, total = _checklist_counts(text)
        return NemawashiStatus(
            state=NemawashiState.ACTIVE,
            seed_title=_first_h1(text),
            checklist_done=done,
            checklist_total=total,
            unpicked_count=unpicked_count,
            trail_count=trail_count,
            drop_count=drop_count,
            root_seed_count=root_seed_count,
        )

    state = _pick_state(root_seed_count, unpicked_count)
    return NemawashiStatus(
        state=state,
        seed_title=None,
        checklist_done=0,
        checklist_total=0,
        unpicked_count=unpicked_count,
        trail_count=trail_count,
        drop_count=drop_count,
        root_seed_count=root_seed_count,
    )


def _scan_shukuba(directory: Path) -> ShukubaStatus:
    open_files = _md_files(directory)
    parked_count = _count_md_files(directory / "parked")
    trail_count = _count_md_files(directory / "trail")
    open_count = len(open_files)

    station_title = None
    if open_count == 1:
        station_title = _first_h1(open_files[0].read_text(encoding="utf-8"))

    state = ShukubaState.OPEN if open_count >= 1 else ShukubaState.NONE_OPEN
    return ShukubaStatus(
        state=state,
        station_title=station_title,
        parked_count=parked_count,
        trail_count=trail_count,
        open_count=open_count,
    )


def _scan_tobiishi(directory: Path) -> TobiishiStatus:
    changes: list[TobiishiChange] = []
    trail_count = 0
    drop_count = 0
    if directory.is_dir():
        for entry in sorted(directory.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name == "trail":
                trail_count = len([p for p in entry.iterdir() if p.is_dir()])
                continue
            if entry.name == "drop":
                drop_count = len([p for p in entry.iterdir() if p.is_dir()])
                continue
            changes.append(
                TobiishiChange(
                    name=entry.name,
                    has_change_request=(entry / "change_request.md").is_file(),
                )
            )
    return TobiishiStatus(changes=changes, trail_count=trail_count, drop_count=drop_count)


def _read_product_path(project_dir: Path) -> str | None:
    project_md = project_dir / "project.md"
    if not project_md.is_file():
        return None
    match = _PRODUCT_PATH.search(project_md.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def _check_pick_invariant(label: str, root_seed_count: int) -> Violation | None:
    """Check 1 — the pick invariant. A violation iff the seedbed's root holds more than one
    seed. Takes only a label and a root-seed count — `unpicked/`'s own count is never in scope
    to be read, so it cannot be consulted by construction (T1). Applies to any seedbed —
    the instance's `system/nemawashi/` and every project's, alike (T4)."""
    if root_seed_count > 1:
        return Violation(
            check=1,
            where=label,
            message=f"{root_seed_count} seed(s) sit at the root of {label} — expected at most 1",
        )
    return None


def _check_project(project: ProjectStatus) -> list[Violation]:
    violations: list[Violation] = []
    nemawashi = project.nemawashi
    shukuba = project.shukuba

    if shukuba.open_count > 1:
        violations.append(
            Violation(
                check=2,
                where=project.name,
                message=f"{shukuba.open_count} stations open in journey/shukuba/ — expected at most 1",
            )
        )

    if shukuba.open_count >= 1 and nemawashi.state in (NemawashiState.NO_PICK, NemawashiState.EMPTY):
        violations.append(
            Violation(
                check=3,
                where=project.name,
                message=f"a station is open while nemawashi is {nemawashi.state.value}",
            )
        )

    for change in project.tobiishi.changes:
        if not change.has_change_request:
            violations.append(
                Violation(
                    check=4,
                    where=project.name,
                    message=f"tobiishi change '{change.name}' holds no change_request.md",
                )
            )

    return violations


def scan(root: str | Path, *, generated_at: datetime | None = None) -> InstanceModel:
    """Walk `root` (an instance root) and build its `InstanceModel`. Read-only — never writes."""
    root = Path(root)
    instance_nemawashi = _scan_instance_nemawashi(root / "system" / "nemawashi")
    instance_shukuba = _scan_instance_shukuba(root / "system" / "shukuba")

    violations: list[Violation] = []
    instance_check1 = _check_pick_invariant("system/nemawashi/", instance_nemawashi.root_seed_count)
    if instance_check1 is not None:
        violations.append(instance_check1)

    projects: list[ProjectStatus] = []
    projects_root = root / "system" / "projects"
    if projects_root.is_dir():
        for entry in sorted(projects_root.iterdir()):
            if not entry.is_dir():
                continue
            journey = entry / "journey"
            if not journey.is_dir():
                continue
            project = ProjectStatus(
                name=entry.name,
                product_path=_read_product_path(entry),
                nemawashi=_scan_nemawashi(journey / "nemawashi"),
                shukuba=_scan_shukuba(journey / "shukuba"),
                tobiishi=_scan_tobiishi(journey / "tobiishi"),
            )
            projects.append(project)
            project_check1 = _check_pick_invariant(project.name, project.nemawashi.root_seed_count)
            if project_check1 is not None:
                violations.append(project_check1)
            violations.extend(_check_project(project))

    return InstanceModel(
        name=root.name,
        root=root,
        nemawashi=instance_nemawashi,
        shukuba=instance_shukuba,
        projects=projects,
        violations=violations,
        generated_at=generated_at or datetime.now(timezone.utc),
    )


# =========================================================================================
# The render — one self-contained HTML string, no external references
# =========================================================================================

_CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
html, body { max-width: 100%; overflow-x: hidden; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  margin: 0; padding: 2rem;
  background: #f7f7f8; color: #1c1c1e;
  max-width: 1000px; margin-inline: auto;
  word-break: break-word;
}
header { margin-bottom: 1.5rem; }
header h1 { margin: 0 0 0.25rem; font-size: 1.4rem; }
header .generated-at { color: #6b6b70; font-size: 0.85rem; }
.violations { background: #fdecea; border: 1px solid #f4a5a0; border-radius: 8px;
  padding: 1rem 1.25rem; margin-bottom: 1.5rem; overflow-wrap: anywhere; }
.violations h2 { margin: 0 0 0.5rem; font-size: 1.05rem; color: #a02c22; }
.violation { margin: 0.25rem 0; }
.violation .check { font-weight: 600; }
.clean { background: #e9f7ef; border: 1px solid #a7d7bb; border-radius: 8px;
  padding: 1rem 1.25rem; margin-bottom: 1.5rem; color: #1e6b3c; }
.project-card { background: #ffffff; border: 1px solid #e2e2e5; border-radius: 8px;
  padding: 1rem 1.25rem; margin-bottom: 1rem; overflow-wrap: anywhere; }
.project-card h2 { margin: 0 0 0.5rem; font-size: 1.1rem; }
.product-path { color: #6b6b70; font-size: 0.8rem; margin: 0 0 0.75rem; }
.stations { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem; }
.station-block h3 { margin: 0 0 0.25rem; font-size: 0.85rem; text-transform: uppercase;
  letter-spacing: 0.03em; color: #6b6b70; }
.station-block p { margin: 0.15rem 0; font-size: 0.9rem; }
@media (prefers-color-scheme: dark) {
  body { background: #1c1c1e; color: #f2f2f4; }
  header .generated-at { color: #a0a0a6; }
  .violations { background: #3a1f1d; border-color: #7a3a34; }
  .violations h2 { color: #ff8f85; }
  .clean { background: #1c3324; border-color: #3f7a56; color: #7fe0a4; }
  .project-card { background: #26262a; border-color: #3a3a3f; }
  .product-path { color: #a0a0a6; }
  .station-block h3 { color: #a0a0a6; }
}
"""


def _fmt_generated_at(when: datetime) -> str:
    return when.strftime("%Y-%m-%d %H:%M UTC") if when.tzinfo else when.strftime("%Y-%m-%d %H:%M")


def _render_nemawashi_block(status: NemawashiStatus | InstanceNemawashi, *, is_instance: bool) -> str:
    lines = ['<div class="station-block">', "<h3>Nemawashi</h3>"]
    if is_instance:
        assert isinstance(status, InstanceNemawashi)
        lines.append(f"<p>state: {html.escape(status.state.value)}</p>")
        lines.append(f"<p>{status.root_seed_count} root seed(s)</p>")
    else:
        assert isinstance(status, NemawashiStatus)
        lines.append(f"<p>state: {html.escape(status.state.value)}</p>")
        if status.state is NemawashiState.ACTIVE:
            lines.append(f"<p>{html.escape(status.seed_title or '')}</p>")
            lines.append(f"<p>{status.checklist_done}/{status.checklist_total} checked</p>")
    lines.append(
        f"<p>unpicked: {status.unpicked_count} · trail: {status.trail_count}"
        f" · drop: {status.drop_count}</p>"
    )
    lines.append("</div>")
    return "\n".join(lines)


def _render_shukuba_block(status: ShukubaStatus | InstanceShukuba, *, is_instance: bool) -> str:
    lines = ['<div class="station-block">', "<h3>Shukuba</h3>"]
    if is_instance:
        assert isinstance(status, InstanceShukuba)
        lines.append("<p>router — never walked</p>")
    else:
        assert isinstance(status, ShukubaStatus)
        lines.append(f"<p>state: {html.escape(status.state.value)}</p>")
        if status.station_title:
            lines.append(f"<p>{html.escape(status.station_title)}</p>")
        lines.append(f"<p>parked: {status.parked_count}</p>")
    lines.append(f"<p>trail: {status.trail_count}</p>")
    lines.append("</div>")
    return "\n".join(lines)


def _render_tobiishi_block(status: TobiishiStatus) -> str:
    lines = ['<div class="station-block">', "<h3>Tobiishi</h3>"]
    if status.changes:
        for change in status.changes:
            mark = "" if change.has_change_request else " — no change_request.md"
            lines.append(f"<p>{html.escape(change.name)}{html.escape(mark)}</p>")
    else:
        lines.append("<p>no active change</p>")
    lines.append(f"<p>trail: {status.trail_count}</p>")
    lines.append(f"<p>drop: {status.drop_count}</p>")
    lines.append("</div>")
    return "\n".join(lines)


def _render_project(project: ProjectStatus) -> str:
    parts = ['<section class="project-card">', f"<h2>{html.escape(project.name)}</h2>"]
    if project.product_path:
        parts.append(f'<p class="product-path">{html.escape(project.product_path)}</p>')
    parts.append('<div class="stations">')
    parts.append(_render_nemawashi_block(project.nemawashi, is_instance=False))
    parts.append(_render_shukuba_block(project.shukuba, is_instance=False))
    parts.append(_render_tobiishi_block(project.tobiishi))
    parts.append("</div>")
    parts.append("</section>")
    return "\n".join(parts)


def _render_violations(violations: list[Violation]) -> str:
    """A violations block, or nothing at all — a clean instance renders straight to its
    project cards, per Task 2's own layout: "a violations block first, or nothing at all when
    the repo is clean"."""
    if not violations:
        return ""
    items = "\n".join(
        f'<p class="violation"><span class="check">check {v.check}</span> — '
        f"{html.escape(v.where)}: {html.escape(v.message)}</p>"
        for v in violations
    )
    return f'<div class="violations"><h2>Violations ({len(violations)})</h2>\n{items}\n</div>'


def render(model: InstanceModel) -> str:
    """Render `model` into one self-contained HTML document. Pure — never writes a file."""
    generated = _fmt_generated_at(model.generated_at)
    instance_card = "\n".join(
        [
            '<section class="project-card">',
            "<h2>Instance seedbed / router</h2>",
            '<div class="stations">',
            _render_nemawashi_block(model.nemawashi, is_instance=True),
            _render_shukuba_block(model.shukuba, is_instance=True),
            "</div>",
            "</section>",
        ]
    )
    project_cards = "\n".join(_render_project(project) for project in model.projects)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(model.name)} — journey status</title>
<style>{_CSS}</style>
</head>
<body>
<header>
<h1>{html.escape(model.name)}</h1>
<p class="generated-at">generated {generated}</p>
</header>
{_render_violations(model.violations)}
{instance_card}
{project_cards}
</body>
</html>
"""


# =========================================================================================
# CLI
# =========================================================================================


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="journey_status.py")
    parser.add_argument("--repo", default=".", help="instance root to scan (default: cwd)")
    parser.add_argument(
        "--out", default=None, help="output HTML path (default: <repo>/system/logs/journey_status.html)"
    )
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    out = Path(args.out).resolve() if args.out else repo / "system" / "logs" / "journey_status.html"

    model = scan(repo)
    page = render(model)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
