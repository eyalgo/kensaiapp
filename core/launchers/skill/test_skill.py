"""Contract tests for `skill/launcher.sh` — the one launcher for any skill carrying a `launcher.md`.

The launcher names no skill, so every fixture here writes its own `launcher.md` into a `tmp_path`
instance, and the suite pins what the launcher's header states: the fields, what an argument
name means, the refusals — of a call and of a declaration — before anything spawns, the fixed prompt
read off the spawned argv, and the shared telemetry and completion-watch tails. Two tests read a
real declaration — `skills/pm/.claude/skills/tobiishi-open/launcher.md`, the first skill to declare a
launch, `nemawashi-pick`'s and `nemawashi-unpick`'s beside it,
`skills/scrum-master/.claude/skills/shukuba-retire/launcher.md` and
`skills/cpo/.claude/skills/project-agari/launcher.md` — so the files that ship are held to the same contract as the
fixtures. Every shipped **Reporter:** is also held to the registry and to what it reads.

Isolation: the real script at its real location, an independent `tmp_path` tree standing in for a
whole instance, and stubs for `claude`, the watcher, the notifier and `caffeinate`.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shlex
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

import pytest

from kensaiapp_launchers_conftest import (
    _PRINT_RUN_HEAD,
    assert_launch_recorded_its_identity,
    _granted_dirs,
    _plugin_skills,
    _prompt_of,
    _provider_argv,
    _without_session_id,
)

_SCRIPT = Path(__file__).resolve().parent / "launcher.sh"
_LAUNCHERS_DIR = _SCRIPT.parent.parent
_CORE_DIR = _LAUNCHERS_DIR.parent
_REPO = _CORE_DIR.parent
_TOBIISHI_OPEN_LAUNCHER_MD = _REPO / "skills" / "pm" / ".claude" / "skills" / "tobiishi-open" / "launcher.md"
_NEMAWASHI_PICK_LAUNCHER_MD = _REPO / "skills" / "pm" / ".claude" / "skills" / "nemawashi-pick" / "launcher.md"
_NEMAWASHI_UNPICK_LAUNCHER_MD = _REPO / "skills" / "pm" / ".claude" / "skills" / "nemawashi-unpick" / "launcher.md"
_SHUKUBA_RETIRE_LAUNCHER_MD = (
    _REPO / "skills" / "scrum-master" / ".claude" / "skills" / "shukuba-retire" / "launcher.md"
)
_TOBIISHI_DROP_LAUNCHER_MD = (
    _REPO / "skills" / "pm" / ".claude" / "skills" / "tobiishi-drop" / "launcher.md"
)


def _group_agent(name):
    """The agent `name` where the shipped tree holds it: its own group, `skills/<name>/`."""
    return _REPO / "skills" / name / ".claude" / "agents" / f"{name}.md"


_SCRUM_MASTER_AGENT_MD = _group_agent("scrum-master")
_PM_AGENT_MD = _group_agent("pm")
_DEVELOPMENT_IMPLEMENTATION_LAUNCHER_MD = (
    _REPO / "skills" / "developer" / ".claude" / "skills" / "development-implementation" / "launcher.md"
)

CLAUDE_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" > "$CLAUDE_ARGV_LOG"
printf '%s\\n' '{"type":"result","subtype":"success","is_error":false,"result":"ok"}'
"""

from kensaiapp_launchers_conftest import CODEX_STUB

GEMINI_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" > "$GEMINI_ARGV_LOG"
printf '%s\\n' '{"type":"result","subtype":"success","is_error":false,"result":"ok"}'
"""

WATCHER_STUB = """import sys
if "--list-ids" in sys.argv:
    print("pre1,pre2")
else:
    with open(__import__("os").environ["WATCHER_ARGV_LOG"], "w") as fh:
        fh.write("\\n".join(sys.argv[1:]))
    # Held only for a case that asserts keep-awake PRESENCE. The watcher's exit is what releases
    # caffeinate, so a watcher that exits before the caffeinate stub has recorded makes that record
    # depend on a race. The hold ends on the record or at the case's teardown, never on a clock.
    import os, time
    hold_until = os.environ.get("WATCHER_STUB_HOLD_UNTIL")
    release = os.environ.get("WATCHER_STUB_RELEASE")
    while hold_until and not os.path.exists(release):
        if os.path.exists(hold_until) and open(hold_until).read().strip():
            break
        time.sleep(0.05)
"""

NOTIFIER_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" >> "$NOTIFIER_ARGV_LOG"
"""

# The keep-awake bind is detached, so its caffeinate lands after the launcher returns. Under a
# loaded parallel run (`-n 32`, `core/pytest.ini`) the stub's first exec queues behind every other
# first exec on the machine — `warm_executables` (`core/launchers/conftest.py`) takes that out of
# the window — and a presence case also holds its watcher until the record exists. A presence
# check waits this long; an absence check passes `wait=2.5`, since it always waits its whole
# budget out.
_KEEPAWAKE_WAIT = 10.0

CAFFEINATE_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" >> "$CAFFEINATE_ARGV_LOG"
"""


def _md(
    *,
    agent="pm",
    model=None,
    effort=None,
    arguments="<project>",
    prompt="invoke the demo skill for the {project} project.",
    reporter=None,
    reads=None,
    requires=None,
):
    """A launcher.md with prose around its field lines — the prose mentions a label mid-line, which
    the launcher must never read as a field."""
    lines = [
        "# demo — unattended launch",
        "",
        "Prose for a reader. A **Prompt:** written mid-line like this one is never a field.",
        "",
    ]
    if agent is not None:
        lines.append(f"**Agent:** {agent}")
    if model is not None:
        lines.append(f"**Model:** {model}")
    if effort is not None:
        lines.append(f"**Effort:** {effort}")
    if arguments is not None:
        lines.append(f"**Arguments:** {arguments}")
    if prompt is not None:
        lines.append(f"**Prompt:** {prompt}")
    if reporter is not None:
        lines.append(f"**Reporter:** {reporter}")
    if reads is not None:
        lines.append(f"**Reads:** {reads}")
    if requires is not None:
        lines.append(f"**Requires:** {requires}")
    lines += ["", "More prose after the fields."]
    return "\n".join(lines) + "\n"


# The run is a detached process: its stub records after the launcher returns, and under the
# suite's parallel load its first exec can queue behind other workers — the same ten-second budget
# the Codex cases use. A launch that was refused, or only dry-run, spawned nothing and never will,
# so its absence is read after a short settle rather than the whole budget.
_DETACHED_WAIT = 10.0
_ABSENT_WAIT = 0.5


@pytest.fixture
def run(tmp_path, warm_executables, _session_pin):
    """`run(*cli_args) -> CompletedProcess`, invoking the real launcher with `tmp_path` as its cwd —
    how the launcher resolves its instance root. `run.skill(name, md, group=None)` writes a skill
    directory, flat or under `skills/<group>/` (with a launcher.md unless `md` is None); `run.project(name, …)` writes a project; the
    `*_argv()` helpers read back what the stubs recorded. `run.core_dir` is the session pin's own
    `core/` — every `<CORE>`-derived path in a real (non-isolated) launch resolves there, since
    the launcher enters that pin before anything else reads `CORE_DIR` (Task 12). `run.pin_root`
    is that pin's own top directory — a Claude launch's own trailing `--add-dir <pin root>`
    (Task 13)."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, content in (
        ("claude", CLAUDE_STUB),
        ("caffeinate", CAFFEINATE_STUB),
    ):
        warm_executables.link(bin_dir / name, content)
    codex_stub = bin_dir / "codex"
    codex_stub.write_text(CODEX_STUB)
    codex_stub.chmod(0o755)
    gemini_stub = bin_dir / "agy"
    gemini_stub.write_text(GEMINI_STUB)
    gemini_stub.chmod(0o755)

    watcher_stub = tmp_path / "watch_agent_stub.py"
    watcher_stub.write_text(WATCHER_STUB)
    notifier_stub = warm_executables.link(tmp_path / "notify_stub.sh", NOTIFIER_STUB)

    argv_log = tmp_path / "claude_argv.log"
    codex_argv_log = tmp_path / "codex_argv.log"
    gemini_argv_log = tmp_path / "gemini_argv.log"
    watcher_log = tmp_path / "watcher_argv.log"
    caffeinate_log = tmp_path / "caffeinate_argv.log"
    watcher_release = tmp_path / "watcher_release"

    home = tmp_path / "home"
    home.mkdir()
    # The instance's own provider file: an unforced launch reads it at the instance root.
    (tmp_path / ".providers.toml").write_text(_DELIVERED_PROVIDERS)
    agents = tmp_path / ".claude" / "agents"
    agents.mkdir(parents=True)
    # No `model:` — an agent file carries none (CP-180), and a run's intelligence is its skill's.
    (agents / "pm.md").write_text("---\nname: pm\n---\n")

    env = dict(os.environ)
    # The no-flag cases assert the `launchers.skill` entry's provider (`claude` as delivered). A
    # session that exports KENSAIAPP_AGENT_PROVIDER would otherwise rewrite every one of them.
    env.pop("KENSAIAPP_AGENT_PROVIDER", None)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    # A path nothing occupies, so the suite never reads this machine's real telemetry endpoint.
    env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(tmp_path / "no-instrument-endpoint")
    env["CLAUDE_ARGV_LOG"] = str(argv_log)
    env["CODEX_ARGV_LOG"] = str(codex_argv_log)
    env["GEMINI_ARGV_LOG"] = str(gemini_argv_log)
    env["WATCHER_ARGV_LOG"] = str(watcher_log)
    env["NOTIFIER_ARGV_LOG"] = str(tmp_path / "notifier_argv.log")
    env["CAFFEINATE_ARGV_LOG"] = str(caffeinate_log)
    env["WATCHER_STUB_RELEASE"] = str(watcher_release)
    env["LAUNCH_SKILL_WATCHER"] = str(watcher_stub)
    env["LAUNCH_SKILL_NOTIFIER"] = str(notifier_stub)
    # The skills are looked up under the host root; here the host and the instance are one tree.
    env["LAUNCH_SKILL_SKILLS_ROOT"] = str(tmp_path)
    env["HOME"] = str(home)
    env.pop("KENSAIAPP_NOTIFIER", None)

    def _run(*cli_args, script=_SCRIPT, cwd=None):
        return subprocess.run(
            [str(script), *cli_args],
            cwd=cwd or str(tmp_path),
            capture_output=True,
            text=True,
            env=env,
        )

    def _skill(name, md, group=None):
        base = tmp_path / "skills" / group if group else tmp_path
        skill_dir = base / ".claude" / "skills" / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\n---\n")
        if md is not None:
            (skill_dir / "launcher.md").write_text(md)
        return skill_dir

    def _project(name, product_path=None, card=True):
        project_dir = tmp_path / "system" / "projects" / name
        project_dir.mkdir(parents=True)
        if card:
            text = f"# {name}\n"
            if product_path is not None:
                text += f"\n**Product path:** {product_path}   <!-- where the product lives -->\n"
            (project_dir / "project.md").write_text(text)
        return project_dir

    def _hold_watcher_until_kept_awake():
        env["WATCHER_STUB_HOLD_UNTIL"] = str(caffeinate_log)

    def _launched_argv(wait=_DETACHED_WAIT):
        # The run is a detached process, so what its stub recorded lands after the launcher returns.
        return _poll(argv_log, wait)

    def _codex_argv(wait=_DETACHED_WAIT):
        return _poll(codex_argv_log, wait)

    def _gemini_argv(wait=_DETACHED_WAIT):
        return _poll(gemini_argv_log, wait)

    def _poll(log, wait=2.5):
        for _ in range(int(wait / 0.05)):
            if log.exists() and log.read_text():
                return log.read_text().splitlines()
            time.sleep(0.05)
        return []

    _run.root = tmp_path
    _run.home = home
    _run.env = env
    _run.core_dir = _session_pin.core
    _run.pin_root = _session_pin.root
    _run.hold_watcher_until_kept_awake = _hold_watcher_until_kept_awake
    _run.skill = _skill
    _run.project = _project
    _run.launched_argv = _launched_argv
    _run.launched_prompt = lambda: _prompt_of(_launched_argv())
    _run.codex_argv = _codex_argv
    _run.gemini_argv = _gemini_argv
    _run.watcher_argv = lambda: _poll(watcher_log)
    _run.caffeinate_argv = lambda wait=_KEEPAWAKE_WAIT: _poll(caffeinate_log, wait)
    yield _run
    watcher_release.touch()


@pytest.fixture
def demo(run):
    """The common case: a `demo` skill taking `<project>`, and a project `some-project` to take."""
    run.skill("demo", _md())
    run.project("some-project")
    return run


def _dry_run_argv(stdout):
    """The provider argv a dry run printed, from the provider's own name on."""
    for line in stdout.splitlines():
        tokens = _provider_argv(shlex.split(line.strip())) if line.strip() else []
        if tokens[:1] in (["claude"], ["codex"], ["codex-skill"], ["agy"]):
            return tokens
    raise AssertionError(f"no provider command in:\n{stdout}")


def _registered_reporter_names():
    registry = _CORE_DIR / "tools" / "reporters.py"
    tree = ast.parse(registry.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "REGISTRY" for t in node.targets
        ):
            return {k.value for k in node.value.keys if isinstance(k, ast.Constant)}
    raise AssertionError(f"no REGISTRY mapping found in {registry}")


def _isolated_core(tmp_path_factory, *tools):
    """A copy of the launcher at `<tmp>/core/launchers/skill/`, beside a `<tmp>/core/tools/` holding
    only the named real tools plus the machinery every launcher and every Claude launch now
    unconditionally reaches: the pin (`pin_enter` sources `pin_run.sh`, which shells out to
    `pin.py`) and the one Claude builder (`agent_run.py`, and its own three module imports
    `model_assignment.py`, `task_context.py` and `env_file.py`) and the provider reader — how an
    absent shared home is simulated without editing the launcher. `<tmp>` itself carries a
    `pin.json`, so `pin_enter` finds this tree already
    its own pin and neither re-execs nor copies anything: what the test built is exactly what runs."""
    isolated = tmp_path_factory.mktemp("isolated_core")
    core_root = isolated / "core"
    launcher_dir = core_root / "launchers" / "skill"
    launcher_dir.mkdir(parents=True)
    copied = launcher_dir / "launcher.sh"
    copied.write_text(_SCRIPT.read_text())
    copied.chmod(0o755)
    tools_dir = core_root / "tools"
    tools_dir.mkdir()
    always = ("pin.py", "pin_run.sh", "agent_run.py", "codex_skill_run.py", "model_assignment.py", "task_context.py",
              "hook_wiring.py",
              "env_file.py", "detached_run.sh", "intelligence.py", "run_intelligence.py",
              "providers.py")
    for tool in dict.fromkeys((*always, *tools)):
        shutil.copy(_CORE_DIR / "tools" / tool, tools_dir / tool)
    (isolated / "pin.json").write_text(
        json.dumps({"id": "isolated", "source_host_root": str(isolated), "created": "1970-01-01T00:00:00+00:00"})
        + "\n"
    )
    return copied


# --- the provider: the flag, else the variable, else the launcher's entry in .providers.toml -----

# The delivered text is the tracked template at the instance root, which no suite leans a live
# `.providers.toml` for: that file is untracked and absent from a fresh checkout.
_DELIVERED_PROVIDERS = (_CORE_DIR.parent / ".providers.toml.example").read_text()
_ISOLATED_TOOLS = ("skill_path.py", "detach_watcher.sh", "detach_process_watcher.sh",
                   "instrument_run.sh", "watch_process.py")


def _instance_provider_file(run, text):
    """The instance's own `.providers.toml` — the launcher's cwd is the instance — holding
    `text` (removed when `None`). The launcher is the real one, so the file the reader reads is
    the instance's and nothing in a core copy."""
    file = run.root / ".providers.toml"
    if text is None:
        file.unlink(missing_ok=True)
    else:
        file.write_text(text)
    return _SCRIPT


def _skill_entry(value):
    """The delivered file with only `launchers.skill` changed to `value`."""
    assert '\nskill = "claude"\n' in _DELIVERED_PROVIDERS
    return _DELIVERED_PROVIDERS.replace('\nskill = "claude"\n', f'\nskill = "{value}"\n', 1)


def _publish_endpoint(run):
    """A published telemetry endpoint, so a dry run prints its `Telemetry:` line."""
    endpoint = run.root / "published-endpoint"
    endpoint.write_text("http://127.0.0.1:4318\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint)


def test_unforced_dry_run_goes_to_the_skills_entry(demo):
    result = demo("demo", "some-project", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "Provider:  claude" in result.stdout
    assert _dry_run_argv(result.stdout)[:2] == ["claude", "--print"]


def test_forced_codex_dry_run_goes_to_codex(demo):
    _publish_endpoint(demo)
    result = demo("demo", "some-project", "--provider", "codex", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "Provider:  codex" in result.stdout
    assert _dry_run_argv(result.stdout)[0] == "codex-skill"
    assert "kensai.provider=codex" in result.stdout


def test_a_steps_entry_does_not_govern_the_skill_launcher(demo):
    text = _DELIVERED_PROVIDERS.replace('\ndesign = "claude"\n', '\ndesign = "codex"\n', 1)
    assert text != _DELIVERED_PROVIDERS
    script = _instance_provider_file(demo, text)

    result = demo("demo", "some-project", "--dry-run", script=script)

    assert result.returncode == 0, result.stderr
    assert "Provider:  claude" in result.stdout


def test_the_skill_entry_decides_an_unforced_launch(demo):
    _publish_endpoint(demo)
    script = _instance_provider_file(demo, _skill_entry("gemini"))

    result = demo("demo", "some-project", "--dry-run", script=script)

    assert result.returncode == 0, result.stderr
    assert "Provider:  gemini" in result.stdout
    assert _dry_run_argv(result.stdout)[0] == "agy"
    assert "kensai.provider=gemini" in result.stdout


def test_an_empty_variable_is_unforced(demo):
    demo.env["KENSAIAPP_AGENT_PROVIDER"] = ""

    result = demo("demo", "some-project", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "Provider:  claude" in result.stdout


def test_the_variable_forces_without_reading_the_file(demo):
    demo.env["KENSAIAPP_AGENT_PROVIDER"] = "gemini"
    without_entry = _DELIVERED_PROVIDERS.replace('\nskill = "claude"\n', "\n", 1)
    script = _instance_provider_file(demo, without_entry)

    result = demo("demo", "some-project", "--dry-run", script=script)

    assert result.returncode == 0, result.stderr
    assert "Provider:  gemini" in result.stdout


def test_a_forced_launch_on_a_copy_without_the_entry_goes_to_codex(demo):
    without_entry = _DELIVERED_PROVIDERS.replace('\nskill = "claude"\n', "\n", 1)
    assert without_entry != _DELIVERED_PROVIDERS

    for text in (without_entry, None):
        script = _instance_provider_file(demo, text)
        result = demo("demo", "some-project", "--provider", "codex", "--dry-run", script=script)

        assert result.returncode == 0, result.stderr
        assert "Provider:  codex" in result.stdout
        assert _dry_run_argv(result.stdout)[0] == "codex-skill"


def test_an_explicit_empty_provider_flag_is_refused_as_today(demo):
    result = demo("demo", "some-project", "--provider", "", "--dry-run")

    assert result.returncode != 0
    assert "unknown provider ''" in result.stderr
    _nothing_spawned(demo)


@pytest.mark.parametrize("contents", [b"[launchers\n", b"\xff", None,
                                       b'[launchers]\nskill = "grok"\n'],
                         ids=["malformed-toml", "non-utf8", "directory", "unknown-entry"])
@pytest.mark.parametrize("force_channel", ["flag", "environment"])
def test_a_force_bypasses_an_unreadable_or_invalid_provider_file(
    demo, contents, force_channel
):
    """CP-296: both force channels reach Codex regardless of the instance file's condition."""
    script = _instance_provider_file(demo, None)
    path = demo.root / ".providers.toml"
    if contents is None:
        path.mkdir()
    else:
        path.write_bytes(contents)
    if force_channel == "environment":
        demo.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"
    args = ("--provider", "codex") if force_channel == "flag" else ()

    result = demo("demo", "some-project", *args, "--dry-run", script=script)

    assert result.returncode == 0, result.stderr
    assert "Provider:  codex" in result.stdout
    assert _dry_run_argv(result.stdout)[0] == "codex-skill"
    assert ".providers.toml" not in result.stderr


# --- the shipped declaration -----------------------------------------------------------------


def test_the_shipped_tobiishi_open_declaration_launches_under_pm_with_its_fixed_prompt(run):
    run.skill("tobiishi-open", _TOBIISHI_OPEN_LAUNCHER_MD.read_text())
    run.project("some-project")

    result = run("tobiishi-open", "some-project")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert argv[:4] == _PRINT_RUN_HEAD
    assert argv[argv.index("--permission-prompts") + 1] == "none"
    assert _prompt_of(argv) == "invoke the tobiishi-open skill for the some-project project."
    assert argv[argv.index("--agent") + 1] == "pm"
    assert "--model" not in argv
    assert argv[argv.index("--permission-mode") + 1] == "auto"
    assert "--dangerously-skip-permissions" not in argv


_IMPLEMENTATION_PROMPT = (
    "invoke the development-implementation skill for the some-project project, "
    "change key 2026-09-19_some-change."
)


def _implementation_run(run, *cli):
    (run.root / ".claude" / "agents" / "developer.md").write_text(
        "---\nname: developer\nmodel: sonnet\n---\n"
    )
    run.skill("development-implementation", _DEVELOPMENT_IMPLEMENTATION_LAUNCHER_MD.read_text())
    run.project("some-project")
    return run("development-implementation", "some-project", "2026-09-19_some-change", *cli)


def test_development_implementation_without_after_launches_todays_prompt(run):
    result = _implementation_run(run)

    assert result.returncode == 0, result.stderr
    assert run.launched_prompt() == _IMPLEMENTATION_PROMPT


def test_development_implementation_with_after_scopes_the_batch(run):
    result = _implementation_run(run, "3")

    assert result.returncode == 0, result.stderr
    prompt = run.launched_prompt()
    assert prompt.startswith(_IMPLEMENTATION_PROMPT)
    # The launcher substitutes and does not compute, so the start is stated as `3+1`, not `4`.
    assert prompt[len(_IMPLEMENTATION_PROMPT):] == (
        " Tasks 1–3 are committed; start at task 3+1."
    )


def test_an_after_that_is_path_shaped_is_refused(run):
    result = _implementation_run(run, "a/b")

    assert result.returncode != 0
    assert "<after> 'a/b' looks like a path" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


_DEVELOPMENT_SPECS_DIR = (
    _REPO / "skills" / "product-owner" / ".claude" / "skills" / "development-specs"
)


def test_a_shipped_declaration_launches_on_its_intelligence(run):
    # The real declaration and the real intelligence file, placed where the shipped tree puts them,
    # launched for real: the model and the effort on the command are the file's, once each.
    agents = run.root / ".claude" / "agents"
    shutil.copy(_group_agent("product-owner"), agents / "product-owner.md")
    skill_dir = run.skill("development-specs", (_DEVELOPMENT_SPECS_DIR / "launcher.md").read_text(),
                          group="product-owner")
    (skill_dir / "intelligence").mkdir()
    shutil.copy(
        _DEVELOPMENT_SPECS_DIR / "intelligence" / "claude.md",
        skill_dir / "intelligence" / "claude.md",
    )
    run.project("some-project")

    result = run("development-specs", "some-project")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert argv.count("--model") == 1 and argv[argv.index("--model") + 1] == "claude-opus-5-5"
    assert argv.count("--effort") == 1 and argv[argv.index("--effort") + 1] == "high"


def test_the_shipped_nemawashi_pick_declaration_launches_under_pm_with_its_fixed_prompt(run):
    run.skill("nemawashi-pick", _NEMAWASHI_PICK_LAUNCHER_MD.read_text())
    run.project("some-project")

    result = run("nemawashi-pick", "some-project")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert argv[:4] == _PRINT_RUN_HEAD
    assert argv[argv.index("--permission-prompts") + 1] == "none"
    assert _prompt_of(argv) == "invoke the nemawashi-pick skill for the some-project project."
    assert argv[argv.index("--agent") + 1] == "pm"
    assert "--model" not in argv
    assert argv[argv.index("--permission-mode") + 1] == "auto"
    assert "--dangerously-skip-permissions" not in argv


def test_the_shipped_nemawashi_unpick_declaration_quotes_the_reason_and_is_granted_its_group(run):
    run.skill("nemawashi-unpick", _NEMAWASHI_UNPICK_LAUNCHER_MD.read_text(), group="pm")
    run.project("some-project")

    result = run("nemawashi-unpick", "some-project", "the station waits on an upstream decision")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert _prompt_of(argv) == (
        "invoke the nemawashi-unpick skill for the some-project project, with the reason "
        '"the station waits on an upstream decision" for its commit body and its report.'
    )
    assert argv[argv.index("--agent") + 1] == "pm"
    # The group is granted on the Codex path only, through --add-dir (Task 13's own new
    # test_claude_run_passes_no_group_add_dir_for_a_grouped_skill covers that directly); a Claude
    # run reaches it through the pin's plugin instead.
    assert str(run.root / "skills" / "pm") not in argv
    assert "--model" not in argv


def test_the_shipped_shukuba_retire_declaration_launches_under_scrum_master_granted_its_group(run):
    # The real declaration and the real agent file it names, placed where the shipped tree puts them:
    # the skill in the `scrum-master` group, so the run starts as the seat the skill's Posture gates
    # to, with the model left to the agent file. The group itself reaches a Claude run through the
    # pin's plugin, not `--add-dir` (Task 13) — Codex still gets `--add-dir`, covered elsewhere.
    shutil.copy(_SCRUM_MASTER_AGENT_MD, run.root / ".claude" / "agents" / "scrum-master.md")
    run.skill("shukuba-retire", _SHUKUBA_RETIRE_LAUNCHER_MD.read_text(), group="scrum-master")
    run.project("some-project")

    result = run("shukuba-retire", "some-project")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert _prompt_of(argv) == "invoke the shukuba-retire skill for the some-project project."
    assert argv[argv.index("--agent") + 1] == "scrum-master"
    assert str(run.root / "skills" / "scrum-master") not in argv
    assert "--model" not in argv


def test_the_shipped_tobiishi_drop_declaration_quotes_the_reason_under_pm_granted_its_group(run):
    shutil.copy(_PM_AGENT_MD, run.root / ".claude" / "agents" / "pm.md")
    run.skill("tobiishi-drop", _TOBIISHI_DROP_LAUNCHER_MD.read_text(), group="pm")
    run.project("some-project")

    result = run("tobiishi-drop", "some-project", "2026-09-19_some-change", "subject gone upstream")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert _prompt_of(argv) == (
        "invoke the tobiishi-drop skill for the some-project project, change key "
        '2026-09-19_some-change, reason "subject gone upstream".'
    )
    assert argv[argv.index("--agent") + 1] == "pm"
    # The group reaches a Claude run through the pin's plugin, not `--add-dir` (Task 13).
    assert str(run.root / "skills" / "pm") not in argv
    assert "--model" not in argv


def _shipped_launcher_mds():
    return sorted(_REPO.glob(".claude/skills/*/launcher.md")) + sorted(
        _REPO.glob("skills/*/.claude/skills/*/launcher.md")
    )


def _field(text, label):
    match = re.search(rf"^\*\*{label}:\*\*[ \t]*(\S+)", text, re.MULTILINE)
    return match.group(1) if match else None


def test_every_shipped_declaration_of_a_reporter_names_a_registered_one_and_what_it_reads():
    declared = [(md, _field(md.read_text(), "Reporter")) for md in _shipped_launcher_mds()]
    declared = [(md, reporter) for md, reporter in declared if reporter]
    assert len(declared) >= 8, declared
    for md, reporter in declared:
        assert reporter in _registered_reporter_names(), md
        if reporter != "generic":
            assert _field(md.read_text(), "Reads") in ("product", "project", "instance"), md


def _named_actors(skill_md):
    return set(re.findall(r"--actor[ \t]+[`\"]?([a-z][a-z-]*)", skill_md.read_text()))


def test_every_shipped_skill_commits_as_the_agent_its_declaration_launches():
    # An actor left for the run to guess is how a development-audit run committed as
    # `Role: Senior Engineer`: it tried `auditor`, the builder refused the unmapped token,
    # and it retried under another seat's. So these skills name it, and no skill
    # names one its declaration does not launch.
    naming = [
        md
        for md in _shipped_launcher_mds()
        if md.parent.name.startswith("development-") or md.parent.name in ("tobiishi-open", "nemawashi-drop")
    ]
    assert len(naming) == 9, naming
    for md in _shipped_launcher_mds():
        agent = _field(md.read_text(), "Agent")
        named = _named_actors(md.parent / "SKILL.md")
        assert named <= {agent}, (md, agent, named)
        if md in naming:
            assert named == {agent}, (md, agent, named)


def test_every_shipped_declaration_launches_an_agent_the_instance_holds():
    # The test above holds a declaration's agent and its skill's `--actor` to each other, so a
    # rename that misses both in one skill passes it. The launcher resolves the name to
    # its group file `skills/<agent>/.claude/agents/<agent>.md`; that file is what has to exist.
    declared = [(md, _field(md.read_text(), "Agent")) for md in _shipped_launcher_mds()]
    declared = [(md, agent) for md, agent in declared if agent]
    assert declared
    for md, agent in declared:
        assert _group_agent(agent).is_file(), (md, agent)


def test_every_seed_cut_commits_as_the_principal_pm():
    seed_cut_run = _REPO / "core" / "prompts" / "principal_pm_cut_seeds_run.md"
    assert _named_actors(seed_cut_run) == {"principal-pm"}


def test_test_driven_development_commits_as_the_developer():
    tdd = _REPO / "skills" / "developer" / ".claude" / "skills" / "test-driven-development" / "SKILL.md"
    assert _named_actors(tdd) == {"developer"}


def test_the_shipped_project_agari_declaration_is_watched_by_agari_reading_the_project(run):
    shutil.copy(_group_agent("cpo"), run.root / ".claude" / "agents" / "cpo.md")
    run.skill("project-agari", (_REPO / "skills" / "cpo" / ".claude" / "skills" / "project-agari" / "launcher.md").read_text())
    run.project("some-project")

    result = run("project-agari", "some-project")

    assert result.returncode == 0, result.stderr
    assert run.launched_prompt() == "invoke the project-agari skill for the some-project project."
    argv = run.watcher_argv()
    assert argv[argv.index("--reporter") + 1] == "agari"
    assert argv[argv.index("--artifact-path") + 1] == str(run.root / "system" / "projects" / "some-project")



def test_the_shipped_shukuba_refine_declaration_is_watched_by_its_reporter_reading_the_project(run):
    shutil.copy(_group_agent("pm"), run.root / ".claude" / "agents" / "pm.md")
    run.skill("shukuba-refine",
              (_REPO / "skills" / "pm" / ".claude" / "skills" / "shukuba-refine" / "launcher.md").read_text())
    run.project("some-project")

    result = run("shukuba-refine", "some-project")

    assert result.returncode == 0, result.stderr
    argv = run.watcher_argv()
    assert argv[argv.index("--reporter") + 1] == "shukuba-refine"
    assert argv[argv.index("--artifact-path") + 1] == str(run.root / "system" / "projects" / "some-project")


def test_the_shipped_nemawashi_drop_declaration_says_the_kill_and_quotes_the_reason(run):
    shutil.copy(_group_agent("principal-pm"),
                run.root / ".claude" / "agents" / "principal-pm.md")
    declaration = _REPO / "skills" / "principal-pm" / ".claude" / "skills" / "nemawashi-drop" / "launcher.md"
    run.skill("nemawashi-drop", declaration.read_text(), group="principal-pm")
    run.project("some-project")

    result = run("nemawashi-drop", "some-project", "2026-08-01_old", "overtaken by the walk")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert _prompt_of(argv) == (
        "invoke the nemawashi-drop skill for the some-project project, killing the seed "
        '2026-08-01_old, reason "overtaken by the walk".'
    )
    assert argv[argv.index("--agent") + 1] == "principal-pm"
    assert "--model" not in argv


def test_the_shipped_seeds_from_product_docs_declaration_cuts_the_projects_product(run):
    shutil.copy(_group_agent("principal-pm"),
                run.root / ".claude" / "agents" / "principal-pm.md")
    declaration = _REPO / "skills" / "principal-pm" / ".claude" / "skills" / "seeds-from-product-docs" / "launcher.md"
    run.skill("seeds-from-product-docs", declaration.read_text(), group="principal-pm")
    product = run.root / "external-product"
    product.mkdir()
    run.project("some-project", product_path=str(product))

    result = run("seeds-from-product-docs", "some-project")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert _prompt_of(argv) == "invoke the seeds-from-product-docs skill for the some-project project."
    assert argv[argv.index("--agent") + 1] == "principal-pm"
    assert "--effort" not in argv
    assert "--model" not in argv
    assert _granted_dirs(argv) == [str(product), str(run.pin_root)]


_PRODUCT_SDD_DIR = _REPO / "skills" / "cto" / ".claude" / "skills" / "product-sdd"
_PRODUCT_SDD_PROMPT = "invoke the product-sdd skill for the some-project project."
# What the skill's own text must never say (CP-397): a live seat session, or an authorship by three.
_LIVE_SEAT_TEXT = re.compile(
    r"sdd_(?:run|seat)|SendMessage|three seats|one run, three", re.IGNORECASE)


def _named_product_sdd_dirs():
    """Every directory named `product-sdd` under either skill root, the way the resolver matches."""
    return sorted(
        path
        for pattern in (".claude/skills/product-sdd", "skills/*/.claude/skills/product-sdd")
        for path in _REPO.glob(pattern)
    )


def test_product_sdd_resolves_only_in_the_cto_group():
    assert _named_product_sdd_dirs() == [_PRODUCT_SDD_DIR]
    for component in ("SKILL.md", "launcher.md", "stack.json", "intelligence"):
        assert (_PRODUCT_SDD_DIR / component).exists(), component
    resolved = subprocess.run(
        ["python3", str(_CORE_DIR / "tools" / "skill_path.py"), "product-sdd",
         "--root", str(_REPO)],
        capture_output=True, text=True,
    )
    assert resolved.returncode == 0, resolved.stderr
    assert resolved.stdout.strip() == str(_PRODUCT_SDD_DIR)


def test_the_shipped_product_sdd_declaration_launches_under_cto(run):
    shutil.copy(_group_agent("cto"), run.root / ".claude" / "agents" / "cto.md")
    run.skill("product-sdd", (_PRODUCT_SDD_DIR / "launcher.md").read_text(), group="cto")
    run.project("some-project")

    result = run("product-sdd", "some-project")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert argv[argv.index("--agent") + 1] == "cto"
    assert _prompt_of(argv) == _PRODUCT_SDD_PROMPT


def test_the_shipped_product_sdd_dry_run_launches_nothing(run):
    shutil.copy(_group_agent("cto"), run.root / ".claude" / "agents" / "cto.md")
    run.skill("product-sdd", (_PRODUCT_SDD_DIR / "launcher.md").read_text(), group="cto")
    run.project("some-project")

    result = run("product-sdd", "some-project", "--dry-run")

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    assert argv[argv.index("--agent") + 1] == "cto"
    assert _PRODUCT_SDD_PROMPT in argv
    _nothing_spawned(run)
    assert run.watcher_argv() == []


def test_product_sdd_stack_is_complete_and_has_no_live_seat_instructions():
    stack = json.loads((_PRODUCT_SDD_DIR / "stack.json").read_text())
    listed = stack["substance"]
    skill_md = "skills/cto/.claude/skills/product-sdd/SKILL.md"
    assert skill_md in listed
    assert "skills/cto/.claude/skills/product-sdd/prompts/rich.md" in listed
    for forbidden in ("sdd_conversation_conduct", "cpo_create_sdd", "cdo_create_sdd"):
        assert not any(forbidden in path for path in listed), forbidden
    for path in listed:
        assert (_REPO / path).is_file(), path
    own_text = [_PRODUCT_SDD_DIR / "SKILL.md", _PRODUCT_SDD_DIR / "launcher.md"]
    own_text += [_REPO / path for path in listed]
    for text_file in own_text:
        assert not _LIVE_SEAT_TEXT.search(text_file.read_text()), text_file


def test_live_seat_guard_rejects_each_retired_module_case_insensitively():
    """Both retired module file names are rejected whatever their case, and the other
    alternatives still match as before."""
    for text in ("SDD_RUN.PY", "SDD_SEAT.PY", "SendMessage", "three seats", "one run, three"):
        assert _LIVE_SEAT_TEXT.search(text), text
    assert not _LIVE_SEAT_TEXT.search("one run, one seat")


def test_product_sdd_commits_as_cto():
    skill_text = (_PRODUCT_SDD_DIR / "SKILL.md").read_text()
    assert "--actor cto --skill product-sdd" in skill_text
    assert _named_actors(_PRODUCT_SDD_DIR / "SKILL.md") == {"cto"}
    declaration = (_PRODUCT_SDD_DIR / "launcher.md").read_text()
    assert _field(declaration, "Agent") == "cto"
    assert _field(declaration, "Reporter") in _registered_reporter_names()
    assert _field(declaration, "Reads") == "product"


# --- a launch ----------------------------------------------------------------------------------


def test_a_launch_reports_the_skill_its_argument_and_the_two_watch_lines(demo):
    result = demo("demo", "some-project")

    assert result.returncode == 0, result.stderr
    assert "Skill:     demo" in result.stdout
    assert "Argument:  <project> some-project" in result.stdout
    assert "claude agents" not in result.stdout
    run_log = re.search(r"^Launched\. Run log: (.+\.jsonl)$", result.stdout, re.MULTILINE)
    assert run_log, result.stdout
    assert Path(run_log.group(1)).parent == demo.root / "system" / "logs"
    session = re.search(r"Session:  (\S+)   \(once the run has ended, claude --resume \1 opens it\)", result.stdout)
    assert session, result.stdout


def test_the_flags_may_sit_anywhere_after_the_skill(demo):
    result = demo("demo", "--dry-run", "some-project")

    assert result.returncode == 0, result.stderr
    assert "DRY RUN — would launch:" in result.stdout
    assert demo.launched_argv(wait=_ABSENT_WAIT) == []


def test_claude_dry_run_prints_the_pin_line_and_carries_the_delivery(demo):
    # The launcher enters the pin (Task 12), and the Claude argv comes from the adapter, carrying
    # the pin delivery (Task 13).
    result = demo("demo", "some-project", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert re.search(r"^Pin: .+\(inherited\)$", result.stdout, re.MULTILINE)
    argv = _dry_run_argv(result.stdout)
    assert argv[argv.index("--setting-sources") + 1] == "user"
    assert "--plugin-dir" in argv
    assert _granted_dirs(argv) == [str(demo.pin_root)]


def test_dry_run_prints_exactly_the_command_a_real_launch_spawns(demo):
    dry = demo("demo", "some-project", "--dry-run")
    assert dry.returncode == 0, dry.stderr
    printed = _dry_run_argv(dry.stdout)
    assert demo.launched_argv(wait=_ABSENT_WAIT) == []
    assert demo.watcher_argv() == []

    real = demo("demo", "some-project")
    assert real.returncode == 0, real.stderr

    assert printed[0] == "claude"
    assert _without_session_id(printed[1:]) == _without_session_id(demo.launched_argv())


def test_codex_dry_run_bootstraps_the_agent_and_names_no_model(demo):
    result = demo(
        "demo", "some-project", "--provider", "codex", "--dry-run"
    )

    assert result.returncode == 0, result.stderr
    assert "Provider:  codex" in result.stdout
    argv = _dry_run_argv(result.stdout)
    assert argv[0] == "codex-skill"
    assert "--model" not in argv
    assert "--config" not in argv
    prompt = argv[-1]
    assert f"{demo.root}/.claude/agents/pm.md" in prompt
    assert argv[argv.index("--skill-path") + 1] == f"{demo.root}/.claude/skills/demo/SKILL.md"
    assert "invoke the demo skill for the some-project project." in prompt
    assert demo.codex_argv(wait=_ABSENT_WAIT) == []


def test_gemini_dry_run_names_no_model_and_no_effort_without_an_intelligence_folder(demo):
    result = demo("demo", "some-project", "--provider", "gemini", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "Provider:  gemini" in result.stdout
    argv = _dry_run_argv(result.stdout)
    assert argv[0] == "agy"
    assert "--mode" in argv and argv[argv.index("--mode") + 1] == "accept-edits"
    assert "--model" not in argv
    assert "--effort" not in argv
    assert argv[argv.index("--output-format") + 1] == "stream-json"
    assert argv[argv.index("--add-dir") + 1] == f"{demo.root}/.claude/skills/demo"
    prompt = argv[-1]
    assert argv[-2] == "-p"
    assert f"{demo.root}/.claude/agents/pm.md" in prompt
    # Native skill loading: SKILL.md is not instructed to be read as text in the prompt
    assert f"{demo.root}/.claude/skills/demo/SKILL.md" not in prompt
    assert "invoke the demo skill for the some-project project." in prompt
    assert "`--surface Gemini`" in prompt


def test_codex_prompt_names_the_pinned_agent_file(run):
    # `developer` is a real shipped host agent, held only by the session pin's own group
    # `skills/developer/.claude/agents/` — never written into this test's own instance (unlike
    # `pm`, which the
    # `run` fixture always writes at `tmp_path/.claude/agents/pm.md`). Task 14: the Codex prompt's
    # agent path is resolved through `pin.py agent-file`, not a hardcoded instance path, so it
    # names the pin's copy.
    run.skill("demo", _md(agent="developer"))
    run.project("some-project")

    result = run("demo", "some-project", "--provider", "codex", "--dry-run")

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    prompt = argv[-1]
    pinned_agent_file = (
        run.core_dir.parent / "skills" / "developer" / ".claude" / "agents" / "developer.md"
    )
    assert f"read and follow the agent instructions in: {pinned_agent_file}" in prompt
    assert str(run.root / ".claude" / "agents") not in prompt


def test_codex_launches_detached_through_agent_run_and_writes_jsonl(demo):
    result = demo("demo", "some-project", "--provider", "codex")

    assert result.returncode == 0, result.stderr
    argv = demo.codex_argv()
    assert argv[0] == "app-server"
    assert "--model" not in argv
    assert "--config" not in argv
    assert "--skill-path" in argv
    prompt = argv[-1]
    assert "as the pm agent" in prompt
    assert "Execute this fixed task:" in prompt
    assert "invoke the demo skill for the some-project project." in prompt
    match = re.search(r"Launched\. Run log: (.+)", result.stdout)
    assert match, result.stdout
    log_path = Path(match.group(1))
    # The stub runs detached, so it writes after the launcher returns. This waits for that write —
    # it does not time it — so the deadline is generous: a loaded machine delays it, and only a
    # stub that never writes should fail here.
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if log_path.exists() and "turn.completed" in log_path.read_text():
            break
        time.sleep(0.02)
    else:
        raise AssertionError("Codex stub did not write its terminal JSON event")


def test_codex_declaration_with_no_agent_bootstraps_the_skill_on_its_intelligence(run):
    _intelligence(run.skill("demo", _md(agent=None)), "codex")
    run.project("some-project")

    result = run(
        "demo", "some-project", "--provider", "codex", "--dry-run"
    )

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    assert argv[argv.index("--model") + 1] == "claude-m-1"
    # Under the pin every `<CORE>`-derived path is the pin's own, this one included (Task 12).
    assert f"Kensaiapp core resolution: `<CORE>` = `{run.core_dir}`." in argv[-1]
    assert "/.claude/agents/" not in argv[-1]
    assert argv[argv.index("--skill-path") + 1] == f"{run.root}/.claude/skills/demo/SKILL.md"


@pytest.mark.parametrize(
    "cli, expected",
    [
        (
            ("--provider", "other"),
            "unknown provider 'other' — available providers: claude, codex, gemini, hf, ollama.",
        ),
        (("--provider",), "--provider needs claude, codex, gemini, hf or ollama."),
    ],
)
def test_codex_provider_refuses_unsupported_or_malformed_calls(demo, cli, expected):
    result = demo("demo", "some-project", *cli)

    assert result.returncode != 0
    assert expected in result.stderr
    assert demo.launched_argv(wait=_ABSENT_WAIT) == []
    assert demo.codex_argv(wait=_ABSENT_WAIT) == []


def test_codex_keep_awake_is_bound_to_the_process_observer(demo):
    result = demo("demo", "some-project", "--provider", "codex", "--keep-awake")

    assert result.returncode == 0, result.stderr
    assert "Completion watch:" in result.stdout
    argv = demo.caffeinate_argv()
    assert argv == ["-i", "-s"]


def test_codex_completion_observer_runs_the_chain_hook_without_a_notifier(demo):
    hook_log = demo.root / "hook-outcome"
    hook = demo.root / "hook.sh"
    hook.write_text(
        "#!/usr/bin/env bash\n"
        f"printf '%s' \"$1\" > {shlex.quote(str(hook_log))}\n"
    )
    hook.chmod(0o755)
    demo.env["DETACH_WATCHER_ON_COMPLETE"] = str(hook)
    demo.env["LAUNCH_SKILL_NOTIFIER"] = str(demo.root / "missing-notifier")
    demo.env.pop("LAUNCH_SKILL_WATCHER")

    result = demo("demo", "some-project", "--provider", "codex")

    assert result.returncode == 0, result.stderr
    for _ in range(int(_KEEPAWAKE_WAIT / 0.05)):
        if hook_log.exists():
            break
        time.sleep(0.05)
    assert hook_log.read_text() == "completed"


def test_provider_can_be_selected_by_environment(demo):
    demo.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"

    result = demo("demo", "some-project", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert _dry_run_argv(result.stdout)[0] == "codex-skill"


def test_a_declaration_with_no_agent_passes_its_intelligence_model_and_no_agent(run):
    _intelligence(run.skill("demo", _md(agent=None)), "claude", model="claude-opus-5-5")
    run.project("some-project")

    result = run("demo", "some-project")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert argv[argv.index("--model") + 1] == "claude-opus-5-5"
    assert "--agent" not in argv


def test_a_declaration_with_no_arguments_takes_none(run):
    run.skill("demo", _md(arguments=None, prompt="invoke the demo skill."))

    ok = run("demo")
    assert ok.returncode == 0, ok.stderr
    assert run.launched_prompt() == "invoke the demo skill."

    extra = run("demo", "anything")
    assert extra.returncode != 0
    assert "unexpected argument: anything" in extra.stderr


@pytest.mark.parametrize(
    "cli, expected",
    [
        (("some-project",), "invoke demo for some-project."),
        (("some-project", "k1"), "invoke demo for some-project at unit k1."),
    ],
)
def test_an_optional_segment_is_kept_only_when_its_argument_is_given(run, cli, expected):
    run.skill(
        "demo",
        _md(arguments="<project> [<unit-key>]", prompt="invoke demo for {project}[ at unit {unit-key}]."),
    )
    run.project("some-project")

    result = run("demo", *cli)

    assert result.returncode == 0, result.stderr
    assert run.launched_prompt() == expected


def test_a_value_is_never_scanned_for_a_placeholder(run):
    run.skill("demo", _md(arguments="<slug> <other>", prompt="a {slug} b {other}"))

    result = run("demo", "{other}", "x")

    assert result.returncode == 0, result.stderr
    assert run.launched_prompt() == "a {other} b x"


# --- refusals of the call ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cli, expected",
    [
        ((), "is required"),
        (("--dry-run",), "is required"),
        (("a/b",), "looks like a path"),
        ((".hidden",), "looks like a path"),
        (("no-such-skill",), "no skill named 'no-such-skill'"),
        (("demo",), "needs <project>"),
        (("demo", "some-project", "extra"), "unexpected argument: extra"),
        (("demo", "some-project", "--dryrun"), "unknown argument: --dryrun"),
        (("demo", ""), "<project> is empty"),
        (("demo", "system/projects/some-project"), "looks like a path"),
        (("demo", "no-such-project"), "no system/projects/no-such-project/"),
        (("demo", "some-project", "--instance-root", "/tmp"), "unknown argument: --instance-root"),
    ],
)
def test_a_refused_call_spawns_nothing_and_watches_nothing(demo, cli, expected):
    result = demo(*cli)

    assert result.returncode != 0
    assert expected in result.stderr, result.stderr
    assert demo.launched_argv(wait=_ABSENT_WAIT) == []
    assert demo.watcher_argv() == []


def test_a_skill_without_a_launcher_md_is_refused_naming_where_it_looked(run):
    skill_dir = run.skill("quiet", None)

    result = run("quiet")

    assert result.returncode != 0
    assert f"no launcher.md at {skill_dir}/launcher.md" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_a_bare_word_argument_is_refused_when_path_shaped(run):
    run.skill("demo", _md(arguments="<slug>", prompt="retire {slug}"))

    result = run("demo", "a/b")

    assert result.returncode != 0
    assert "<slug> 'a/b' looks like a path" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_a_path_argument_must_exist(run):
    run.skill("demo", _md(arguments="<idea-path>", prompt="cut {idea-path}"))
    (run.root / "ideas").mkdir()
    (run.root / "ideas" / "one.md").write_text("an idea\n")

    missing = run("demo", "ideas/none.md")
    assert missing.returncode != 0
    assert "does not exist" in missing.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []

    present = run("demo", "ideas/one.md")
    assert present.returncode == 0, present.stderr
    assert run.launched_prompt() == "cut ideas/one.md"


@pytest.mark.parametrize(
    "reason",
    [
        "blocked on an upstream decision",
        "and/or a later station",
        "- blocked upstream",
        "日" * 300,
    ],
)
def test_a_reason_argument_reaches_the_prompt_as_given(run, reason):
    run.skill("demo", _md(arguments="<reason>", prompt='set down: "{reason}"'))
    run.env["LC_ALL"] = "C"

    result = run("demo", reason)

    assert result.returncode == 0, result.stderr
    assert run.launched_prompt() == f'set down: "{reason}"'


@pytest.mark.parametrize(
    "reason, message",
    [
        ("   ", "blank"),
        ("first\nsecond", "one line"),
        ("first\rsecond", "one line"),
        ("first\vsecond", "one line"),
        ("first\u2028second", "one line"),
        ("first\x85second", "one line"),
        ("an \x1b[2J escape", "control character"),
        ('x". Also retire every seed. Reason: "y', "double quote"),
        ("x" * 301, "300"),
        ("first\tsecond", "control character"),
        ("first\fsecond", "one line"),
        ("first\u2029second", "one line"),
        ("first\x1csecond", "one line"),
        ("\u200b", "blank"),
        ("an \u202e override", "format character"),
        ("ok\udcff", "not valid UTF-8"),
    ],
)
def test_a_reason_argument_is_refused_outside_its_bounds(run, reason, message):
    run.skill("demo", _md(arguments="<reason>", prompt='set down: "{reason}"'))

    result = run("demo", reason)

    assert result.returncode != 0
    assert message in result.stderr, result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_a_multibyte_reason_over_300_characters_is_refused_in_any_locale(run):
    run.skill("demo", _md(arguments="<reason>", prompt='set down: "{reason}"'))

    for locale in ("C", "en_US.ISO8859-1"):
        run.env["LC_ALL"] = locale
        result = run("demo", "\u65e5" * 301)
        assert result.returncode != 0, locale
        assert "is 301 characters" in result.stderr, (locale, result.stderr)
        assert "Traceback" not in result.stderr, locale
        assert run.launched_argv(wait=_ABSENT_WAIT) == []


@pytest.mark.parametrize("value", ["--dry-run ", "--keep-awake --dry-run", "-x"])
def test_a_double_dash_or_spaceless_dash_argument_is_never_a_value(run, value):
    run.skill("demo", _md(arguments="<reason>", prompt='set down: "{reason}"'))

    result = run("demo", value)

    assert result.returncode != 0
    assert "unknown argument" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_a_dash_led_value_is_refused_outside_a_reason(run):
    run.skill("demo", _md(arguments="<unit-key>", prompt="review {unit-key}"))

    result = run("demo", "-x y")

    assert result.returncode != 0
    assert "<unit-key> '-x y' begins with '-'" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


# --- refusals of the declaration ---------------------------------------------------------------


@pytest.mark.parametrize(
    "md, expected",
    [
        (_md(prompt=None), "no **Prompt:** line"),
        (_md(agent=None), "no **Agent:** and no intelligence/ folder"),
        (_md(agent="ghost"), "ghost has no agent file"),
        (_md(model="opus"), "belongs in intelligence/<provider>.md"),
        (_md(model="two words"), "belongs in intelligence/<provider>.md"),
        (_md(effort="high"), "belongs in intelligence/<provider>.md"),
        (_md(arguments="project"), "is neither <name> nor [<name>]"),
        (_md(arguments="<Project>"), "a name is lowercase"),
        (_md(arguments="[<key>] <project>", prompt="{project}[ {key}]"), "follows an optional"),
        (_md(arguments="<project> <project>"), "declared twice"),
        (_md(prompt="for {project} and {other}"), "{other} names no argument"),
        (_md(arguments="<project> <slug>", prompt="for {project}"), "never uses <slug>"),
        (_md(arguments="<project> [<key>]", prompt="{project} {key}"), "outside a [ … ] segment"),
        (_md(prompt="{project} [unclosed"), "is never closed"),
        (_md(prompt="{project} [a [b] c]"), "do not nest"),
        (_md(prompt="{project} ]"), "closes no '['"),
        (_md(prompt="{project} {open"), "a '{' is never closed"),
        (_md(reporter="no-such-reporter", reads="product"), "'no-such-reporter' is not a name in REGISTRY"),
        (_md(reporter="prd"), "prd needs **Reads:**"),
        (_md(reads="product"), "names no **Reporter:**"),
        (_md(reporter="prd", reads="docs"), "'docs' is not product, project or instance"),
        (
            _md(arguments="<slug>", prompt="for {slug}", reporter="agari", reads="project"),
            "needs <project> in **Arguments:**",
        ),
    ],
)
def test_a_defective_declaration_is_refused_naming_the_file_before_anything_spawns(run, md, expected):
    skill_dir = run.skill("demo", md)
    run.project("some-project")

    # --dry-run too: a defect is refused on every path, not only a real launch.
    result = run("demo", "some-project", "--dry-run")

    assert result.returncode != 0
    assert expected in result.stderr, result.stderr
    assert str(skill_dir / "launcher.md") in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def _group_only_agent(run, name):
    """An agent held only as `skills/<name>/.claude/agents/<name>.md` under the instance, with no
    flat file for it anywhere, and no pin in force — a dry run before any pin exists on this host
    makes none, which is the state this agent has to be found in."""
    path = run.root / "skills" / name / ".claude" / "agents" / f"{name}.md"
    path.parent.mkdir(parents=True)
    path.write_text(f"---\nname: {name}\n---\n")
    run.env["KENSAIAPP_PIN"] = ""
    return path


def test_declared_agent_only_in_group_launches_without_defect(run):
    run.skill("demo", _md(agent="delegate"))
    run.project("some-project")
    _group_only_agent(run, "delegate")

    result = run("demo", "some-project", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "has no agent file" not in result.stderr


def test_codex_prompt_names_group_agent_file(run):
    run.skill("demo", _md(agent="delegate"))
    run.project("some-project")
    group_file = _group_only_agent(run, "delegate")

    result = run("demo", "some-project", "--dry-run", "--provider", "codex")

    assert result.returncode == 0, result.stderr
    assert str(group_file.resolve()) in result.stdout


def test_unknown_agent_refusal_names_the_group_shape(run):
    run.skill("demo", _md(agent="ghost"))
    run.project("some-project")

    result = run("demo", "some-project", "--dry-run")

    assert result.returncode != 0
    assert (
        "**Agent:** ghost has no agent file in any group (skills/<group>/.claude/agents/ghost.md)"
        in result.stderr
    ), result.stderr
    assert f"{run.root}/.claude/agents/ghost.md" not in result.stderr


def test_an_agent_held_by_neither_is_still_a_defect(run):
    # Task 14: the existence check is judged through `pin.py agent-file` — an agent absent from
    # both the instance and the pin is still refused, naming the declaration, before anything
    # spawns on either provider. (The parametrized `agent="ghost"` case above already covers the
    # dry-run/Claude path; this covers a real, non-dry-run launch on the Codex path.)
    run.skill("demo", _md(agent="ghost"))
    run.project("some-project")

    result = run("demo", "some-project", "--provider", "codex")

    assert result.returncode != 0
    assert "ghost has no agent file" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []
    assert run.codex_argv(wait=_ABSENT_WAIT) == []


def test_a_defect_is_reported_ahead_of_a_missing_argument(run):
    run.skill("demo", _md(prompt=None))

    result = run("demo")

    assert "no **Prompt:** line" in result.stderr
    assert "needs <project>" not in result.stderr


def test_a_bracket_in_the_arguments_field_is_never_expanded_against_the_instance(run):
    run.skill("demo", _md(arguments="<project> [<k>]", prompt="{project}[ {k}]"))
    run.project("some-project")
    (run.root / "k").write_text("a file a glob [<k>] could never match, but [k] would\n")

    result = run("demo", "some-project")

    assert result.returncode == 0, result.stderr
    assert run.launched_prompt() == "some-project"


# --- a skill's intelligence: its model and its effort (CP-169 … CP-175) --------------------------

_PROVIDERS = ["claude", "codex", "gemini"]
_MODES = ["--dry-run", "real"]
_TIER_MODELS = (
    "gpt-5.6-sol",
    "gpt-5.6-terra",
    "gemini-3.1-pro-high",
    "gemini-3.1-pro-low",
)


def _intelligence(skill_dir, provider, model="claude-m-1", effort=None, text=None):
    """`<skill dir>/intelligence/<provider>.md`, with prose that mentions a label mid-line."""
    folder = skill_dir / "intelligence"
    folder.mkdir(exist_ok=True)
    if text is None:
        lines = [
            f"# demo — {provider} intelligence",
            "",
            "Prose for a reader. A **Model:** written mid-line like this one is never a field.",
            "",
            f"**Model:** {model}",
        ]
        if effort is not None:
            lines.append(f"**Effort:** {effort}")
        text = "\n".join(lines) + "\n"
    (folder / f"{provider}.md").write_text(text)
    return folder / f"{provider}.md"


def _launch(run, provider, mode, skill="demo", project="some-project"):
    """The provider's command: the dry run's printed one, or the real launch's recorded one."""
    args = [skill, project, "--provider", provider]
    if mode == "--dry-run":
        result = run(*args, "--dry-run")
        return result, (_dry_run_argv(result.stdout) if result.returncode == 0 else [])
    result = run(*args)
    reader = {
        "claude": run.launched_argv,
        "codex": run.codex_argv,
        "gemini": run.gemini_argv,
        "hf": run.launched_argv,
        "ollama": run.launched_argv,
    }[provider]
    return result, (reader() if result.returncode == 0 else [])


def _nothing_spawned(run):
    for reader in (run.launched_argv, run.codex_argv, run.gemini_argv):
        assert reader(wait=_ABSENT_WAIT) == []


def _efforts(argv, provider):
    """Every effort level the command carries, in that provider's own form."""
    if provider == "codex":
        return [a.split('"')[1] for a in argv if a.startswith("model_reasoning_effort=")]
    return [argv[i + 1] for i, a in enumerate(argv) if a == "--effort"]


def _models(argv):
    return [argv[i + 1] for i, a in enumerate(argv) if a == "--model"]


@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("provider", _PROVIDERS)
def test_an_intelligence_file_puts_its_model_and_effort_on_the_command(run, provider, mode):
    _intelligence(run.skill("demo", _md()), provider, model="claude-m-1", effort="low")
    run.project("some-project")

    result, argv = _launch(run, provider, mode)

    assert result.returncode == 0, result.stderr
    assert _models(argv) == ["claude-m-1"]
    assert _efforts(argv, provider) == ["low"]


@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("provider", _PROVIDERS)
def test_an_intelligence_file_with_no_effort_puts_no_effort_token(run, provider, mode):
    _intelligence(run.skill("demo", _md()), provider, model="claude-m-1")
    run.project("some-project")

    result, argv = _launch(run, provider, mode)

    assert result.returncode == 0, result.stderr
    assert _models(argv) == ["claude-m-1"]
    assert _efforts(argv, provider) == []


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_no_tier_is_resolved_and_no_agent_file_is_read_for_a_model(run, provider):
    tiered = run.root / ".claude" / "agents" / "tiered.md"
    tiered.write_text("---\nname: tiered\nmodel: opus\n---\n")
    _intelligence(run.skill("demo", _md(agent="tiered")), provider, model="claude-m-1")
    run.project("some-project")

    result = run("demo", "some-project", "--provider", provider, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert _models(_dry_run_argv(result.stdout)) == ["claude-m-1"]
    for tier_model in _TIER_MODELS:
        assert tier_model not in result.stdout


@pytest.mark.parametrize("mode", _MODES)
def test_a_folder_without_the_providers_file_is_refused_naming_the_path(run, mode):
    skill_dir = run.skill("demo", _md())
    _intelligence(skill_dir, "claude")
    run.project("some-project")

    result, _ = _launch(run, "codex", mode)

    assert result.returncode == 1
    assert str(skill_dir / "intelligence" / "codex.md") in result.stderr
    _nothing_spawned(run)


_MALFORMED_INTELLIGENCE = [
    "# no model line\n",
    "**Model:**\n",
    "**Model:** two words\n",
    "**Model:** claude-m-1\n**Effort:** ultra\n",
    "**Model:** claude-m-1\n**Effort:** Low\n",
]


@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("text", _MALFORMED_INTELLIGENCE)
def test_a_malformed_intelligence_file_is_refused_naming_it(run, text, mode):
    path = _intelligence(run.skill("demo", _md()), "claude", text=text)
    run.project("some-project")

    result, _ = _launch(run, "claude", mode)

    assert result.returncode == 1
    assert str(path) in result.stderr
    _nothing_spawned(run)


@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("provider", _PROVIDERS)
def test_a_skill_with_no_intelligence_folder_launches_with_no_model_and_no_effort(
    demo, provider, mode
):
    result, argv = _launch(demo, provider, mode)

    assert result.returncode == 0, result.stderr
    assert _models(argv) == []
    assert _efforts(argv, provider) == []
    assert "Intelligence: none — provider default" in result.stdout


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_a_dry_run_names_the_intelligence_file_it_read(run, provider):
    path = _intelligence(run.skill("demo", _md()), provider)
    run.project("some-project")

    result = run("demo", "some-project", "--provider", provider, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert f"Intelligence: {path}" in result.stdout


def test_no_agent_and_no_intelligence_folder_is_a_declaration_defect(run):
    skill_dir = run.skill("demo", _md(agent=None))
    run.project("some-project")

    result = run("demo", "some-project", "--dry-run")

    assert result.returncode == 1
    assert str(skill_dir / "launcher.md") in result.stderr
    assert "no **Agent:** and no intelligence/ folder" in result.stderr
    _nothing_spawned(run)


@pytest.mark.parametrize("declared", [{"model": "opus"}, {"effort": "high"}])
def test_a_model_or_effort_line_in_launcher_md_is_a_declaration_defect(run, declared):
    skill_dir = run.skill("demo", _md(**declared))

    # No project argument: a defect is judged before any argument value, and before a missing one.
    result = run("demo")

    assert result.returncode == 1
    assert str(skill_dir / "launcher.md") in result.stderr
    assert "belongs in intelligence/<provider>.md" in result.stderr
    assert "needs <project>" not in result.stderr
    _nothing_spawned(run)


def test_the_header_names_the_intelligence_file_and_no_model_or_effort_field():
    header = "\n".join(l for l in _SCRIPT.read_text().splitlines() if l.startswith("#"))
    assert "intelligence/<provider>.md" in header
    assert not re.search(r"^#\s+\*\*(Model|Effort):\*\*", header, re.MULTILINE)


def _tracked_launcher_mds():
    tracked = subprocess.run(
        ["git", "ls-files", "--", "skills", ".claude/skills"],
        cwd=_REPO, capture_output=True, text=True, check=True,
    ).stdout.split()
    return [_REPO / name for name in tracked if name.endswith("/launcher.md")]


def test_no_shipped_launcher_md_carries_a_model_or_effort_line():
    declarations = _tracked_launcher_mds()
    assert len(declarations) >= 20, declarations
    carrying = [
        str(md.relative_to(_REPO))
        for md in declarations
        if re.search(r"^\*\*(Model|Effort):\*\*", md.read_text(), re.MULTILINE)
    ]
    assert carrying == []


def test_no_shipped_launcher_md_says_an_agent_pins_its_model():
    stale = ("pins its model", "pins the model", "no Model line")
    said = [
        str(md.relative_to(_REPO))
        for md in _tracked_launcher_mds()
        if any(phrase in md.read_text() for phrase in stale)
    ]
    assert said == []


# --- a grouped skill's group ------------------------------------------------------------------------


def test_a_grouped_skill_grants_its_group(run):
    # Codex only: on the Claude path the group is never `--add-dir`-granted (it reaches a Claude
    # run through the pin's plugin instead) — see test_claude_run_passes_no_group_add_dir_for_a_grouped_skill.
    run.skill("demo", _md(), group="pm")
    run.project("some-project")

    result = run("demo", "some-project", "--provider", "codex")

    assert result.returncode == 0, result.stderr
    group = run.root / "skills" / "pm"
    assert f"Group:     {group}" in result.stdout
    argv = run.codex_argv()
    assert _granted_dirs(argv) == [str(group)]


def test_the_group_is_read_off_the_skill_location_not_its_agent(run):
    _intelligence(run.skill("demo", _md(agent=None), group="elsewhere"), "codex")
    run.project("some-project")

    result = run("demo", "some-project", "--provider", "codex")

    assert result.returncode == 0, result.stderr
    argv = run.codex_argv()
    assert _granted_dirs(argv) == [str(run.root / "skills" / "elsewhere")]


def test_a_grouped_skill_with_an_external_product_grants_both(run):
    product = run.root / "external-product"
    product.mkdir()
    run.skill("demo", _md(), group="pm")
    run.project("some-project", product_path=str(product))

    result = run("demo", "some-project", "--provider", "codex")

    assert result.returncode == 0, result.stderr
    argv = run.codex_argv()
    granted = _granted_dirs(argv)
    assert granted == [str(run.root / "skills" / "pm"), str(product)]


def test_a_satellite_finds_its_skill_in_the_host_and_is_granted_the_hosts_group(run, tmp_path_factory):
    # A satellite holds no skills and no `skills` symlink: the skill lives only in the host, and
    # the host's group is what the run is granted. The project and the cwd stay the satellite's.
    host = tmp_path_factory.mktemp("host")
    skill_dir = host / "skills" / "pm" / ".claude" / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: demo\n---\n")
    (skill_dir / "launcher.md").write_text(_md())
    run.project("some-project")
    run.env["LAUNCH_SKILL_SKILLS_ROOT"] = str(host)
    assert not (run.root / "skills").exists()

    result = run("demo", "some-project", "--provider", "codex")

    assert result.returncode == 0, result.stderr
    assert f"Launcher:  {skill_dir / 'launcher.md'}" in result.stdout
    argv = run.codex_argv()
    assert _granted_dirs(argv) == [str(host / "skills" / "pm")]


def test_claude_run_passes_no_group_add_dir_for_a_grouped_skill(run):
    # The product `--add-dir` is still present for an absolute product path; the pin's own
    # trailing `--add-dir <pin root>` rides along too (pin delivery, unconditional) — only the
    # group's own directory is gone from the Claude command.
    product = run.root / "external-product"
    product.mkdir()
    run.skill("demo", _md(), group="pm")
    run.project("some-project", product_path=str(product))

    result = run("demo", "some-project")

    assert result.returncode == 0, result.stderr
    group = run.root / "skills" / "pm"
    argv = run.launched_argv()
    assert str(group) not in argv
    assert _granted_dirs(argv) == [str(product), str(run.pin_root)]


def test_a_grouped_skills_claude_launch_lists_its_group_and_no_other(run):
    # `tobiishi-drop` is a shipped `pm` skill with no `depends-on:`, so its grant reaches `pm`
    # alone; the session pin holds every other shipped group beside it.
    run.skill("tobiishi-drop", _md(), group="pm")
    run.project("some-project")

    result = run("tobiishi-drop", "some-project")

    assert result.returncode == 0, result.stderr
    listed, groups = _plugin_skills(run.launched_argv())
    assert "tobiishi-drop" in listed
    assert groups == {"pm"}


def test_a_flat_skills_claude_launch_lists_no_grouped_skill(demo):
    result = demo("demo", "some-project")

    assert result.returncode == 0, result.stderr
    listed, groups = _plugin_skills(demo.launched_argv())
    assert "demo" in listed
    assert groups == set()


def test_a_skill_only_in_the_instance_is_not_found(run, tmp_path_factory):
    # The instance's own tree is never searched: a skill there and not in the host is refused.
    run.skill("demo", _md(), group="pm")
    run.project("some-project")
    host = tmp_path_factory.mktemp("host")
    run.env["LAUNCH_SKILL_SKILLS_ROOT"] = str(host)

    result = run("demo", "some-project")

    assert result.returncode != 0
    assert f"no skill named 'demo' under {host}" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_a_flat_skill_grants_no_group(demo):
    # No group and no product — the pin's own trailing `--add-dir <pin root>` (Task 13) is the
    # only one left, not an empty list.
    result = demo("demo", "some-project")

    assert result.returncode == 0, result.stderr
    assert "Group:" not in result.stdout
    argv = demo.launched_argv()
    granted = _granted_dirs(argv)
    assert granted == [str(demo.pin_root)]


def test_a_dry_run_prints_the_group_grant(run):
    # Codex only: on the Claude path the group is never granted with `--add-dir` (Task 13).
    run.skill("demo", _md(), group="pm")
    run.project("some-project")

    result = run("demo", "some-project", "--provider", "codex", "--dry-run")

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    assert _granted_dirs(argv) == [str(run.root / "skills" / "pm")]


# --- a project's product directory --------------------------------------------------------------


def test_an_absolute_product_path_that_exists_is_granted(run):
    product = run.root / "external-product"
    product.mkdir()
    run.skill("demo", _md())
    run.project("some-project", product_path=str(product))

    run("demo", "some-project")

    argv = run.launched_argv()
    # The pin grants its own root too (pin delivery, unconditional) — the product rides with it.
    assert _granted_dirs(argv) == [str(product), str(run.pin_root)]


def test_a_tilde_product_path_is_expanded_before_it_is_granted(run):
    (run.home / "prod").mkdir()
    run.skill("demo", _md())
    run.project("some-project", product_path="~/prod")

    run("demo", "some-project")

    argv = run.launched_argv()
    assert _granted_dirs(argv) == [str(run.home / "prod"), str(run.pin_root)]


@pytest.mark.parametrize(
    "product_path, card, warning",
    [
        ("products/thing", True, None),
        ("/no/such/product/dir", True, "does not exist"),
        (None, True, "no 'Product path:' line"),
        (None, False, "no project card"),
    ],
)
def test_no_product_grant_is_ever_a_refusal(run, product_path, card, warning):
    # No product `--add-dir` — the pin's own trailing `--add-dir <pin root>` (Task 13) is the only
    # one left, not an empty list.
    run.skill("demo", _md())
    run.project("some-project", product_path=product_path, card=card)

    result = run("demo", "some-project")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    granted = _granted_dirs(argv)
    assert granted == [str(run.pin_root)]
    if warning:
        assert warning in result.stdout


# --- instance root ---------------------------------------------------------------------------


def test_instance_root_as_the_first_argument_sets_the_root(demo, tmp_path_factory):
    elsewhere = tmp_path_factory.mktemp("elsewhere")

    result = demo("--instance-root", str(demo.root), "demo", "some-project", "--dry-run", cwd=str(elsewhere))

    assert result.returncode == 0, result.stderr
    assert "Argument:  <project> some-project" in result.stdout


# --- telemetry -----------------------------------------------------------------------------------


def test_a_present_instrument_endpoint_hands_the_spawn_settings(demo, tmp_path):
    # `--settings` is now unconditional under a pin (Task 7's merged document, always present) —
    # the meaningful assertion is the merged document's own `env`, not `--settings`'s bare presence.
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    demo.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)

    result = demo("demo", "some-project")

    assert result.returncode == 0, result.stderr
    argv = demo.launched_argv()
    settings_path = Path(argv[argv.index("--settings") + 1])
    merged = json.loads(settings_path.read_text())
    assert merged["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://127.0.0.1:9/v1"


def test_claude_argv_carries_instrument_settings_once(demo, tmp_path):
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    demo.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)

    result = demo("demo", "some-project")

    assert result.returncode == 0, result.stderr
    assert demo.launched_argv().count("--settings") == 1


def test_a_missing_instrument_library_leaves_the_launch_uninstrumented_but_successful(demo, tmp_path_factory):
    script = _isolated_core(tmp_path_factory, "skill_path.py", "detach_watcher.sh")

    result = demo("demo", "some-project", script=script)

    assert result.returncode == 0, result.stderr
    assert "no instrument library at" in result.stdout
    argv = demo.launched_argv()
    settings_path = Path(argv[argv.index("--settings") + 1])
    merged = json.loads(settings_path.read_text())
    assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in merged.get("env", {})


_REFUSING_RUNNER = """\
import sys
sys.stderr.write("agent_run: refused for the test\\n")
sys.exit(2)
"""


def test_a_refusal_from_the_claude_builder_is_the_launchers_refusal(demo, tmp_path_factory):
    """The Claude argv is read from `agent_run.py --print-argv`. A refusal there used to be
    swallowed by the process substitution, and the launcher went on with an empty argv — under
    bash 3.2 it died on `claude_argv[@]: unbound variable`, under bash 4.4+ it launched nothing and
    said so. The runner's own message reaches the caller, the launcher names the refusal and its
    exit code, and nothing spawns."""
    script = _isolated_core(tmp_path_factory, "skill_path.py", "detach_watcher.sh")
    (script.parents[2] / "tools" / "agent_run.py").write_text(_REFUSING_RUNNER)

    result = demo("demo", "some-project", script=script)

    assert result.returncode != 0
    assert "agent_run: refused for the test" in result.stderr
    assert "the launch was refused (exit 2)" in result.stderr
    assert "unbound variable" not in result.stderr
    assert "Launched." not in result.stdout
    assert demo.launched_argv(wait=_ABSENT_WAIT) == []


_SILENT_RUNNER = """\
import sys
sys.exit(0)
"""


def test_a_builder_that_prints_no_command_is_refused(demo, tmp_path_factory):
    """The other half of the same fix: a builder that exits 0 and prints nothing leaves an empty
    argv, and the launcher refuses it by name rather than launching an empty command."""
    script = _isolated_core(tmp_path_factory, "skill_path.py", "detach_watcher.sh")
    (script.parents[2] / "tools" / "agent_run.py").write_text(_SILENT_RUNNER)

    result = demo("demo", "some-project", script=script)

    assert result.returncode == 1
    assert "the launch printed no run record" in result.stderr
    assert "unbound variable" not in result.stderr
    assert "Launched." not in result.stdout
    assert demo.launched_argv(wait=_ABSENT_WAIT) == []


# --- the completion watch -----------------------------------------------------------------------


def test_the_watcher_is_told_the_label_the_prompt_and_the_launch_output(demo):
    demo("demo", "some-project")

    argv = demo.watcher_argv()
    assert argv != []
    # Outside git, the instance is named by the instance root's own folder.
    assert argv[argv.index("--label") + 1] == f"{demo.root.name} · some-project · demo"
    assert argv[argv.index("--provider") + 1] == "claude"
    assert argv[argv.index("--pid") + 1].isdigit()
    assert argv[argv.index("--log") + 1].startswith(str(demo.root / "system" / "logs" / "claude-demo-"))
    reporter = argv[argv.index("--reporter") + 1]
    assert reporter == "generic"
    assert reporter in _registered_reporter_names()
    assert argv[argv.index("--cwd") + 1] == str(demo.root)


def test_a_declaration_with_no_reporter_is_watched_by_generic_reading_nothing(demo):
    # Every launcher.md written before **Reporter:** existed takes this path, unchanged.
    demo("demo", "some-project")

    argv = demo.watcher_argv()
    assert argv[argv.index("--reporter") + 1] == "generic"
    assert "--artifact-path" not in argv and "--product-path" not in argv


def test_a_declared_reporter_reading_the_product_is_handed_the_product_path(run):
    (run.root / "products" / "thing").mkdir(parents=True)
    run.skill("demo", _md(reporter="prd", reads="product"))
    run.project("some-project", product_path="products/thing")

    result = run("demo", "some-project")

    assert result.returncode == 0, result.stderr
    argv = run.watcher_argv()
    assert argv[argv.index("--reporter") + 1] == "prd"
    assert argv[argv.index("--artifact-path") + 1] == str(run.root / "products" / "thing")
    assert f"Reporter:  prd reads {run.root / 'products' / 'thing'}" in result.stdout


def test_a_declared_reporter_reading_the_project_is_handed_the_project_directory(run):
    run.skill("demo", _md(reporter="agari", reads="project"))
    run.project("some-project")

    result = run("demo", "some-project")

    assert result.returncode == 0, result.stderr
    argv = run.watcher_argv()
    assert argv[argv.index("--reporter") + 1] == "agari"
    assert argv[argv.index("--artifact-path") + 1] == str(run.root / "system" / "projects" / "some-project")


def test_a_declared_reporter_reading_the_instance_is_handed_the_instance_root_with_no_argument(run):
    run.skill("demo", _md(arguments=None, prompt="invoke the demo skill.",
                          reporter="writing-bar", reads="instance"))

    result = run("demo")

    assert result.returncode == 0, result.stderr
    argv = run.watcher_argv()
    assert argv[argv.index("--reporter") + 1] == "writing-bar"
    assert argv[argv.index("--artifact-path") + 1] == str(run.root)
    assert f"Reporter:  writing-bar reads {run.root}" in result.stdout


@pytest.mark.parametrize("dry_run", [False, True])
def test_a_required_program_missing_from_path_refuses_the_launch_naming_it(run, dry_run):
    run.skill("demo", _md(requires="sh kensaiapp-no-such-program"))
    run.project("some-project")

    result = run("demo", "some-project", *(["--dry-run"] if dry_run else []))

    assert result.returncode != 0
    assert "kensaiapp-no-such-program not found on PATH" in result.stderr, result.stderr
    assert "Telemetry:" not in result.stdout
    assert run.launched_argv() == []
    assert run.watcher_argv() == []


def test_required_programs_on_path_let_the_launch_go_on(run):
    run.skill("demo", _md(requires="sh python3"))
    run.project("some-project")

    result = run("demo", "some-project")

    assert result.returncode == 0, result.stderr
    assert run.launched_argv() != []


def test_an_explicit_generic_reporter_needs_nothing_to_read(demo):
    demo.skill("demo", _md(reporter="generic"))

    result = demo("demo", "some-project")

    assert result.returncode == 0, result.stderr
    argv = demo.watcher_argv()
    assert argv[argv.index("--reporter") + 1] == "generic"
    assert "--artifact-path" not in argv


def test_the_dry_run_names_the_reporter_and_watches_nothing(run):
    run.skill("demo", _md(reporter="agari", reads="project"))
    run.project("some-project")

    result = run("demo", "some-project", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert f"Reporter:  agari reads {run.root / 'system' / 'projects' / 'some-project'}" in result.stdout
    assert run.watcher_argv() == []


@pytest.mark.parametrize(
    "product_path, card",
    [
        ("products/missing", True),
        (None, True),
        (None, False),
    ],
)
def test_a_reporter_with_nothing_to_read_falls_back_to_generic_and_still_launches(run, product_path, card):
    run.skill("demo", _md(reporter="prd", reads="product"))
    run.project("some-project", product_path=product_path, card=card)

    result = run("demo", "some-project")

    assert result.returncode == 0, result.stderr
    assert "falls back to generic" in result.stdout
    assert run.launched_argv() != []
    argv = run.watcher_argv()
    assert argv[argv.index("--reporter") + 1] == "generic"
    assert "--artifact-path" not in argv


def test_an_optional_project_not_given_falls_back_to_generic(run):
    run.skill(
        "demo",
        _md(arguments="[<project>]", prompt="invoke demo[ for {project}].", reporter="agari", reads="project"),
    )

    result = run("demo")

    assert result.returncode == 0, result.stderr
    assert "falls back to generic" in result.stdout
    argv = run.watcher_argv()
    assert argv[argv.index("--reporter") + 1] == "generic"


def test_a_run_with_no_project_is_labelled_with_the_instance_and_the_skill(run):
    run.skill("demo", _md(arguments=None, prompt="invoke the demo skill."))

    run("demo")

    argv = run.watcher_argv()
    assert argv[argv.index("--label") + 1] == f"{run.root.name} · demo"


def test_a_run_from_a_worktree_is_labelled_with_the_checkout_it_was_cut_from(demo, tmp_path_factory):
    git = ["git", "-c", "user.email=suite@example.invalid", "-c", "user.name=suite"]
    subprocess.run(git + ["-C", str(demo.root), "init", "-q"], check=True)
    subprocess.run(git + ["-C", str(demo.root), "commit", "-q", "--allow-empty", "-m", "base"], check=True)
    tree = tmp_path_factory.mktemp("worktrees") / "branch-tree"
    subprocess.run(git + ["-C", str(demo.root), "worktree", "add", "-q", str(tree)], check=True)
    shutil.copytree(demo.root / ".claude", tree / ".claude")
    shutil.copytree(demo.root / "system", tree / "system")
    shutil.copy2(demo.root / ".providers.toml", tree / ".providers.toml")

    result = demo("demo", "some-project", cwd=str(tree))

    assert result.returncode == 0, result.stderr
    argv = demo.watcher_argv()
    assert argv[argv.index("--label") + 1] == f"{demo.root.name} · some-project · demo"


def test_keep_awake_is_forwarded_to_the_detached_completion_watcher(demo):
    demo.hold_watcher_until_kept_awake()
    result = demo("demo", "some-project", "--keep-awake")

    assert result.returncode == 0, result.stderr
    assert "-i" in demo.caffeinate_argv()


def test_no_notifier_still_watches_so_a_chain_hook_still_fires(demo):
    """The run is watched whether or not anything can be told: the watch is what hands a chain its
    outcome. With no notifier the watcher is told to notify nothing."""
    demo.env["LAUNCH_SKILL_NOTIFIER"] = str(demo.root / "nope" / "missing.sh")

    result = demo("demo", "some-project")

    assert result.returncode == 0, result.stderr
    assert demo.launched_argv() != []
    argv = demo.watcher_argv()
    assert argv[argv.index("--notify") + 1] == "/usr/bin/true"


def test_a_claude_run_hands_the_chain_hook_its_outcome_without_a_notifier(demo):
    hook_log = demo.root / "hook-outcome"
    hook = demo.root / "hook.sh"
    hook.write_text(
        "#!/usr/bin/env bash\n"
        f"printf '%s' \"$1\" > {shlex.quote(str(hook_log))}\n"
    )
    hook.chmod(0o755)
    demo.env["DETACH_WATCHER_ON_COMPLETE"] = str(hook)
    demo.env["LAUNCH_SKILL_NOTIFIER"] = str(demo.root / "missing-notifier")
    demo.env.pop("LAUNCH_SKILL_WATCHER")

    result = demo("demo", "some-project")

    assert result.returncode == 0, result.stderr
    for _ in range(int(_KEEPAWAKE_WAIT / 0.05)):
        if hook_log.exists():
            break
        time.sleep(0.05)
    assert hook_log.read_text() == "completed"


def test_the_watcher_default_resolves_through_core_dir_with_the_override_unset(demo):
    demo.env.pop("LAUNCH_SKILL_WATCHER")

    result = demo("demo", "some-project")

    assert result.returncode == 0, result.stderr
    assert "completion watch skipped" not in result.stdout
    assert "Completion watch:" in result.stdout
    logs_dir = demo.root / "system" / "logs"
    assert any(logs_dir.glob("watch-demo-*.log"))


def test_a_missing_detach_library_prints_one_skip_line_and_the_launch_still_succeeds(demo, tmp_path_factory):
    script = _isolated_core(tmp_path_factory, "skill_path.py")

    result = demo("demo", "some-project", script=script)

    assert result.returncode == 0, result.stderr
    assert demo.launched_argv() != []
    assert "no completion-watch library at" in result.stdout


# --- the file itself -----------------------------------------------------------------------------


def _code_lines():
    return [l for l in _SCRIPT.read_text().splitlines() if not l.lstrip().startswith("#")]


def test_the_launcher_names_no_skill():
    code = "\n".join(_code_lines())
    assert "tobiishi" not in code


def test_the_shared_homes_are_used_never_copied():
    code = "\n".join(_code_lines())
    assert "source \"$DETACH_LIB\"" in code
    assert "nohup python3" not in code
    assert not any("caffeinate" in l for l in _code_lines())
    assert "backgrounded" not in code


def test_no_worktree_and_no_branch_is_ever_created(demo):
    code = "\n".join(_code_lines())
    assert re.search(r"git\s+(worktree|branch|checkout)\b", code) is None

    demo("demo", "some-project")

    assert not (demo.root / ".worktrees").exists()


def test_a_script_with_no_launchers_ancestor_exits_one(tmp_path):
    orphan_dir = tmp_path / "somewhere" / "with" / "no" / "ancestor"
    orphan_dir.mkdir(parents=True)
    orphan = orphan_dir / "launcher.sh"
    shutil.copy(_SCRIPT, orphan)
    orphan.chmod(0o755)

    result = subprocess.run([str(orphan)], cwd=str(tmp_path), capture_output=True, text=True)

    assert result.returncode == 1
    stderr_lines = [l for l in result.stderr.splitlines() if l.strip()]
    assert len(stderr_lines) == 1
    assert "/launchers/" in stderr_lines[0] and str(orphan_dir) in stderr_lines[0]


def test_the_launcher_is_mode_0755_and_opens_with_the_env_bash_shebang():
    assert _SCRIPT.stat().st_mode & 0o777 == 0o755
    with open(_SCRIPT) as fh:
        assert fh.readline().rstrip("\n") == "#!/usr/bin/env bash"


def test_the_structure_map_records_the_launcher_its_suite_and_launcher_md():
    text = (_CORE_DIR / "doctrine" / "setup" / "kensaiapp_structure.md").read_text()
    start = text.index("### Owner-run launcher folder")
    launchers_section = text[start : text.index("\n### ", start + 1)]
    assert "core/launchers/skill/launcher.sh" in launchers_section
    assert "core/launchers/skill/test_skill.py" in launchers_section

    start = text.index("#### Skills — vendored skill definitions")
    skills_section = text[start : text.index("\n#### ", start + 1)]
    assert "launcher.md" in skills_section


# --- characterization: the Codex prompt, composed whole (refactor sweep, 2026-09-23) -----------
# These pin the exact sentence sequence the launcher composes for Codex, in both arms, so a
# change to how the prompt is assembled that alters one byte of it goes red. The adapter may
# wrap the prompt with text of its own, so each asserts the composed prompt is contained whole.


def test_codex_prompt_with_an_agent_is_composed_exactly(demo):
    result = demo("demo", "some-project", "--provider", "codex", "--dry-run")

    assert result.returncode == 0, result.stderr
    prompt = _dry_run_argv(result.stdout)[-1]
    expected = (
        "You are running a Kensaiapp unattended skill as the pm agent. "
        f"For every instruction in this run, <CORE> resolves to: {demo.core_dir}. "
        f"The instance root is: {demo.root}. "
        "Before doing anything else, read and follow the agent instructions in: "
        f"{demo.root}/.claude/agents/pm.md. "
        "Execute this fixed task: invoke the demo skill for the some-project project."
    )
    assert expected in prompt


def test_codex_prompt_without_an_agent_is_composed_exactly(run):
    _intelligence(run.skill("demo", _md(agent=None)), "codex")
    run.project("some-project")

    result = run("demo", "some-project", "--provider", "codex", "--dry-run")

    assert result.returncode == 0, result.stderr
    prompt = _dry_run_argv(result.stdout)[-1]
    expected = (
        "You are running a Kensaiapp unattended skill. "
        f"For every instruction in this run, <CORE> resolves to: {run.core_dir}. "
        f"The instance root is: {run.root}. "
        "Execute this fixed task: invoke the demo skill for the some-project project."
    )
    assert expected in prompt


# --- a caller-named tier (CP-190 … CP-192) --------------------------------------------------------
#     change 2026-09-30_runs-record-provider-model-effort-and-source

_TIER_VOCABULARY = ("fable", "opus", "sonnet", "haiku")
_CP_192 = "its model and effort come from its intelligence file, not from a tier"


def _stderr_lines(result):
    return [line for line in result.stderr.splitlines() if line.strip()]


@pytest.mark.parametrize("mode", _MODES)
def test_bogus_tier_is_refused_naming_the_four_tiers(demo, mode):
    cli = ["demo", "some-project", "--provider", "codex", "--model-tier", "bogus"]

    result = demo(*cli, *(["--dry-run"] if mode == "--dry-run" else []))

    assert result.returncode != 0
    lines = _stderr_lines(result)
    assert len(lines) == 1, result.stderr
    assert "bogus" in lines[0]
    for tier in _TIER_VOCABULARY:
        assert tier in lines[0]
    _nothing_spawned(demo)
    assert demo.watcher_argv() == []


@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize(
    "files", [("codex",), ("claude",)], ids=["providers-file", "other-file-only"]
)
def test_tier_on_a_skill_with_an_intelligence_folder_is_refused(run, mode, files):
    """CP-192 holds whenever the folder exists — including a folder with no file for the selected
    provider, which without a tier would be refused as the missing file instead."""
    skill_dir = run.skill("demo", _md())
    for provider in files:
        _intelligence(skill_dir, provider, model="claude-m-1", effort="low")
    run.project("some-project")
    cli = ["demo", "some-project", "--provider", "codex", "--model-tier", "sonnet"]

    result = run(*cli, *(["--dry-run"] if mode == "--dry-run" else []))

    assert result.returncode != 0
    lines = _stderr_lines(result)
    assert len(lines) == 1, result.stderr
    assert _CP_192 in lines[0]
    assert str(skill_dir / "intelligence" / "codex.md") not in result.stderr
    _nothing_spawned(run)


def test_tier_on_a_skill_with_a_malformed_intelligence_file_is_refused_as_cp_192(run):
    skill_dir = run.skill("demo", _md())
    path = _intelligence(skill_dir, "codex", text="**Model:** two words\n")
    run.project("some-project")

    result = run("demo", "some-project", "--provider", "codex", "--model-tier", "sonnet")

    assert result.returncode != 0
    assert _CP_192 in result.stderr
    assert str(path) not in result.stderr
    _nothing_spawned(run)


def test_bogus_tier_on_an_intelligence_skill_gets_the_vocabulary_line(run):
    _intelligence(run.skill("demo", _md()), "codex", model="claude-m-1")
    run.project("some-project")

    result = run("demo", "some-project", "--provider", "codex", "--model-tier", "bogus")

    assert result.returncode != 0
    assert _CP_192 not in result.stderr
    for tier in _TIER_VOCABULARY:
        assert tier in result.stderr
    _nothing_spawned(run)


def test_model_tier_without_a_value_is_refused(demo):
    result = demo("demo", "some-project", "--model-tier")

    assert result.returncode != 0
    assert "--model-tier" in result.stderr
    _nothing_spawned(demo)


def test_model_tier_may_sit_anywhere_after_the_skill(demo):
    result = demo(
        "demo", "--model-tier", "sonnet", "some-project", "--provider", "codex", "--dry-run"
    )

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    assert _models(argv) == ["gpt-5.6-terra"]
    assert _efforts(argv, "codex") == ["medium"]


@pytest.mark.parametrize(
    "provider, model, effort",
    [("claude", "sonnet", []), ("codex", "gpt-5.6-terra", ["medium"]),
     ("gemini", "gemini-3.8-flash-medium", ["medium"])],
)
def test_a_tier_reaches_the_real_launch_on_every_provider(demo, provider, model, effort):
    """The tier path hands the runner the tier, on all three branches — the real launch, not only
    the dry run, goes at model_assignment.py's answer."""
    result, argv = _launch(demo, provider, "real")
    assert result.returncode == 0, result.stderr
    assert _models(argv) == []  # without the tier, the provider default
    for name in ("claude_argv.log", "codex_argv.log", "gemini_argv.log"):
        (demo.root / name).unlink(missing_ok=True)

    result = demo("demo", "some-project", "--provider", provider, "--model-tier", "sonnet")

    assert result.returncode == 0, result.stderr
    readers = {"claude": demo.launched_argv, "codex": demo.codex_argv, "gemini": demo.gemini_argv}
    reader = readers[provider]
    argv = reader()
    assert _models(argv) == [model]
    assert _efforts(argv, provider) == effort


def test_a_bogus_tier_is_judged_before_the_skill_resolves(run):
    """The refusal order is provider → tier vocabulary → skill resolution → CP-192
    (tl_instruction Task 2): a bogus tier on a skill that does not exist gets the vocabulary
    line."""
    run.project("some-project")

    result = run("no-such-skill", "some-project", "--provider", "codex", "--model-tier", "bogus")

    assert result.returncode != 0
    lines = _stderr_lines(result)
    assert len(lines) == 1, result.stderr
    for tier in _TIER_VOCABULARY:
        assert tier in lines[0]
    assert "no-such-skill" not in lines[0]
    _nothing_spawned(run)


def test_an_absent_intelligence_resolver_is_refused_naming_it(demo, tmp_path_factory):
    """tl_instruction Task 3: with run_intelligence.py absent the launcher dies naming it, as it
    did for intelligence.py — a run is never launched at a model nothing resolved."""
    script = _isolated_core(tmp_path_factory, "skill_path.py", "detach_watcher.sh")
    (script.parents[2] / "tools" / "run_intelligence.py").unlink()

    result = demo("demo", "some-project", script=script)

    assert result.returncode == 1, result.stdout
    assert "no intelligence resolver at" in result.stderr
    assert "run_intelligence.py" in result.stderr


def test_a_launch_records_its_run_and_watcher_for_the_engine_that_named_a_file(demo):
    identity = demo.root / "launch.identity.json"
    demo.env["DETACHED_RUN_IDENTITY_FILE"] = str(identity)

    result = demo("demo", "some-project")

    assert result.returncode == 0, result.stderr
    assert_launch_recorded_its_identity(result.stdout, identity)


def test_a_launch_no_engine_started_leaves_a_run_record_the_board_reads(demo):
    logs = demo.root / "system" / "logs"
    demo.env.pop("DETACHED_RUN_IDENTITY_FILE", None)

    result = demo("demo", "some-project")

    assert result.returncode == 0, result.stderr
    identity = logs / "skill-demo@some-project.identity.json"
    assert_launch_recorded_its_identity(result.stdout, identity)
    record = json.loads((logs / "skill-demo@some-project.run.json").read_text())
    assert (record["skill"], record["project"], record["identity"]) == (
        "demo", "some-project", str(identity))
    assert datetime.fromisoformat(record["started_at"]).tzinfo is not None


def test_a_launch_an_engine_started_leaves_no_run_record(demo):
    demo.env["DETACHED_RUN_IDENTITY_FILE"] = str(demo.root / "launch.identity.json")

    result = demo("demo", "some-project")

    assert result.returncode == 0, result.stderr
    assert list((demo.root / "system" / "logs").glob("skill-*")) == []


# --- hf: the Claude run, aimed at Hugging Face's router (CP-424 … CP-432) ------------------------

_HF_SENTINEL = "hf_SKILL_sentinel_do_not_leak"
_HF_SONNET = "MiniMaxAI/MiniMax-M3:novita"
_SKILL_USAGE = (
    "usage: <CORE>/launchers/skill/launcher.sh <skill> [<argument>...] "
    "[--provider claude|codex|gemini|hf|ollama] [--model-tier fable|opus|sonnet|haiku] "
    "[--dry-run] [--keep-awake]"
)


def _give_hf_token(run, value=_HF_SENTINEL):
    (run.home / ".env").write_text(f"HF_TOKEN={value}\n")


@pytest.mark.parametrize("channel", ["flag", "variable", "provider-file"])
def test_hf_is_accepted_by_flag_variable_and_provider_file(demo, channel):
    _give_hf_token(demo)
    args, script = [], _SCRIPT
    if channel == "flag":
        args = ["--provider", "hf"]
    elif channel == "variable":
        demo.env["KENSAIAPP_AGENT_PROVIDER"] = "hf"
    else:
        script = _instance_provider_file(demo, _skill_entry("hf"))

    result = demo("demo", "some-project", *args, "--dry-run", script=script)

    assert result.returncode == 0, result.stderr
    assert "Provider:  hf" in result.stdout


def test_hf_dry_run_is_a_claude_turn_with_the_pin_delivery(demo):
    _give_hf_token(demo)

    result = demo("demo", "some-project", "--provider", "hf", "--dry-run")

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    assert argv[:4] == ["claude", "--print", "--output-format", "stream-json"]
    assert "--session-id" in argv
    assert argv[argv.index("--setting-sources") + 1] == "user"
    assert "--plugin-dir" in argv
    assert _granted_dirs(argv) == [str(demo.pin_root)]
    assert argv[argv.index("--agent") + 1] == "pm"
    assert "invoke the demo skill for the some-project project." in argv[-1]
    assert "Execute this fixed task:" not in argv[-1]


def test_hf_dry_run_prints_exactly_the_command_a_real_launch_spawns(demo):
    _give_hf_token(demo)
    dry = demo("demo", "some-project", "--provider", "hf", "--dry-run")
    assert dry.returncode == 0, dry.stderr
    printed = _dry_run_argv(dry.stdout)
    assert demo.launched_argv(wait=_ABSENT_WAIT) == []

    real = demo("demo", "some-project", "--provider", "hf")
    assert real.returncode == 0, real.stderr

    assert printed[0] == "claude"
    assert _without_session_id(printed[1:]) == _without_session_id(demo.launched_argv())


def test_an_hf_launch_carries_the_product_dir_and_the_telemetry_settings(run, tmp_path):
    product = run.root / "external-product"
    product.mkdir()
    run.skill("demo", _md())
    run.project("some-project", product_path=str(product))
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    _give_hf_token(run)

    result = run("demo", "some-project", "--provider", "hf")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert _granted_dirs(argv) == [str(product), str(run.pin_root)]
    assert argv.count("--settings") == 1
    merged = json.loads(Path(argv[argv.index("--settings") + 1]).read_text())
    assert merged["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://127.0.0.1:9/v1"


def test_an_hf_tier_puts_hfs_model_on_the_command(demo):
    _give_hf_token(demo)

    result = demo("demo", "some-project", "--provider", "hf", "--model-tier", "sonnet")

    assert result.returncode == 0, result.stderr
    assert _models(demo.launched_argv()) == [_HF_SONNET]


@pytest.mark.parametrize("mode", _MODES)
def test_the_fable_tier_is_refused_on_hf_before_anything_spawns(demo, mode):
    _give_hf_token(demo)
    flags = ["--dry-run"] if mode == "--dry-run" else []

    result = demo("demo", "some-project", "--provider", "hf", "--model-tier", "fable", *flags)

    assert result.returncode != 0
    assert "provider 'hf' has no model for tier 'fable'" in result.stderr
    _nothing_spawned(demo)


@pytest.mark.parametrize("mode", _MODES)
def test_an_hf_intelligence_file_puts_its_model_and_effort_on_the_command(run, mode):
    skill_dir = run.skill("demo", _md())
    hf_file = _intelligence(skill_dir, "hf", model="open/model-1", effort="low")
    run.project("some-project")
    _give_hf_token(run)

    result, argv = _launch(run, "hf", mode)

    assert result.returncode == 0, result.stderr
    assert _models(argv) == ["open/model-1"]
    assert _efforts(argv, "hf") == ["low"]
    if mode == "--dry-run":
        assert f"Intelligence: {hf_file}" in result.stdout


@pytest.mark.parametrize("mode", _MODES)
def test_a_folder_without_hf_md_is_refused_naming_the_path(run, mode):
    skill_dir = run.skill("demo", _md())
    _intelligence(skill_dir, "claude")
    run.project("some-project")
    _give_hf_token(run)
    flags = ["--dry-run"] if mode == "--dry-run" else []

    result = run("demo", "some-project", "--provider", "hf", *flags)

    assert result.returncode != 0
    assert "intelligence/hf.md" in result.stderr
    _nothing_spawned(run)


@pytest.mark.parametrize("token", [None, ""], ids=["no-env-file", "empty-token"])
@pytest.mark.parametrize("mode", _MODES)
def test_hf_with_no_token_is_refused_before_anything_spawns(demo, mode, token):
    if token is not None:
        _give_hf_token(demo, token)
    flags = ["--dry-run"] if mode == "--dry-run" else []

    result = demo("demo", "some-project", "--provider", "hf", *flags)

    assert result.returncode != 0
    assert "HF_TOKEN" in result.stderr
    _nothing_spawned(demo)
    assert demo.watcher_argv() == []


def test_the_hf_token_leaks_nowhere(demo):
    _give_hf_token(demo)

    dry = demo("demo", "some-project", "--provider", "hf", "--dry-run")
    real = demo("demo", "some-project", "--provider", "hf")

    assert dry.returncode == 0 and real.returncode == 0, (dry.stderr, real.stderr)
    spoken = [dry.stdout, dry.stderr, real.stdout, real.stderr]
    spoken += demo.launched_argv() + demo.watcher_argv()
    assert not any(_HF_SENTINEL in text for text in spoken)
    kept_secret = demo.home / ".env"
    leaked = [
        str(path)
        for path in demo.root.rglob("*")
        if path.is_file() and path != kept_secret
        and _HF_SENTINEL.encode() in path.read_bytes()
    ]
    assert leaked == []


def test_an_hf_run_is_watched_naming_provider_hf(demo):
    _give_hf_token(demo)

    result = demo("demo", "some-project", "--provider", "hf")

    assert result.returncode == 0, result.stderr
    watcher = demo.watcher_argv()
    assert watcher[watcher.index("--provider") + 1] == "hf"


def test_an_unknown_provider_is_refused_naming_the_five(demo):
    result = demo("demo", "some-project", "--provider", "other")

    assert result.returncode != 0
    assert (
        "unknown provider 'other' — available providers: claude, codex, gemini, hf, ollama. "
        + _SKILL_USAGE
    ) in result.stderr
    _nothing_spawned(demo)


def test_a_provider_flag_with_no_value_is_refused_naming_the_five(demo):
    result = demo("demo", "some-project", "--provider")

    assert result.returncode != 0
    assert f"--provider needs claude, codex, gemini, hf or ollama. {_SKILL_USAGE}" in result.stderr


def test_the_usage_line_names_hf_and_ollama(run):
    result = run()

    assert result.returncode != 0
    assert _SKILL_USAGE in result.stderr


def test_the_header_usage_names_hf_and_ollama():
    header = {line.lstrip("#").strip() for line in _SCRIPT.read_text().splitlines()
              if line.startswith("#")}

    assert _SKILL_USAGE.removeprefix("usage: ") in header
    assert (
        "--keep-awake  keep the Mac awake for the observed run's duration, whatever the provider"
    ) in header
    assert (
        "--provider    claude, codex, gemini, hf or ollama; else KENSAIAPP_AGENT_PROVIDER, else the"
    ) in header
    assert (
        "`launchers.skill` entry of .providers.toml at the instance root, else a"
    ) in header
    assert (
        "refusal — there is no default. An hf run is the Claude run, aimed at Hugging"
    ) in header
    assert "Face's router, and it is refused unless ~/.env holds a non-empty HF_TOKEN." in header
    assert (
        "An ollama run is the Claude run, aimed at the local Ollama server, and it is"
    ) in header
    assert "refused unless that server answers" in header


# --- hf, from the spec's own words (added by development-code-integrity) -------------------------

_HF_ROUTER = "https://router.huggingface.co"


def _settings_of(argv):
    return json.loads(Path(argv[argv.index("--settings") + 1]).read_text())


@pytest.mark.parametrize("mode", _MODES)
def test_an_hf_launch_is_aimed_at_hugging_faces_router(demo, mode):
    # CP-426: "It is pointed at Hugging Face's router."
    _give_hf_token(demo)

    result, argv = _launch(demo, "hf", mode)

    assert result.returncode == 0, result.stderr
    assert _settings_of(argv)["env"]["ANTHROPIC_BASE_URL"] == _HF_ROUTER


@pytest.mark.parametrize("mode", _MODES)
def test_an_hf_skill_with_no_intelligence_folder_takes_the_provider_default(demo, mode):
    # CP-427: no intelligence/ folder and no --model-tier → the provider default, as on claude.
    _give_hf_token(demo)

    result, argv = _launch(demo, "hf", mode)

    assert result.returncode == 0, result.stderr
    assert _models(argv) == []
    assert _efforts(argv, "hf") == []
    assert "Intelligence: none — provider default" in result.stdout


# --- ollama: the Claude run, aimed at the local Ollama server (CP-499 … CP-502) -----------------

_OLLAMA_SONNET = "qwen3-coder:30b"
_OLLAMA_FABLE = "qwen3.8:27b"
_NO_SERVER = "provider 'ollama' needs an Ollama server answering at {address}"


def _point_at(run, server):
    """Aim the run at an answering stub server; a case that skips this keeps the guard's
    address, where nothing listens."""
    run.env["KENSAIAPP_OLLAMA_URL"] = server.address


@pytest.mark.parametrize("channel", ["flag", "variable", "provider-file"])
def test_ollama_is_accepted_by_flag_variable_and_provider_file(demo, ollama_server, channel):
    _point_at(demo, ollama_server)
    args, script = [], _SCRIPT
    if channel == "flag":
        args = ["--provider", "ollama"]
    elif channel == "variable":
        demo.env["KENSAIAPP_AGENT_PROVIDER"] = "ollama"
    else:
        script = _instance_provider_file(demo, _skill_entry("ollama"))

    result = demo("demo", "some-project", *args, "--dry-run", script=script)

    assert result.returncode == 0, result.stderr
    assert "Provider:  ollama" in result.stdout


def test_ollama_dry_run_is_a_claude_turn_with_the_pin_delivery(demo, ollama_server):
    _point_at(demo, ollama_server)

    result = demo("demo", "some-project", "--provider", "ollama", "--dry-run")

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    assert argv[:4] == ["claude", "--print", "--output-format", "stream-json"]
    assert "--session-id" in argv
    assert argv[argv.index("--setting-sources") + 1] == "user"
    assert "--plugin-dir" in argv
    assert _granted_dirs(argv) == [str(demo.pin_root)]
    assert argv[argv.index("--agent") + 1] == "pm"
    assert "invoke the demo skill for the some-project project." in argv[-1]
    assert "Execute this fixed task:" not in argv[-1]


def test_ollama_dry_run_prints_exactly_the_command_a_real_launch_spawns(demo, ollama_server):
    _point_at(demo, ollama_server)
    dry = demo("demo", "some-project", "--provider", "ollama", "--dry-run")
    assert dry.returncode == 0, dry.stderr
    printed = _dry_run_argv(dry.stdout)
    assert demo.launched_argv(wait=_ABSENT_WAIT) == []

    real = demo("demo", "some-project", "--provider", "ollama")
    assert real.returncode == 0, real.stderr

    assert printed[0] == "claude"
    assert _without_session_id(printed[1:]) == _without_session_id(demo.launched_argv())


def test_an_ollama_launch_carries_the_product_dir_and_the_telemetry_settings(
    run, tmp_path, ollama_server
):
    product = run.root / "external-product"
    product.mkdir()
    run.skill("demo", _md())
    run.project("some-project", product_path=str(product))
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    _point_at(run, ollama_server)

    result = run("demo", "some-project", "--provider", "ollama")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert _granted_dirs(argv) == [str(product), str(run.pin_root)]
    assert argv.count("--settings") == 1
    merged = json.loads(Path(argv[argv.index("--settings") + 1]).read_text())
    assert merged["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://127.0.0.1:9/v1"


@pytest.mark.parametrize(
    "tier, model", [("sonnet", _OLLAMA_SONNET), ("fable", _OLLAMA_FABLE)]
)
def test_an_ollama_tier_puts_the_local_model_on_the_command(demo, ollama_server, tier, model):
    _point_at(demo, ollama_server)

    result = demo("demo", "some-project", "--provider", "ollama", "--model-tier", tier)

    assert result.returncode == 0, result.stderr
    assert _models(demo.launched_argv()) == [model]


@pytest.mark.parametrize("mode", _MODES)
def test_a_folder_without_ollama_md_is_refused_naming_the_path(run, ollama_server, mode):
    skill_dir = run.skill("demo", _md())
    _intelligence(skill_dir, "claude")
    run.project("some-project")
    _point_at(run, ollama_server)
    flags = ["--dry-run"] if mode == "--dry-run" else []

    result = run("demo", "some-project", "--provider", "ollama", *flags)

    assert result.returncode != 0
    assert "intelligence/ollama.md" in result.stderr
    _nothing_spawned(run)


@pytest.mark.parametrize("mode", _MODES)
def test_an_ollama_skill_with_no_intelligence_folder_takes_the_provider_default(
    demo, ollama_server, mode
):
    _point_at(demo, ollama_server)

    result, argv = _launch(demo, "ollama", mode)

    assert result.returncode == 0, result.stderr
    assert _models(argv) == []
    assert _efforts(argv, "ollama") == []
    assert "Intelligence: none — provider default" in result.stdout


@pytest.mark.parametrize("mode", _MODES)
def test_ollama_with_no_server_is_refused_before_anything_spawns(demo, mode):
    flags = ["--dry-run"] if mode == "--dry-run" else []

    result = demo("demo", "some-project", "--provider", "ollama", *flags)

    assert result.returncode != 0
    assert _NO_SERVER.format(address=demo.env["KENSAIAPP_OLLAMA_URL"]) in result.stderr
    _nothing_spawned(demo)
    assert demo.watcher_argv() == []


@pytest.mark.parametrize("mode", _MODES)
def test_an_ollama_launch_is_aimed_at_the_local_server(demo, ollama_server, mode):
    _point_at(demo, ollama_server)

    result, argv = _launch(demo, "ollama", mode)

    assert result.returncode == 0, result.stderr
    env = _settings_of(argv)["env"]
    assert env["ANTHROPIC_BASE_URL"] == ollama_server.address
    assert env["ANTHROPIC_AUTH_TOKEN"] == "ollama"


def test_an_ollama_run_is_watched_naming_provider_ollama(demo, ollama_server):
    _point_at(demo, ollama_server)

    result = demo("demo", "some-project", "--provider", "ollama")

    assert result.returncode == 0, result.stderr
    watcher = demo.watcher_argv()
    assert watcher[watcher.index("--provider") + 1] == "ollama"


_README_STATUS_DIR = _REPO / "skills" / "content-editor" / ".claude" / "skills" / "readme-status"
_README_STATUS_PROMPT = "invoke the readme-status skill for the some-project project."


def _install_readme_status(run):
    """The shipped package and the shipped `content-editor` agent, so no old pin stands in."""
    shutil.copy(_group_agent("content-editor"),
                run.root / ".claude" / "agents" / "content-editor.md")
    run.skill("readme-status", (_README_STATUS_DIR / "launcher.md").read_text(),
              group="content-editor")


def test_the_shipped_readme_status_files_exist():
    for component in ("SKILL.md", "prompts/thin.md", "launcher.md"):
        assert (_README_STATUS_DIR / component).is_file(), component
    assert "prompts/thin.md" in (_README_STATUS_DIR / "SKILL.md").read_text()


def test_the_shipped_readme_status_carries_its_text_without_a_change_folder():
    package = "\n".join(path.read_text() for path in _README_STATUS_DIR.rglob("*.md"))
    required_text = (
        "readme-status changed no file and made no commit.",
        "It needs Content Editor posture.",
        "readme-status found nothing to change and made no commit.",
        "readme-status made commit `{sha}` in `{checkout}`.",
        "which came in with commit `{sha}`.",
        "Nothing that {the product's name for itself} was defined to do is left to build.",
    )
    for sentence in required_text:
        assert sentence in package, f"Published text missing from the shipped package: {sentence}"
    assert "change_text.md" not in package


def test_the_shipped_readme_status_declaration_launches_under_content_editor_granted_its_group(run):
    _install_readme_status(run)
    run.project("some-project")

    result = run("readme-status", "some-project")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert _prompt_of(argv) == _README_STATUS_PROMPT
    assert argv[argv.index("--agent") + 1] == "content-editor"
    assert "--model" not in argv


def test_the_shipped_readme_status_declaration_grants_an_external_product(run):
    _install_readme_status(run)
    product = run.root / "external-product"
    product.mkdir()
    run.project("some-project", product_path=str(product))

    result = run("readme-status", "some-project")

    assert result.returncode == 0, result.stderr
    assert _granted_dirs(run.launched_argv()) == [str(product), str(run.pin_root)]


def test_the_shipped_readme_status_dry_run_reports_skill_group_and_product_and_launches_nothing(
    run,
):
    _install_readme_status(run)
    product = run.root / "external-product"
    product.mkdir()
    run.project("some-project", product_path=str(product))

    result = run("readme-status", "some-project", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "readme-status" in result.stdout
    assert "skills/content-editor" in result.stdout
    assert "<project> some-project" in result.stdout
    assert str(product) in result.stdout
    _nothing_spawned(run)
    assert run.watcher_argv() == []


def test_the_shipped_readme_status_declaration_carries_no_reporter_or_reads():
    declaration = (_README_STATUS_DIR / "launcher.md").read_text()
    assert _field(declaration, "Reporter") is None
    assert _field(declaration, "Reads") is None


_FIRST_WHAT_LEFT_DIR = _REPO / "skills" / "cpo" / ".claude" / "skills" / "first-what-left"
_FIRST_WHAT_LEFT_PROMPT = "invoke the first-what-left skill for the some-project project."
_FIRST_WHAT_LEFT_FILES = {
    "SKILL.md",
    "launcher.md",
    "prompts/thin.md",
    "intelligence/claude.md",
    "intelligence/codex.md",
    "intelligence/gemini.md",
    "intelligence/ollama.md",
}
_FIRST_WHAT_LEFT_ANCHORS = (
    "project.md",
    "nominal",
    "docs/what_left.md",
    "agari.md",
    "agari_open_issues.md",
    "docs/PRD.md",
)


def test_the_shipped_first_what_left_declaration_launches_under_cpo(run):
    shutil.copy(_group_agent("cpo"), run.root / ".claude" / "agents" / "cpo.md")
    run.skill("first-what-left", (_FIRST_WHAT_LEFT_DIR / "launcher.md").read_text(), group="cpo")
    run.project("some-project")

    result = run("first-what-left", "some-project")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert argv[argv.index("--agent") + 1] == "cpo"
    assert _prompt_of(argv) == _FIRST_WHAT_LEFT_PROMPT
    assert "--model" not in argv


def test_the_shipped_first_what_left_declaration_takes_the_project_and_no_reporter_or_reads():
    declaration = (_FIRST_WHAT_LEFT_DIR / "launcher.md").read_text()

    assert _field(declaration, "Arguments") == "<project>"
    assert _field(declaration, "Reporter") is None
    assert _field(declaration, "Reads") is None


def test_the_first_what_left_directory_holds_exactly_the_planned_files():
    shipped = (p for p in _FIRST_WHAT_LEFT_DIR.rglob("*") if p.is_file())
    files = {p.relative_to(_FIRST_WHAT_LEFT_DIR).as_posix() for p in shipped}

    assert files == _FIRST_WHAT_LEFT_FILES
    assert not list(_FIRST_WHAT_LEFT_DIR.rglob("*.py"))
    assert not [p for p in _FIRST_WHAT_LEFT_DIR.rglob("*") if p.is_file() and os.access(p, os.X_OK)]
    assert not (_FIRST_WHAT_LEFT_DIR / "evals").exists()


def _first_what_left_frontmatter():
    text = (_FIRST_WHAT_LEFT_DIR / "SKILL.md").read_text()
    return text.split("---\n")[1]


def test_the_first_what_left_skill_md_frontmatter_is_well_formed():
    frontmatter = _first_what_left_frontmatter()

    assert re.search(r"^name: first-what-left$", frontmatter, re.M)
    description = re.search(r"^description: (.*)$", frontmatter, re.M).group(1)
    assert ": " not in description
    assert re.search(r'^  version: "\d+\.\d+\.\d+"$', frontmatter, re.M)


def test_the_first_what_left_skill_md_names_the_list_file_and_one_actor():
    skill_md = _FIRST_WHAT_LEFT_DIR / "SKILL.md"

    assert "docs/what_left.md" in skill_md.read_text()
    assert "--actor cpo" in skill_md.read_text()
    assert "--skill first-what-left" in skill_md.read_text()
    assert _named_actors(skill_md) == {"cpo"}


def test_the_first_what_left_checks_list_holds_the_six_anchors_in_order():
    text = (_FIRST_WHAT_LEFT_DIR / "SKILL.md").read_text()
    section = re.search(r"^## The checks, in order\n(.*?)(?=^## |\Z)", text, re.M | re.S).group(1)
    items = re.findall(r"^\d+\. (.*?)(?=^\d+\. |\Z)", section, re.M | re.S)

    opening = [re.match(r"`([^`]+)`", item.lstrip()).group(1) for item in items[:6]]

    assert len(items) >= len(_FIRST_WHAT_LEFT_ANCHORS)
    assert tuple(opening) == _FIRST_WHAT_LEFT_ANCHORS


def _refused_readme_status(run, expected, *arguments):
    _install_readme_status(run)
    run.project("some-project")

    result = run("readme-status", *arguments)

    assert result.returncode == 1
    assert expected in result.stderr, result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []
    assert run.watcher_argv() == []


def test_readme_status_without_a_project_is_refused_before_anything_spawns(run):
    _refused_readme_status(run, "needs <project>")


def test_readme_status_with_two_projects_is_refused_before_anything_spawns(run):
    _refused_readme_status(run, "unexpected argument", "some-project", "other-project")
