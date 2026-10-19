#!/usr/bin/env python3
"""Report every satellite whose `.claude/` layers do not match what `link_satellite.py` produces.

WHAT IT IS FOR
    `link_satellite.py --check` answers the question for ONE satellite you already thought to
    ask about. Nothing asked it across the roster, and that is the whole reason two of
    the producer satellite's three linked layers were hand copies for months: every hook and workflow
    this host added since was invisible over there, and it surfaced only because a human noticed
    one specific hook missing — recorded in the tools project's own trail.

    So this fans that same check across the roster and prints one line per satellite. Read-only
    and cheap: run it after wiring a hook into the host's `.claude/settings.json`, or whenever a
    satellite behaves like it is a version behind.

WHAT IT REUSES, AND WHY THAT IS THE POINT
    Everything about what "correct" means comes from `link_satellite`: the layer list, the link
    form, the consumer/producer split, and the created / repointed / dangling / conflict
    distinctions. This file imports it and calls `link_satellite(..., check=True)`.

    A checker with its own opinion of correct would be the same defect one level up — two
    definitions that agree today and drift the first time either moves. The one thing it may
    have of its own is a check the linker structurally cannot make (§ THE ONE LINE THE LINKER CANNOT PRINT).

WHERE THE ROSTER COMES FROM
    `<instance-root>/system/satellites.md`, and the instance arrives **by argument**, never from
    this file's own location. `core/` is shared by every instance that binds `<CORE>` to it, so a
    tool here that reached for `system/` would read whichever instance happens to hold the core
    rather than the one the caller means: reading an instance's own `system/satellites.md` from
    `<CORE>` would point core at instance data. `--instance-root`, defaulting to the caller's
    cwd, is the shape `journey_status.py:554` already uses.

    A row's **section** is its kind: the roster's two headings are the two `--skills-mode`
    answers. The kind is read rather than sniffed from disk, because sniffing it makes the check
    circular — a satellite that drifted into the wrong shape would define its own correctness.

THE ONE LINE THE LINKER CANNOT PRINT
    `satellites.md` § The two kinds states each kind's on-disk signature: a consumer holds no
    skills layer at all — neither `.claude/skills` nor a root `skills/` — and a producer's root
    `skills/` is a real directory. This compares the rostered kind against what is there.

    For a consumer it is a detection the linker cannot make: the linker never removes what an
    earlier run linked (removing it is a commit in the satellite), so a `.claude/skills` link left
    from before every host skill was grouped would otherwise go unnamed while it still resolves.

    For a producer it is a diagnosis, not a detection. A producer whose skills root is a symlink is already
    caught — `_link_tree` recurses through the link, every host file resolves to a real file, and
    each is reported as a conflict, so `--check` exits 1 (measured 2026-08-23,
    `test_check_satellites.py` keeps the measurement). But a conflict means "the satellite holds
    its own real file here" (`link_satellite.py`'s `Report.render`), and that is the opposite of what
    happened: they are the HOST's files seen through a link, and a producer's eval writes will
    land on them. The reader gets N lines pointing away from the cause and none pointing at it.
    One line naming the shape is the whole fix, and the linker has nowhere to put it — it reports
    per path, and this is a fact about a directory.

THE INSTRUCTION FILES
    The linker has no opinion about an instance's root, so this is the second check of this
    file's own. An instance is routed by `AGENTS.md` and described by `kensaiapp.md`, and Claude
    Code is led to both by a one-line `CLAUDE.md` that imports `AGENTS.md`. So each instance is
    read for that: a missing `AGENTS.md`, `CLAUDE.md` or `kensaiapp.md`, and an `AGENTS.md` or
    `CLAUDE.md` that differs from its template under `<CORE>/templates/` (both are template-owned;
    `spawn_satellite.py` rewrites them on a resume). The host is read the same way and gets a line of its own, because it is an instance too and is on no roster.

THE OVERLAYS
    The third check of this file's own. A seat added to the host reaches a satellite only when
    someone stamps its overlay there (`adding_a_role.md` step 7), and a seat renamed leaves an
    overlay renamed while it still extends the old seat. Neither is a link, so the linker cannot
    see either. Each row of an instance's loader map must reach `system/loaders/<stem>.md`, and
    that file's Extends line must name `<stem>_global.md`, held by this core. The host is read
    the same way. What an overlay SAYS is not checked: a seam naming the wrong seat is prose, and
    only a reader catches it.

THE AGENTS FOLDER
    The fourth check of this file's own. A satellite's `.claude/agents/` is its own: it holds a
    real `<name>.md` only for an agent the satellite overrides, and a launched run takes that
    file in place of the agent file of the same name in the host's groups. The linker no longer
    links the folder and has no opinion of it, so the check of it is this file's alone.

    The folder is in one of four states: absent, a real directory, a symlink that resolves, or a
    symlink that dangles. The state is decided from the path itself, before anything inside it is
    read.

    A real directory is read for agent files. An agent file is an entry directly inside it whose
    name ends in `.md` and does not start with a dot, and which is a file once links are followed.
    A link to a file counts. A subdirectory, another extension and a dangling link do not, and the
    linker still reports a dangling one. Each agent file is an override, and one line beneath the
    headline lists them by name in byte order: `agent overrides: architect, pm`.

    An override is not drift. It changes neither the satellite's mark, nor the counts on its
    headline, nor the exit code. An absent folder, or a real one holding no agent file, prints
    nothing.

    A symlink, resolving or dangling, is drift, and one line beneath the headline says so. It is
    never read for overrides, because a link into the host would list the host's files as the
    satellite's own.

USAGE
    python3 <CORE>/tools/check_satellites.py [--instance-root .] [--quiet]

EXIT CODES
    0  every rostered satellite is level
    1  at least one has drifted, is absent, or needs attention
    2  bad invocation (no roster at the given root)
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import link_satellite

__version__ = "1.6.0"

# The roster's section heading -> the `--skills-mode` that section's rows were spawned with.
# `satellites.md` § The two kinds states the pair; this maps the headings that carry them.
_KIND_BY_HEADING = (("consumer", "consumer"), ("producer", "producer"))

_HEADING = re.compile(r"^##\s+(?P<text>.+?)\s*$")

# A roster row: `| `name` | /abs/path |`. The name is backticked in every row of both tables;
# requiring the backticks is what keeps the preamble's kinds table — whose first column is a bare
# word — from being read as two satellites called `consumer` and `producer`.
_ROW = re.compile(r"^\|\s*`(?P<name>[^`]+)`\s*\|\s*`?(?P<path>[^`|]+?)`?\s*\|\s*$")


@dataclass(frozen=True)
class Satellite:
    """One rostered satellite: what it is called, where it is, and which kind it was spawned as."""

    name: str
    path: Path
    kind: str


def read_roster(instance_root: Path) -> list[Satellite]:
    """Every satellite in `<instance-root>/system/satellites.md`, in the order it is listed."""
    roster = Path(instance_root) / "system" / "satellites.md"
    if not roster.is_file():
        raise SystemExit(f"error: no roster at {roster}. Pass --instance-root.")

    entries: list[Satellite] = []
    kind: str | None = None
    for line in roster.read_text().splitlines():
        heading = _HEADING.match(line)
        if heading:
            lowered = heading.group("text").lower()
            kind = next((k for token, k in _KIND_BY_HEADING if token in lowered), None)
            continue
        if kind is None:
            continue
        row = _ROW.match(line)
        if not row:
            continue
        entries.append(
            Satellite(
                name=row.group("name"),
                path=Path(os.path.expanduser(row.group("path").strip())),
                kind=kind,
            )
        )
    return entries


@dataclass(frozen=True)
class Verdict:
    """One satellite's outcome: the linker's own report, or the reason there is none."""

    satellite: Satellite
    report: link_satellite.Report | None
    absent: bool = False
    shape: str | None = None  # the skills root's shape, when it contradicts the rostered kind
    instructions: tuple[str, ...] = ()  # what is wrong with its instruction files, one line each
    overlays: tuple[str, ...] = ()  # what is wrong with its role overlays, one line each
    agent_overrides: tuple[str, ...] = ()  # the agents it overrides, by name; never drift
    agents_link: str | None = None  # the leftover-link problem, when `.claude/agents` is a symlink

    @property
    def drifted(self) -> bool:
        if self.absent or self.shape or self.instructions or self.overlays or self.agents_link:
            return True
        return bool(self.report and (self.report.would_change or self.report.needs_attention))

    @property
    def headline(self) -> str:
        if self.absent:
            return f"DRIFT {self.satellite.name} ({self.satellite.kind}) — not on disk: {self.satellite.path}"
        r = self.report
        assert r is not None
        counts = (
            f"{len(r.created)} unlinked, {len(r.repointed)} to repoint, "
            f"{len(r.written)} settings to write, {len(r.removed)} links to remove, "
            f"{len(r.conflicts)} conflicts, {len(r.dangling)} dangling, "
            f"{len(r.dir_links)} dir-symlinks"
        )
        mark = "DRIFT" if self.drifted else "ok   "
        line = f"{mark} {self.satellite.name} ({self.satellite.kind}) — {counts}"
        if self.shape:
            line += f"\n      {self.shape}"
        for problem in self.instructions + self.overlays:
            line += f"\n      {problem}"
        if self.agent_overrides:
            line += f"\n      {AGENT_OVERRIDES_PREFIX}{', '.join(self.agent_overrides)}"
        if self.agents_link:
            line += f"\n      {self.agents_link}"
        return line


AGENT_OVERRIDES_PREFIX = "agent overrides: "

AGENTS_LINK_PROBLEM = (
    ".claude/agents is a symlink, and a satellite's agents folder is its own — writes through "
    "it land in the link's target; removing it is a commit in the satellite"
)


def _agents_folder(satellite: Path) -> tuple[tuple[str, ...], str | None]:
    """The satellite's agent-override names and its leftover-link problem; never both set.

    The folder's state is decided on the path itself, before anything inside it is read:
    `Path.is_dir` follows a link, so a symlink into the host would otherwise be read as a real
    directory and the host's files listed as this satellite's own."""
    agents = satellite / ".claude" / "agents"
    if agents.is_symlink():
        return (), AGENTS_LINK_PROBLEM
    if not agents.is_dir():
        return (), None
    names = {
        entry.name[: -len(".md")]
        for entry in agents.iterdir()
        if entry.name.endswith(".md") and not entry.name.startswith(".") and entry.is_file()
    }
    return tuple(sorted(names, key=lambda name: name.encode("utf-8"))), None


def _shape_mismatch(satellite: Satellite) -> str | None:
    """The skills layout, when it contradicts the kind the roster gives this satellite, per
    `satellites.md` § The two kinds. The kind is read from the roster and the shape from disk,
    never the reverse: deriving the kind from the shape would let a satellite that drifted define
    its own correctness."""
    if satellite.kind == "producer":
        if (satellite.path / "skills").is_symlink():
            return (
                "skills root is a symlink, and a producer's must be a real directory — every "
                "eval/evidence write through it lands in the host"
            )
        return None
    if satellite.kind == "consumer":
        for layer in (Path(".claude") / "skills", Path("skills")):
            if os.path.lexists(satellite.path / layer):
                return (
                    f"{layer} is present, and a consumer holds no skills layer — its launchers "
                    "grant each group from the host; removing it is a commit in the satellite"
                )
    return None


# The template-owned root files: name, its template under `<CORE>/templates/`, and what its
# absence costs the instance.
_TEMPLATE_OWNED = (
    ("AGENTS.md", "agents_md_template.md", "the instance has no loader map"),
    ("CLAUDE.md", "claude_md_template.md", "Claude Code falls back to AGENTS.md and says so every session"),
)


def instruction_problems(instance_root: Path, host: Path) -> tuple[str, ...]:
    """What is wrong with one instance's instruction files — empty when nothing is."""
    problems: list[str] = []
    for name, template_name, cost in _TEMPLATE_OWNED:
        path = instance_root / name
        template = host / "core" / "templates" / template_name
        if not path.is_file():
            problems.append(f"{name} is missing — {cost}")
        elif template.is_file() and path.read_text(encoding="utf-8") != template.read_text(encoding="utf-8"):
            problems.append(f"{name} differs from {template_name} — re-stamp it")
    if not (instance_root / "kensaiapp.md").is_file():
        problems.append("kensaiapp.md is missing — the instance states no identity")
    return tuple(problems)


# A loader-map row in `AGENTS.md`, and the Extends line every overlay template stamps.
_MAP_ROW = re.compile(r"^- `(?P<prefix>[a-z-]+):`\s+→\s+system/loaders/(?P<stem>[a-z_]+)\.md\s*$",
                      re.MULTILINE)
_EXTENDS = re.compile(r"Extends `<CORE>/roles/loaders/(?P<stem>[a-z_]+)_global\.md`")


def overlay_problems(instance_root: Path, host: Path) -> tuple[str, ...]:
    """What is wrong with one instance's role overlays — empty when nothing is. Every row of its
    loader map must reach an overlay, and that overlay must extend its own seat's global loader in
    this core. A seat added or renamed in the host and never carried across leaves exactly these:
    a prefix that resolves to nothing, or an overlay renamed while it still extends the old seat."""
    agents = instance_root / "AGENTS.md"
    if not agents.is_file():
        return ()
    problems: list[str] = []
    for row in _MAP_ROW.finditer(agents.read_text(encoding="utf-8")):
        stem = row.group("stem")
        overlay = f"system/loaders/{stem}.md"
        path = instance_root / overlay
        if not path.is_file():
            problems.append(f"{overlay} is missing — the `{row.group('prefix')}:` prefix resolves to nothing")
            continue
        extends = _EXTENDS.search(path.read_text(encoding="utf-8"))
        named = extends.group("stem") if extends else None
        if named != stem:
            problems.append(f"{overlay} extends {named}_global.md, not {stem}_global.md")
        elif not (host / "core" / "roles" / "loaders" / f"{stem}_global.md").is_file():
            problems.append(f"{overlay} extends {stem}_global.md, which this core does not hold")
    return tuple(problems)


def check_one(satellite: Satellite, host: Path) -> Verdict:
    """Run the linker's own `--check` against one satellite. Changes nothing, anywhere."""
    if not satellite.path.is_dir():
        return Verdict(satellite=satellite, report=None, absent=True)
    report = link_satellite.link_satellite(
        satellite.path, host, skills_mode=satellite.kind, check=True
    )
    overrides, agents_link = _agents_folder(satellite.path)
    return Verdict(
        satellite=satellite,
        report=report,
        shape=_shape_mismatch(satellite),
        instructions=instruction_problems(satellite.path, host),
        overlays=overlay_problems(satellite.path, host),
        agent_overrides=overrides,
        agents_link=agents_link,
    )


def check_roster(instance_root: Path) -> list[Verdict]:
    """Every rostered satellite, checked. One failing satellite never stops the others."""
    return [check_one(entry, instance_root) for entry in read_roster(instance_root)]


def render(verdict: Verdict, *, quiet: bool) -> str:
    """The headline, plus the linker's own detail unless the caller asked for the verdict alone."""
    lines = [verdict.headline]
    if not quiet and verdict.report is not None and verdict.drifted:
        lines.append(verdict.report.render(check=True))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_satellites.py",
        description=(
            "Report every satellite whose .claude/ layers do not match what link_satellite.py "
            "would produce, and list the agents each satellite overrides in its own "
            ".claude/agents/. Read-only."
        ),
    )
    parser.add_argument(
        "--instance-root",
        default=".",
        help="the host instance whose system/satellites.md is the roster (default: cwd)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print one headline per satellite and none of the linker's detail",
    )
    args = parser.parse_args(argv)

    host = Path(args.instance_root).expanduser().resolve()
    verdicts = check_roster(host)
    for verdict in verdicts:
        print(render(verdict, quiet=args.quiet))

    host_problems = instruction_problems(host, host) + overlay_problems(host, host)
    print(("DRIFT" if host_problems else "ok   ") + f" {host.name} (host) — instruction files and overlays")
    for problem in host_problems:
        print(f"      {problem}")

    return 1 if host_problems or any(v.drifted for v in verdicts) else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
