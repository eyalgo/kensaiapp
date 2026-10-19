"""Contract tests for `chain-product/launcher.sh`.

The one chain over a product's documents: its spine is every product document, both tiers, and every
producer runs through `<CORE>/launchers/skill/launcher.sh` — the engine's own rule, which
`core/tools/test_chain.py` owns. This suite pins the launcher's wiring, and that every skill the walk
will start declares a launch.

**`chain.py` is stubbed, never run for real, in this file**: a real `--start` would launch a real run
for a missing document.

**No test invokes a real notifier.** The `run` fixture clears `KENSAIAPP_NOTIFIER` on every call.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent / "launcher.sh"

PRODUCT_SPINE = "PRD,Agari,SRS,UXD,DESIGN,CONTENT,SDD,FDR,ADR,NFDR"

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
    `core/` — every `<CORE>`-derived value the launcher hands the engine resolves there, since
    the launcher enters that pin before anything else reads `CORE_DIR` (Task 20)."""
    chain_stub = tmp_path / "chain_stub.py"
    chain_stub.write_text(CHAIN_STUB)
    chain_stub.chmod(0o755)

    argv_log = tmp_path / "chain_argv.log"

    env = dict(os.environ)
    env.pop("KENSAIAPP_NOTIFIER", None)
    for name in ("ENGINE_STUB_LINE", "ENGINE_STUB_EXIT"):
        env.pop(name, None)
    env["LAUNCH_CHAIN_PRODUCT_SCRIPT"] = str(chain_stub)
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
    _run.pin_root = _session_pin.root
    _run.chain_script = chain_stub
    _run.project = _project
    _run.chain_argv = _chain_argv
    _run.notifier = _notifier
    return _run


# --- the pin (Task 20): the launcher enters it before the engine is resolved -------------------


def test_dry_run_prints_the_pin_line(run):
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert re.search(r"^Pin: .+\(inherited\)$", result.stdout, re.MULTILINE)


def test_the_engine_is_started_from_the_pin(run):
    run.project("example-product")

    run("example-product")

    argv = run.chain_argv()
    assert argv[argv.index("--core-dir") + 1] == str(run.core_dir)


# --- the spine: what this launcher exists to vary ------------------------------------------


def test_the_product_spine_reaches_the_engine(run):
    run.project("example-product")

    result = run("example-product")

    assert result.returncode == 0
    argv = run.chain_argv()
    assert argv[argv.index("--spine") + 1] == PRODUCT_SPINE


def test_the_spine_is_every_document_the_engine_registers_upstream_first():
    """Both tiers, so a companion on either is swept — and in the order the documents read each
    other in."""
    chain = _engine()

    assert set(PRODUCT_SPINE.split(",")) == set(chain.DOCUMENT_REGISTRY)
    ranks = [chain.canonical_rank(chain.document(name)) for name in PRODUCT_SPINE.split(",")]
    assert ranks == sorted(ranks)


def test_the_spine_literal_is_committed_in_the_script_not_composed():
    """The behavioural half cannot tell a literal from a value composed to look like one —
    only reading the committed text can. A change to the spine is therefore a test change."""
    assert f'"{PRODUCT_SPINE}"' in _SCRIPT.read_text()


def test_the_spine_is_not_read_from_an_argument_or_the_environment(run):
    run.project("example-product")
    run.env["PRODUCT_SPINE"] = "something else entirely"
    run.env["KENSAIAPP_CHAIN_SPINE"] = "something else entirely"

    run("example-product")

    argv = run.chain_argv()
    assert argv[argv.index("--spine") + 1] == PRODUCT_SPINE


def _engine():
    import sys
    sys.path.insert(0, str(_SCRIPT.parent.parent.parent / "tools"))
    import chain
    return chain


def test_every_spine_document_is_one_the_engine_knows(run):
    assert _engine().parse_spine(PRODUCT_SPINE)


# --- the skills the walk starts ---------------------------------------------------------------


def test_every_skill_the_walk_starts_declares_a_launch_taking_the_project():
    """The walk hands each skill `<project>` and nothing else, so each one's `launcher.md` must
    exist and take exactly that — read off this repository's real declarations."""
    chain = _engine()
    repo = _SCRIPT.parent.parent.parent.parent
    for name in PRODUCT_SPINE.split(","):
        spec = chain.document(name)
        resolved = subprocess.run(
            ["python3", str(repo / "core" / "tools" / "skill_path.py"), spec.skill,
             "--root", str(repo)], capture_output=True, text=True)
        assert resolved.returncode == 0, (spec.skill, resolved.stderr)
        declaration = (Path(resolved.stdout.strip()) / "launcher.md").read_text()
        assert re.search(r"^\*\*Arguments:\*\* <project>\s*$", declaration, re.MULTILINE), spec.skill


# --- the-chains-stop-announces-itself, leg 6 — the launcher names its own walk -------------
#
# Mirrors the spine's own assertions above: the flag reaches the engine as argv (never merely
# stdout), the literal is committed in the script text, and it cannot be composed from an
# argument or the environment.


CHAIN_NAME = "product"


def test_the_chain_name_reaches_the_engine(run):
    run.project("example-product")

    result = run("example-product")

    assert result.returncode == 0
    argv = run.chain_argv()
    assert argv[argv.index("--chain-name") + 1] == CHAIN_NAME


def test_the_chain_name_literal_is_committed_in_the_script_not_composed():
    assert f'"{CHAIN_NAME}"' in _SCRIPT.read_text()


def test_the_chain_name_is_not_read_from_an_argument_or_the_environment(run):
    run.project("example-product")
    run.env["CHAIN_NAME"] = "something else entirely"
    run.env["KENSAIAPP_CHAIN_NAME"] = "something else entirely"

    run("example-product")

    argv = run.chain_argv()
    assert argv[argv.index("--chain-name") + 1] == CHAIN_NAME


# --- the guards -----------------------------------------------------------------------------


def test_no_project_arg_dies_with_usage(run):
    result = run()

    assert result.returncode != 0
    assert "usage:" in result.stderr
    assert run.chain_argv() == []


def test_unknown_project_dies_before_launching(run):
    result = run("nope")

    assert result.returncode != 0
    assert "no project card" in result.stderr
    assert run.chain_argv() == []


def test_project_card_without_product_path_dies(run):
    run.project("example-product", card="# example-product\n\nno path here\n")

    result = run("example-product")

    assert result.returncode != 0
    assert "Product path" in result.stderr


def test_unknown_flag_is_refused_not_silently_ignored(run):
    run.project("example-product")

    result = run("example-product", "--wat")

    assert result.returncode != 0
    assert "unknown flag" in result.stderr
    assert run.chain_argv() == []


def test_an_extra_positional_argument_is_refused(run):
    run.project("example-product")

    result = run("example-product", "and-something-else")

    assert result.returncode != 0
    assert "unexpected argument" in result.stderr


# --- the product path -----------------------------------------------------------------------


def test_relative_product_path_resolves_under_the_instance_root(run):
    run.project("example-product", product_path="products/thing")

    result = run("example-product")

    assert f"product path={run.root}/products/thing" in result.stdout


def test_absolute_product_path_is_used_verbatim(run):
    run.project("example-product", product_path="/somewhere/else")

    result = run("example-product")

    assert "product path=/somewhere/else" in result.stdout


def test_tilde_product_path_expands_to_home(run):
    run.project("example-product", product_path="~/products/thing")

    result = run("example-product")

    assert f"product path={run.home}/products/thing" in result.stdout


def test_trailing_comment_is_stripped_from_the_product_path(run):
    run.project("example-product", card="# example-product\n\n**Product path:** products/thing <!-- a note -->\n")

    result = run("example-product")

    assert f"product path={run.root}/products/thing" in result.stdout


# --- the engine invocation --------------------------------------------------------------------


def test_hands_the_walk_to_chain_py_start(run):
    run.project("example-product")

    run("example-product")

    argv = run.chain_argv()
    assert argv[0] == "--start"


def test_start_is_given_every_argument_it_requires(run):
    run.project("example-product")

    run("example-product")

    argv = run.chain_argv()
    for flag in ("--instance-root", "--product-path", "--project", "--core-dir",
                 "--shim-path", "--spine"):
        assert flag in argv, flag


def test_the_state_and_shim_paths_land_under_system_logs(run):
    run.project("example-product")

    run("example-product")

    argv = run.chain_argv()
    assert argv[1] == f"{run.root}/system/logs/chain-example-product-state.json"
    assert argv[argv.index("--shim-path") + 1] == f"{run.root}/system/logs/chain-example-product.sh"


def test_an_unset_notifier_is_skipped_never_an_error(run):
    run.project("example-product")

    result = run("example-product")

    assert result.returncode == 0
    assert "--notifier" not in run.chain_argv()


def test_kensaiapp_notifier_is_resolved_here_and_passed_as_a_parameter(run, tmp_path):
    spy = tmp_path / "notifier.sh"
    spy.write_text(NOTIFIER_STUB)
    spy.chmod(0o755)
    run.notifier(spy)
    run.project("example-product")

    run("example-product")

    argv = run.chain_argv()
    assert argv[argv.index("--notifier") + 1] == str(spy)


def test_no_notifier_is_ever_invoked_directly_by_this_suite(run, tmp_path):
    """The launcher passes the notifier down; it never sends anything itself."""
    log = tmp_path / "notifier_argv.log"
    spy = tmp_path / "notifier.sh"
    spy.write_text(NOTIFIER_STUB)
    spy.chmod(0o755)
    run.env["NOTIFIER_ARGV_LOG"] = str(log)
    run.notifier(spy)
    run.project("example-product")

    run("example-product")

    assert not log.exists()


# --- --dry-run and --keep-awake ---------------------------------------------------------------


def test_dry_run_prints_the_resolved_project_product_path_and_spine(run):
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert "project=example-product" in result.stdout
    assert "product path=" in result.stdout
    assert f"spine={PRODUCT_SPINE}" in result.stdout


def test_dry_run_prints_would_run_and_starts_nothing(run):
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert "DRY RUN" in result.stdout
    assert run.chain_argv() == []


def test_dry_run_prints_the_exact_command_the_real_run_invokes(run):
    run.project("example-product")
    dry = run("example-product", "--dry-run")

    run("example-product")

    for token in run.chain_argv():
        assert token in dry.stdout, token


def test_keep_awake_is_passed_to_the_engine(run):
    run.project("example-product")

    run("example-product", "--keep-awake")

    assert "--keep-awake" in run.chain_argv()


def _forced(run):
    argv = run.chain_argv()
    return argv[argv.index("--provider") + 1] if "--provider" in argv else None


@pytest.mark.parametrize("provider", ["codex", "gemini", "claude"])
def test_the_provider_flag_is_handed_to_the_engine_as_the_force(run, provider):
    run.project("example-product")

    result = run("example-product", "--provider", provider)

    assert result.returncode == 0, result.stderr
    assert _forced(run) == provider
    assert "chain-product: provider=" + provider + " (forced on every document)" in result.stdout


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
    """Each document then runs on its own provider: the entry the instance's `.providers.toml`
    holds."""
    run.project("example-product")
    run.env.pop("KENSAIAPP_AGENT_PROVIDER", None)

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert _forced(run) is None
    assert "chain-product: provider=each document's own" in result.stdout


def test_unknown_provider_is_refused_before_the_engine(run):
    run.project("example-product")

    result = run("example-product", "--provider", "other")

    assert result.returncode != 0
    assert "provider must be claude, codex, gemini, hf or ollama (got 'other')" in result.stderr
    assert run.chain_argv() == []


def test_keep_awake_is_absent_unless_asked_for(run):
    run.project("example-product")

    run("example-product")

    assert "--keep-awake" not in run.chain_argv()


def test_keep_awake_is_accepted_in_either_order_with_dry_run(run):
    run.project("example-product")

    for args in (("example-product", "--dry-run", "--keep-awake"),
                 ("example-product", "--keep-awake", "--dry-run")):
        result = run(*args)
        assert result.returncode == 0
        assert "--keep-awake" in result.stdout


def test_this_launcher_holds_no_caffeinate_of_its_own(run):
    """The mechanism is `core/tools/detach_watcher.sh`'s, which every launcher this chain runs
    already sources — this script exits seconds after the first producer is launched, so a
    caffeinate held here would cover none of the walk."""
    code = "\n".join(line for line in _SCRIPT.read_text().splitlines()
                     if not line.lstrip().startswith("#"))

    assert "caffeinate" not in code


# --- --on-end: a command the walk runs when it ends ------------------------------------------
#
# `build-idea` runs a refine report's sweep row through this launcher and needs to be told when the
# sweep is over. The launcher only carries the command to the engine; what runs it, and when, is
# `chain.py`'s.


ON_END = "/hooks/next-queue.sh --chain-ended"


def test_on_end_reaches_the_engine_with_its_value(run):
    run.project("example-product")

    result = run("example-product", "--on-end", ON_END)

    assert result.returncode == 0
    argv = run.chain_argv()
    assert argv[argv.index("--on-end") + 1] == ON_END


def test_without_on_end_the_engine_argv_is_unchanged(run):
    run.project("example-product")

    run("example-product")

    assert run.chain_argv() == [
        "--start", f"{run.root}/system/logs/chain-example-product-state.json",
        "--instance-root", str(run.root), "--product-path", f"{run.root}/products/thing",
        "--project", "example-product", "--core-dir", str(run.core_dir),
        "--shim-path", f"{run.root}/system/logs/chain-example-product.sh",
        "--spine", PRODUCT_SPINE, "--chain-name", CHAIN_NAME]


def test_on_end_with_no_value_dies(run):
    run.project("example-product")

    result = run("example-product", "--on-end")

    assert result.returncode != 0
    assert "--on-end needs a command" in result.stderr
    assert "unknown flag" not in result.stderr
    assert run.chain_argv() == []


def test_on_end_with_an_empty_value_dies(run):
    run.project("example-product")

    result = run("example-product", "--on-end", "")

    assert result.returncode != 0
    assert "--on-end needs a command" in result.stderr
    assert run.chain_argv() == []


@pytest.mark.parametrize("args", [
    ("--on-end", ON_END, "--keep-awake"),
    ("--keep-awake", "--on-end", ON_END),
    ("--dry-run", "--on-end", ON_END),
])
def test_on_end_is_accepted_anywhere_after_the_project(run, args):
    run.project("example-product")

    result = run("example-product", *args)

    assert result.returncode == 0
    if "--dry-run" not in args:
        argv = run.chain_argv()
        assert argv[argv.index("--on-end") + 1] == ON_END


def test_the_dry_run_prints_the_on_end_command(run):
    run.project("example-product")

    result = run("example-product", "--dry-run", "--on-end", ON_END)

    assert "--on-end" in result.stdout
    assert "next-queue.sh" in result.stdout
    assert run.chain_argv() == []


def test_the_usage_line_and_the_usage_block_name_the_flag(run):
    result = run()

    assert "--on-end" in result.stderr
    header = _SCRIPT.read_text().split("set -euo pipefail", 1)[0]
    assert "--on-end" in header.split("# USAGE", 1)[1]


# --- the file itself ---------------------------------------------------------------------------


def test_launcher_is_executable():
    assert os.access(_SCRIPT, os.X_OK)


def test_the_launcher_names_no_literal_core_path():
    """Machinery points at core through `<CORE>`, never a literal `core/` — a satellite binds
    its own, and a literal would name this host's."""
    code = "\n".join(line for line in _SCRIPT.read_text().splitlines()
                     if not line.lstrip().startswith("#"))

    assert "~/.claude/" not in code
    assert not re.search(r"(?<![\w/.])core/", code)


# --- --stop: the owner's brake, handed to the engine's --stop (CP-373) -------------------------


def test_stop_reaches_the_engine_stop_with_the_state_path(run):
    run.project("example-product")

    result = run("example-product", "--stop")

    assert result.returncode == 0, result.stderr
    assert run.chain_argv() == ["--stop", f"{run.root}/system/logs/chain-example-product-state.json"]


def test_stop_passes_the_notifier_it_resolved(run, tmp_path):
    run.project("example-product")
    run.notifier(tmp_path / "notify.sh")

    run("example-product", "--stop")

    argv = run.chain_argv()
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
        ("--on-end", "true"),
    ],
    ids=[
        "--dry-run",
        "--keep-awake",
        "--provider claude",
        "--on-end true",
    ],
)
def test_stop_with_another_flag_dies_and_runs_no_engine(run, flag):
    run.project("example-product")

    after = run("example-product", "--stop", *flag)
    before = run("example-product", *flag, "--stop")

    for result in (after, before):
        assert result.returncode == 1
        assert "<project> --stop" in result.stderr
    assert run.chain_argv() == []


def test_the_usage_names_the_stop():
    header = _SCRIPT.read_text().split("set -euo pipefail", 1)[0]

    assert "<project> --stop" in header.split("# USAGE", 1)[1]


# CP-425: the usage message, the header's first USAGE line and the missing-value refusal name
# `hf`, in change_text.md's words.
_HF_USAGE = (
    "chain-product: usage: <CORE>/launchers/chain-product/launcher.sh <project>"
    " [--provider claude|codex|gemini|hf|ollama] [--on-end <command>] [--dry-run]"
    " [--keep-awake] | <project> --stop"
)
_HF_HEADER_USAGE = (
    "<CORE>/launchers/chain-product/launcher.sh"
    " <project> [--provider claude|codex|gemini|hf|ollama]"
)


def test_the_usage_line_names_hf(run):
    result = run()

    assert result.returncode != 0
    assert _HF_USAGE in result.stderr
    assert run.chain_argv() == []


def test_the_header_usage_names_hf():
    header = {line.lstrip("#").strip() for line in _SCRIPT.read_text().splitlines()
              if line.startswith("#")}

    assert _HF_HEADER_USAGE in header


def test_a_provider_flag_with_no_value_is_refused_naming_the_five(run):
    run.project("example-product")

    result = run("example-product", "--provider")

    assert result.returncode != 0
    assert "chain-product: --provider needs claude, codex, gemini, hf or ollama" in result.stderr
    assert run.chain_argv() == []
