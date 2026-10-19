#!/usr/bin/env python3
"""Proves a skill-evals run left its input fixtures byte-identical, and puts them back when it didn't.

An eval run resolves a fixture's relative `Product path:` into the repo, so a producer skill that
"owns its file locations" resolves into `evals/inputs/**` — tracked files. Four verbs:

  snapshot  capture the guarded tree (bytes, hashes, modes, directory mtimes, index state) and lock
  verify    detect any movement; exit 3 and keep the lock when something moved
  repair    put the captured bytes back and un-stage what was staged; never commits
  audit     snapshot-free check of a guarded tree against HEAD, plus the ghost-write heuristic

Directory mtimes are recorded because the observed damage mode leaves no other trace: a file created
inside a fixture directory and deleted again changes no tracked content, so hashes, `git status` and
history are all blank while the directory's mtime has moved.

Restore is deliberately built from index-only `git reset -- <path>` plus Python byte writes. The
work-discarding git verbs are force-deferred to a permission prompt by
`.claude/hooks/development-bash-approve.py` (see its RISKY set), which would stall an unattended run;
`test_fixture_guard.py` asserts this file names none of them.

Exit codes: 0 clean · 2 precondition/usage · 3 damage found · 4 repair could not finish.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
LOCK_NAME = "kensaiapp-fixture-guard.json"
SNAPSHOTS_TO_KEEP = 5

EXIT_CLEAN = 0
EXIT_PRECONDITION = 2
EXIT_DAMAGE = 3
EXIT_REPAIR_INCOMPLETE = 4

# Findings that repair can actually undo. A moved directory mtime cannot be un-moved, so it stays a
# finding for the report rather than something repair claims to fix.
RESTORABLE = {
    "modified",
    "mode-changed",
    "deleted-worktree",
    "created",
    "staged-deletion",
    "staged-add",
    "staged-modify",
}


# --------------------------------------------------------------------------- git helpers


def git(repo: Path, *args: str) -> str:
    """Run a read-only git command and return stdout. Raises on non-zero."""
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def git_allow_fail(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )


def find_repo_root(start: Path) -> Path:
    return Path(git(start, "rev-parse", "--show-toplevel").strip())


def find_git_dir(repo: Path) -> Path:
    """Per-worktree git dir, so linked worktrees never share a lock."""
    return Path(git(repo, "rev-parse", "--absolute-git-dir").strip())


def porcelain(repo: Path, *paths: str) -> list[tuple[str, str]]:
    """`git status --porcelain -z` parsed into (XY, path) pairs."""
    out = git(repo, "status", "--porcelain", "-z", "--", *paths)
    entries: list[tuple[str, str]] = []
    fields = [f for f in out.split("\0") if f]
    index = 0
    while index < len(fields):
        field = fields[index]
        code, path = field[:2], field[3:]
        entries.append((code, path))
        # A rename/copy carries its origin path in the following field.
        if code and code[0] in ("R", "C"):
            index += 1
        index += 1
    return entries


def index_entries(repo: Path, root_rel: str) -> dict[str, dict]:
    """`git ls-files -s` for the guarded root: relpath -> {mode, blob, stage}."""
    out = git(repo, "ls-files", "-s", "-z", "--", root_rel)
    entries: dict[str, dict] = {}
    for record in out.split("\0"):
        if not record:
            continue
        meta, _, path = record.partition("\t")
        mode, blob, stage = meta.split()
        entries[path] = {"mode": mode, "blob": blob, "stage": stage}
    return entries


# --------------------------------------------------------------------------- tree helpers


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_tree(root: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    """Return (files, dirs) keyed by path relative to root.

    files: {sha256, size, mode}. dirs: {mtime_ns} — the ghost-write detector.
    """
    files: dict[str, dict] = {}
    dirs: dict[str, dict] = {}
    if not root.exists():
        return files, dirs

    dirs["."] = {"mtime_ns": root.stat().st_mtime_ns}
    for current, subdirs, filenames in os.walk(root):
        current_path = Path(current)
        subdirs[:] = [d for d in subdirs if d != "__pycache__"]
        for name in subdirs:
            directory = current_path / name
            dirs[str(directory.relative_to(root))] = {
                "mtime_ns": directory.stat().st_mtime_ns
            }
        for name in filenames:
            file_path = current_path / name
            if not file_path.is_file() or file_path.is_symlink():
                continue
            stat = file_path.stat()
            files[str(file_path.relative_to(root))] = {
                "sha256": sha256_of(file_path),
                "size": stat.st_size,
                "mode": stat.st_mode & 0o7777,
            }
    return files, dirs


# --------------------------------------------------------------------------- lock


def lock_path(git_dir: Path) -> Path:
    return git_dir / LOCK_NAME


def read_lock(git_dir: Path) -> dict | None:
    path = lock_path(git_dir)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"unparseable": True, "path": str(path)}


def clear_lock(git_dir: Path) -> None:
    path = lock_path(git_dir)
    if path.exists():
        path.unlink()


# --------------------------------------------------------------------------- snapshot


def cmd_snapshot(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    if not skill_dir.is_dir():
        print(f"fixture-guard: no such skill dir: {skill_dir}", file=sys.stderr)
        return EXIT_PRECONDITION

    repo = find_repo_root(skill_dir)
    git_dir = find_git_dir(repo)
    guarded = skill_dir / "evals" / "inputs"
    guarded_rel = str(guarded.relative_to(repo))

    existing = read_lock(git_dir)
    if existing is not None and not args.supersede:
        print(
            "fixture-guard: a prior run's guard is still open — run `verify` "
            "(then `repair`) first, or pass --supersede.\n"
            f"  lock: {lock_path(git_dir)}",
            file=sys.stderr,
        )
        return EXIT_PRECONDITION

    if not guarded.exists():
        # No fixtures: still lock, so a later verify is a present-and-empty no-op.
        print(f"fixture-guard: no fixture tree at {guarded_rel} — nothing to guard")
        files, dirs, dirty = {}, {}, []
    else:
        dirty = porcelain(repo, guarded_rel)
        if dirty and not args.allow_dirty_inputs:
            print(
                "fixture-guard: the fixture tree is already dirty — refusing to start.\n"
                "Nobody edits fixtures mid-run, so this is very likely damage from an "
                "earlier run. Inspect it, then either commit it or restore it.\n"
                "Pass --allow-dirty-inputs to snapshot these bytes as the restore target "
                "(your uncommitted work is then what gets restored, never HEAD).",
                file=sys.stderr,
            )
            for code, path in dirty:
                print(f"  {code} {path}", file=sys.stderr)
            return EXIT_PRECONDITION
        files, dirs = scan_tree(guarded)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    snapshot_root = (
        Path(args.snapshot_root).resolve()
        if args.snapshot_root
        else repo / "system" / "logs" / "fixture-guard"
    )
    store = snapshot_root / skill_dir.name / stamp
    tree_store = store / "tree"
    tree_store.mkdir(parents=True, exist_ok=True)

    for relpath in files:
        source = guarded / relpath
        target = tree_store / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_utc": stamp,
        "repo_root": str(repo),
        "skill_dir": str(skill_dir),
        "guarded_root": guarded_rel,
        "head": git(repo, "rev-parse", "HEAD").strip(),
        "files": files,
        "dirs": dirs,
        "index": index_entries(repo, guarded_rel) if guarded.exists() else {},
        "snapshot_was_dirty": [list(entry) for entry in dirty],
    }
    (store / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    lock_path(git_dir).write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "pid": os.getpid(),
                "opened_utc": stamp,
                "skill_dir": str(skill_dir),
                "guarded_root": guarded_rel,
                "snapshot": str(store),
            },
            indent=2,
        )
        + "\n"
    )

    prune_snapshots(snapshot_root / skill_dir.name, keep=SNAPSHOTS_TO_KEEP, active=store)

    print(
        f"fixture-guard: snapshot ok — {len(files)} files / {len(dirs)} dirs\n"
        f"  store: {store}\n"
        f"  lock:  {lock_path(git_dir)}"
    )
    return EXIT_CLEAN


def prune_snapshots(skill_store: Path, keep: int, active: Path) -> None:
    if not skill_store.is_dir():
        return
    stamps = sorted(
        (p for p in skill_store.iterdir() if p.is_dir()), key=lambda p: p.name
    )
    for stale in stamps[:-keep] if len(stamps) > keep else []:
        if stale.resolve() == active.resolve():
            continue
        shutil.rmtree(stale, ignore_errors=True)


# --------------------------------------------------------------------------- verify


def load_open_snapshot(skill_dir: Path | None) -> tuple[Path, Path, dict, Path]:
    """Resolve (repo, git_dir, manifest, store) from the open lock.

    Raises LookupError with a human message when there is no usable lock.
    """
    anchor = skill_dir if skill_dir else Path.cwd()
    repo = find_repo_root(anchor)
    git_dir = find_git_dir(repo)
    lock = read_lock(git_dir)
    if lock is None:
        raise LookupError(
            "fixture-guard: no open guard — run `snapshot` before the eval run."
        )
    if lock.get("unparseable"):
        raise LookupError(f"fixture-guard: lock is unreadable: {lock.get('path')}")
    store = Path(lock["snapshot"])
    manifest_file = store / "manifest.json"
    if not manifest_file.exists():
        raise LookupError(f"fixture-guard: snapshot manifest missing: {manifest_file}")
    return repo, git_dir, json.loads(manifest_file.read_text()), store


def collect_findings(repo: Path, manifest: dict) -> list[dict]:
    """Compare the guarded tree and index against the manifest."""
    guarded_rel = manifest["guarded_root"]
    guarded = repo / guarded_rel
    findings: list[dict] = []

    before_files: dict[str, dict] = manifest["files"]
    before_dirs: dict[str, dict] = manifest["dirs"]
    now_files, now_dirs = scan_tree(guarded)

    for relpath, before in before_files.items():
        now = now_files.get(relpath)
        if now is None:
            findings.append({"kind": "deleted-worktree", "path": relpath})
            continue
        if now["sha256"] != before["sha256"]:
            findings.append({"kind": "modified", "path": relpath})
        elif now["mode"] != before["mode"]:
            findings.append({"kind": "mode-changed", "path": relpath})

    for relpath in now_files:
        if relpath not in before_files:
            findings.append({"kind": "created", "path": relpath})

    # A directory whose mtime moved while its contents are byte-identical means a file was created
    # and removed inside it during the run — the mode that leaves no git trace at all.
    changed_paths = {f["path"] for f in findings}
    for relpath, before in before_dirs.items():
        now = now_dirs.get(relpath)
        if now is None or now["mtime_ns"] == before["mtime_ns"]:
            continue
        touched_here = any(
            str(Path(p).parent) == relpath or (relpath == "." and "/" not in p)
            for p in changed_paths
        )
        if not touched_here:
            findings.append({"kind": "transient-write", "path": relpath})

    before_index: dict[str, dict] = manifest["index"]
    now_index = index_entries(repo, guarded_rel)
    for path, before in before_index.items():
        now = now_index.get(path)
        if now is None:
            findings.append({"kind": "staged-deletion", "path": path, "repo_relative": True})
        elif now["blob"] != before["blob"]:
            findings.append({"kind": "staged-modify", "path": path, "repo_relative": True})
    for path in now_index:
        if path not in before_index:
            findings.append({"kind": "staged-add", "path": path, "repo_relative": True})

    return findings


def cases_reading(skill_dir: Path, relpaths: set[str]) -> dict[str, list[str]]:
    """Map a damaged fixture path to the eval cases whose prompt reads that product."""
    evals_file = skill_dir / "evals" / "evals.json"
    if not evals_file.exists() or not relpaths:
        return {}
    try:
        data = json.loads(evals_file.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    products = {p.split("/")[0] for p in relpaths if "/" in p}
    affected: dict[str, list[str]] = {}
    for case in data.get("evals", []):
        prompt = case.get("prompt", "")
        hits = [product for product in products if f"inputs/{product}" in prompt]
        if hits:
            affected[case.get("name", str(case.get("id")))] = sorted(hits)
    return affected


def write_report(
    workspace: Path | None, skill_dir: Path, findings: list[dict], manifest: dict
) -> None:
    payload = {
        "clean": not findings,
        "guarded_root": manifest["guarded_root"],
        "snapshot_utc": manifest["created_utc"],
        "findings": findings,
        "suspect_cases": cases_reading(
            skill_dir, {f["path"] for f in findings if not f.get("repo_relative")}
        ),
    }
    lines = ["# Fixture integrity", ""]
    if not findings:
        lines.append(
            f"Clean — `{manifest['guarded_root']}` is byte-identical to the pre-run snapshot "
            f"({manifest['created_utc']})."
        )
    else:
        lines.append(
            f"**VIOLATED** — {len(findings)} finding(s) against the pre-run snapshot "
            f"({manifest['created_utc']}).\n"
        )
        lines.append("| kind | path |")
        lines.append("|---|---|")
        for finding in findings:
            lines.append(f"| `{finding['kind']}` | `{finding['path']}` |")
        if payload["suspect_cases"]:
            lines += [
                "",
                "## Grading may be invalid, not merely the tree dirty",
                "",
                "Both arms run in parallel against one fixture tree, so a run that wrote into a "
                "fixture may have fed its own output to the other arm. These cases read a damaged "
                "product:",
                "",
            ]
            for case, products in payload["suspect_cases"].items():
                lines.append(f"- `{case}` — reads {', '.join(f'`{p}`' for p in products)}")
        if any(f["kind"] == "transient-write" for f in findings):
            lines += [
                "",
                "## transient-write",
                "",
                "A directory's mtime moved while its contents stayed byte-identical: a file was "
                "created inside the fixture and removed again during the run. There is nothing to "
                "restore — the tree is already correct — but a write reached the fixture, so this "
                "stays a finding.",
            ]
        lines += [
            "",
            "## Recovery",
            "",
            "```",
            f"python3 {Path(__file__).name} repair --apply",
            "```",
        ]

    if workspace is None:
        print("\n".join(lines))
        print("\nfixture-guard: no --workspace given, so no report file was written.")
        return
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "fixture_guard.json").write_text(json.dumps(payload, indent=2) + "\n")
    (workspace / "fixture_guard_report.md").write_text("\n".join(lines) + "\n")


def cmd_verify(args: argparse.Namespace) -> int:
    try:
        repo, git_dir, manifest, _ = load_open_snapshot(
            Path(args.skill_dir).resolve() if args.skill_dir else None
        )
    except LookupError as error:
        print(str(error), file=sys.stderr)
        return EXIT_PRECONDITION

    skill_dir = Path(manifest["skill_dir"])
    findings = collect_findings(repo, manifest)
    workspace = Path(args.workspace).resolve() if args.workspace else None
    write_report(workspace, skill_dir, findings, manifest)

    if findings:
        print(
            f"fixture-guard: VIOLATED — {len(findings)} finding(s) in "
            f"{manifest['guarded_root']}; lock retained.",
            file=sys.stderr,
        )
        for finding in findings:
            print(f"  {finding['kind']}: {finding['path']}", file=sys.stderr)
        return EXIT_DAMAGE

    clear_lock(git_dir)
    print(
        f"fixture-guard: clean — {manifest['guarded_root']} is byte-identical; lock cleared."
    )
    return EXIT_CLEAN


# --------------------------------------------------------------------------- repair


def cmd_repair(args: argparse.Namespace) -> int:
    try:
        repo, git_dir, manifest, store = load_open_snapshot(
            Path(args.skill_dir).resolve() if args.skill_dir else None
        )
    except LookupError as error:
        print(str(error), file=sys.stderr)
        return EXIT_PRECONDITION

    guarded_rel = manifest["guarded_root"]
    guarded = repo / guarded_rel
    tree_store = store / "tree"
    findings = collect_findings(repo, manifest)
    actionable = [f for f in findings if f["kind"] in RESTORABLE]

    if not findings:
        clear_lock(git_dir)
        print("fixture-guard: nothing to repair — already clean; lock cleared.")
        return EXIT_CLEAN

    if not args.apply:
        print("fixture-guard: dry run — pass --apply to perform these actions:")
        for finding in findings:
            verb = {
                "created": "delete stray",
                "modified": "restore bytes",
                "mode-changed": "restore mode",
                "deleted-worktree": "recreate from snapshot",
                "staged-deletion": "un-stage (index only), then restore bytes",
                "staged-modify": "un-stage (index only), then restore bytes",
                "staged-add": "un-stage (index only)",
                "transient-write": "nothing to restore — stays a finding",
            }[finding["kind"]]
            print(f"  {verb}: {finding['path']}")
        return EXIT_DAMAGE

    # 1. Un-stage first, path by path. An index-only reset undoes a staged deletion without
    #    touching the worktree, which is what keeps this off the force-deferred restore verbs.
    staged = [f for f in actionable if f.get("repo_relative")]
    for finding in staged:
        result = git_allow_fail(repo, "reset", "--", finding["path"])
        if result.returncode != 0:
            print(
                f"fixture-guard: could not un-stage {finding['path']}: "
                f"{result.stderr.strip()}",
                file=sys.stderr,
            )

    # 2. Restore content from the snapshot bytes.
    for finding in actionable:
        if finding["kind"] == "created":
            continue
        relpath = (
            str(Path(finding["path"]).relative_to(guarded_rel))
            if finding.get("repo_relative")
            else finding["path"]
        )
        if relpath not in manifest["files"]:
            continue
        source = tree_store / relpath
        target = guarded / relpath
        if not source.exists():
            print(
                f"fixture-guard: snapshot bytes missing for {relpath}", file=sys.stderr
            )
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        os.chmod(target, manifest["files"][relpath]["mode"])

    # 3. Remove strays, then prune directories the snapshot never had.
    strays = [f["path"] for f in actionable if f["kind"] == "created"]
    for relpath in strays:
        stray = guarded / relpath
        if stray.is_file():
            os.unlink(stray)
    for relpath in sorted({str(Path(p).parent) for p in strays}, key=len, reverse=True):
        if relpath in manifest["dirs"] or relpath == ".":
            continue
        candidate = guarded / relpath
        try:
            if candidate.is_dir() and not any(candidate.iterdir()):
                os.rmdir(candidate)
        except OSError:
            pass

    remaining = [f for f in collect_findings(repo, manifest) if f["kind"] in RESTORABLE]
    workspace = Path(args.workspace).resolve() if args.workspace else None
    ghosts = [f for f in collect_findings(repo, manifest) if f["kind"] == "transient-write"]
    write_report(workspace, Path(manifest["skill_dir"]), remaining + ghosts, manifest)

    if remaining:
        print(
            f"fixture-guard: repair incomplete — {len(remaining)} finding(s) resisted:",
            file=sys.stderr,
        )
        for finding in remaining:
            print(f"  {finding['kind']}: {finding['path']}", file=sys.stderr)
        return EXIT_REPAIR_INCOMPLETE

    clear_lock(git_dir)
    message = "fixture-guard: repaired — guarded tree restored; lock cleared."
    if ghosts:
        message += (
            f"\n  {len(ghosts)} transient-write finding(s) remain in the report: a write "
            "reached the fixture even though its bytes are correct."
        )
    print(message)
    return EXIT_CLEAN


# --------------------------------------------------------------------------- audit


def cmd_audit(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    repo = find_repo_root(skill_dir)
    guarded = skill_dir / "evals" / "inputs"
    if not guarded.exists():
        print(f"fixture-guard: no fixture tree at {guarded}")
        return EXIT_CLEAN
    guarded_rel = str(guarded.relative_to(repo))

    dirty = porcelain(repo, guarded_rel)
    print(f"fixture-guard: audit of {guarded_rel}")
    if dirty:
        print("  working tree vs HEAD:")
        for code, path in dirty:
            print(f"    {code} {path}")
    else:
        print("  working tree vs HEAD: clean")

    # Ghost-write heuristic: a directory whose mtime is well past every entry inside it had something
    # created and removed. This is what surfaced two past incidents that left no git trace.
    #
    # Compare against every entry, subdirectories included — creating a subdirectory bumps the
    # parent's mtime too — and require a real gap. Writing the last file in a directory leaves the
    # directory a few microseconds newer than that file, which is ordinary authoring, not a ghost.
    # `verify` needs none of this slack: it diffs exact mtimes against a snapshot.
    gap_ns = int(args.min_gap_seconds * 1e9)
    ghosts = []
    for current, subdirs, filenames in os.walk(guarded):
        directory = Path(current)
        entries = [
            (directory / name).stat().st_mtime_ns for name in (*filenames, *subdirs)
        ]
        if not entries:
            continue
        dir_ns = directory.stat().st_mtime_ns
        if dir_ns - max(entries) > gap_ns:
            ghosts.append((str(directory.relative_to(repo)), dir_ns, max(entries)))
    if ghosts:
        print(
            f"  suspected past writes (directory mtime more than {args.min_gap_seconds:g}s "
            "past every entry inside it):"
        )
        for path, dir_ns, file_ns in ghosts:
            print(
                f"    {path}\n"
                f"      dir  {datetime.fromtimestamp(dir_ns / 1e9).isoformat(timespec='seconds')}"
                f"  >  newest file "
                f"{datetime.fromtimestamp(file_ns / 1e9).isoformat(timespec='seconds')}"
            )
    else:
        print("  no directory is meaningfully newer than its contents")
    return EXIT_DAMAGE if dirty else EXIT_CLEAN


# --------------------------------------------------------------------------- cli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fixture_guard.py",
        description="Guard a skill's eval fixtures across a skill-evals run.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    snap = sub.add_parser("snapshot", help="capture the guarded tree and open the lock")
    snap.add_argument("--skill-dir", required=True)
    snap.add_argument("--snapshot-root", default=None)
    snap.add_argument("--allow-dirty-inputs", action="store_true")
    snap.add_argument("--supersede", action="store_true")
    snap.set_defaults(func=cmd_snapshot)

    check = sub.add_parser("verify", help="detect movement; never repairs")
    check.add_argument("--skill-dir", default=None)
    check.add_argument("--workspace", default=None)
    check.set_defaults(func=cmd_verify)

    fix = sub.add_parser("repair", help="restore the guarded tree from the snapshot")
    fix.add_argument("--skill-dir", default=None)
    fix.add_argument("--workspace", default=None)
    fix.add_argument("--apply", action="store_true")
    fix.set_defaults(func=cmd_repair)

    look = sub.add_parser("audit", help="snapshot-free check against HEAD")
    look.add_argument("--skill-dir", required=True)
    look.add_argument(
        "--min-gap-seconds",
        type=float,
        default=60.0,
        help="report a directory only when its mtime is this far past every entry inside it "
        "(default 60; a few microseconds is ordinary authoring, not a ghost write)",
    )
    look.set_defaults(func=cmd_audit)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except subprocess.CalledProcessError as error:
        print(
            f"fixture-guard: git failed: {' '.join(error.cmd)}\n{error.stderr}",
            file=sys.stderr,
        )
        return EXIT_PRECONDITION


if __name__ == "__main__":
    sys.exit(main())
