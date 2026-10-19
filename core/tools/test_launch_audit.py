"""Contract tests for `launch-audit.sh`.

Deliberately small — the guards, the round resolution delegated to `auditrun`, the fixed-prompt
guarantee, and the fail-closed handoff (chain into `launch-fix-author.sh`, or halt+notify) that
reads the round's own `audit.md` after the completion watch returns. Unlike the detach-and-return
siblings, this launcher always watches FOREGROUND — there is no `--wait` flag, because acting
after the run stops is what the launcher exists to do.

Isolation, as in `test_launch_fix_author.py`: the core-resident launcher derives its own core as
`SCRIPT_DIR/..` (Task 18) and resolves its instance root from its cwd (`$PWD`), so the fixture
copies the launcher and the pin machinery it now unconditionally reaches — `pin_enter` sources
`pin_run.sh`, which shells out to `pin.py`, and the one Claude builder `agent_run.py` (and its own
three module imports `model_assignment.py`, `task_context.py` and `env_file.py`) — into `<tmp>/example-satellite/core/tools/`,
and runs the script from there with `<tmp>/example-satellite/` as cwd, making that the instance root,
with `<tmp>/example-host/` — the host its `.env` binds — for its `--add-dir` to resolve to. `<tmp>/example-satellite/`
itself carries a `pin.json`, the same trick `core/launchers/skill/test_skill.py`'s `_isolated_core`
uses — so `pin_enter` finds this tree already its own pin and neither re-execs nor copies the host:
what the fixture builds is exactly what runs. A fake `claude` on PATH records the argv it was
handed — the assertion surface for the fixed-prompt guarantee. The completion watch is always
stubbed via `$LAUNCH_AUDIT_WATCHER` (a recording, instantly-terminal Python stub — there is no
"real watcher" path to test here, since the watch is unconditional). The fail-closed handoff reads
`audit.md` off disk AFTER the watch returns — a test simulating a landed audit sets
`CLAUDE_WRITES_AUDIT_AT` so the stub `claude` writes the file as its one side effect (mirroring
what the real run would produce), never pre-creating it before the resolve step, which would trip
the refuse-to-overwrite guard on an explicit version instead. `launch-fix-author.sh` is likewise
stubbed as a sibling script beside the copied launcher, recording its own argv.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent / "launch-audit.sh"
_TOOLS_DIR = Path(__file__).resolve().parent
_AUDITRUN_DIR = Path(__file__).resolve().parent / "auditrun"
_SKILL_PATH_PY = Path(__file__).resolve().parent / "skill_path.py"
_PIN_TOOLS = ("pin.py", "pin_run.sh", "agent_run.py", "model_assignment.py", "task_context.py",
               "env_file.py", "hook_wiring.py")
# The provider reader, the one file it reads, and the two modules the reader imports: the launcher
# asks the reader for its `launch-audit` entry before it resolves the skill.
_PROVIDER_TOOLS = ("providers.py", "run_intelligence.py", "intelligence.py")
_ENTRY = "launch-audit"
# The delivered text is the tracked template at the instance root, which no suite leans a live
# `.providers.toml` for: that file is untracked and absent from a fresh checkout.
_DELIVERED_PROVIDERS = (_TOOLS_DIR.parents[1] / ".providers.toml.example").read_text()

CLAUDE_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" > "$CLAUDE_ARGV_LOG"
if [ -n "${CLAUDE_WRITES_AUDIT_AT:-}" ]; then
  mkdir -p "$(dirname "$CLAUDE_WRITES_AUDIT_AT")"
  printf '# Audit\\n' > "$CLAUDE_WRITES_AUDIT_AT"
fi
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

# A watcher that records every call it gets, `--list-ids` included — `WATCH_STUB` records only the
# real watch call, which is not enough to show a launch was refused before it looked at anything.
ANY_CALL_WATCH_STUB = """import os, sys
with open(os.environ["WATCH_ANY_LOG"], "a") as fh:
    fh.write(" ".join(sys.argv[1:]) + "\\n")
sys.exit(0)
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


FIX_AUTHOR_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" > "$FIX_AUTHOR_ARGV_LOG"
exit 0
"""

# Instantly-terminal watcher stub: answers --list-ids (the pre-launch snapshot) with nothing,
# records the real watch call's argv, and exits 0 — foreground "terminal reached" the moment
# it's invoked. What the launcher does next is driven entirely by whether `audit.md` is on disk,
# never by anything this stub says — proving the launcher reads the artifact, not agent state.
WATCH_STUB = """import os, sys
if "--list-ids" in sys.argv:
    sys.exit(0)
log = os.environ.get("WATCH_ARGV_LOG")
if log:
    with open(log, "w") as fh:
        fh.write("\\n".join(sys.argv[1:]))
sys.exit(0)
"""


@pytest.fixture
def run(tmp_path):
    """`run(*args, extra_env=None) -> CompletedProcess`, with helpers hanging off the callable.

    - `run.round(version, audit=False, skill="thing")` creates an evidence folder
    - `run.skill(name)` creates a bare skill dir with no evidence vault
    - `run.launched_argv()` is the argv the stub `claude` received (empty under --dry-run)
    - `run.fix_author_argv()` is the argv the stub `launch-fix-author.sh` received (empty if
      never invoked)
    - `run.watch_argv()` is the argv the stub watcher received on its real (non `--list-ids`) call
    """
    audit_root = tmp_path / "example-satellite"
    audit_root.mkdir()
    # The host whose core the satellite binds — named by the satellite's own `.env`, the way a
    # real satellite names it, so the --add-dir resolves to it wherever it sits.
    host_root = tmp_path / "example-host"
    (host_root / "core").mkdir(parents=True)
    (audit_root / ".env").write_text(f"CORE={host_root / 'core'}\n")

    # The pin root is its OWN tree, distinct from `audit_root` (the instance root this launcher's
    # cwd resolves to) — the shape a real pin always has (`~/.kensaiapp/pins/<id>/`, never the
    # live host itself). Keeping them distinct is what lets `test_the_instance_repo_is_not_added_
    # to_itself`-shaped assertions stay meaningful: a pin root that coincided with the instance
    # root would make the adapter's own trailing `--add-dir <pin root>` (Task 7) indistinguishable
    # from the very add-dir a test is asserting THIS launcher's own logic did or didn't add.
    pin_root_dir = tmp_path / "pin"
    tools_dir = pin_root_dir / "core" / "tools"   # this script lives in <CORE>/tools (Task 18)
    tools_dir.mkdir(parents=True)

    script_dst = tools_dir / "launch-audit.sh"
    shutil.copy2(_SCRIPT, script_dst)
    script_dst.chmod(0o755)

    shutil.copytree(_AUDITRUN_DIR, tools_dir / "auditrun",
                     ignore=shutil.ignore_patterns("__pycache__"))

    resolver_dst = tools_dir / "skill_path.py"
    shutil.copy2(_SKILL_PATH_PY, resolver_dst)

    fix_author_dst = tools_dir / "launch-fix-author.sh"
    fix_author_dst.write_text(FIX_AUTHOR_STUB)
    fix_author_dst.chmod(0o755)

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
        json.dumps({"id": "isolated-audit", "source_host_root": str(pin_root_dir),
                    "created": "1970-01-01T00:00:00+00:00"})
        + "\n"
    )

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    claude_stub = bin_dir / "claude"
    claude_stub.write_text(CLAUDE_STUB)
    claude_stub.chmod(0o755)

    watcher = tmp_path / "watch_rec.py"
    watcher.write_text(WATCH_STUB)

    argv_log = tmp_path / "claude_argv.log"
    fix_author_argv_log = tmp_path / "fix_author_argv.log"
    watch_argv_log = tmp_path / "watch_argv.log"
    adapter_log = tmp_path / "adapter_argv.log"

    env = dict(os.environ)
    env.pop("KENSAIAPP_NOTIFIER", None)   # never let a host-set real notifier leak into a test
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["CLAUDE_ARGV_LOG"] = str(argv_log)
    env["FIX_AUTHOR_ARGV_LOG"] = str(fix_author_argv_log)
    env["WATCH_ARGV_LOG"] = str(watch_argv_log)
    env["ADAPTER_ARGV_LOG"] = str(adapter_log)
    env["LAUNCH_AUDIT_NOTIFIER"] = str(tmp_path / "nope" / "missing.sh")   # notifier off by default
    env["LAUNCH_AUDIT_WATCHER"] = str(watcher)

    def _run(*args, extra_env=None, cwd=None):
        e = dict(env)
        if extra_env:
            e.update(extra_env)
        return subprocess.run(
            [str(script_dst), *args], cwd=str(cwd or audit_root),
            capture_output=True, text=True, env=e,
        )

    def _round(version, audit=False, skill="thing"):
        d = audit_root / ".claude" / "skills" / skill / "evidence" / f"v{version}"
        d.mkdir(parents=True)
        if audit:
            (d / "audit.md").write_text(f"# Audit — thing v{version}\n")
        return d

    def _skill(name="thing"):
        d = audit_root / ".claude" / "skills" / name
        d.mkdir(parents=True)
        return d

    def _launched_argv():
        return argv_log.read_text().splitlines() if argv_log.exists() else []

    def _fix_author_argv():
        return fix_author_argv_log.read_text().splitlines() if fix_author_argv_log.exists() else []

    def _watch_argv():
        return watch_argv_log.read_text().splitlines() if watch_argv_log.exists() else []

    def _grouped_round(version, group="g", audit=False, skill="thing"):
        d = audit_root / "skills" / group / ".claude" / "skills" / skill / "evidence" / f"v{version}"
        d.mkdir(parents=True)
        if audit:
            (d / "audit.md").write_text(f"# Audit — thing v{version}\n")
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
    _run.tmp = tmp_path
    _run.round = _round
    _run.skill = _skill
    _run.launched_argv = _launched_argv
    _run.fix_author_argv = _fix_author_argv
    _run.watch_argv = _watch_argv
    _run.grouped_round = _grouped_round
    _run.grouped_skill = _grouped_skill
    _run.remove_resolver = _remove_resolver
    return _run


# --- guards ------------------------------------------------------------------


def test_no_skill_arg_dies_with_usage(run):
    result = run()
    assert result.returncode == 1
    assert "usage: launch-audit.sh <skill>" in result.stderr


def test_unknown_skill_dies_before_launching(run):
    result = run("nope")
    assert result.returncode == 1
    assert "is 'nope' a real skill?" in result.stderr
    assert run.launched_argv() == []


def test_skill_without_evidence_vault_dies(run):
    run.skill("thing")
    result = run("thing")
    assert result.returncode == 1
    assert "nothing has been audited" in result.stderr
    assert run.launched_argv() == []


# --- round resolution (delegated to auditrun.resolve_target) -----------------


def test_newest_unaudited_round_is_interpolated(run):
    run.round("1.0.0", audit=True)
    run.round("1.1.0", audit=False)
    result = run("thing", "--dry-run")
    # The resolved round is v1.1.0, reported on its own line — v1.0.0 (audited) legitimately
    # still appears as the interpolated PRIOR round, so this checks the resolved round
    # specifically rather than asserting "v1.0.0" is absent from the output altogether.
    assert "round v1.1.0" in result.stdout


def test_nothing_to_audit_dies(run):
    run.round("1.0.0", audit=True)
    run.round("2.0.0", audit=True)
    result = run("thing")
    assert result.returncode == 1
    assert "nothing to audit" in result.stderr
    assert run.launched_argv() == []


def test_refuse_to_overwrite_existing_audit(run):
    run.round("1.0.0", audit=True)
    result = run("thing", "1.0.0")
    assert result.returncode == 1
    assert "delete it yourself" in result.stderr
    assert run.launched_argv() == []


def test_prose_positional_never_reaches_the_prompt(run):
    run.round("1.0.0", audit=False)
    result = run("thing", "and also fix everything")
    # The extra words are read as one version positional; it names no round, so the guard
    # fails before anything is built — the prose never reaches the prompt.
    assert result.returncode == 1
    assert run.launched_argv() == []


def test_prior_absent_interpolates_no_prior(run):
    run.round("1.0.0", audit=False)
    result = run("thing", "--dry-run")
    assert "prior round" not in result.stdout


# --- --dry-run -----------------------------------------------------------------


def test_dry_run_prints_command_without_launching(run):
    run.round("1.0.0", audit=False)
    result = run("thing", "--dry-run")
    assert result.returncode == 0
    assert "DRY RUN" in result.stdout
    assert run.launched_argv() == []


# --- the pin (Task 18) ---------------------------------------------------------


def test_dry_run_prints_the_pin_line(run):
    """`pin_enter` runs right after the `CORE_DIR` guard, ahead of every other use of
    `CORE_DIR` — this fixture's `pin.json` marks `run.root` as already its own pin, so the
    line reads `(inherited)`, not `(new)`."""
    run.round("1.0.0", audit=False)
    result = run("thing", "--dry-run")
    assert result.returncode == 0
    assert f"Pin: {run.pin_root} (inherited)" in result.stdout


def test_launch_audit_passes_no_audit_group_add_dir(run):
    """kaizen-audit's own group, when it resolves grouped, now reaches the run through the
    pin's plugin — not a second `--add-dir` this launcher used to assemble by hand."""
    group_dir = run.grouped_skill("g", "kaizen-audit")
    run.round("1.0.0", audit=False)
    result = run("thing", "--dry-run")
    assert result.returncode == 0
    assert str(group_dir.parents[2]) not in result.stdout   # <root>/skills/g, never granted


def test_host_root_add_dir_is_kept_where_it_was(run):
    run.round("1.0.0", audit=False)
    result = run("thing", "--dry-run")
    assert result.returncode == 0
    assert "--add-dir" in result.stdout
    assert str(run.host) in result.stdout


# --- the fixed prompt: outputs-only, skill not agent --------------------------


def test_run_invokes_the_kaizen_audit_skill_not_an_agent(run):
    run.round("1.0.0", audit=False)
    result = run("thing", "--dry-run")
    assert "kaizen-audit" in result.stdout
    # A token check, not a substring one: the pin delivery's own `--agents` (Task 7) is a
    # different flag that happens to contain "--agent" as a substring.
    assert "--agent" not in result.stdout.split()
    # The launch command must also carry the two launcher-family invariants named in the intent
    # (change_spec §Fixed prompt; tl_instruction Task 2 §5): --permission-mode auto — REQUIRED,
    # since a --bg run that hits a prompt stops forever — and --add-dir on the host repo, so <CORE>
    # doctrine and the symlinked SKILL.md resolve. Substrings (not "--permission-mode auto" as one
    # phrase) because --dry-run echoes each argv token %q-escaped and space-separated.
    assert "--permission-mode" in result.stdout
    assert "auto" in result.stdout
    assert "--add-dir" in result.stdout


def test_outputs_only_producing_stack_absent_from_prompt(run):
    """The interpolated values are exactly {skill, round dir, prior dir, surfacing fact} — no
    path under the audited skill's producing stack (SKILL.md, its authoring prompt, templates,
    loader) ever reaches the fixed prompt."""
    run.round("1.0.0", audit=False)
    result = run("thing", "--dry-run")
    assert "SKILL.md" not in result.stdout
    assert "template" not in result.stdout.lower()
    assert "loader" not in result.stdout.lower()


def test_surfacing_fact_is_a_caller_flag(run):
    """Read off the actual launched prompt (unescaped), not --dry-run's `%q`-escaped echo —
    a multi-word phrase like "surfaces the owner's own work: no" is space-escaped per word
    under `printf %q` and would never match a plain substring check."""
    run.round("1.0.0", audit=False)
    run("thing", "1.0.0")
    without_argv = run.launched_argv()
    without_prompt = without_argv[without_argv.index("--bg") + 1]
    assert "surfaces the owner's own work: no" in without_prompt

    run.round("2.0.0", audit=False)
    run("thing", "2.0.0", "--surfaces-owner-work")
    with_argv = run.launched_argv()
    with_prompt = with_argv[with_argv.index("--bg") + 1]
    assert "surfaces the owner's own work: yes" in with_prompt


# --- the fail-closed handoff: chain into fix-author, or halt+notify -----------


def test_chains_into_fix_author_on_landed_audit(run):
    d = run.round("1.0.0", audit=False)
    result = run("thing", "1.0.0", extra_env={"CLAUDE_WRITES_AUDIT_AT": str(d / "audit.md")})
    assert result.returncode == 0
    argv = run.fix_author_argv()
    assert argv == ["thing", "1.0.0"]


def test_halts_and_notifies_on_missing_audit(run):
    run.round("1.0.0", audit=False)     # no audit.md — the run never landed one
    notifier = run.tmp / "notify.sh"
    notifier.write_text("#!/usr/bin/env bash\nexit 0\n")
    notifier.chmod(0o755)
    result = run("thing", "1.0.0", extra_env={"LAUNCH_AUDIT_NOTIFIER": str(notifier)})
    assert result.returncode == 1
    assert run.fix_author_argv() == []
    watch_argv = run.watch_argv()
    assert "--notify" in watch_argv
    assert watch_argv[watch_argv.index("--notify") + 1] == str(notifier)


def test_audit_only_stops_after_the_audit(run):
    d = run.round("1.0.0", audit=False)
    result = run("thing", "1.0.0", "--audit-only",
                 extra_env={"CLAUDE_WRITES_AUDIT_AT": str(d / "audit.md")})
    assert result.returncode == 0
    assert run.fix_author_argv() == []


# --- family plumbing: --instance-root, --keep-awake, notifier-unset ----------


def test_instance_root_override_is_honoured(run):
    alt_root = run.tmp / "alt-instance"
    d = alt_root / ".claude" / "skills" / "thing" / "evidence" / "v1.0.0"
    d.mkdir(parents=True)
    (alt_root / ".providers.toml").write_text(_DELIVERED_PROVIDERS)
    empty_cwd = run.tmp / "elsewhere"
    empty_cwd.mkdir()
    result = run("--instance-root", str(alt_root), "thing", "--dry-run", cwd=empty_cwd)
    assert result.returncode == 0
    assert "v1.0.0" in result.stdout


def test_keep_awake_holds_caffeinate_across_the_foreground_watch(run):
    d = run.round("1.0.0", audit=False)
    result = run("thing", "1.0.0", "--keep-awake",
                 extra_env={"CLAUDE_WRITES_AUDIT_AT": str(d / "audit.md")})
    assert result.returncode == 0
    assert "Keep-awake:" in result.stdout or "caffeinate not found" in result.stdout


def test_notifier_unset_still_completes(run):
    d = run.round("1.0.0", audit=False)
    result = run("thing", "1.0.0", extra_env={
        "LAUNCH_AUDIT_NOTIFIER": "",
        "CLAUDE_WRITES_AUDIT_AT": str(d / "audit.md"),
    })
    assert result.returncode == 0
    assert run.fix_author_argv() == ["thing", "1.0.0"]
    assert "--notify" not in run.watch_argv()


# --- the resolver: grouped layout, not-found, ambiguous, missing resolver ----


def test_a_grouped_skill_resolves_and_the_prompt_names_the_grouped_round(run):
    d = run.grouped_round("1.0.0")
    result = run("thing", "--dry-run")
    assert result.returncode == 0
    assert str(d) in result.stdout


def test_grouped_fixture_builds_no_flat_path(run):
    run.grouped_round("1.0.0")
    assert not (run.root / ".claude" / "skills").exists()


def test_the_instance_root_override_still_honours_the_flat_layout(run):
    """condition 2's own test, unchanged — must keep passing after the resolver adoption."""
    alt_root = run.tmp / "alt-instance"
    d = alt_root / ".claude" / "skills" / "thing" / "evidence" / "v1.0.0"
    d.mkdir(parents=True)
    (alt_root / ".providers.toml").write_text(_DELIVERED_PROVIDERS)
    empty_cwd = run.tmp / "elsewhere"
    empty_cwd.mkdir()
    result = run("--instance-root", str(alt_root), "thing", "--dry-run", cwd=empty_cwd)
    assert result.returncode == 0
    assert "v1.0.0" in result.stdout


def test_unknown_skill_dies_before_launching_naming_no_layout(run):
    result = run("nope")
    assert result.returncode != 0
    assert "no skill at" in result.stderr
    assert str(run.root) in result.stderr          # the root searched
    assert "'nope'" in result.stderr                # the skill name
    assert ".claude/skills" not in result.stderr
    assert "skills/" not in result.stderr
    assert run.launched_argv() == []


def test_stderr_noise_on_a_clean_resolve_never_reaches_the_captured_path(run):
    """The resolver's own stderr is folded into the captured value today (2>&1), so any text a
    future resolver version prints on a successful exit would land INSIDE skill_dir. A stub
    resolver here — exit 0, a real directory on stdout, a line of noise on stderr — proves the
    fold does not happen: the launcher proceeds against the stdout path alone."""
    d = run.round("1.0.0", audit=False)
    skill_dir = d.parents[1]
    stub = run.tmp / "stub_resolver.py"
    stub.write_text(
        "import sys\n"
        f"print({str(skill_dir)!r})\n"
        "print('resolver: a future warning', file=sys.stderr)\n"
    )
    result = run("thing", "--dry-run", extra_env={"LAUNCH_AUDIT_RESOLVER": str(stub)})
    assert result.returncode == 0, result.stderr
    assert "resolver: a future warning" not in result.stdout
    assert str(skill_dir) in result.stdout


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


def test_a_missing_resolver_dies_as_this_launcher_not_a_traceback(run):
    run.remove_resolver()
    result = run("thing")
    assert result.returncode != 0
    assert "launch-audit:" in result.stderr
    assert "usage: launch-audit.sh" in result.stderr
    assert "Traceback" not in result.stderr
    assert run.launched_argv() == []
# --- the one core-relative path this launcher has ---------------------------------
#
# `launch-audit.sh` is flat in `<CORE>/tools/`, so its watcher default is `$SCRIPT_DIR/watch_agent.py`
# — the other of the two path shapes, and the one `kensaiapp_structure.md` § Owner-run launcher folder
# calls the failure that does not announce itself. It has NO `$DETACH_LIB`, deliberately: it runs the
# watcher in the FOREGROUND under the utility form (`caffeinate -i -s python3 "$WATCHER" …`, no pid
# anywhere, nothing detached), so there is no detach-and-return tail for the shared home to serve and
# no second path to prove. Asserting one here would be checking for something correctly absent.


def test_watcher_is_found_beside_the_script_when_the_env_override_is_unset(run):
    """The only test here that drops `$LAUNCH_AUDIT_WATCHER`. Every other one stubs it and would
    stay green against a default expressed with the wrong walk — and a wrong walk here is quiet in
    its own way: `python3 "$WATCHER" … || true` swallows the failure, so the launcher carries on to
    its fail-closed artifact check and exits 0 having watched nothing.

    The stub is written to the launcher's own directory, which IS the path under test, and it exits
    immediately — the real watcher would hold this test open for its whole appear window, because
    this launcher waits on it rather than detaching it."""
    (run.script.parent / "watch_agent.py").write_text(WATCH_STUB)
    run.env.pop("LAUNCH_AUDIT_WATCHER", None)
    run.env["WATCH_ARGV_LOG"] = str(run.tmp / "default_path_watch_argv.log")

    run.skill()
    d = run.round("1.0.0", audit=False)
    result = run("thing", "1.0.0", "--audit-only",
                 extra_env={"CLAUDE_WRITES_AUDIT_AT": str(d / "audit.md")})

    assert result.returncode == 0
    argv = (run.tmp / "default_path_watch_argv.log").read_text().splitlines()
    assert argv, (
        "the watcher at the default path was never reached — the launcher failed to resolve "
        f"watch_agent.py beside itself. stdout: {result.stdout}"
    )
    assert argv[argv.index("--reporter") + 1] == "generic"


# --- the provider: this launcher's entry in .providers.toml ------------------------------------
#
# The launcher asks the one reader for `launchers.launch-audit` right after its usage check and
# runs on what it answers. It reads that one entry and no other: the fix author it chains into
# reads its own. The `claude --bg` argv carries no provider token, so what these cases look at is
# the call the launcher makes to the adapter (`run.adapter_calls()`), which the fixture's
# recording stand-in logs. The instance's own `.providers.toml` is the only file a case can
# change: no variable or flag selects the file.


def test_a_missing_entry_refuses_and_launches_nothing(run):
    run.set_providers(_toml_without(_ENTRY))
    watcher = run.tmp / "any_call_watcher.py"
    watcher.write_text(ANY_CALL_WATCH_STUB)
    watcher_log = run.tmp / "watch_any.log"
    run.round("1.0.0")

    result = run("thing", "1.0.0", extra_env={
        "LAUNCH_AUDIT_WATCHER": str(watcher), "WATCH_ANY_LOG": str(watcher_log)})

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr
    assert str(run.providers_file) in result.stderr
    assert run.launched_argv() == []                 # the stub `claude` received no argv
    assert run.adapter_calls() == []                 # the adapter was never called
    assert not watcher_log.exists()                  # no watcher call at all, not even --list-ids
    assert run.fix_author_argv() == []               # the fix author was never reached


def test_a_missing_entry_refuses_a_dry_run_too(run):
    run.set_providers(_toml_without(_ENTRY))
    run.round("1.0.0")

    result = run("thing", "--dry-run")

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr
    assert "DRY RUN" not in result.stdout
    assert run.adapter_calls() == []


def test_the_delivered_entry_puts_provider_claude_on_the_adapter_call(run):
    run.round("1.0.0")

    result = run("thing", "--dry-run")

    assert result.returncode == 0
    calls = run.adapter_calls()
    assert len(calls) == 1
    assert calls[0][calls[0].index("--provider") + 1] == "claude"
    assert "DRY RUN — would launch:" in result.stdout
    assert "--bg" in result.stdout


def test_the_claude_launch_grants_kaizen_audit(run):
    # This harness pins an isolated tree with no skill groups, so the grant is observed on the
    # argv the launcher hands the adapter. `kaizen-audit` declares `depends-on: kensaiapp-auditor`
    # (an agent), which adds no group — that half is `test_pin.py`'s.
    run.round("1.0.0")

    result = run("thing", "--dry-run")

    assert result.returncode == 0
    (call,) = run.adapter_calls()
    assert call.count("--grant-skill") == 1
    assert call[call.index("--grant-skill") + 1] == "kaizen-audit"


def test_an_entry_naming_an_unknown_provider_is_refused_by_name(run):
    run.set_providers(_toml_with(_ENTRY, "grok"))
    run.round("1.0.0")

    result = run("thing", "--dry-run")

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr and "grok" in result.stderr
    assert "DRY RUN" not in result.stdout
    assert run.adapter_calls() == []


def test_an_entry_naming_codex_is_refused_by_name(run):
    run.set_providers(_toml_with(_ENTRY, "codex"))
    run.round("1.0.0")

    result = run("thing", "--dry-run")

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr and "codex" in result.stderr
    assert "DRY RUN" not in result.stdout
    assert run.adapter_calls() == []


def test_a_missing_provider_file_is_refused_naming_the_file(run):
    run.providers_file.unlink()
    run.round("1.0.0")

    result = run("thing", "--dry-run")

    assert result.returncode != 0
    assert str(run.providers_file) in result.stderr
    assert "cp .providers.toml.example .providers.toml" in result.stderr   # CP-486
    assert "DRY RUN" not in result.stdout
    assert run.adapter_calls() == []


def test_the_force_variable_is_ignored(run):
    run.round("1.0.0")

    result = run("thing", "--dry-run", extra_env={"KENSAIAPP_AGENT_PROVIDER": "codex"})

    assert result.returncode == 0
    calls = run.adapter_calls()
    assert calls[0][calls[0].index("--provider") + 1] == "claude"


def test_audit_reads_only_its_own_entry(run):
    """A copy lacking only the fix author's entry: the audit still launches and still reaches the
    fix author, which is where that entry is read (and, here, only a stub)."""
    run.set_providers(_toml_without("launch-fix-author"))
    d = run.round("1.0.0")

    result = run("thing", "1.0.0", extra_env={"CLAUDE_WRITES_AUDIT_AT": str(d / "audit.md")})

    assert result.returncode == 0
    assert run.launched_argv() != []                 # the audit launched
    assert run.fix_author_argv() == ["thing", "1.0.0"]


def test_audit_only_never_reaches_the_fix_author(run):
    run.set_providers(_toml_without("launch-fix-author"))
    d = run.round("1.0.0")

    result = run("thing", "1.0.0", "--audit-only",
                 extra_env={"CLAUDE_WRITES_AUDIT_AT": str(d / "audit.md")})

    assert result.returncode == 0
    assert run.fix_author_argv() == []


def test_a_chained_fix_author_without_its_entry_refuses_and_the_audit_stays(run):
    """The real fix author behind a landed audit, in a copy lacking only its own entry: it refuses
    at its first read, naming the entry, and the audit launcher hands that exit through. The audit
    that already landed is left where it is."""
    real_fix_author = run.script.parent / "launch-fix-author.sh"
    shutil.copy2(_TOOLS_DIR / "launch-fix-author.sh", real_fix_author)   # over the fixture's stub
    real_fix_author.chmod(0o755)
    run.set_providers(_toml_without("launch-fix-author"))
    d = run.round("1.0.0")

    result = run("thing", "1.0.0", extra_env={"CLAUDE_WRITES_AUDIT_AT": str(d / "audit.md")})

    assert run.launched_argv() != []                 # the audit ran
    assert result.returncode != 0
    assert "launchers.launch-fix-author" in result.stderr
    assert (d / "audit.md").exists()                 # the landed audit stays
    assert run.fix_author_argv() == []               # the stub was replaced, never reached


def test_a_missing_provider_reader_is_refused_by_name(run):
    """The guard is a rule of its own: without it the missing file surfaces as python3's own
    complaint, which names no launcher and no reader."""
    (run.script.parent / "providers.py").unlink()
    run.round("1.0.0")

    result = run("thing", "--dry-run")

    assert result.returncode != 0
    assert f"no provider reader at {run.script.parent / 'providers.py'}" in result.stderr
    assert run.adapter_calls() == []


def test_a_missing_intelligence_resolver_is_refused_by_name(run):
    """The reader imports the resolver, so its absence would otherwise be a traceback."""
    (run.script.parent / "run_intelligence.py").unlink()
    run.round("1.0.0")

    result = run("thing", "--dry-run")

    assert result.returncode != 0
    resolver = run.script.parent / "run_intelligence.py"
    assert f"no intelligence resolver at {resolver}" in result.stderr
    assert "Traceback" not in result.stderr
    assert run.adapter_calls() == []


# --- the provider: what the spec states and the cases above leave unasserted -------------------
#
# Added by the integrity review (development-code-integrity), each from the rule it names.


def test_a_provider_file_that_is_not_toml_is_refused_naming_the_file(run):
    """CP-350: a file that cannot be read as TOML is refused, naming its path."""
    run.set_providers("[launchers\nlaunch-audit = = claude\n")
    run.round("1.0.0")

    result = run("thing", "--dry-run")

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
    assert run.fix_author_argv() == []


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

    result = run("thing", "--dry-run")

    assert result.returncode != 0
    assert f"launchers.{_ENTRY}" in result.stderr
    assert str(run.providers_file) in result.stderr
    assert all(str(decoy) not in result.stderr for decoy in decoys)
    assert run.adapter_calls() == []


def test_an_instance_that_binds_its_own_core_adds_no_host(run):
    """The host itself binds `CORE=core/`, relatively: it is its own host, so nothing is added."""
    (run.root / ".env").write_text("CORE=core/\n")
    run.round("1.0.0", audit=False)
    result = run("thing", "--dry-run")
    assert result.returncode == 0
    assert str(run.host) not in result.stdout


def test_an_instance_with_no_env_file_adds_no_host(run):
    (run.root / ".env").unlink()
    run.round("1.0.0", audit=False)
    result = run("thing", "--dry-run")
    assert result.returncode == 0
    assert str(run.host) not in result.stdout
