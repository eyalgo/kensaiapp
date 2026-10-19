"""Contract tests for `chain-agari/launcher.sh`.

The chain that walks a project's PRD and then its Agari, and nothing after it on its own
initiative. Every producer and answer run is started by the engine, which `core/tools/test_chain.py`
owns. This suite pins the launcher's wiring: the spine and the chain name reaching the engine, the
state path it shares with `chain-product`, every printed line and every refusal.

**`chain.py` is stubbed, never run for real, in this file**: a real `--start` would launch a real
run for a missing document. The one engine call made in-process is `walk_stop.stop_command`, a pure
function that launches nothing.

**No test invokes a real notifier.** The `run` fixture clears `KENSAIAPP_NOTIFIER` on every call.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent / "launcher.sh"
_LAUNCHERS_DIR = _SCRIPT.parent.parent
_CORE = _LAUNCHERS_DIR.parent
_REPO = _CORE.parent
_MANIFEST = _CORE / "doctrine" / "setup" / "kensaiapp_structure.md"

SPINE = "PRD,Agari"
CHAIN_NAME = "agari"
PREFIX = "chain-agari:"
STOP_USAGE = (
    "chain-agari: usage: <CORE>/launchers/chain-agari/launcher.sh <project> --stop"
    " — a stop takes no other flag"
)
FULL_USAGE = (
    "chain-agari: usage: <CORE>/launchers/chain-agari/launcher.sh <project>"
    " [--provider claude|codex|gemini|hf|ollama] [--on-end <command>] [--dry-run] [--keep-awake]"
    " | <project> --stop"
)
ON_END = "/hooks/next.sh --x"

CHAIN_STUB = """#!/usr/bin/env python3
import os, sys
with open(os.environ["CHAIN_ARGV_LOG"], "w") as fh:
    fh.write("\\n".join(sys.argv[1:]))
print(os.environ.get("ENGINE_STUB_LINE", "chain-stub: started"))
sys.exit(int(os.environ.get("ENGINE_STUB_EXIT", "0")))
"""

NOTIFIER_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" >> "$NOTIFIER_ARGV_LOG"
"""


@pytest.fixture
def run(tmp_path, _session_pin):
    """`run(*cli_args) -> CompletedProcess`, invoking the real launcher with `tmp_path` as its
    cwd (the launcher's own instance root, `$PWD`). `run.core_dir` is the session pin's own
    `core/`: every `<CORE>`-derived value the launcher hands the engine resolves there, since the
    launcher enters that pin before anything else reads `CORE_DIR`."""
    chain_stub = tmp_path / "chain_stub.py"
    chain_stub.write_text(CHAIN_STUB)
    chain_stub.chmod(0o755)

    argv_log = tmp_path / "chain_argv.log"

    env = dict(os.environ)
    for name in ("KENSAIAPP_NOTIFIER", "KENSAIAPP_AGENT_PROVIDER",
                 "ENGINE_STUB_LINE", "ENGINE_STUB_EXIT"):
        env.pop(name, None)
    env["LAUNCH_CHAIN_AGARI_SCRIPT"] = str(chain_stub)
    env["CHAIN_ARGV_LOG"] = str(argv_log)
    env["HOME"] = str(tmp_path / "home")
    (tmp_path / "home").mkdir()

    def _run(*cli_args, cwd=None):
        return subprocess.run([str(_SCRIPT), *cli_args], cwd=cwd or str(tmp_path),
                              capture_output=True, text=True, env=env)

    def _project(name, product_path="products/thing", card=None):
        project_dir = tmp_path / "system" / "projects" / name
        project_dir.mkdir(parents=True)
        if card is None:
            card = f"# {name}\n\n**Product path:** {product_path}\n"
        (project_dir / "project.md").write_text(card)
        return project_dir

    def _chain_argv():
        return argv_log.read_text().splitlines() if argv_log.exists() else []

    def _notifier(path):
        env["KENSAIAPP_NOTIFIER"] = str(path)

    _run.root = tmp_path
    _run.home = tmp_path / "home"
    _run.env = env
    _run.core_dir = _session_pin.core
    _run.argv_log = argv_log
    _run.project = _project
    _run.chain_argv = _chain_argv
    _run.notifier = _notifier
    return _run


def _engine():
    sys.path.insert(0, str(_CORE / "tools"))
    import chain
    return chain


def _code_lines():
    return [line for line in _SCRIPT.read_text().splitlines()
            if not line.lstrip().startswith("#")]


def _header():
    return _SCRIPT.read_text().split("set -euo pipefail", 1)[0]


def _lines(result):
    """What the launcher printed, less the `Pin:` lines `pin_enter` prints before anything else.
    Only the leading ones are dropped: a `Pin:` line after the four start lines is not one the
    pin printed first, and CP-408 has the engine's output follow the four lines directly."""
    lines = result.stdout.splitlines()
    while lines and lines[0].startswith("Pin: "):
        lines.pop(0)
    return lines


def _value_after(argv, flag):
    return argv[argv.index(flag) + 1]


def _forced(run):
    argv = run.chain_argv()
    return _value_after(argv, "--provider") if "--provider" in argv else None


def _stub_notifier(tmp_path, run):
    spy = tmp_path / "notifier.sh"
    spy.write_text(NOTIFIER_STUB)
    spy.chmod(0o755)
    run.notifier(spy)
    return spy


# --- the entry command (CP-404) -----------------------------------------------------------------


def test_launcher_exists_is_executable_and_is_named_without_a_launch_prefix():
    assert _SCRIPT.is_file()
    assert os.access(_SCRIPT, os.X_OK)
    assert not _SCRIPT.parent.name.startswith("launch-")
    assert _SCRIPT.parent.name != "chain-product"


# --- the spine (CP-405) -------------------------------------------------------------------------


def test_spine_reaches_the_engine_as_argv(run):
    run.project("example-product")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert _value_after(run.chain_argv(), "--spine") == SPINE


def test_spine_literal_is_committed_once_across_all_launchers():
    assert f'"{SPINE}"' in _SCRIPT.read_text()
    holders = [path for path in sorted(_LAUNCHERS_DIR.rglob("launcher.sh"))
               if f'"{SPINE}"' in path.read_text()]
    assert holders == [_SCRIPT]


def test_exported_spine_variables_do_not_change_the_spine(run):
    run.project("example-product")
    run.env["PRODUCT_SPINE"] = "something else entirely"
    run.env["KENSAIAPP_CHAIN_SPINE"] = "something else entirely"

    run("example-product")

    assert _value_after(run.chain_argv(), "--spine") == SPINE


def test_every_spine_document_is_known_to_the_engine_and_its_skill_takes_project():
    chain = _engine()
    documents = chain.parse_spine(SPINE)
    assert [spec.name for spec in documents] == SPINE.split(",")
    for name in SPINE.split(","):
        spec = chain.document(name)
        resolved = subprocess.run(
            ["python3", str(_CORE / "tools" / "skill_path.py"), spec.skill,
             "--root", str(_REPO)], capture_output=True, text=True)
        assert resolved.returncode == 0, (spec.skill, resolved.stderr)
        declaration = (Path(resolved.stdout.strip()) / "launcher.md").read_text()
        assert re.search(r"^\*\*Arguments:\*\* <project>\s*$", declaration,
                         re.MULTILINE), spec.skill


# --- the chain name (CP-406, CP-407) ------------------------------------------------------------


def test_chain_name_reaches_the_engine_and_is_a_committed_literal(run):
    run.project("example-product")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert _value_after(run.chain_argv(), "--chain-name") == CHAIN_NAME
    assert f'"{CHAIN_NAME}"' in _SCRIPT.read_text()
    assert CHAIN_NAME != "product"


def test_exported_chain_name_variables_do_not_change_the_chain_name(run):
    run.project("example-product")
    run.env["CHAIN_NAME"] = "something else entirely"
    run.env["KENSAIAPP_CHAIN_NAME"] = "something else entirely"

    run("example-product")

    assert _value_after(run.chain_argv(), "--chain-name") == CHAIN_NAME


def test_folder_name_and_the_engines_stop_command_name_this_launcher():
    """The engine prints a live walk's stop command from the chain name the walk recorded. A
    launcher folder that is not `chain-<name>` would be named there and not exist."""
    _engine()
    from walk_stop import stop_command

    assert _SCRIPT.parent.name == f"chain-{CHAIN_NAME}"
    command = stop_command(str(_CORE), f"chain-{CHAIN_NAME}", "example-product")
    assert Path(shlex.split(command)[0]).resolve() == _SCRIPT
    assert command.endswith("example-product --stop")


# --- what a start does (CP-408, CP-409) ---------------------------------------------------------


def test_start_prints_four_lines_then_the_engine_output_and_returns_its_status(run):
    run.project("example-product")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert _lines(result) == [
        "chain-agari: project=example-product",
        f"chain-agari: product path={run.root}/products/thing",
        f"chain-agari: spine={SPINE}",
        "chain-agari: provider=each document's own",
        "chain-stub: started",
    ]
    run.env["ENGINE_STUB_EXIT"] = "3"
    assert run("example-product").returncode == 3


def test_start_argv_is_exactly_the_documented_set(run):
    run.project("example-product")

    run("example-product")

    assert run.chain_argv() == [
        "--start", f"{run.root}/system/logs/chain-example-product-state.json",
        "--instance-root", str(run.root), "--product-path", f"{run.root}/products/thing",
        "--project", "example-product", "--core-dir", str(run.core_dir),
        "--shim-path", f"{run.root}/system/logs/chain-example-product.sh",
        "--spine", SPINE, "--chain-name", CHAIN_NAME]


def test_notifier_is_passed_but_never_run(run, tmp_path):
    log = tmp_path / "notifier_argv.log"
    run.env["NOTIFIER_ARGV_LOG"] = str(log)
    run.project("example-product")

    assert run("example-product").returncode == 0
    assert "--notifier" not in run.chain_argv()

    spy = _stub_notifier(tmp_path, run)
    run("example-product")

    assert _value_after(run.chain_argv(), "--notifier") == str(spy)
    assert not log.exists()


def test_an_empty_notifier_is_left_out_of_a_start_and_a_stop(run):
    """CP-409 and CP-417: an empty `KENSAIAPP_NOTIFIER` is never an error, and no `--notifier`
    reaches the engine, on a start or on a stop."""
    run.project("example-product")
    run.env["KENSAIAPP_NOTIFIER"] = ""

    assert run("example-product").returncode == 0
    assert "--notifier" not in run.chain_argv()

    assert run("example-product", "--stop").returncode == 0
    assert run.chain_argv() == ["--stop", f"{run.root}/system/logs/chain-example-product-state.json"]


def test_dry_run_prints_the_inherited_pin_line(run):
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert re.search(r"^Pin: .+\(inherited\)$", result.stdout, re.MULTILINE)


@pytest.mark.parametrize(("card_value", "resolved"), [
    ("products/thing", "{root}/products/thing"),
    ("/somewhere/else", "/somewhere/else"),
    ("~/products/thing", "{home}/products/thing"),
    ("products/thing <!-- a note -->", "{root}/products/thing"),
    ("products/thing   ", "{root}/products/thing"),
], ids=["relative", "absolute", "tilde", "trailing-comment", "trailing-whitespace"])
def test_product_path_forms(run, card_value, resolved):
    run.project("example-product", product_path=card_value)
    expected = resolved.format(root=run.root, home=run.home)

    result = run("example-product")

    assert f"chain-agari: product path={expected}" in result.stdout.splitlines()
    assert _value_after(run.chain_argv(), "--product-path") == expected


def test_the_first_product_path_line_is_the_one_read(run):
    """CP-410: the value comes from the card's first `**Product path:**` line."""
    run.project("example-product", card=(
        "# example-product\n\n**Product path:** products/first\n**Product path:** products/second\n"))

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert _value_after(run.chain_argv(), "--product-path") == f"{run.root}/products/first"


def test_an_ended_state_file_does_not_stop_a_start(run):
    run.project("example-product")
    state = run.root / "system" / "logs" / "chain-example-product-state.json"
    state.parent.mkdir(parents=True)
    ended = '{"ended": "sealed"}'
    state.write_text(ended)

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert run.chain_argv()[:2] == ["--start", str(state)]
    assert state.read_text() == ended


# --- the provider force (CP-412) ----------------------------------------------------------------


@pytest.mark.parametrize("provider", ["codex", "claude", "gemini"])
def test_provider_flag_forces_the_provider(run, provider):
    run.project("example-product")

    result = run("example-product", "--provider", provider)

    assert result.returncode == 0, result.stderr
    assert _forced(run) == provider
    assert _lines(result)[3] == (
        f"chain-agari: provider={provider} (forced on every document)")


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


def test_provider_from_the_environment_forces_alone_and_the_flag_wins(run):
    run.project("example-product")
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"

    assert run("example-product").returncode == 0
    assert _forced(run) == "codex"
    assert run("example-product", "--provider=claude").returncode == 0
    assert _forced(run) == "claude"


def test_unknown_provider_is_refused_before_the_engine_runs(run):
    run.project("example-product")

    result = run("example-product", "--provider", "other")

    assert result.returncode == 1
    assert ("chain-agari: provider must be claude, codex, gemini, hf or ollama (got 'other')"
            in result.stderr)
    assert run.chain_argv() == []


def test_provider_flag_without_a_value_is_refused(run):
    run.project("example-product")

    result = run("example-product", "--provider")

    assert result.returncode == 1
    assert "chain-agari: --provider needs claude, codex, gemini, hf or ollama" in result.stderr
    assert run.chain_argv() == []


# --- --on-end (CP-413) --------------------------------------------------------------------------


def test_on_end_value_reaches_argv_as_one_token(run):
    run.project("example-product")

    assert run("example-product", "--on-end", ON_END).returncode == 0
    assert _value_after(run.chain_argv(), "--on-end") == ON_END
    argv = run.chain_argv()
    assert argv.count("--on-end") == 1 and ON_END in argv

    dry = run("example-product", "--dry-run", "--on-end", ON_END)
    printed = shlex.split(dry.stdout.split("DRY RUN — would run:")[1])
    assert _value_after(printed, "--on-end") == ON_END


@pytest.mark.parametrize("args", [("--on-end",), ("--on-end", "")], ids=["missing", "empty"])
def test_on_end_without_a_command_is_refused(run, args):
    run.project("example-product")

    result = run("example-product", *args)

    assert result.returncode == 1
    assert "chain-agari: --on-end needs a command" in result.stderr
    assert run.chain_argv() == []


# --- --dry-run, --keep-awake and flag order (CP-414 to CP-416) ----------------------------------


def test_dry_run_prints_the_command_and_starts_nothing(run):
    run.project("example-product")
    real = run("example-product")
    real_argv = run.chain_argv()
    run.argv_log.unlink()

    dry = run("example-product", "--dry-run")

    lines = _lines(dry)
    assert dry.returncode == 0
    assert lines[:4] == _lines(real)[:4]
    assert lines[4] == "DRY RUN — would run:"
    assert len(lines) == 6
    assert run.chain_argv() == []
    printed = shlex.split(lines[5])
    for token in real_argv:
        assert token in printed, token


def test_keep_awake_is_passed_only_when_given(run):
    run.project("example-product")

    run("example-product")
    assert "--keep-awake" not in run.chain_argv()

    run("example-product", "--keep-awake")
    assert "--keep-awake" in run.chain_argv()
    assert not [line for line in _code_lines() if "caffeinate" in line]


@pytest.mark.parametrize(("args", "expected", "dry"), [
    (("example-product", "--keep-awake", "--dry-run"), ["--keep-awake"], True),
    (("example-product", "--dry-run", "--keep-awake"), ["--keep-awake"], True),
    (("example-product", "--on-end", "X", "--keep-awake"), ["--on-end", "X", "--keep-awake"], False),
    (("example-product", "--keep-awake", "--on-end", "X", "--provider", "codex"),
     ["--keep-awake", "--on-end", "X", "--provider", "codex"], False),
], ids=["keep-dry", "dry-keep", "on-end-keep", "keep-on-end-provider"])
def test_flags_are_accepted_in_any_order(run, args, expected, dry):
    run.project("example-product")

    result = run(*args)

    assert result.returncode == 0, result.stderr
    reached = shlex.split(result.stdout.split("DRY RUN — would run:")[1]) if dry \
        else run.chain_argv()
    for token in expected:
        assert token in reached, token


# --- --stop (CP-417) ----------------------------------------------------------------------------


def test_stop_runs_the_engine_stop_on_the_state_path(run, tmp_path):
    run.project("example-product")
    state = f"{run.root}/system/logs/chain-example-product-state.json"

    assert run("example-product", "--stop").returncode == 0
    assert run.chain_argv() == ["--stop", state]

    spy = _stub_notifier(tmp_path, run)
    run("example-product", "--stop")
    assert run.chain_argv() == ["--stop", state, "--notifier", str(spy)]

    run.env["ENGINE_STUB_LINE"] = "stopped: nothing was live"
    run.env["ENGINE_STUB_EXIT"] = "3"
    result = run("example-product", "--stop")
    assert result.returncode == 3
    assert "stopped: nothing was live" in result.stdout


@pytest.mark.parametrize("flag", [
    ("--dry-run",), ("--keep-awake",), ("--provider", "codex"), ("--on-end", "X"),
], ids=["--dry-run", "--keep-awake", "--provider codex", "--on-end X"])
def test_stop_with_any_other_flag_is_refused(run, flag):
    run.project("example-product")

    after = run("example-product", "--stop", *flag)
    before = run("example-product", *flag, "--stop")

    for result in (after, before):
        assert result.returncode == 1
        assert STOP_USAGE in result.stderr
    assert run.chain_argv() == []


def test_an_exported_provider_is_not_a_flag_beside_a_stop(run):
    """CP-417: `<project> --stop` with no other flag runs the engine's stop. An exported
    `KENSAIAPP_AGENT_PROVIDER` is the environment's force, not a flag, so it neither refuses the
    stop nor reaches the stop's argv."""
    run.project("example-product")
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"

    result = run("example-product", "--stop")

    assert result.returncode == 0, result.stderr
    assert run.chain_argv() == ["--stop", f"{run.root}/system/logs/chain-example-product-state.json"]


# --- refusing a missing assumption (CP-418) -----------------------------------------------------


def test_missing_assumptions_are_refused_with_the_stated_message(run):
    run.project("example-product")
    run.project("bare", card="# bare\n\nno path here\n")
    card = run.root / "system" / "projects"

    cases = [
        ((), FULL_USAGE),
        (("nope",),
         f"chain-agari: no project card at {card}/nope/project.md (is 'nope' a real project?)"),
        (("bare",), f"chain-agari: no 'Product path:' line in {card}/bare/project.md"),
        (("example-product", "--wat"), "chain-agari: unknown flag: --wat"),
        (("example-product", "extra"), "chain-agari: unexpected argument: extra"),
    ]
    for args, message in cases:
        result = run(*args)
        assert result.returncode == 1, args
        assert message in result.stderr.splitlines(), (args, result.stderr)
        assert run.chain_argv() == [], args
    assert run().stderr.startswith("chain-agari: usage:")


# --- the file itself (CP-419, CP-420) -----------------------------------------------------------


def test_header_states_what_it_launches_and_assumes():
    header = _header()

    assert "chain.py" in header and SPINE in header
    for assumption, refusal in (
        ("instance root", "chain-agari: no project card at <card path>"),
        ("project.md", "chain-agari: no 'Product path:' line in <card path>"),
        ("Product path", "chain-agari: no 'Product path:' line in <card path>"),
        ("/launchers/", "chain-agari: no /launchers/ ancestor above"),
    ):
        assert assumption in header, assumption
        assert refusal in header, refusal
    assert "## Launchers owed" in header and "still walked" in header
    usage = header.split("# USAGE", 1)[1]
    assert "<CORE>/launchers/chain-agari/launcher.sh <project> [--provider" in usage
    assert "--on-end" in usage and "<project> --stop" in usage


def test_usage_names_both_invocation_forms_in_full():
    """CP-419: `# USAGE` names both forms whole. The start form wraps across two comment lines, so
    its pieces are read in order from the joined block."""
    usage = " ".join(line.lstrip("#").strip()
                     for line in _header().split("# USAGE", 1)[1].splitlines())

    start = ("<CORE>/launchers/chain-agari/launcher.sh <project> "
             "[--provider claude|codex|gemini|hf|ollama] "
             "[--on-end <command>] [--dry-run] [--keep-awake]")
    assert start in usage
    assert "<CORE>/launchers/chain-agari/launcher.sh <project> --stop" in usage


def test_code_lines_name_no_core_path_no_claude_dir_and_no_answer_step():
    code = "\n".join(_code_lines())

    assert "~/.claude/" not in code
    assert not re.search(r"(?<![\w/.])core/", code)
    assert "claude " not in code
    assert "companion-self-answer" not in code


# --- the record that names it (CP-422, CP-423) --------------------------------------------------


def _bullets():
    return [line for line in _MANIFEST.read_text().splitlines() if line.startswith("- ")]


def test_manifest_places_the_launcher_and_suite_bullets_after_chain_products_pair():
    bullets = _bullets()
    start = next(index for index, line in enumerate(bullets)
                 if line.startswith("- `core/launchers/chain-product/test_chain_product.py`"))

    following = bullets[start + 1:start + 4]

    assert following[0].startswith("- `core/launchers/chain-agari/launcher.sh`")
    assert following[1].startswith("- `core/launchers/chain-agari/test_chain_agari.py`")
    assert following[2].startswith("- `core/launchers/chain-development/launcher.sh`")


def _launcher_bullet():
    lines = _MANIFEST.read_text().splitlines()
    start = next(index for index, line in enumerate(lines)
                 if line.startswith("- `core/launchers/chain-agari/launcher.sh`"))
    end = next(index for index in range(start + 1, len(lines)) if lines[index].startswith("- "))
    return " ".join(line.strip() for line in lines[start:end])


def test_manifest_launcher_bullet_states_its_literals_shared_walk_and_both_forms():
    """CP-422: the launcher bullet states the spine literal, the chain-name literal, the walk it
    shares with `chain-product` and both invocation forms."""
    bullet = _launcher_bullet()

    assert f'`"{SPINE}"`' in bullet
    assert f'`"{CHAIN_NAME}"`' in bullet
    assert "`system/logs/chain-<project>-state.json`" in bullet and "chain-product" in bullet
    assert ("`<CORE>/launchers/chain-agari/launcher.sh <project> "
            "[--provider claude|codex|gemini|hf|ollama]"
            " [--on-end <command>] [--dry-run] [--keep-awake]`") in bullet
    assert "`<CORE>/launchers/chain-agari/launcher.sh <project> --stop`" in bullet


def test_manifest_chain_py_bullet_names_both_entry_commands():
    lines = _MANIFEST.read_text().splitlines()
    start = next(index for index, line in enumerate(lines)
                 if line.startswith("- `core/tools/chain.py`"))
    end = next(index for index in range(start + 1, len(lines)) if lines[index].startswith("- "))
    bullet = " ".join(lines[start:end])

    assert "`core/launchers/chain-product/`" in bullet
    assert "`core/launchers/chain-agari/`" in bullet


def test_suite_basename_is_unique_under_core_launchers():
    found = list(_LAUNCHERS_DIR.rglob("test_chain_agari.py"))

    assert found == [Path(__file__).resolve()]
