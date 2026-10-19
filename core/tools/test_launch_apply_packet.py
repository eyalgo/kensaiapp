"""Contract tests for `launch-apply-packet.sh`.

Deliberately small — the two gates, the fixed-prompt guarantee, and the one piece of
real logic (deriving the repos the entries edit). Everything else the launcher does is
covered by its siblings' suites.

Isolation, as in `test_launch_fix_author.py`: the core-resident launcher derives its own core as
`SCRIPT_DIR/..` (Task 18) and resolves its instance root from its cwd (`$PWD`), so the fixture
runs it with `<tmp>/example-host/` as cwd — making that the instance root, with a sibling
`<tmp>/example-satellite/` as a second real git repo the multi-repo tests need (the derivation asks
git, so a bare directory will not do). The launcher itself, and the pin machinery it now
unconditionally reaches, live in a THIRD tree, `<tmp>/pin/`, kept apart from both instance repos —
the shape a real pin always has (never the live host itself) — so the adapter's own trailing
`--add-dir <pin root>` (Task 7) can never coincide with an instance path a test asserts about.
`<tmp>/pin/` carries a `pin.json`, the same trick `core/launchers/skill/test_skill.py`'s
`_isolated_core` uses, so `pin_enter` finds it already its own pin and neither re-execs nor copies
a host. A fake `claude` on PATH records the argv it was handed, the assertion surface: a dry run
proves what the script *would* print, the stub proves what it *does* pass.

Fixture is local rather than in `conftest.py` — that file's `run` fixture is
product-prd's, down to its env var names.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent / "launch-apply-packet.sh"
_TOOLS_DIR = Path(__file__).resolve().parent
_PIN_TOOLS = ("pin.py", "pin_run.sh", "agent_run.py", "model_assignment.py", "task_context.py",
               "env_file.py", "hook_wiring.py")
# The provider reader, the one file it reads, and the two modules the reader imports: the launcher
# asks the reader for its `launch-apply-packet` entry before it looks at the packet.
_PROVIDER_TOOLS = ("providers.py", "run_intelligence.py", "intelligence.py")
_ENTRY = "launch-apply-packet"
# The delivered text is the tracked template at the instance root, which no suite leans a live
# `.providers.toml` for: that file is untracked and absent from a fresh checkout.
_DELIVERED_PROVIDERS = (_TOOLS_DIR.parents[1] / ".providers.toml.example").read_text()

# A watcher stub written to a launcher's OWN default path, for the tests that prove the walk.
# It exits immediately on every call, so a test can prove the path resolved without waiting on a
# real watcher's appear window.
DEFAULT_PATH_WATCHER_STUB = """import os, sys
if "--list-ids" in sys.argv:
    sys.exit(0)
print("watcher-at-default-path: reached", file=sys.stderr, flush=True)
sys.exit(0)
"""


CLAUDE_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" > "$CLAUDE_ARGV_LOG"
"""

# A recording stand-in for `agent_run.py`: it logs the argv it was called with, one JSON list per
# call, and hands off to the real adapter kept beside it as `agent_run_real.py`, so a dry run still
# prints the real command. The `claude --bg` argv the adapter builds carries no provider token, so
# the adapter call is the only place `--provider` can be seen; an empty log is how a test shows the
# launcher never reached the adapter.
ADAPTER_RECORDER = """#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
with open(os.environ["ADAPTER_ARGV_LOG"], "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\\n")
real = Path(__file__).with_name("agent_run_real.py")
os.execv(sys.executable, [sys.executable, str(real), *sys.argv[1:]])
"""


def _toml_without(key):
    """The delivered file with only `launchers.<key>` removed, in the way
    `core/launchers/test_launcher_providers.py` `toml_without` does it."""
    lines = _DELIVERED_PROVIDERS.splitlines(keepends=True)
    kept = [ln for ln in lines if not re.fullmatch(rf"{re.escape(key)} = \"[a-z]+\"\n", ln)]
    assert len(kept) == len(lines) - 1, f"launchers.{key} is not one line of the delivered file"
    return "".join(kept)


def _toml_with(key, value):
    """The delivered file with `launchers.<key>` naming `value`."""
    return re.sub(rf"^{re.escape(key)} = \"[a-z]+\"$", f'{key} = "{value}"',
                  _DELIVERED_PROVIDERS, flags=re.MULTILINE)


def packet(state="approved", verdict="fix", files=(), out_of_scope=()):
    """A packet with just the fields the launcher reads.

    `out_of_scope` files are written indented, the way `## Out of scope` carries them —
    the launcher must not widen its grant to those.
    """
    body = f"# Fix packet — thing 1.0.0 → 1.1.0\n\n**State:** {state}\n**Verdict:** {verdict}\n\n## Entries\n"
    for i, f in enumerate(files, start=1):
        body += f"\n### E{i} — an entry\n\n- **File:** `{f}`\n- **Anchor:**\n  ```\n  old\n  ```\n"
    if out_of_scope:
        body += "\n## Out of scope\n"
        for f in out_of_scope:
            body += f"\n- **E9 — withdrawn**\n  - **File:** `{f}`\n"
    return body


@pytest.fixture
def run(tmp_path):
    """`run(*args) -> CompletedProcess`, with helpers hanging off the callable.

    - `run.write(text) -> Path` writes a packet inside the instance repo
    - `run.write_external(text) -> Path` writes one in the audit vault
    - `run.launched_argv()` is the argv the stub `claude` received (empty under --dry-run)
    """
    dev_root = tmp_path / "example-host"
    audit_root = tmp_path / "example-satellite"
    for root in (dev_root, audit_root):
        (root / "system" / "loaders").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(root)], check=True)

    # The pin root is its OWN tree, distinct from both `dev_root` (the instance root this
    # launcher's cwd resolves to) and `audit_root` — the shape a real pin always has, so the
    # adapter's own trailing `--add-dir <pin root>` (Task 7) can never coincide with a repo path
    # a test asserts about.
    pin_root_dir = tmp_path / "pin"
    tools_dir = pin_root_dir / "core" / "tools"   # this script lives in <CORE>/tools (Task 18)
    tools_dir.mkdir(parents=True)

    script_dst = tools_dir / "launch-apply-packet.sh"
    shutil.copy2(_SCRIPT, script_dst)
    script_dst.chmod(0o755)
    # The launcher `source`s its detach-and-return tail from `detach_watcher.sh` beside it
    # ($SCRIPT_DIR/, the flat shape). This copy of the tree is where the launcher actually
    # runs from, so the library has to be here too — a fixture that omits it is testing a
    # launcher that cannot reach its own machinery, and every keep-awake assertion below
    # would pass or fail on the wrong branch.
    shutil.copy2(_SCRIPT.parent / "detach_watcher.sh", tools_dir / "detach_watcher.sh")

    # The pin machinery every launcher and every Claude launch now unconditionally reaches
    # (`pin_enter` sources `pin_run.sh`, which shells out to `pin.py`; the Claude argv comes from
    # `agent_run.py`, and its own three module imports). `pin_root_dir` carries a `pin.json` below,
    # so `pin_enter` finds this tree already its own pin — the same trick `test_skill.py`'s
    # `_isolated_core` uses — and neither re-execs nor copies a host.
    for tool in _PIN_TOOLS + _PROVIDER_TOOLS:
        shutil.copy2(_TOOLS_DIR / tool, tools_dir / tool)
    # The real adapter moves aside and the recorder takes its name (see ADAPTER_RECORDER).
    shutil.copy2(_TOOLS_DIR / "agent_run.py", tools_dir / "agent_run_real.py")
    (tools_dir / "agent_run.py").write_text(ADAPTER_RECORDER)
    (pin_root_dir / "pin.json").write_text(
        json.dumps({"id": "isolated-packet", "source_host_root": str(pin_root_dir),
                    "created": "1970-01-01T00:00:00+00:00"})
        + "\n"
    )

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    claude_stub = bin_dir / "claude"
    claude_stub.write_text(CLAUDE_STUB)
    claude_stub.chmod(0o755)

    argv_log = tmp_path / "claude_argv.log"
    adapter_log = tmp_path / "adapter_argv.log"

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["CLAUDE_ARGV_LOG"] = str(argv_log)
    env["ADAPTER_ARGV_LOG"] = str(adapter_log)
    env["LAUNCH_PACKET_NOTIFIER"] = str(tmp_path / "nope" / "missing.sh")   # watcher skipped

    def _run(*args):
        return subprocess.run(
            [str(script_dst), *args], cwd=str(dev_root),
            capture_output=True, text=True, env=env,
        )

    def _write(text, where=None):
        p = (where or dev_root) / "fix_packet.md"
        p.write_text(text)
        return p

    def _write_external(text):
        d = audit_root / ".claude" / "skills" / "thing" / "evidence" / "v1.0.0"
        d.mkdir(parents=True)
        p = d / "fix_packet.md"
        p.write_text(text)
        return p

    def _launched_argv():
        return argv_log.read_text().splitlines() if argv_log.exists() else []

    def _adapter_calls():
        """Every call the launcher made to the adapter, as the argv list each carried."""
        if not adapter_log.exists():
            return []
        return [json.loads(line) for line in adapter_log.read_text().splitlines()]

    def _set_providers(text):
        """Replace the instance's own `.providers.toml` — the only file the launcher reads."""
        providers_file.write_text(text)

    providers_file = dev_root / ".providers.toml"
    providers_file.write_text(_DELIVERED_PROVIDERS)
    _run.providers_file = providers_file
    _run.set_providers = _set_providers
    _run.adapter_calls = _adapter_calls
    _run.script = script_dst
    _run.env = env
    _run.dev = dev_root
    _run.audit = audit_root
    _run.pin_root = pin_root_dir
    _run.write = _write
    _run.write_external = _write_external
    _run.launched_argv = _launched_argv
    return _run


def _add_dirs(argv):
    """Every `--add-dir` value, written as two tokens or as one `--add-dir=<dir>`."""
    paired = [argv[i + 1] for i, a in enumerate(argv) if a == "--add-dir"]
    return paired + [a[len("--add-dir="):] for a in argv if a.startswith("--add-dir=")]


# --- guards ------------------------------------------------------------------


def test_no_packet_arg_dies_with_usage(run):
    result = run()
    assert result.returncode == 1
    assert "usage: launch-apply-packet.sh <packet-path>" in result.stderr


def test_missing_packet_dies(run):
    result = run("nope/fix_packet.md")
    assert result.returncode == 1
    assert "no packet at" in result.stderr
    assert run.launched_argv() == []


# --- the two gates -----------------------------------------------------------
#
# Both are duplicated ENFORCEMENT of a rule fix_packet.md owns — they fail in a second
# instead of spending an agent on a run that must stop.


def test_an_unapproved_packet_is_refused(run):
    p = run.write(packet(state="awaiting-owner", files=[run.dev / "system" / "loaders" / "cpo.md"]))
    result = run(str(p))
    assert result.returncode == 1
    assert "not 'approved'" in result.stderr
    assert "awaiting-owner" in result.stderr        # tells you which state blocked it
    assert run.launched_argv() == []


def test_a_packet_with_no_state_is_refused(run):
    p = run.write("# Fix packet\n\n**Verdict:** fix\n")
    result = run(str(p))
    assert result.returncode == 1
    assert "missing" in result.stderr
    assert run.launched_argv() == []


def test_a_rebuild_verdict_spawns_no_fixer(run):
    p = run.write(packet(verdict="rebuild"))
    result = run(str(p))
    assert result.returncode == 1
    assert "carries no entries" in result.stderr
    assert run.launched_argv() == []


# --- deriving the repos the entries edit -------------------------------------


def test_a_packet_naming_no_entry_files_is_refused(run):
    p = run.write(packet(files=[]))
    result = run(str(p))
    assert result.returncode == 1
    assert "no entry files" in result.stderr
    assert run.launched_argv() == []


def test_a_file_outside_any_git_repo_dies_before_launching(run, tmp_path):
    loose = tmp_path / "loose"
    loose.mkdir()
    p = run.write(packet(files=[loose / "thing.md"]))
    result = run(str(p))
    assert result.returncode == 1
    assert "in no git repo" in result.stderr
    assert run.launched_argv() == []


def test_a_file_in_a_nonexistent_directory_dies(run):
    p = run.write(packet(files=[run.dev / "gone" / "thing.md"]))
    result = run(str(p))
    assert result.returncode == 1
    assert "does not exist" in result.stderr
    assert run.launched_argv() == []


def test_the_instance_repo_is_not_added_to_itself(run):
    """In-repo edits are covered by cwd; adding it would be noise."""
    p = run.write(packet(files=[run.dev / "system" / "loaders" / "cpo.md"]))
    run(str(p))
    assert run.dev not in [Path(d) for d in _add_dirs(run.launched_argv())]


def test_a_second_instance_is_added_so_its_loader_is_writable(run):
    """The reason 1.1.0 exists: a role's loader lives in every instance it runs in."""
    p = run.write(packet(files=[
        run.dev / "system" / "loaders" / "cpo.md",
        run.audit / "system" / "loaders" / "cpo.md",
    ]))
    run(str(p))
    assert str(run.audit) in _add_dirs(run.launched_argv())


def test_each_repo_is_added_once_however_many_entries_name_it(run):
    p = run.write(packet(files=[
        run.audit / "system" / "loaders" / "cpo.md",
        run.audit / "system" / "loaders" / "cpo.md",
    ]))
    run(str(p))
    assert _add_dirs(run.launched_argv()).count(str(run.audit)) == 1


def test_an_out_of_scope_file_does_not_widen_the_grant(run):
    """An out-of-scope entry is one the fixer must NOT edit."""
    p = run.write(packet(
        files=[run.dev / "system" / "loaders" / "cpo.md"],
        out_of_scope=[run.audit / "system" / "loaders" / "cpo.md"],
    ))
    run(str(p))
    assert str(run.audit) not in _add_dirs(run.launched_argv())


def test_the_repos_are_reported_to_the_caller(run):
    p = run.write(packet(files=[
        run.dev / "system" / "loaders" / "cpo.md",
        run.audit / "system" / "loaders" / "cpo.md",
    ]))
    result = run(str(p), "--dry-run")
    assert "Edits land in:" in result.stdout
    assert str(run.audit) in result.stdout


# --- the fixed prompt --------------------------------------------------------


def test_launches_with_the_fixed_prompt_and_the_fixer_agent(run):
    p = run.write(packet(files=[run.dev / "system" / "loaders" / "cpo.md"]))
    run(str(p))
    argv = run.launched_argv()
    assert argv[:2] == ["--bg", f"apply the fix packet at {p}."]
    assert argv[argv.index("--agent") + 1] == "kaizen-fixer"


def test_the_prompt_stays_one_line(run):
    """watch_agent.py matches a run by name == prompt exactly; a multi-line prompt
    orphans the watcher (d158fb1)."""
    p = run.write(packet(files=[
        run.dev / "system" / "loaders" / "cpo.md",
        run.audit / "system" / "loaders" / "cpo.md",
    ]))
    run(str(p))
    assert "\n" not in run.launched_argv()[1]


def test_the_repo_list_never_reaches_the_prompt(run):
    """The grant travels by --add-dir; the prompt names only the packet."""
    p = run.write(packet(files=[
        run.dev / "system" / "loaders" / "cpo.md",
        run.audit / "system" / "loaders" / "cpo.md",
    ]))
    run(str(p))
    assert str(run.audit) not in run.launched_argv()[1]


def test_the_run_is_launched_in_auto_permission_mode(run):
    """Load-bearing: nobody can answer a permission prompt in a --bg run."""
    p = run.write(packet(files=[run.dev / "system" / "loaders" / "cpo.md"]))
    run(str(p))
    argv = run.launched_argv()
    assert argv[argv.index("--permission-mode") + 1] == "auto"


def test_an_external_packet_is_added_as_a_readable_input(run):
    p = run.write_external(packet(files=[run.dev / "system" / "loaders" / "cpo.md"]))
    run(str(p))
    assert str(p.parent) in _add_dirs(run.launched_argv())


def test_dry_run_prints_the_command_without_launching(run):
    p = run.write(packet(files=[run.dev / "system" / "loaders" / "cpo.md"]))
    result = run(str(p), "--dry-run")
    assert result.returncode == 0
    assert "DRY RUN" in result.stdout
    assert "kaizen-fixer" in result.stdout
    assert run.launched_argv() == []


# --- the pin (Task 18) --------------------------------------------------------


def test_dry_run_prints_the_pin_line(run):
    """`pin_enter` runs right after the `CORE_DIR` guard, ahead of every other use of
    `CORE_DIR` — this fixture's `pin.json` marks `run.pin_root` as already its own pin, so the
    line reads `(inherited)`, not `(new)`."""
    p = run.write(packet(files=[run.dev / "system" / "loaders" / "cpo.md"]))
    result = run(str(p), "--dry-run")
    assert result.returncode == 0
    assert f"Pin: {run.pin_root} (inherited)" in result.stdout


def test_the_agent_flag_is_kept(run):
    """The argv comes from the one adapter now (Task 18), not a hand-assembled `set --`; the
    fixer's own agent grant must still ride it."""
    p = run.write(packet(files=[run.dev / "system" / "loaders" / "cpo.md"]))
    run(str(p))
    argv = run.launched_argv()
    assert argv[argv.index("--agent") + 1] == "kaizen-fixer"


# --- keep-awake (--keep-awake) -----------------------------------------------
# The held path is the shared keep-awake block, proven behaviourally end to end in
# core/launchers/seeds-from-idea/test_seeds_from_idea.py and proven to be the SAME block here by
# core/tools/test_keep_awake_binding.py; what this file pins is this launcher's own arg-parse
# recognizing the flag — the no-notifier note only prints when keep_awake was set.
# (Until 2026-08-22 this comment pointed at test_launch_cold_read.py, which does not exist.)


def test_keep_awake_without_a_notifier_notes_it_and_exits_zero(run):
    p = run.write(packet(files=[run.dev / "system" / "loaders" / "cpo.md"]))
    result = run(str(p), "--keep-awake")
    assert result.returncode == 0
    assert "keep-awake needs a completion watcher" in result.stdout


# --- the two core-relative paths, at their real depth ----------------------------
#
# This is a FLAT launcher: it lives in `<CORE>/tools/` beside the machinery it reads, so both its
# watcher and its detach library are `$SCRIPT_DIR/<file>` — the other of the two path shapes, and
# the reason `kensaiapp_structure.md` § Owner-run launcher folder calls the wrong walk the failure
# that does not announce itself. A watcher it cannot find leaves the detach unrun on an exit-0
# launch; a library it cannot find skips the detach the same way.


def test_watcher_is_found_beside_the_script_when_nothing_overrides_it(run):
    """The flat shape's default: `$SCRIPT_DIR/watch_agent.py`. The stub is written to the
    launcher's own directory — the path under test — so a default expressed with any other walk
    finds nothing and this fails. Every other test in this suite points the notifier at a missing
    file and never reaches the happy path at all, so this is the only one that proves it."""
    (run.script.parent / "watch_agent.py").write_text(DEFAULT_PATH_WATCHER_STUB)
    notifier = run.dev / "notify.sh"
    notifier.write_text("#!/usr/bin/env bash\nexit 0\n")
    notifier.chmod(0o755)
    run.env["LAUNCH_PACKET_NOTIFIER"] = str(notifier)

    p = run.write(packet(files=[run.dev / "system" / "loaders" / "cpo.md"]))
    result = run(str(p))

    assert result.returncode == 0
    assert "completion watch skipped" not in result.stdout
    assert "Watcher log:" in result.stdout, (
        f"the detach did not run — the launcher failed to resolve watch_agent.py beside itself. "
        f"stdout: {result.stdout}"
    )
    # The detached child creates its own log, so discovery, read and completeness share one deadline.
    deadline = time.monotonic() + 30.0
    logs = []
    text = ""
    while True:
        logs = list((run.dev / "system" / "logs").glob("watch-packet-*.log"))
        if logs:
            text = logs[0].read_text()
        if "watcher-at-default-path: reached" in text or time.monotonic() >= deadline:
            break
        time.sleep(0.05)
    assert logs, "no watcher log was written, so no completion watch is running"
    assert "watcher-at-default-path: reached" in text, (
        f"the log exists but the watcher at the default path never ran: {text!r}"
    )


def test_detach_watcher_is_found_beside_the_script_when_nothing_overrides_it(run):
    """`$DETACH_LIB` has no env override — no test or caller ever wants a stub in its place — so
    the fixture stages the REAL library beside the copied launcher and every launch here already
    runs against it. This names that invariant instead of leaving it a side effect nothing asserts."""
    p = run.write(packet(files=[run.dev / "system" / "loaders" / "cpo.md"]))
    result = run(str(p))

    assert result.returncode == 0
    assert "no completion-watch library at" not in result.stdout


def test_a_missing_detach_watcher_is_reported_distinctly_and_does_not_block_the_launch(run):
    """The negative case: remove the library from beside the copied launcher — never from the real
    `core/tools/`, which every other test in this suite depends on. The launch must still happen
    and the report must name the library rather than blaming the notifier."""
    (run.script.parent / "detach_watcher.sh").unlink()

    p = run.write(packet(files=[run.dev / "system" / "loaders" / "cpo.md"]))
    result = run(str(p))

    assert result.returncode == 0
    assert run.launched_argv() != [], "the primary launch still happened"
    assert "no completion-watch library at" in result.stdout


# --- the provider: this launcher's entry in .providers.toml ------------------------------------
#
# The launcher asks the one reader for `launchers.launch-apply-packet` right after its usage
# check and runs on what it answers. The `claude --bg` argv carries no provider token, so what
# these cases look at is the call the launcher makes to the adapter (`run.adapter_calls()`), which
# the fixture's recording stand-in logs. The instance's own `.providers.toml` is the only
# file a case can change: no variable or flag selects the file.


def _approved_packet(run):
    return run.write(packet(files=[run.dev / "system" / "loaders" / "cpo.md"]))


def _arm_watcher(run):
    """Put a watcher stub at the launcher's own default path and a notifier that exists, so that a
    launch that got past the provider read would spawn a completion watch — and leave a log."""
    (run.script.parent / "watch_agent.py").write_text(DEFAULT_PATH_WATCHER_STUB)
    notifier = run.dev / "notify.sh"
    notifier.write_text("#!/usr/bin/env bash\nexit 0\n")
    notifier.chmod(0o755)
    run.env["LAUNCH_PACKET_NOTIFIER"] = str(notifier)


def _watcher_logs(run):
    return list((run.dev / "system" / "logs").glob("watch-packet-*.log"))


def test_a_missing_entry_refuses_and_launches_nothing(run):
    run.set_providers(_toml_without(_ENTRY))
    _arm_watcher(run)
    p = _approved_packet(run)

    result = run(str(p))

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr
    assert str(run.providers_file) in result.stderr
    assert run.launched_argv() == []                 # the stub `claude` received no argv
    assert run.adapter_calls() == []                 # the adapter was never called
    assert _watcher_logs(run) == []                  # no completion watch was spawned


def test_a_missing_entry_refuses_a_dry_run_too(run):
    run.set_providers(_toml_without(_ENTRY))
    p = _approved_packet(run)

    result = run(str(p), "--dry-run")

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr
    assert "DRY RUN" not in result.stdout
    assert run.adapter_calls() == []


def test_the_delivered_entry_puts_provider_claude_on_the_adapter_call(run):
    p = _approved_packet(run)

    result = run(str(p), "--dry-run")

    assert result.returncode == 0
    calls = run.adapter_calls()
    assert len(calls) == 1
    assert calls[0][calls[0].index("--provider") + 1] == "claude"
    assert "DRY RUN — would launch:" in result.stdout
    assert "--bg" in result.stdout and "kaizen-fixer" in result.stdout


def test_an_entry_naming_codex_is_refused_by_name(run):
    run.set_providers(_toml_with(_ENTRY, "codex"))
    p = _approved_packet(run)

    result = run(str(p), "--dry-run")

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr and "codex" in result.stderr
    assert "DRY RUN" not in result.stdout
    assert run.adapter_calls() == []


def test_a_missing_provider_file_is_refused_naming_the_file(run):
    run.providers_file.unlink()
    p = _approved_packet(run)

    result = run(str(p), "--dry-run")

    assert result.returncode != 0
    assert str(run.providers_file) in result.stderr
    assert "cp .providers.toml.example .providers.toml" in result.stderr   # CP-486
    assert "DRY RUN" not in result.stdout
    assert run.adapter_calls() == []


def test_the_force_variable_is_ignored(run):
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"
    p = _approved_packet(run)

    result = run(str(p), "--dry-run")

    assert result.returncode == 0
    calls = run.adapter_calls()
    assert calls[0][calls[0].index("--provider") + 1] == "claude"


def test_a_missing_provider_reader_is_refused_by_name(run):
    """The guard is a rule of its own: without it the missing file surfaces as python3's own
    complaint, which names no launcher and no reader."""
    (run.script.parent / "providers.py").unlink()
    p = _approved_packet(run)

    result = run(str(p), "--dry-run")

    assert result.returncode != 0
    assert f"no provider reader at {run.script.parent / 'providers.py'}" in result.stderr
    assert run.adapter_calls() == []


def test_a_missing_intelligence_resolver_is_refused_by_name(run):
    """The reader imports the resolver, so its absence would otherwise be a traceback."""
    (run.script.parent / "run_intelligence.py").unlink()
    p = _approved_packet(run)

    result = run(str(p), "--dry-run")

    assert result.returncode != 0
    resolver = run.script.parent / "run_intelligence.py"
    assert f"no intelligence resolver at {resolver}" in result.stderr
    assert "Traceback" not in result.stderr
    assert run.adapter_calls() == []


# --- the provider: what the spec states and the cases above leave unasserted -------------------
#
# Added by the integrity review (development-code-integrity), each from the rule it names.


def test_an_entry_naming_an_unknown_provider_is_refused_by_name(run):
    """CP-350: a value that is not a known provider is refused, naming the entry and the value."""
    run.set_providers(_toml_with(_ENTRY, "grok"))
    p = _approved_packet(run)

    result = run(str(p), "--dry-run")

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr and "grok" in result.stderr
    assert "DRY RUN" not in result.stdout
    assert run.adapter_calls() == []


def test_a_provider_file_that_is_not_toml_is_refused_naming_the_file(run):
    """CP-350: a file that cannot be read as TOML is refused, naming its path."""
    run.set_providers("[launchers\nlaunch-apply-packet = = claude\n")
    p = _approved_packet(run)

    result = run(str(p), "--dry-run")

    assert result.returncode != 0
    assert str(run.providers_file) in result.stderr
    assert "DRY RUN" not in result.stdout
    assert run.adapter_calls() == []


def test_a_dry_run_refuses_with_the_launch_s_own_message(run):
    """CP-351: the dry run refuses exactly where the launch would, with the same message."""
    run.set_providers(_toml_without(_ENTRY))
    p = _approved_packet(run)

    launch = run(str(p))
    dry = run(str(p), "--dry-run")

    assert launch.returncode != 0 and dry.returncode != 0
    assert dry.stderr == launch.stderr
    assert run.adapter_calls() == []


def test_a_missing_entry_with_invalid_arguments_still_launches_nothing(run):
    """CP-349: with the entry missing and the packet not there either, the script exits non-zero
    and launches nothing, whichever message it prints first."""
    run.set_providers(_toml_without(_ENTRY))

    result = run(str(run.dev / "no_such_fix_packet.md"))

    assert result.returncode != 0
    assert run.launched_argv() == []
    assert run.adapter_calls() == []


def test_a_provider_file_outside_the_instance_is_not_read(run):
    """CP-483: the script reads the file at the root of the instance it launches for. A complete
    `.providers.toml` at the host root or in the sibling audit folder does not stand in for an
    instance file lacking the entry."""
    run.set_providers(_toml_without(_ENTRY))
    decoys = [run.pin_root / ".providers.toml",
              run.pin_root.parent / "example-satellite" / ".providers.toml"]
    for decoy in decoys:
        decoy.parent.mkdir(parents=True, exist_ok=True)
        decoy.write_text(_DELIVERED_PROVIDERS)
    p = _approved_packet(run)

    result = run(str(p), "--dry-run")

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr
    assert str(run.providers_file) in result.stderr
    assert all(str(decoy) not in result.stderr for decoy in decoys)
    assert run.adapter_calls() == []
