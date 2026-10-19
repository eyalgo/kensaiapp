"""manifest.py — parse + validate the stack manifest.

Turns a skill's `stack.json` into a validated `Stack`, or raises `ManifestError`. Knows nothing
about launching, watching, or outcomes — only the manifest's shape and the containment rule.

`stack.json` is DATA beside the skill's SKILL.md — the ordered substance set the cold-read reads, one
isolated cold-read loop per file, in array order (doctrine's "skill first, then the prompt"):

    { "version": 1, "substance": ["skills/<group>/.claude/skills/<skill>/SKILL.md", "skills/<group>/.claude/skills/<skill>/prompts/rich.md"] }

Templates are deliberately absent (they are recommended supplements, never read subjects — the read
scope is owned by <CORE>/doctrine/kaizen/skills.md, and this data follows it). Values are `--file`
values verbatim: repo-relative paths, validated here exactly as the launcher validates `--file`
(relative, and resolving to a file under the instance root) — so a renamed prompt breaks the read
LOUDLY at entry, not silently at link 2 four hours in. Defense in depth, not a moved check: the
launcher still re-validates each path per link.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import skill_path

SCHEMA_VERSION = 1


class ManifestError(Exception):
    """A stack.json that cannot be trusted as a run plan. The entry converts it to a die()
    before any link launches."""


@dataclass(frozen=True)
class Stack:
    substance: tuple[str, ...]   # ordered, len >= 1, each repo-relative, each an existing file


def _derive_root(skill_dir: str) -> str:
    """The instance root, given a skill's directory under either layout — delegates to
    `skill_path.instance_root`, which recognises both the flat and the grouped shape. This is
    the default behind an omitted `root`; a caller that already knows the root passes it."""
    return str(skill_path.instance_root(skill_dir))


def load_stack(skill_dir: str, root: str | None = None) -> Stack:
    """Load and validate `<skill_dir>/stack.json`. Raise ManifestError on any untrustworthy input.

    `root` is the instance root that repo-relative substance paths resolve against; derived from
    `skill_dir` when omitted (a caller running from the root can pass it explicitly).
    """
    root = root if root is not None else _derive_root(skill_dir)
    manifest_path = os.path.join(skill_dir, "stack.json")

    try:
        with open(manifest_path, encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        raise ManifestError(f"no stack.json at {manifest_path}: {exc} "
                            f"(every skill needs one — a single-file skill declares a one-entry manifest: "
                            f'{{ \"version\": 1, \"substance\": [\"<path to its one substance file>\"] }})')

    try:
        data = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise ManifestError(f"stack.json at {manifest_path} is not valid JSON: {exc}")

    if not isinstance(data, dict):
        raise ManifestError(f"stack.json at {manifest_path} must be a JSON object")

    if data.get("version") != SCHEMA_VERSION:
        raise ManifestError(
            f"stack.json at {manifest_path} has version {data.get('version')!r}; "
            f"this tool understands version {SCHEMA_VERSION}"
        )

    substance = data.get("substance")
    if not isinstance(substance, list) or not substance:
        raise ManifestError(
            f"stack.json at {manifest_path} needs a non-empty 'substance' array (the ordered read set)"
        )

    root_real = os.path.realpath(root)
    validated: list[str] = []
    for entry in substance:
        validated.append(_validate_path(entry, root_real, manifest_path))

    return Stack(substance=tuple(validated))


def _validate_path(entry, root_real: str, manifest_path: str) -> str:
    """A substance entry must be a non-empty, relative string resolving to a file under the root.
    Returns the entry unchanged on success; raises ManifestError otherwise."""
    if not isinstance(entry, str) or not entry:
        raise ManifestError(
            f"stack.json at {manifest_path}: every 'substance' entry must be a non-empty "
            f"repo-relative path string (got {entry!r})"
        )
    if os.path.isabs(entry):
        raise ManifestError(
            f"stack.json at {manifest_path}: 'substance' path {entry!r} is absolute; "
            f"paths are repo-relative to the instance root"
        )

    abs_path = os.path.realpath(os.path.join(root_real, entry))
    # Containment: the resolved path must sit inside the instance root (rejects ../ and symlink-out).
    if abs_path != root_real and not abs_path.startswith(root_real + os.sep):
        raise ManifestError(
            f"stack.json at {manifest_path}: 'substance' path {entry!r} resolves outside "
            f"the instance root ({root_real}); refusing"
        )
    if not os.path.isfile(abs_path):
        raise ManifestError(
            f"stack.json at {manifest_path}: 'substance' path {entry!r} does not exist "
            f"under the instance root — a renamed or removed file breaks the read at entry"
        )
    return entry
