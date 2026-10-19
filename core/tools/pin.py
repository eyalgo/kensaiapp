#!/usr/bin/env python3
"""pin.py — a frozen copy of a host's `core/`, `.claude/` and `skills/` trees, which a run reads
in place of the host's own.

WHY THIS EXISTS

A running launcher resolves `<CORE>` as wherever the host's `core/` sits today. A long chain, a
background agent, or a resumed Claude turn can span minutes to hours; if the owner edits a skill
or a doctrine file while one is in flight, the running turn silently picks up the edit mid-run —
version drift nobody asked for and nobody can reproduce. A pin freezes the three trees a run needs
at the moment a launch makes it, so a walk in flight keeps its pin: an edit to those trees made
after the launch cannot reach it, and a resumed turn reads the tree as it stood then, not as it
stands now. Which pin a launch runs in is decided by the rules in `core/tools/pin_run.sh`; a
`build-idea` start inside a pin takes a new pin when the host has changed since that pin was made.

`make` copies a host's working tree as it stands, never a commit — an uncommitted edit rides
along, because that is what the owner is actually running. `of_core` and `inherited` answer
whether a given `core/` or environment names a pin at all, both refusing a directory that carries
no manifest as firmly as one that does not exist. `pin.json`, written last, is what makes a pin
found: a copy still in flight has no manifest yet and is invisible to both.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import string
import subprocess
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

__version__ = "1.5.0"

_TREES = ("core", ".claude", "skills")


class PinMissing(Exception):
    """Raised by `inherited` when `KENSAIAPP_PIN` names a directory that is not a complete pin —
    missing outright, or present without a `pin.json`."""


@dataclass(frozen=True)
class Pin:
    """One frozen copy of a host's `core/`, `.claude/` and `skills/` trees.

    `root` is the pin's own top directory; `core` is `root/core`, the path every launcher inside
    the pin resolves `<CORE>` to. `source_host_root` is the real path of the host the pin was made
    from — the identity ownership decisions (Task 2) compare against. `id` is the pin's own name
    under its pins home. `source_head` is the host's `HEAD` commit at the moment the pin was made —
    `None` when the host was not a git work tree at pin time, or for a pin made before this field
    existed. A caller that needs to attribute a pinned file to a commit (e.g. `commit_builder.py`'s
    `Skill-Version:` / `Prompt-Version:` provenance) runs `git` in `source_host_root` restricted to
    this revision, never in the pin's own directory, which is a plain copy and not a git repo.
    """

    root: Path
    core: Path
    source_host_root: Path
    id: str
    source_head: str | None = None


def pins_home(environ: Mapping[str, str]) -> Path:
    """Where pins live: `KENSAIAPP_PINS_HOME`, else `~/.kensaiapp/pins`, created on first use."""
    override = environ.get("KENSAIAPP_PINS_HOME")
    home = Path(override) if override else Path(environ["HOME"]) / ".kensaiapp" / "pins"
    home.mkdir(parents=True, exist_ok=True)
    return home


def _new_id() -> str:
    """A UTC timestamp plus a random suffix, so two makes in the same second are still two ids."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{stamp}-{suffix}"


def is_git_work_tree(host_root: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(host_root), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def _tracked_relpaths(host_root: Path) -> list[str]:
    """Every file under the three trees as the host's working tree stands right now: tracked
    (uncommitted edits included) plus untracked-but-not-ignored — never a file `.gitignore`
    matches."""
    existing = [tree for tree in _TREES if (host_root / tree).exists()]
    if not existing:
        return []
    result = subprocess.run(
        ["git", "-C", str(host_root), "ls-files", "-z", "-co", "--exclude-standard", "--", *existing],
        capture_output=True,
        text=True,
        check=True,
    )
    return [relpath for relpath in result.stdout.split("\0") if relpath]


def tree_files(root: Path) -> list[str]:
    """Every file under the three trees of `root`, no ignore rule applied — the listing for a host
    that is not a git work tree, where the whole of each tree that exists is copied, and for a pin
    root, which is a plain copy with no git behind it."""
    relpaths: list[str] = []
    for tree in _TREES:
        tree_root = root / tree
        if not tree_root.exists():
            continue
        for path in tree_root.rglob("*"):
            if path.is_file():
                relpaths.append(str(path.relative_to(root)))
    return relpaths


def host_files(host_root: Path) -> list[str]:
    """The relpaths `make` copies from `host_root`: on a git work tree the tracked and the
    untracked-not-ignored files under the three trees, otherwise every file under them. It is the
    listing as `make` reads it — a tracked path deleted from the working tree may still appear,
    and `make` skips it when the copy finds it gone."""
    if is_git_work_tree(host_root):
        return _tracked_relpaths(host_root)
    return tree_files(host_root)


def _host_head(host_root: Path) -> str | None:
    """The host's current `HEAD` commit, full 40-hex, or `None` on any failure — an unborn branch
    (no commits yet) included. Never raises; a pin records what it can and omits the rest."""
    result = subprocess.run(
        ["git", "-C", str(host_root), "rev-parse", "HEAD"],
        capture_output=True, text=True,
    )
    sha = result.stdout.strip()
    if result.returncode != 0 or not sha:
        return None
    return sha


def make(host_root: Path, pins_home: Path) -> Pin:
    """Copy `host_root`'s `core/`, `.claude/` and `skills/` trees, as they stand right now, into a
    new directory under `pins_home`. Each file's mode travels with it. `pin.json` is written
    last — a pin without it is incomplete, and neither `of_core` nor `inherited` will find one.

    Also records the host's `HEAD` at this moment as `source_head` — the revision a later `git
    log` against `source_host_root` restricts itself to, so a commit made to the host *after* the
    pin exists never changes what a pinned run attributes a file to. Omitted when the host is not
    a git work tree (the split `host_files` makes) or `HEAD` cannot
    be resolved (e.g. an unborn branch) — never guessed."""
    host_root = Path(host_root).resolve()
    is_work_tree = is_git_work_tree(host_root)
    relpaths = host_files(host_root)
    source_head = _host_head(host_root) if is_work_tree else None

    pin_id = _new_id()
    root = Path(pins_home) / pin_id
    root.mkdir(parents=True)

    for relpath in relpaths:
        src = host_root / relpath
        dst = root / relpath
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
        except FileNotFoundError:
            # Gone between the listing above and this copy — another live process's own
            # scratch file, deleted after `git ls-files` saw it and before this line ran. The
            # pin is a snapshot of a moving tree; a file that vanished mid-snapshot is absent
            # from it exactly as if the snapshot had landed a moment earlier.
            continue

    manifest = {
        "id": pin_id,
        "source_host_root": str(host_root),
        "created": datetime.now(timezone.utc).isoformat(),
    }
    if source_head is not None:
        manifest["source_head"] = source_head
    (root / "pin.json").write_text(json.dumps(manifest, indent=2) + "\n")

    return Pin(
        root=root, core=root / "core", source_host_root=host_root, id=pin_id,
        source_head=source_head,
    )


def _pin_from_manifest(root: Path) -> Pin | None:
    manifest = root / "pin.json"
    if not manifest.is_file():
        return None
    data = json.loads(manifest.read_text())
    return Pin(
        root=root,
        core=root / "core",
        source_host_root=Path(data["source_host_root"]),
        id=data["id"],
        source_head=data.get("source_head"),
    )


def of_core(core_dir: Path) -> Pin | None:
    """The pin `core_dir` belongs to, or `None` when `core_dir`'s parent carries no `pin.json` —
    a live host's `core/` included."""
    return _pin_from_manifest(Path(core_dir).parent)


def inherited(environ: Mapping[str, str]) -> Pin | None:
    """The pin named by `KENSAIAPP_PIN`, or `None` when the variable is unset. Raises
    `PinMissing` when it names a directory that is not a complete pin."""
    value = environ.get("KENSAIAPP_PIN")
    if not value:
        return None
    pin = _pin_from_manifest(Path(value))
    if pin is None:
        raise PinMissing(f"KENSAIAPP_PIN names no complete pin: {value}")
    return pin


class Kind(str, Enum):
    """The three things `owned_entries` and `agent_file` decide ownership of. Each value is the
    directory name they live under: flat under `.claude/<kind>/`, and grouped under
    `skills/*/.claude/<kind>/` for skills and for agents. An agent is a `*.md` file; the host's
    agents all live in groups, and a flat `.claude/agents/<name>.md` is an instance's own."""

    SKILLS = "skills"
    AGENTS = "agents"
    WORKFLOWS = "workflows"


@dataclass(frozen=True)
class Ownership:
    """Maps each name of one `Kind` to the one path a run loads it from: the instance's own path
    when the instance genuinely holds that name, the pin's path for every other name."""

    paths: Mapping[str, Path]

    def __getitem__(self, name: str) -> Path:
        return self.paths[name]

    def __contains__(self, name: str) -> bool:
        return name in self.paths

    def __iter__(self):
        return iter(self.paths)

    def __len__(self) -> int:
        return len(self.paths)

    def get(self, name: str, default: Path | None = None) -> Path | None:
        return self.paths.get(name, default)


def _group_skill_dirs(pin: Pin) -> list[tuple[str, Path]]:
    """Every skill group the pin holds, as (group name, its `.claude/skills` directory), in
    name order."""
    skills_root = pin.root / "skills"
    if not skills_root.is_dir():
        return []
    groups = []
    for group_dir in sorted(skills_root.iterdir()):
        grouped_dir = group_dir / ".claude" / "skills"
        if grouped_dir.is_dir():
            groups.append((group_dir.name, grouped_dir))
    return groups


def _agent_entries(agents_dir: Path) -> dict[str, Path]:
    """The agent files in one directory, keyed by name. Only `*.md` is an agent: a `.gitkeep`
    that keeps the directory in a clone is not, and a dotfile's `Path.stem` is its whole name,
    so the suffix is the test and the stem alone would not exclude it."""
    if not agents_dir.is_dir():
        return {}
    return {
        entry.stem: entry for entry in sorted(agents_dir.iterdir()) if entry.suffix == ".md"
    }


def _grouped_agents(root: Path) -> dict[str, Path]:
    """Every agent file `root` holds in a group, `skills/<group>/.claude/agents/<name>.md`,
    keyed by name. Groups are read in name order and a later group's file replaces an earlier
    one of the same name. `root` is joined onto as given, never resolved, so a relative root
    answers a relative path."""
    skills_root = root / "skills"
    if not skills_root.is_dir():
        return {}
    agents: dict[str, Path] = {}
    for group_dir in sorted(skills_root.iterdir()):
        agents.update(_agent_entries(group_dir / ".claude" / Kind.AGENTS.value))
    return agents


def _depends_on(skill_md: Path) -> list[str]:
    """The names a SKILL.md's frontmatter `depends-on:` line lists — a comma-separated value
    under `metadata:` — or nothing when the file, the frontmatter or the line is absent. Only
    the frontmatter is read: a body line that happens to start the same way is not a
    dependency. A plain line scan, no `yaml` import (`languages/python/toolchain.md` —
    effectively zero third-party dependencies)."""
    if not skill_md.is_file():
        return []
    lines = skill_md.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, _, value = line.strip().partition(":")
        if key == "depends-on":
            return [name.strip() for name in value.split(",") if name.strip()]
    return []


def granted_groups(pin: Pin, skills: Iterable[str]) -> frozenset[str]:
    """The skill groups a grant of `skills` reaches: every group whose `.claude/skills/` holds
    a granted name, then, for each name that skill's `depends-on:` lists, that name's groups and
    its own `depends-on:`, transitively. A name that is flat, held by no group, or not a skill at
    all (an agent) adds no group and is not an error; a cycle ends because each name is
    followed once."""
    groups: set[str] = set()
    followed: set[str] = set()
    worklist = list(skills)
    while worklist:
        name = worklist.pop()
        if name in followed:
            continue
        followed.add(name)
        for group, grouped_dir in _group_skill_dirs(pin):
            skill_dir = grouped_dir / name
            if skill_dir.exists():
                groups.add(group)
                worklist.extend(_depends_on(skill_dir / "SKILL.md"))
    return frozenset(groups)


def _pin_names(pin: Pin, kind: Kind, groups: frozenset[str]) -> dict[str, Path]:
    """Every name the pin itself holds for `kind`: the flat `.claude/<kind>/*` entries, plus,
    for skills, the grouped `skills/<group>/.claude/skills/*` entries of the granted `groups`
    only, and, for agents, the grouped `skills/<group>/.claude/agents/*.md` entries of every
    group, whatever the grant."""
    names: dict[str, Path] = {}

    flat_dir = pin.root / ".claude" / kind.value
    if kind is Kind.AGENTS:
        names.update(_agent_entries(flat_dir))
        names.update(_grouped_agents(pin.root))
    elif flat_dir.is_dir():
        for entry in sorted(flat_dir.iterdir()):
            names[entry.stem] = entry

    if kind is Kind.SKILLS:
        for group, grouped_dir in _group_skill_dirs(pin):
            if group in groups:
                for entry in sorted(grouped_dir.iterdir()):
                    names[entry.stem] = entry

    return names


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False


def owned_entries(
    pin: Pin, instance_root: Path, kind: Kind, groups: frozenset[str] = frozenset()
) -> Ownership:
    """Every name of `kind` a run can load, mapped to the one path it loads it from. `groups`
    names the skill groups the run is granted; it filters `Kind.SKILLS` only, and with the
    default, empty grant no grouped skill is listed, while every group's agents always are. An
    instance entry — or the whole directory holding it, when that directory is itself a link — belongs to
    the host when its real path lies under the real path of the pin's source host root, and is
    served from the pin like every other host name. Every other instance entry is the instance's
    own and wins by name over the pin."""
    paths = _pin_names(pin, kind, groups)

    instance_dir = Path(instance_root) / ".claude" / kind.value
    if instance_dir.is_dir():
        host_root = pin.source_host_root.resolve()
        for entry in sorted(instance_dir.iterdir()):
            if kind is Kind.AGENTS and entry.suffix != ".md":
                continue
            if _is_under(entry, host_root):
                continue  # the host's own — already served from the pin above
            paths[entry.stem] = entry

    return Ownership(paths=paths)


def agent_file(
    pin: Pin | None, instance_root: Path, name: str, host_root: Path | None = None
) -> Path | None:
    """The one path a run loads agent `name` from, or `None` when nothing holds it. With a pin
    it is `owned_entries(...)`'s answer. With `pin=None` there is no pin to add to the instance,
    so the first of these that holds `name` answers: the instance's own
    `.claude/agents/<name>.md`; the instance's group file `skills/<group>/.claude/agents/<name>.md`,
    joined onto `instance_root` as given; the same group file under `host_root`, when given.
    With a `host_root`, a file whose real path lies under `<host_root>/.claude/agents` is the
    host's own, reached through a satellite's link, and is never the instance's own."""
    if pin is not None:
        return owned_entries(pin, instance_root, Kind.AGENTS).get(name)

    own = Path(instance_root) / ".claude" / Kind.AGENTS.value / f"{name}.md"
    host_flat_dir = (
        None if host_root is None else Path(host_root).resolve() / ".claude" / Kind.AGENTS.value
    )
    if own.is_file() and not (host_flat_dir is not None and _is_under(own, host_flat_dir)):
        return own

    grouped = _grouped_agents(Path(instance_root)).get(name)
    if grouped is not None:
        return grouped
    if host_root is None:
        return None
    return _grouped_agents(Path(host_root)).get(name)


def run_env(pin: Pin, environ: Mapping[str, str]) -> dict[str, str]:
    """The environment a pinned run carries: `KENSAIAPP_PIN`, plus `core.hooksPath` pointed at
    the pin's own githooks, delivered through `GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_<n>` /
    `GIT_CONFIG_VALUE_<n>` at the index an inherited `GIT_CONFIG_COUNT` already reaches — so a
    caller's own `GIT_CONFIG_*` pairs travel through untouched, and the pin's pair, landing last,
    outranks a repo's own local `core.hooksPath`."""
    count = int(environ.get("GIT_CONFIG_COUNT") or "0")
    env: dict[str, str] = {"KENSAIAPP_PIN": str(pin.root)}
    for i in range(count):
        key_name, val_name = f"GIT_CONFIG_KEY_{i}", f"GIT_CONFIG_VALUE_{i}"
        if key_name in environ:
            env[key_name] = environ[key_name]
        if val_name in environ:
            env[val_name] = environ[val_name]
    env[f"GIT_CONFIG_KEY_{count}"] = "core.hooksPath"
    env[f"GIT_CONFIG_VALUE_{count}"] = str(pin.root / "core" / "githooks")
    env["GIT_CONFIG_COUNT"] = str(count + 1)
    return env


def _nearest_core_ancestor(path: Path) -> Path | None:
    """The nearest ancestor of `path` (`path` itself included) named `core`, or `None` — every
    launcher path this function is asked about ends `core/launchers/<name>/launcher.sh` or
    `core/launch-<name>.sh`."""
    for ancestor in (path, *path.parents):
        if ancestor.name == "core":
            return ancestor
    return None


def _resolved_candidate(raw: str, *, core_dir: Path, instance_root: Path) -> Path:
    """`raw` as a real, absolute path: `<CORE>` substituted with `core_dir`, a relative path
    joined to `instance_root`, then resolved."""
    candidate = Path(str(raw).replace("<CORE>", str(core_dir)))
    if not candidate.is_absolute():
        candidate = instance_root / candidate
    return candidate.resolve()


def _launcher_tail(candidate: Path, *, core_dir: Path, host_core: Path,
                   pins_root: Path | None) -> str | None:
    """`candidate`'s (already resolved) tail below `core/` when it names a launcher under this
    run's own `core_dir`, under the live source host's `core/`, under any other pin of that
    same source, or under a pin of this run's `pins_root` that has since been pruned.

    A pruned pin has no `pin.json` left to name its source, so its source cannot be checked; it
    is accepted on its tail: a report written while its pin stood outlives the pin, and refusing
    it refused every row of the walk that read it. A pin that still stands is held to its source
    as before."""
    try:
        return str(candidate.relative_to(core_dir))
    except ValueError:
        pass

    try:
        return str(candidate.relative_to(host_core.resolve()))
    except ValueError:
        pass

    candidate_core = _nearest_core_ancestor(candidate)
    if candidate_core is not None:
        candidate_pin = of_core(candidate_core)
        if (
            candidate_pin is not None
            and candidate_pin.source_host_root.resolve() == host_core.resolve().parent
        ):
            try:
                return str(candidate.relative_to(candidate_core))
            except ValueError:
                pass
        if (
            candidate_pin is None
            and pins_root is not None
            and candidate_core.parent.parent == pins_root
            and not candidate_core.parent.exists()
        ):
            return str(candidate.relative_to(candidate_core))

    return None


def same_launcher(written: str, expected: str, *, core_dir: Path, instance_root: Path) -> bool:
    """True when `written` and `expected` name the same host launcher — whether `written` names
    the live host, a relative `core/launchers/...` path, the `<CORE>` placeholder, or any other
    pin of the same source host — or, failing all of those, the identical real file. `expected`
    is always already under `core_dir`.

    The identical-real-file check exists beside the tail comparison, not instead of it: a
    launcher's own file can be a symlink to somewhere outside every core or pin tree entirely (a
    test harness's own performance shortcut is the live case, not a hypothetical one), and
    `resolve()` follows that symlink before either side's tail could be computed — landing the
    candidate nowhere the tail check would ever recognize, even though `written` and `expected`
    name the one file."""
    core_dir = Path(core_dir).resolve()
    instance_root = Path(instance_root)

    written_candidate = _resolved_candidate(written, core_dir=core_dir,
                                             instance_root=instance_root)
    expected_candidate = _resolved_candidate(expected, core_dir=core_dir,
                                              instance_root=instance_root)
    if written_candidate == expected_candidate:
        return True

    this_pin = of_core(core_dir)
    host_core = (this_pin.source_host_root / "core") if this_pin is not None else core_dir
    pins_root = this_pin.root.resolve().parent if this_pin is not None else None

    written_tail = _launcher_tail(written_candidate, core_dir=core_dir, host_core=host_core,
                                  pins_root=pins_root)
    expected_tail = _launcher_tail(expected_candidate, core_dir=core_dir, host_core=host_core,
                                   pins_root=pins_root)
    return written_tail is not None and written_tail == expected_tail


def _cmd_make(args: argparse.Namespace, environ: Mapping[str, str]) -> int:
    made = make(Path(args.host), pins_home(environ))
    print(made.root)
    return 0


def _cmd_resolve(args: argparse.Namespace, environ: Mapping[str, str]) -> int:
    found = of_core(Path(args.core))
    if found is None:
        try:
            found = inherited(environ)
        except PinMissing as exc:
            print(str(exc), file=sys.stderr)
            return 3
    if found is not None:
        print(f"pin={found.root}")
        print(f"source={found.source_host_root}")
    return 0


def _cmd_env(args: argparse.Namespace, environ: Mapping[str, str]) -> int:
    found = _pin_from_manifest(Path(args.pin))
    if found is None:
        print(f"not a pin: {args.pin}", file=sys.stderr)
        return 1
    for key, value in run_env(found, environ).items():
        print(f"{key}={value}")
    return 0


def _cmd_agent_file(args: argparse.Namespace, environ: Mapping[str, str]) -> int:
    # No pin in force — a `--dry-run` before any pin exists on this host makes none, so the
    # launcher passes an empty value. `agent_file`'s no-pin branch is then the whole answer: the
    # instance's own agents are the instance's either way, and the pin only ever adds the host's
    # to them. The host is the repo this file sits in (`core/tools/pin.py`, two levels down), so
    # a satellite that holds no groups of its own still finds the host's.
    host_root = Path(__file__).resolve().parents[2]
    if not args.pin.strip():
        resolved = agent_file(None, Path(args.instance_root), args.name, host_root=host_root)
        if resolved is None:
            return 1
        print(resolved)
        return 0
    found = _pin_from_manifest(Path(args.pin))
    if found is None:
        print(f"not a pin: {args.pin}", file=sys.stderr)
        return 1
    resolved = agent_file(found, Path(args.instance_root), args.name)
    if resolved is None:
        return 1
    print(resolved)
    return 0


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pin.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    make_parser = subparsers.add_parser("make")
    make_parser.add_argument("--host", required=True)

    resolve_parser = subparsers.add_parser("resolve")
    resolve_parser.add_argument("--core", required=True)

    env_parser = subparsers.add_parser("env")
    env_parser.add_argument("--pin", required=True)

    agent_file_parser = subparsers.add_parser("agent-file")
    agent_file_parser.add_argument("--pin", required=True)
    agent_file_parser.add_argument("--instance-root", required=True)
    agent_file_parser.add_argument("--name", required=True)

    return parser


def main(argv: list[str] | None = None, environ: Mapping[str, str] | None = None) -> int:
    environ = os.environ if environ is None else environ
    args = _build_arg_parser().parse_args(argv)
    handler = {
        "make": _cmd_make,
        "resolve": _cmd_resolve,
        "env": _cmd_env,
        "agent-file": _cmd_agent_file,
    }[args.command]
    return handler(args, environ)


if __name__ == "__main__":
    raise SystemExit(main())
