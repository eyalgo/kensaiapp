"""A scratch instance for tests that drive a real launcher.

A launcher runs from an instance root and refuses a project that root does not hold. A test that
ran it from this repository borrowed one of this instance's own projects and its untracked
`.providers.toml`, so it failed wherever those are absent — a clone of the release among them. This
builds the instance instead: this repository's machinery by link, and a project, a provider file and
a git repository of its own.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# What a launcher reads from an instance root and the test does not own: the machinery, linked.
_LINKED = (".claude", "skills", "core", "AGENTS.md")


def scratch_instance(root: Path, project: str) -> Path:
    """`root/instance`, built once: the machinery linked from this repository,
    `system/projects/<project>/project.md` and the product folder it names,
    `products/<project>/`, the delivered `.providers.toml.example` as its
    `.providers.toml`, and `git init` — an instance is a repository, and a run's `kensai.instance`
    is derived from it. A second call with the same `root` returns the same instance."""
    instance = root / "instance"
    if instance.is_dir():
        return instance
    instance.mkdir(parents=True)
    for name in _LINKED:
        (instance / name).symlink_to(REPO / name)
    card = instance / "system" / "projects" / project / "project.md"
    card.parent.mkdir(parents=True)
    card.write_text(f"# Project Context — {project}\n\n**Product path:** products/{project}\n")
    (instance / "products" / project).mkdir(parents=True)
    shutil.copy2(REPO / ".providers.toml.example", instance / ".providers.toml")
    subprocess.run(["git", "init", "-q", str(instance)], check=True)
    return instance
