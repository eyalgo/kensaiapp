"""Tests for the owner's ask as the two walk launchers carry it.

The real launcher scripts run, each against a recording engine in place of the chain, so no walk
starts, no step launches and no suite is issued. What the engine does with the ask is
`test_chain_development.py`'s to pin (state, transport); this file pins what the launchers hand it:
the engine's own `--gate-owners-mac` argument exactly when the owner supplied it on the command
line, and never from the environment, a card or a pending record the owner did not write.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path

import pytest

CORE_ROOT = Path(__file__).resolve().parent.parent
DEVELOPMENT_LAUNCHER = CORE_ROOT / "launchers" / "chain-development" / "launcher.sh"
CHANGE_LAUNCHER = CORE_ROOT / "launchers" / "chain-change" / "launcher.sh"
ASK = "--gate-owners-mac"

# One recording engine. Each call appends its argv to a JSON-lines log, so a test reads every call
# in order; `--describe` answers a change and a step, and every other call exits 0.
ENGINE_STUB = """#!/usr/bin/env python3
import json, os, sys
with open(os.environ["ENGINE_CALLS"], "a") as handle:
    handle.write(json.dumps(sys.argv[1:]) + "\\n")
if "--describe" in sys.argv:
    print("key=2026-10-14_stub-change")
    print("entry=design")
sys.exit(0)
"""


# The definition walk's engine, behind chain-product and chain-agari, which run for real: it records
# its argv and can fire the `--on-end` hook it was handed, the way the engine does at a walk's end.
DEFINITION_STUB = """#!/usr/bin/env python3
import json, os, shlex, subprocess, sys
with open(os.environ["DEFINITION_CALLS"], "a") as handle:
    handle.write(json.dumps(sys.argv[1:]) + "\\n")
if int(os.environ.get("DEF_STUB_EXIT", "0")):
    print("refused", file=sys.stderr)
    sys.exit(int(os.environ["DEF_STUB_EXIT"]))
"""

SIBLING_OF = {"full": "product", "prd-agari": "agari"}


class Launcher:
    """One launcher run in a temporary instance root with a recording engine."""

    def __init__(self, root: Path, script: Path, engine_variable: str) -> None:
        self.root = root
        self.script = script
        engine = root / "engine_stub.py"
        engine.write_text(ENGINE_STUB)
        engine.chmod(0o755)
        self.calls_path = root / "engine_calls.jsonl"
        self.env = dict(os.environ)
        for name in ("KENSAIAPP_NOTIFIER", "KENSAIAPP_GATE_OWNERS_MAC", "KENSAIAPP_AGENT_PROVIDER"):
            self.env.pop(name, None)
        self.definition_path = root / "definition_calls.jsonl"
        definition = root / "definition_stub.py"
        definition.write_text(DEFINITION_STUB)
        definition.chmod(0o755)
        self.env.update({engine_variable: str(engine), "ENGINE_CALLS": str(self.calls_path),
                         "DEFINITION_CALLS": str(self.definition_path),
                         "LAUNCH_CHAIN_PRODUCT_SCRIPT": str(definition),
                         "LAUNCH_CHAIN_AGARI_SCRIPT": str(definition),
                         "HOME": str(root / "home")})
        (root / "home").mkdir()

    def project(self, name: str, card: str | None = None, product_path: str = "products/thing",
                definition: str | None = None) -> None:
        folder = self.root / "system" / "projects" / name
        folder.mkdir(parents=True)
        text = card if card is not None else f"# {name}\n\n**Product path:** {product_path}\n"
        if definition is not None:
            text += f"**Definition:** {definition}\n"
        (folder / "project.md").write_text(text)

    def run(self, *arguments: str, env: dict | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([str(self.script), *arguments], cwd=str(self.root),
                              capture_output=True, text=True, env={**self.env, **(env or {})})

    def reset(self) -> None:
        self.calls_path.unlink(missing_ok=True)
        self.definition_path.unlink(missing_ok=True)

    def calls(self) -> list[list[str]]:
        if not self.calls_path.exists():
            return []
        return [json.loads(line) for line in self.calls_path.read_text().splitlines()]

    def starts(self) -> list[list[str]]:
        return [call for call in self.calls() if call and call[0] == "--start"]

    def describes(self) -> list[list[str]]:
        return [call for call in self.calls() if call and call[0] == "--describe"]

    def definition_calls(self) -> list[list[str]]:
        if not self.definition_path.exists():
            return []
        return [json.loads(line) for line in self.definition_path.read_text().splitlines()]

    def pending(self) -> list[Path]:
        logs = self.root / "system" / "logs"
        return sorted(logs.glob("chain-change-*-pending.*")) if logs.exists() else []

    def fire(self, call: list[str], end: str, env: dict | None = None):
        """Run the end hook a definition walk was handed, as the engine does: split, end last."""
        hook = shlex.split(call[call.index("--on-end") + 1])
        return subprocess.run([*hook, end], cwd=str(self.root), capture_output=True, text=True,
                              env={**self.env, **(env or {})})


@pytest.fixture
def development(tmp_path):
    return Launcher(tmp_path, DEVELOPMENT_LAUNCHER, "LAUNCH_CHAIN_DEVELOPMENT_SCRIPT")


# ==================================================================================================
# chain-development
# ==================================================================================================


def test_development_launcher_forwards_only_explicit_ask(development):
    development.project("demo")

    assert development.run("demo").returncode == 0
    [plain] = development.starts()
    assert ASK not in plain

    development.reset()
    assert development.run("demo", ASK).returncode == 0
    [start] = development.starts()
    assert start[0] == "--start" and start.count(ASK) == 1

    # The ask is the flag's, whichever order the flags come in.
    development.reset()
    assert development.run("demo", "--keep-awake", ASK).returncode == 0
    [start] = development.starts()
    assert start.count(ASK) == 1 and "--keep-awake" in start

    # Not the inherited variable, and not anything the project's card says.
    development.reset()
    development.project("carded", card=("# carded\n\n**Product path:** products/thing\n"
                                        "**Gate owners mac:** yes\n**Owners mac:** 1\n"))
    result = development.run("carded", env={"KENSAIAPP_GATE_OWNERS_MAC": "1"})
    assert result.returncode == 0
    [start] = development.starts()
    assert ASK not in start


def test_development_launcher_dry_run_keeps_ask_without_launch(development):
    development.project("demo")

    result = development.run("demo", "--dry-run", ASK)

    assert result.returncode == 0, result.stderr
    # The reported start carries the ask; the engine was asked only to describe, never to start.
    reported = next(line for line in result.stdout.splitlines() if "--start" in line)
    assert ASK in reported.split()
    assert development.starts() == []
    [described] = development.describes()
    assert described[0] == "--describe" and ASK not in described
    without = development.run("demo", "--dry-run")
    assert ASK not in next(line for line in without.stdout.splitlines() if "--start" in line)


def test_development_launcher_stop_rejects_start_option(development):
    development.project("demo")

    result = development.run("demo", "--stop", ASK)

    assert result.returncode == 1
    assert "takes no other flag" in result.stderr
    assert development.calls() == []
    # A stop alone is unchanged: it reaches the engine's stop and carries no start option.
    alone = development.run("demo", "--stop")
    assert alone.returncode == 0
    [stop] = development.calls()
    assert stop[0] == "--stop" and ASK not in stop


def test_development_launcher_preserves_quoted_arguments(development, tmp_path):
    name = "my proj ; $(touch never) `x` $HOME"
    product = "products/the thing ; $(touch never)"
    development.project(name, product_path=product)

    result = development.run(name, ASK)

    assert result.returncode == 0, result.stderr
    [start] = development.starts()
    assert start[start.index("--project") + 1] == name
    assert start[start.index("--product-path") + 1] == f"{development.root}/{product}"
    assert ASK in start
    assert not (tmp_path / "never").exists() and not (Path.cwd() / "never").exists()


def test_development_launcher_help_names_the_option_after_keep_awake():
    text = DEVELOPMENT_LAUNCHER.read_text()

    usage = [line for line in text.splitlines() if "[--keep-awake]" in line and "usage" in line]
    assert usage and all("[--keep-awake] [--gate-owners-mac]" in line for line in usage)
    header = [line for line in text.splitlines() if line.startswith("#   <CORE>/launchers/")
              and "[--keep-awake]" in line]
    assert header and all("[--keep-awake] [--gate-owners-mac]" in line for line in header)
    assert "the owner's ask to run the card's test command on the owner's Mac" in text
    assert "No card field, product record or exported variable sets it." in text


# ==================================================================================================
# chain-change
# ==================================================================================================


@pytest.fixture
def change(tmp_path):
    return Launcher(tmp_path, CHANGE_LAUNCHER, "LAUNCH_CHAIN_CHANGE_SCRIPT")


def test_change_launcher_immediate_start_forwards_explicit_ask(change):
    change.project("demo", definition="none")

    assert change.run("demo").returncode == 0
    [plain] = change.starts()
    assert ASK not in plain

    change.reset()
    assert change.run("demo", ASK).returncode == 0
    [start] = change.starts()
    assert start[0] == "--start" and start.count(ASK) == 1
    assert start[start.index("--steps") + 1] == "change"

    # The same argument the development launcher hands its engine, whatever order it comes in.
    change.reset()
    assert change.run("demo", "--context-cap", "1000", ASK, "--keep-awake").returncode == 0
    [start] = change.starts()
    assert start.count(ASK) == 1 and "--keep-awake" in start and "1000" in start

    # Neither an inherited variable nor a card line asks.
    change.reset()
    change.project("carded", card=("# carded\n\n**Product path:** products/thing\n"
                                   "**Gate owners mac:** yes\n"), definition="none")
    assert change.run("carded", env={"KENSAIAPP_GATE_OWNERS_MAC": "1"}).returncode == 0
    [start] = change.starts()
    assert ASK not in start

    # A stop takes no other flag; the ask is one.
    change.reset()
    refused = change.run("demo", "--stop", ASK)
    assert refused.returncode == 1 and "takes no other flag" in refused.stderr
    assert change.calls() == []


def test_change_launcher_preserves_quoted_arguments(change, tmp_path):
    name = "my proj ; $(touch never) `x`"
    change.project(name, product_path="products/the thing ; $(touch never)", definition="none")

    result = change.run(name, ASK)

    assert result.returncode == 0, result.stderr
    [start] = change.starts()
    assert start[start.index("--project") + 1] == name
    assert start[start.index("--product-path") + 1] == (
        f"{change.root}/products/the thing ; $(touch never)")
    assert start.count(ASK) == 1 and not (tmp_path / "never").exists()


@pytest.mark.parametrize("definition", sorted(SIBLING_OF))
def test_definition_continuation_retains_pending_owner_ask(change, definition):
    change.project("demo", definition=definition)

    asked = change.run("demo", ASK, "--keep-awake")

    assert asked.returncode == 0, asked.stderr
    # The definition walk is handed no ask; the change walk waits in the record.
    [call] = change.definition_calls()
    assert ASK not in call and ASK not in " ".join(call)
    assert change.starts() == []
    [record] = change.pending()
    assert "gate_owners_mac=1\n" in record.read_text()

    # The continuation obeys its saved launch, whatever the environment and card say now.
    (change.root / "system/projects/demo/project.md").write_text(
        f"# demo\n\n**Product path:** elsewhere\n**Definition:** {definition}\n")
    fired = change.fire(call, "settled", env={"KENSAIAPP_GATE_OWNERS_MAC": ""})
    assert fired.returncode == 0, fired.stderr
    [start] = change.starts()
    assert start.count(ASK) == 1 and "--keep-awake" in start
    assert start[start.index("--product-path") + 1] == f"{change.root}/products/thing"

    # An owner start without the ask saves none, and a later ambient value cannot add one.
    change.reset()
    assert change.run("demo").returncode == 0
    [call] = change.definition_calls()
    [record] = change.pending()
    assert "gate_owners_mac=\n" in record.read_text()
    change.fire(call, "left_for_the_owner", env={"KENSAIAPP_GATE_OWNERS_MAC": "1"})
    [start] = change.starts()
    assert ASK not in start


def test_older_pending_record_has_no_owner_ask(change):
    change.project("demo", definition="full")
    logs = change.root / "system" / "logs"
    logs.mkdir(parents=True)
    token = "abc123"
    (logs / f"chain-change-demo-pending.{token}").write_text(
        f"product_path={change.root}/products/thing\nprovider=\nkeep_awake=\n"
        "context_cap=\nnotifier=\n")

    fired = change.run("demo", "--after-definition", token, "--definition-ended", "settled",
                       env={"KENSAIAPP_GATE_OWNERS_MAC": "1"})

    assert fired.returncode == 0, fired.stderr
    [start] = change.starts()
    assert start[0] == "--start" and ASK not in start


def test_pending_ask_cannot_survive_cancellation(change):
    change.project("demo", definition="full")

    # A stop removes the record the ask lives in, so the end hook finds no change walk waiting.
    assert change.run("demo", ASK).returncode == 0
    [call] = change.definition_calls()
    assert change.run("demo", "--stop").returncode == 0
    assert change.pending() == []
    fired = change.fire(call, "settled")
    assert fired.returncode == 0 and "nothing to start" in fired.stdout
    assert [c for c in change.starts()] == []

    # A refused definition start removes its own record and starts no change walk.
    change.reset()
    refused = change.run("demo", ASK, env={"DEF_STUB_EXIT": "3"})
    assert refused.returncode == 3
    assert change.pending() == [] and change.starts() == []

    # A claimed record cannot start a second walk, and a halted definition starts none.
    change.reset()
    assert change.run("demo", ASK).returncode == 0
    [call] = change.definition_calls()
    assert change.fire(call, "settled").returncode == 0
    assert change.fire(call, "settled").returncode == 0
    assert len(change.starts()) == 1

    change.reset()
    assert change.run("demo", ASK).returncode == 0
    [call] = change.definition_calls()
    halted = change.fire(call, "halted")
    assert halted.returncode == 0 and "did not start" in halted.stdout
    assert change.starts() == [] and change.pending() == []


def test_change_launcher_dry_run_is_read_only(change):
    change.project("demo", definition="none")

    result = change.run("demo", "--dry-run", ASK)

    assert result.returncode == 0, result.stderr
    reported = next(line for line in result.stdout.splitlines() if "--start" in line)
    assert ASK in reported.split()
    assert change.starts() == [] and change.definition_calls() == []
    [described] = change.describes()
    assert ASK not in described

    # Under a definition the dry run writes no record and starts no definition walk, and the ask
    # shows only in the change walk's proposed argument vector.
    change.reset()
    change.project("full-demo", definition="full")
    result = change.run("full-demo", "--dry-run", ASK)
    assert result.returncode == 0, result.stderr
    assert change.pending() == [] and change.definition_calls() == [] and change.starts() == []
    assert sum(1 for line in result.stdout.splitlines() if ASK in line.split()) == 1


def test_change_launcher_help_names_the_option_after_the_context_cap():
    text = CHANGE_LAUNCHER.read_text()

    # Both forms of the usage line: the refusal's and the header's second line of the synopsis.
    assert "[--keep-awake] [--context-cap <tokens>] [--gate-owners-mac] | <project> --stop" in text
    header = text.split("set -euo pipefail", 1)[0]
    assert "\n#                                             [--context-cap <tokens>] " \
        "[--gate-owners-mac]\n" in header
    assert "Never handed to a definition walk." in header
    assert ("A start that waits on a definition walk keeps the ask in its pending-launch record"
            in " ".join(line.lstrip("# ") for line in header.splitlines()))
