#!/usr/bin/env python3
"""Records what a run did to its staged product, so grading reads a fact instead of guessing a path.

With fixtures staged per run (`stage_fixtures.py`), a skill writes where its own contract says — under
`<staged Product path>/docs/...`. That is the right thing, but it leaves the evidence somewhere the
grader cannot reliably find: the grading prompt hands over `outputs/` and nothing instructs a recursive
read, `agents/grader.md` says "List files in outputs_dir", and the viewer's `build_run` silently drops
directories. Before staging, executors improvised — some wrote `outputs/SRS.md`, some
`outputs/docs/SRS.md`, one wrote `srs.md` — so an assertion naming a path was grading a coin flip.

This closes that. Harvest diffs the staged product against the pristine fixture and writes three things
into `outputs/`, all at the top level where every reader already looks:

  - `run_delta.json` — created / modified / deleted, as product-relative paths. An assertion about
    *where* a file landed is checked against this, not against a directory walk.
  - `product/<relpath>` — the files the run created or modified, path preserved, so content assertions
    have something to read.
  - `reference/<relpath>` — the pristine version of every file the run modified or deleted. This is what
    makes "the answered companion is retired WHOLE" checkable: the grader gets both sides. Without it,
    wholeness degrades to "mentions a few expected strings".

`deleted` is the entry that earns the most. A skill whose done-signal is removing a file could never be
tested for it while executors wrote into a sandbox — the file was never there to remove. Now its removal
is a recorded positive fact.

Usage:
    harvest_run.py --config-dir <abs>   # the <case>/<config> dir holding inputs/ and outputs/
    [--fixture-root <abs>]              # defaults to the pristine tree named in stage_manifest.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

SCHEMA_VERSION = 1


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_map(root: Path) -> dict[str, Path]:
    """Every file under root, keyed by its path relative to root."""
    if not root.is_dir():
        return {}
    return {
        str(p.relative_to(root)): p
        for p in sorted(root.rglob("*"))
        if p.is_file() and not p.is_symlink() and "__pycache__" not in p.parts
    }


def find_fixture_root(config_dir: Path) -> Path | None:
    """The pristine tree, read from the staging manifest at the workspace root."""
    for parent in config_dir.parents:
        manifest = parent / "stage_manifest.json"
        if manifest.is_file():
            try:
                root = json.loads(manifest.read_text()).get("fixture_root")
            except (json.JSONDecodeError, OSError):
                return None
            return Path(root) if root else None
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="harvest_run.py",
        description="Diff a run's staged product against the pristine fixture and record the delta.",
    )
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--fixture-root", default=None)
    args = parser.parse_args(argv)

    config_dir = Path(args.config_dir).resolve()
    staged = config_dir / "inputs"
    outputs = config_dir / "outputs"

    if not staged.is_dir():
        print(
            f"harvest: no staged inputs at {staged} — nothing to harvest "
            "(a case with no fixture is a clean no-op)",
            file=sys.stderr,
        )
        return 0

    fixture_root = (
        Path(args.fixture_root).resolve() if args.fixture_root else find_fixture_root(config_dir)
    )

    # The baseline is the tree AS STAGED, recorded by stage_fixtures after it rewrote each project.md's
    # `Product path:`. Diffing against the pristine fixture instead would report staging's own edit to
    # every project.md as a change the run made — noise in exactly the file assertions care least about.
    manifest_file = config_dir / "staged_manifest.json"
    if not manifest_file.is_file():
        print(
            f"harvest: no staged_manifest.json at {manifest_file} — this run's fixtures were not "
            "staged, so there is no baseline to diff against.",
            file=sys.stderr,
        )
        return 2
    try:
        before_hashes: dict[str, str] = json.loads(manifest_file.read_text())["files"]
    except (json.JSONDecodeError, KeyError, OSError) as error:
        print(f"harvest: unreadable staged manifest: {error}", file=sys.stderr)
        return 2

    after = file_map(staged)
    created = sorted(k for k in after if k not in before_hashes)
    deleted = sorted(k for k in before_hashes if k not in after)
    modified = sorted(
        k for k in after if k in before_hashes and sha256_of(after[k]) != before_hashes[k]
    )

    # `reference/` needs bytes, and the staged originals are gone — the run overwrote them. The pristine
    # fixture is the only surviving copy, and it is byte-identical to what was staged for everything
    # except project.md, which never appears in the delta.
    pristine = file_map(fixture_root) if fixture_root and fixture_root.is_dir() else {}

    outputs.mkdir(parents=True, exist_ok=True)

    for relpath in created + modified:
        target = outputs / "product" / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(after[relpath], target)

    missing_reference: list[str] = []
    for relpath in modified + deleted:
        source = pristine.get(relpath)
        if source is None:
            missing_reference.append(relpath)
            continue
        target = outputs / "reference" / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    delta = {
        "schema_version": SCHEMA_VERSION,
        "product_root": str(staged),
        "fixture_root": str(fixture_root),
        "created": created,
        "modified": modified,
        "deleted": deleted,
        "reference_unavailable": missing_reference,
        "note": (
            "Paths are relative to the run's staged product root. 'product/' holds what the run wrote; "
            "'reference/' holds the pristine version of anything it modified or deleted, so a "
            "before/after comparison is possible without reaching outside outputs/."
        ),
    }
    (outputs / "run_delta.json").write_text(json.dumps(delta, indent=2) + "\n")

    print(
        f"harvest: {len(created)} created, {len(modified)} modified, {len(deleted)} deleted "
        f"→ {outputs.parent.name}/{outputs.name}/run_delta.json"
    )
    for kind, items in (("created", created), ("modified", modified), ("deleted", deleted)):
        for relpath in items:
            print(f"  {kind}: {relpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
