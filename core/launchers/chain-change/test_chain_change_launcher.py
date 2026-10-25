"""Contract tests for `chain-change/launcher.sh`.

**Named `test_chain_change_launcher.py`, not `test_chain_change.py`.** The identity rule
(`kensaiapp_structure.md` § Owner-run launcher folder) would give this suite the second name; the
`_launcher` suffix is its sibling's for the same reason — pytest imports test modules by basename,
and this launcher shares an engine, and so nearly a name, with `chain-development`.

**The engine is stubbed, never run for real, except where a test says otherwise.** A real `--start`
would open a station and launch a real `claude --bg` run. What the engine does with its argv is
`core/tools/test_chain_development.py`'s to pin; this suite pins the argv this launcher builds.

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
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent / "launcher.sh"
_EXAMPLE = Path(__file__).resolve().parents[3] / ".providers.toml.example"
_CORE = _SCRIPT.parent.parent.parent

ENGINE_STUB = """#!/usr/bin/env python3
import json, os, sys
if "--describe" in sys.argv:
    with open(os.environ["DESCRIBE_ARGV_LOG"], "w") as fh:
        fh.write("\\n".join(sys.argv[1:]))
    refusal = os.environ.get("DESCRIBE_REFUSE")
    if refusal:
        print("chain_development: " + refusal, file=sys.stderr)
        sys.exit(3)
    sys.stdout.write(os.environ.get("DESCRIBE_STDOUT", "key=2026-09-15_stub\\nentry=design\\n"))
    sys.exit(0)
with open(os.environ["ENGINE_ARGV_LOG"], "w") as fh:
    fh.write("\\n".join(sys.argv[1:]))
if os.environ.get("ENGINE_HISTORY_LOG"):
    with open(os.environ["ENGINE_HISTORY_LOG"], "a") as fh:
        fh.write(json.dumps(sys.argv[1:]) + "\\n")
print(os.environ.get("ENGINE_STUB_LINE", "engine-stub: started"))
sys.exit(int(os.environ.get("ENGINE_STUB_EXIT", "0")))
"""

# The definition engine stub stands in for `chain.py` behind `chain-product` and `chain-agari`,
# which run for real. It records its argv, and on request it refuses (non-zero, reason on stderr)
# or fires its `--on-end` value the way `run_end_hook` does: `shlex.split` plus the end, cwd the
# root. The hook's own return code and output are written to a log the tests read.
DEFINITION_STUB = """#!/usr/bin/env python3
import json, os, shlex, subprocess, sys
with open("__CALLS__", "a") as fh:
    fh.write(json.dumps(sys.argv[1:]) + "\\n")
if int(os.environ.get("DEF_STUB_EXIT", "0")):
    print(os.environ.get("DEF_STUB_REFUSAL", "refused"), file=sys.stderr)
    sys.exit(int(os.environ["DEF_STUB_EXIT"]))
for end in filter(None, os.environ.get("DEF_STUB_FIRE", "").split(",")):
    hook = sys.argv[1:][sys.argv[1:].index("--on-end") + 1]
    done = subprocess.run(shlex.split(hook) + [end], cwd=os.getcwd(), capture_output=True,
                          text=True)
    with open("__HOOKS__", "a") as fh:
        fh.write(json.dumps([done.returncode, done.stdout, done.stderr]) + "\\n")
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

    history_log = tmp_path / "engine_history.log"
    hooks_log = tmp_path / "definition_hooks.log"
    definition_logs = {}
    env = dict(os.environ)
    env.pop("KENSAIAPP_NOTIFIER", None)
    for name in ("ENGINE_STUB_LINE", "ENGINE_STUB_EXIT"):
        env.pop(name, None)
    for name in ("DESCRIBE_REFUSE", "DESCRIBE_STDOUT"):
        env.pop(name, None)
    for name in ("DEF_STUB_EXIT", "DEF_STUB_REFUSAL", "DEF_STUB_FIRE", "KENSAIAPP_DEFINITION"):
        env.pop(name, None)
    env["LAUNCH_CHAIN_CHANGE_SCRIPT"] = str(engine_stub)
    env["ENGINE_ARGV_LOG"] = str(argv_log)
    env["ENGINE_HISTORY_LOG"] = str(history_log)
    env["DESCRIBE_ARGV_LOG"] = str(describe_log)
    # One definition-engine stub per sibling, each with its own call log: the siblings run for real
    # and reach their stub through the override each already has for its engine.
    for kind, variable in (("product", "LAUNCH_CHAIN_PRODUCT_SCRIPT"),
                           ("agari", "LAUNCH_CHAIN_AGARI_SCRIPT")):
        definition_logs[kind] = tmp_path / f"definition_{kind}_calls.log"
        stub_path = tmp_path / f"definition_{kind}_stub.py"
        stub_path.write_text(DEFINITION_STUB.replace("__CALLS__", str(definition_logs[kind]))
                             .replace("__HOOKS__", str(hooks_log)))
        stub_path.chmod(0o755)
        env[variable] = str(stub_path)
    env["HOME"] = str(tmp_path / "home")
    (tmp_path / "home").mkdir()

    def _run(*cli_args):
        return subprocess.run([str(_SCRIPT), *cli_args], cwd=str(tmp_path),
                              capture_output=True, text=True, env=env)

    def _project(name, product_path="products/thing", card=None, definition="none"):
        project_dir = tmp_path / "system" / "projects" / name
        project_dir.mkdir(parents=True)
        if card is None:
            card = f"# {name}\n\n**Product path:** {product_path}\n"
            if definition is not None:
                card += f"**Definition:** {definition}\n"
        (project_dir / "project.md").write_text(card)

    def _card(name):
        return tmp_path / "system" / "projects" / name / "project.md"

    def _rewrite_card(name, old, new):
        card = _card(name)
        text = card.read_text()
        assert old in text
        card.write_text(text.replace(old, new))

    def _engine_argv():
        return argv_log.read_text().splitlines() if argv_log.exists() else []

    def _describe_argv():
        return describe_log.read_text().splitlines() if describe_log.exists() else []

    def _value(flag):
        argv = _engine_argv()
        return argv[argv.index(flag) + 1]

    def _json_lines(path):
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def _change_calls():
        return _json_lines(history_log)

    def _change_starts():
        return [call for call in _change_calls() if call[0] == "--start"]

    def _definition_calls(kind):
        return _json_lines(definition_logs[kind])

    def _hook_results():
        return _json_lines(hooks_log)

    def _pending(project=None):
        logs = tmp_path / "system" / "logs"
        pattern = f"chain-change-{project or '*'}-pending.*"
        return sorted(path.name for path in logs.glob(pattern)) if logs.exists() else []

    def _hook_of(call):
        return shlex.split(call[call.index("--on-end") + 1])

    def _fire(call, end, env=None):
        """Run a definition walk's recorded end hook the way the engine does."""
        return subprocess.run(_hook_of(call) + [end], cwd=str(tmp_path), capture_output=True,
                              text=True, env=env or dict(_run.env))

    def _forget_engine_calls():
        history_log.unlink(missing_ok=True)
        argv_log.unlink(missing_ok=True)

    _run.root = tmp_path
    _run.env = env
    _run.core_dir = _session_pin.core
    _run.pin_root = _session_pin.root
    _run.project = _project
    _run.engine_argv = _engine_argv
    _run.describe_argv = _describe_argv
    _run.value = _value
    _run.card = _card
    _run.rewrite_card = _rewrite_card
    _run.change_calls = _change_calls
    _run.change_starts = _change_starts
    _run.definition_calls = _definition_calls
    _run.hook_results = _hook_results
    _run.pending = _pending
    _run.hook_of = _hook_of
    _run.fire = _fire
    _run.forget_engine_calls = _forget_engine_calls
    return _run


# --- the engine invocation --------------------------------------------------------------------


def test_hands_the_walk_to_the_engine_start_with_its_own_state_file(run):
    run.project("example-product")

    result = run("example-product")

    assert result.returncode == 0
    argv = run.engine_argv()
    assert argv[0] == "--start"
    assert argv[1] == f"{run.root}/system/logs/chain-change-example-product-state.json"


def test_the_state_file_is_neither_siblings(run):
    """One state file IS one walk. A change walk that shared either sibling's file could not run
    beside it, and the whole point of a separate name is that it can."""
    run.project("example-product")

    run("example-product")

    assert run.engine_argv()[1] not in (
        f"{run.root}/system/logs/chain-development-example-product-state.json",
        f"{run.root}/system/logs/chain-example-product-state.json",
    )


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


def test_the_engine_is_told_which_table_and_given_no_spine(run):
    """The one thing this launcher says that its sibling does not. It names a table the engine
    holds; it does not hand one in, which is why there is still no `--spine` here."""
    run.project("example-product")

    run("example-product")

    assert run.value("--steps") == "change"
    assert "--spine" not in run.engine_argv()


def test_the_engine_defaults_to_the_shared_engine_under_core(run):
    """With the override gone the dry run asks the REAL engine, so the default path is proven by
    a call that answers, not by a string the launcher printed. A project with nothing open is the
    state a change walk is built to start in."""
    run.project("example-product")
    # The dry run asks the real engine, which reads the instance's own provider file.
    (run.root / ".providers.toml").write_text(
        _EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    (run.root / "system" / "projects" / "example-product" / "journey" / "shukuba").mkdir(parents=True)
    (run.root / "system" / "projects" / "example-product" / "journey" / "tobiishi").mkdir(parents=True)
    run.env.pop("LAUNCH_CHAIN_CHANGE_SCRIPT")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "entry step=station" in result.stdout
    assert f"{run.core_dir}/tools/chain_development.py" in result.stdout
    assert not (run.root / "system" / "logs").exists()


# --- where the walk's end goes ------------------------------------------------------------------
#
# The walk ends by running a command the launcher hands the engine, which appends the end
# (`sealed` or `halted`). That command is `build-idea`, which starts the next queue only on `sealed`
# — the loop the refine report's After column and the queue engine close.


def test_the_walk_is_given_an_on_end_naming_build_idea_for_the_project(run):
    run.project("example-product")

    run("example-product")

    assert shlex.split(run.value("--on-end")) == [
        f"{run.core_dir}/launchers/build-idea/launcher.sh", "example-product", "--chain-ended"]


def test_chain_change_end_hook_names_the_pins_build_idea(run):
    """Beyond `test_the_walk_is_given_an_on_end_naming_build_idea_for_the_project` — this is the
    same fact stated for Task 20's own reason: `--on-end` is built AFTER the launcher enters the
    pin, so it can only ever name the pin's own `build-idea/launcher.sh`, never the live host's."""
    run.project("example-product")

    run("example-product")

    on_end = shlex.split(run.value("--on-end"))
    assert on_end[0] == str(run.core_dir / "launchers" / "build-idea" / "launcher.sh")
    assert Path(on_end[0]).is_relative_to(run.pin_root)


def test_the_on_end_path_survives_a_core_path_with_spaces(run, tmp_path):
    """The hook is one string the engine splits the way a shell does, so a `<CORE>` whose path
    holds a space must arrive as one word — not as two, the second a command that does not exist."""
    run.project("example-product")
    spaced_host = tmp_path / "a core with spaces"
    spaced_core = spaced_host / "core"
    spaced = spaced_core / "launchers" / "chain-change"
    spaced.mkdir(parents=True)
    shutil.copy(_SCRIPT, spaced / "launcher.sh")
    # `pin_enter` (Task 20) sources `<CORE_DIR>/tools/pin_run.sh` before anything else, so this
    # synthetic core needs a `tools/` to source it from — nested under a literal `core/` segment,
    # since that is what a pin's own layout (and `pin_run.sh`'s own self-pin check) assumes, the
    # space living in the ancestor `spaced_host` segment instead. `<spaced_host>/pin.json` marks
    # the tree already its own pin, so `pin_enter` neither re-execs nor makes a real one (which
    # would walk the symlink below into the whole real `core/tools/`, copied file by file).
    (spaced_core / "tools").symlink_to(_CORE / "tools")
    (spaced_host / "pin.json").write_text(json.dumps({
        "id": "spaced-self-pin",
        "source_host_root": str(spaced_host),
        "created": "1970-01-01T00:00:00+00:00",
    }) + "\n")

    result = subprocess.run([str(spaced / "launcher.sh"), "example-product"], cwd=str(tmp_path),
                            capture_output=True, text=True, env=run.env)

    assert result.returncode == 0, result.stderr
    assert shlex.split(run.value("--on-end")) == [
        f"{tmp_path}/a core with spaces/core/launchers/build-idea/launcher.sh", "example-product",
        "--chain-ended"]


def test_the_on_end_is_given_beside_a_notifier_and_keep_awake_and_stays_one_argument(run):
    run.project("example-product")
    run.env["KENSAIAPP_NOTIFIER"] = "/bin/echo"

    run("example-product", "--keep-awake")

    argv = run.engine_argv()
    assert argv.count("--on-end") == 1
    assert "--notifier" in argv and "--keep-awake" in argv
    assert argv[argv.index("--on-end") + 1].endswith("--chain-ended")


def test_a_walk_with_the_owners_mac_ask_hands_it_to_build_idea(run):
    """The ask reaches the next change's walk through the queue the end starts. The end is
    appended after `--chain-ended`, so the ask sits before it."""
    run.project("example-product")

    run("example-product", "--gate-owners-mac")

    assert shlex.split(run.value("--on-end")) == [
        f"{run.core_dir}/launchers/build-idea/launcher.sh", "example-product",
        "--gate-owners-mac", "--chain-ended"]


@pytest.mark.parametrize("definition", ["full", "prd-agari"])
def test_a_definition_first_walk_with_the_ask_hands_it_to_build_idea(run, definition):
    """The change walk the definition walk's end starts is the `none` launch's, its build-idea hook
    and its ask included, though the hook's own invocation takes no ask flag."""
    run.env["KENSAIAPP_NOTIFIER"] = "/bin/echo"
    run.project("example-product")
    baseline, launched = _start_and_baseline(run, definition, "--gate-owners-mac")
    assert launched.returncode == 0, launched.stderr

    fired = run.fire(run.definition_calls(_SIBLING_OF[definition])[0], "settled")

    assert fired.returncode == 0, fired.stderr
    assert run.change_starts() == [baseline]
    assert "--gate-owners-mac" in shlex.split(_flag_value(baseline, "--on-end"))


def test_the_dry_run_prints_the_on_end(run):
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert "--on-end" in result.stdout
    assert "build-idea/launcher.sh" in result.stdout and "--chain-ended" in result.stdout
    assert run.engine_argv() == []


def test_the_header_says_where_the_loop_closes():
    header = _SCRIPT.read_text().split("set -euo pipefail", 1)[0]

    assert "WHERE THE LOOP CLOSES" in header
    assert "build-idea" in header.split("WHERE THE LOOP CLOSES", 1)[1]


# --- the dry run ------------------------------------------------------------------------------


def test_the_dry_run_asks_the_engine_before_it_prints_and_starts_nothing(run):
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0
    assert run.describe_argv()[0] == "--describe"
    assert run.engine_argv() == []
    assert "DRY RUN — would run:" in result.stdout
    # `printf '  %q'` puts two spaces before every token, so the pair is read as tokens rather
    # than as a single-space join.
    printed = result.stdout.split("DRY RUN — would run:")[1].split()
    assert printed[printed.index("--steps") + 1] == "change"


@pytest.mark.parametrize("card_path, resolved", [
    ("products/thing", "{root}/products/thing"),
    ("/somewhere/else", "/somewhere/else"),
    ("~/products/thing", "{root}/home/products/thing"),
])
def test_the_dry_run_describe_argv_carries_the_resolved_product_path(run, card_path, resolved):
    """Row C1: `--describe` reads the per-task commits where the start will, so it is given the
    product path the start's argv carries — and the rest of its argv is what it was."""
    run.project("example-product", product_path=card_path)
    expected = resolved.format(root=run.root)

    run("example-product")
    started = run.value("--product-path")
    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert started == expected
    assert run.describe_argv() == [
        "--describe", f"{run.root}/system/logs/chain-change-example-product-state.json",
        "--instance-root", str(run.root), "--product-path", expected,
        "--project", "example-product", "--steps", "change"]


def test_the_dry_run_names_the_change_and_the_entry_step(run):
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert "chain-change: change=2026-09-15_stub" in result.stdout
    assert "chain-change: entry step=design" in result.stdout


def test_a_walk_with_no_change_yet_still_dry_runs_and_says_so(run):
    """The difference from the sibling. Before `tobiishi-open` there IS no key, so a dry run that
    demanded one would refuse every walk this launcher exists to start."""
    run.project("example-product")
    run.env["DESCRIBE_STDOUT"] = "key=\nentry=station\n"

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "chain-change: change=(none yet)" in result.stdout
    assert "chain-change: entry step=station" in result.stdout
    assert "DRY RUN — would run:" in result.stdout


def test_a_dry_run_naming_no_entry_step_is_not_an_answer(run):
    """An exit 0 that names no step means the engine did not answer, and a DRY RUN block after it
    would report a walk nothing checked."""
    run.project("example-product")
    run.env["DESCRIBE_STDOUT"] = "key=\n"

    result = run("example-product", "--dry-run")

    assert result.returncode != 0
    assert "DRY RUN" not in result.stdout


def test_a_refused_describe_fails_the_dry_run_with_the_engines_reason(run):
    run.project("example-product")
    run.env["DESCRIBE_REFUSE"] = "more than one active change under ..."

    result = run("example-product", "--dry-run")

    assert result.returncode != 0
    assert "more than one active change" in result.stderr
    assert "DRY RUN" not in result.stdout


# --- the guards -------------------------------------------------------------------------------


def test_no_project_arg_dies_with_usage(run):
    result = run()

    assert result.returncode != 0
    assert "usage:" in result.stderr
    assert run.engine_argv() == []


def test_an_unknown_project_dies_naming_the_card_it_looked_for(run):
    result = run("ghost")

    assert result.returncode != 0
    assert "system/projects/ghost/project.md" in result.stderr
    assert run.engine_argv() == []


def test_a_card_with_no_product_path_dies_rather_than_guessing(run):
    run.project("example-product", card="# example-product\n\nno path here\n")

    result = run("example-product")

    assert result.returncode != 0
    assert "Product path" in result.stderr
    assert run.engine_argv() == []


def test_an_unknown_flag_dies(run):
    run.project("example-product")

    result = run("example-product", "--steps")

    assert result.returncode != 0
    assert "unknown flag" in result.stderr
    assert run.engine_argv() == []


def test_a_second_positional_dies_saying_the_change_is_discovered(run):
    """Nothing is named to this launcher but the project: the station and the change are both
    read off the disk, which is what makes a relaunch resume rather than restart."""
    run.project("example-product")

    result = run("example-product", "2026-09-17_something")

    assert result.returncode != 0
    assert "unexpected argument" in result.stderr
    assert run.engine_argv() == []


# --- what is passed down ------------------------------------------------------------------------


def test_an_absolute_product_path_is_passed_through_untouched(run):
    run.project("example-product", product_path="/somewhere/else")

    run("example-product")

    assert run.value("--product-path") == "/somewhere/else"


def test_a_tilde_product_path_resolves_against_home(run):
    run.project("example-product", product_path="~/products/thing")

    run("example-product")

    assert run.value("--product-path") == f"{run.root}/home/products/thing"


def test_the_notifier_is_resolved_here_and_passed_as_a_parameter(run):
    run.project("example-product")
    run.env["KENSAIAPP_NOTIFIER"] = "/bin/echo"

    run("example-product")

    assert run.value("--notifier") == "/bin/echo"


def test_an_unset_notifier_is_omitted_rather_than_passed_empty(run):
    """Skipped, never an error — the engine's own rule for an absent channel."""
    run.project("example-product")

    run("example-product")

    assert "--notifier" not in run.engine_argv()


def test_keep_awake_is_passed_down_to_the_engine(run):
    run.project("example-product")

    run("example-product", "--keep-awake")

    assert "--keep-awake" in run.engine_argv()


def _forced(run):
    argv = run.engine_argv()
    return argv[argv.index("--provider") + 1] if "--provider" in argv else None


@pytest.mark.parametrize("provider", ["codex", "gemini", "claude"])
def test_the_provider_flag_is_handed_to_the_engine_as_the_force(run, provider):
    run.project("example-product")

    result = run("example-product", "--provider", provider)

    assert result.returncode == 0, result.stderr
    assert _forced(run) == provider
    assert "chain-change: provider=" + provider + " (forced on every step)" in result.stdout


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
    assert "chain-change: provider=each step's own" in result.stdout


def test_unknown_provider_is_refused_before_the_engine(run):
    run.project("example-product")

    result = run("example-product", "--provider", "other")

    assert result.returncode != 0
    assert "provider must be claude, codex, gemini, hf or ollama (got 'other')" in result.stderr
    assert run.engine_argv() == []


# --- the developer's context cap ------------------------------------------------------------------


def test_context_cap_is_passed_to_the_engine(run):
    run.project("example-product")

    result = run("example-product", "--context-cap", "80000")

    assert result.returncode == 0, result.stderr
    assert run.value("--context-cap") == "80000"


def test_context_cap_may_sit_beside_the_other_flags_in_either_order(run):
    run.project("example-product")

    run("example-product", "--keep-awake", "--context-cap", "80000")

    argv = run.engine_argv()
    assert argv[argv.index("--context-cap") + 1] == "80000"
    assert "--keep-awake" in argv


def test_no_context_cap_passes_none(run):
    """The engine's own default applies: nothing here restates it, so it cannot drift from it."""
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
def test_a_bad_context_cap_is_refused_before_the_engine(run, cli):
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


def test_the_header_and_usage_name_the_context_cap_as_the_developers_alone():
    header = _SCRIPT.read_text().split("set -euo pipefail", 1)[0]
    usage = header.split("# USAGE", 1)[1]

    synopsis = usage.split("(run from", 1)[0]
    assert "--context-cap" in header.split("# USAGE", 1)[0]
    assert "--context-cap <tokens>" in synopsis
    assert "developer's run only" in usage.split("--context-cap <tokens>", 2)[2]


# --- --stop: the owner's brake, handed to the engine's --stop (CP-373) -------------------------


def test_stop_reaches_the_engine_stop_with_the_state_path(run):
    run.project("example-product")

    result = run("example-product", "--stop")

    assert result.returncode == 0, result.stderr
    assert run.engine_argv() == ["--stop", f"{run.root}/system/logs/chain-change-example-product-state.json"]


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
        ("--context-cap", "1000"),
    ],
    ids=[
        "--dry-run",
        "--keep-awake",
        "--provider claude",
        "--context-cap 1000",
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
    "chain-change: usage: <CORE>/launchers/chain-change/launcher.sh <project>"
    " [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake]"
    " [--context-cap <tokens>] [--gate-owners-mac] | <project> --stop"
)
_HF_HEADER_USAGE = (
    "<CORE>/launchers/chain-change/launcher.sh"
    " <project> [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake]"
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
    assert "chain-change: --provider needs claude, codex, gemini, hf or ollama" in result.stderr
    assert run.engine_argv() == []


# --- the card's Definition line: what it is, and what runs before the change (CP-433 to CP-453) ---
#
# The sibling definition launchers (`chain-product`, `chain-agari`) run for real; only the engine
# behind each is a recording stub. The change engine is a stub too, so a "change started" is a line
# in its history and never a real walk.

_DEFINITION_LINES = {
    "full": "chain-change: definition=full — chain-product's walk runs first, then the change walk",
    "prd-agari": ("chain-change: definition=prd-agari — chain-agari's walk runs first, then the "
                  "change walk"),
    "none": "chain-change: definition=none — the change walk alone",
}
_SIBLING_OF = {"full": "product", "prd-agari": "agari"}
_PRODUCT_SPINE = "PRD,Agari,SRS,UXD,DESIGN,CONTENT,SDD,FDR,ADR,NFDR"
_NO_LINE = ("chain-change: no 'Definition:' line in {card} — add **Definition:** full, prd-agari "
            "or none")
_BAD_VALUE = ("chain-change: 'Definition:' in {card} reads '{value}' — it must be full, prd-agari "
              "or none")
_DUPLICATE = "chain-change: {card} carries {n} 'Definition:' lines — it must carry one"
_WHOLE_SPINE_ENDS = ("settled", "left_for_the_owner")
_STOP_NOTICE = ("chain-change: no change walk waiting on a definition walk will start now. This "
                "stop leaves the definition walk alone. chain-product's or chain-agari's own "
                "--stop ends it.")
_DEFINITION_REFUSED = ("chain-change: the definition walk did not start, so the change walk will "
                       "not start either")


def _card(*lines, product_path="products/thing"):
    return "\n".join(["# example-product", "", f"**Product path:** {product_path}", *lines, ""])


def _after_product_path(stdout):
    lines = stdout.splitlines()
    index = next(i for i, line in enumerate(lines)
                 if line.startswith("chain-change: product path="))
    return lines[index + 1]


def _flag_value(argv, flag):
    return argv[argv.index(flag) + 1] if flag in argv else None


def _start_and_baseline(run, definition, *cli_args):
    """The change walk a `none` launch with these options starts, and a `definition` launch of the
    same project and options (not yet ended): `(baseline_argv, launch_result)`."""
    assert run("example-product", *cli_args).returncode == 0
    baseline = run.change_starts()[-1]
    run.forget_engine_calls()
    run.rewrite_card("example-product", "**Definition:** none", f"**Definition:** {definition}")
    return baseline, run("example-product", *cli_args)


# --- none: the start is what it was, plus one line ------------------------------------------------


@pytest.mark.parametrize("extra", [(), ("--dry-run",)], ids=["start", "dry-run"])
def test_none_walk_keeps_the_change_invocation(run, extra):
    run.project("example-product")

    result = run("example-product", *extra)

    assert result.returncode == 0, result.stderr
    assert _after_product_path(result.stdout) == _DEFINITION_LINES["none"]
    assert result.stdout.count("definition=") == 1
    # Everything else the launcher printed is what it printed before this change, line by line.
    others = [line for line in result.stdout.splitlines() if line != _DEFINITION_LINES["none"]]
    assert re.fullmatch(r"Pin: .+ \(inherited\)", others[0])
    assert others[1] == "chain-change: project=example-product"
    assert others[2].startswith("chain-change: product path=")
    assert others[2].endswith("/products/thing")
    assert others[3] == "chain-change: provider=each step's own"
    if extra:
        assert others[4:7] == ["chain-change: change=2026-09-15_stub",
                               "chain-change: entry step=design", "DRY RUN \u2014 would run:"]
        assert len(others) == 8 and "--steps  change" in others[7]
    else:
        assert others[4:] == ["engine-stub: started"]
    assert run.definition_calls("product") == [] and run.definition_calls("agari") == []
    assert run.pending() == []
    if not extra:
        argv = run.engine_argv()
        assert argv[0] == "--start" and run.value("--steps") == "change"
        assert shlex.split(run.value("--on-end")) == [
            f"{run.core_dir}/launchers/build-idea/launcher.sh", "example-product", "--chain-ended"]


# --- what the reader refuses ----------------------------------------------------------------------


@pytest.mark.parametrize("extra", [(), ("--dry-run",)], ids=["start", "dry-run"])
def test_missing_definition_refuses_before_any_engine_call(run, extra):
    run.project("example-product", card=_card())
    card = run.card("example-product")

    result = run("example-product", *extra)

    assert result.returncode == 1
    assert result.stderr.strip().splitlines()[-1] == _NO_LINE.format(card=card)
    assert "DRY RUN" not in result.stdout
    assert run.engine_argv() == [] and run.describe_argv() == []
    assert run.definition_calls("product") == [] and run.definition_calls("agari") == []
    assert run.pending() == []


@pytest.mark.parametrize("line", [
    "Definition: full",
    "**definition:** full",
    "  **Definition:** full",
    "*Definition:* full",
], ids=["unbolded", "lowercase", "indented", "italic"])
def test_only_the_exact_definition_label_is_read(run, line):
    run.project("example-product", card=_card(line))

    result = run("example-product")

    assert result.returncode == 1
    assert result.stderr.strip().splitlines()[-1] == _NO_LINE.format(card=run.card("example-product"))
    assert run.engine_argv() == [] and run.definition_calls("product") == []


@pytest.mark.parametrize("line, value", [
    ("**Definition:**    none     ", "none"),
    ("**Definition:** none      <!-- full | prd-agari | none — a comment -->", "none"),
    ("**Definition:**\tprd-agari\t<!-- c -->", "prd-agari"),
    ("**Definition:** full<!-- c -->", "full"),
], ids=["trailing-blanks", "comment", "tabs", "tight-comment"])
def test_surrounding_whitespace_and_a_comment_are_stripped(run, line, value):
    run.project("example-product", card=_card(line))

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert _after_product_path(result.stdout) == _DEFINITION_LINES[value]


@pytest.mark.parametrize("type_line, definition", [
    ("**Type:** no-code", "full"),
    ("**Type:** software", "none"),
    ("**Type:** software", "prd-agari"),
    ("**Type:** no-code", "none"),
])
def test_the_value_controls_the_dispatch_whatever_the_type_says(run, type_line, definition):
    run.project("example-product", card=_card(type_line, f"**Definition:** {definition}"))

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert _after_product_path(result.stdout) == _DEFINITION_LINES[definition]


@pytest.mark.parametrize("raw, shown", [
    ("", ""),
    ("   ", ""),
    ("Full", "Full"),
    ("NONE", "NONE"),
    ("partial", "partial"),
    ("full prd-agari", "full prd-agari"),
    (" Full   <!-- c -->", "Full"),
    ("<!-- only a comment -->", ""),
])
def test_invalid_definition_is_refused(run, raw, shown):
    run.project("example-product", card=_card(f"**Definition:**{(' ' + raw) if raw else ''}"))

    for extra in ((), ("--dry-run",)):
        result = run("example-product", *extra)

        assert result.returncode == 1
        assert result.stderr.strip().splitlines()[-1] == _BAD_VALUE.format(
            card=run.card("example-product"), value=shown)
        assert run.engine_argv() == [] and run.describe_argv() == []
        assert run.definition_calls("product") == [] and run.definition_calls("agari") == []
        assert run.pending() == []


@pytest.mark.parametrize("lines", [
    ("**Definition:** none", "**Definition:** full"),
    ("**Definition:** none", "**Definition:** none"),
    ("**Definition:** full", "**Definition:** full", "**Definition:** full"),
], ids=["differ", "agree", "three"])
def test_duplicate_definition_is_refused(run, lines):
    run.project("example-product", card=_card(*lines))

    for extra in ((), ("--dry-run",)):
        result = run("example-product", *extra)

        assert result.returncode == 1
        assert result.stderr.strip().splitlines()[-1] == _DUPLICATE.format(
            card=run.card("example-product"), n=len(lines))
        assert run.engine_argv() == [] and run.definition_calls("product") == []
        assert run.pending() == []


def test_definition_cannot_be_overridden(run):
    run.project("example-product", card=_card())
    run.env["KENSAIAPP_DEFINITION"] = "none"

    flag = run("example-product", "--definition", "none")
    env_only = run("example-product")

    assert flag.returncode != 0 and "unknown flag: --definition" in flag.stderr
    assert env_only.returncode == 1
    assert env_only.stderr.strip().splitlines()[-1] == _NO_LINE.format(card=run.card("example-product"))
    assert run.engine_argv() == [] and run.definition_calls("product") == []

    run.project("sonar", card=_card("**Definition:** full").replace("example-product", "sonar"))
    kept = run("sonar", "--dry-run")
    assert _after_product_path(kept.stdout) == _DEFINITION_LINES["full"]


# --- full and prd-agari: the definition walk is started first -------------------------------------


@pytest.mark.parametrize("definition, spine, chain_name", [
    ("full", _PRODUCT_SPINE, "product"),
    ("prd-agari", "PRD,Agari", "agari"),
])
def test_a_definition_walk_is_started_before_the_change(run, definition, spine, chain_name):
    run.project("example-product", definition=definition)

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert _after_product_path(result.stdout) == _DEFINITION_LINES[definition]
    own, other = _SIBLING_OF[definition], {"product": "agari", "agari": "product"}[
        _SIBLING_OF[definition]]
    calls = run.definition_calls(own)
    assert len(calls) == 1 and run.definition_calls(other) == []
    call = calls[0]
    assert call[0] == "--start"
    assert _flag_value(call, "--spine") == spine
    assert _flag_value(call, "--chain-name") == chain_name
    assert _flag_value(call, "--project") == "example-product"
    assert run.engine_argv() == [] and run.change_calls() == []
    hook = run.hook_of(call)
    assert hook[:2] == [f"{run.core_dir}/launchers/chain-change/launcher.sh", "example-product"]
    assert hook[2] == "--after-definition" and re.fullmatch(r"[A-Za-z0-9]+", hook[3])
    assert hook[4:] == ["--definition-ended"]
    assert run.pending("example-product") == [f"chain-change-example-product-pending.{hook[3]}"]


@pytest.mark.parametrize("definition", ["full", "prd-agari"])
@pytest.mark.parametrize("end", _WHOLE_SPINE_ENDS)
def test_whole_spine_end_continues_the_same_change_launch(run, definition, end):
    """Four ends of a launch, each across both definition values. The change walk is the one a
    `none` launch with the same options starts — compared argv for argv, including the build-idea
    hook."""
    run.env["KENSAIAPP_NOTIFIER"] = "/bin/echo"
    run.project("example-product")
    baseline, launched = _start_and_baseline(
        run, definition, "--provider", "codex", "--keep-awake", "--context-cap", "1000")
    assert launched.returncode == 0, launched.stderr
    assert run.change_starts() == []

    fired = run.fire(run.definition_calls(_SIBLING_OF[definition])[0], end)

    assert fired.returncode == 0, fired.stderr
    assert "chain-change: the definition walk ended " + end + " — starting the change walk" \
        in fired.stdout
    assert run.change_starts() == [baseline]
    assert shlex.split(_flag_value(baseline, "--on-end")) == [
        f"{run.core_dir}/launchers/build-idea/launcher.sh", "example-product", "--chain-ended"]
    assert run.pending() == []


@pytest.mark.parametrize("definition", ["full", "prd-agari"])
def test_synchronous_definition_end_can_continue(run, definition):
    """The walk has nothing to launch, so it ends inside its own `--start` and runs the hook before
    the definition launcher returns. The record must already be complete when that happens."""
    run.env["KENSAIAPP_NOTIFIER"] = "/bin/echo"
    run.project("example-product")
    baseline, _ = _start_and_baseline(run, definition, "--keep-awake", "--context-cap", "7")
    run.forget_engine_calls()
    unfired = run.pending()
    run.env["DEF_STUB_FIRE"] = "settled"

    result = run("example-product", "--keep-awake", "--context-cap", "7")

    assert result.returncode == 0, result.stderr
    assert run.change_starts() == [baseline]
    assert [rc for rc, _, _ in run.hook_results()][-1] == 0
    assert run.pending() == unfired   # only the earlier, unfired launch's record is left


@pytest.mark.parametrize("end", [
    "could_not_be_settled", "machinery", "cap", "no_runnable_command", "stopped", "empty_run",
    "an_end_added_later",
])
def test_other_definition_ends_start_no_change(run, end):
    run.project("example-product", definition="full")
    assert run("example-product").returncode == 0

    fired = run.fire(run.definition_calls("product")[0], end)

    assert fired.returncode == 0, fired.stderr
    assert fired.stdout.strip().splitlines()[-1] == (
        f"chain-change: the definition walk ended {end} — the change walk did not start. Run "
        "chain-change again to walk the definition and then the change.")
    assert run.change_calls() == []
    assert run.pending() == []


def test_refused_definition_preserves_other_pending_launches(run):
    run.project("example-product", definition="full")
    assert run("example-product").returncode == 0
    first_record = run.pending("example-product")
    first_call = run.definition_calls("product")[0]
    run.env["DEF_STUB_EXIT"] = "3"
    run.env["DEF_STUB_REFUSAL"] = "chain-product: a walk is already live on example-product"

    refused = run("example-product")

    assert refused.returncode == 3
    assert "chain-product: a walk is already live on example-product" in refused.stderr
    assert refused.stderr.strip().splitlines()[-1] == _DEFINITION_REFUSED
    assert run.change_calls() == []
    assert run.pending("example-product") == first_record
    run.env.pop("DEF_STUB_EXIT")
    assert run.fire(first_call, "settled").returncode == 0
    assert len(run.change_starts()) == 1


@pytest.mark.parametrize("definition", ["full", "prd-agari"])
def test_each_start_runs_the_definition_first(run, definition):
    run.project("example-product", definition=definition)
    journey = run.root / "system" / "projects" / "example-product" / "journey" / "tobiishi"
    (journey / "2026-09-15_part-walked").mkdir(parents=True)
    (journey / "2026-09-15_part-walked" / "change_spec.md").write_text("# spec\n")
    sibling = _SIBLING_OF[definition]

    assert run("example-product").returncode == 0
    assert run("example-product").returncode == 0

    assert len(run.definition_calls(sibling)) == 2
    assert run.change_calls() == []
    assert len(run.pending("example-product")) == 2


# --- the options each walk receives ---------------------------------------------------------------


@pytest.mark.parametrize("channel", ["flags", "environment", "flag-beats-environment"])
def test_definition_and_change_receive_their_own_options(run, channel):
    run.project("example-product", definition="prd-agari")
    cli = ["--keep-awake", "--context-cap", "1000"]
    expected_provider = "codex"
    if channel == "flags":
        cli += ["--provider", "codex"]
    elif channel == "environment":
        run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"
    else:
        run.env["KENSAIAPP_AGENT_PROVIDER"] = "gemini"
        cli += ["--provider", "codex"]
    run.env["KENSAIAPP_NOTIFIER"] = "/bin/echo"

    assert run("example-product", *cli).returncode == 0
    definition_call = run.definition_calls("agari")[0]
    assert _flag_value(definition_call, "--provider") == expected_provider
    assert "--keep-awake" in definition_call
    assert "--context-cap" not in definition_call
    assert _flag_value(definition_call, "--notifier") == "/bin/echo"

    assert run.fire(definition_call, "settled").returncode == 0
    started = run.change_starts()[0]
    assert _flag_value(started, "--provider") == expected_provider
    assert "--keep-awake" in started
    assert _flag_value(started, "--context-cap") == "1000"
    assert _flag_value(started, "--notifier") == "/bin/echo"


@pytest.mark.parametrize("later_provider", ["claude", "invalid-later-provider"])
def test_continuation_uses_saved_values_after_environment_and_card_change(run, later_provider):
    run.env["KENSAIAPP_NOTIFIER"] = "/bin/echo"
    run.project("example-product", definition="full")
    assert run("example-product", "--provider", "codex", "--keep-awake", "--context-cap", "1000"
               ).returncode == 0
    call = run.definition_calls("product")[0]
    hook_env = dict(run.env)
    hook_env["KENSAIAPP_AGENT_PROVIDER"] = later_provider
    hook_env["KENSAIAPP_NOTIFIER"] = "/usr/bin/false"
    # The card moves on: another product path, and no Definition line at all. The hook reads neither
    # the line nor the new path.
    (run.card("example-product")).write_text(_card(product_path="products/elsewhere"))

    fired = run.fire(call, "settled", env=hook_env)

    assert fired.returncode == 0, fired.stderr
    started = run.change_starts()[0]
    assert _flag_value(started, "--product-path") == f"{run.root}/products/thing"
    assert _flag_value(started, "--provider") == "codex"
    assert _flag_value(started, "--notifier") == "/bin/echo"
    assert "--keep-awake" in started and _flag_value(started, "--context-cap") == "1000"


@pytest.mark.parametrize("later_provider", ["claude", "invalid-later-provider"])
def test_empty_saved_options_stay_omitted_despite_later_environment(run, later_provider):
    run.project("example-product", definition="full")
    assert run("example-product").returncode == 0
    hook_env = dict(run.env)
    hook_env["KENSAIAPP_AGENT_PROVIDER"] = later_provider
    hook_env["KENSAIAPP_NOTIFIER"] = "/bin/echo"

    fired = run.fire(run.definition_calls("product")[0], "settled", env=hook_env)

    assert fired.returncode == 0, fired.stderr
    started = run.change_starts()[0]
    for flag in ("--provider", "--notifier", "--keep-awake", "--context-cap"):
        assert flag not in started


def test_pending_values_remain_data(run, tmp_path):
    marker = tmp_path / "ran"
    hostile = f"/odd dir/a=b;touch {marker};$(touch {marker}) `touch {marker}` back\\slash & * ?"
    run.project("example-product", product_path=hostile, definition="full")
    run.env["KENSAIAPP_NOTIFIER"] = f"/n o;tify=1 $(touch {marker}) &"

    assert run("example-product").returncode == 0
    fired = run.fire(run.definition_calls("product")[0], "settled")

    assert fired.returncode == 0, fired.stderr
    started = run.change_starts()[0]
    assert _flag_value(started, "--product-path") == hostile
    assert _flag_value(started, "--notifier") == f"/n o;tify=1 $(touch {marker}) &"
    assert not marker.exists()


def test_the_callback_survives_a_core_path_with_spaces(run, tmp_path):
    run.project("example-product", definition="full")
    spaced_host = tmp_path / "a core with spaces"
    spaced_core = spaced_host / "core"
    for name in ("chain-change", "chain-product"):
        folder = spaced_core / "launchers" / name
        folder.mkdir(parents=True)
        shutil.copy(_CORE / "launchers" / name / "launcher.sh", folder / "launcher.sh")
    (spaced_core / "tools").symlink_to(_CORE / "tools")
    (spaced_host / "pin.json").write_text(json.dumps({
        "id": "spaced-self-pin",
        "source_host_root": str(spaced_host),
        "created": "1970-01-01T00:00:00+00:00",
    }) + "\n")

    result = subprocess.run([str(spaced_core / "launchers" / "chain-change" / "launcher.sh"),
                             "example-product"], cwd=str(tmp_path), capture_output=True, text=True,
                            env=run.env)

    assert result.returncode == 0, result.stderr
    call = run.definition_calls("product")[0]
    assert run.hook_of(call)[0] == f"{spaced_core}/launchers/chain-change/launcher.sh"
    fired = run.fire(call, "settled")
    assert fired.returncode == 0, fired.stderr
    assert shlex.split(_flag_value(run.change_starts()[0], "--on-end")) == [
        f"{spaced_core}/launchers/build-idea/launcher.sh", "example-product", "--chain-ended"]


# --- a dry run starts neither walk ----------------------------------------------------------------


@pytest.mark.parametrize("definition", ["full", "prd-agari"])
def test_definition_dry_run_starts_nothing(run, definition):
    run.project("example-product", definition=definition)

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert _after_product_path(result.stdout) == _DEFINITION_LINES[definition]
    assert "chain-change: change=2026-09-15_stub" in result.stdout
    assert "DRY RUN — would run:" in result.stdout
    assert run.describe_argv()[0] == "--describe"
    assert run.definition_calls("product") == [] and run.definition_calls("agari") == []
    assert run.change_calls() == [] and run.pending() == []


@pytest.mark.parametrize("definition", ["full", "prd-agari"])
def test_definition_dry_run_prints_todays_change_dry_run_after_its_line(run, definition):
    """CP-448: the CP-440 line, then what a dry run prints today for the change walk. Today's lines
    are a `none` dry run's on the same project and options, compared line for line, so an extra or
    a missing line fails as surely as a changed one."""
    run.project("example-product")
    cli = ("--dry-run", "--keep-awake", "--context-cap", "1000")
    baseline = run("example-product", *cli)
    assert baseline.returncode == 0, baseline.stderr
    run.rewrite_card("example-product", "**Definition:** none", f"**Definition:** {definition}")

    result = run("example-product", *cli)

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        _DEFINITION_LINES[definition] if line == _DEFINITION_LINES["none"] else line
        for line in baseline.stdout.splitlines()]
    assert run.definition_calls(_SIBLING_OF[definition]) == [] and run.pending() == []


# --- --stop ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("card_lines", [
    (),
    ("**Definition:** Full",),
    ("**Definition:** none", "**Definition:** none"),
], ids=["missing", "invalid", "duplicated"])
def test_stop_ignores_the_definition_field(run, card_lines):
    run.project("example-product", card=_card(*card_lines))
    run.env["KENSAIAPP_NOTIFIER"] = "/bin/echo"

    result = run("example-product", "--stop")

    assert result.returncode == 0, result.stderr
    assert run.engine_argv() == ["--stop", f"{run.root}/system/logs/chain-change-example-product-state.json",
                                 "--notifier", "/bin/echo"]
    assert _STOP_NOTICE not in result.stdout


def test_stop_cancels_every_pending_launch_of_its_project(run):
    run.project("example-product", definition="full")
    run.project("sonar", definition="prd-agari", card=None)
    assert run("example-product").returncode == 0 and run("example-product").returncode == 0
    assert run("sonar").returncode == 0
    product_calls = run.definition_calls("product")
    sonar_call = run.definition_calls("agari")[0]
    assert len(run.pending("example-product")) == 2 and len(run.pending("sonar")) == 1
    run.env["ENGINE_STUB_EXIT"] = "3"
    run.env["ENGINE_STUB_LINE"] = "engine: no change walk to stop"

    stopped = run("example-product", "--stop")

    assert stopped.returncode == 3
    assert stopped.stdout.splitlines().index(_STOP_NOTICE) < stopped.stdout.splitlines().index(
        "engine: no change walk to stop")
    assert run.pending("example-product") == [] and len(run.pending("sonar")) == 1
    for call in product_calls:
        late = run.fire(call, "settled")
        assert late.returncode == 0
    assert run.change_starts() == []
    run.env.pop("ENGINE_STUB_EXIT")
    assert run.fire(sonar_call, "settled").returncode == 0
    assert len(run.change_starts()) == 1


def test_a_claimed_callback_cannot_start_twice(run):
    run.project("example-product", definition="full")
    assert run("example-product").returncode == 0
    call = run.definition_calls("product")[0]

    first = run.fire(call, "settled")
    second = run.fire(call, "settled")

    assert first.returncode == 0 and second.returncode == 0
    assert len(run.change_starts()) == 1
    assert second.stdout.strip().splitlines()[-1] == (
        "chain-change: the definition walk ended settled, and no change walk is waiting on it — "
        "nothing to start")


def test_a_callback_with_no_record_starts_nothing(run):
    run.project("example-product", definition="full")

    result = subprocess.run(
        [str(_SCRIPT), "example-product", "--after-definition", "Abc123", "--definition-ended", "settled"],
        cwd=str(run.root), capture_output=True, text=True, env=run.env)

    assert result.returncode == 0, result.stderr
    assert "no change walk is waiting on it — nothing to start" in result.stdout
    assert run.change_calls() == []


def test_continuation_propagates_change_engine_status(run):
    run.project("example-product", definition="full")
    assert run("example-product").returncode == 0
    call = run.definition_calls("product")[0]
    run.env["ENGINE_STUB_EXIT"] = "7"

    failed = run.fire(call, "settled")
    again = run.fire(call, "settled")

    assert failed.returncode == 7
    assert run.pending() == []
    assert again.returncode == 0
    assert len(run.change_starts()) == 1


# --- the hook-only form refuses what a start could not have written -------------------------------


def _hook(run, *args):
    return subprocess.run([str(_SCRIPT), "example-product", *args], cwd=str(run.root), capture_output=True,
                          text=True, env=run.env)


_PAIR = ("chain-change: --after-definition and --definition-ended go together — they are the "
         "definition walk's end hook, which passes both")
_NO_OTHER_FLAG = ("chain-change: --after-definition and --definition-ended are the definition "
                  "walk's end hook and take no other flag")
_TOKEN_NEEDED = "chain-change: --after-definition needs the pending-launch token the start wrote"
_END_NEEDED = ("chain-change: --definition-ended needs the end the definition walk reported "
               "(settled, left_for_the_owner, ...)")


@pytest.mark.parametrize("args, message", [
    (("--after-definition", "Abc123"), _PAIR),
    (("--definition-ended", "settled"), _PAIR),
    (("--after-definition", "Abc123", "--definition-ended", "settled", "--dry-run"),
     _NO_OTHER_FLAG),
    (("--after-definition", "Abc123", "--definition-ended", "settled", "--keep-awake"),
     _NO_OTHER_FLAG),
    (("--after-definition", "Abc123", "--definition-ended", "settled", "--provider", "claude"),
     _NO_OTHER_FLAG),
    (("--after-definition", "Abc123", "--definition-ended", "settled", "--context-cap", "5"),
     _NO_OTHER_FLAG),
    (("--after-definition", "Abc123", "--definition-ended", "settled", "--stop"), _NO_OTHER_FLAG),
    (("--stop", "--after-definition", "Abc123", "--definition-ended", "settled"), _NO_OTHER_FLAG),
    (("--after-definition",), _TOKEN_NEEDED),
    (("--after-definition", "", "--definition-ended", "settled"), _TOKEN_NEEDED),
    (("--after-definition", "Abc123", "--definition-ended"), _END_NEEDED),
    (("--after-definition", "Abc123", "--definition-ended", ""), _END_NEEDED),
], ids=["token-alone", "end-alone", "dry-run", "keep-awake", "provider", "context-cap",
        "stop-after", "stop-before", "token-missing", "token-empty", "end-missing", "end-empty"])
def test_hook_only_arguments_are_validated(run, args, message):
    run.project("example-product", definition="full")
    assert run("example-product").returncode == 0
    pending = run.pending()
    run.forget_engine_calls()

    result = _hook(run, *args)

    assert result.returncode == 1
    assert result.stderr.strip().splitlines()[-1] == message
    assert run.change_calls() == [] and run.pending() == pending


@pytest.mark.parametrize("token", ["a/b", "..", ".", "a.b", "../x", "d/../../../sentinel.txt",
                                   "ab cd", "ab;cd", "a$b"])
def test_a_token_a_start_could_not_have_written_is_refused_before_any_file_is_read(run, token):
    run.project("example-product", definition="full")
    logs = run.root / "system" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "chain-change-example-product-pending.d").mkdir()
    sentinel = run.root / "sentinel.txt"
    sentinel.write_text("keep")

    result = _hook(run, "--after-definition", token, "--definition-ended", "settled")

    assert result.returncode == 1
    assert result.stderr.strip().splitlines()[-1] == (
        f"chain-change: '{token}' is not a pending-launch token — refusing to read a file for it")
    assert sentinel.read_text() == "keep"
    assert run.change_calls() == []


# --- the launcher's own words and the template ----------------------------------------------------


def test_template_card_is_accepted_by_the_reader(run):
    template = (_CORE / "templates" / "project_template.md").read_text()
    card = template.replace("products/<product-dir>", "products/thing")
    run.project("example-product", card=card)

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert _after_product_path(result.stdout) == _DEFINITION_LINES["full"]


def test_header_states_the_definition_contract():
    text = _SCRIPT.read_text()
    header, body = text.split("set -euo pipefail", 1)

    for heading in ("WHAT RUNS BEFORE THE CHANGE WALK", 'WHY THE RULE OVER STEPS="change" CHANGED',
                    "A CARD WITHOUT THE LINE IS REFUSED", "THE PENDING-LAUNCH RECORD"):
        assert f"# {heading}" in header
    assert "whose card" in header
    assert "**Definition:** line reading full, prd-agari or none" in header
    assert ("<CORE>/launchers/chain-change/launcher.sh <project> --after-definition <token> "
            "--definition-ended <end>") in header
    assert 'STEPS="change"' in body
    assert [line for line in header.splitlines() if "Definition" in line]
    assert [line for line in body.splitlines() if "Definition:" in line and "grep" in line]


def test_the_provider_usage_entry_survives_the_new_prose():
    lines = _SCRIPT.read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if re.match(r"#\s+--provider\s", line))
    entry = [lines[start]]
    for line in lines[start + 1:]:
        if not re.match(r"#\s{10,}\S", line):
            break
        entry.append(line)
    flat = " ".join(" ".join(part.lstrip("#").split()) for part in entry)

    assert ".providers.toml" in flat and "is refused" in flat
    assert "The force reaches a definition walk's runs too." in flat
