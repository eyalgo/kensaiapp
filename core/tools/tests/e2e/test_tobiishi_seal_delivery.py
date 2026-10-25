"""Execute the adopted seal recipe; real Git/builder paths and injected external faults."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

from test_deliver_change import BUILDER, KEY, TOOL, VERSIONED, Scenario, git

ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / "skills/pm/.claude/skills/tobiishi-seal/SKILL.md"
IDENTITY = "gpt-6.1-sol <noreply@openai.com>"
ENVIRONMENT = "Environment: container — python:3.12, arm64"
CONTEXT = "# Context header\n\n## Current change — PM view\n\n**Status:** Open\n\nKeep this.\n"
CODES = ["deliver-precondition-failed", "merge-conflict", "merge-hook-failed",
         "instance-merge-after-product", "teardown-failed", "delivery-failed"]


def extract(source, name):
    match = re.search(r"<!-- " + name + r" -->\n```python\n(.*?)\n```", source, re.S)
    assert match, f"Missing executable {name} block in {SKILL}"
    return match.group(1) + "\n"


@pytest.fixture
def recipe():
    module = types.ModuleType("seal_caller_recipe")
    sys.modules[module.__name__] = module
    exec(compile(extract(SKILL.read_text(), "caller-delivery"), str(SKILL), "exec"),
         module.__dict__)
    yield module
    sys.modules.pop(module.__name__, None)


class Managed:
    def __init__(self, root, *, fixed=False, context=True, deferred=()):
        self.scenario = Scenario(root, fixed)
        self.root = root
        self.worktree = self.scenario.worktrees["instance"]
        primary = self.scenario.repos["instance"]
        primary_root = primary / "system/projects/example/journey/tobiishi"
        primary_root.mkdir(parents=True)
        (primary_root / "README.md").write_text("Managed journey\n")
        git(primary, "add", "system")
        git(primary, "commit", "-qm", "open managed journey")
        self.scenario.tips["instance"] = git(primary, "rev-parse", "main").stdout.strip()
        self.active = self.worktree / "system/projects/example/journey/tobiishi" / KEY
        self.active.mkdir(parents=True)
        self.payload = {"change_request.md": b"# Request\n", "change_spec.md": b"spec\x00bytes\n",
                        "flow_findings/review.md": b"joined finding\n"}
        for name, content in self.payload.items():
            path = self.active / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        self.context = self.worktree / "system/projects/example/contexts/CONTEXT_PM.md"
        if context:
            self.context.parent.mkdir(parents=True)
            self.context.write_text(CONTEXT)
        (self.worktree / "system/projects/example/agari.md").write_text("# Example terminus\n")
        git(self.worktree, "add", "system")
        git(self.worktree, "commit", "-qm", "managed carving")
        self.recorded_tip = git(self.worktree, "rev-parse", "HEAD").stdout.strip()
        self.core = root / "stable core ; $(literal)"
        (self.core / "tools").mkdir(parents=True)
        (self.core / "tools/deliver_change.py").write_text(
            "import runpy, sys\n"
            f"sys.path.insert(0, {str(TOOL.parent)!r})\n"
            f"runpy.run_path({str(TOOL)!r}, run_name='__main__')\n"
        )
        self.events = root / "caller-events.jsonl"
        self.builder = self.core / "tools/commit_builder.py"
        self.builder.write_text(
            "import json, subprocess, sys\nfrom pathlib import Path\n"
            f"root = Path({str(root)!r})\nlog = Path({str(self.events)!r})\n"
            f"product = Path({str(self.scenario.worktrees.get('product', self.worktree))!r})\n"
            "event = {'argv': sys.argv[1:], 'product_disk': product.exists()}\n"
            "product_repo = "
            f"{str(self.scenario.repos.get('product', self.scenario.repos['instance']))!r}\n"
            "for name, args in [('product_ref', ['show-ref', '--verify', '--quiet', "
            f"{'refs/heads/' + KEY!r}]), "
            "('product_registrations', ['worktree', 'list', '--porcelain'])]:\n"
            "    observation = subprocess.run(['git', '-C', product_repo, *args], "
            "capture_output=True, text=True)\n"
            "    event[name] = [observation.returncode, observation.stdout, observation.stderr]\n"
            "if 'commit' in sys.argv:\n"
            "    event['dependencies'] = {str(p): p.read_text() for p in "
            "root.glob('seal-caller-*/*') if p.is_file()}\n"
            f"result = subprocess.run([sys.executable, {str(BUILDER)!r}, *sys.argv[1:]], "
            "capture_output=True, text=True)\n"
            "event['exit'] = result.returncode\n"
            "with log.open('a') as stream: stream.write(json.dumps(event) + '\\n')\n"
            "print(result.stdout, end=''); print(result.stderr, end='', file=sys.stderr)\n"
            "sys.exit(result.returncode)\n"
        )
        self.config = {"core": str(self.core), "caller_source": str(SKILL),
                       "contract": self.scenario.contract, "merges": self.scenario.merges,
                       "bookkeeping": {"date": "2026-09-30", "deferred": list(deferred),
                                       "environment_line": ENVIRONMENT,
                                       "directional": "Agari: example — progress: seal",
                                       "surface": "Codex", "co_authored_by": IDENTITY,
                                       "reasoning_effort": "high"}}
        for record in self.config["merges"].values():
            record.update(surface="Codex", co_authored_by=IDENTITY, reasoning_effort="high")
        self.config_path = root / "configuration ; $(touch never).json"
        self.save()

    def save(self):
        self.config_path.write_text(json.dumps(self.config))

    def caller(self, recipe, processes=None, files=None):
        return recipe.Caller(files=files or recipe.Files(self.root),
                             processes=processes or recipe.Processes())

    def prepare(self, recipe, processes=None, files=None):
        self.save()
        return self.caller(recipe, processes, files).prepare(self.config_path)

    def invoke(self, recipe, processes=None, files=None):
        caller = self.caller(recipe, processes, files)
        self.save()
        prepared = caller.prepare(self.config_path)
        return caller.deliver(prepared), prepared

    def log(self):
        return [json.loads(line) for line in self.events.read_text().splitlines()]

    def effects(self):
        """The builder calls that could change a repository; none before delivery starts."""
        return [e for e in self.log() if not read_only(e)] if self.events.exists() else []

    def assert_landed(self, outcome, prepared):
        assert outcome["status"] == "ok", outcome
        assert outcome["audit_cleanup_eligible"] is True
        assert outcome["observations"]["exit"] == 0
        assert outcome["observations"]["stdout"] == (
            "delivery: complete\ndelivered: " + ",".join(self.scenario.repos) +
            "\ncleanup: complete\n"
        )
        seal = json.loads((prepared.directory / "seal-evidence.json").read_text())["seal_sha"]
        assert seal != self.recorded_tip
        assert git(self.scenario.repos["instance"], "merge-base", "--is-ancestor",
                   seal, "main").returncode == 0
        for role, repo in self.scenario.repos.items():
            tip = (
                seal if role == "instance"
                else prepared.before[role]["change_head"]["stdout"].strip()
            )
            assert git(repo, "show", "-s", "--format=%P", "main").stdout.split() == [
                self.scenario.tips[role], tip,
            ]
            self.scenario.assert_cleaned(role)
        events = [e for e in self.log() if not read_only(e)]
        assert sum("commit" in e["argv"] for e in events) == 1
        assert sum("merge" in e["argv"] for e in events) == len(self.scenario.repos)
        assert prepared.directory.is_dir()
        return seal


class RecordingProcesses:
    def __init__(self, real, *, terminal=None, fail_launch=False, unavailable=False):
        self.real = real
        self.terminal = terminal
        self.fail_launch = fail_launch
        self.unavailable = unavailable
        self.calls = []

    def run(self, argv, *, cwd):
        self.calls.append((list(argv), Path(cwd)))
        if "--contract" in argv:
            if self.fail_launch:
                raise OSError("launch unavailable")
            if self.terminal is not None:
                code, stdout, stderr = self.terminal
                return subprocess.CompletedProcess(argv, code, stdout, stderr)
        if self.unavailable and argv[0] == "git":
            return subprocess.CompletedProcess(argv, 128, "", "observation unavailable")
        return self.real.run(argv, cwd=cwd)


def read_only(event):
    """A builder call that changes nothing: a merge's check, or the directional's."""
    return "--check-only" in event["argv"] or "check-directional" in event["argv"]


def terminal(roles, code="delivery-failed"):
    return f"delivery: halt\nhalt: {code}\ndelivered: {roles}\ncleanup: incomplete\n"


def assert_halt(outcome, code, stdout, exit_code=1, stderr="diagnostic"):
    assert outcome["status"] == "halt"
    assert outcome["halt_reason"] == code
    assert outcome["audit_cleanup_eligible"] is False
    assert outcome["observations"] == {"exit": exit_code, "stdout": stdout, "stderr": stderr}
    report = Path(outcome["halt_report"])
    assert report.is_file()
    assert code in report.read_text()
    assert json.loads(report.read_text().split("```json\n", 1)[1].split("\n```", 1)[0])[
        "observations"] == outcome["observations"]


def test_relative_caller_seals_then_delivers_once(tmp_path, recipe):
    managed = Managed(tmp_path)
    script = tmp_path / "actual caller.py"
    script.write_text(extract(SKILL.read_text(), "caller-delivery"))
    result = subprocess.run([sys.executable, str(script), str(managed.config_path)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    outcome = json.loads(result.stdout)
    assert outcome["status"] == "ok", outcome
    assert len([e for e in managed.log() if "commit" in e["argv"]]) == 1
    assert len([e for e in managed.log() if "merge" in e["argv"]
                and "--check-only" not in e["argv"]]) == 1
    assert outcome["seal_evidence"]["available"] is True
    seal = outcome["seal_evidence"]["seal_sha"]
    assert seal != managed.recorded_tip
    assert git(
        managed.scenario.repos["instance"], "show", "-s", "--format=%P", "main"
    ).stdout.split() == [
        managed.scenario.tips["instance"], seal,
    ]
    assert git(managed.scenario.repos["instance"], "merge-base", "--is-ancestor", seal,
               "main").returncode == 0
    managed.scenario.assert_cleaned("instance")


def test_fixed_caller_delivers_product_before_seal_and_instance(tmp_path, recipe):
    managed = Managed(tmp_path, fixed=True)
    outcome, prepared = managed.invoke(recipe)
    managed.assert_landed(outcome, prepared)
    effects = [e for e in managed.log() if not read_only(e)]
    assert ["seal" if "commit" in e["argv"] else
            next(role for role, repo in managed.scenario.repos.items() if str(repo) == e["argv"][1])
            for e in effects] == ["product", "seal", "instance"]
    assert effects[1]["product_disk"] is False
    assert effects[1]["product_ref"][0] == 1
    assert effects[1]["product_registrations"][0] == 0
    assert (
        str(managed.scenario.worktrees["product"]) not in
        effects[1]["product_registrations"][1]
    )


def test_caller_invokes_the_public_delivery_cli_from_a_stable_directory(tmp_path, recipe):
    managed = Managed(tmp_path, fixed=True)
    port = RecordingProcesses(recipe.Processes())
    outcome, prepared = managed.invoke(recipe, port)
    managed.assert_landed(outcome, prepared)
    calls = [(argv, cwd) for argv, cwd in port.calls if "--contract" in argv]
    assert len(calls) == 1
    argv, cwd = calls[0]
    assert argv[:2] == [sys.executable, str(managed.core / "tools/deliver_change.py")]
    assert argv[2:] == ["--contract", str(prepared.directory / "contract.json"),
                       "--merges", str(prepared.directory / "merges.json"),
                       "--seal-action", str(prepared.directory / "seal.json"),
                       "--builder", str(managed.builder)]
    assert cwd == prepared.directory and cwd.is_absolute() and cwd.is_dir()
    for worktree in managed.scenario.worktrees.values():
        assert not cwd.is_relative_to(worktree)
    assert all(Path(argv[i]).is_file() for i in (3, 5, 7, 9))


@pytest.mark.parametrize("optional", [False, True])
def test_caller_preserves_the_complete_contract_and_role_records(tmp_path, recipe, optional):
    managed = Managed(tmp_path, fixed=True)
    product = managed.config["merges"]["product"]
    product.pop("actor")
    product["authorizer"] = "Product"
    if optional:
        product.update(branch_commits=["second", "first"],
                       claude_session="https://example.invalid/session")
        managed.config["merges"]["instance"].update(
            branch_commits=[], bump=[f"{VERSIONED['instance']}=patch"])
    else:
        for record in managed.config["merges"].values():
            for field in ("co_authored_by", "reasoning_effort"):
                record.pop(field)
    prepared = managed.prepare(recipe)
    assert (
        json.loads((prepared.directory / "contract.json").read_text()) ==
        managed.config["contract"]
    )
    assert json.loads((prepared.directory / "merges.json").read_text()) == managed.config["merges"]
    assert not managed.effects()
    for field in ("kind", "code_repo", "pipeline_repo", "code_worktree", "pipeline_worktree",
                  "delivery_repos"):
        assert field in json.loads((prepared.directory / "contract.json").read_text())


@pytest.mark.parametrize(
    "fault", ["alias", "unknown", "roles", "required", "both-identities", "type"]
)
def test_invalid_public_inputs_reach_unchanged_tool_refusal(tmp_path, recipe, fault):
    managed = Managed(tmp_path)
    if fault == "alias":
        managed.config["contract"]["code_worktree"] += "/child"
    elif fault == "unknown":
        managed.config["contract"]["unknown"] = "preserved"
    elif fault == "roles":
        managed.config["merges"]["product"] = dict(managed.config["merges"]["instance"])
    elif fault == "required":
        managed.config["merges"]["instance"].pop("description")
    elif fault == "both-identities":
        managed.config["merges"]["instance"]["authorizer"] = "Product"
    else:
        managed.config["merges"]["instance"]["branch_commits"] = "wrong type"
    outcome, prepared = managed.invoke(recipe)
    assert outcome["halt_reason"] == "deliver-precondition-failed", outcome
    assert (
        json.loads((prepared.directory / "contract.json").read_text()) ==
        managed.config["contract"]
    )
    assert json.loads((prepared.directory / "merges.json").read_text()) == managed.config["merges"]
    assert managed.worktree.is_dir() and managed.active.is_dir()


def test_caller_dependencies_survive_product_and_instance_cleanup(tmp_path, recipe):
    managed = Managed(tmp_path, fixed=True)
    outcome, prepared = managed.invoke(recipe)
    managed.assert_landed(outcome, prepared)
    action_event = next(e for e in managed.log() if "commit" in e["argv"])
    assert action_event["product_disk"] is False
    assert action_event["product_ref"][0] == 1
    assert action_event["product_registrations"][0] == 0
    assert (
        str(managed.scenario.worktrees["product"]) not in
        action_event["product_registrations"][1]
    )
    for name in ("contract.json", "merges.json", "seal.json", "action.py", "action-config.json"):
        path = prepared.directory / name
        assert str(path) in action_event["dependencies"]
        assert path.read_text() == action_event["dependencies"][str(path)]
    assert managed.builder.is_file() and (managed.core / "tools/deliver_change.py").is_file()
    assert json.loads((prepared.directory / "result.json").read_text()) == outcome


def test_caller_materializes_the_action_from_the_adopted_source(tmp_path, recipe):
    managed = Managed(tmp_path)
    adopted = tmp_path / "adopted source.md"
    older = tmp_path / "older source.md"
    original = SKILL.read_text()
    adopted.write_text(original.replace(
        '"seal_sha": seal_sha', '"seal_sha": seal_sha, "adopted": True'
    ))
    older.write_text(original.replace(
        '"seal_sha": seal_sha', '"seal_sha": seal_sha, "older": True'
    ))
    managed.config["caller_source"] = str(adopted)
    caller = managed.caller(recipe)
    prepared = managed.prepare(recipe)
    assert (prepared.directory / "action.py").read_text() == extract(
        adopted.read_text(), "caller-seal-action"
    )
    assert not managed.effects()
    adopted.unlink()
    outcome = caller.deliver(prepared)
    managed.assert_landed(outcome, prepared)
    evidence = json.loads((prepared.directory / "seal-evidence.json").read_text())
    assert evidence["adopted"] is True and "older" not in evidence


def test_caller_treats_configuration_and_paths_as_literal_values(tmp_path, recipe):
    managed = Managed(tmp_path)
    literal = "literal ; $(touch never) `literal` $value"
    managed.config["merges"]["instance"]["description"] = literal
    managed.config["bookkeeping"]["date"] = literal
    outcome, prepared = managed.invoke(recipe)
    seal = managed.assert_landed(outcome, prepared)
    argv = json.loads((prepared.directory / "seal.json").read_text())["argv"]
    assert argv == [sys.executable, str(prepared.directory / "action.py"),
                    str(prepared.directory / "action-config.json")]
    assert Path(argv[0]).is_absolute() and Path(argv[0]).exists()
    assert not (tmp_path / "never").exists()
    request = f"system/projects/example/journey/tobiishi/trail/{KEY}/change_request.md"
    assert literal in git(managed.scenario.repos["instance"], "show", f"{seal}:{request}").stdout


@pytest.mark.parametrize("deferred", [[], ["Deferred: task 8 — blocked — decision.md",
                                          "Deferred: task 2 — depends on task 8 — decision.md"]])
def test_seal_action_moves_all_carving_bytes_and_records_the_result(tmp_path, recipe, deferred):
    managed = Managed(tmp_path, deferred=deferred)
    prepared = managed.prepare(recipe)
    argv = json.loads((prepared.directory / "seal.json").read_text())["argv"]
    result = subprocess.run(argv, cwd=managed.worktree, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    trail = managed.active.parent / "trail" / KEY
    assert not managed.active.exists() and trail.is_dir()
    for name, content in managed.payload.items():
        if name != "change_request.md":
            assert (trail / name).read_bytes() == content
    expected = "sealed with deferrals" if deferred else "accepted"
    assert (trail / "change_request.md").read_text() == (
        "# Request\n\n**Sealed:** 2026-09-30 — " + expected +
        "; merged to `main` via `--no-ff`.\n" + ENVIRONMENT + "\n" +
        "".join(line + "\n" for line in deferred)
    )
    seal = json.loads((prepared.directory / "seal-evidence.json").read_text())["seal_sha"]
    assert (
        git(managed.worktree, "show", "-s", "--format=%P", seal).stdout.strip() ==
        managed.recorded_tip
    )
    assert git(managed.worktree, "status", "--porcelain").stdout == ""
    assert not any("merge" in event["argv"] for event in managed.log())


@pytest.mark.parametrize("missing", ["absent", "", "   ", None])
def test_seal_action_refuses_a_missing_environment_line_before_moving_anything(
    tmp_path, recipe, missing
):
    managed = Managed(tmp_path)
    if missing == "absent":
        del managed.config["bookkeeping"]["environment_line"]
    else:
        managed.config["bookkeeping"]["environment_line"] = missing
    prepared = managed.prepare(recipe)
    argv = json.loads((prepared.directory / "seal.json").read_text())["argv"]
    result = subprocess.run(argv, cwd=managed.worktree, capture_output=True, text=True)
    assert result.returncode == 1 and "environment_line" in result.stderr
    assert managed.active.is_dir() and not (managed.active.parent / "trail").exists()
    for name, content in managed.payload.items():
        assert (managed.active / name).read_bytes() == content
    assert git(managed.worktree, "status", "--porcelain").stdout == ""
    assert git(managed.worktree, "rev-parse", "HEAD").stdout.strip() == managed.recorded_tip
    assert not (prepared.directory / "seal-evidence.json").exists()


def test_the_environment_line_survives_product_cleanup_into_the_instance_seal(tmp_path, recipe):
    managed = Managed(tmp_path, fixed=True)
    managed.config["bookkeeping"]["environment_line"] = "Environment: none — no suite ran"
    outcome, prepared = managed.invoke(recipe)
    seal = managed.assert_landed(outcome, prepared)
    assert not managed.scenario.worktrees["product"].exists()
    retained = json.loads((prepared.directory / "action-config.json").read_text())
    assert retained["bookkeeping"]["environment_line"] == "Environment: none — no suite ran"
    request = f"system/projects/example/journey/tobiishi/trail/{KEY}/change_request.md"
    sealed = git(managed.scenario.repos["instance"], "show", f"{seal}:{request}").stdout
    assert "merged to `main` via `--no-ff`.\nEnvironment: none — no suite ran\n" in sealed
    assert git(managed.scenario.repos["instance"], "show", f"main:{request}").stdout == sealed


@pytest.mark.parametrize("context", [False, True])
def test_seal_action_updates_only_the_existing_pm_context_item(tmp_path, recipe, context):
    managed = Managed(tmp_path, context=context)
    prepared = managed.prepare(recipe)
    result = subprocess.run(json.loads((prepared.directory / "seal.json").read_text())["argv"],
                            cwd=managed.worktree, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    if context:
        assert (
            managed.context.read_text() ==
            CONTEXT.replace("**Status:** Open", "**Status:** Sealed")
        )
    else:
        assert not managed.context.exists()
        assert not any(
            value.endswith("CONTEXT_PM.md")
            for value in next(e for e in managed.log() if "commit" in e["argv"])["argv"]
        )


@pytest.mark.parametrize("session", [None, "https://example.invalid/session"])
def test_seal_and_delivery_preserve_runtime_attribution(tmp_path, recipe, session):
    managed = Managed(tmp_path, fixed=True)
    product = managed.config["merges"]["product"]
    product.update(co_authored_by="distinct-model <noreply@openai.com>", reasoning_effort="low",
                   branch_commits=["product second", "product first"])
    managed.config["merges"]["instance"].update(
        branch_commits=["instance entry"], bump=[f"{VERSIONED['instance']}=patch"])
    if session:
        managed.config["bookkeeping"]["claude_session"] = session
        for record in managed.config["merges"].values():
            record["claude_session"] = session
    outcome, prepared = managed.invoke(recipe)
    seal = managed.assert_landed(outcome, prepared)
    instance = managed.scenario.repos["instance"]
    for ref in (seal, "main"):
        body = git(instance, "show", "-s", "--format=%B", ref).stdout
        assert "Surface: Codex" in body and f"Co-Authored-By: {IDENTITY}" in body
        assert "Reasoning-Effort: high" in body
        assert (
            (f"Claude-Session: {session}" in body) if session else ("Claude-Session:" not in
            body)
        )
    body = git(managed.scenario.repos["product"], "show", "-s", "--format=%B", "main").stdout
    assert "Co-Authored-By: distinct-model <noreply@openai.com>" in body
    assert "Reasoning-Effort: low" in body
    assert body.index("product second") < body.index("product first")
    # The instance's marker moves at the landing merge; the product's release number does not.
    assert git(instance, "show", f"main:{VERSIONED['instance']}").stdout == '__version__ = "1.0.1"\n'
    assert (
        git(managed.scenario.repos["product"], "show", "main:version.py").stdout ==
        '__version__ = "1.0.0"\n'
    )
    assert json.loads((prepared.directory / "merges.json").read_text()) == managed.config["merges"]
    assert seal not in (prepared.directory / "merges.json").read_text()


@pytest.mark.parametrize("fixed", [False, True])
def test_caller_requires_exact_success_and_exit_zero(tmp_path, recipe, fixed):
    managed = Managed(tmp_path, fixed=fixed)
    stdout = ("delivery: complete\ndelivered: " + ",".join(managed.scenario.repos) +
              "\ncleanup: complete\n")
    port = RecordingProcesses(recipe.Processes(), terminal=(0, stdout, "retained diagnostics"))
    outcome, _ = managed.invoke(recipe, port)
    assert outcome["status"] == "ok" and outcome["audit_cleanup_eligible"] is True
    assert (
        outcome["observations"] ==
        {"exit": 0, "stdout": stdout, "stderr": "retained diagnostics"}
    )


@pytest.mark.parametrize("fixed,delivered", [(False, "instance"), (True, "product,instance")])
def test_caller_proves_the_three_line_complete_block_with_every_role(
    tmp_path, recipe, fixed, delivered
):
    managed = Managed(tmp_path, fixed=fixed)
    stdout = f"delivery: complete\ndelivered: {delivered}\ncleanup: complete\n"
    port = RecordingProcesses(recipe.Processes(), terminal=(0, stdout, "diagnostic"))
    outcome, _ = managed.invoke(recipe, port)
    assert outcome["status"] == "ok", outcome
    assert outcome["delivered"] == delivered and outcome["cleanup"] == "complete"
    assert outcome["landing_proved"] is True
    assert not (managed.active / "halt_report.md").exists()


EMPTY_PRODUCT = "delivery: complete\ndelivered: instance\nempty: product\ncleanup: complete\n"


def test_fixed_caller_accepts_an_instance_only_delivery_with_an_empty_product(tmp_path, recipe):
    managed = Managed(tmp_path, fixed=True)
    port = RecordingProcesses(recipe.Processes(), terminal=(0, EMPTY_PRODUCT, "diagnostic"))
    outcome, prepared = managed.invoke(recipe, port)
    assert outcome["status"] == "ok", outcome
    assert outcome["delivered"] == "instance" and outcome["cleanup"] == "complete"
    assert outcome["landing_proved"] is True
    assert outcome["audit_cleanup_eligible"] is True
    assert "halt_reason" not in outcome or outcome["halt_reason"] is None
    assert outcome["observations"] == {"exit": 0, "stdout": EMPTY_PRODUCT, "stderr": "diagnostic"}
    assert json.loads((prepared.directory / "result.json").read_text()) == outcome
    assert not (managed.active / "halt_report.md").exists()


@pytest.mark.parametrize("stdout,exit_code", [
    (EMPTY_PRODUCT, 1),
    (EMPTY_PRODUCT, 2),
    ("delivery: complete\nempty: product\ndelivered: instance\ncleanup: complete\n", 0),
    (EMPTY_PRODUCT + "extra: yes\n", 0),
    (EMPTY_PRODUCT.replace("empty: product", "empty: instance"), 0),
    (EMPTY_PRODUCT.replace("delivered: instance", "delivered: product,instance"), 0),
    (EMPTY_PRODUCT.rstrip("\n"), 0),
    (terminal("instance").replace("cleanup: incomplete", "empty: product\ncleanup: incomplete"), 1),
    (EMPTY_PRODUCT.replace("delivery: complete\n", ""), 0),
    (EMPTY_PRODUCT.replace("delivered: instance\n", ""), 0),
    (EMPTY_PRODUCT.replace("cleanup: complete\n", ""), 0),
    (EMPTY_PRODUCT.replace("empty: product\n", "empty: product\nempty: product\n"), 0),
    (EMPTY_PRODUCT.replace("cleanup: complete", "cleanup: incomplete"), 0),
    (EMPTY_PRODUCT.replace("delivered: instance", "delivered: product"), 0),
    (EMPTY_PRODUCT.replace("\n", "\r\n"), 0),
    (terminal("none").replace("cleanup: incomplete", "empty: product\ncleanup: incomplete"), 1),
])
def test_fixed_caller_rejects_a_malformed_empty_product_block(tmp_path, recipe, stdout, exit_code):
    managed = Managed(tmp_path, fixed=True)
    port = RecordingProcesses(recipe.Processes(), terminal=(exit_code, stdout, "diagnostic"))
    outcome, _ = managed.invoke(recipe, port)
    assert_halt(outcome, "delivery-failed", stdout, exit_code)
    assert outcome["landing_proved"] is False


@pytest.mark.parametrize("fixed,roles", [(False, "none"), (False, "instance"), (True, "none"),
                                       (True, "product"), (True, "product,instance")])
@pytest.mark.parametrize("code", CODES)
def test_caller_preserves_each_valid_delivery_halt(tmp_path, recipe, fixed, roles, code):
    managed = Managed(tmp_path, fixed=fixed)
    stdout = terminal(roles, code)
    port = RecordingProcesses(recipe.Processes(), terminal=(1, stdout, "diagnostic"))
    outcome, _ = managed.invoke(recipe, port)
    assert_halt(outcome, code, stdout)
    assert outcome["delivered"] == roles and outcome["cleanup"] == "incomplete"
    assert outcome["landing_proved"] is True


@pytest.mark.parametrize("stdout,exit_code", [
    ("", 0), ("delivery: complete\n", 0),
    ("delivery: complete\ndelivered: instance\ncleanup: complete\nextra: yes\n", 0),
    ("delivery: complete\ndelivered: instance\ncleanup: complete\ncleanup: complete\n", 0),
    ("delivery: complete\ndelivered: instance\ncleanup: complete\n", 1),
    ("delivery: complete\ndelivered: product,instance\ncleanup: complete\n", 0),
    ("delivery: complete\ndelivered: instance,product\ncleanup: complete\n", 0),
    ("delivery: complete\ndelivered: none\ncleanup: complete\n", 0),
    (terminal("none", "unknown-code"), 1), (terminal("product"), 1),
    ("delivery: complete\ndelivered: instance\nempty: product\ncleanup: complete\n", 0),
    (terminal("none"), 0), (terminal("none"), 2),
    (terminal("none").replace("cleanup: incomplete", "cleanup: complete"), 1),
    (terminal("none").replace("halt: delivery-failed", "reason: delivery-failed"), 1),
])
def test_caller_rejects_unproved_terminal_results(tmp_path, recipe, stdout, exit_code):
    managed = Managed(tmp_path)
    port = RecordingProcesses(recipe.Processes(), terminal=(exit_code, stdout, "diagnostic"))
    outcome, _ = managed.invoke(recipe, port)
    assert_halt(outcome, "delivery-failed", stdout, exit_code)
    assert outcome["landing_proved"] is False


def test_launch_failure_has_no_invented_exit(tmp_path, recipe):
    managed = Managed(tmp_path)
    port = RecordingProcesses(recipe.Processes(), fail_launch=True)
    outcome, _ = managed.invoke(recipe, port)
    assert_halt(outcome, "delivery-failed", "", None, "launch unavailable")
    assert outcome["landing_proved"] is False


@pytest.mark.parametrize("moved", [False, True])
def test_halt_report_uses_the_existing_active_or_trail_folder(tmp_path, recipe, moved):
    managed = Managed(tmp_path)
    caller = managed.caller(recipe)
    prepared = managed.prepare(recipe)
    if moved:
        result = subprocess.run(
            json.loads((prepared.directory / "seal.json").read_text())["argv"],
            cwd=managed.worktree, capture_output=True, text=True,
        )
        assert result.returncode == 0
    port = RecordingProcesses(recipe.Processes(), terminal=(1, terminal("none"), "diagnostic"))
    outcome = managed.caller(recipe, port).deliver(prepared)
    folder = managed.active.parent / "trail" / KEY if moved else managed.active
    assert Path(outcome["halt_report"]) == folder / "halt_report.md"


@pytest.mark.parametrize("primary_active", [False, True])
@pytest.mark.parametrize("unavailable", [False, True])
def test_halt_report_survives_instance_worktree_removal(
    tmp_path, recipe, primary_active, unavailable
):
    managed = Managed(tmp_path)
    prepared = managed.prepare(recipe)
    repo = managed.scenario.repos["instance"]
    root = repo / "system/projects/example/journey/tobiishi"
    root.mkdir(parents=True, exist_ok=True)
    if primary_active:
        (root / KEY).mkdir()
    git(repo, "worktree", "remove", str(managed.worktree))
    port = RecordingProcesses(
        recipe.Processes(),
        terminal=(1, terminal("instance", "teardown-failed"), "diagnostic"),
        unavailable=unavailable,
    )
    outcome = managed.caller(recipe, port).deliver(prepared)
    assert (
        Path(outcome["halt_report"]) ==
        (root / KEY if primary_active else root) / "halt_report.md"
    )
    assert not managed.worktree.exists()
    assert (root / KEY).exists() is primary_active
    assert git(repo, "show-ref", "--verify", "refs/heads/" + KEY).returncode == 0
    if unavailable:
        assert "observation unavailable" in Path(outcome["halt_report"]).read_text()
        assert '"available": false' in Path(outcome["halt_report"]).read_text()


@pytest.mark.parametrize("failure", ["seal", "conflict", "hook", "cleanup"])
def test_partial_delivery_report_retains_observed_recovery_state(tmp_path, recipe, failure):
    managed = Managed(tmp_path, fixed=True)
    s = managed.scenario
    if failure == "seal":
        git(managed.worktree, "rm", "-r", str(managed.active.relative_to(managed.worktree)))
        git(managed.worktree, "commit", "-qm", "missing seal input")
    elif failure == "conflict":
        (s.repos["instance"] / "shared").write_text("competing instance main\n")
        git(s.repos["instance"], "add", "shared")
        git(s.repos["instance"], "commit", "-qm", "competing main")
    elif failure == "hook":
        hooks = tmp_path / "instance-hooks"
        hooks.mkdir(exist_ok=True)
        hook = hooks / "pre-merge-commit"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
    else:
        (s.worktrees["product"] / ".gitignore").write_text("leftover\n")
        git(s.worktrees["product"], "add", ".gitignore")
        git(s.worktrees["product"], "commit", "-qm", "ignored recovery content")
        (s.worktrees["product"] / "leftover").write_text("retain me")
        # Ignored content alone is removed with the worktree; a lock is what refuses removal.
        git(s.repos["product"], "worktree", "lock", str(s.worktrees["product"]))
    expected_main = {role: git(repo, "rev-parse", "main").stdout.strip()
                     for role, repo in s.repos.items()}
    expected_change = {role: git(worktree, "rev-parse", "HEAD").stdout.strip()
                       for role, worktree in s.worktrees.items()}
    outcome, prepared = managed.invoke(recipe)
    assert outcome["status"] == "halt", outcome
    for role in s.repos:
        assert (outcome["recorded_before"][role]["main_head"]["stdout"].strip() ==
                expected_main[role])
        assert (outcome["recorded_before"][role]["change_head"]["stdout"].strip() ==
                expected_change[role])
    assert outcome["halt_reason"] == ("teardown-failed" if failure == "cleanup" else
                                      "instance-merge-after-product")
    assert outcome["delivered"] == "product"
    recovery = outcome["recovery"]
    product = recovery["product"]
    merge = git(s.repos["product"], "rev-parse", "main").stdout.strip()
    assert product["main_head"]["stdout"].strip() == merge
    assert product["intended_landing"] is True
    assert product["main_parents"]["stdout"].split() == [
        prepared.before["product"]["main_head"]["stdout"].strip(),
        prepared.before["product"]["change_head"]["stdout"].strip(),
    ]
    assert recovery["instance"]["disk"]["present"] is True
    assert recovery["instance"]["change_ref"]["exit"] == 0
    assert str(managed.worktree) in recovery["instance"]["registrations"]["stdout"]
    assert "recorded_before" in outcome
    if failure == "conflict":
        assert recovery["instance"]["primary_merge_head"]["exit"] == 0
        assert recovery["instance"]["primary_unmerged"]["stdout"]
    if failure == "hook":
        assert recovery["instance"]["primary_merge_head"]["exit"] == 0
        assert recovery["instance"]["primary_unmerged"]["stdout"] == ""
    if failure == "cleanup":
        assert s.worktrees["product"].is_dir()
    else:
        s.assert_cleaned("product")


def test_landed_merge_is_reported_despite_a_later_process_failure(tmp_path, recipe):
    managed = Managed(tmp_path, fixed=True)
    text = managed.builder.read_text()
    text = text.replace("sys.exit(result.returncode)",
                        "sys.exit(7 if 'merge' in sys.argv and '--check-only' not in sys.argv "
                        "and 'product' in sys.argv[2] else result.returncode)")
    managed.builder.write_text(text)
    outcome, _ = managed.invoke(recipe)
    assert outcome["status"] == "halt" and outcome["delivered"] == "product"
    assert outcome["cleanup"] == "incomplete"
    assert outcome["halt_reason"] == "instance-merge-after-product"
    assert outcome["recovery"]["product"]["intended_landing"] is True
    assert managed.scenario.worktrees["product"].is_dir()


def test_delivery_halt_causes_no_recovery_or_audit_cleanup(tmp_path, recipe):
    managed = Managed(tmp_path, fixed=True)
    s = managed.scenario
    audit = tmp_path / "audit recovery"
    git(s.repos["instance"], "worktree", "add", "-qb", KEY + "__audit-proof", str(audit))
    (s.repos["instance"] / "shared").write_text("conflict\n")
    git(s.repos["instance"], "add", "shared")
    git(s.repos["instance"], "commit", "-qm", "main conflict")
    port = RecordingProcesses(recipe.Processes())
    outcome, _ = managed.invoke(recipe, port)
    assert outcome["halt_reason"] == "instance-merge-after-product"
    assert outcome["audit_cleanup_eligible"] is False
    assert git(s.repos["instance"], "rev-parse", "--verify", "MERGE_HEAD").returncode == 0
    assert git(s.repos["instance"], "ls-files", "-u").stdout
    assert audit.is_dir() and managed.worktree.is_dir()
    assert git(s.repos["instance"], "show-ref", "--verify", "refs/heads/" + KEY).returncode == 0
    assert sum("--contract" in argv for argv, _ in port.calls) == 1
    assert not any("--abort" in argv or "reset" in argv or "worktree" in argv and "remove" in argv
                   for argv, _ in port.calls)
    assert sum("commit" in e["argv"] for e in managed.log()) == 1
    assert sum("merge" in e["argv"] and "--check-only" not in e["argv"]
               for e in managed.log()) == 2


def test_context_status_outside_current_item_is_preserved(tmp_path, recipe):
    managed = Managed(tmp_path)
    content = "# Header\n**Status:** Open\n\n" + CONTEXT + "\n## Other item\n**Status:** Open\n"
    managed.context.write_text(content)
    git(managed.worktree, "add", str(managed.context.relative_to(managed.worktree)))
    git(managed.worktree, "commit", "-qm", "context with sibling status")
    prepared = managed.prepare(recipe)
    result = subprocess.run(json.loads((prepared.directory / "seal.json").read_text())["argv"],
                            cwd=managed.worktree, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert managed.context.read_text() == content.replace(CONTEXT, CONTEXT.replace(
        "**Status:** Open", "**Status:** Sealed",
    ))


def test_input_lifetime_is_rejected_before_effects(tmp_path, recipe):
    managed = Managed(tmp_path)
    managed.config["core"] = str(managed.worktree / "core")
    managed.save()
    with pytest.raises(ValueError, match="survive cleanup"):
        managed.caller(recipe).prepare(managed.config_path)
    assert not managed.effects()
    assert managed.active.is_dir()


def test_malformed_result_keeps_unavailable_observations_as_unavailable(tmp_path, recipe):
    managed = Managed(tmp_path)
    port = RecordingProcesses(recipe.Processes(), terminal=(0, "unexpected output", "raw stderr"),
                              unavailable=True)
    outcome, _ = managed.invoke(recipe, port)
    assert_halt(outcome, "delivery-failed", "unexpected output", 0, "raw stderr")
    record = outcome["recovery"]["instance"]
    assert record["main_head"]["available"] is False
    assert record["main_head"]["exit"] == 128
    assert record["main_head"]["stderr"] == "observation unavailable"
    assert record["intended_landing"] is None
    assert record["disk"]["present"] is True


@pytest.mark.parametrize("fixed", [False, True])
def test_instance_cleanup_halt_retains_landed_merge_and_sealed_carving(tmp_path, recipe, fixed):
    managed = Managed(tmp_path, fixed=fixed)
    worktree = managed.worktree
    (worktree / ".gitignore").write_text("retained-recovery\n")
    git(worktree, "add", ".gitignore")
    git(worktree, "commit", "-qm", "ignore local recovery content")
    recovery_file = worktree / "retained-recovery"
    recovery_file.write_text("keep this after cleanup refusal\n")
    # Ignored content alone is removed with the worktree; a lock is what refuses removal.
    git(managed.scenario.repos["instance"], "worktree", "lock", str(worktree))

    outcome, prepared = managed.invoke(recipe)

    roles = "product,instance" if fixed else "instance"
    assert outcome["status"] == "halt"
    assert outcome["halt_reason"] == "teardown-failed"
    assert outcome["delivered"] == roles
    assert outcome["cleanup"] == "incomplete"
    assert outcome["audit_cleanup_eligible"] is False
    assert outcome["observations"]["exit"] == 1
    assert outcome["observations"]["stdout"] == terminal(roles, "teardown-failed")
    seal = outcome["seal_evidence"]["seal_sha"]
    repo = managed.scenario.repos["instance"]
    merge = git(repo, "rev-parse", "main").stdout.strip()
    assert git(repo, "show", "-s", "--format=%P", merge).stdout.split() == [
        managed.scenario.tips["instance"], seal,
    ]
    assert git(repo, "merge-base", "--is-ancestor", seal, "main").returncode == 0
    record = outcome["recovery"]["instance"]
    assert record["intended_landing"] is True
    assert record["main_head"]["stdout"].strip() == merge
    assert record["disk"] == {"available": True, "present": True}
    assert record["change_ref"]["exit"] == 0
    assert str(worktree) in record["registrations"]["stdout"]
    trail = managed.active.parent / "trail" / KEY
    assert Path(outcome["halt_report"]) == trail / "halt_report.md"
    assert not managed.active.exists()
    assert recovery_file.read_text() == "keep this after cleanup refusal\n"
    assert json.loads((prepared.directory / "result.json").read_text()) == outcome
    if fixed:
        managed.scenario.assert_cleaned("product")


@pytest.mark.parametrize("stdout", [
    "delivery: complete\ndelivered: instance\ncleanup: complete\n",
    "delivery: complete\ndelivered: instance,product\ncleanup: complete\n",
    "delivery: complete\ndelivered: product\ncleanup: complete\n",
    terminal("instance"),
    terminal("instance,product"),
])
def test_fixed_caller_rejects_incomplete_or_reordered_delivery_roles(tmp_path, recipe, stdout):
    managed = Managed(tmp_path, fixed=True)
    exit_code = 1 if stdout.startswith("delivery: halt\n") else 0
    port = RecordingProcesses(recipe.Processes(), terminal=(exit_code, stdout, "diagnostic"))

    outcome, _ = managed.invoke(recipe, port)

    assert_halt(outcome, "delivery-failed", stdout, exit_code)
    assert outcome["landing_proved"] is False
    assert not managed.effects()
    assert sum("--contract" in argv for argv, _ in port.calls) == 1


def test_filesystem_observation_failure_is_not_reported_as_absence(tmp_path, recipe):
    managed = Managed(tmp_path, fixed=True)

    class UnavailableFiles(recipe.Files):
        def exists(self, path):
            if path == managed.scenario.worktrees["product"]:
                raise OSError("disk observation unavailable")
            return super().exists(path)

    files = UnavailableFiles(tmp_path)
    port = RecordingProcesses(recipe.Processes(), terminal=(1, terminal("none"), "diagnostic"))
    outcome, _ = managed.invoke(recipe, port, files)

    assert_halt(outcome, "delivery-failed", terminal("none"))
    disk = outcome["recovery"]["product"]["disk"]
    assert disk == {"available": False, "present": None,
                    "diagnostics": "disk observation unavailable"}
    assert outcome["recorded_before"]["product"]["disk"] == disk
    assert managed.scenario.worktrees["product"].is_dir()


def audit_fixture(tmp_path, nested):
    scenario = Scenario(tmp_path)
    repo = scenario.repos["instance"]
    parent = repo / ".worktrees" / "outer branch" if nested else tmp_path
    audits = []
    for name in ["design", "implementation", "untouched"]:
        branch = KEY + "__audit-" + name
        path = parent / (name + " audit ; literal")
        git(repo, "worktree", "add", "-qb", branch, str(path), "main")
        audits.append((branch, path))
    return repo, audits


def run_audit_cleanup(tmp_path, repo, branches):
    script = tmp_path / "cleanup.py"
    script.write_text(extract(SKILL.read_text(), "caller-audit-cleanup"))
    return subprocess.run([sys.executable, str(script), str(repo), KEY, *branches],
                          cwd=tmp_path, capture_output=True, text=True)


@pytest.mark.parametrize("nested", [False, True])
def test_audit_cleanup_removes_only_explicit_joined_registered_paths(tmp_path, nested):
    repo, audits = audit_fixture(tmp_path, nested)
    before = git(repo, "rev-parse", "main").stdout
    result = run_audit_cleanup(tmp_path, repo, [branch for branch, _ in audits[:2]])
    assert result.returncode == 0, result.stderr
    for branch, path in audits[:2]:
        assert not path.exists()
        assert str(path) not in git(repo, "worktree", "list", "--porcelain").stdout
        assert git(repo, "show-ref", "--verify", "--quiet", "refs/heads/" + branch,
                   check=False).returncode == 1
    assert audits[2][1].is_dir()
    assert git(repo, "show-ref", "--verify", "refs/heads/" + audits[2][0]).returncode == 0
    assert git(repo, "rev-parse", "main").stdout == before


@pytest.mark.parametrize("fault", ["missing", "mismatch", "dirty", "unmerged", "locked",
                                   "foreign", "duplicate"])
def test_audit_cleanup_rejects_entire_invalid_set_before_mutation(tmp_path, fault):
    repo, audits = audit_fixture(tmp_path, True)
    branch, path = audits[1]
    branches = [audits[0][0], branch]
    if fault == "missing":
        git(repo, "worktree", "remove", str(path))
    elif fault == "mismatch":
        git(path, "switch", "--detach")
    elif fault == "dirty":
        (path / "retained").write_text("uncommitted")
    elif fault == "unmerged":
        (path / "new").write_text("unmerged")
        git(path, "add", "new")
        git(path, "commit", "-qm", "unmerged audit")
    elif fault == "locked":
        git(repo, "worktree", "lock", str(path))
    elif fault == "foreign":
        branches[1] = "unrelated"
    else:
        branches.append(branch)
    before = (git(repo, "show-ref").stdout, git(repo, "worktree", "list", "--porcelain").stdout)
    result = run_audit_cleanup(tmp_path, repo, branches)
    assert result.returncode == 1
    assert "teardown-failed" in result.stderr
    assert audits[0][1].is_dir()
    assert (git(repo, "show-ref").stdout,
            git(repo, "worktree", "list", "--porcelain").stdout) == before


def test_audit_cleanup_empty_joined_set_leaves_all_worktrees(tmp_path):
    repo, audits = audit_fixture(tmp_path, True)
    result = run_audit_cleanup(tmp_path, repo, [])
    assert result.returncode == 0, result.stderr
    assert all(path.is_dir() for _, path in audits)


def test_caller_cli_reports_delivery_halt_on_stderr_without_changing_json(tmp_path):
    managed = Managed(tmp_path)
    managed.config["merges"]["instance"].pop("description")
    managed.save()
    script = tmp_path / "caller.py"
    script.write_text(extract(SKILL.read_text(), "caller-delivery"))
    result = subprocess.run([sys.executable, str(script), str(managed.config_path)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1
    outcome = json.loads(result.stdout)
    assert outcome["status"] == "halt"
    assert outcome["halt_reason"] == "deliver-precondition-failed"
    assert "error: deliver-precondition-failed" in result.stderr
    assert outcome["halt_report"] in result.stderr
    assert "missing or unknown fields" in outcome["observations"]["stderr"]
    assert Path(outcome["halt_report"]).is_file()
    assert managed.worktree.is_dir()


def test_caller_cli_reports_a_preparation_refusal_in_a_halt_report(tmp_path):
    managed = Managed(tmp_path)
    source = tmp_path / "no action block.md"
    source.write_text("# An adopted source without its action block\n")
    managed.config["caller_source"] = str(source)
    managed.save()
    script = tmp_path / "caller.py"
    script.write_text(extract(SKILL.read_text(), "caller-delivery"))
    result = subprocess.run([sys.executable, str(script), str(managed.config_path)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1, result.stderr
    outcome = json.loads(result.stdout)
    assert outcome["status"] == "halt"
    assert outcome["halt_reason"] == "deliver-precondition-failed"
    assert outcome["landing_proved"] is False and outcome["delivered"] == "none"
    assert "caller-seal-action" in outcome["observations"]["stderr"]
    assert Path(outcome["halt_report"]) == managed.active / "halt_report.md"
    assert "caller-seal-action" in Path(outcome["halt_report"]).read_text()
    assert outcome["halt_report"] in result.stderr
    assert not managed.effects()
    managed.scenario.assert_recovery("instance")


@pytest.mark.parametrize("fault", ["target-branch", "missing-directory", "wrong-audit-branch"])
def test_audit_cleanup_preserves_all_state_when_registered_identity_is_unusable(tmp_path, fault):
    repo, audits = audit_fixture(tmp_path, True)
    branch, path = audits[1]
    if fault == "target-branch":
        git(repo, "switch", "-c", "other-target")
    elif fault == "missing-directory":
        shutil.rmtree(path)
    else:
        git(path, "switch", "-c", "other-audit")
    before = (git(repo, "show-ref").stdout,
              git(repo, "worktree", "list", "--porcelain", "-z").stdout,
              git(repo, "rev-parse", "HEAD").stdout)
    result = run_audit_cleanup(tmp_path, repo, [audits[0][0], branch])
    assert result.returncode == 1
    assert "error: teardown-failed" in result.stderr
    assert audits[0][1].is_dir()
    assert audits[2][1].is_dir()
    assert path.exists() is (fault != "missing-directory")
    assert (git(repo, "show-ref").stdout,
            git(repo, "worktree", "list", "--porcelain", "-z").stdout,
            git(repo, "rev-parse", "HEAD").stdout) == before


@pytest.mark.parametrize("fixed", [False, True])
def test_caller_refuses_a_refused_directional_before_any_merge(tmp_path, fixed):
    managed = Managed(tmp_path, fixed=fixed)
    managed.config["bookkeeping"]["directional"] = "Shukuba: progress: sealed " + KEY
    managed.save()
    script = tmp_path / "caller.py"
    script.write_text(extract(SKILL.read_text(), "caller-delivery"))
    result = subprocess.run([sys.executable, str(script), str(managed.config_path)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1, result.stderr
    outcome = json.loads(result.stdout)
    assert outcome["halt_reason"] == "deliver-precondition-failed"
    assert outcome["delivered"] == "none"
    assert "names no station" in outcome["observations"]["stderr"]
    assert [e["argv"][-3] for e in managed.log()] == ["check-directional"]
    assert not managed.effects()
    for role in managed.scenario.repos:
        managed.scenario.assert_recovery(role)


def test_caller_checks_the_directional_before_the_first_merge(tmp_path, recipe):
    managed = Managed(tmp_path, fixed=True)
    outcome, prepared = managed.invoke(recipe)
    managed.assert_landed(outcome, prepared)
    calls = [e["argv"] for e in managed.log()]
    check = next(at for at, argv in enumerate(calls) if "check-directional" in argv)
    first_merge = next(at for at, argv in enumerate(calls)
                       if "merge" in argv and "--check-only" not in argv)
    assert check < first_merge
    assert calls[check][calls[check].index("--directional") + 1] == \
        managed.config["bookkeeping"]["directional"]
    assert calls[check][calls[check].index("--repo") + 1] == \
        managed.config["contract"]["instance_worktree"]
