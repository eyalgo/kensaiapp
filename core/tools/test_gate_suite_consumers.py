"""Tests for what the four gate consumers adopt from `core/prompts/gate_suite.md`.

A consumer does not call the gate tool through a helper of its own: the recipe, and each skill that
adopts it, carries the executable block. These tests pull that block out of the file the skills
read, fill its placeholders, and hand the resulting arguments to the real `gate_suite.main` with the
fake host `test_gate_suite.py` builds — so what runs is the adopted call's own bytes, against the
real tool's own resolution, readiness and execution, and nothing starts a guest or a container.

Held by review, not here: a complete repository inventory and a correct reading of every CI
configuration. No test establishes a run's understanding of arbitrary syntax; these tests prove the
calls and the evidence they carry.
"""

from __future__ import annotations

import json
import re
import shlex
import types
from pathlib import Path

import pytest

import chain_development as cd
import gate_suite
import record_declarations
from test_gate_suite import (
    CARD_COMMAND,
    CHECK_INPUTS,
    CHECK_PATHS,
    CHECK_RECORD,
    CHECK_TRACKED,
    CI_NONE,
    CI_UNREADABLE,
    CheckHarness,
    DOES_NOT,
    forbidden_host,
    OWES,
    PROJECT,
    RESOLVES,
    WORKTREE,
    DASH,
    Harness,
    card_text,
    ci_readable,
    container_raw,
    guest_raw,
    mac_raw,
    raw_input,
    source,
    stage_record,
)

CORE_ROOT = Path(__file__).resolve().parent.parent
RECIPE = CORE_ROOT / "prompts" / "gate_suite.md"
INPUTS_FILE = "/private/tmp/gate-suite-inputs/inputs.json"
GATES = ("developer", "code-integrity", "seal")
_BLOCK = re.compile(r"```sh (?P<label>[a-z-]+)\n(?P<body>.*?)```", re.DOTALL)
_REDIRECTS = {">", "2>", ">>", "2>>"}


def invocation_blocks(path: Path) -> dict[str, str]:
    """Every labelled executable block of the file, by label."""
    return {found["label"]: found["body"] for found in _BLOCK.finditer(path.read_text())}


def adopted_argv(label: str, gate: str, path: Path = RECIPE) -> list[str]:
    """The arguments the labelled block passes to `gate_suite.py`, its placeholders filled and its
    output redirections dropped."""
    body = invocation_blocks(path)[label].replace("\\\n", " ")
    values = {"<instance change worktree>": WORKTREE, "<project>": PROJECT, "<key>": "key1",
              "<gate>": gate, "<inputs file>": INPUTS_FILE}
    for placeholder, value in values.items():
        body = body.replace(placeholder, value)
    tokens, kept, skip = shlex.split(body), [], False
    for token in tokens:
        if skip:
            skip = False
        elif token in _REDIRECTS:
            skip = True
        else:
            kept.append(token)
    script = next(position for position, token in enumerate(kept)
                  if token.endswith("/tools/gate_suite.py"))
    assert kept[script].startswith("<CORE>/")
    return kept[script + 1:]


def run_adopted(harness: Harness, label: str, gate: str, raw: dict | None = None,
                path: Path = RECIPE) -> int:
    if raw is not None:
        harness.files.files[Path(INPUTS_FILE)] = json.dumps(raw)
    return gate_suite.main(adopted_argv(label, gate, path), host=harness.host,
                           stdout=harness.out, stderr=harness.err)


_CHECK_BLOCK = re.compile(r"```sh\n(?P<body>[^`]*?gate_suite\.py\" check.*?)```", re.DOTALL)


def check_argv() -> list[str]:
    """The arguments the recipe's unlabelled check block passes to `gate_suite.py`, its placeholders
    filled with the check harness's files and its output redirections dropped."""
    found = _CHECK_BLOCK.search(RECIPE.read_text())
    assert found, "the recipe has no unlabelled check block"
    body = found["body"].replace("\\\n", " ")
    values = {"<instance change worktree>": WORKTREE, "<project>": PROJECT, "<key>": "key1",
              "<inputs file>": str(CHECK_INPUTS), "<paths file>": str(CHECK_PATHS),
              "<tracked-files list>": str(CHECK_TRACKED),
              "<decision-record file>": str(CHECK_RECORD)}
    for placeholder, value in values.items():
        body = body.replace(placeholder, value)
    kept, skip = [], False
    for token in shlex.split(body):
        if skip:
            skip = False
        elif token in _REDIRECTS:
            skip = True
        else:
            kept.append(token)
    script = next(at for at, token in enumerate(kept) if token.endswith("/tools/gate_suite.py"))
    assert kept[script].startswith("<CORE>/")
    return kept[script + 1:]


ENVIRONMENTS = {
    "guest": (guest_raw, "Environment: macos-guest — swift-guest"),
    "container": (container_raw, "Environment: container — python:3.12, arm64"),
    "mac": (mac_raw, "Environment: owners-mac — no CI"),
}


# --- the recipe's executable invocation -----------------------------------------------------------


@pytest.mark.parametrize("gate", GATES)
@pytest.mark.parametrize("environment", sorted(ENVIRONMENTS))
def test_shared_invocation_calls_real_gate_tool(gate, environment):
    make_raw, line = ENVIRONMENTS[environment]
    harness = Harness()

    status = run_adopted(harness, "invocation", gate, make_raw())

    assert status == 0
    assert harness.first_line == line
    [(argv, cwd)] = harness.processes.issued
    assert cwd == WORKTREE
    expected_head = {"guest": ["tart", "exec", "swift-guest"], "container": ["podman", "run"],
                     "mac": ["sh", "-c", CARD_COMMAND]}[environment]
    assert argv[:len(expected_head)] == expected_head
    assert "suite out" in harness.out.getvalue()


def test_the_invocation_carries_the_suites_own_exit_status():
    harness = Harness()
    harness.processes.suite = gate_suite.Completed(7, "boom\n", "bad\n")

    status = run_adopted(harness, "invocation", "developer", mac_raw())

    assert status == 7
    assert harness.first_line == "Environment: owners-mac — no CI"
    assert "boom" in harness.out.getvalue() and "bad" in harness.err.getvalue()


def test_every_block_names_the_gate_tool_through_the_core_placeholder():
    blocks = invocation_blocks(RECIPE)

    assert set(blocks) == {"invocation", "invocation-owners-ask", "invocation-no-inputs"}
    for label in blocks:
        assert adopted_argv(label, "seal")[0] == "run"


# --- the owner's ask is a separate input ----------------------------------------------------------


def test_shared_invocation_keeps_owner_authority_separate():
    # The sourced input and the product's own records cannot supply the ask.
    raw = container_raw()
    raw["owners_mac"] = raw["owners_ask"] = True
    raw["decisions"]["owners_mac"] = True
    harness = Harness()
    run_adopted(harness, "invocation", "developer", raw)
    assert harness.first_line == "Environment: container — python:3.12, arm64"

    # A recorded choice of the owner's Mac is the product's own decision, not an ask.
    named = raw_input(override={"environment": "owners-mac", "source": source()})
    recorded = Harness()
    assert run_adopted(recorded, "invocation", "developer", named) == 0
    assert recorded.first_line == "Environment: owners-mac — product's decision"
    assert recorded.processes.issued == [(["sh", "-c", CARD_COMMAND], WORKTREE)]

    # The owner's ask is the block that carries the explicit flag, and it needs no sourced input.
    asked = Harness()
    assert run_adopted(asked, "invocation-owners-ask", "developer") == 0
    assert asked.first_line == "Environment: owners-mac — owner's ask"
    assert asked.processes.probes == []
    assert asked.processes.issued == [(["sh", "-c", CARD_COMMAND], WORKTREE)]


def test_shared_check_invocation_calls_the_real_check():
    argv = check_argv()
    assert argv[0] == "check"
    assert "--owners-mac" not in argv and "--gate" not in argv
    assert argv[argv.index("--decision-record") + 1] == str(CHECK_RECORD)
    cases = (
        (raw_input(languages=("python",), guest=None), 0, RESOLVES),
        (raw_input(languages=("python", "shell"), guest=None), 1, OWES),
        (raw_input(ci=CI_UNREADABLE, guest=None), 1, DOES_NOT),
    )
    for raw, status, answer in cases:
        harness = CheckHarness()
        stage_record(harness, None)
        harness.stage(raw)

        got = gate_suite.main(argv, check_host=harness.host, host_factory=forbidden_host,
                              stdout=harness.out, stderr=harness.err)

        assert got == status
        assert harness.out.getvalue().startswith(f"{answer} {DASH} ")
        assert harness.err.getvalue() == ""


def test_the_recipe_names_only_the_two_sources_of_the_owners_ask():
    text = RECIPE.read_text()

    assert "KENSAIAPP_GATE_OWNERS_MAC" in text
    assert "exactly `1`" in text
    assert "--owners-mac" in adopted_argv("invocation-owners-ask", "seal")
    for label in ("invocation", "invocation-no-inputs"):
        assert "--owners-mac" not in adopted_argv(label, "seal")


# --- failure and no-suite results keep the tool's own words ---------------------------------------


def test_shared_invocation_preserves_failure_and_no_suite_results():
    refused = Harness()
    assert run_adopted(refused, "invocation", "developer", raw_input(ci=CI_UNREADABLE)) != 0
    assert refused.first_line.startswith("Environment: unresolved — the runner cannot be read")
    assert refused.processes.probes == [] and refused.processes.issued == []
    assert refused.err.getvalue().endswith(
        "The test command was not run, on the owner's Mac or anywhere else.\n")

    unreachable = Harness()
    unreachable.processes.when("tart", "list", result=gate_suite.ExecutableMissing("tart"))
    assert run_adopted(unreachable, "invocation", "code-integrity", guest_raw()) != 0
    assert unreachable.first_line == "Environment: macos-guest — swift-guest"
    assert unreachable.processes.issued == []

    for gate, kind, line in (("developer", "relative", "Environment: none — no suite"),
                             ("code-integrity", "relative", "Environment: none — no suite"),
                             ("seal", "external", "Environment: none — no suite ran")):
        none = Harness(card=card_text("none"), kind=kind)
        assert run_adopted(none, "invocation-no-inputs", gate) == 0
        assert none.first_line == line
        assert none.processes.probes == [] and none.processes.issued == []


# --- source-backed input of a form the tool has no name for ---------------------------------------


def test_shared_input_contract_accepts_source_backed_unfamiliar_ci():
    harness = Harness()
    pipeline = Path(WORKTREE) / "ops/pipeline.kdl"
    harness.files.files[pipeline] = 'stage "check" {\n  runner "macos-14"\n}\n'
    raw = guest_raw()
    raw["ci"] = {"finding": "readable", "runners": [{
        "platform": "macos", "source": source("ops/pipeline.kdl", 'runner "macos-14"')}]}

    assert run_adopted(harness, "invocation", "developer", raw) == 0
    assert harness.first_line == "Environment: macos-guest — swift-guest"

    # The same fact with an anchor the file does not hold never resolves the environment.
    forged = Harness()
    forged.files.files[pipeline] = 'stage "check" {}\n'
    assert run_adopted(forged, "invocation", "developer", raw) != 0
    assert forged.first_line.startswith("Environment: unresolved")
    assert forged.processes.issued == []


def test_an_omitted_ci_answer_is_never_no_ci():
    raw = guest_raw()
    del raw["ci"]
    harness = Harness()

    assert run_adopted(harness, "invocation", "developer", raw) != 0
    assert harness.first_line.startswith("Environment: unresolved — the runner cannot be read")

    explicit = Harness()
    assert run_adopted(explicit, "invocation", "developer", raw_input(ci=CI_NONE)) == 0
    assert explicit.first_line == "Environment: owners-mac — no CI"


# --- the recipe's own form ------------------------------------------------------------------------


def test_the_recipe_is_a_versioned_prompt_that_points_into_core_only_by_placeholder():
    text = RECIPE.read_text()

    assert re.match(r'---\nversion: "\d+\.\d+\.\d+"\n---\n', text)
    assert not re.findall(r"(?<![<>\w/.])core/", text)
    assert not re.findall(r"system/projects/[a-z]", text)
    assert "<CORE>/tools/gate_suite.py" in text
    assert "<CORE>/doctrine/engineering/languages/" in text


# ==================================================================================================
# The developer's closing run (development-implementation)
# ==================================================================================================

DEVELOPER_SKILL = (CORE_ROOT.parent / "skills" / "developer" / ".claude" / "skills"
                   / "development-implementation" / "SKILL.md")


def marker_template() -> list[str]:
    """The closing marker's body template, the fenced block that opens with its `Suite:` line."""
    text = DEVELOPER_SKILL.read_text()
    block = next(found for found in re.finditer(r"```\n(Suite: .*?)```", text, re.DOTALL))
    return block.group(1).splitlines()


def test_developer_adopted_invocation_runs_each_environment():
    assert set(invocation_blocks(DEVELOPER_SKILL)) == {"invocation", "invocation-no-inputs"}
    for environment, (make_raw, line) in ENVIRONMENTS.items():
        harness = Harness()

        status = run_adopted(harness, "invocation", "unused-gate-label", make_raw(),
                             path=DEVELOPER_SKILL)

        assert status == 0, environment
        # The block names its own gate: the label it was handed is not what ran.
        argv_run = adopted_argv("invocation", "unused-gate-label", DEVELOPER_SKILL)
        assert argv_run[argv_run.index("--gate") + 1] == "developer"
        assert harness.first_line == line
        [(argv, _cwd)] = harness.processes.issued
        assert argv[0] in {"tart", "podman", "sh"}
        # The marker's line is the printed first line, whole, directly under `Suite:`.
        template = marker_template()
        position = next(at for at, text in enumerate(template) if text.startswith("Suite: "))
        assert template[position + 1].startswith("Environment: ")
        assert harness.out.getvalue().split("\n")[0] == line


def test_developer_reclose_uses_fresh_result():
    text = DEVELOPER_SKILL.read_text()
    reclose = next(line for line in text.splitlines()
                   if line.startswith("- **Run the test command**"))

    assert "gate_suite.md" in reclose
    assert "`Environment:`" in reclose
    assert "nothing is copied from the superseded marker" in reclose
    assert "narrowed task gate" in text

    # Two closing runs, two results: the second is its own, whatever the first said.
    harness = Harness()
    harness.processes.suite = gate_suite.Completed(1, "first\n", "")
    assert run_adopted(harness, "invocation", "developer", mac_raw(), path=DEVELOPER_SKILL) == 1
    again = Harness()
    again.processes.suite = gate_suite.Completed(0, "second\n", "")
    assert run_adopted(again, "invocation", "developer", mac_raw(), path=DEVELOPER_SKILL) == 0
    assert "first" not in again.out.getvalue()


def test_developer_failure_cannot_publish_green():
    text = DEVELOPER_SKILL.read_text()
    refused = Harness()
    assert run_adopted(refused, "invocation", "developer", raw_input(ci=CI_UNREADABLE),
                       path=DEVELOPER_SKILL) != 0
    assert refused.first_line.startswith("Environment: unresolved — ")
    assert refused.processes.issued == []

    unreachable = Harness()
    unreachable.processes.when("tart", "list", result=gate_suite.ExecutableMissing("tart"))
    assert run_adopted(unreachable, "invocation", "developer", guest_raw(),
                       path=DEVELOPER_SKILL) != 0
    assert unreachable.processes.issued == []

    assert "The test command was not run. It reported: {reason}" in text
    assert "a refusal or an unreachable environment is `Suite: red`" in text


def test_developer_no_suite_marker_has_exact_line():
    text = DEVELOPER_SKILL.read_text()
    harness = Harness(card=card_text("none"))

    assert run_adopted(harness, "invocation-no-inputs", "developer", path=DEVELOPER_SKILL) == 0
    assert harness.first_line == "Environment: none — no suite"
    assert harness.processes.probes == [] and harness.processes.issued == []
    assert "Suite: none" in text and "Environment: none — no suite" in text
    assert any(line.startswith("Language resolution:") for line in marker_template())


def test_developer_task_invocations_keep_existing_contract():
    text = DEVELOPER_SKILL.read_text()
    step_three = text.index("### Step 3 — Close")
    bite_sized = text.index("## Bite-Sized Task Granularity")

    # The gate tool is named in the close and in the places that point at it, and nowhere in the
    # per-task red/green section.
    assert "gate_suite" not in text[text.index("### Step 2 — Developer batch"):step_three]
    assert "gate_suite.py" in text[step_three:bite_sized]
    assert "`test-driven-development`" in text[text.index("### Step 2"):step_three]


# ==================================================================================================
# The code-integrity run (development-code-integrity)
# ==================================================================================================

INTEGRITY_SKILL = (CORE_ROOT.parent / "skills" / "senior-engineer" / ".claude" / "skills"
                   / "development-code-integrity" / "SKILL.md")
EARLIER_RUN = re.compile(r"- An earlier run of the test command exited \{status\} and printed "
                         r"`\{line\}`\.")


def report_template() -> list[str]:
    """The report's opening lines as the skill lays them out: the fenced block with its verdict."""
    text = INTEGRITY_SKILL.read_text()
    block = next(found for found in re.finditer(r"```\n\s*(# [^\n]*\n.*?)```", text, re.DOTALL)
                 if "Integrity: <pass | stopped>" in found.group(1))
    return [line.strip() for line in block.group(1).splitlines()]


def test_integrity_adopted_invocation_runs_each_environment():
    assert set(invocation_blocks(INTEGRITY_SKILL)) == {"invocation", "invocation-no-inputs"}
    for environment, (make_raw, line) in ENVIRONMENTS.items():
        harness = Harness()

        status = run_adopted(harness, "invocation", "unused-gate-label", make_raw(),
                             path=INTEGRITY_SKILL)

        argv_run = adopted_argv("invocation", "unused-gate-label", INTEGRITY_SKILL)
        assert argv_run[argv_run.index("--gate") + 1] == "code-integrity"
        assert status == 0, environment
        assert harness.first_line == line
        [(argv, _cwd)] = harness.processes.issued
        assert CARD_COMMAND in " ".join(argv)

    template = [text for text in report_template() if text.strip()]
    verdict = next(at for at, text in enumerate(template) if text.startswith("Integrity: "))
    assert template[verdict + 1].startswith("Environment: ")


def test_integrity_final_run_supplies_leading_environment():
    shape = EARLIER_RUN.search(INTEGRITY_SKILL.read_text())
    assert shape, "the skill states no bullet for an earlier run"

    earlier = []
    for make_raw, status in ((guest_raw, 1), (container_raw, 1)):
        harness = Harness()
        harness.processes.suite = gate_suite.Completed(status, "red\n", "")
        assert run_adopted(harness, "invocation", "x", make_raw(), path=INTEGRITY_SKILL) == status
        earlier.append((status, harness.first_line))
    final = Harness()
    assert run_adopted(final, "invocation", "x", mac_raw(), path=INTEGRITY_SKILL) == 0

    bullets = [shape.group(0).replace("{status}", str(status)).replace("{line}", line)
               for status, line in earlier]
    report = "\n".join(["# Code integrity report", "", "Integrity: pass", final.first_line, "",
                        "## Tests run", "", *bullets, ""])

    declared = [line.text for line in
                record_declarations.parse(report).read(record_declarations.ENVIRONMENT)]
    assert declared == [final.first_line]
    assert cd.DiskReader._environment_kind(declared[0]) == "owners-mac"
    assert all(line in report for _status, line in earlier)


def test_integrity_failure_cannot_publish_pass():
    text = INTEGRITY_SKILL.read_text()
    refused = Harness()
    assert run_adopted(refused, "invocation", "x", raw_input(ci=CI_UNREADABLE),
                       path=INTEGRITY_SKILL) != 0
    assert refused.first_line.startswith("Environment: unresolved — ")
    assert refused.processes.issued == []

    unreachable = Harness()
    unreachable.processes.when("podman", "info", result=gate_suite.ExecutableMissing("podman"))
    assert run_adopted(unreachable, "invocation", "x", container_raw(),
                       path=INTEGRITY_SKILL) != 0
    assert unreachable.first_line == "Environment: container — python:3.12, arm64"
    assert unreachable.processes.issued == []

    assert "The test command was not run. It reported: {reason}" in text
    assert "a refusal or an unreachable environment is `Integrity: stopped`" in text
    assert "a failed suite is Step 3's red" in text


def test_integrity_no_suite_and_early_stop_are_honest():
    text = INTEGRITY_SKILL.read_text()
    harness = Harness(card=card_text("none"))

    assert run_adopted(harness, "invocation-no-inputs", "x", path=INTEGRITY_SKILL) == 0
    assert harness.first_line == "Environment: none — no suite"
    assert harness.processes.probes == [] and harness.processes.issued == []

    stopped = "Environment: none — the run stopped before the test command ran"
    assert stopped in text and "Environment: none — no suite" in text
    # A stopped run states why no suite ran; it never reuses another run's environment.
    assert cd.DiskReader._environment_kind(stopped) == "none"
    assert "never copies an environment" in text


def test_integrity_interactive_runner_discovery_is_preserved():
    text = INTEGRITY_SKILL.read_text()

    assert "infer the project's test runner from the codebase" in text
    assert "keeps its own discovery of the test runner" in text
    assert "the card's `Test command:` as a managed gate" in text
    assert "gate_suite.py" not in text[text.index("**Interactive mode:** infer"):
                                       text.index("**Language packets")]


# ==================================================================================================
# The security run (development-security)
# ==================================================================================================

SECURITY_SKILL = (CORE_ROOT.parent / "skills" / "senior-engineer" / ".claude" / "skills"
                  / "development-security" / "SKILL.md")


def test_security_adopted_invocation_runs_each_environment_under_the_code_integrity_gate():
    # The tool has no gate of the security step's own; the skill passes `code-integrity`, the step
    # it follows, and says so (`core/prompts/gate_suite.md`).
    assert set(invocation_blocks(SECURITY_SKILL)) == {"invocation"}
    for environment, (make_raw, line) in ENVIRONMENTS.items():
        harness = Harness()

        status = run_adopted(harness, "invocation", "unused-gate-label", make_raw(),
                             path=SECURITY_SKILL)

        argv_run = adopted_argv("invocation", "unused-gate-label", SECURITY_SKILL)
        assert argv_run[argv_run.index("--gate") + 1] == "code-integrity"
        assert status == 0, environment
        assert harness.first_line == line
        [(argv, _cwd)] = harness.processes.issued
        assert CARD_COMMAND in " ".join(argv)


def test_security_copies_environment_lines_as_bullets_and_a_failure_undoes_the_fix():
    text = SECURITY_SKILL.read_text()
    assert "into the report as a bullet, never as a bare line" in text
    assert "A red or refused run means the change it was proving" in text
    assert "`development-security`" in RECIPE.read_text()

    refused = Harness()
    assert run_adopted(refused, "invocation", "x", raw_input(ci=CI_UNREADABLE),
                       path=SECURITY_SKILL) != 0
    assert refused.processes.issued == []


# ==================================================================================================
# The seal's suite run (tobiishi-seal)
# ==================================================================================================

SEAL_SKILL = (CORE_ROOT.parent / "skills" / "pm" / ".claude" / "skills" / "tobiishi-seal"
              / "SKILL.md")
SEAL_DATE = "2026-10-14"


class ActionFiles:
    """The seal action's file port over a dict: the real action bytes run with nothing on disk."""

    def __init__(self, files: dict[Path, str]) -> None:
        self.files = files
        self.directories: list[Path] = []

    def read(self, path: Path) -> str:
        return self.files[path]

    def write(self, path: Path, content: str) -> None:
        self.files[path] = content

    def exists(self, path: Path) -> bool:
        return path in self.files

    def ensure_directory(self, path: Path) -> None:
        self.directories.append(path)


class ActionProcesses:
    """The seal action's process port: every call succeeds and is recorded."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def run(self, argv: list[str], *, cwd: Path):
        self.calls.append(argv)
        stdout = "0123abc\n" if "rev-parse" in argv else ""
        return types.SimpleNamespace(returncode=0, stdout=stdout, stderr="")


def unwrapped(text: str) -> str:
    """The prose with its line wrapping undone, so a sentence is matched whatever its wrap."""
    return " ".join(text.split())


def seal_action_module():
    """The `caller-seal-action` block of the seal skill, executed as the module it is."""
    text = SEAL_SKILL.read_text()
    found = re.search(r"<!-- caller-seal-action -->\n```python\n(.*?)\n```", text, re.DOTALL)
    assert found, "the seal skill has no caller-seal-action block"
    module = types.ModuleType("seal_action_under_test")
    exec(compile(found.group(1) + "\n", str(SEAL_SKILL), "exec"), module.__dict__)
    return module


def run_seal_action(bookkeeping: dict, deferred: list[str] = ()):
    """Run the real action over fake ports; return (the sealed request text, the process calls)."""
    module = seal_action_module()
    worktree = Path("/work/instance-worktree")
    root = Path("system/projects/demo/journey/tobiishi")
    destination = worktree / root / "trail" / "key1" / "change_request.md"
    configuration = Path("/stable/action-config.json")
    files = ActionFiles({
        destination: "# Request\n",
        configuration: json.dumps({
            "contract": {"instance_worktree": str(worktree), "project": "demo", "key": "key1"},
            "bookkeeping": {"date": SEAL_DATE, "deferred": list(deferred),
                            "directional": "Agari: demo — progress: seal", "surface": "Codex",
                            "co_authored_by": "model <noreply@example.invalid>",
                            "reasoning_effort": "high", **bookkeeping},
            "builder": "/stable/commit_builder.py", "evidence": "/stable/seal-evidence.json"}),
    })
    processes = ActionProcesses()
    action = module.SealAction(files=files, processes=processes)
    action.seal(configuration)
    return files.files[destination], processes.calls


def test_seal_adopted_invocation_runs_each_environment():
    assert set(invocation_blocks(SEAL_SKILL)) == {"invocation", "invocation-no-inputs"}
    for environment, (make_raw, line) in ENVIRONMENTS.items():
        harness = Harness()

        status = run_adopted(harness, "invocation", "unused-gate-label", make_raw(),
                             path=SEAL_SKILL)

        argv_run = adopted_argv("invocation", "unused-gate-label", SEAL_SKILL)
        assert argv_run[argv_run.index("--gate") + 1] == "seal"
        assert status == 0, environment
        assert harness.first_line == line
        [(argv, cwd)] = harness.processes.issued
        assert cwd == WORKTREE and CARD_COMMAND in " ".join(argv)

        # The line the tool printed is the one the seal's record carries, whole.
        sealed, _calls = run_seal_action({"environment_line": harness.first_line})
        assert sealed.splitlines()[2:4] == [
            f"**Sealed:** {SEAL_DATE} — accepted; merged to `main` via `--no-ff`.", line]


def test_sealed_record_places_environment_before_deferrals():
    deferred = ["Deferred: task 8 — blocked — decision.md",
                "Deferred: task 2 — depends on task 8 — decision.md"]
    line = "Environment: container — python:3.12, arm64"

    sealed, _calls = run_seal_action({"environment_line": line}, deferred)

    assert sealed == ("# Request\n\n"
                      f"**Sealed:** {SEAL_DATE} — sealed with deferrals; merged to `main` via "
                      f"`--no-ff`.\n{line}\n" + "".join(text + "\n" for text in deferred))
    # The developer's and the integrity run's lines are never copied into the seal's record.
    assert "code-integrity" not in sealed and sealed.count("Environment:") == 1


def test_seal_no_suite_forms_keep_exact_line():
    ran_none = "Environment: none — no suite ran"
    for gate_card in ("none", "N/A", "validated by use — the roles are prose",
                      "skill-evals"):
        harness = Harness(card=card_text(gate_card))

        assert run_adopted(harness, "invocation-no-inputs", "x", path=SEAL_SKILL) == 0
        assert harness.first_line == ran_none, gate_card
        assert harness.processes.probes == [] and harness.processes.issued == []

    # A product in its own repository runs no suite at the seal, whatever its card says.
    fixed = Harness(kind="external")
    assert run_adopted(fixed, "invocation-no-inputs", "x", path=SEAL_SKILL) == 0
    assert fixed.first_line == ran_none
    assert fixed.processes.probes == [] and fixed.processes.issued == []

    sealed, _calls = run_seal_action({"environment_line": ran_none})
    assert sealed.endswith(f"`--no-ff`.\n{ran_none}\n")


@pytest.mark.parametrize("bookkeeping", [{}, {"environment_line": ""},
                                         {"environment_line": "   "},
                                         {"environment_line": None}])
def test_missing_environment_bookkeeping_fails_before_move(bookkeeping):
    module = seal_action_module()
    worktree = Path("/work/instance-worktree")
    configuration = Path("/stable/action-config.json")
    files = ActionFiles({configuration: json.dumps({
        "contract": {"instance_worktree": str(worktree), "project": "demo", "key": "key1"},
        "bookkeeping": {"date": SEAL_DATE, "deferred": [], "directional": "d", **bookkeeping},
        "builder": "/stable/commit_builder.py", "evidence": "/stable/seal-evidence.json"})})
    processes = ActionProcesses()

    with pytest.raises(ValueError, match="environment_line"):
        module.SealAction(files=files, processes=processes).seal(configuration)

    # Nothing moved, nothing created, nothing written, no commit made.
    assert processes.calls == [] and files.directories == []
    assert list(files.files) == [configuration]


def test_seal_failure_preserves_existing_delivery_boundary():
    text = unwrapped(SEAL_SKILL.read_text())
    refused = Harness()
    assert run_adopted(refused, "invocation", "x", raw_input(ci=CI_UNREADABLE),
                       path=SEAL_SKILL) != 0
    assert refused.first_line.startswith("Environment: unresolved — ")
    assert refused.processes.issued == []
    assert refused.err.getvalue().endswith(gate_suite.CLOSING_LINE + "\n")

    unreachable = Harness()
    unreachable.processes.when("tart", "list", result=gate_suite.ExecutableMissing("tart"))
    assert run_adopted(unreachable, "invocation", "x", guest_raw(), path=SEAL_SKILL) != 0
    assert unreachable.processes.issued == []
    assert unreachable.err.getvalue().endswith(gate_suite.CLOSING_LINE + "\n")

    # A suite that was issued and failed does not end in that line: it keeps the old rule.
    failed = Harness()
    failed.processes.suite = gate_suite.Completed(3, "red\n", "bad\n")
    assert run_adopted(failed, "invocation", "x", mac_raw(), path=SEAL_SKILL) == 3
    assert not failed.err.getvalue().endswith(gate_suite.CLOSING_LINE + "\n")

    assert "ends with `The test command was not run, on the owner's Mac or anywhere else.`" in text
    assert "a refusal or an unreachable environment halts `deliver-precondition-failed`" in text
    assert "A failed suite keeps the rule above" in text


def test_seal_step_one_a_calls_the_tool_once_after_the_advance():
    text = unwrapped(SEAL_SKILL.read_text())
    step = text[text.index("### Step 1a"):text.index("### Step 1b")]

    assert step.index("**The advance.**") < step.index("gate_suite")
    assert step.count("```sh invocation ") == 1
    assert "`environment_line`" in step and "bookkeeping" in step
    assert "never reuse the developer's or the integrity run's line" in step
    # The fixed topology takes the tool's no-suite result and runs no advance.
    assert "invocation-no-inputs" in step and "Environment: none — no suite ran" in step


# --- the guest example the recipe publishes, run through the adopted call -------------------------

_GUEST_EXAMPLE = re.compile(r'```json\n(?P<body>\s*"guest": \{.*?)```', re.DOTALL)
_GUEST_NAME = "kensai-macos"
_PRODUCTS_ROOT = "/h/products"
_INSTANCE_REPOSITORY = "/h/kensai/host-instance"
_CLOSING = "The test command was not run, on the owner's Mac or anywhere else."


def published_guest() -> dict:
    """The `guest` member of the recipe's own macOS example, with its placeholders filled the way
    a caller reading the host's login job would fill them."""
    found = _GUEST_EXAMPLE.search(RECIPE.read_text())
    assert found, "the recipe publishes no macOS guest example"
    text = (found["body"].replace("<products root>", _PRODUCTS_ROOT)
            .replace("<instance repository>", _INSTANCE_REPOSITORY)
            .replace("<instance>", "host-instance"))
    return json.loads("{" + text + "}")["guest"]


def macos_input() -> dict:
    return guest_raw(published_guest())


def running_guest(harness: Harness) -> Harness:
    """The host's guest is up: `tart list` shows it running."""
    harness.processes.when("tart", "list", result=gate_suite.Completed(
        0, json.dumps([{"Name": _GUEST_NAME, "State": "running"}]), ""))
    return harness


@pytest.mark.parametrize("gate", GATES)
def test_published_guest_example_runs_two_worktrees_for_every_gate(gate):
    guest = published_guest()
    assert guest["name"] == _GUEST_NAME and len(guest["shares"]) == 2
    folders = (f"{_PRODUCTS_ROOT}/widget-app/.worktrees/k1",
               f"{_INSTANCE_REPOSITORY}/.worktrees/k2")
    guests = ("/Volumes/My Shared Files/products/widget-app/.worktrees/k1",
              "/Volumes/My Shared Files/host-instance/.worktrees/k2")
    for folder, in_guest in zip(folders, guests):
        harness = running_guest(Harness(run_folder=folder))

        status = run_adopted(harness, "invocation", gate, macos_input())

        assert status == 0
        assert harness.first_line == f"Environment: macos-guest {DASH} {_GUEST_NAME}"
        # The suite builds in a copy streamed from the host onto the guest's own disk, removed
        # after the suite.
        scratch = "/tmp/kensaiapp-gate-suite-tok123"
        assert harness.processes.probes[-3:] == [
            ["tart", "exec", _GUEST_NAME, "sh", "-c",
             f"test -f {shlex.quote(in_guest + '/.gate_suite_token_tok123')}"],
            ["tart", "exec", _GUEST_NAME, "sh", "-c", "command -v python3"],
            ["tart", "exec", _GUEST_NAME, "sh", "-c", f"rm -rf {scratch}"]]
        [(producer, consumer, _cwd)] = harness.processes.pipes
        assert producer[:3] == ["tar", "-C", folder] and consumer[:4] == [
            "tart", "exec", "-i", _GUEST_NAME]
        assert harness.processes.issued == [(
            ["tart", "exec", _GUEST_NAME, "sh", "-c",
             f"cd {scratch} && {CARD_COMMAND}"], folder)]


@pytest.mark.parametrize("gate", GATES)
def test_adopted_guest_call_refuses_an_unshared_run(gate):
    harness = Harness(run_folder="/Users/o/scratch/w")

    status = run_adopted(harness, "invocation", gate, macos_input())

    assert status == 1
    assert harness.first_line == f"Environment: macos-guest {DASH} {_GUEST_NAME}"
    lines = harness.err.getvalue().splitlines()
    assert lines[0] == ("gate_suite: this run's checkout, /Users/o/scratch/w, is under none of "
                        f"the shares this run was given for the macOS guest {_GUEST_NAME}.")
    assert lines[1] == f"The shares this run was given: {_PRODUCTS_ROOT}, {_INSTANCE_REPOSITORY}."
    assert lines[-1] == _CLOSING
    assert harness.processes.probes == [] and harness.processes.issued == []
    assert harness.lock.holds == 0


# --- a Linux matrix, through the adopted calls (CP-782 to CP-784) ---------------------------------

from test_gate_suite import (  # noqa: E402
    CELL_CONTAINERS, CELL_DECLARATIONS, CELL_REFS, CI_FILE, MATRIX_CI_TEXT, failed_line,
    matrix_harness, matrix_inputs, passed_line, stored_run)

ADOPTERS = (("recipe", RECIPE, "developer"), ("developer", DEVELOPER_SKILL, "developer"),
            ("integrity", INTEGRITY_SKILL, "code-integrity"),
            ("security", SECURITY_SKILL, "code-integrity"), ("seal", SEAL_SKILL, "seal"))


@pytest.mark.parametrize("name, path, gate", ADOPTERS, ids=[entry[0] for entry in ADOPTERS])
def test_adopted_gate_calls_run_every_linux_cell(name, path, gate):
    assert "invocation" in invocation_blocks(path)
    argv = adopted_argv("invocation", gate, path)
    assert argv[argv.index("--gate") + 1] == gate

    harness = matrix_harness()
    assert run_adopted(harness, "invocation", gate, matrix_inputs(), path=path) == 0

    # Every sourced cell ran, and the leading block of declarations is the complete one.
    assert harness.out.getvalue().splitlines()[:3] == CELL_DECLARATIONS
    assert [argv_[-4] for argv_, _ in harness.processes.issued] == list(CELL_REFS)
    for cell in CELL_CONTAINERS:
        assert passed_line(cell) in harness.out.getvalue()

    # A one-cell call keeps its single declaration and gains no matrix line.
    single = Harness()
    assert run_adopted(single, "invocation", gate, container_raw(), path=path) == 0
    assert single.first_line == "Environment: container — python:3.12, arm64"
    assert single.out.getvalue().count("Environment:") == 1
    assert "gate_suite: the run in" not in single.out.getvalue()


def test_the_seal_still_takes_only_the_first_line_of_the_leading_block():
    harness = matrix_harness()
    run_adopted(harness, "invocation", "seal", matrix_inputs(), path=SEAL_SKILL)

    sealed, _calls = run_seal_action({"environment_line": harness.first_line})

    assert harness.first_line == CELL_DECLARATIONS[0]
    assert sealed.count("Environment:") == 1 and CELL_DECLARATIONS[0] in sealed


def test_adopted_matrix_call_keeps_status_and_trusted_declarations(tmp_path):
    store = gate_suite.FileRunRecords(tmp_path / "runs")
    spoof = "Environment: container — python:9.9, arm64"
    harness = matrix_harness({
        CELL_REFS[0]: gate_suite.Completed(0, f"{spoof}\nout\n", f"{spoof}\n"),
        CELL_REFS[1]: gate_suite.Completed(4, "boom\n", ""),
        CELL_REFS[2]: gate_suite.Completed(0, "fine\n", "")}, store)

    status = run_adopted(harness, "invocation", "developer", matrix_inputs())

    assert status == 4
    found = stored_run(harness, store)
    # The prefix the gate bounds is the three stored declarations, whatever a suite printed.
    assert found.environment_lines == tuple(CELL_DECLARATIONS) and found.status == 4
    assert found.stdout.splitlines()[:3] == CELL_DECLARATIONS
    assert found.stdout.count(spoof) == 1 and failed_line(CELL_CONTAINERS[1], 4) in found.stdout


def test_adopted_matrix_check_resolves_without_running():
    argv = check_argv()
    harness = CheckHarness(product_files={CI_FILE: MATRIX_CI_TEXT})
    stage_record(harness, None)
    harness.stage({**matrix_inputs(), "guest": None})

    got = gate_suite.main(argv, check_host=harness.host, host_factory=forbidden_host,
                          stdout=harness.out, stderr=harness.err)

    assert got == 0 and harness.err.getvalue() == ""
    printed = harness.out.getvalue()
    assert printed.startswith(f"{RESOLVES} {DASH} ")
    assert [printed.index(f"python:{tag}") for tag in ("3.11", "3.12", "3.13")] == sorted(
        printed.index(f"python:{tag}") for tag in ("3.11", "3.12", "3.13"))
    assert "Environment:" not in printed


# --- a not-ready environment is read by the three skills that run the gate ----------------------


def test_developer_skill_states_the_not_ready_write_up():
    text = unwrapped(DEVELOPER_SKILL.read_text())

    assert "The environment was not ready. It reported: {reason}" in text
    assert "environment-not-ready" in text


def test_integrity_skill_reads_not_ready_as_stopped():
    text = unwrapped(INTEGRITY_SKILL.read_text())

    assert "An environment that was not ready, including one whose test command exited 127, " \
           "is `Integrity: stopped` too." in text
    assert "environment-not-ready" in text


def test_seal_halts_on_a_not_ready_line_read_by_the_prompt():
    text = unwrapped(SEAL_SKILL.read_text())
    rule = text[text.index("An environment that was not ready is no suite result either."):]
    rule = rule[:rule.index("**The environment line.**")]

    assert "`Environment: not-ready`" in rule
    assert "`deliver-precondition-failed`" in rule
    assert "§ *Reading the run's lines*" in rule
