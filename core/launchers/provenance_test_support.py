"""Shared by every instrumented launcher's suite: its printed `Telemetry:` line stamps exactly the
provenance the run was handed, after the pairs it stamped before (CP-218, CP-227). A launcher that
consults its own skill's intelligence is run from an `isolated_host`, where the test decides what
that skill holds.

The check that a launcher's `run_telemetry` call hands over the four provenance keys on the call's
own line (CP-229, CP-230) is `assert_run_telemetry_call_carries_provenance` in
`core/tools/launcher_telemetry_test_support.py`. Each launcher's suite imports it from there, so one
reader answers that question for every suite.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

__version__ = "1.1.0"

PROVENANCE_KEYS = ("provider", "model", "effort", "source")

_TELEMETRY = "Telemetry:"
_ENDPOINT_ARROW = " → "


def telemetry_pairs(output: str) -> list[tuple[str, str]]:
    """The `kensai.*` pairs on a launch's one printed `Telemetry:` line, in order, each key without
    its `kensai.` prefix. A launch that printed no attribute list fails here rather than answering
    an empty list a caller could read as "nothing stamped"."""
    lines = [line for line in output.splitlines() if line.strip().startswith(_TELEMETRY)]
    assert len(lines) == 1, f"expected one {_TELEMETRY} line, found {len(lines)}: {output!r}"
    attributes = lines[0].split(_TELEMETRY, 1)[1].rsplit(_ENDPOINT_ARROW, 1)[0].strip()
    pairs = []
    for attribute in attributes.split(","):
        key, separator, value = attribute.partition("=")
        if separator and key.startswith("kensai."):
            pairs.append((key.removeprefix("kensai."), value))
    assert pairs, f"the {_TELEMETRY} line carries no kensai.* attribute: {lines[0]!r}"
    return pairs


def assert_provenance_stamped(
    output: str,
    *,
    provider: str,
    model: str = "",
    effort: str = "",
    source: str = "",
    after: tuple[str, ...] = (),
) -> None:
    """The line stamps exactly these provenance pairs, in `PROVENANCE_KEYS` order — an empty value
    is a key that must be absent, as `run_telemetry` drops it — and every one of them follows each
    key named in `after`, the pairs the launcher stamped before this change."""
    pairs = telemetry_pairs(output)
    expected = [
        (key, value)
        for key, value in zip(PROVENANCE_KEYS, (provider, model, effort, source))
        if value
    ]
    stamped = [pair for pair in pairs if pair[0] in PROVENANCE_KEYS]
    assert stamped == expected, f"stamped {stamped}, expected {expected}"
    keys = [key for key, _ in pairs]
    first_provenance = min(keys.index(key) for key, _ in stamped)
    for key in after:
        assert key in keys, f"the existing pair {key} is no longer stamped: {pairs}"
        assert keys.index(key) < first_provenance, (
            f"the existing pair {key} no longer precedes the provenance pairs: {pairs}"
        )


_CORE = Path(__file__).resolve().parents[1]

# What a launcher that resolves its own skill reaches before it spawns, dry run included: the pin
# (`pin_enter` sources `pin_run.sh`, which runs `pin.py`), the one Claude builder and its imports,
# the skill resolver, the one intelligence resolution and its two readers, and the provider reader
# (a launcher asks `providers.py` which provider it goes to; the file it reads is the instance's
# own `.providers.toml`, which a case writes at the instance it runs for). The telemetry helper,
# `run_telemetry.sh`, is not copied, so a launch from this host prints its `(no instrument library
# at … — run uninstrumented)` line and runs untagged.
HOST_TOOLS = (
    "pin.py",
    "pin_run.sh",
    "agent_run.py",
    "hook_wiring.py",
    "model_assignment.py",
    "task_context.py",
    "env_file.py",
    "skill_path.py",
    "run_intelligence.py",
    "intelligence.py",
    "providers.py",
)


def isolated_host(root: Path, script: Path, *, tools: tuple[str, ...] = HOST_TOOLS) -> Path:
    """A host at `root` holding a copy of `script` at `core/launchers/<its folder>/launcher.sh`,
    beside `core/tools/` with exactly `tools` copied from the real core, and a `pin.json` marking
    `root` as its own pin — so `pin_enter` neither re-execs nor copies, and the launcher's host root
    (`${CORE_DIR%/core}`) is `root`, where a test places, or leaves out, the launcher's own skill.
    Returns the copied launcher."""
    launcher_dir = root / "core" / "launchers" / script.parent.name
    launcher_dir.mkdir(parents=True)
    copied = launcher_dir / script.name
    copied.write_text(script.read_text())
    copied.chmod(0o755)
    tools_dir = root / "core" / "tools"
    tools_dir.mkdir()
    for tool in tools:
        shutil.copy(_CORE / "tools" / tool, tools_dir / tool)
    (root / "pin.json").write_text(
        json.dumps(
            {
                "id": "isolated",
                "source_host_root": str(root),
                "created": "1970-01-01T00:00:00+00:00",
            }
        )
        + "\n"
    )
    return copied


def place_own_skill(root: Path, name: str, intelligence: str | None = None) -> Path:
    """The launcher's own skill at `<root>/.claude/skills/<name>`, with `intelligence/claude.md`
    holding `intelligence` when one is given. Returns the skill dir."""
    skill_dir = root / ".claude" / "skills" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\n---\n")
    if intelligence is not None:
        (skill_dir / "intelligence").mkdir()
        (skill_dir / "intelligence" / "claude.md").write_text(intelligence)
    return skill_dir


# The two own-skill intelligence folders the one resolution refuses: `missing` holds no file for
# the provider (the resolver's exit 4), `malformed` holds a broken one (exit 2). A launcher that
# consults its own skill turns either into a refusal carrying the reader's own words.
REFUSED_OWN_INTELLIGENCE = {
    "missing": ("codex.md", "**Model:** gpt-6-luna\n"),
    "malformed": ("claude.md", "**Model:** opus\n"),
}


def place_refused_own_skill(root: Path, name: str, kind: str) -> str:
    """The launcher's own skill at `<root>/.claude/skills/<name>`, whose intelligence folder is the
    `kind` of `REFUSED_OWN_INTELLIGENCE`. Returns the exact stderr `intelligence.py` gives for it —
    the words the launcher's refusal must repeat behind its own prefix."""
    skill_dir = place_own_skill(root, name)
    file_name, text = REFUSED_OWN_INTELLIGENCE[kind]
    (skill_dir / "intelligence").mkdir()
    (skill_dir / "intelligence" / file_name).write_text(text)
    reference = subprocess.run(
        [sys.executable, str(_CORE / "tools" / "intelligence.py"),
         "--skill-dir", str(skill_dir), "--provider", "claude"],
        capture_output=True, text=True,
    )
    assert reference.returncode in (2, 4), reference
    return reference.stderr
