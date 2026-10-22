"""Contract tests for `build-idea/launcher.sh`.

**Named `test_build_idea_launcher.py`, not `test_build_idea.py`.** The identity rule
(`kensaiapp_structure.md` § Owner-run launcher folder) would give this suite the second name; the
`_launcher` suffix is because `core/tools/test_build_idea.py` already holds it, and pytest imports
test modules by basename — a second one aborts the whole run before a test executes.

**Two kinds of test, and the engine is stubbed only in the first.** The contract half stubs the
engine through `LAUNCH_BUILD_IDEA_SCRIPT` and pins the argv this launcher builds; what the engine
does with it is `core/tools/test_build_idea.py`'s. The end-to-end half runs the real launcher and
the real engine over a synthetic core — its `skill`, `chain-product`, `chain-agari` and
`chain-change` launchers replaced by stubs that record their argv and exit — and drives each
landing by changing the disk and calling the row's shim, exactly as a finished run would.

**No test invokes a real notifier.** `KENSAIAPP_NOTIFIER` is cleared on every call — to a spy when a
test asks for one, to nothing otherwise.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path

import pytest

import pin
from provenance_test_support import isolated_host

_SCRIPT = Path(__file__).resolve().parent / "launcher.sh"
_CORE = _SCRIPT.parent.parent.parent
# The delivered provider file is the tracked template at the instance root, which no suite
# leans on a live `.providers.toml` for: it is untracked and absent from a fresh checkout.
_PROVIDER_EXAMPLE = _CORE.parent / ".providers.toml.example"

ENGINE_STUB = """#!/usr/bin/env python3
import os, sys
if "--describe" in sys.argv:
    with open(os.environ["DESCRIBE_ARGV_LOG"], "w") as fh:
        fh.write("\\n".join(sys.argv[1:]))
    refusal = os.environ.get("DESCRIBE_REFUSE")
    if refusal:
        print("build_idea: " + refusal, file=sys.stderr)
        sys.exit(3)
    default = "1. close the reached station — after — — x\\n"
    sys.stdout.write(os.environ.get("DESCRIBE_STDOUT", default))
    sys.exit(0)
with open(os.environ["ENGINE_ARGV_LOG"], "w") as fh:
    fh.write("\\n".join(sys.argv[1:]))
if "--stop" in sys.argv:
    print(os.environ.get("STOP_LINE", "engine-stub: stop recorded"))
    sys.exit(int(os.environ.get("STOP_EXIT", "0")))
print("engine-stub: started")
"""

NOTIFIER_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" >> "$NOTIFIER_ARGV_LOG"
"""


@pytest.fixture
def run(tmp_path, _session_pin):
    """`run(*cli_args) -> CompletedProcess`, invoking the real launcher with `tmp_path` as its
    cwd — the launcher's own instance root. `run.core_dir` is the session pin's own `core/` —
    every `<CORE>`-derived value the launcher hands the engine resolves there, since the launcher
    enters that pin before anything else reads `CORE_DIR` (Task 20)."""
    engine_stub = tmp_path / "engine_stub.py"
    engine_stub.write_text(ENGINE_STUB)
    engine_stub.chmod(0o755)
    argv_log = tmp_path / "engine_argv.log"
    describe_log = tmp_path / "describe_argv.log"

    env = dict(os.environ)
    env.pop("KENSAIAPP_NOTIFIER", None)
    # A force the caller's session exports is not a case's.
    env.pop("KENSAIAPP_AGENT_PROVIDER", None)
    for name in ("DESCRIBE_REFUSE", "DESCRIBE_STDOUT", "STOP_LINE", "STOP_EXIT"):
        env.pop(name, None)
    env["LAUNCH_BUILD_IDEA_SCRIPT"] = str(engine_stub)
    env["ENGINE_ARGV_LOG"] = str(argv_log)
    env["DESCRIBE_ARGV_LOG"] = str(describe_log)
    env["HOME"] = str(tmp_path / "home")
    (tmp_path / "home").mkdir()

    def _run(*cli_args):
        return subprocess.run([str(_SCRIPT), *cli_args], cwd=str(tmp_path),
                              capture_output=True, text=True, env=env)

    def _project(name, product_path="products/thing", card=None):
        project_dir = tmp_path / "system" / "projects" / name
        project_dir.mkdir(parents=True)
        if card is None:
            card = f"# {name}\n\n**Product path:** {product_path}\n"
        (project_dir / "project.md").write_text(card)

    def _engine_argv():
        return argv_log.read_text().splitlines() if argv_log.exists() else []

    def _describe_argv():
        return describe_log.read_text().splitlines() if describe_log.exists() else []

    def _value(flag):
        argv = _engine_argv()
        return argv[argv.index(flag) + 1]

    _run.root = tmp_path
    _run.env = env
    _run.core_dir = _session_pin.core
    _run.pin_root = _session_pin.root
    _run.project = _project
    _run.engine_argv = _engine_argv
    _run.describe_argv = _describe_argv
    _run.value = _value
    return _run


# --- the engine invocation --------------------------------------------------------------------


def test_hands_the_queue_to_the_engine_start_with_its_own_state_file(run):
    run.project("example-product")

    result = run("example-product")

    assert result.returncode == 0
    argv = run.engine_argv()
    assert argv[0] == "--start"
    assert argv[1] == f"{run.root}/system/logs/build-idea-example-product-state.json"


def test_the_state_file_is_no_siblings(run):
    """One state file IS one project's queue, so a queue that shared a chain's file could not run
    beside it."""
    run.project("example-product")

    run("example-product")

    assert run.engine_argv()[1] not in (
        f"{run.root}/system/logs/chain-change-example-product-state.json",
        f"{run.root}/system/logs/chain-example-product-state.json",
        f"{run.root}/system/logs/chain-development-example-product-state.json")


def test_start_is_given_every_flag_the_engine_requires_with_resolved_values(run):
    run.project("example-product")

    run("example-product")

    assert run.value("--instance-root") == str(run.root)
    assert run.value("--project") == "example-product"
    assert run.value("--core-dir") == str(run.core_dir)
    assert run.value("--shim-dir") == f"{run.root}/system/logs"


def test_no_key_is_passed_unless_one_is_given(run):
    run.project("example-product")

    run("example-product")

    assert "--key" not in run.engine_argv()


def test_a_unit_key_is_passed_as_key(run):
    run.project("example-product")

    result = run("example-product", "2026-09-18_a-unit")

    assert result.returncode == 0
    assert run.value("--key") == "2026-09-18_a-unit"


def test_a_second_positional_dies(run):
    run.project("example-product")

    result = run("example-product", "2026-09-18_a-unit", "another")

    assert result.returncode != 0
    assert "unexpected argument" in result.stderr
    assert run.engine_argv() == []


# --- the pin (Task 20): the launcher enters it before the engine is resolved -------------------


def test_dry_run_prints_the_pin_line(run):
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert re.search(r"^Pin: .+\(inherited\)$", result.stdout, re.MULTILINE)


def test_the_engine_is_started_from_the_pin(run):
    run.project("example-product")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert run.value("--core-dir") == str(run.core_dir)


def test_stop_is_handled_from_the_pin_too(run):
    """`--stop` returns before the engine's `--core-dir` is ever built, so the pin line is the
    only signal that this branch, like the start branch, entered the pin before anything else
    read `CORE_DIR`."""
    run.project("example-product")

    result = run("example-product", "--stop")

    assert result.returncode == 0, result.stderr
    assert re.search(r"^Pin: .+\(inherited\)$", result.stdout, re.MULTILINE)


# --- the guards -------------------------------------------------------------------------------


def test_no_project_arg_dies_with_usage(run):
    result = run()

    assert result.returncode != 0
    assert "usage:" in result.stderr
    assert run.engine_argv() == []


def test_an_unknown_project_dies_naming_the_card(run):
    result = run("nope")

    assert result.returncode != 0
    assert f"no project card at {run.root}/system/projects/nope/project.md" in result.stderr
    assert run.engine_argv() == []


def test_an_unknown_flag_dies(run):
    run.project("example-product")

    result = run("example-product", "--wat")

    assert result.returncode != 0
    assert "unknown flag" in result.stderr
    assert run.engine_argv() == []


def test_the_usage_line_and_the_usage_block_name_every_flag(run):
    result = run()

    header = _SCRIPT.read_text().split("set -euo pipefail", 1)[0]
    usage = header.split("# USAGE", 1)[1]
    for flag in ("--provider", "--dry-run", "--keep-awake", "--context-cap", "--chain-ended", "--stop"):
        assert flag in result.stderr and flag in usage, flag


# --- the notifier -----------------------------------------------------------------------------


def test_an_unset_notifier_is_omitted(run):
    run.project("example-product")

    result = run("example-product")

    assert result.returncode == 0
    assert "--notifier" not in run.engine_argv()


def test_the_notifier_is_resolved_here_and_passed_as_a_parameter(run, tmp_path):
    spy = tmp_path / "notifier.sh"
    spy.write_text(NOTIFIER_STUB)
    spy.chmod(0o755)
    run.env["KENSAIAPP_NOTIFIER"] = str(spy)
    log = tmp_path / "notifier_argv.log"
    run.env["NOTIFIER_ARGV_LOG"] = str(log)
    run.project("example-product")

    run("example-product")

    assert run.value("--notifier") == str(spy)
    assert not log.exists(), "the launcher passes the notifier down; it never sends anything"


# --- --keep-awake -----------------------------------------------------------------------------


def test_keep_awake_is_passed_to_the_engine(run):
    run.project("example-product")

    run("example-product", "--keep-awake")

    assert "--keep-awake" in run.engine_argv()


def test_keep_awake_is_absent_unless_asked_for(run):
    run.project("example-product")

    run("example-product")

    assert "--keep-awake" not in run.engine_argv()


# --- provider ---------------------------------------------------------------------------------


def _forced(run):
    argv = run.engine_argv()
    return argv[argv.index("--provider") + 1] if "--provider" in argv else None


@pytest.mark.parametrize("provider", ["codex", "gemini", "claude"])
def test_the_provider_flag_is_handed_to_the_engine_as_the_force(run, provider):
    run.project("example-product")

    result = run("example-product", "--provider", provider)

    assert result.returncode == 0, result.stderr
    assert _forced(run) == provider
    assert "build-idea: provider=" + provider + " (forced on every row)" in result.stdout


@pytest.mark.parametrize("channel", ["flag", "equals-flag", "variable"])
def test_provider_hf_reaches_the_engine(run, channel):
    # CP-424: every way the launcher takes a provider takes `hf`, and the engine is handed it.
    run.project("example-product")
    args = {"flag": ["--provider", "hf"], "equals-flag": ["--provider=hf"], "variable": []}[channel]
    if channel == "variable":
        run.env["KENSAIAPP_AGENT_PROVIDER"] = "hf"

    result = run("example-product", *args)

    assert result.returncode == 0, result.stderr
    assert _forced(run) == "hf"


@pytest.mark.parametrize("channel", ["flag", "equals-flag", "variable"])
def test_provider_ollama_reaches_the_engine(run, channel):
    # CP-424: every way the launcher takes a provider takes `ollama`, and the engine is handed it.
    run.project("example-product")
    args = {
        "flag": ["--provider", "ollama"],
        "equals-flag": ["--provider=ollama"],
        "variable": [],
    }[channel]
    if channel == "variable":
        run.env["KENSAIAPP_AGENT_PROVIDER"] = "ollama"

    result = run("example-product", *args)

    assert result.returncode == 0, result.stderr
    assert _forced(run) == "ollama"


def test_an_exported_provider_is_the_same_force_and_the_flag_wins(run):
    run.project("example-product")
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"

    assert run("example-product").returncode == 0
    assert _forced(run) == "codex"
    assert run("example-product", "--provider=claude").returncode == 0
    assert _forced(run) == "claude"


def test_with_no_force_the_engine_is_handed_none(run):
    """Each row then runs on its own provider: the entry the instance's `.providers.toml` holds."""
    run.project("example-product")
    run.env.pop("KENSAIAPP_AGENT_PROVIDER", None)

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert _forced(run) is None
    assert "build-idea: provider=each row's own" in result.stdout


def test_unknown_provider_is_refused_before_the_engine(run):
    run.project("example-product")

    result = run("example-product", "--provider", "other")

    assert result.returncode != 0
    assert "provider must be claude, codex, gemini, hf or ollama (got 'other')" in result.stderr
    assert run.engine_argv() == []


# --- --context-cap ---------------------------------------------------------------------------


def test_build_idea_launcher_passes_context_cap(run):
    run.project("example-product")

    result = run("example-product", "--context-cap", "80000", "--keep-awake")

    assert result.returncode == 0, result.stderr
    assert run.value("--context-cap") == "80000"
    assert "--keep-awake" in run.engine_argv()


def test_no_context_cap_is_passed_unless_one_is_given(run):
    """The engine's own default applies, so this launcher cannot drift from it."""
    run.project("example-product")

    run("example-product")

    assert "--context-cap" not in run.engine_argv()


@pytest.mark.parametrize("cli", [
    ("--context-cap", "abc"),
    ("--context-cap", "0"),
    ("--context-cap", "-5"),
    ("--context-cap", "1.5"),
    ("--context-cap", ""),
    ("--context-cap",),
    ("--context-cap", "--keep-awake"),
])
def test_build_idea_launcher_refuses_a_bad_context_cap(run, cli):
    run.project("example-product")

    for extra in ((), ("--dry-run",)):
        result = run("example-product", *cli, *extra)

        assert result.returncode != 0
        assert "--context-cap" in result.stderr and "positive integer" in result.stderr
        assert run.engine_argv() == [] and run.describe_argv() == []


def test_the_dry_run_prints_the_context_cap_it_would_pass(run):
    run.project("example-product")

    result = run("example-product", "--context-cap", "80000", "--dry-run")

    assert result.returncode == 0, result.stderr
    command = shlex.split(next(line for line in result.stdout.splitlines()
                               if line.strip().startswith("python3")))
    assert command[command.index("--context-cap") + 1] == "80000"
    assert run.engine_argv() == []


# --- --dry-run --------------------------------------------------------------------------------


def test_the_dry_run_asks_describe_and_never_start(run):
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0
    assert run.engine_argv() == [], "a dry run starts nothing"
    describe = run.describe_argv()
    assert describe[0] == "--describe"
    assert describe[1] == f"{run.root}/system/logs/build-idea-example-product-state.json"
    assert describe[describe.index("--instance-root") + 1] == str(run.root)
    assert describe[describe.index("--project") + 1] == "example-product"
    assert describe[describe.index("--core-dir") + 1] == str(run.core_dir)


def test_the_dry_run_prints_what_describe_said_and_the_exact_start_command(run):
    run.project("example-product")

    result = run("example-product", "2026-09-18_a-unit", "--keep-awake", "--dry-run")

    assert "1. close the reached station — after — — x" in result.stdout
    assert "DRY RUN — would run:" in result.stdout
    assert "--start" in result.stdout and "--keep-awake" in result.stdout
    assert re.search(r"--key\s+2026-09-18_a-unit", result.stdout)
    assert run.describe_argv()[-2:] == ["--key", "2026-09-18_a-unit"]


def test_a_refused_describe_fails_the_dry_run_with_the_reason(run):
    run.project("example-product")
    run.env["DESCRIBE_REFUSE"] = "no sealed unit to run for example-product"

    result = run("example-product", "--dry-run")

    assert result.returncode != 0
    assert "no sealed unit to run for example-product" in result.stderr
    assert "DRY RUN" not in result.stdout


def _described_provider(run):
    argv = run.describe_argv()
    return argv[argv.index("--provider") + 1] if "--provider" in argv else None


def test_describe_argv_carries_the_provider_flag_when_forced_by_flag(run):
    """CP-317: the dry run's query is told the force exactly when the start command is."""
    run.project("example-product")

    assert run("example-product", "--provider", "codex", "--dry-run").returncode == 0

    assert _described_provider(run) == "codex"


def test_describe_argv_carries_the_exported_provider_when_forced_by_env(run):
    run.project("example-product")
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"

    assert run("example-product", "--dry-run").returncode == 0
    assert _described_provider(run) == "codex"
    assert run("example-product", "--provider=claude", "--dry-run").returncode == 0
    assert _described_provider(run) == "claude"


def test_describe_argv_carries_no_provider_when_unforced(run):
    run.project("example-product")
    run.env.pop("KENSAIAPP_AGENT_PROVIDER", None)

    assert run("example-product", "--dry-run").returncode == 0

    assert "--provider" not in run.describe_argv()


@pytest.mark.parametrize("forcing", [(), ("--provider", "gemini")], ids=["unforced", "forced"])
def test_describe_and_start_argv_carry_the_same_provider(run, forcing):
    """The start command the dry run prints and the describe argv agree on the force."""
    run.project("example-product")
    run.env.pop("KENSAIAPP_AGENT_PROVIDER", None)

    result = run("example-product", *forcing, "--dry-run")

    printed = shlex.split(result.stdout.split("DRY RUN — would run:")[1])
    started = printed[printed.index("--provider") + 1] if "--provider" in printed else None
    assert started == _described_provider(run) == (forcing[1] if forcing else None)


# --- --dry-run against the real engine ---------------------------------------------------------
#
# The contract half above stubs `--describe`, so it can prove which flags the launcher passes and
# never what the engine decides. These run the real launcher and the real engine on an isolated
# host whose own `.providers.toml` the case writes at the instance root. The tools are REAL FILES:
# a symlink would lead Python's `sys.path[0]` straight back to the whole real tree.

REAL_ENGINE_TOOLS = (
    "build_idea.py", "chain.py", "chain_development.py", "gate_suite.py", "journey_names.py",
    "journey_status.py",
    "reporters.py",
    "providers.py", "run_intelligence.py", "agent_run.py", "hook_wiring.py", "intelligence.py",
    "model_assignment.py", "task_context.py", "env_file.py", "completion_shim.py", "walk_stop.py",
    "pin.py", "pin_run.sh", "pin_host_changed.py", "product_checkout.py", "development_path.py",
)
REMOVED_ENTRY = "pick a seed"
PICK_ENTRY = f'build-idea."{REMOVED_ENTRY}"'


class DryRunHost:
    """The real launcher and engine on an isolated host: a sealed unit whose report holds one row,
    the close of the reached station — a kind whose entry is never the removed one."""

    def __init__(self, tmp_path: Path, *, without: str | None = None):
        self.root = tmp_path / "host"
        self.root.mkdir()
        self.launcher = isolated_host(self.root, _SCRIPT, tools=REAL_ENGINE_TOOLS)
        self.core = self.root / "core"
        provider_file = self.root / ".providers.toml"
        text = _PROVIDER_EXAMPLE.read_text()
        if without:
            kept = [line for line in text.splitlines() if not line.startswith(f'"{without}" =')]
            assert len(kept) == len(text.splitlines()) - 1, f"no `{without}` entry to remove"
            text = "\n".join(kept) + "\n"
        provider_file.write_text(text)
        project = self.root / "system" / "projects" / PROJECT
        (project / "contexts").mkdir(parents=True)
        (project / "project.md").write_text(f"# {PROJECT}\n\n**Product path:** products/thing\n")
        (project / "contexts" / "CONTEXT_PM.md").write_text(
            f"# CONTEXT_PM\n\n**Status:** Sealed\n\n`{KEY}` — the unit.\n")
        trail = project / "journey" / "tobiishi" / "trail" / KEY
        trail.mkdir(parents=True)
        (trail / "change_request.md").write_text("x")
        (project / "journey" / "shukuba").mkdir(parents=True)
        (project / "journey" / "shukuba" / STATION).write_text("a station")
        report = project / "journey" / "nemawashi" / "unpicked" / SEED / f"{KEY}_report.md"
        report.parent.mkdir(parents=True)
        self.command = f"{self.core}/launchers/skill/launcher.sh shukuba-retire {PROJECT}"
        report.write_text(
            f"# a report\n\n## Next moves\n\n{_HEADER}"
            f"| 1 | close the reached station | owner | `{self.command}` | — | Moves row 1 |\n"
            f"\n## Read\n\nx\n")
        (self.root / "home").mkdir()
        self.env = {"PATH": os.environ["PATH"], "HOME": str(self.root / "home")}
        self.row_line = (f"1. close the reached station — after — — {self.command} "
                         f"{STATION.removesuffix('.md')}")

    def dry_run(self, *args: str, **env) -> subprocess.CompletedProcess:
        return subprocess.run([str(self.launcher), PROJECT, *args, "--dry-run"],
                              cwd=str(self.root), capture_output=True, text=True,
                              env={**self.env, **env})

    def wrote_no_queue_state(self) -> bool:
        return not list((self.root / "system" / "logs").glob("build-idea-*-state.json")) \
            if (self.root / "system" / "logs").exists() else True


def _start_command(result: subprocess.CompletedProcess) -> list[str]:
    return shlex.split(result.stdout.split("DRY RUN — would run:")[1])


def test_dry_run_refuses_a_missing_entry_unforced(tmp_path):
    """CP-314, CP-318 case 1 — an entry missing from the file refuses the dry run by name, though
    the report holds no row of that kind; nothing is printed as a plan and nothing is saved."""
    host = DryRunHost(tmp_path, without=REMOVED_ENTRY)

    result = host.dry_run()

    assert result.returncode == 1, (result.stdout, result.stderr)
    assert result.stderr.startswith("build-idea: a start would be refused — ")
    assert PICK_ENTRY in result.stderr
    assert host.row_line not in result.stdout and "DRY RUN" not in result.stdout
    assert host.wrote_no_queue_state()


def test_dry_run_prints_each_row_with_the_file_whole(tmp_path):
    """CP-316, CP-318 case 2 — the plan, then the block, then the start command, exit 0."""
    host = DryRunHost(tmp_path)

    result = host.dry_run()

    assert result.returncode == 0, (result.stdout, result.stderr)
    lines = result.stdout.splitlines()
    assert lines.index(host.row_line) < lines.index("DRY RUN — would run:")
    start = _start_command(result)
    assert "--start" in start and "--provider" not in start
    assert host.wrote_no_queue_state()


def test_dry_run_forced_by_flag_ignores_the_missing_entry(tmp_path):
    """CP-317, CP-318 case 3 — forced, the file is not read: a missing entry refuses nothing."""
    host = DryRunHost(tmp_path, without=REMOVED_ENTRY)

    result = host.dry_run("--provider", "claude")

    assert result.returncode == 0, (result.stdout, result.stderr)
    assert host.row_line in result.stdout.splitlines()
    start = _start_command(result)
    assert start[start.index("--provider") + 1] == "claude"
    assert host.wrote_no_queue_state()


def test_dry_run_forced_by_env_ignores_the_missing_entry(tmp_path):
    host = DryRunHost(tmp_path, without=REMOVED_ENTRY)

    result = host.dry_run(KENSAIAPP_AGENT_PROVIDER="codex")

    assert result.returncode == 0, (result.stdout, result.stderr)
    assert host.row_line in result.stdout.splitlines()
    start = _start_command(result)
    assert start[start.index("--provider") + 1] == "codex"
    assert host.wrote_no_queue_state()


@pytest.mark.parametrize("fault", ["missing", "invalid-toml", "invalid-utf8", "directory"])
def test_dry_run_refuses_unreadable_provider_files(tmp_path, fault):
    """CP-314 covers every provider-file refusal through the real launcher and engine."""
    host = DryRunHost(tmp_path)
    provider_file = host.root / ".providers.toml"
    if fault == "missing":
        provider_file.unlink()
    elif fault == "invalid-toml":
        provider_file.write_text("[build-idea\n")
    elif fault == "invalid-utf8":
        provider_file.write_bytes(b"\xff")
    else:
        provider_file.unlink()
        provider_file.mkdir()

    result = host.dry_run()

    assert result.returncode == 1, (result.stdout, result.stderr)
    assert result.stderr.startswith("build-idea: a start would be refused — ")
    assert str(provider_file) in result.stderr
    assert "Traceback" not in result.stderr
    assert not any(re.match(r"^\d+\. ", line) for line in result.stdout.splitlines())
    assert "DRY RUN" not in result.stdout
    assert host.wrote_no_queue_state()


def test_dry_run_names_every_bad_provider_entry(tmp_path):
    """CP-314 requires all unanswered entries, including kinds absent from this report."""
    host = DryRunHost(tmp_path, without=REMOVED_ENTRY)
    provider_file = host.root / ".providers.toml"
    provider_file.write_text(provider_file.read_text().replace(
        '"cut the route" = "claude"', '"cut the route" = "grok"'))

    result = host.dry_run()

    assert result.returncode == 1, (result.stdout, result.stderr)
    assert PICK_ENTRY in result.stderr
    assert 'build-idea."cut the route"' in result.stderr and "'grok'" in result.stderr
    assert not any(re.match(r"^\d+\. ", line) for line in result.stdout.splitlines())
    assert "DRY RUN" not in result.stdout
    assert host.wrote_no_queue_state()


@pytest.mark.parametrize("provider", ["claude", "codex", "gemini"])
def test_forced_dry_run_never_decodes_the_provider_file(tmp_path, provider):
    """CP-317's no-read promise survives a file which cannot even be decoded."""
    host = DryRunHost(tmp_path)
    (host.root / ".providers.toml").write_bytes(b"\xff")

    result = host.dry_run("--provider", provider)

    assert result.returncode == 0, (result.stdout, result.stderr)
    assert host.row_line in result.stdout.splitlines()
    start = _start_command(result)
    assert start[start.index("--provider") + 1] == provider
    assert host.wrote_no_queue_state()


# --- --chain-ended: the hook a chain-change walk's end fires -----------------------------------


def test_chain_ended_sealed_starts_the_queue(run):
    run.project("example-product")

    result = run("example-product", "--chain-ended", "sealed")

    assert result.returncode == 0
    assert run.engine_argv()[0] == "--start"


@pytest.mark.parametrize("end", ["halted", "settled", "machinery", "something-new"])
def test_chain_ended_anything_but_sealed_starts_nothing_and_exits_0(run, end):
    run.project("example-product")

    result = run("example-product", "--chain-ended", end)

    assert result.returncode == 0
    assert f"build-idea: the chain ended {end} — nothing to start" in result.stdout
    assert run.engine_argv() == [] and run.describe_argv() == []


def test_chain_ended_with_no_value_dies(run):
    run.project("example-product")

    result = run("example-product", "--chain-ended")

    assert result.returncode != 0
    assert "--chain-ended needs" in result.stderr
    assert run.engine_argv() == []


def test_chain_ended_still_checks_the_project_card(run):
    result = run("nope", "--chain-ended", "halted")

    assert result.returncode != 0 and "no project card" in result.stderr


# --- --stop: the owner's brake ------------------------------------------------------------------


def test_stop_reaches_the_engine_stop_with_the_state_path_and_project(run):
    run.project("example-product")

    result = run("example-product", "--stop")

    assert result.returncode == 0
    argv = run.engine_argv()
    assert argv[0] == "--stop"
    assert argv[1] == f"{run.root}/system/logs/build-idea-example-product-state.json"
    assert run.value("--instance-root") == str(run.root)
    assert run.value("--project") == "example-product"
    assert "--start" not in argv and "--notifier" not in argv


def test_stop_passes_the_notifier_it_resolved(run, tmp_path):
    spy = tmp_path / "notifier.sh"
    spy.write_text(NOTIFIER_STUB)
    spy.chmod(0o755)
    run.env["KENSAIAPP_NOTIFIER"] = str(spy)
    run.project("example-product")

    run("example-product", "--stop")

    assert run.value("--notifier") == str(spy)


def test_stop_prints_the_engines_line_and_exits_with_the_engines_status(run):
    run.project("example-product")
    run.env["STOP_LINE"] = "example-product: stop requested; finishing 1. close the reached station"
    run.env["STOP_EXIT"] = "3"

    result = run("example-product", "--stop")

    assert result.returncode == 3
    assert "example-product: stop requested; finishing 1. close the reached station" in result.stdout


@pytest.mark.parametrize("extra", [
    ["2026-09-18_a-unit"], ["--dry-run"], ["--chain-ended", "sealed"],
], ids=["a-unit-key", "dry-run", "chain-ended"])
def test_stop_with_a_unit_key_dry_run_or_chain_ended_dies(run, extra):
    run.project("example-product")

    result = run("example-product", "--stop", *extra)

    assert result.returncode != 0
    assert "usage:" in result.stderr and "--stop" in result.stderr
    assert run.engine_argv() == []


def test_now_is_an_unknown_flag(run):
    """The house's `claude stop` needs the id of one run, which this launcher — running many —
    has no reliable way to name, so the flag is not offered rather than offered and guessed."""
    run.project("example-product")

    result = run("example-product", "--stop", "--now")

    assert result.returncode != 0
    assert "unknown flag: --now" in result.stderr
    assert run.engine_argv() == []


def test_chain_ended_sealed_passes_by_hook_to_start(run):
    run.project("example-product")

    run("example-product", "--chain-ended", "sealed")

    assert "--by-hook" in run.engine_argv()


def test_a_plain_start_is_not_a_hook_start(run):
    run.project("example-product")

    run("example-product")

    assert "--by-hook" not in run.engine_argv()


def test_the_header_says_how_to_stop_it_and_where_it_starts_again():
    header = _SCRIPT.read_text().split("set -euo pipefail", 1)[0]

    assert "HOW TO STOP IT, AND WHERE IT STARTS AGAIN" in header


def test_the_header_says_a_stop_stops_the_runs_in_flight():
    unwrapped = re.sub(r"\s*\n#\s*", " ", _SCRIPT.read_text().split("set -euo pipefail", 1)[0])
    header = unwrapped

    assert "the runs in flight finish" not in header
    assert "stops the runs in flight" in header
    assert "through that chain's own --stop" in header


# --- what the launcher is not ------------------------------------------------------------------


def _code() -> str:
    return "\n".join(line for line in _SCRIPT.read_text().splitlines()
                     if not line.lstrip().startswith("#"))


def test_the_launcher_spawns_no_claude_and_holds_no_caffeinate():
    """It reads a table and starts launchers that each own their run and their keep-awake; a
    caffeinate held here would cover none of the queue, and a `claude` here would be a model
    deciding what runs next."""
    code = _code()

    assert "claude --" not in code
    assert "set -- claude" not in code
    assert "caffeinate" not in code


def test_the_launcher_has_no_run_telemetry_call_and_declares_no_completion_watcher_library():
    code = _code()

    assert not any(
        line.strip() == "run_telemetry" or line.strip().startswith("run_telemetry ")
        for line in code.splitlines()
    )
    assert "DETACH_LIB" not in code and "detach_watcher" not in code


def test_launcher_is_executable():
    assert os.access(_SCRIPT, os.X_OK)


def test_the_launcher_names_no_literal_core_path():
    code = _code()

    assert "~/.claude/" not in code
    assert not re.search(r"(?<![\w/.])core/", code)


# --- end to end: the real launcher, the real engine, a synthetic core -----------------------------
#
# The `skill`, `chain-product`, `chain-agari` and `chain-change` launchers are stubs that record
# what they were run with and exit. A landing is the disk changing, then the row's shim called with
# an outcome — the shim detaches the engine, so each test waits on the state file and never on the
# shim.

PROJECT = "proj"
KEY = "2026-09-18_a-unit"
SEED = "2026-09-01_a-seed"
STATION = "2026-09-18_a-station.md"
STEM = STATION.removesuffix(".md")

STUB_LAUNCHER = """#!/usr/bin/env bash
identity="$(basename "$(dirname "$0")")"
printf '%s|%s|%s\\n' "$identity" "$*" "${DETACH_WATCHER_ON_COMPLETE:-}" >> "$STUB_LOG"
"""

# Appends each message (its first argument) to $NOTIFIED, framed by a `----` line.
NOTIFIED_STUB = "#!/usr/bin/env bash\nprintf '%s\\n----\\n' \"$1\" >> \"$NOTIFIED\"\n"

_HEADER = "| # | Move | Whose | Command | After | From |\n|---|---|---|---|---|---|\n"


class World:
    """A synthetic instance under `tmp_path`: a core holding the real launcher and the real
    engine's `tools/`, stub launchers, and a project whose unit is sealed and refined."""

    def __init__(self, tmp_path: Path, warm_executables):
        self.root = tmp_path
        self.core = tmp_path / "core"
        # Every executable of the synthetic core is a link to a warm file (`conftest.py`,
        # `warm_executables`), so none of them is a first exec inside a case's window. A link is
        # safe here because both scripts take their identity from the path they were invoked by,
        # never from a resolved one: the launcher's `SCRIPT_DIR` is `${BASH_SOURCE[0]}` through a
        # logical `cd … && pwd`, and a stub's identity is `basename "$(dirname "$0")"`.
        warm_executables.link(self.core / "launchers" / "build-idea" / "launcher.sh",
                              _SCRIPT.read_text())
        (self.core / "tools").symlink_to(_CORE / "tools")
        for identity in ("skill", "chain-product", "chain-agari", "chain-change"):
            # One body per identity. Stubs sharing a body share one warm file, and
            # `pin.same_launcher` names launchers that resolve to one real file the same
            # launcher, so the engine could not tell the sweep's wrong chain from its right one.
            warm_executables.link(self.core / "launchers" / identity / "launcher.sh",
                                  f"{STUB_LAUNCHER}# {identity}\n")
        # `<tmp_path>` itself carries a `pin.json`, so `pin_enter` (Task 20) finds this synthetic
        # tree already its own pin and neither re-execs nor makes a real one — a real `make` would
        # walk `self.core / "tools"` through its symlink into the whole real `core/tools/`, copied
        # file by file, on every single launch this class drives.
        (tmp_path / "pin.json").write_text(json.dumps({
            "id": "world-self-pin",
            "source_host_root": str(tmp_path),
            "created": "1970-01-01T00:00:00+00:00",
        }) + "\n")
        self.stub_log = tmp_path / "stub.log"
        self.notified = tmp_path / "notified.log"
        notifier = warm_executables.link(tmp_path / "notify.sh", NOTIFIED_STUB)
        self.env = dict(os.environ)
        self.env.pop("LAUNCH_BUILD_IDEA_SCRIPT", None)
        self.env.update(STUB_LOG=str(self.stub_log), NOTIFIED=str(self.notified),
                        KENSAIAPP_NOTIFIER=str(notifier), HOME=str(tmp_path / "home"))
        (tmp_path / "home").mkdir()
        # The instance's own provider file: an unforced queue reads it at the instance root.
        shutil.copy2(_PROVIDER_EXAMPLE, tmp_path / ".providers.toml")
        project = tmp_path / "system" / "projects" / PROJECT
        (project / "contexts").mkdir(parents=True)
        (project / "project.md").write_text(
            f"# {PROJECT}\n\n**Product path:** products/thing\n**Definition:** full\n")
        (project / "contexts" / "CONTEXT_PM.md").write_text(
            f"# CONTEXT_PM\n\n**Status:** Sealed\n\n`{KEY}` — the unit.\n")
        (project / "journey" / "tobiishi" / "trail" / KEY).mkdir(parents=True)
        (project / "journey" / "tobiishi" / "trail" / KEY / "change_request.md").write_text("x")
        self.shukuba = project / "journey" / "shukuba"
        self.shukuba.mkdir(parents=True)
        (self.shukuba / STATION).write_text("a station")
        self.seedbed = project / "journey" / "nemawashi"
        self.report = self.seedbed / "unpicked" / SEED / f"{KEY}_report.md"
        self.report.parent.mkdir(parents=True)
        self.state_path = tmp_path / "system" / "logs" / f"build-idea-{PROJECT}-state.json"

    # the report
    def command(self, identity: str, *args: str) -> str:
        return f"`{self.core}/launchers/{identity}/launcher.sh {' '.join(args)}`"

    def write_report(self, rows: list[tuple[str, str, str]], header: str = _HEADER) -> None:
        """`rows` is `(move, command cell, after)`, numbered from 1."""
        body = "".join(f"| {number} | {move} | owner | {command} | {after} | Moves row 1 |\n"
                       for number, (move, command, after) in enumerate(rows, 1))
        self.report.write_text(f"# a report\n\n## Next moves\n\n{header}{body}\n## Read\n\nx\n")

    def close(self, after: str = "—") -> tuple[str, str, str]:
        return ("close the reached station",
                self.command("skill", "shukuba-retire", PROJECT), after)

    def pick(self, after: str = "—") -> tuple[str, str, str]:
        return ("pick a seed", self.command("skill", "nemawashi-pick", PROJECT), after)

    def sweep(self, after: str = "—") -> tuple[str, str, str]:
        return ("sweep the product's companions",
                self.command("chain-product", PROJECT), after)

    def agari_sweep(self, after: str = "—") -> tuple[str, str, str]:
        return ("sweep the product's companions",
                self.command("chain-agari", PROJECT), after)

    def set_definition(self, definition: str) -> None:
        """The project card's `**Definition:**` line, rewritten to `definition`."""
        card = self.root / "system" / "projects" / PROJECT / "project.md"
        card.write_text(f"# {PROJECT}\n\n**Product path:** products/thing\n"
                        f"**Definition:** {definition}\n")

    def owners_act(self, after: str = "—") -> tuple[str, str, str]:
        return ("the owner's act", "none — walk it yourself", after)

    def change(self, after: str = "—") -> tuple[str, str, str]:
        return ("walk the next change", self.command("chain-change", PROJECT), after)

    # running it
    def launch(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([str(self.core / "launchers" / "build-idea" / "launcher.sh"),
                               PROJECT, *args], cwd=str(self.root), capture_output=True,
                              text=True, env=self.env)

    def shim(self, number: int, outcome: str) -> None:
        # The queue launches one row at a time, so the row this hook belongs to may still be
        # starting when the case gets here. The engine writes the shim before it records the row
        # as pending, so pending is the point the file is known to exist; bash on an absent file
        # exits 127.
        self.wait_for(lambda state: str(number) in state["pending"], f"row {number} to launch")
        shim = self.root / "system" / "logs" / f"build-idea-{PROJECT}-row-{number}.sh"
        # The engine wrote this file a moment ago, so exec'ing it would be a first exec inside the
        # case's window (`warm_executables`, `conftest.py`). It is `#!/usr/bin/env bash` and reads
        # only `$1`, so its interpreter runs the same bytes.
        subprocess.run(["bash", str(shim), outcome], cwd=str(self.root), env=self.env, check=True,
                       capture_output=True)

    def state(self) -> dict:
        return json.loads(self.state_path.read_text())

    def wait_for(self, predicate, what: str, timeout: float = 30.0) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.state_path.exists():
                try:
                    state = self.state()
                except ValueError:      # read between the engine's write and its replace
                    state = None
                if state is not None and predicate(state):
                    return state
            time.sleep(0.05)
        last = self.state_path.read_text() if self.state_path.exists() else None
        raise AssertionError(f"timed out waiting for {what}; state: {last}")

    def wait_for_message(self, needle: str, timeout: float = 30.0) -> str:
        """Wait until the notifier has been handed a message carrying `needle`, and return them all.

        The engine saves `ended` (`build_idea.py`) and only then sends the end message, so a case
        that waited on `ended` and read the messages at once could read them before the message
        was sent — the shape `9a42ae3b` fixed for the `launched` line, applied to the notifier.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if needle in self.messages():
                return self.messages()
            time.sleep(0.05)
        raise AssertionError(f"timed out waiting for a message carrying {needle!r}; "
                             f"messages: {self.messages()!r}")

    def statuses(self) -> dict[int, str]:
        return {row["number"]: row["status"] for row in self.state()["rows"]}

    def launched(self) -> list[str]:
        """What the stub launchers were run with, as `identity|args|shim`, in order."""
        return self.stub_log.read_text().splitlines() if self.stub_log.exists() else []

    def messages(self) -> str:
        return self.notified.read_text() if self.notified.exists() else ""

    def finish(self, number: int, outcome: str = "completed") -> None:
        """A run ended: its shim called, then wait for the engine to have taken it off pending."""
        self.shim(number, outcome)
        self.wait_for(lambda state: str(number) not in state["pending"], f"row {number} to settle")

    def close_the_station(self) -> None:
        """What `shukuba-retire` leaves: the station moved whole into `trail/`."""
        (self.shukuba / "trail").mkdir(exist_ok=True)
        (self.shukuba / STATION).rename(self.shukuba / "trail" / STATION)


@pytest.fixture
def world(tmp_path, warm_executables):
    return World(tmp_path, warm_executables)


def test_a_dash_row_and_a_row_waiting_on_it_start_in_after_order(world):
    """Row 2 waits on row 1, and the wait is for row 1 to have LANDED — its shim called with
    `completed` after its fact is on disk — and never for its launcher to have been run."""
    world.write_report([world.close(), world.pick(after="1")])

    result = world.launch()

    assert result.returncode == 0, result.stderr
    assert [line.split("|")[0:2] for line in world.launched()] == [
        ["skill", f"shukuba-retire {PROJECT} {STEM}"]]
    assert world.statuses() == {1: "launched", 2: "waiting"}

    world.close_the_station()
    world.finish(1)

    # The engine saves a row `launched` BEFORE it runs the launcher (`build_idea.py` `_launch`),
    # so the stub's own line is waited for too — under load it lands after the status does.
    world.wait_for(lambda state: state["rows"][1]["status"] == "launched"
                   and len(world.launched()) == 2, "row 2 to launch")
    assert [line.split("|")[1] for line in world.launched()] == [
        f"shukuba-retire {PROJECT} {STEM}", f"nemawashi-pick {PROJECT}"]
    shim_seen_by_the_stub = world.launched()[0].split("|")[2]
    assert shim_seen_by_the_stub.endswith(f"build-idea-{PROJECT}-row-1.sh")


def test_a_prd_agari_cards_sweep_runs_chain_agari_end_to_end(world):
    """The card's `Definition:` names the chain: a `prd-agari` card's sweep row is accepted with
    the `chain-agari` command and launched through the real launcher and the real engine."""
    world.set_definition("prd-agari")
    world.write_report([world.agari_sweep()])

    result = world.launch()

    assert result.returncode == 0, result.stderr
    world.wait_for(lambda state: len(world.launched()) == 1, "the sweep to launch")
    row_1_shim = world.root / "system" / "logs" / f"build-idea-{PROJECT}-row-1.sh"
    assert world.launched() == [f"chain-agari|{PROJECT} --on-end {row_1_shim}|"]
    assert not any(line.startswith("chain-product|") for line in world.launched())


def test_a_prd_agari_card_refuses_the_chain_product_sweep_row_end_to_end(world):
    """The row is refused alone: it never launches, and the queue ends halted naming the
    command the card's definition runs."""
    world.set_definition("prd-agari")
    world.write_report([world.sweep()])

    result = world.launch()

    assert result.returncode == 0, result.stdout + result.stderr
    state = world.wait_for(lambda state: state["ended"] is not None, "the queue to end")
    assert state["ended"] == "halted"
    assert f"{world.core}/launchers/chain-agari/launcher.sh {PROJECT}" in state["ended_reason"]
    assert world.launched() == []


def test_the_cap_reaches_the_chain_change_row_and_no_other_launcher(world):
    """End to end, through the real launcher and the real engine: the sweep runs `chain-product`,
    which knows no such flag, and the change row runs `chain-change`, which needs it."""
    world.write_report([world.close(), world.sweep(), world.change(after="1, 2")])

    result = world.launch("--context-cap", "80000")

    assert result.returncode == 0, result.stderr
    world.close_the_station()
    world.finish(1)
    world.finish(2, "settled")
    world.wait_for(lambda state: len(world.launched()) == 3, "the change row to launch")
    by_launcher = {line.split("|")[0]: line.split("|")[1] for line in world.launched()}
    assert "--context-cap" not in by_launcher["skill"]
    assert "--context-cap" not in by_launcher["chain-product"]
    assert by_launcher["chain-change"] == f"{PROJECT} --context-cap 80000"
    assert world.state()["context_cap"] == 80000


def test_retirement_refinement_and_the_next_seed_walk_through_real_shims(world):
    retire = world.command("skill", "nemawashi-retire", PROJECT)
    active = world.seedbed / SEED
    world.report.parent.rename(active)
    world.report = active / f"{KEY}_report.md"
    (active / "seed.md").write_text("# walked seed\n- [x] walked\n")
    world.write_report([("retire a seed", retire, "—")])
    original_report = world.report.read_text()

    result = world.launch("--provider", "codex", "--context-cap", "123456")
    assert result.returncode == 0, result.stderr
    world.wait_for(lambda state: "1" in state["pending"], "retirement")
    assert world.state()["ended"] is None
    trail = world.seedbed / "trail"
    trail.mkdir()
    active.rename(trail / SEED)
    world.shim(1, "completed")
    world.wait_for_message("launched 2. refine a seed")
    assert world.launched()[-1].split("|")[1] == f"nemawashi-refine {PROJECT} {SEED}"

    report = world.root / "system/projects" / PROJECT / "docs/nemawashi-refine" / f"{SEED}_report.md"
    report.parent.mkdir(parents=True)
    world.report = report
    world.write_report([
        world.sweep(),
        ("cut from the product's documents",
         world.command("skill", "seeds-from-product-docs", PROJECT), "1"),
        world.pick("2"),
        ("cut the route", world.command("skill", "stations-from-seed", PROJECT), "3"),
        world.change("4"),
    ])
    world.shim(2, "completed")
    world.wait_for_message("launched 3. sweep the product's companions")
    assert world.launched()[-1].split("|")[0] == "chain-product"
    world.shim(3, "settled")
    world.wait_for_message("launched 4. cut from the product's documents")
    assert world.launched()[-1].split("|")[1] == f"seeds-from-product-docs {PROJECT}"
    candidate = world.seedbed / "unpicked" / "next-seed.md"
    candidate.write_text("# next seed\nCut from docs/SDD.md\n")
    world.shim(4, "completed")
    world.wait_for_message("launched 5. pick a seed")
    assert world.launched()[-1].split("|")[1] == f"nemawashi-pick {PROJECT}"
    picked = world.seedbed / candidate.name
    candidate.rename(picked)
    world.shim(5, "completed")
    world.wait_for_message("launched 6. cut the route")
    assert world.launched()[-1].split("|")[1] == f"stations-from-seed {PROJECT}"
    picked.write_text("# next seed\n## Stations\n- [ ] build the next thing\n")
    world.shim(6, "completed")
    world.wait_for(lambda state: state["ended"] == "handed-off", "the next change")
    assert world.state()["ended"] == "handed-off"
    assert world.launched()[-1] == f"chain-change|{PROJECT} --context-cap 123456|"
    assert (trail / SEED / f"{KEY}_report.md").read_text() == original_report



def test_a_halt_ends_the_loop(world):
    world.write_report([world.sweep(), world.close(after="1")])
    world.launch()
    assert [line.split("|")[0] for line in world.launched()] == ["chain-product"]

    world.finish(1, "machinery")

    state = world.wait_for(lambda state: state["ended"] is not None, "the queue to end")
    assert state["ended"] == "halted"
    assert world.statuses() == {1: "failed", 2: "blocked"}
    assert len(world.launched()) == 1


def test_a_refused_queue_launches_nothing(world):
    """A five-column report — one written before the After column — cannot be run."""
    world.write_report([world.close()], header="| # | Move | Whose | Command | From |\n"
                                               "|---|---|---|---|---|\n")

    result = world.launch()

    assert result.returncode != 0
    assert "After" in result.stderr
    assert world.launched() == [] and not world.state_path.exists()
    assert "After" in world.messages()


def test_a_failed_row_ends_the_loop(world):
    """A close whose run completed with its station still at the root did not close anything."""
    world.write_report([world.close(), world.pick(after="1")])
    world.launch()

    world.finish(1)

    state = world.wait_for(lambda state: state["ended"] is not None, "the queue to end")
    assert state["ended"] == "halted"
    assert "1. close the reached station" in state["ended_reason"]
    assert world.statuses() == {1: "failed", 2: "blocked"}
    assert len(world.launched()) == 1


def test_a_row_with_no_launcher_is_named_and_skipped(world):
    cut_seed = ("cut a seed", "none — `seeds-from-idea`, in a `principal-pm:` session", "—")
    world.write_report([cut_seed, world.close()])
    world.launch()
    assert [line.split("|")[0] for line in world.launched()] == ["skill"]

    world.close_the_station()
    world.finish(2)

    state = world.wait_for(lambda state: state["ended"] is not None, "the queue to end")
    assert state["ended"] == "done"
    world.wait_for_message("skipped: 1. cut a seed")
    assert "skipped: 1. cut a seed" in world.messages()
    assert len(world.launched()) == 1


def test_the_report_file_is_byte_identical_after_a_run(world):
    world.write_report([world.close(), world.pick(after="1")])
    before = world.report.read_bytes()

    world.launch()
    world.close_the_station()
    world.finish(1)
    world.wait_for(lambda state: state["rows"][1]["status"] == "launched", "row 2 to launch")

    assert world.report.read_bytes() == before


def test_a_stop_then_a_chain_end_starts_nothing(world):
    """The owner stops the loop; the walk that was running then ends and reaches for it through
    the hook. Nothing starts, and the owner is told why."""
    world.write_report([world.close(), world.pick(after="1")])

    stopped = world.launch("--stop")
    assert stopped.returncode == 0, stopped.stderr
    assert "no queue is live" in stopped.stdout
    assert world.state()["stop_requested"] is True

    result = world.launch("--chain-ended", "sealed")

    assert result.returncode == 0, result.stderr
    assert world.launched() == []
    assert "build-idea is stopped — chain-change's end did not restart it" in world.messages()
    assert world.state()["stop_requested"] is True
    assert world.state()["rows"] == [], "a suppressed start begins no queue"


def test_a_plain_start_after_a_stop_resumes_skipping_what_landed(world):
    """A queue stopped mid-way: the stop ends it at once and stops the chain row through its own
    launcher. The station is closed on disk afterwards, and a plain start runs only what is still
    owed."""
    world.write_report([world.sweep(), world.close(after="1"), world.pick(after="2")])
    world.launch()
    assert [line.split("|")[0] for line in world.launched()] == ["chain-product"]

    stopped = world.launch("--stop")
    assert stopped.returncode == 0, stopped.stderr
    world.close_the_station()

    row_1_shim = f"{world.root}/system/logs/build-idea-{PROJECT}-row-1.sh"
    assert world.state()["ended"] == "stopped", "the stop does not wait for the rows in flight"
    assert world.statuses() == {1: "failed", 2: "waiting", 3: "waiting"}
    assert [line.split("|")[:2] for line in world.launched()] == [
        ["chain-product", f"{PROJECT} --on-end {row_1_shim}"],
        ["chain-product", f"{PROJECT} --stop"]]
    assert "never run: 2. close the reached station" in world.messages()
    assert "never run: 3. pick a seed" in world.messages()

    resumed = world.launch()

    assert resumed.returncode == 0, resumed.stderr
    # The engine saves a row `launched` BEFORE it runs the launcher (`build_idea.py` `_launch`),
    # so the stub's own line is waited for too — under load it lands after the status does.
    world.wait_for(lambda state: state["rows"][0]["status"] == "launched"
                   and len(world.launched()) == 3, "row 1 to launch")
    assert [line.split("|")[1] for line in world.launched()][2:] == [
        f"{PROJECT} --on-end {row_1_shim}"]
    assert world.statuses() == {1: "launched", 2: "landed", 3: "waiting"}
    assert world.state()["stop_requested"] is False


def test_an_owners_act_row_ends_the_loop_and_nothing_waiting_on_it_starts(world):
    world.write_report([world.close(), world.owners_act(after="1"), world.pick(after="2")])
    result = world.launch()
    assert result.returncode == 0, result.stderr

    world.close_the_station()
    world.finish(1)

    state = world.wait_for(lambda state: state["ended"] is not None, "the queue to end")
    assert state["ended"] == "owner-owed"
    assert world.statuses() == {1: "landed", 2: "end", 3: "blocked"}
    assert [line.split("|")[1] for line in world.launched()] == [
        f"shukuba-retire {PROJECT} {STEM}"]


def test_the_owners_act_notification_carries_the_step_and_the_resume_command(world):
    world.write_report([world.close(), world.owners_act(after="1"), world.pick(after="2")])
    world.launch()

    world.close_the_station()
    world.finish(1)

    world.wait_for(lambda state: state["ended"] is not None, "the queue to end")
    world.wait_for_message("walk it yourself")
    world.wait_for_message(f"{world.core}/launchers/build-idea/launcher.sh {PROJECT}")
    assert "walk it yourself" in world.messages()
    assert f"{world.core}/launchers/build-idea/launcher.sh {PROJECT}" in world.messages()


def test_a_table_with_an_owners_act_row_starts_no_chain_change(world):
    world.write_report([world.close(), world.owners_act(after="1"), world.change(after="1")])
    world.launch()

    world.close_the_station()
    world.finish(1)

    state = world.wait_for(lambda state: state["ended"] is not None, "the queue to end")
    assert state["ended"] == "owner-owed"
    assert world.statuses()[3] == "blocked"
    assert not any(line.startswith("chain-change|") for line in world.launched())


# --- the pin renews when the host changed: the real launcher over a throwaway git host -----------
#
# A `build-idea` start compares its pin with the host the pin was made from, across `core/`,
# `.claude/` and `skills/`, and takes a new pin when they differ (`pin_host_changed.py` owns what
# "differ" means). These cases run the real launcher, `pin_run.sh`, `pin.py` and the comparator,
# copied into a throwaway **git** host under `tmp_path`, with only the engine stubbed through
# `LAUNCH_BUILD_IDEA_SCRIPT`. The environment is built from scratch, so the session pin the other
# cases run under cannot answer for it. "Runs on pin X" is read off the engine's `--core-dir`.

_GIT_HOST_PROJECT = "proj"
_HOST_EDIT = "edited after the pin\n"


def _git(*args: str, cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True,
                            text=True)
    return result.stdout.strip()


def _snapshot(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes()
            for path in sorted(root.rglob("*")) if path.is_file()}


class GitHost:
    """A git work tree that is also the instance: the real launcher and the shared tools it needs
    under `core/`, a file in each of `.claude/` and `skills/`, a project card and a note under
    `system/`, and a `.gitignore` matching a log under `core/`. `pin_of_host` is the pin made of it
    as committed; nothing has been edited since."""

    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.root = tmp_path / "host"
        self.root.mkdir()
        _git("init", "-q", cwd=self.root)
        _git("config", "user.email", "host@example.com", cwd=self.root)
        _git("config", "user.name", "Host", cwd=self.root)
        (self.root / "core" / "tools").mkdir(parents=True)
        for name in ("pin.py", "pin_run.sh", "pin_host_changed.py"):
            shutil.copy2(_CORE / "tools" / name, self.root / "core" / "tools" / name)
        (self.root / "core" / "launchers" / "build-idea").mkdir(parents=True)
        shutil.copy2(_SCRIPT, self.root / "core" / "launchers" / "build-idea" / "launcher.sh")
        (self.root / ".claude" / "skills" / "example").mkdir(parents=True)
        (self.root / ".claude" / "skills" / "example" / "SKILL.md").write_text("a skill\n")
        (self.root / "skills" / "grp").mkdir(parents=True)
        (self.root / "skills" / "grp" / "SKILL.md").write_text("a grouped skill\n")
        card = self.root / "system" / "projects" / _GIT_HOST_PROJECT / "project.md"
        card.parent.mkdir(parents=True)
        card.write_text(f"# {_GIT_HOST_PROJECT}\n\n**Product path:** products/thing\n")
        (self.root / "system" / "note.md").write_text("a note\n")
        (self.root / ".gitignore").write_text("core/ignored.log\n__pycache__/\n")
        _git("add", "-A", cwd=self.root)
        _git("commit", "-q", "-m", "initial", cwd=self.root)

        self.pins_home = tmp_path / "pins"
        self.pins_home.mkdir()
        self.pin_of_host = pin.make(self.root, self.pins_home)

        engine = tmp_path / "engine_stub.py"
        engine.write_text(ENGINE_STUB)
        engine.chmod(0o755)
        self.argv_log = tmp_path / "engine_argv.log"
        (tmp_path / "home").mkdir()
        self.env = {
            "PATH": os.environ["PATH"],
            "HOME": str(tmp_path / "home"),
            "KENSAIAPP_PINS_HOME": str(self.pins_home),
            "LAUNCH_BUILD_IDEA_SCRIPT": str(engine),
            "ENGINE_ARGV_LOG": str(self.argv_log),
            "DESCRIBE_ARGV_LOG": str(tmp_path / "describe_argv.log"),
        }

    def launcher_of(self, made: pin.Pin) -> Path:
        return made.root / "core" / "launchers" / "build-idea" / "launcher.sh"

    @property
    def host_launcher(self) -> Path:
        return self.root / "core" / "launchers" / "build-idea" / "launcher.sh"

    def launch(self, launcher: Path, *args: str, **env) -> subprocess.CompletedProcess:
        return subprocess.run([str(launcher), *args], cwd=str(self.root), capture_output=True,
                              text=True, env={**self.env, **env})

    def start_from_pin(self, *args: str) -> subprocess.CompletedProcess:
        """Start `build-idea` from inside the pin of the host — `_GIT_HOST_PROJECT` first."""
        return self.launch(self.launcher_of(self.pin_of_host), _GIT_HOST_PROJECT, *args)

    def pin_lines(self, result: subprocess.CompletedProcess) -> list[str]:
        return [line for line in result.stdout.splitlines() if line.startswith("Pin: ")]

    def pin_names(self) -> list[str]:
        return sorted(path.name for path in self.pins_home.iterdir())

    def engine_argv(self) -> list[str]:
        return self.argv_log.read_text().splitlines() if self.argv_log.exists() else []

    def engine_core_dir(self) -> Path:
        argv = self.engine_argv()
        return Path(argv[argv.index("--core-dir") + 1]).resolve()

    def commit_edit(self, relpath: str, text: str = _HOST_EDIT) -> None:
        (self.root / relpath).write_text(text)
        _git("add", "-A", cwd=self.root)
        _git("commit", "-q", "-m", f"edit {relpath}", cwd=self.root)

    def new_pin_root(self) -> Path:
        """The one pin the pins home holds besides the pin of the host as committed."""
        (root,) = [path for path in self.pins_home.iterdir()
                   if path.name != self.pin_of_host.id]
        return root.resolve()


@pytest.fixture
def git_host(tmp_path):
    return GitHost(tmp_path)


def test_a_start_on_a_host_differing_only_by_an_ignored_core_tool_file_and_a_system_file_inherits(
        git_host):
    """CP-167 case 3: a gitignored file inside `core/` and a file under `system/` are not a
    change, so the start keeps the pin it is in."""
    (git_host.root / "core" / "ignored.log").write_text("noise added after the pin\n")
    (git_host.root / "system" / "added_after_the_pin.md").write_text("a new note\n")
    assert (git_host.root / "core" / "ignored.log").exists()
    assert (git_host.root / "system" / "added_after_the_pin.md").exists()

    result = git_host.start_from_pin()

    assert result.returncode == 0, result.stderr
    assert git_host.pin_lines(result) == [f"Pin: {git_host.pin_of_host.root.resolve()} (inherited)"]
    assert git_host.engine_core_dir() == git_host.pin_of_host.core.resolve()
    assert git_host.pin_names() == [git_host.pin_of_host.id]


def test_a_start_after_a_commit_only_under_system_inherits(git_host):
    """CP-163 case 1 through the launcher: `HEAD` moved off the pin's `source_head`, but nothing
    under the three trees changed."""
    git_host.commit_edit("system/note.md")
    assert _git("rev-parse", "HEAD", cwd=git_host.root) != git_host.pin_of_host.source_head

    result = git_host.start_from_pin()

    assert result.returncode == 0, result.stderr
    assert git_host.pin_lines(result) == [f"Pin: {git_host.pin_of_host.root.resolve()} (inherited)"]
    assert git_host.pin_names() == [git_host.pin_of_host.id]


def _assert_one_new_pin_and_engine_runs_from_it(git_host, result, before=None):
    """Exactly one `Pin:` line naming the one new pin as `(new)`; the engine is handed that pin's
    `core/`; the pins home holds the pin of the host as committed and the new pin, and nothing
    else; and, when `before` is given, the first pin's files and bytes are as they were."""
    assert result.returncode == 0, result.stderr
    new_root = git_host.new_pin_root()
    assert git_host.pin_lines(result) == [f"Pin: {new_root} (new)"]
    assert git_host.engine_core_dir() == new_root / "core"
    assert git_host.pin_names() == sorted([git_host.pin_of_host.id, new_root.name])
    if before is not None:
        assert _snapshot(git_host.pin_of_host.root) == before
    return new_root


def test_a_start_inside_a_pin_on_a_host_with_a_committed_edit_takes_a_new_pin(git_host):
    """CP-167 case 1."""
    git_host.commit_edit(".claude/skills/example/SKILL.md")
    before = _snapshot(git_host.pin_of_host.root)

    result = git_host.start_from_pin()

    new_root = _assert_one_new_pin_and_engine_runs_from_it(git_host, result, before)
    assert (new_root / ".claude" / "skills" / "example" / "SKILL.md").read_text() == _HOST_EDIT


def test_a_start_inside_a_pin_on_a_host_with_an_uncommitted_edit_takes_a_new_pin(git_host):
    """CP-167 case 2: `HEAD` is still the commit the pin was made at, so only the working tree
    says the host changed."""
    (git_host.root / "skills" / "grp" / "SKILL.md").write_text(_HOST_EDIT)
    assert _git("rev-parse", "HEAD", cwd=git_host.root) == git_host.pin_of_host.source_head
    before = _snapshot(git_host.pin_of_host.root)

    result = git_host.start_from_pin()

    new_root = _assert_one_new_pin_and_engine_runs_from_it(git_host, result, before)
    assert (new_root / "skills" / "grp" / "SKILL.md").read_text() == _HOST_EDIT


def test_a_plain_start_on_a_changed_host_takes_a_new_pin(git_host):
    """CP-167 case 4: no flag at all."""
    (git_host.root / "core" / "added_after_the_pin.txt").write_text("a new file in core/\n")

    result = git_host.start_from_pin()

    _assert_one_new_pin_and_engine_runs_from_it(git_host, result)


def test_a_chain_ended_sealed_start_on_a_changed_host_takes_a_new_pin(git_host):
    """CP-167 case 5: the start a walk's end makes counts as a start, and is still the hook's."""
    pin_source = git_host.root / "core" / "tools" / "pin.py"
    git_host.commit_edit("core/tools/pin.py", pin_source.read_text() + "\n")

    result = git_host.start_from_pin("--chain-ended", "sealed")

    _assert_one_new_pin_and_engine_runs_from_it(git_host, result)
    assert "--by-hook" in git_host.engine_argv()


def test_a_host_copy_start_under_an_inherited_pin_on_a_changed_host_takes_a_new_pin(git_host):
    """CP-156: the host's own launcher, run with a pin of that host inherited, compares that pin
    and makes the new pin of the host — never of the instance."""
    (git_host.root / ".claude" / "skills" / "example" / "SKILL.md").write_text(_HOST_EDIT)

    result = git_host.launch(git_host.host_launcher, _GIT_HOST_PROJECT,
                             KENSAIAPP_PIN=str(git_host.pin_of_host.root))

    new_root = _assert_one_new_pin_and_engine_runs_from_it(git_host, result)
    manifest = json.loads((new_root / "pin.json").read_text())
    assert manifest["source_host_root"] == str(git_host.root.resolve())


def test_a_chain_ended_halted_start_on_a_changed_host_takes_a_new_pin_then_starts_nothing(
        git_host):
    """CP-159: after the `Pin:` line the output is the launcher's own, unchanged."""
    (git_host.root / "core" / "added_after_the_pin.txt").write_text("new\n")

    result = git_host.start_from_pin("--chain-ended", "halted")

    assert result.returncode == 0, result.stderr
    new_root = git_host.new_pin_root()
    assert result.stdout.splitlines() == [
        f"Pin: {new_root} (new)", "build-idea: the chain ended halted — nothing to start"]
    assert git_host.engine_argv() == []


def test_a_stop_on_a_changed_host_takes_a_new_pin_then_stops(git_host):
    """CP-159: `--stop` is a start too, and prints the engine's own stop line after `Pin:`."""
    (git_host.root / "core" / "added_after_the_pin.txt").write_text("new\n")

    result = git_host.start_from_pin("--stop")

    assert result.returncode == 0, result.stderr
    new_root = git_host.new_pin_root()
    assert result.stdout.splitlines() == [f"Pin: {new_root} (new)", "engine-stub: stop recorded"]


def test_a_dry_run_on_a_changed_host_names_a_new_pin_and_makes_none(git_host):
    """CP-160."""
    (git_host.root / "core" / "added_after_the_pin.txt").write_text("new\n")

    result = git_host.start_from_pin("--dry-run")

    assert result.returncode == 0, result.stderr
    assert git_host.pin_lines(result) == [f"Pin: a new pin of {git_host.root.resolve()}"]
    assert git_host.pin_names() == [git_host.pin_of_host.id]


def test_a_start_whose_pin_host_is_gone_inherits_and_says_so_on_stderr(git_host, tmp_path):
    """CP-161: a pin whose `source_host_root` no longer exists is kept, with one line saying so."""
    manifest_path = git_host.pin_of_host.root / "pin.json"
    manifest = json.loads(manifest_path.read_text())
    vanished = tmp_path / "a-host-that-no-longer-exists"
    manifest["source_host_root"] = str(vanished)
    manifest_path.write_text(json.dumps(manifest))
    assert not vanished.exists()

    result = git_host.start_from_pin()

    assert result.returncode == 0, result.stderr
    assert git_host.pin_lines(result) == [f"Pin: {git_host.pin_of_host.root.resolve()} (inherited)"]
    (stderr_line,) = [line for line in result.stderr.splitlines() if line.strip()]
    assert str(vanished) in stderr_line
    assert git_host.engine_argv()[0] == "--start"
    assert git_host.pin_names() == [git_host.pin_of_host.id]


def test_a_start_naming_a_unit_key_on_a_changed_host_takes_a_new_pin(git_host):
    """CP-159: a start naming a unit key follows the same rule, and after the `Pin:` line the
    output is the launcher's own, unchanged — the key still reaches the engine."""
    (git_host.root / "core" / "added_after_the_pin.txt").write_text("new\n")

    result = git_host.start_from_pin("2026-01-01_some-unit")

    new_root = _assert_one_new_pin_and_engine_runs_from_it(git_host, result)
    assert result.stdout.splitlines() == [
        f"Pin: {new_root} (new)",
        f"build-idea: project={_GIT_HOST_PROJECT}",
        "build-idea: provider=each row's own",
        "engine-stub: started",
    ]
    argv = git_host.engine_argv()
    assert argv[argv.index("--key") + 1] == "2026-01-01_some-unit"


def test_a_dry_run_on_an_unchanged_host_inherits_and_makes_no_pin(git_host):
    """CP-160, the unchanged half: a dry run inside a pin whose host still matches it names that
    pin as inherited and makes nothing."""
    result = git_host.start_from_pin("--dry-run")

    assert result.returncode == 0, result.stderr
    assert git_host.pin_lines(result) == [f"Pin: {git_host.pin_of_host.root.resolve()} (inherited)"]
    assert git_host.pin_names() == [git_host.pin_of_host.id]


def test_renewed_pin_supplies_native_codex_skill_path_to_next_launcher(git_host):
    """A build-idea renewal must reach native selection, not only the engine's core-dir."""
    for name in ('agent_run.py', 'hook_wiring.py', 'codex_skill_run.py', 'model_assignment.py',
                 'task_context.py', 'env_file.py', 'skill_path.py', 'detached_run.sh', 'intelligence.py',
                 'run_intelligence.py', 'providers.py'):
        source = _CORE / 'tools' / name
        if source.exists():
            shutil.copy2(source, git_host.root / 'core' / 'tools' / name)
    target = git_host.root / 'core' / 'launchers' / 'skill'
    target.mkdir()
    shutil.copy2(_CORE / 'launchers' / 'skill' / 'launcher.sh', target / 'launcher.sh')
    skill = git_host.root / '.claude' / 'skills' / 'example'
    (skill / 'SKILL.md').write_text('---\nname: example\ndescription: renewed example\n---\nnew pinned body\n')
    (skill / 'launcher.md').write_text(
        '# Example\n\n**Arguments:** <project>\n'
        '**Prompt:** invoke the example skill for the {project} project.\n'
    )
    # The model a run goes at is the skill's own, beside it (`skill_intelligence.md`).
    (skill / 'intelligence').mkdir()
    (skill / 'intelligence' / 'codex.md').write_text('**Model:** m-1\n')
    result = git_host.start_from_pin()
    new_root = _assert_one_new_pin_and_engine_runs_from_it(git_host, result)
    launch = subprocess.run(
        [str(git_host.engine_core_dir() / 'launchers' / 'skill' / 'launcher.sh'),
         'example', _GIT_HOST_PROJECT, '--provider', 'codex', '--dry-run'],
        cwd=git_host.root, env={**git_host.env, 'KENSAIAPP_PIN': str(new_root)},
        capture_output=True, text=True,
    )
    assert launch.returncode == 0, launch.stderr
    assert '--skill-path' in launch.stdout
    assert str(new_root / '.claude' / 'skills' / 'example' / 'SKILL.md') in launch.stdout
    assert str(git_host.pin_of_host.root / '.claude' / 'skills' / 'example' / 'SKILL.md') not in launch.stdout


@pytest.mark.parametrize("written, resolved", [
    ("products/thing", "{root}/products/thing"),
    ("/abs/thing <!-- a note -->", "/abs/thing"),
    ("~/thing", "{home}/thing"),
])
def test_the_cards_product_path_is_passed_to_the_engine(run, written, resolved):
    run.project("example-product", product_path=written)

    run("example-product")

    assert run.value("--product-path") == resolved.format(root=run.root,
                                                          home=run.env["HOME"])


def test_a_card_with_no_product_path_passes_none(run):
    run.project("example-product", card="# example-product\n")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert "--product-path" not in run.engine_argv()


# CP-425: the usage message, the header's first USAGE line and the missing-value refusal name
# `hf`, in change_text.md's words.
_HF_USAGE = (
    "build-idea: usage: <CORE>/launchers/build-idea/launcher.sh <project> [<unit-key>]"
    " [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake]"
    " [--context-cap <tokens>] [--chain-ended <end>] | <project> --stop"
)
_HF_HEADER_USAGE = (
    "<CORE>/launchers/build-idea/launcher.sh"
    " <project> [<unit-key>] [--provider claude|codex|gemini|hf|ollama]"
)


def test_the_usage_line_names_hf(run):
    result = run()

    assert result.returncode != 0
    assert _HF_USAGE in result.stderr
    assert run.engine_argv() == []


def test_the_header_usage_names_hf():
    header = {line.lstrip("#").strip() for line in _SCRIPT.read_text().splitlines()
              if line.startswith("#")}

    assert _HF_HEADER_USAGE in header


def test_a_provider_flag_with_no_value_is_refused_naming_the_five(run):
    run.project("example-product")

    result = run("example-product", "--provider")

    assert result.returncode != 0
    assert "build-idea: --provider needs claude, codex, gemini, hf or ollama" in result.stderr
    assert run.engine_argv() == []
