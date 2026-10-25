"""Contract tests for `launch-fix-author.sh`.

Deliberately small — the guards, the fixed-prompt guarantee, and the one piece of
real logic (picking the newest version). Everything else the launcher does is
covered by its siblings' suites.

Isolation, as in `test_launch_product_prd.py`: the core-resident launcher resolves its
instance root from its cwd (`$PWD`), so the fixture runs it with `<tmp>/example-satellite/`
as cwd — making that the instance root, with `<tmp>/example-host/` — the host its `.env` binds — for its
`--add-dir` to resolve to. (The fixture runs a copy under that tree; the copy's location
is incidental — cwd is what selects the instance.) A fake `claude` on PATH records the
argv it was handed, the assertion surface for the fixed-prompt guarantee: a dry run proves
what the script *would* print, the stub proves what it *does* pass.

Fixture is local — product-prd's own `run` fixture lives in its test file (env var names
specific to it), so this suite keeps its own.

Isolation, extended for Task 18: the launcher's own core is `SCRIPT_DIR/..`, and the pin
machinery it now unconditionally reaches (`pin_enter`, `pin.py`, `agent_run.py`, and the one
Claude builder's own two module imports) lives in a THIRD tree, `<tmp>/pin/`, kept apart from
`<tmp>/example-satellite/` — the shape a real pin always has — so the adapter's own trailing
`--add-dir <pin root>` (Task 7) can never coincide with an instance path a test asserts about.
`<tmp>/pin/` carries a `pin.json`, the same trick `core/launchers/skill/test_skill.py`'s
`_isolated_core` uses, so `pin_enter` finds it already its own pin and neither re-execs nor
copies a host.
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

_SCRIPT = Path(__file__).resolve().parent / "launch-fix-author.sh"
_SKILL_PATH_PY = Path(__file__).resolve().parent / "skill_path.py"
_TOOLS_DIR = Path(__file__).resolve().parent
_PIN_TOOLS = ("pin.py", "pin_run.sh", "agent_run.py", "model_assignment.py", "task_context.py",
               "env_file.py", "hook_wiring.py")
# The provider reader, the one file it reads, and the two modules the reader imports: the launcher
# asks the reader for its `launch-fix-author` entry before it resolves the skill.
_PROVIDER_TOOLS = ("providers.py", "run_intelligence.py", "intelligence.py")
_ENTRY = "launch-fix-author"
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

AWAITING = "# Fix packet\n\n**State:** awaiting-owner\n\n### E1 — a thing\n### E2 — another\n"
APPROVED = "# Fix packet\n\n**State:** approved\n\n### E1 — a thing\n"
ANSWERS = "# Owner answers\n\n### A1 — the call\n- **Call:** option (a)\n"

AUDIT_BODY = """# Audit — thing v{ver}

## Skill-general findings

- **SG-A · [non-blocking · skill-general · altitude]** something. Direction: fix it.
- **SG-B · [non-blocking · skill-general · coverage]** something else. Direction: fix it.

## Change-local findings

- **CL-1 · [non-blocking · change-local · coverage]** a third. Direction: note it.
"""


@pytest.fixture
def run(tmp_path):
    """`run(*args) -> CompletedProcess`, with helpers hanging off the callable.

    - `run.round(version, audit=True, packet=None)` creates an evidence folder
    - `run.launched_argv()` is the argv the stub `claude` received (empty under --dry-run)
    """
    audit_root = tmp_path / "example-satellite"
    audit_root.mkdir()
    # The host whose core the satellite binds — named by the satellite's own `.env`, the way a
    # real satellite names it, so the --add-dir resolves to it wherever it sits.
    host_root = tmp_path / "example-host"
    (host_root / "core").mkdir(parents=True)
    (audit_root / ".env").write_text(f"CORE={host_root / 'core'}\n")

    # The pin root is its OWN tree, distinct from `audit_root` (the instance root this launcher's
    # cwd resolves to) — the shape a real pin always has, so the adapter's own trailing
    # `--add-dir <pin root>` (Task 7) can never coincide with a repo path a test asserts about.
    pin_root_dir = tmp_path / "pin"
    tools_dir = pin_root_dir / "core" / "tools"   # this script lives in <CORE>/tools (Task 18)
    tools_dir.mkdir(parents=True)

    script_dst = tools_dir / "launch-fix-author.sh"
    shutil.copy2(_SCRIPT, script_dst)
    script_dst.chmod(0o755)
    resolver_dst = tools_dir / "skill_path.py"
    shutil.copy2(_SKILL_PATH_PY, resolver_dst)
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
        json.dumps({"id": "isolated-author", "source_host_root": str(pin_root_dir),
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
    env["LAUNCH_AUTHOR_NOTIFIER"] = str(tmp_path / "nope" / "missing.sh")   # watcher skipped

    def _run(*args):
        return subprocess.run(
            [str(script_dst), *args], cwd=str(audit_root),
            capture_output=True, text=True, env=env,
        )

    def _round(version, audit=True, packet=None, answers=None, skill="thing"):
        d = audit_root / ".claude" / "skills" / skill / "evidence" / f"v{version}"
        d.mkdir(parents=True)
        if audit:
            (d / "audit.md").write_text(AUDIT_BODY.format(ver=version))
        if packet is not None:
            (d / "fix_packet.md").write_text(packet)
        if answers is not None:
            (d / "owner_answers.md").write_text(answers)
        return d

    def _launched_argv():
        return argv_log.read_text().splitlines() if argv_log.exists() else []

    def _grouped_round(version, group="g", audit=True, packet=None, answers=None, skill="thing"):
        d = audit_root / "skills" / group / ".claude" / "skills" / skill / "evidence" / f"v{version}"
        d.mkdir(parents=True)
        if audit:
            (d / "audit.md").write_text(AUDIT_BODY.format(ver=version))
        if packet is not None:
            (d / "fix_packet.md").write_text(packet)
        if answers is not None:
            (d / "owner_answers.md").write_text(answers)
        return d

    def _grouped_skill(group, skill="thing"):
        d = audit_root / "skills" / group / ".claude" / "skills" / skill
        d.mkdir(parents=True)
        return d

    def _remove_resolver():
        resolver_dst.unlink()

    def _adapter_calls():
        """Every call the launcher made to the adapter, as the argv list each carried."""
        if not adapter_log.exists():
            return []
        return [json.loads(line) for line in adapter_log.read_text().splitlines()]

    def _set_providers(text):
        """Replace the instance's own `.providers.toml` — the only file the launcher reads."""
        providers_file.write_text(text)

    providers_file = audit_root / ".providers.toml"
    providers_file.write_text(_DELIVERED_PROVIDERS)
    _run.providers_file = providers_file
    _run.set_providers = _set_providers
    _run.adapter_calls = _adapter_calls
    _run.script = script_dst
    _run.env = env
    _run.root = audit_root
    _run.pin_root = pin_root_dir
    _run.host = host_root
    _run.round = _round
    _run.launched_argv = _launched_argv
    _run.grouped_round = _grouped_round
    _run.grouped_skill = _grouped_skill
    _run.remove_resolver = _remove_resolver
    return _run


# --- guards ------------------------------------------------------------------


def test_no_skill_arg_dies_with_usage(run):
    result = run()
    assert result.returncode == 1
    assert "usage: launch-fix-author.sh <skill>" in result.stderr


def test_unknown_skill_dies_before_launching(run):
    result = run("nope")
    assert result.returncode == 1
    assert "is 'nope' a real skill?" in result.stderr
    assert run.launched_argv() == []


def test_skill_without_an_evidence_vault_dies(run):
    (run.root / ".claude" / "skills" / "thing").mkdir(parents=True)
    result = run("thing")
    assert result.returncode == 1
    assert "no evidence vault" in result.stderr


def test_version_with_no_audit_dies(run):
    run.round("1.0.0", audit=False)
    result = run("thing", "1.0.0")
    assert result.returncode == 1
    assert "has not been audited" in result.stderr


def test_evidence_exists_but_nothing_is_audited_dies(run):
    run.round("1.0.0", audit=False)
    result = run("thing")
    assert result.returncode == 1
    assert "audit a round first" in result.stderr


def test_an_existing_packet_is_never_overwritten(run):
    run.round("1.0.0", packet="# Fix packet\n\n**State:** approved\n")
    result = run("thing")
    assert result.returncode == 1
    assert "a packet already exists" in result.stderr
    assert "approved" in result.stderr          # tells you which one you nearly clobbered
    assert run.launched_argv() == []


# --- version resolution ------------------------------------------------------


def test_newest_version_wins_numerically_not_lexically(run):
    """v3.17.0 beats v3.4.0 — a lexical sort gets this pair backwards."""
    run.round("3.4.0")
    run.round("3.17.0")
    result = run("thing", "--dry-run")
    assert "round v3.17.0" in result.stdout
    assert "v3.4.0" not in result.stdout


def test_a_version_without_an_audit_is_not_chosen_as_newest(run):
    run.round("1.0.0")
    run.round("2.0.0", audit=False)
    result = run("thing", "--dry-run")
    assert "round v1.0.0" in result.stdout


def test_an_explicit_version_is_honoured(run):
    run.round("1.0.0")
    run.round("2.0.0")
    result = run("thing", "1.0.0", "--dry-run")
    assert "round v1.0.0" in result.stdout


# --- the fixed prompt --------------------------------------------------------


def test_launches_with_the_fixed_prompt_and_the_author_agent(run):
    d = run.round("1.0.0")
    run("thing", "1.0.0")
    argv = run.launched_argv()
    assert argv[:2] == ["--bg", f"author the fix packet for the thing skill from the audit at "
                                f"{d / 'audit.md'}. write it to {d / 'fix_packet.md'}."]
    assert "--agent" in argv and argv[argv.index("--agent") + 1] == "kaizen-fix-author"


def test_the_run_is_launched_in_auto_permission_mode(run):
    """Load-bearing: nobody can answer a permission prompt in a --bg run."""
    run.round("1.0.0")
    run("thing", "1.0.0")
    argv = run.launched_argv()
    assert argv[argv.index("--permission-mode") + 1] == "auto"


def test_caller_cannot_append_to_the_prompt(run):
    run.round("1.0.0")
    run("thing", "1.0.0", "and also fix everything else")
    # The extra word is read as a version, so it fails the audit guard — it never
    # reaches the prompt.
    assert run.launched_argv() == []


def test_the_host_repo_is_added_so_core_and_symlinked_skills_resolve(run):
    run.round("1.0.0")
    run("thing", "1.0.0")
    argv = run.launched_argv()
    assert f"--add-dir={run.host}" in argv


def test_the_findings_count_is_reported_but_not_passed_into_the_run(run):
    run.round("1.0.0")
    result = run("thing", "1.0.0")
    assert "3 findings" in result.stdout          # 2 SG + 1 CL
    # The count is for the caller's eyes only — it must not steer the run. (Assert the
    # count, not the bare word: pytest names its tmp dir after the test, so "findings"
    # appears in every path in argv.)
    assert "3 findings" not in " ".join(run.launched_argv())


def test_dry_run_prints_the_command_without_launching(run):
    run.round("1.0.0")
    result = run("thing", "1.0.0", "--dry-run")
    assert result.returncode == 0
    assert "DRY RUN" in result.stdout
    assert "kaizen-fix-author" in result.stdout
    assert run.launched_argv() == []


# --- the pin (Task 18) --------------------------------------------------------


def test_dry_run_prints_the_pin_line(run):
    """`pin_enter` runs right after the `CORE_DIR` guard, ahead of every other use of
    `CORE_DIR` — this fixture's `pin.json` marks `run.pin_root` as already its own pin, so the
    line reads `(inherited)`, not `(new)`."""
    run.round("1.0.0")
    result = run("thing", "1.0.0", "--dry-run")
    assert result.returncode == 0
    assert f"Pin: {run.pin_root} (inherited)" in result.stdout


def test_host_root_add_dir_is_kept_where_it_was(run):
    """The argv comes from the one adapter now (Task 18), not a hand-assembled `set --`; the
    host repo's own grant must still ride it."""
    run.round("1.0.0")
    run("thing", "1.0.0")
    argv = run.launched_argv()
    assert f"--add-dir={run.host}" in argv


def test_the_agent_flag_is_kept(run):
    run.round("1.0.0")
    run("thing", "1.0.0")
    argv = run.launched_argv()
    assert argv[argv.index("--agent") + 1] == "kaizen-fix-author"


# --- --settle: the same packet guard, read the other way ---------------------
#
# The default mode dies when a packet exists; --settle dies when one doesn't. The
# pair of tests below and `test_an_existing_packet_is_never_overwritten` above are
# the two halves of that one condition — if either flips, the guard was dropped
# rather than inverted.


def test_settle_without_a_packet_dies(run):
    run.round("1.0.0")
    result = run("thing", "1.0.0", "--settle")
    assert result.returncode == 1
    assert "nothing to settle" in result.stderr
    assert run.launched_argv() == []


def test_settle_without_owner_answers_dies_and_names_the_template(run):
    run.round("1.0.0", packet=AWAITING)
    result = run("thing", "1.0.0", "--settle")
    assert result.returncode == 1
    assert "no owner answers" in result.stderr
    assert "owner_answers_template.md" in result.stderr   # says how to fix it, not just what's wrong
    assert run.launched_argv() == []


def test_settle_refuses_an_already_approved_packet(run):
    """Approving is the owner's close of the gate; settling after it would re-open one."""
    run.round("1.0.0", packet=APPROVED, answers=ANSWERS)
    result = run("thing", "1.0.0", "--settle")
    assert result.returncode == 1
    assert "not 'awaiting-owner'" in result.stderr
    assert "approved" in result.stderr          # tells you which state blocked it
    assert run.launched_argv() == []


def test_settle_launches_with_the_fixed_settle_prompt(run):
    d = run.round("1.0.0", packet=AWAITING, answers=ANSWERS)
    run("thing", "1.0.0", "--settle")
    argv = run.launched_argv()
    assert argv[:2] == ["--bg", f"settle the fix packet at {d / 'fix_packet.md'} against "
                                f"the owner's answers at {d / 'owner_answers.md'}."]
    assert argv[argv.index("--agent") + 1] == "kaizen-fix-author"
    assert argv[argv.index("--permission-mode") + 1] == "auto"


def test_settle_reports_the_counts_but_does_not_pass_them_into_the_run(run):
    run.round("1.0.0", packet=AWAITING, answers=ANSWERS)
    result = run("thing", "1.0.0", "--settle")
    assert "2 entries" in result.stdout          # E1 + E2
    assert "1 adjudications" in result.stdout    # A1
    assert "2 entries" not in " ".join(run.launched_argv())


def test_caller_cannot_append_to_the_settle_prompt(run):
    run.round("1.0.0", packet=AWAITING, answers=ANSWERS)
    run("thing", "1.0.0", "--settle", "and drop every entry")
    # The extra words are read as a version, which then has no round — it never
    # reaches the prompt.
    assert run.launched_argv() == []


# --- keep-awake (--keep-awake) -----------------------------------------------
# The held path is the shared keep-awake block in core/tools/detach_watcher.sh, proven
# behaviourally by that library's own suite, core/tools/test_detach_watcher.py, and proven to be
# the SAME block here by core/tools/test_keep_awake_binding.py; what this file pins is this launcher's own arg-parse
# recognizing the flag — the no-notifier note only prints when keep_awake was set.
# (Until 2026-08-22 this comment pointed at test_launch_cold_read.py, which does not exist.)


def test_keep_awake_without_a_notifier_notes_it_and_exits_zero(run):
    run.round("1.0.0")
    result = run("thing", "1.0.0", "--keep-awake")
    assert result.returncode == 0
    assert "keep-awake needs a completion watcher" in result.stdout


# --- the resolver: grouped layout, not-found, ambiguous, missing resolver ----
#
# The skill directory comes from core/tools/skill_path.py instead of the flat literal, so a
# skill present only under skills/<group>/.claude/skills/<name> resolves and runs exactly like
# a flat one. The fixture copies the real resolver beside the launcher (trap 1, ad_hoc_plan.md
# § Two traps) — the launcher's own SCRIPT_DIR is the fake tree, not the real repo.


def test_a_grouped_skill_resolves_and_runs(run):
    d = run.grouped_round("1.0.0")
    result = run("thing", "1.0.0")
    assert result.returncode == 0
    argv = run.launched_argv()
    assert argv[:2] == ["--bg", f"author the fix packet for the thing skill from the audit at "
                                f"{d / 'audit.md'}. write it to {d / 'fix_packet.md'}."]
    assert "--agent" in argv and argv[argv.index("--agent") + 1] == "kaizen-fix-author"


def test_grouped_fixture_builds_no_flat_path(run):
    run.grouped_round("1.0.0")
    assert not (run.root / ".claude" / "skills").exists()


def test_the_flat_case_still_resolves_with_no_grouped_layer_present(run):
    """The existing flat-layout behaviour, unchanged by the resolver adoption."""
    d = run.round("1.0.0")
    result = run("thing", "1.0.0")
    assert result.returncode == 0
    argv = run.launched_argv()
    assert argv[:2] == ["--bg", f"author the fix packet for the thing skill from the audit at "
                                f"{d / 'audit.md'}. write it to {d / 'fix_packet.md'}."]


def test_unknown_skill_dies_before_launching_naming_no_layout(run):
    result = run("nope")
    assert result.returncode != 0
    assert "no skill at" in result.stderr
    assert str(run.root) in result.stderr          # the root searched
    assert "'nope'" in result.stderr                # the skill name
    assert ".claude/skills" not in result.stderr
    assert "skills/" not in result.stderr
    assert run.launched_argv() == []


def test_ambiguous_skill_dies_naming_both_matching_directories(run):
    d1 = run.grouped_skill("g1")
    d2 = run.grouped_skill("g2")
    result = run("thing")
    assert result.returncode != 0
    assert str(d1) in result.stderr
    assert str(d2) in result.stderr
    assert run.launched_argv() == []


def test_ambiguous_message_differs_from_not_found_message(run):
    run.grouped_skill("g1")
    run.grouped_skill("g2")
    ambiguous = run("thing")
    not_found = run("nope")
    assert ambiguous.stderr != not_found.stderr
    assert ambiguous.returncode != 0
    assert not_found.returncode != 0


def test_stderr_noise_on_a_clean_resolve_never_reaches_the_captured_path(run):
    """The resolver's own stderr is folded into the captured value today (2>&1), so any text a
    future resolver version prints on a successful exit would land INSIDE skill_dir. A stub
    resolver here — exit 0, a real directory on stdout, a line of noise on stderr — proves the
    fold does not happen: the launcher proceeds against the stdout path alone, and the noise
    reaches neither the launched argv nor stdout."""
    d = run.round("1.0.0")
    skill_dir = run.root / ".claude" / "skills" / "thing"
    stub = run.root.parent / "stub_resolver.py"
    stub.write_text(
        "import sys\n"
        f"print({str(skill_dir)!r})\n"
        "print('resolver: a future warning', file=sys.stderr)\n"
    )
    run.env["LAUNCH_AUTHOR_RESOLVER"] = str(stub)
    result = run("thing", "1.0.0")
    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert argv[:2] == ["--bg", f"author the fix packet for the thing skill from the audit at "
                                f"{d / 'audit.md'}. write it to {d / 'fix_packet.md'}."]
    assert "resolver: a future warning" not in " ".join(argv)
    assert "resolver: a future warning" not in result.stdout


def test_a_missing_resolver_dies_as_this_launcher_not_a_traceback(run):
    run.remove_resolver()
    result = run("thing")
    assert result.returncode != 0
    assert "launch-fix-author:" in result.stderr
    assert "usage: launch-fix-author.sh" in result.stderr
    assert "Traceback" not in result.stderr
    assert run.launched_argv() == []
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
    notifier = run.root / "notify.sh"
    notifier.write_text("#!/usr/bin/env bash\nexit 0\n")
    notifier.chmod(0o755)
    run.env["LAUNCH_AUTHOR_NOTIFIER"] = str(notifier)

    run.round("1.0.0")
    result = run("thing", "1.0.0")

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
        logs = list((run.root / "system" / "logs").glob("watch-author-thing-*.log"))
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
    run.round("1.0.0")
    result = run("thing", "1.0.0")

    assert result.returncode == 0
    assert "no completion-watch library at" not in result.stdout


def test_a_missing_detach_watcher_is_reported_distinctly_and_does_not_block_the_launch(run):
    """The negative case: remove the library from beside the copied launcher — never from the real
    `core/tools/`, which every other test in this suite depends on. The launch must still happen
    and the report must name the library rather than blaming the notifier."""
    (run.script.parent / "detach_watcher.sh").unlink()

    run.round("1.0.0")
    result = run("thing", "1.0.0")

    assert result.returncode == 0
    assert run.launched_argv() != [], "the primary launch still happened"
    assert "no completion-watch library at" in result.stdout


# --- the provider: this launcher's entry in .providers.toml ------------------------------------
#
# The launcher asks the one reader for `launchers.launch-fix-author` right after its usage check
# and runs on what it answers — above the `--settle` split, so one entry governs both modes. The
# `claude --bg` argv carries no provider token, so what these cases look at is the call the
# launcher makes to the adapter (`run.adapter_calls()`), which the fixture's recording stand-in
# logs. The instance's own `.providers.toml` is the only file a case can change: no variable
# or flag selects the file.


def _arm_watcher(run):
    """Put a watcher stub at the launcher's own default path and a notifier that exists, so that a
    launch that got past the provider read would spawn a completion watch — and leave a log."""
    (run.script.parent / "watch_agent.py").write_text(DEFAULT_PATH_WATCHER_STUB)
    notifier = run.root / "notify.sh"
    notifier.write_text("#!/usr/bin/env bash\nexit 0\n")
    notifier.chmod(0o755)
    run.env["LAUNCH_AUTHOR_NOTIFIER"] = str(notifier)


def _watcher_logs(run):
    return list((run.root / "system" / "logs").glob("watch-author-*.log"))


def test_a_missing_entry_refuses_and_launches_nothing(run):
    run.set_providers(_toml_without(_ENTRY))
    _arm_watcher(run)
    run.round("1.0.0")

    result = run("thing", "1.0.0")

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr
    assert str(run.providers_file) in result.stderr
    assert run.launched_argv() == []                 # the stub `claude` received no argv
    assert run.adapter_calls() == []                 # the adapter was never called
    assert _watcher_logs(run) == []                  # no completion watch was spawned


def test_a_missing_entry_refuses_a_dry_run_too(run):
    run.set_providers(_toml_without(_ENTRY))
    run.round("1.0.0")

    result = run("thing", "1.0.0", "--dry-run")

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr
    assert "DRY RUN" not in result.stdout
    assert run.adapter_calls() == []


def test_the_missing_entry_also_refuses_settle_mode(run):
    run.set_providers(_toml_without(_ENTRY))
    run.round("1.0.0", packet=AWAITING, answers=ANSWERS)

    result = run("thing", "1.0.0", "--settle")

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr
    assert run.launched_argv() == []
    assert run.adapter_calls() == []


def test_the_delivered_entry_puts_provider_claude_on_the_adapter_call(run):
    run.round("1.0.0")

    result = run("thing", "1.0.0", "--dry-run")

    assert result.returncode == 0
    calls = run.adapter_calls()
    assert len(calls) == 1
    assert calls[0][calls[0].index("--provider") + 1] == "claude"
    assert "DRY RUN — would launch:" in result.stdout
    assert "--bg" in result.stdout and "kaizen-fix-author" in result.stdout


def test_an_entry_naming_codex_is_refused_by_name(run):
    run.set_providers(_toml_with(_ENTRY, "codex"))
    run.round("1.0.0")

    result = run("thing", "1.0.0", "--dry-run")

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr and "codex" in result.stderr
    assert "DRY RUN" not in result.stdout
    assert run.adapter_calls() == []


def test_a_missing_provider_file_is_refused_naming_the_file(run):
    run.providers_file.unlink()
    run.round("1.0.0")

    result = run("thing", "1.0.0", "--dry-run")

    assert result.returncode != 0
    assert str(run.providers_file) in result.stderr
    assert "cp .providers.toml.example .providers.toml" in result.stderr   # CP-486
    assert "DRY RUN" not in result.stdout
    assert run.adapter_calls() == []


def test_the_force_variable_is_ignored(run):
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"
    run.round("1.0.0")

    result = run("thing", "1.0.0", "--dry-run")

    assert result.returncode == 0
    calls = run.adapter_calls()
    assert calls[0][calls[0].index("--provider") + 1] == "claude"


def test_a_missing_provider_reader_is_refused_by_name(run):
    """The guard is a rule of its own: without it the missing file surfaces as python3's own
    complaint, which names no launcher and no reader."""
    (run.script.parent / "providers.py").unlink()
    run.round("1.0.0")

    result = run("thing", "1.0.0", "--dry-run")

    assert result.returncode != 0
    assert f"no provider reader at {run.script.parent / 'providers.py'}" in result.stderr
    assert run.adapter_calls() == []


def test_a_missing_intelligence_resolver_is_refused_by_name(run):
    """The reader imports the resolver, so its absence would otherwise be a traceback."""
    (run.script.parent / "run_intelligence.py").unlink()
    run.round("1.0.0")

    result = run("thing", "1.0.0", "--dry-run")

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
    run.round("1.0.0")

    result = run("thing", "1.0.0", "--dry-run")

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr and "grok" in result.stderr
    assert "DRY RUN" not in result.stdout
    assert run.adapter_calls() == []


def test_a_provider_file_that_is_not_toml_is_refused_naming_the_file(run):
    """CP-350: a file that cannot be read as TOML is refused, naming its path."""
    run.set_providers("[launchers\nlaunch-fix-author = = claude\n")
    run.round("1.0.0")

    result = run("thing", "1.0.0", "--dry-run")

    assert result.returncode != 0
    assert str(run.providers_file) in result.stderr
    assert "DRY RUN" not in result.stdout
    assert run.adapter_calls() == []


def test_a_dry_run_refuses_with_the_launch_s_own_message(run):
    """CP-351: the dry run refuses exactly where the launch would, with the same message."""
    run.set_providers(_toml_without(_ENTRY))
    run.round("1.0.0")

    launch = run("thing", "1.0.0")
    dry = run("thing", "1.0.0", "--dry-run")

    assert launch.returncode != 0 and dry.returncode != 0
    assert dry.stderr == launch.stderr
    assert run.adapter_calls() == []


def test_a_missing_entry_with_invalid_arguments_still_launches_nothing(run):
    """CP-349: with the entry missing and the skill not there either, the script exits non-zero
    and launches nothing, whichever message it prints first."""
    run.set_providers(_toml_without(_ENTRY))

    result = run("no-such-skill", "1.0.0")

    assert result.returncode != 0
    assert run.launched_argv() == []
    assert run.adapter_calls() == []


def test_a_provider_file_outside_the_instance_is_not_read(run):
    """CP-483: the script reads the file at the root of the instance it launches for. A complete
    `.providers.toml` at the pin root or in the host folder does not stand in for an
    instance file lacking the entry."""
    run.set_providers(_toml_without(_ENTRY))
    decoys = [run.pin_root / ".providers.toml", run.host / ".providers.toml"]
    for decoy in decoys:
        decoy.parent.mkdir(parents=True, exist_ok=True)
        decoy.write_text(_DELIVERED_PROVIDERS)
    run.round("1.0.0")

    result = run("thing", "1.0.0", "--dry-run")

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr
    assert str(run.providers_file) in result.stderr
    assert all(str(decoy) not in result.stderr for decoy in decoys)
    assert run.adapter_calls() == []
