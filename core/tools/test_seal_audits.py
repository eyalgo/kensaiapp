"""Tests for seal_audits.py — the seal's audit join and its post-delivery removal.

Layer 1 hands the engine hand-written fakes for both ports and asserts on what they received.
Layer 2 runs the tool against a real repository from `test_deliver_change.Scenario` and the real
`commit_builder.py`.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

import seal_audits
from test_deliver_change import BUILDER, KEY, VERSIONED, Scenario, git

PYTHON = "python-under-test"
BUILDER_PATH = "/stable/commit_builder.py"
WORKTREE = Path("/instance/change-worktree")
BRANCH_PREFIX = f"{KEY}__audit-"
FINDINGS = f"system/projects/example/journey/tobiishi/{KEY}/flow_findings"
CONTEXT = f"tobiishi-seal {KEY} — audit fan-out join"
FULL = seal_audits.Attribution(
    actor="pm", surface="Codex", co_authored_by="gpt-6.1-sol <noreply@openai.com>",
    reasoning_effort="high", claude_session="https://claude.ai/session/abc",
)
MINIMAL = seal_audits.Attribution(actor="pm", surface="Codex")


class FakeFiles:
    """The `Files` port: a set of existing directories and a map of readable texts."""

    def __init__(self, *, dirs=(), texts=None):
        self.dirs = {Path(path) for path in dirs}
        self.texts = {Path(path): text for path, text in (texts or {}).items()}

    def is_dir(self, path):
        return Path(path) in self.dirs

    def read_text(self, path):
        try:
            return self.texts[Path(path)]
        except KeyError:
            raise FileNotFoundError(str(path)) from None


class FakeProcesses:
    """The `Processes` port for the join: one repository's refs, merge state and a builder.

    `builder_outcomes` scripts the builder call by call: `ok` merges, `ok-not-ancestor` exits 0
    without the branch becoming an ancestor, `conflict` and `hook` leave a merge in progress (with
    and without unmerged paths) and exit 1, `fail` exits 1 with nothing in progress.
    """

    def __init__(self, branches=(), *, head=f"refs/heads/{KEY}", merged=(), merge_in_progress=False,
                 unanswerable=(), builder_outcomes=(), abort_code=0):
        self.refs = [f"refs/heads/{name}" for name in branches]
        self.head = head
        self.ancestors = set(merged)
        self.merge_in_progress = merge_in_progress
        self.unanswerable = set(unanswerable)
        self.outcomes = list(builder_outcomes)
        self.abort_code = abort_code
        self.unmerged = ""
        self.calls = []

    def run(self, argv, *, cwd):
        self.calls.append(list(argv))
        if argv[0] == PYTHON:
            return self._builder(argv)
        assert argv[:2] == ["git", "-C"], argv
        return self._git(argv[3:])

    def _done(self, argv, code=0, out="", err=""):
        return subprocess.CompletedProcess(argv, code, out, err)

    def _git(self, args):
        command = args[0]
        if command in self.unanswerable:
            return self._done(args, 128, "", f"fatal: {command} cannot answer")
        if args[:3] == ["symbolic-ref", "--quiet", "HEAD"]:
            return self._done(args, 0, self.head + "\n")
        if command == "for-each-ref":
            return self._done(args, 0, "".join(ref + "\n" for ref in self.refs))
        if args[:4] == ["rev-parse", "-q", "--verify", "MERGE_HEAD"]:
            if self.merge_in_progress:
                return self._done(args, 0, "abc\n")
            return self._done(args, 1)
        if command == "diff":
            return self._done(args, 0, self.unmerged)
        if command == "merge-base":
            branch = args[2].removeprefix("refs/heads/")
            return self._done(args, 0 if branch in self.ancestors else 1)
        if command == "log":
            branch = args[2].rpartition("..")[2].removeprefix("refs/heads/")
            return self._done(args, 0, f"1a2b3c first commit of {branch}\n4d5e6f second commit\n")
        if args[:2] == ["merge", "--abort"]:
            if self.abort_code == 0:
                self.merge_in_progress = False
            return self._done(args, self.abort_code, "", "abort failed" if self.abort_code else "")
        raise AssertionError(f"unscripted git call: {args}")

    def _builder(self, argv):
        outcome = self.outcomes.pop(0) if self.outcomes else "ok"
        branch = argv[argv.index("--branch") + 1]
        if outcome == "ok":
            self.ancestors.add(branch)
            return self._done(argv)
        if outcome == "ok-not-ancestor":
            return self._done(argv)
        if outcome in ("conflict", "hook"):
            self.merge_in_progress = True
            self.unmerged = "flow_findings/clash.md\n" if outcome == "conflict" else ""
            return self._done(argv, 1, "", f"builder: merge {outcome}")
        return self._done(argv, 1, "", "builder said no")

    def builder_calls(self):
        return [call for call in self.calls if call[0] == PYTHON]

    def aborts(self):
        return [call for call in self.calls if call[-2:] == ["merge", "--abort"]]


def engine(processes, *, files=None):
    files = FakeFiles(dirs=[WORKTREE]) if files is None else files
    return seal_audits.AuditSeal(processes=processes, files=files, python=PYTHON)


def join_argv(*, key=KEY, extra=()):
    return ["join", "--worktree", str(WORKTREE), "--key", key, "--builder", BUILDER_PATH,
            "--actor", "pm", "--surface", "Codex", *extra]


def run_cli(argv, processes, *, files=None):
    out, err = io.StringIO(), io.StringIO()
    code = seal_audits.run(argv, engine=engine(processes, files=files), stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def join(processes, *, key=KEY, attribution=MINIMAL, files=None):
    return engine(processes, files=files).join(
        worktree=WORKTREE, key=key, builder=Path(BUILDER_PATH), attribution=attribution)


def values(argv, flag):
    """The tokens a flag carries: everything after it up to the next flag."""
    rest = argv[argv.index(flag) + 1:]
    end = next((i for i, token in enumerate(rest) if token.startswith("--")), len(rest))
    return rest[:end]


def merged_branches(processes):
    return [values(call, "--branch")[0] for call in processes.builder_calls()]


def test_join_set_is_only_branches_prefixed_with_key_audit_dash():
    processes = FakeProcesses([f"{BRANCH_PREFIX}x", f"{KEY}-other__audit-y", KEY,
                               BRANCH_PREFIX, "main"])
    assert join(processes) == [f"{BRANCH_PREFIX}x"]
    assert merged_branches(processes) == [f"{BRANCH_PREFIX}x"]


def test_join_set_is_taken_in_ascending_name_order():
    names = [f"{BRANCH_PREFIX}{step}" for step in ("plan", "design", "specs", "content")]
    processes = FakeProcesses(names)
    assert join(processes) == sorted(names)
    assert merged_branches(processes) == sorted(names)


def test_join_counts_an_ancestor_branch_as_joined_without_a_builder_call():
    names = [f"{BRANCH_PREFIX}{step}" for step in ("a", "b", "c", "d", "e")]
    processes = FakeProcesses(names, merged=names[:2])
    assert join(processes) == names
    assert merged_branches(processes) == names[2:]


def test_join_of_an_empty_set_reports_an_empty_list_and_calls_no_builder():
    processes = FakeProcesses(["main", KEY])
    code, out, err = run_cli(join_argv(), processes)
    assert (code, json.loads(out), err) == (0, {"key": KEY, "joined": []}, "")
    assert processes.builder_calls() == []


def test_join_calls_the_builder_once_per_branch_with_the_fixed_arguments():
    names = [f"{BRANCH_PREFIX}design", f"{BRANCH_PREFIX}plan"]
    processes = FakeProcesses(names)
    join(processes, attribution=FULL)
    assert len(processes.builder_calls()) == 2
    for call, name in zip(processes.builder_calls(), names):
        assert call[:5] == [PYTHON, BUILDER_PATH, "--repo", str(WORKTREE), "merge"]
        assert values(call, "--branch") == [name]
        assert values(call, "--target-branch") == [KEY]
        suffix = name.removeprefix(BRANCH_PREFIX)
        assert values(call, "--description") == [f"development-audit findings — {suffix}"]
        assert values(call, "--branch-commits") == [
            f"1a2b3c first commit of {name}", "4d5e6f second commit"]
        assert values(call, "--merge-context") == [CONTEXT]
        assert values(call, "--actor") == ["pm"]
        assert values(call, "--surface") == ["Codex"]
        assert values(call, "--co-authored-by") == [FULL.co_authored_by]
        assert values(call, "--reasoning-effort") == ["high"]
        assert values(call, "--claude-session") == [FULL.claude_session]
        assert "--bump" not in call
        assert all(isinstance(token, str) for token in call)


def test_join_leaves_out_an_optional_attribution_that_was_not_given():
    processes = FakeProcesses([f"{BRANCH_PREFIX}x"])
    join(processes, attribution=MINIMAL)
    (call,) = processes.builder_calls()
    for flag in ("--co-authored-by", "--reasoning-effort", "--claude-session", "--bump"):
        assert flag not in call


def test_join_output_is_one_json_object_on_stdout_only():
    names = [f"{BRANCH_PREFIX}a", f"{BRANCH_PREFIX}b"]
    code, out, err = run_cli(join_argv(), FakeProcesses(names))
    assert code == 0
    assert out.endswith("\n") and out.count("\n") == 1
    assert json.loads(out) == {"key": KEY, "joined": names}
    assert err == ""


def test_join_conflict_aborts_and_names_merge_conflict():
    names = [f"{BRANCH_PREFIX}{step}" for step in "abcde"]
    processes = FakeProcesses(names, builder_outcomes=["ok", "ok", "conflict"])
    code, out, err = run_cli(join_argv(), processes)
    assert code == 1
    assert out == ""
    assert err.startswith("error: merge-conflict: ")
    assert len(processes.builder_calls()) == 3
    assert len(processes.aborts()) == 1


def test_join_conflict_stays_merge_conflict_when_the_abort_fails():
    processes = FakeProcesses([f"{BRANCH_PREFIX}a"], builder_outcomes=["conflict"], abort_code=1)
    code, out, err = run_cli(join_argv(), processes)
    assert (code, out) == (1, "")
    assert err.startswith("error: merge-conflict: ")
    assert "abort" in err


def test_join_hook_failure_names_merge_hook_failed_and_aborts():
    processes = FakeProcesses([f"{BRANCH_PREFIX}a"], builder_outcomes=["hook"])
    code, out, err = run_cli(join_argv(), processes)
    assert (code, out) == (1, "")
    assert err.startswith("error: merge-hook-failed: ")
    assert len(processes.aborts()) == 1


def test_join_reads_the_failure_before_it_aborts():
    processes = FakeProcesses([f"{BRANCH_PREFIX}a"], builder_outcomes=["conflict"])
    run_cli(join_argv(), processes)
    calls = processes.calls
    built = next(i for i, call in enumerate(calls) if call[0] == PYTHON)
    aborted = next(i for i, call in enumerate(calls) if call[-2:] == ["merge", "--abort"])
    reads = calls[built + 1:aborted]
    assert any(call[3:7] == ["rev-parse", "-q", "--verify", "MERGE_HEAD"] for call in reads)
    assert any(call[3:5] == ["diff", "--name-only"] for call in reads)


@pytest.mark.parametrize("fault", ["missing-worktree", "head-elsewhere", "key-is-main",
                                   "merge-in-progress", "git-will-not-answer", "usage"])
def test_join_other_refusals_name_deliver_precondition_failed_and_call_no_builder(fault):
    names = [f"{BRANCH_PREFIX}a"]
    key, argv, files = KEY, join_argv(), None
    processes = FakeProcesses(names)
    if fault == "missing-worktree":
        files = FakeFiles()
    elif fault == "head-elsewhere":
        processes = FakeProcesses(names, head="refs/heads/other")
    elif fault == "key-is-main":
        key, argv = "main", join_argv(key="main")
        processes = FakeProcesses(["main__audit-a"], head="refs/heads/main")
    elif fault == "merge-in-progress":
        processes = FakeProcesses(names, merge_in_progress=True)
    elif fault == "git-will-not-answer":
        processes = FakeProcesses(names, unanswerable=["for-each-ref"])
    else:
        argv = ["join", "--key", key]
    code, out, err = run_cli(argv, processes, files=files)
    assert (code, out) == (1, "")
    assert err.startswith("error: deliver-precondition-failed: ")
    assert processes.builder_calls() == []
    assert processes.aborts() == []


def test_join_builder_failure_with_no_merge_in_progress_quotes_its_stderr():
    processes = FakeProcesses([f"{BRANCH_PREFIX}a"], builder_outcomes=["fail"])
    code, out, err = run_cli(join_argv(), processes)
    assert (code, out) == (1, "")
    assert err.startswith("error: deliver-precondition-failed: ")
    assert "builder said no" in err
    assert processes.aborts() == []


def test_join_refuses_a_merged_branch_that_is_not_then_an_ancestor():
    names = [f"{BRANCH_PREFIX}a", f"{BRANCH_PREFIX}b"]
    processes = FakeProcesses(names, builder_outcomes=["ok-not-ancestor", "ok"])
    code, out, err = run_cli(join_argv(), processes)
    assert (code, out) == (1, "")
    assert err.startswith("error: deliver-precondition-failed: ")
    assert len(processes.builder_calls()) == 1


def test_join_never_names_deliver_change_or_a_merge_into_main():
    names = [f"{BRANCH_PREFIX}{step}" for step in "abc"]
    runs = [FakeProcesses(names), FakeProcesses(names, builder_outcomes=["ok", "conflict"])]
    for processes in runs:
        run_cli(join_argv(), processes)
    argvs = [call for processes in runs for call in processes.calls]
    assert argvs
    for call in argvs:
        assert not any("deliver_change.py" in token for token in call)
        assert not {"-D", "--force", "-f"} & set(call)
        if call[0] == PYTHON:
            assert values(call, "--target-branch") == [KEY]
        elif call[3:4] == ["merge"]:
            assert "main" not in call


@pytest.mark.parametrize("unanswered", ["symbolic-ref", "merge-base"],
                         ids=["head-cannot-be-read", "ancestor-check-will-not-answer"])
def test_join_refuses_when_git_cannot_say_where_head_is_or_what_is_already_joined(unanswered):
    processes = FakeProcesses([f"{BRANCH_PREFIX}a"], unanswerable=[unanswered])
    code, out, err = run_cli(join_argv(), processes)
    assert (code, out) == (1, "")
    assert err.startswith("error: deliver-precondition-failed: ")
    assert processes.builder_calls() == []


@pytest.mark.parametrize("extra", [["--bogus"], ["stray"]], ids=["unknown-option", "stray-word"])
def test_join_names_deliver_precondition_failed_for_an_unrecognized_argument(extra):
    processes = FakeProcesses([f"{BRANCH_PREFIX}a"])
    code, out, err = run_cli(join_argv(extra=extra), processes)
    assert (code, out) == (1, "")
    assert err.startswith("error: deliver-precondition-failed: ")
    assert processes.calls == []


class UnstartableProcesses:
    """The `Processes` port on a machine where the command cannot be started at all."""

    def __init__(self):
        self.calls = []

    def run(self, argv, *, cwd):
        self.calls.append(list(argv))
        raise FileNotFoundError(2, "No such file or directory", argv[0])


def test_join_reports_a_git_that_cannot_start_as_a_refusal_line_not_a_traceback():
    processes = UnstartableProcesses()
    code, out, err = run_cli(join_argv(), processes)
    assert (code, out) == (1, "")
    assert err.startswith("error: deliver-precondition-failed: ")
    assert err.count("\n") == 1
    assert processes.calls


FINDING = "findings of {step}\n"


def make_audit_branches(scenario, steps, *, start=KEY, contents=None):
    """One audit branch per step, each in its own registered worktree adding one findings file."""
    repo = scenario.repos["instance"]
    made = []
    for step in steps:
        branch = f"{BRANCH_PREFIX}{step}"
        path = scenario.root / f"audit {step} worktree"
        git(repo, "worktree", "add", "-qb", branch, str(path), start)
        findings = path / FINDINGS / f"{step}.md"
        findings.parent.mkdir(parents=True, exist_ok=True)
        findings.write_text((contents or FINDING).format(step=step))
        git(path, "add", "system")
        git(path, "commit", "-qm", f"findings of {step}")
        made.append((branch, path))
    return made


def real_join(scenario, capsys):
    code = seal_audits.main(
        ["join", "--worktree", str(scenario.worktrees["instance"]), "--key", KEY,
         "--builder", str(BUILDER), "--actor", "pm", "--surface", "Codex"])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def merge_through_builder(scenario, branch):
    subprocess.run(
        [sys.executable, str(BUILDER), "--repo", str(scenario.worktrees["instance"]), "merge",
         "--branch", branch, "--target-branch", KEY, "--description", "earlier join",
         "--actor", "pm", "--merge-context", CONTEXT, "--surface", "Codex"],
        check=True, capture_output=True, text=True)


def audit_state(repo):
    refs = [line for line in git(repo, "for-each-ref", "--format=%(refname) %(objectname)",
                                 "refs/heads/").stdout.splitlines() if "__audit-" in line]
    listing = git(repo, "worktree", "list", "--porcelain").stdout.splitlines()
    # A registration is its path and its branch; a HEAD moves when an earlier join lands.
    return refs, [line for line in listing if line.startswith(("worktree ", "branch "))]


def test_five_audit_branches_join_as_five_merges_on_the_change_branch(tmp_path, capsys):
    scenario = Scenario(tmp_path)
    repo, worktree = scenario.repos["instance"], scenario.worktrees["instance"]
    steps = ["content", "design", "implementation", "plan", "specs"]
    branches = [branch for branch, _ in make_audit_branches(scenario, steps)]
    before = git(repo, "rev-parse", KEY).stdout.strip()
    main_before = git(repo, "rev-parse", "main").stdout
    marker_before = git(repo, "show", f"{KEY}:{VERSIONED['instance']}").stdout

    code, out, err = real_join(scenario, capsys)

    assert code == 0, err
    assert json.loads(out) == {"key": KEY, "joined": branches}
    merges = git(repo, "rev-list", "--merges", f"{before}..{KEY}").stdout.split()
    assert len(merges) == 5
    for step in steps:
        assert (worktree / FINDINGS / f"{step}.md").read_text() == FINDING.format(step=step)
    assert git(repo, "rev-parse", "main").stdout == main_before
    touched = git(repo, "diff", "--name-only", before, KEY).stdout.split()
    assert touched == sorted(f"{FINDINGS}/{step}.md" for step in steps)
    assert git(repo, "show", f"{KEY}:{VERSIONED['instance']}").stdout == marker_before


def test_rerun_after_a_partial_join_adds_only_the_missing_merges(tmp_path, capsys):
    scenario = Scenario(tmp_path)
    repo = scenario.repos["instance"]
    branches = [branch for branch, _ in
                make_audit_branches(scenario, ["a", "b", "c", "d", "e"])]
    merge_through_builder(scenario, branches[0])
    merge_through_builder(scenario, branches[1])
    before = git(repo, "rev-parse", KEY).stdout.strip()

    code, out, err = real_join(scenario, capsys)

    assert code == 0, err
    assert json.loads(out)["joined"] == branches
    assert len(git(repo, "rev-list", "--merges", f"{before}..{KEY}").stdout.split()) == 3


def test_a_real_conflict_aborts_and_leaves_every_audit_ref_and_worktree(tmp_path, capsys):
    scenario = Scenario(tmp_path)
    repo, worktree = scenario.repos["instance"], scenario.worktrees["instance"]
    made = make_audit_branches(scenario, ["a", "b"], contents="{step} wrote a different thing\n")
    for branch, path in made:
        clash = path / FINDINGS / "clash.md"
        clash.write_text(f"{branch} wrote this\n")
        git(path, "add", "system")
        git(path, "commit", "-qm", "clash")
    state = audit_state(repo)

    code, out, err = real_join(scenario, capsys)

    assert code == 1 and out == ""
    assert err.startswith("error: merge-conflict: ")
    assert git(worktree, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).returncode != 0
    assert git(repo, "merge-base", "--is-ancestor", made[0][0], KEY, check=False).returncode == 0
    assert audit_state(repo) == state
    assert all(path.is_dir() for _, path in made)


def test_a_real_commit_hook_failure_names_merge_hook_failed(tmp_path, capsys):
    scenario = Scenario(tmp_path)
    worktree = scenario.worktrees["instance"]
    make_audit_branches(scenario, ["a"])
    scenario.hook("instance", "commit-msg", "exit 1")

    code, out, err = real_join(scenario, capsys)

    assert code == 1 and out == ""
    assert err.startswith("error: merge-hook-failed: ")
    assert git(worktree, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).returncode != 0


REPO = Path("/instance/main-checkout")
REPORT_PATH = Path("/stable/audit-join.json")
OUTCOME_PATH = Path("/stable/delivery-outcome.json")
PROVED = {"status": "ok", "audit_cleanup_eligible": True, "key": KEY}


class FakeTeardown:
    """The `Processes` port for the removal: one main checkout and its registered audit worktrees.

    It answers the reads the removal makes and carries out `worktree remove` and `branch -d`, so a
    test asserts on what is left. A branch in `dirty` has an uncommitted change in its worktree, one
    in `unmerged` has a tip `main` lacks, and `flags` marks a registration `locked` or `prunable`.
    """

    def __init__(self, branches, *, main_head="refs/heads/main", dirty=(), unmerged=(),
                 flags=None, elsewhere=(), dirtied_by_removal=None):
        self.dirtied_by_removal = dict(dirtied_by_removal or {})
        self.paths = {branch: Path(f"/audits/{branch}") for branch in branches}
        self.heads = {path: f"{seal_audits.HEADS}{branch}" for branch, path in self.paths.items()}
        for branch in elsewhere:
            self.heads[self.paths[branch]] = "refs/heads/other"
        self.main_head = main_head
        self.dirty = set(dirty)
        self.unmerged = set(unmerged)
        self.flags = dict(flags or {})
        self.branches = set(branches)
        self.calls = []

    def run(self, argv, *, cwd):
        self.calls.append(list(argv))
        assert argv[:2] == ["git", "-C"], argv
        where, args = Path(argv[2]), argv[3:]
        if args[:3] == ["symbolic-ref", "--quiet", "HEAD"]:
            head = self.main_head if where == REPO else self.heads[where]
            return self._done(args, 0, head + "\n")
        if args[:3] == ["worktree", "list", "--porcelain"] and args[3:] == ["-z"]:
            return self._done(args, 0, self._registrations())
        if args[0] == "status":
            return self._done(args, 0, "?? retained\n" if self._branch_at(where) in self.dirty
                              else "")
        if args[:2] == ["merge-base", "--is-ancestor"]:
            branch = args[2].removeprefix(seal_audits.HEADS)
            lacking = branch in self.unmerged or branch not in self.branches
            return self._done(args, 1 if lacking else 0)
        if args[:2] == ["worktree", "remove"]:
            removed = self._branch_at(Path(args[2]))
            self.paths = {b: p for b, p in self.paths.items() if p != Path(args[2])}
            if removed in self.dirtied_by_removal:
                self.dirty.add(self.dirtied_by_removal[removed])
            return self._done(args, 0)
        if args[:2] == ["branch", "-d"]:
            self.branches.discard(args[2])
            return self._done(args, 0)
        if args[0] == "for-each-ref":
            ref = args[-1].removeprefix(seal_audits.HEADS)
            return self._done(args, 0, args[-1] + "\n" if ref in self.branches else "")
        raise AssertionError(f"unscripted git call: {args}")

    @staticmethod
    def _done(args, code, out=""):
        return subprocess.CompletedProcess(args, code, out, "")

    def _branch_at(self, where):
        return next((b for b, p in self.paths.items() if p == where), None)

    def _registrations(self):
        blocks = [f"worktree {REPO}\0HEAD 0\0branch refs/heads/main\0\0"]
        for branch, path in self.paths.items():
            flag = self.flags.get(branch)
            blocks.append(f"worktree {path}\0HEAD 0\0branch {seal_audits.HEADS}{branch}\0"
                          + (f"{flag}\0" if flag else "") + "\0")
        return "".join(blocks)

    def mutations(self):
        return [call for call in self.calls
                if call[3:5] in (["worktree", "remove"], ["branch", "-d"])]


def audits(*steps):
    return [f"{BRANCH_PREFIX}{step}" for step in steps]


def remove_argv(*, key=KEY):
    return ["remove", "--repo", str(REPO), "--key", key, "--joined", str(REPORT_PATH),
            "--outcome", str(OUTCOME_PATH)]


def report_text(branches, **overrides):
    return json.dumps({"key": KEY, "joined": branches, **overrides})


def removal_files(branches, *, outcome=PROVED, report=None):
    texts = {REPORT_PATH: report_text(branches) if report is None else report}
    if outcome is not None:
        texts[OUTCOME_PATH] = outcome if isinstance(outcome, str) else json.dumps(outcome)
    return FakeFiles(texts=texts)


def run_removal(teardown, branches, **kwargs):
    return run_cli(remove_argv(), teardown, files=removal_files(branches, **kwargs))


@pytest.mark.parametrize("outcome", [
    None,
    "{not json",
    "[]",
    {"status": "halt", "audit_cleanup_eligible": False, "key": KEY},
    {"status": "ok", "audit_cleanup_eligible": False, "key": KEY},
    {"status": "ok", "audit_cleanup_eligible": "true", "key": KEY},
    {"status": "ok", "audit_cleanup_eligible": 1, "key": KEY},
    {"status": "ok", "key": KEY},
    {"status": "ok", "audit_cleanup_eligible": True, "key": "2026-01-01_another-change"},
], ids=["missing", "unreadable", "not-an-object", "halt", "eligible-false", "eligible-string",
        "eligible-one", "eligible-absent", "key-mismatch"])
def test_remove_refuses_any_outcome_that_is_not_proved_success_and_calls_no_git(outcome):
    branches = audits("a", "b")
    teardown = FakeTeardown(branches)
    code, out, err = run_removal(teardown, branches, outcome=outcome)
    assert (code, out) == (1, "")
    assert err.startswith("error: teardown-failed: ")
    assert teardown.calls == []


@pytest.mark.parametrize("report", [
    "{not json",
    json.dumps({"key": "2026-01-01_another-change", "joined": []}),
    json.dumps({"key": KEY, "joined": "not-a-list"}),
    json.dumps({"key": KEY, "joined": [7]}),
    None,
], ids=["unreadable", "key-mismatch", "not-a-list", "not-strings", "missing"])
def test_remove_refuses_an_unusable_join_report_before_any_mutating_call(report):
    branches = audits("a", "b")
    teardown = FakeTeardown(branches)
    files = removal_files(branches, report=report or "")
    if report is None:
        del files.texts[REPORT_PATH]
    code, out, err = run_cli(remove_argv(), teardown, files=files)
    assert (code, out) == (1, "")
    assert err.startswith("error: teardown-failed: ")
    assert teardown.mutations() == []


def test_remove_acts_on_exactly_the_reported_branches():
    registered = audits("a", "b", "c")
    reported = registered[:2]
    teardown = FakeTeardown(registered)
    code, _, err = run_removal(teardown, reported)
    assert code == 0, err
    touched = {call[-1] for call in teardown.mutations()}
    assert touched == set(reported) | {f"/audits/{branch}" for branch in reported}
    assert registered[2] in teardown.branches
    assert Path(f"/audits/{registered[2]}") in teardown.paths.values()
    assert not any(call[3] == "for-each-ref" and call[-1] == seal_audits.HEADS
                   for call in teardown.calls)


def test_remove_checks_the_whole_set_before_removing_anything():
    branches = audits("a", "b", "c")
    teardown = FakeTeardown(branches, dirty=[branches[2]])
    code, out, err = run_removal(teardown, branches)
    assert (code, out) == (1, "")
    assert err.startswith("error: teardown-failed: ")
    assert teardown.mutations() == []


@pytest.mark.parametrize("fault", ["duplicate", "foreign", "main-elsewhere", "locked",
                                   "prunable", "unregistered", "wrong-head", "dirty", "unmerged"])
def test_remove_refuses_each_fault_of_the_set_before_any_mutation(fault):
    branches = audits("a", "b")
    reported = list(branches)
    options = {}
    if fault == "duplicate":
        reported.append(branches[0])
    elif fault == "foreign":
        reported[1] = "unrelated"
    elif fault == "main-elsewhere":
        options["main_head"] = "refs/heads/other-target"
    elif fault in ("locked", "prunable"):
        options["flags"] = {branches[1]: fault}
    elif fault == "unregistered":
        reported.append(f"{BRANCH_PREFIX}gone")
    elif fault == "wrong-head":
        options["elsewhere"] = [branches[1]]
    elif fault == "dirty":
        options["dirty"] = [branches[1]]
    else:
        options["unmerged"] = [branches[1]]
    teardown = FakeTeardown(branches, **options)
    code, out, err = run_removal(teardown, reported)
    assert (code, out) == (1, "")
    assert err.startswith("error: teardown-failed: ")
    assert teardown.mutations() == []


def test_remove_never_forces_and_never_runs_a_deliver_or_a_commit_or_a_main_merge():
    branches = audits("a", "b")
    joining = FakeProcesses(branches)
    run_cli(join_argv(), joining)
    teardown = FakeTeardown(branches)
    run_removal(teardown, branches)
    calls = joining.calls + teardown.calls
    assert teardown.mutations()
    for call in calls:
        assert not {"-D", "--force", "-f"} & set(call)
        assert not any("deliver_change.py" in token for token in call)
        assert call[3:4] != ["commit"]
        if call[3:4] == ["merge"]:
            assert "main" not in call
    code, out, err = run_cli(["remove"], FakeTeardown([]))
    assert (code, out) == (1, "")
    assert err.startswith("error: teardown-failed: ")


@pytest.mark.parametrize("argv", [
    ["remove"],
    [*remove_argv(), "--bogus"],
    [*remove_argv(), "stray"],
], ids=["missing-arguments", "unknown-option", "stray-word"])
def test_remove_names_teardown_failed_for_every_usage_error(argv):
    branches = audits("a")
    teardown = FakeTeardown(branches)
    code, out, err = run_cli(argv, teardown, files=removal_files(branches))
    assert (code, out) == (1, "")
    assert err.startswith("error: teardown-failed: ")
    assert teardown.calls == []


def test_remove_rechecks_each_branch_immediately_before_removing_it():
    branches = audits("a", "b")
    teardown = FakeTeardown(branches, dirtied_by_removal={branches[0]: branches[1]})
    code, out, err = run_removal(teardown, branches)
    assert (code, out) == (1, "")
    assert err.startswith("error: teardown-failed: ")
    assert branches[0] not in teardown.branches
    assert not any(branches[1] in call[-1] for call in teardown.mutations())
    assert branches[1] in teardown.branches
    assert branches[1] in teardown.paths


def test_remove_reports_a_git_that_cannot_start_as_a_refusal_line_not_a_traceback():
    processes = UnstartableProcesses()
    code, out, err = run_cli(remove_argv(), processes, files=removal_files(audits("a")))
    assert (code, out) == (1, "")
    assert err.startswith("error: teardown-failed: ")
    assert err.count("\n") == 1
    assert processes.calls


def test_remove_success_reports_removed_branches_in_report_order():
    branches = audits("b", "a")
    teardown = FakeTeardown(branches)
    code, out, err = run_removal(teardown, branches)
    assert (code, err) == (0, "")
    assert out.endswith("\n") and out.count("\n") == 1
    assert json.loads(out) == {"key": KEY, "removed": branches}
    assert teardown.branches == set() and teardown.paths == {}


def test_remove_of_an_empty_report_removes_nothing_and_exits_zero():
    teardown = FakeTeardown(audits("a"))
    code, out, err = run_removal(teardown, [])
    assert (code, err) == (0, "")
    assert json.loads(out) == {"key": KEY, "removed": []}
    assert teardown.mutations() == []


def test_a_branch_created_after_the_join_survives_the_removal(tmp_path, capsys):
    scenario = Scenario(tmp_path)
    repo = scenario.repos["instance"]
    joined = []
    for step in ("design", "plan"):
        path = tmp_path / f"{step} audit worktree"
        git(repo, "worktree", "add", "-qb", f"{BRANCH_PREFIX}{step}", str(path), "main")
        joined.append(f"{BRANCH_PREFIX}{step}")
    code, out, err = real_join(scenario, capsys)
    assert code == 0, err
    assert json.loads(out)["joined"] == joined
    report, outcome = tmp_path / "audit-join.json", tmp_path / "delivery-outcome.json"
    report.write_text(out)
    outcome.write_text(json.dumps(PROVED))
    late = tmp_path / "late audit worktree"
    git(repo, "worktree", "add", "-qb", f"{BRANCH_PREFIX}late", str(late), "main")

    code = seal_audits.main(["remove", "--repo", str(repo), "--key", KEY,
                             "--joined", str(report), "--outcome", str(outcome)])

    removed = capsys.readouterr()
    assert code == 0, removed.err
    assert json.loads(removed.out) == {"key": KEY, "removed": joined}
    for branch in joined:
        assert git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}",
                   check=False).returncode == 1
    assert not (tmp_path / "design audit worktree").exists()
    assert late.is_dir()
    assert git(repo, "show-ref", "--verify", f"refs/heads/{BRANCH_PREFIX}late").returncode == 0


# The contract suites: each fake above against the real adapter it stands in for, so a unit test
# that passes on a fake says something about the real port (testing_doctrine.md § A fake is
# verified against its port's contract). Layer 2: the real runs work in `tmp_path` only.

TEXT = '{"key": "k"}\n'


class FilesContract:
    """The `Files` port as the removal reads it: the text back, a miss as `OSError`, a dir test."""

    def make(self, tmp_path):
        raise NotImplementedError

    def test_reads_back_the_text_a_file_holds(self, tmp_path):
        files, text_path, _ = self.make(tmp_path)
        assert files.read_text(text_path) == TEXT

    def test_a_missing_file_is_an_os_error(self, tmp_path):
        files, _, _ = self.make(tmp_path)
        with pytest.raises(OSError):
            files.read_text(tmp_path / "absent.json")

    def test_says_a_directory_exists_and_a_file_or_a_missing_path_is_not_one(self, tmp_path):
        files, text_path, directory = self.make(tmp_path)
        assert files.is_dir(directory) is True
        assert files.is_dir(text_path) is False
        assert files.is_dir(tmp_path / "absent") is False


class TestTheRealFiles(FilesContract):
    def make(self, tmp_path):
        text_path, directory = tmp_path / "report.json", tmp_path / "worktree"
        text_path.write_text(TEXT)
        directory.mkdir()
        return seal_audits.Files(), text_path, directory


class TestTheFakeFiles(FilesContract):
    def make(self, tmp_path):
        text_path, directory = tmp_path / "report.json", tmp_path / "worktree"
        return FakeFiles(dirs=[directory], texts={text_path: TEXT}), text_path, directory


class JoinGitContract:
    """The git answers the join decides by, in a change worktree on `<key>` whose audit branch
    `a` is already joined and whose audit branch `b` is not."""

    def make(self, tmp_path):
        raise NotImplementedError

    def answer(self, tmp_path, *args):
        processes, worktree = self.make(tmp_path)
        return processes.run(["git", "-C", str(worktree), *args], cwd=None)

    def test_head_is_the_change_branch(self, tmp_path):
        result = self.answer(tmp_path, "symbolic-ref", "--quiet", "HEAD")
        assert (result.returncode, result.stdout.strip()) == (0, f"refs/heads/{KEY}")

    def test_the_ref_listing_holds_both_audit_branches(self, tmp_path):
        result = self.answer(tmp_path, "for-each-ref", "--format=%(refname)", "refs/heads/")
        assert result.returncode == 0
        assert {f"refs/heads/{BRANCH_PREFIX}a", f"refs/heads/{BRANCH_PREFIX}b"} <= set(
            result.stdout.splitlines())

    def test_no_merge_is_in_progress(self, tmp_path):
        assert self.answer(tmp_path, "rev-parse", "-q", "--verify", "MERGE_HEAD").returncode == 1

    @pytest.mark.parametrize("step,status", [("a", 0), ("b", 1)])
    def test_the_ancestor_check_says_which_branch_is_joined(self, tmp_path, step, status):
        result = self.answer(tmp_path, "merge-base", "--is-ancestor",
                             f"refs/heads/{BRANCH_PREFIX}{step}", f"refs/heads/{KEY}")
        assert result.returncode == status

    def test_an_unjoined_branch_has_commit_lines_of_its_own(self, tmp_path):
        result = self.answer(tmp_path, "log", "--oneline",
                             f"refs/heads/{KEY}..refs/heads/{BRANCH_PREFIX}b")
        assert result.returncode == 0 and result.stdout.splitlines()


class TestTheRealGitAnswersTheJoin(JoinGitContract):
    def make(self, tmp_path):
        scenario = Scenario(tmp_path)
        make_audit_branches(scenario, ["a", "b"])
        merge_through_builder(scenario, f"{BRANCH_PREFIX}a")
        return seal_audits.Processes(), scenario.worktrees["instance"]


class TestTheFakeGitAnswersTheJoin(JoinGitContract):
    def make(self, tmp_path):
        names = [f"{BRANCH_PREFIX}a", f"{BRANCH_PREFIX}b", KEY, "main"]
        return FakeProcesses(names, merged=[f"{BRANCH_PREFIX}a"]), WORKTREE


class TeardownGitContract:
    """The git answers and effects the removal relies on, from a main checkout on `main` with one
    audit branch, an ancestor of `main`, registered in a worktree of its own."""

    BRANCH = f"{BRANCH_PREFIX}x"

    def make(self, tmp_path, *, dirty=False):
        raise NotImplementedError

    @staticmethod
    def git(processes, where, *args):
        return processes.run(["git", "-C", str(where), *args], cwd=None)

    def registered_path(self, processes, repo):
        listing = self.git(processes, repo, "worktree", "list", "--porcelain", "-z").stdout
        for block in listing.split("\0\0"):
            fields = dict(field.partition(" ")[::2] for field in block.split("\0") if field)
            if fields.get("branch") == f"refs/heads/{self.BRANCH}":
                return fields["worktree"]
        return None

    def test_the_main_checkout_is_on_main(self, tmp_path):
        processes, repo = self.make(tmp_path)
        assert self.git(processes, repo, "symbolic-ref", "--quiet", "HEAD").stdout.strip() == (
            "refs/heads/main")

    def test_the_audit_worktree_is_registered_on_its_branch_and_clean(self, tmp_path):
        processes, repo = self.make(tmp_path)
        path = self.registered_path(processes, repo)
        assert path is not None
        head = self.git(processes, path, "symbolic-ref", "--quiet", "HEAD")
        assert head.stdout.strip() == f"refs/heads/{self.BRANCH}"
        status = self.git(processes, path, "status", "--porcelain", "--untracked-files=all")
        assert (status.returncode, status.stdout) == (0, "")

    def test_an_untracked_file_shows_in_the_status(self, tmp_path):
        processes, repo = self.make(tmp_path, dirty=True)
        path = self.registered_path(processes, repo)
        status = self.git(processes, path, "status", "--porcelain", "--untracked-files=all")
        assert status.stdout

    def test_the_branch_is_an_ancestor_of_main(self, tmp_path):
        processes, repo = self.make(tmp_path)
        result = self.git(processes, repo, "merge-base", "--is-ancestor",
                          f"refs/heads/{self.BRANCH}", "refs/heads/main")
        assert result.returncode == 0

    def test_removing_the_worktree_and_branch_leaves_no_registration_or_ref(self, tmp_path):
        processes, repo = self.make(tmp_path)
        path = self.registered_path(processes, repo)
        assert self.git(processes, repo, "worktree", "remove", path).returncode == 0
        assert self.git(processes, repo, "branch", "-d", self.BRANCH).returncode == 0
        assert self.registered_path(processes, repo) is None
        refs = self.git(processes, repo, "for-each-ref", "--format=%(refname)",
                        f"refs/heads/{self.BRANCH}")
        assert (refs.returncode, refs.stdout) == (0, "")


class TestTheRealGitAnswersTheRemoval(TeardownGitContract):
    def make(self, tmp_path, *, dirty=False):
        scenario = Scenario(tmp_path)
        repo, path = scenario.repos["instance"], tmp_path / "x audit worktree"
        git(repo, "worktree", "add", "-qb", self.BRANCH, str(path), "main")
        if dirty:
            (path / "retained").write_text("uncommitted\n")
        return seal_audits.Processes(), repo


class TestTheFakeGitAnswersTheRemoval(TeardownGitContract):
    def make(self, tmp_path, *, dirty=False):
        return FakeTeardown([self.BRANCH], dirty=[self.BRANCH] if dirty else ()), REPO


class UnstartableContract:
    """A program that cannot be started is an `OSError` from the port, not a result."""

    def make(self, tmp_path):
        raise NotImplementedError

    def test_a_program_that_cannot_start_raises_an_os_error(self, tmp_path):
        processes, argv = self.make(tmp_path)
        with pytest.raises(OSError):
            processes.run(argv, cwd=None)


class TestTheRealProcessesCannotStartAMissingProgram(UnstartableContract):
    def make(self, tmp_path):
        return seal_audits.Processes(), [str(tmp_path / "no-such-program")]


class TestTheUnstartableFake(UnstartableContract):
    def make(self, tmp_path):
        return UnstartableProcesses(), ["git"]
