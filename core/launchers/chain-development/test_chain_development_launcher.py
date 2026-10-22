"""Contract tests for `chain-development/launcher.sh`.

**Named `test_chain_development_launcher.py`, not `test_chain_development.py`.** The identity rule
(`kensaiapp_structure.md` § Owner-run launcher folder) would give this suite the second name, and
`core/tools/test_chain_development.py` — the engine's suite — already holds it. pytest imports test
modules by basename, so the same name twice aborts every run with `import file mismatch`, which is
the failure that rule exists to prevent.

**The engine is stubbed, never run for real, in this file.** A real `--start` would discover a
change and launch a real `claude --bg` run through `<CORE>/launchers/skill/launcher.sh`. What the
engine does with its argv is `core/tools/test_chain_development.py`'s to pin; this suite pins the
argv this launcher builds.

**No test invokes a real notifier.** `KENSAIAPP_NOTIFIER` is cleared on every call — to a spy when a
test asks for one, to nothing otherwise.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent / "launcher.sh"
_EXAMPLE = Path(__file__).resolve().parents[3] / ".providers.toml.example"

ENGINE_STUB = """#!/usr/bin/env python3
import os, sys
if "--describe" in sys.argv:
    with open(os.environ["DESCRIBE_ARGV_LOG"], "w") as fh:
        fh.write("\\n".join(sys.argv[1:]))
    refusal = os.environ.get("DESCRIBE_REFUSE")
    if refusal:
        print("chain_development: " + refusal, file=sys.stderr)
        sys.exit(3)
    sys.stderr.write(os.environ.get("DESCRIBE_STDERR", ""))
    if "DESCRIBE_STDOUT" in os.environ:
        sys.stdout.write(os.environ["DESCRIBE_STDOUT"])
    else:
        print("key=2026-09-15_stub-change")
        print("entry=design")
    sys.exit(int(os.environ.get("DESCRIBE_EXIT", "0")))
with open(os.environ["ENGINE_ARGV_LOG"], "w") as fh:
    fh.write("\\n".join(sys.argv[1:]))
print(os.environ.get("ENGINE_STUB_LINE", "engine-stub: started"))
sys.exit(int(os.environ.get("ENGINE_STUB_EXIT", "0")))
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
    for name in ("ENGINE_STUB_LINE", "ENGINE_STUB_EXIT"):
        env.pop(name, None)
    for name in ("DESCRIBE_REFUSE", "DESCRIBE_STDERR", "DESCRIBE_STDOUT", "DESCRIBE_EXIT"):
        env.pop(name, None)
    env["LAUNCH_CHAIN_DEVELOPMENT_SCRIPT"] = str(engine_stub)
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
    _run.home = tmp_path / "home"
    _run.env = env
    _run.core_dir = _session_pin.core
    _run.pin_root = _session_pin.root
    _run.project = _project
    _run.engine_argv = _engine_argv
    _run.describe_argv = _describe_argv
    _run.value = _value
    return _run


# --- the engine invocation --------------------------------------------------------------------


def test_hands_the_walk_to_the_engine_start_with_its_own_state_file(run):
    run.project("example-product")

    result = run("example-product")

    assert result.returncode == 0
    argv = run.engine_argv()
    assert argv[0] == "--start"
    assert argv[1] == f"{run.root}/system/logs/chain-development-example-product-state.json"


def test_the_state_file_is_not_the_one_the_document_chain_keeps(run):
    """`chain-product` keeps `chain-<project>-state.json`, and a development walk must be able to
    run while it is walking the same project."""
    run.project("example-product")

    run("example-product")

    assert run.engine_argv()[1] != f"{run.root}/system/logs/chain-example-product-state.json"


def test_start_is_given_every_flag_the_engine_requires_with_resolved_values(run):
    run.project("example-product", product_path="products/thing")

    run("example-product")

    assert run.value("--instance-root") == str(run.root)
    assert run.value("--product-path") == f"{run.root}/products/thing"
    assert run.value("--project") == "example-product"
    assert run.value("--core-dir") == str(run.core_dir)
    assert run.value("--shim-dir") == f"{run.root}/system/logs"


def test_dry_run_prints_the_pin_line(run):
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert re.search(r"^Pin: .+\(inherited\)$", result.stdout, re.MULTILINE)


def test_the_engine_is_started_from_the_pin(run):
    run.project("example-product")

    run("example-product")

    assert run.value("--core-dir") == str(run.core_dir)


def test_the_engine_is_given_no_spine_and_no_chain_name(run):
    """The document chains pass both; this engine owns its step table and its name, so a flag
    carrying either would be one it refuses."""
    run.project("example-product")

    run("example-product")

    assert "--spine" not in run.engine_argv()
    assert "--chain-name" not in run.engine_argv()


def test_the_engine_defaults_to_the_development_chain_under_core(run):
    """With the override gone the dry run asks the REAL engine, so the default path is proven by
    a call that answers, not by a string the launcher printed."""
    run.project("example-product")
    # The dry run asks the real engine, which reads the instance's own provider file.
    (run.root / ".providers.toml").write_text(
        _EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    change = run.root / "system" / "projects" / "example-product" / "journey" / "tobiishi" / "2026-09-15_real"
    change.mkdir(parents=True)
    (change / "change_request.md").write_text("req\n")
    run.env.pop("LAUNCH_CHAIN_DEVELOPMENT_SCRIPT")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "change=2026-09-15_real" in result.stdout
    assert "entry step=specs" in result.stdout
    assert f"{run.core_dir}/tools/chain_development.py" in result.stdout
    assert not (run.root / "system" / "logs").exists()


# --- the guards -------------------------------------------------------------------------------


def test_no_project_arg_dies_with_usage(run):
    result = run()

    assert result.returncode != 0
    assert "usage:" in result.stderr
    assert run.engine_argv() == []


def test_unknown_project_dies_before_launching(run):
    result = run("nope")

    assert result.returncode != 0
    assert "no project card" in result.stderr
    assert run.engine_argv() == []


def test_project_card_without_product_path_dies(run):
    run.project("example-product", card="# example-product\n\nno path here\n")

    result = run("example-product")

    assert result.returncode != 0
    assert "Product path" in result.stderr
    assert run.engine_argv() == []


def test_unknown_flag_is_refused_not_silently_ignored(run):
    run.project("example-product")

    result = run("example-product", "--wat")

    assert result.returncode != 0
    assert "unknown flag" in result.stderr
    assert run.engine_argv() == []


def test_an_extra_positional_argument_is_refused(run):
    run.project("example-product")

    result = run("example-product", "2026-09-15_a-key")

    assert result.returncode != 0
    assert "unexpected argument" in result.stderr
    assert run.engine_argv() == []


# --- the product path -------------------------------------------------------------------------


def test_absolute_product_path_is_used_verbatim(run):
    run.project("example-product", product_path="/somewhere/else")

    run("example-product")

    assert run.value("--product-path") == "/somewhere/else"


def test_tilde_product_path_expands_to_home(run):
    run.project("example-product", product_path="~/products/thing")

    run("example-product")

    assert run.value("--product-path") == f"{run.home}/products/thing"


def test_trailing_comment_is_stripped_from_the_product_path(run):
    run.project("example-product", card="# example-product\n\n**Product path:** products/thing <!-- a note -->\n")

    run("example-product")

    assert run.value("--product-path") == f"{run.root}/products/thing"


# --- the notifier -----------------------------------------------------------------------------


def test_an_unset_notifier_is_skipped_never_an_error(run):
    run.project("example-product")

    result = run("example-product")

    assert result.returncode == 0
    assert "--notifier" not in run.engine_argv()


def test_kensaiapp_notifier_is_resolved_here_and_passed_but_never_invoked(run, tmp_path):
    log = tmp_path / "notifier_argv.log"
    spy = tmp_path / "notifier.sh"
    spy.write_text(NOTIFIER_STUB)
    spy.chmod(0o755)
    run.env["NOTIFIER_ARGV_LOG"] = str(log)
    run.env["KENSAIAPP_NOTIFIER"] = str(spy)
    run.project("example-product")

    run("example-product")

    assert run.value("--notifier") == str(spy)
    assert not log.exists()


# --- --dry-run and --keep-awake ---------------------------------------------------------------


def test_dry_run_asks_the_engine_to_describe_and_never_to_start(run):
    run.project("example-product")

    dry = run("example-product", "--dry-run")

    assert dry.returncode == 0, dry.stderr
    assert run.engine_argv() == []
    assert run.describe_argv() == [
        "--describe", f"{run.root}/system/logs/chain-development-example-product-state.json",
        "--instance-root", str(run.root), "--product-path", f"{run.root}/products/thing",
        "--project", "example-product"]


@pytest.mark.parametrize("card_path, resolved", [
    ("products/thing", "{root}/products/thing"),
    ("/somewhere/else", "/somewhere/else"),
    ("~/products/thing", "{home}/products/thing"),
])
def test_the_dry_run_describe_gets_the_product_path_a_start_would(run, card_path, resolved):
    """The dry run reports what a real start would do, so `--describe` reads the commits where the
    start will: the product path it is given is the one the start's argv carries, however the card
    spells it."""
    run.project("example-product", product_path=card_path)
    expected = resolved.format(root=run.root, home=run.home)

    run("example-product")
    started = run.value("--product-path")
    dry = run("example-product", "--dry-run")

    assert dry.returncode == 0, dry.stderr
    described = run.describe_argv()
    assert described[described.index("--product-path") + 1] == started == expected


def test_dry_run_names_the_change_and_the_entry_step_before_the_command(run):
    run.project("example-product")

    dry = run("example-product", "--dry-run")

    lines = dry.stdout.splitlines()
    assert "chain-development: change=2026-09-15_stub-change" in lines
    assert "chain-development: entry step=design" in lines
    assert lines.index("chain-development: entry step=design") < lines.index("DRY RUN — would run:")


def test_dry_run_prints_every_token_the_real_start_invokes(run):
    run.project("example-product")
    dry = run("example-product", "--dry-run")

    run("example-product")

    for token in run.engine_argv():
        assert token in dry.stdout, token


def test_a_refused_describe_fails_the_dry_run_with_the_engines_reason(run):
    """A dry run that prints a command the real start would refuse is a dry run that lies."""
    run.project("example-product")
    run.env["DESCRIBE_REFUSE"] = "no active change under the project"

    dry = run("example-product", "--dry-run")

    assert dry.returncode != 0
    assert "no active change under the project" in dry.stderr
    assert "DRY RUN" not in dry.stdout
    assert run.engine_argv() == []


# --- development-code-integrity, 2026-09-15: the dry run, tested from its plan ------------------
#
# From the approved plan `plan-something-like-development-frolicking-crystal.md`: the outcome (a dry
# run "names the change the walk would carry and the step it would enter at", "fails with the same
# reason the real start would give", and "writes nothing") and § Design 2 ("Non-zero exit: `die`
# with the engine's own reason, and never print `DRY RUN`").


def test_a_describe_that_crashes_fails_the_dry_run_with_what_the_engine_said(run):
    run.project("example-product")
    run.env["DESCRIBE_STDOUT"] = ""
    run.env["DESCRIBE_STDERR"] = ("Traceback (most recent call last):\n"
                                  "  File \"chain_development.py\", line 1, in <module>\n"
                                  "TypeError: the state could not be read\n")
    run.env["DESCRIBE_EXIT"] = "5"

    dry = run("example-product", "--dry-run")

    assert dry.returncode != 0
    assert "TypeError: the state could not be read" in dry.stderr
    assert "DRY RUN" not in dry.stdout
    assert run.engine_argv() == []


@pytest.mark.parametrize("stdout", [
    "",
    "engine-stub: started\n",
    "key=2026-09-15_stub-change\n",
    "entry=design\n",
    "key=\nentry=\n",
], ids=["nothing", "unrelated-line", "key-only", "entry-only", "empty-values"])
def test_a_describe_that_exits_zero_without_naming_the_change_and_step_fails_the_dry_run(run,
                                                                                         stdout):
    """A dry run that cannot name the change and the entry step has not done what it is for, and
    must not print a `DRY RUN` block as though it had. An engine that ignores `--describe` — the
    stub this suite used before the dry run asked — answers exactly like this."""
    run.project("example-product")
    run.env["DESCRIBE_STDOUT"] = stdout

    dry = run("example-product", "--dry-run")

    assert dry.returncode != 0
    assert "DRY RUN" not in dry.stdout
    assert run.engine_argv() == []


def test_stderr_noise_from_a_successful_describe_stays_out_of_the_change_and_the_step(run):
    run.project("example-product")
    run.env["DESCRIBE_STDERR"] = "DeprecationWarning: something upstream changed\n"

    dry = run("example-product", "--dry-run")

    assert dry.returncode == 0, dry.stderr
    lines = dry.stdout.splitlines()
    assert "chain-development: change=2026-09-15_stub-change" in lines
    assert "chain-development: entry step=design" in lines
    assert "DRY RUN — would run:" in lines


@pytest.mark.parametrize("refuse", [False, True], ids=["answered", "refused"])
def test_the_dry_run_leaves_no_temporary_file_behind(run, tmp_path, refuse):
    run.project("example-product")
    scratch = tmp_path / "scratch-tmp"
    scratch.mkdir()
    run.env["TMPDIR"] = str(scratch)
    if refuse:
        run.env["DESCRIBE_REFUSE"] = "no active change under the project"

    run("example-product", "--dry-run")

    assert list(scratch.iterdir()) == []


def test_with_no_active_change_the_real_engine_fails_the_dry_run_and_writes_nothing(run):
    """Plan § Verification 2, in a scratch instance: no change folder, the real engine, and the
    dry run fails with "no active change", prints no `DRY RUN` line, and leaves no `system/logs`."""
    run.project("example-product")
    (run.root / "system" / "projects" / "example-product" / "journey" / "tobiishi").mkdir(parents=True)
    run.env.pop("LAUNCH_CHAIN_DEVELOPMENT_SCRIPT")

    dry = run("example-product", "--dry-run")

    assert dry.returncode != 0
    assert "no active change" in dry.stderr
    assert "Traceback" not in dry.stderr
    assert "DRY RUN" not in dry.stdout
    assert not (run.root / "system" / "logs").exists()


def test_keep_awake_is_passed_to_the_engine_only_when_asked(run):
    run.project("example-product")

    run("example-product")
    assert "--keep-awake" not in run.engine_argv()

    run("example-product", "--keep-awake")
    assert "--keep-awake" in run.engine_argv()


def test_keep_awake_is_accepted_in_either_order_with_dry_run(run):
    run.project("example-product")

    for args in (("example-product", "--dry-run", "--keep-awake"), ("example-product", "--keep-awake", "--dry-run")):
        result = run(*args)
        assert result.returncode == 0
        assert "--keep-awake" in result.stdout


# --- the file itself ---------------------------------------------------------------------------


def _code_lines() -> list[str]:
    return [line for line in _SCRIPT.read_text().splitlines() if not line.lstrip().startswith("#")]


def test_this_launcher_spawns_no_run_holds_no_keep_awake_and_tags_nothing():
    """Each step's own launch goes through `<CORE>/launchers/skill/launcher.sh`, which already
    detaches the watcher, holds the keep-awake and tags the run. A copy of any of the three here
    would cover none of the walk, because this script exits once the first step is launched."""
    code = "\n".join(_code_lines())

    assert "caffeinate" not in code
    assert "claude --bg" not in code and "claude -p " not in code
    assert not any(
        line.strip() == "run_telemetry" or line.strip().startswith("run_telemetry ")
        for line in _code_lines()
    )


def test_launcher_is_executable():
    assert os.access(_SCRIPT, os.X_OK)


def test_the_launcher_names_no_literal_core_path():
    code = "\n".join(_code_lines())

    assert "~/.claude/" not in code
    assert not re.search(r"(?<![\w/.])core/", code)


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
    assert "chain-development: provider=" + provider + " (forced on every step)" in result.stdout


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
    """Each step then runs on its own provider: the entry the instance's `.providers.toml` holds."""
    run.project("example-product")
    run.env.pop("KENSAIAPP_AGENT_PROVIDER", None)

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert _forced(run) is None
    assert "chain-development: provider=each step's own" in result.stdout


def test_unknown_provider_is_refused_before_the_engine(run):
    run.project("example-product")

    result = run("example-product", "--provider", "other")

    assert result.returncode != 0
    assert "provider must be claude, codex, gemini, hf or ollama (got 'other')" in result.stderr
    assert run.engine_argv() == []


# --- --stop: the owner's brake, handed to the engine's --stop (CP-373) -------------------------


def test_stop_reaches_the_engine_stop_with_the_state_path(run):
    run.project("example-product")

    result = run("example-product", "--stop")

    assert result.returncode == 0, result.stderr
    state = f"{run.root}/system/logs/chain-development-example-product-state.json"
    assert run.engine_argv() == ["--stop", state]


def test_stop_passes_the_notifier_it_resolved(run, tmp_path):
    run.project("example-product")
    run.env["KENSAIAPP_NOTIFIER"] = str(tmp_path / "notify.sh")

    run("example-product", "--stop")

    argv = run.engine_argv()
    assert argv[argv.index("--notifier") + 1] == str(tmp_path / "notify.sh")


def test_stop_prints_the_engines_line_and_exits_with_its_status(run):
    run.project("example-product")
    run.env["ENGINE_STUB_LINE"] = "stopped: nothing was live"
    run.env["ENGINE_STUB_EXIT"] = "3"

    result = run("example-product", "--stop")

    assert result.returncode == 3
    assert "stopped: nothing was live" in result.stdout


@pytest.mark.parametrize(
    "flag",
    [
        ("--dry-run",),
        ("--keep-awake",),
        ("--provider", "claude"),
    ],
    ids=[
        "--dry-run",
        "--keep-awake",
        "--provider claude",
    ],
)
def test_stop_with_another_flag_dies_and_runs_no_engine(run, flag):
    run.project("example-product")

    after = run("example-product", "--stop", *flag)
    before = run("example-product", *flag, "--stop")

    for result in (after, before):
        assert result.returncode == 1
        assert "<project> --stop" in result.stderr
    assert run.engine_argv() == []


def test_the_usage_names_the_stop():
    header = _SCRIPT.read_text().split("set -euo pipefail", 1)[0]

    assert "<project> --stop" in header.split("# USAGE", 1)[1]


# CP-425: the usage message, the header's first USAGE line and the missing-value refusal name
# `hf`, in change_text.md's words.
_HF_USAGE = (
    "chain-development: usage: <CORE>/launchers/chain-development/launcher.sh <project>"
    " [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake] [--gate-owners-mac]"
    " | <project> --stop"
)
_HF_HEADER_USAGE = (
    "<CORE>/launchers/chain-development/launcher.sh"
    " <project> [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake]"
    " [--gate-owners-mac]"
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
    assert (
        "chain-development: --provider needs claude, codex, gemini, hf or ollama"
    ) in result.stderr
    assert run.engine_argv() == []
