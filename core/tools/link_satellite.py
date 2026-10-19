#!/usr/bin/env python3
"""Bring a shared-core satellite level with its host instance — write its `.claude/settings.json`
from the host's hook wiring, and, for a producer, link the host's root `skills/` layer, where every
host skill lives in its group.

WHAT IT IS FOR
    A satellite (a local instance that reads the host's core — see
    `<CORE>/doctrine/setup/shared_core_instance.md`) runs the host's hook scripts by absolute
    path, and a producer reads the host's skill files through absolute symlinks, so an edit to
    either in the host is seen instantly. The one copy a satellite holds is its
    `.claude/settings.json`, written from the host's hook wiring, and that copy goes out of date
    when a hook is wired into the host.
    `spawn_satellite.py` calls this at creation; anyone can call it again later to bring a drifted
    satellite level. Re-runnability is the point, not a convenience: a *file* symlink carries
    edits to something that already exists and carries nothing about something created later,
    and nothing fails when it is missing — the satellite silently lacks it. Both hand-built
    satellites drifted that way within days and were hand-resynced. A script that can be re-run
    is what replaces the hand-resync.

WHAT IT LINKS, AND WHAT IT WRITES
    Nothing under `.claude/` is linked. One file there is written:

        .claude/settings.json   the host's `hooks` key and nothing else, with every
                                `${CLAUDE_PROJECT_DIR}/.claude/hooks/` replaced by
                                `<host>/.claude/hooks/`

    So each hook command runs the host's own script, and a satellite needs no `.claude/hooks`
    of its own. The command still runs with `CLAUDE_PROJECT_DIR` set to the satellite, so
    `resolve_core.py` still reads the satellite's own `.env`. A host whose `settings.json` has no
    `hooks` key gives the satellite `{}`. The file is generated: this script rewrites it whenever
    it differs, and what a satellite owns goes in its own `settings.local.json`.

    A hook script edited in the host is live in the satellite at once. A hook wired into the
    host's `settings.json` is not: `--check` reports the satellite as drifted until this script
    is run again.

    `.claude/hooks`, `.claude/workflows` and `.claude/settings.json` were links in earlier
    versions. A link at one of them that points into the host, dangling or not, is removed, and
    the `settings.json` one is replaced by the written file. A real file or directory at
    `.claude/hooks` or `.claude/workflows`, or a link at any of the three that points outside the
    host, is a conflict and is left untouched. A launched run takes the host's workflows from its
    pin, so a satellite needs no `workflows` link.

    `.claude/agents` is not linked, because a satellite's agents folder is its own. It holds a
    real `<name>.md` only for an agent the satellite overrides, and a launched run takes that
    file in place of the agent file of the same name in the host's groups. An `agents` link an
    earlier run made is left as it is. Removing it is a commit in the satellite, and
    `check_satellites.py` reports it as drift.

    The skills are answered by what the satellite DOES rather than by which satellite it is. Every
    host skill lives in a group, `skills/<group>/.claude/skills/<name>/`, and the host's flat
    `.claude/skills/` holds none — so the flat layer is linked in neither mode:

      consumer  — it only reads skills. Nothing is linked: the launchers a consumer runs look a
                  grouped skill up under the host root (`<CORE>/..`) and grant its group from
                  there, so a consumer holds no skills of its own and needs no link to reach them.
                  A `.claude/skills` link an earlier run made is left as it is — removing it is a
                  commit in the satellite, not this script's — and once the host's flat folder is
                  gone it is reported as a dangling link, which is the cue to remove it.
      producer  — it runs `skill-evals` / holds per-skill evidence. Those artifacts land INSIDE
                  the skill folder (`<skill>/evals/workspace/iteration-N/`), so the folder must be
                  real or the write silently lands in the HOST. The host's root `skills/` is
                  therefore mirrored: every directory recreated as a real directory and every file
                  inside it symlinked, at any depth — so each content file is still single-source
                  with the host, while every possible write path resolves inside the satellite.
                  A `.claude/skills` tree an earlier run mirrored is left as it is too, and its
                  links are reported dangling once the host's flat files are gone.

    A host with no root `skills/` — one that has created no group — is not drift. So for a
    producer an absent host `skills/` is a no-op: nothing is written, nothing dangles, the run
    still exits 0, and the report names the layer it skipped and the host path it looked for,
    rather than staying silent about it.

    The producer shape is the reason this script recurses rather than linking only `SKILL.md`.
    Linking the top-level files alone is what the hand-built satellites did, and it is why one of
    them carries a `product-prd/` with no `evals/` at all while the host has one.

WHAT IT NEVER TOUCHES
    The satellite's own real files — `.env`, `system/loaders/*.md`, `.claude/settings.local.json`,
    the stamped instance files, and any per-instance data (a producer's `evals/` and `evidence/`
    output). Where a real file already sits at a path this script would link, or a real file or
    directory sits at `.claude/hooks` or `.claude/workflows`, it reports a CONFLICT and leaves it
    alone. Deciding that a real file should become a link is a judgement, and this script does
    not make it. `.claude/settings.json` is not the satellite's own: it is this script's output,
    and a regular file there that differs from what this script writes is rewritten.

WHY ABSOLUTE LINKS
    Absolute is the only form. Every link carries the host's full path — a link reads the same
    from anywhere, and a satellite can be moved without touching it.

    Relative was the original choice, for the property that a *sibling* pair moves together and
    neither carries a machine path. That property only exists when the two sit in one tree, and
    the fleet does not: a satellite may live under one root while its host is under another,
    where the relative form computes to a five-level `../` climb that
    resolves but protects nothing. A form that is right for some satellites and meaningless for
    others is two forms, and two forms drift. So the relative one is retired rather than kept
    as a mode.

    The cost, named plainly: the target string is machine-specific, and these links are tracked
    in git as mode 120000 with the target as the blob's content. A clone on another machine —
    or a moved host — gets dangling links until they are re-linked by re-running this script.
    That is the trade accepted for one form.

    Each link is still verified after it is written, so a target that does not resolve is
    reported at link time instead of discovered as a missing skill weeks later.

USAGE
    python3 <CORE>/tools/link_satellite.py \
        --satellite /abs/path/to/kensaiapp-<name> \
        --host      /abs/path/to/host \
        --skills-mode consumer|producer \
        [--check]

    `--check` changes nothing and exits 1 if anything would change — a drift gate you can run
    against a live satellite. A link of the wrong FORM counts as drift: right target, relative
    text. That is what converges a satellite linked before absolute-only. A `settings.json` that
    is absent or differs from what this script writes, and a link into the host it would remove,
    count as drift too.

EXIT CODES
    0  nothing needed doing, or everything asked for was done
    1  `--check` found drift, or a conflict / dangling link was reported
    2  bad invocation (missing path, host has no `.claude/` or no `.claude/settings.json`,
       relative host path)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import hook_wiring

__version__ = "1.4.0"

# The file this script writes in a satellite, and the two links an earlier version made there that
# it now removes when they point into the host. `settings.json` was a third; it is replaced by the
# written file rather than removed, so it is not in this tuple. (The skills layer is handled by
# mode at its own call site, and `agents` is the satellite's own.)
SETTINGS_NAME = "settings.json"
RETIRED_LINKS = ("hooks", "workflows")

SKILLS_MODES = ("consumer", "producer")

# Never mirrored, at any depth. Caches are machine-local noise; `evals/workspace/` is the
# producer's OWN output — `skill-evals` writes each round to `<skill>/evals/workspace/iteration-N/`
# and `.gitignore` excludes it for exactly that reason. Linking the host's rounds into a satellite
# would hand it another instance's measurements as if they were its own.
SKIP_NAMES = ("__pycache__", ".pytest_cache", ".DS_Store")
SKIP_UNDER = {"workspace": "evals"}  # name -> the parent name that makes it the write target


@dataclass
class Report:
    """What a run did, in the categories a caller needs to tell apart."""

    created: list[str] = field(default_factory=list)
    repointed: list[str] = field(default_factory=list)
    written: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    already: list[str] = field(default_factory=list)
    dangling: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    dir_links: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    @property
    def would_change(self) -> bool:
        return bool(self.created or self.repointed or self.written or self.removed)

    @property
    def needs_attention(self) -> bool:
        return bool(self.dangling or self.conflicts or self.dir_links)

    def render(self, *, check: bool) -> str:
        verb = "would link" if check else "linked"
        repoint_verb = "would repoint" if check else "repointed"
        write_verb = "would write" if check else "wrote"
        remove_verb = "would remove" if check else "removed"
        lines = [
            f"{verb}: {len(self.created)}",
            f"{repoint_verb} (relative -> absolute): {len(self.repointed)}",
            f"{write_verb} settings.json: {len(self.written)}",
            f"{remove_verb} (no longer linked): {len(self.removed)}",
            f"already correct: {len(self.already)}",
            f"dangling: {len(self.dangling)}",
            f"conflicts: {len(self.conflicts)}",
            f"directory-symlinked where a real directory is needed: {len(self.dir_links)}",
            f"skipped (host source not created yet): {len(self.skipped)}",
        ]
        for path in self.created:
            lines.append(f"  [{verb}] {path}")
        for path in self.repointed:
            lines.append(f"  [{repoint_verb}] {path} — same target, relative text")
        for path in self.written:
            lines.append(f"  [{write_verb}] {path}")
        for path in self.removed:
            lines.append(f"  [{remove_verb}] {path}")
        for entry in self.skipped:
            lines.append(f"  [skipped] {entry}")
        for path in self.dangling:
            lines.append(f"  [dangling] {path} — target no longer exists in the host")
        for path in self.conflicts:
            lines.append(f"  [conflict] {path} — a real file/dir is here; left untouched")
        for path in self.dir_links:
            lines.append(f"  [dir-symlink] {path} — writes here land in the host, not here")
        if self.dir_links:
            lines.append(
                "\nA directory symlink inside a PRODUCER's skill folder is the sharp edge: running "
                "skill-evals through it writes the round into the host instead of here, and nothing "
                "says so. Replace each with a real directory and re-run — this script will then link "
                "the files beneath it. It does not do the replacement itself, because the directory "
                "may be holding content you have not looked at."
            )
        if self.dangling:
            lines.append(
                "\nDangling links are reported, never removed: one may point at something you "
                "deleted from the host on purpose, and one may be the only trace that a skill "
                "used to exist. Remove the ones you mean to remove."
            )
        if self.conflicts:
            lines.append(
                "\nA conflict means the satellite holds its own real file where the host's would "
                "be linked. At .claude/hooks, .claude/workflows and .claude/settings.json nothing "
                "is linked any more. A conflict at one of them is a real file or directory at "
                ".claude/hooks or .claude/workflows, or a link at any of the three that points "
                "outside the host. That is legitimate for per-instance data; it is drift for "
                "shared content. Decide per path — this script will not overwrite either way."
            )
        return "\n".join(lines)


def _link_text(target: Path) -> str:
    """The string written into the symlink: the host path, absolute (see WHY ABSOLUTE LINKS)."""
    if not target.is_absolute():
        raise SystemExit(
            f"error: cannot write an absolute link to a relative target: {target}. "
            "Pass --host as an absolute path."
        )
    return os.fspath(target)


def _verify_resolves(link_path: Path, target: Path, text: str) -> None:
    """Verify rather than assume — a link that does not resolve would otherwise surface much
    later as a mysteriously absent skill."""
    if not link_path.exists() or link_path.resolve() != target.resolve():
        raise SystemExit(
            f"error: wrote {link_path} -> {text} but it does not resolve to {target}."
        )


def _link_one(link_path: Path, target: Path, report: Report, *, check: bool) -> None:
    """Ensure a single symlink at `link_path` points at `target`. Never overwrites a real file."""
    text = _link_text(target)

    if link_path.is_symlink():
        if not link_path.exists():  # follows the link; False means it dangles
            report.dangling.append(str(link_path))
            return
        if link_path.resolve() == target.resolve():
            # Right target. The remaining question is the FORM, and the whole test is whether
            # the text is absolute — not whether it equals `text` exactly, because two absolute
            # paths can differ textually and still be right (a `/var` -> `/private/var` symlink
            # in the path is the common case) and neither needs rewriting.
            if os.path.isabs(os.readlink(link_path)):
                report.already.append(str(link_path))
                return
            # Right target, relative text: a link written before absolute-only. Repointing is
            # safe precisely BECAUSE it resolves to the target already — nothing about what the
            # satellite sees changes, only the text. This is the one case where the script
            # replaces an existing link, and it is why a satellite converges on a re-run
            # instead of needing a hand-repoint.
            report.repointed.append(str(link_path))
            if check:
                return
            _replace_symlink(link_path, text)
            _verify_resolves(link_path, target, text)
            return
        # A symlink pointing somewhere else entirely. Treat it as a conflict rather than
        # silently repointing it — a deliberate override is indistinguishable from drift here,
        # and only the owner knows which this is.
        report.conflicts.append(str(link_path))
        return

    if link_path.exists():
        report.conflicts.append(str(link_path))
        return

    report.created.append(str(link_path))
    if check:
        return

    link_path.parent.mkdir(parents=True, exist_ok=True)
    link_path.symlink_to(text)
    _verify_resolves(link_path, target, text)


def _replace_symlink(link_path: Path, text: str) -> None:
    """Swap an existing symlink's target atomically.

    Written as create-then-rename rather than unlink-then-create so the path is never empty: an
    interrupted unlink-then-create would leave a satellite with no link at that path at all.
    `os.replace` renames the link itself, not what it points at.
    """
    staging = link_path.with_name(link_path.name + ".relink-tmp")
    if os.path.lexists(staging):
        staging.unlink()
    staging.symlink_to(text)
    os.replace(staging, link_path)


def _is_within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _points_into_host(link: Path, host: Path) -> bool:
    """Whether a symlink was made into the host, by this script or an earlier version of it.

    Decided from the link's own text, made absolute against the link's directory, before the link
    is followed — a link whose target is gone still says where it was aimed, and a dangling link
    into the host must be recognised as one. A link whose real path lands under the host counts
    too, which is how a link written through a detour (`/var` for `/private/var`) is read."""
    aimed_at = Path(os.path.normpath(link.parent / os.readlink(link)))
    host_forms = {host, host.resolve()}
    if any(_is_within(aimed_at, form) for form in host_forms):
        return True
    return _is_within(link.resolve(), host.resolve())


def _render_settings(host_claude: Path) -> str:
    """The text a satellite's `settings.json` holds: the host's `hooks` key alone, each live hook
    path replaced by the host's own hooks directory, or `{}` when the host wires none."""
    path = host_claude / SETTINGS_NAME
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise SystemExit(f"error: host .claude/settings.json is not valid JSON: {path}: {exc}")
    if not isinstance(document, dict):
        raise SystemExit(f"error: host .claude/settings.json is not a JSON object: {path}")
    hooks_dir = Path(_link_text(host_claude / "hooks"))
    wired = {"hooks": hook_wiring.rewrite_hooks_dir(document["hooks"], hooks_dir)} if (
        "hooks" in document
    ) else {}
    return json.dumps(wired, indent=2) + "\n"


def _read_text_or_none(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _write_replacing(path: Path, text: str) -> None:
    """Write `text` at `path` by staging it beside the target and renaming it into place, so a
    symlink there is swapped for the file in one step and the path is never empty."""
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_name(path.name + ".write-tmp")
    staging.write_text(text, encoding="utf-8")
    os.replace(staging, path)


def _settle_settings(
    sat_claude: Path, host: Path, host_claude: Path, report: Report, *, check: bool
) -> None:
    """Make the satellite's `settings.json` the file the host's hook wiring renders to."""
    path = sat_claude / SETTINGS_NAME
    expected = _render_settings(host_claude)

    if path.is_symlink():
        if not _points_into_host(path, host):
            report.conflicts.append(str(path))
            return
    elif path.is_dir():
        report.conflicts.append(str(path))
        return
    elif _read_text_or_none(path) == expected:
        report.already.append(str(path))
        return

    report.written.append(str(path))
    if not check:
        _write_replacing(path, expected)


def _remove_retired_link(path: Path, host: Path, report: Report, *, check: bool) -> None:
    """Remove a link an earlier version made into the host. Anything else standing there —
    a real file or directory, or a link aimed elsewhere — is the satellite's to decide."""
    if path.is_symlink():
        if _points_into_host(path, host):
            report.removed.append(str(path))
            if not check:
                path.unlink()
        else:
            report.conflicts.append(str(path))
    elif os.path.lexists(path):
        report.conflicts.append(str(path))


def _link_tree(link_root: Path, target_root: Path, report: Report, *, check: bool) -> None:
    """Mirror `target_root` under `link_root` as real directories + file symlinks, recursively.

    This is the producer shape: every directory is real, so anything written into the tree stays
    in the satellite; every file is a symlink, so shared content has one source.
    """
    if not target_root.is_dir():
        return
    for entry in sorted(target_root.iterdir()):
        if entry.name in SKIP_NAMES:
            continue
        if SKIP_UNDER.get(entry.name) == target_root.name:
            continue
        link_path = link_root / entry.name
        if entry.is_dir() and not entry.is_symlink():
            if link_path.is_symlink():
                # Told apart from a plain conflict on purpose. A symlink standing where a
                # producer needs a real directory is the failure this whole mode exists to
                # prevent — writes through it land in the host — so it gets its own report line
                # rather than hiding among "something else is here".
                report.dir_links.append(str(link_path))
                continue
            if link_path.exists() and not link_path.is_dir():
                report.conflicts.append(str(link_path))
                continue
            if not check:
                link_path.mkdir(parents=True, exist_ok=True)
            _link_tree(link_path, entry, report, check=check)
        else:
            _link_one(link_path, entry, report, check=check)


def _report_dangling_below(root: Path, report: Report, *, handled: set[str]) -> None:
    """Walk what the satellite already has and report links whose target is gone.

    Only reports. A dangling link is evidence of a host-side deletion, and deciding whether that
    deletion should propagate is the owner's call, not this script's. A path this run already
    removes or replaces (`handled`) is reported there, not here.
    """
    if not root.exists():
        return
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in list(dirnames) + filenames:
            path = Path(dirpath) / name
            if path.is_symlink() and not path.exists():
                entry = str(path)
                if entry not in report.dangling and entry not in handled:
                    report.dangling.append(entry)
        # Do not descend through symlinked directories — they belong to the host.
        dirnames[:] = [d for d in dirnames if not (Path(dirpath) / d).is_symlink()]


def _host_problem(host: Path) -> str | None:
    """Why the host cannot be linked to, as the `error:` line that says so; None if it can."""
    host_claude = host / ".claude"
    if not host_claude.is_dir():
        return f"error: host has no .claude/ layer: {host_claude}"
    host_settings = host_claude / SETTINGS_NAME
    if not host_settings.is_file():
        return f"error: host has no .claude/settings.json: {host_settings}"
    return None


def link_satellite(
    satellite: Path,
    host: Path,
    *,
    skills_mode: str,
    check: bool = False,
) -> Report:
    """Write the settings and make every link the satellite owes the host. Idempotent; safe to
    re-run."""
    host_claude = host / ".claude"
    problem = _host_problem(host)
    if problem:
        raise SystemExit(problem)
    if skills_mode not in SKILLS_MODES:
        raise SystemExit(f"error: --skills-mode must be one of {', '.join(SKILLS_MODES)}")

    sat_claude = satellite / ".claude"
    if not check:
        sat_claude.mkdir(parents=True, exist_ok=True)

    report = Report()

    _settle_settings(sat_claude, host, host_claude, report, check=check)
    for name in RETIRED_LINKS:
        _remove_retired_link(sat_claude / name, host, report, check=check)

    # The host's flat `.claude/skills/` holds no skill, so it is linked in neither mode; the root
    # skills/ layer is a producer's only: a consumer's launchers find grouped skills under the
    # host root, so it is given no link (see WHAT IT LINKS).
    host_skills_root = host / "skills"
    sat_skills_root = satellite / "skills"
    if skills_mode == "producer":
        # `_link_tree` is already safe on an absent host_skills_root (its own early return), and
        # it never creates a symlink that could dangle — so the same call handles both cases;
        # the skip is reported alongside it purely for visibility (A2), not to change behaviour.
        _link_tree(sat_skills_root, host_skills_root, report, check=check)
        if not host_skills_root.is_dir():
            report.skipped.append(f"{sat_skills_root} — host has no root skills/ ({host_skills_root})")

    handled = set(report.written) | set(report.removed)
    _report_dangling_below(sat_claude, report, handled=handled)
    if skills_mode == "producer":
        # A producer's root is its own real tree, or absent (`_report_dangling_below`'s own early
        # return) — never a symlink into the host, so walking it reports only the satellite's.
        _report_dangling_below(sat_skills_root, report, handled=handled)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="link_satellite.py",
        description=(
            "Write a shared-core satellite's .claude/settings.json from its host's hook wiring, "
            "and link a producer's root skills/ layer to the host's if the host has one. Nothing "
            "under .claude/ is linked. Idempotent — re-run it to bring a drifted satellite level."
        ),
    )
    parser.add_argument("--satellite", required=True, help="the satellite instance root")
    parser.add_argument("--host", required=True, help="the root of the host instance, the one that holds the shared core")
    parser.add_argument(
        "--skills-mode",
        required=True,
        choices=SKILLS_MODES,
        help=(
            "consumer = no skills layer is linked (launchers find grouped skills in the host); "
            "producer = the host's root skills/ mirrored as real dirs + file symlinks, so "
            "evals/evidence land in the satellite"
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="change nothing; exit 1 if anything would change (a drift gate)",
    )
    args = parser.parse_args(argv)

    satellite = Path(args.satellite).expanduser().resolve()
    host = Path(args.host).expanduser().resolve()
    if satellite == host:
        raise SystemExit("error: --satellite and --host are the same directory")
    if not host.is_dir():
        raise SystemExit(f"error: host is not a directory: {host}")
    if not args.check and not satellite.is_dir():
        raise SystemExit(f"error: satellite is not a directory: {satellite}")

    problem = _host_problem(host)
    if problem:
        print(problem, file=sys.stderr)
        return 2

    report = link_satellite(satellite, host, skills_mode=args.skills_mode, check=args.check)
    print(report.render(check=args.check))

    if args.check and report.would_change:
        return 1
    if report.needs_attention:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
