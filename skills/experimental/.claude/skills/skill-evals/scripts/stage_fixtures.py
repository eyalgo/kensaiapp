#!/usr/bin/env python3
"""Gives each eval run its own copy of the fixtures, so a skill that obeys its own contract can be run.

A fixture's `Product path:` is relative and resolves into `evals/inputs/` — the tree `fixture_guard.py`
protects. So a producer skill that "owns its file locations" resolves *into its own inputs*, and a run
that obeys the skill trips the guard: writing a file is a `created` finding, retiring one is
`deleted-worktree`, and the run halts before grading. Until now that conflict was masked, because every
archived with-skill executor sandboxed itself instead of obeying the skill — which means the assertions
about where files land were passing for the wrong reason.

Staging resolves it at the root. Each (case × configuration) gets its own copy of the fixture tree under
the run's workspace, and the copy's `project.md` is rewritten so `Product path:` names the copy. Then:

  - the skill writes where it says it writes, and the path is real;
  - the guarded tree is never touched, so the guard cannot fire on an obedient run;
  - the two arms stop sharing one tree, so one arm's write cannot become the other's input;
  - `workspace/` is already gitignored, so none of it dirties the repo.

The rewritten path stays **relative** on purpose. An absolute one would flip the skill to its
"the repo *is* the product" branch and change which repo its commit step targets — the eval would then
exercise a different code path than production does.

The inputs-root `README.md` is deliberately **not** copied: it carries the per-case annotations, and a
staged tree is exactly what an executor rummages through when it cannot list a directory.

Usage:
    stage_fixtures.py --skill-dir <abs> --workspace <abs>

Prints JSON to stdout: the repo root, and per case/config the staged inputs root, the binding path, and
the rewritten prompt. A skill with no `evals/inputs/` is a clean no-op.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCHEMA_VERSION = 1
PRODUCT_PATH_RE = re.compile(r"^(\s*\*\*Product path:\*\*\s*)(\S+)(.*)$", re.MULTILINE)


def repo_root_of(path: Path) -> Path:
    out = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(out.stdout.strip())


def ignore_annotations(root: Path):
    """Copy everything except the inputs-root README (the annotations) and caches.

    A callable rather than `ignore_patterns("README.md")`, which would also drop a README nested inside
    a fixture — that one is product content and belongs in the copy.
    """

    def _ignore(directory: str, names: list[str]) -> set[str]:
        drop = {n for n in names if n == "__pycache__"}
        if Path(directory).resolve() == root.resolve():
            drop |= {n for n in names if n == "README.md"}
        return drop

    return _ignore


def rewrite_binding(project_md: Path, staged_product_rel: str) -> bool:
    """Point a staged project.md's `Product path:` at its own copy. Returns True if rewritten.

    Only the path token changes, and the line's trailing comment is dropped: those comments describe the
    tracked fixture's placement and claim a sandbox that the harness does not implement, so carrying them
    into a staged copy would ship a false statement into the executor's own input.
    """
    if not project_md.is_file():
        return False
    text = project_md.read_text()
    new_text, count = PRODUCT_PATH_RE.subn(
        lambda m: f"{m.group(1)}{staged_product_rel}", text, count=1
    )
    if count:
        project_md.write_text(new_text)
    return bool(count)


def stage_one(
    fixture_root: Path, dest_inputs: Path, repo: Path
) -> dict[str, str]:
    """Copy the fixture tree to dest_inputs and repoint every project.md inside it."""
    if dest_inputs.exists():
        shutil.rmtree(dest_inputs)
    dest_inputs.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(fixture_root, dest_inputs, ignore=ignore_annotations(fixture_root))

    bindings: dict[str, str] = {}
    for project_md in sorted(dest_inputs.glob("*/project.md")):
        product_dir = project_md.parent
        staged_rel = str(product_dir.relative_to(repo))
        if rewrite_binding(project_md, staged_rel):
            bindings[product_dir.name] = staged_rel

    # Hash the tree AFTER the binding rewrite, so the baseline harvest diffs against is "the tree as
    # staged". Diffing against the pristine fixture instead would report staging's own edit to every
    # project.md as a change the run made.
    write_staged_manifest(dest_inputs)
    return bindings


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_staged_manifest(dest_inputs: Path) -> None:
    """Record every staged file's hash beside the copy, for harvest to diff against."""
    files = {
        str(p.relative_to(dest_inputs)): sha256_of(p)
        for p in sorted(dest_inputs.rglob("*"))
        if p.is_file() and not p.is_symlink() and "__pycache__" not in p.parts
    }
    (dest_inputs.parent / "staged_manifest.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "files": files}, indent=2) + "\n"
    )


def rewrite_prompt(prompt: str, fixture_root: Path, staged_root: Path, repo: Path) -> str:
    """Point a case prompt at the staged tree, in whichever spelling it used.

    Prompts name the fixture repo-relatively today; an absolute spelling is handled too so a future
    evals.json cannot silently keep reading the tracked tree. A `~/`-rooted path is left alone: that is
    another instance's fixture, outside this repo.
    """
    staged_rel = str(staged_root.relative_to(repo))
    for spelling in (str(fixture_root), str(fixture_root.relative_to(repo))):
        prompt = prompt.replace(spelling, staged_rel)
    return prompt.replace("${FIXTURES}", staged_rel)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stage_fixtures.py",
        description="Give each eval run its own writable copy of the fixtures.",
    )
    parser.add_argument("--skill-dir", required=True)
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args(argv)

    skill_dir = Path(args.skill_dir).resolve()
    workspace = Path(args.workspace).resolve()
    if not skill_dir.is_dir():
        print(f"stage-fixtures: no such skill dir: {skill_dir}", file=sys.stderr)
        return 2

    evals_file = skill_dir / "evals" / "evals.json"
    if not evals_file.is_file():
        print(f"stage-fixtures: no evals.json at {evals_file}", file=sys.stderr)
        return 2

    try:
        data = json.loads(evals_file.read_text())
    except json.JSONDecodeError as error:
        print(f"stage-fixtures: unreadable evals.json: {error}", file=sys.stderr)
        return 2

    repo = repo_root_of(skill_dir)
    fixture_root = skill_dir / "evals" / "inputs"

    # The staged `Product path:` must stay repo-relative (see the module docstring), so the workspace has
    # to live inside the repo. In practice it always does — `<skill-dir>/evals/workspace/iteration-N` —
    # but say so rather than failing later on an unrelatable path.
    if not workspace.is_relative_to(repo):
        print(
            f"stage-fixtures: workspace must be inside the repo, because a staged Product path stays "
            f"repo-relative.\n  workspace: {workspace}\n  repo:      {repo}",
            file=sys.stderr,
        )
        return 2

    if not fixture_root.is_dir():
        # Skills whose prompts are self-contained have nothing to stage.
        print(json.dumps({"schema_version": SCHEMA_VERSION, "fixture_root": None, "cases": {}}))
        print(
            f"stage-fixtures: no fixture tree at {fixture_root} — nothing to stage",
            file=sys.stderr,
        )
        return 0

    cases: dict[str, dict] = {}
    for case in data.get("evals", []):
        name = case.get("name") or str(case.get("id"))
        prompt = case.get("prompt", "")
        cases[name] = {}
        for config in ("with_skill", "without_skill"):
            staged_root = workspace / name / config / "inputs"
            bindings = stage_one(fixture_root, staged_root, repo)
            cases[name][config] = {
                "inputs_root": str(staged_root),
                "inputs_root_rel": str(staged_root.relative_to(repo)),
                "bindings": bindings,
                "prompt": rewrite_prompt(prompt, fixture_root, staged_root, repo),
            }

    payload = {
        "schema_version": SCHEMA_VERSION,
        "repo_root": str(repo),
        "fixture_root": str(fixture_root),
        "cases": cases,
    }
    (workspace / "stage_manifest.json").parent.mkdir(parents=True, exist_ok=True)
    (workspace / "stage_manifest.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload))

    staged = sum(len(c) for c in cases.values())
    print(
        f"stage-fixtures: staged {staged} fixture copies for {len(cases)} case(s) under "
        f"{workspace.name}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
