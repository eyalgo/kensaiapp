"""Delivery proof through real CLI/git, with injected ports only for impossible I/O faults."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import deliver_change
import development_path

TOOL = Path(__file__).with_name("deliver_change.py")
BUILDER = Path(__file__).with_name("commit_builder.py")
KEY = "2026-09-30_example-change"


def git(repo, *args, check=True):
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=check,
    )


def commit(repo, filename, content):
    (repo / filename).write_text(content)
    git(repo, "add", filename)
    git(repo, "commit", "-qm", filename)


def snapshot(repo):
    return tuple(git(repo, *args, check=False).stdout for args in [
        ("show-ref",), ("worktree", "list", "--porcelain"),
        ("status", "--porcelain"), ("ls-files", "--stage"),
    ])


def refusal_snapshot(repo, worktree):
    """Keep failed observations intact while comparing deliberately invalid checkouts."""
    commands = [
        (repo, ("log", "--all", "--format=%H %P")),
        (repo, ("show-ref",)),
        (repo, ("worktree", "list", "--porcelain")),
    ]
    for checkout in (repo, worktree):
        commands.extend((checkout, args) for args in [
            ("rev-parse", "HEAD"), ("status", "--porcelain"), ("ls-files", "--stage"),
        ])
    observations = []
    for checkout, args in commands:
        result = git(checkout, *args, check=False)
        observations.append((result.returncode, result.stdout, result.stderr))
    return tuple(observations)


class Scenario:
    def __init__(self, root, fixed=False):
        self.root = root
        self.events = root / "events.jsonl"
        self.repos = {}
        self.worktrees = {}
        self.tips = {}
        for role in (["product", "instance"] if fixed else ["instance"]):
            repo = root / f"{role} repo ; literal"
            repo.mkdir()
            git(repo, "init", "-qb", "main")
            git(repo, "config", "user.name", "Example")
            git(repo, "config", "user.email", "example@example.invalid")
            git(repo, "config", "core.hooksPath", str(root / f"{role}-hooks"))
            commit(repo, "version.py", '__version__ = "1.0.0"\n')
            commit(repo, "shared", "base\n")
            worktree = root / f"{role} change ; literal"
            git(repo, "worktree", "add", "-qb", KEY, str(worktree))
            commit(worktree, "shared", f"{role} change\n")
            self.repos[role] = repo
            self.worktrees[role] = worktree
            self.tips[role] = git(repo, "rev-parse", "main").stdout.strip()
            git(repo, "branch", "unrelated")
        instance = self.repos["instance"]
        product = self.repos.get("product", instance)
        self.contract = development_path.build_contract(
            kind="fixed" if fixed else "relative", project="example", key=KEY,
            product_path=str(product) if fixed else ".", instance_repo=str(instance),
            instance_worktree=str(self.worktrees["instance"]), product_repo=str(product),
            product_worktree=str(self.worktrees.get("product", self.worktrees["instance"])),
        )
        self.merges = {role: {
            "description": f"deliver {role}", "merge_context": f"verified {role}",
            "surface": "Codex", "actor": "pm",
        } for role in self.repos}
        self.wrapper = root / "record builder.py"
        self.wrapper.write_text(
            "import json, subprocess, sys\nfrom pathlib import Path\n"
            f"log = Path({str(self.events)!r})\n"
            f"r = subprocess.run([sys.executable, {str(BUILDER)!r}, *sys.argv[1:]], "
            "capture_output=True, text=True)\n"
            "with log.open('a') as f: f.write(json.dumps({'argv': sys.argv[1:], "
            "'returncode': r.returncode}) + '\\n')\n"
            "print(r.stdout, end=''); print(r.stderr, end='', file=sys.stderr)\n"
            "sys.exit(r.returncode)\n"
        )
        self.seal_script = root / "seal literal ; $.py"
        self.set_seal()
        self.seal = {"argv": [sys.executable, str(self.seal_script), "literal ; $(echo bad)"]}

    def set_seal(self, before="", after=""):
        self.seal_script.write_text(
            "import json, subprocess, sys\nfrom pathlib import Path\n"
            f"repo = Path.cwd()\nlog = Path({str(self.events)!r})\n"
            "def run(*args):\n"
            "    return subprocess.run(['git', '-C', str(repo), *args], check=True, "
            "capture_output=True, text=True).stdout.strip()\n"
            + before + "\n"
            "Path('seal-content').write_text(sys.argv[1])\n"
            f"r = subprocess.run([sys.executable, {str(BUILDER)!r}, '--repo', str(repo), "
            "'commit', '--add', 'seal-content', '--subject', 'seal: example', '--actor', 'pm', "
            "'--directional', 'Agari: example — progress: seal', '--surface', 'Codex'], "
            "check=True, capture_output=True, text=True)\n"
            "with log.open('a') as f: f.write(json.dumps({'seal': run('rev-parse', 'HEAD'), "
            "'argv': sys.argv[1:]}) + '\\n')\n"
            + after + "\n"
        )

    def write_inputs(self):
        paths = []
        for name, value in [("contract", self.contract), ("merges", self.merges),
                            ("seal", self.seal)]:
            path = self.root / f"{name} input.json"
            path.write_text(json.dumps(value))
            paths.append(path)
        return paths

    def call(self, builder=None, paths=None):
        paths = paths or self.write_inputs()
        return subprocess.run(
            [sys.executable, str(TOOL), "--contract", str(paths[0]), "--merges", str(paths[1]),
             "--seal-action", str(paths[2]), "--builder", str(builder or self.wrapper)],
            cwd=self.root, capture_output=True, text=True,
        )

    def log(self):
        return [json.loads(line) for line in self.events.read_text().splitlines()] \
            if self.events.exists() else []

    def merges_called(self):
        return [e for e in self.log() if "seal" not in e and "--check-only" not in e["argv"]]

    def assert_recovery(self, role):
        assert self.worktrees[role].is_dir()
        assert str(self.worktrees[role]) in git(self.repos[role], "worktree", "list",
                                               "--porcelain").stdout
        assert git(self.repos[role], "rev-parse", KEY).returncode == 0
        assert git(self.repos[role], "rev-parse", "main").stdout.strip() == self.tips[role]

    def assert_cleaned(self, role):
        repo, worktree = self.repos[role], self.worktrees[role]
        assert not worktree.exists()
        assert str(worktree) not in git(repo, "worktree", "list", "--porcelain").stdout
        assert git(repo, "show-ref", "--verify", f"refs/heads/{KEY}", check=False).returncode != 0
        assert git(repo, "rev-parse", "unrelated").returncode == 0

    def hook(self, role, name, body):
        hooks = self.root / f"{role}-hooks"
        hooks.mkdir(exist_ok=True)
        path = hooks / name
        path.write_text("#!/bin/sh\n" + body + "\n")
        path.chmod(0o755)


def halt(result, code, delivered="none"):
    assert result.returncode == 1, result.stderr
    assert result.stdout == (f"delivery: halt\nhalt: {code}\ndelivered: {delivered}\n"
                             "cleanup: incomplete\n"), result.stderr
    assert result.stderr and "Traceback" not in result.stderr


def success(result, roles):
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"delivery: complete\ndelivered: {roles}\ncleanup: complete\n"


def assert_success(s, result):
    roles = list(s.repos)
    success(result, ",".join(roles))
    events = [e for e in s.log() if "seal" in e or "--check-only" not in e["argv"]]
    assert ["seal" if "seal" in e else Path(e["argv"][1]).name.split()[0]
            for e in events] == (["product", "seal", "instance"]
                                if "product" in roles else ["seal", "instance"])
    seal_sha = next(e["seal"] for e in events if "seal" in e)
    for role in roles:
        parents = git(s.repos[role], "show", "-s", "--format=%P", "main").stdout.split()
        assert len(parents) == 2 and parents[0] == s.tips[role]
        if role == "instance":
            assert parents[1] == seal_sha
            assert git(s.repos[role], "show", "main:seal-content").stdout == \
                "literal ; $(echo bad)"
        else:
            assert git(s.repos[role], "show", f"{parents[1]}:shared").stdout == "product change\n"
        s.assert_cleaned(role)
    assert len(s.merges_called()) == len(roles)


def test_single_repo_seals_then_delivers_once(tmp_path):
    s = Scenario(tmp_path)
    assert_success(s, s.call())


def test_fixed_delivery_orders_product_seal_instance(tmp_path):
    s = Scenario(tmp_path, True)
    product = str(s.worktrees["product"])
    repo = str(s.repos["product"])
    s.set_seal(before=f"assert not Path({product!r}).exists()\n"
               f"assert {product!r} not in subprocess.check_output(['git', '-C', {repo!r}, "
               "'worktree', 'list', '--porcelain'], text=True)\n"
               f"assert subprocess.run(['git', '-C', {repo!r}, 'show-ref', '--verify', "
               f"'refs/heads/{KEY}'], capture_output=True).returncode != 0")
    assert_success(s, s.call())


def test_delivery_passes_per_role_metadata_unchanged(tmp_path):
    s = Scenario(tmp_path, True)
    for role, effort, level in [("product", "max", "minor"), ("instance", "high", "patch")]:
        s.merges[role].update(branch_commits=[f"{role} first", f"{role} second"],
                              co_authored_by=f"{role} <example@example.invalid>",
                              reasoning_effort=effort, claude_session=f"session-{role}",
                              bump=[f"version.py={level}"])
    del s.merges["instance"]["actor"]
    s.merges["instance"]["authorizer"] = "Product"
    assert_success(s, s.call())
    for role, metadata in s.merges.items():
        calls = [e["argv"] for e in s.log() if "seal" not in e
                 and e["argv"][1] == str(s.repos[role])]
        assert len(calls) == (3 if role == "product" else 3)
        for argv in calls:
            for field, value in metadata.items():
                flag = "--" + field.replace("_", "-")
                values = value if isinstance(value, list) else [value]
                start = argv.index(flag) + 1
                assert argv[start:start + len(values)] == values
        body = git(s.repos[role], "log", "-1", "--format=%B").stdout
        assert f"Reasoning-Effort: {metadata['reasoning_effort']}" in body
        assert f"Co-Authored-By: {metadata['co_authored_by']}" in body
        assert f"Claude-Session: {metadata['claude_session']}" in body
        assert body.index(metadata["branch_commits"][0]) < body.index(metadata["branch_commits"][1])
        assert f"Merge-Authorized: {'PM' if role == 'product' else 'Product'}" in body
        expected = "1.1.0" if role == "product" else "1.0.1"
        assert expected in git(s.repos[role], "show", "main:version.py").stdout


@pytest.mark.parametrize("empty", [False, True])
def test_delivery_preserves_optional_absence(tmp_path, empty):
    s = Scenario(tmp_path)
    if empty:
        s.merges["instance"].update(branch_commits=[], bump=[])
    assert_success(s, s.call())
    body = git(s.repos["instance"], "log", "-1", "--format=%B").stdout
    for trailer in ("Co-Authored-By:", "Claude-Session:", "Reasoning-Effort:"):
        assert trailer not in body
    for e in s.merges_called():
        assert not any(flag in e["argv"] for flag in (
            "--co-authored-by", "--claude-session", "--reasoning-effort"))


def test_delivery_treats_paths_and_argv_as_literal_arguments(tmp_path):
    s = Scenario(tmp_path)
    assert_success(s, s.call())
    assert not (tmp_path / "bad").exists()
    assert next(e for e in s.log() if "seal" in e)["argv"] == ["literal ; $(echo bad)"]


def test_delivery_resolves_relative_cli_paths_from_invocation_directory(tmp_path):
    s = Scenario(tmp_path)
    paths = s.write_inputs()
    result = subprocess.run(
        [sys.executable, str(TOOL), "--contract", paths[0].name,
         "--merges", paths[1].name, "--seal-action", paths[2].name,
         "--builder", s.wrapper.name],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert_success(s, result)
    assert all(path.is_file() for path in paths)


INVALID = ["unreadable", "json", "missing", "type", "kind", "alias", "repo",
           "reversed", "empty", "duplicate", "unknown-role", "extra-role", "missing-role",
           "merge-field", "merge-type", "seal-field", "seal-type", "seal-empty", "branch",
           "relative-path", "extra-contract", "unsupported-kind", "both-identities",
           "relative-real-path", "relative-distinct", "fixed-same-repo"]


@pytest.mark.parametrize("fault", INVALID)
def test_delivery_rejects_invalid_input_before_effects(tmp_path, fault):
    s = Scenario(tmp_path, True)
    before = {r: snapshot(p) for r, p in s.repos.items()}
    c = s.contract
    if fault == "missing": del c["key"]
    elif fault == "type": c["project"] = 42
    elif fault == "kind": c["kind"] = "relative"
    elif fault == "unsupported-kind": c["kind"] = "unsupported"
    elif fault == "alias": c["pipeline_worktree"] = c["product_worktree"]
    elif fault == "repo": c["instance_repo"] = c["product_repo"]
    elif fault == "reversed": c["delivery_repos"].reverse()
    elif fault == "empty": c["delivery_repos"] = []
    elif fault == "duplicate": c["delivery_repos"] = ["product", "product", "instance"]
    elif fault == "unknown-role": c["delivery_repos"] = ["other"]
    elif fault == "extra-role": s.merges["other"] = s.merges["instance"]
    elif fault == "missing-role": del s.merges["instance"]
    elif fault == "merge-field": s.merges["instance"]["target_branch"] = "other"
    elif fault == "merge-type": s.merges["instance"]["bump"] = [42]
    elif fault == "seal-field": s.seal["shell"] = True
    elif fault == "seal-type": s.seal["argv"] = "sh"
    elif fault == "seal-empty": s.seal["argv"] = []
    elif fault == "branch": c["key"] = "main"
    elif fault == "relative-path": c["instance_repo"] = "relative"
    elif fault == "relative-real-path": c["instance_repo"] = s.repos["instance"].name
    elif fault == "relative-distinct":
        c.update(kind="relative", product_path=".", delivery_repos=["instance"])
        del s.merges["product"]
    elif fault == "fixed-same-repo":
        c.update(product_path=c["instance_repo"], product_repo=c["instance_repo"],
                 product_worktree=c["instance_worktree"], code_repo=c["instance_repo"],
                 code_worktree=c["instance_worktree"])
    elif fault == "extra-contract": c["extra"] = "bad"
    elif fault == "both-identities": s.merges["instance"]["authorizer"] = "Product"
    paths = s.write_inputs()
    if fault == "unreadable": paths[0].unlink()
    if fault == "json": paths[0].write_text("{")
    halt(s.call(paths=paths), "deliver-precondition-failed")
    assert not s.merges_called() and not any("seal" in e for e in s.log())
    for role in s.repos:
        assert snapshot(s.repos[role]) == before[role]
        s.assert_recovery(role)


@pytest.mark.parametrize("field,value", [("actor", "developer"), ("reasoning_effort", "bad"),
    ("branch_commits", [" "]), ("bump", ["missing.py=minor"])])
def test_delivery_checks_second_role_builder_inputs_before_product_merge(tmp_path, field, value):
    s = Scenario(tmp_path, True)
    s.merges["instance"][field] = value
    halt(s.call(), "deliver-precondition-failed")
    assert not s.merges_called()
    for role in s.repos: s.assert_recovery(role)


@pytest.mark.parametrize("fault", ["builder", "seal"])
def test_delivery_rejects_unusable_runtime_before_effects(tmp_path, fault):
    s = Scenario(tmp_path)
    if fault == "seal": s.seal["argv"][0] = str(tmp_path / "absent")
    halt(s.call(builder=tmp_path / "absent" if fault == "builder" else None),
         "deliver-precondition-failed")
    s.assert_recovery("instance")
    assert not s.merges_called()


def refusal_reason(fault, role, repo, worktree):
    """The diagnostic that names this fault, so a refusal for another cause cannot pass."""
    checkout = worktree if fault.startswith("change") else repo
    if fault.startswith("target-") and fault.endswith(("tracked", "staged", "untracked")):
        path, cause = {"target-tracked": ("shared", "collides with a path the merge writes"),
                       "target-staged": ("shared", "staged"),
                       "target-untracked": ("new", "collides with a path the merge writes")
                       }[fault]
        return (f"{role} primary checkout {repo} holds an uncommitted entry this delivery "
                f"refuses: `{path}` ({cause})")
    return {
        "missing": f"{role} worktree", "foreign": f"not of the {role} repository",
        "subdirectory": "is not the root of a git worktree",
        "unregistered": f"{role} unregistered: {worktree}", "detached": "has a detached HEAD",
        "wrong-branch": "is on branch 'wrong'", "target-branch": f"{role} {repo} must be on main",
    }.get(fault) or (f"{role} {checkout} MERGE_HEAD=present" if fault.endswith("merge")
                     else f"{role} dirty checkout: {checkout}")


@pytest.mark.parametrize("fault", ["missing", "foreign", "subdirectory", "unregistered", "detached",
    "wrong-branch", "target-branch", "target-tracked", "target-staged", "target-untracked",
    "change-tracked", "change-staged", "change-untracked", "target-merge", "change-merge"])
@pytest.mark.parametrize("role", ["product", "instance"])
def test_delivery_rejects_invalid_live_repository_state(tmp_path, fault, role):
    s = Scenario(tmp_path, True)
    for name in s.repos:
        s.assert_recovery(name)
    repo, wt = s.repos[role], s.worktrees[role]
    if fault in ("missing", "foreign", "subdirectory"):
        path = tmp_path / "absent" if fault == "missing" else (
            s.worktrees["instance" if role == "product" else "product"]
            if fault == "foreign" else wt / "child")
        if fault == "subdirectory": path.mkdir()
        fields = ("instance_worktree", "pipeline_worktree") if role == "instance" else (
            "product_worktree", "code_worktree",
        )
        for field in fields:
            s.contract[field] = str(path)
    elif fault == "unregistered":
        # Detach the registration from its on-disk .git file, without changing any unrelated tree.
        metadata = Path((wt / ".git").read_text().split(": ")[1].strip())
        (metadata / "gitdir").write_text(str(tmp_path / "elsewhere/.git"))
    elif fault == "detached":
        git(wt, "checkout", "--detach", git(wt, "rev-parse", "HEAD").stdout.strip())
    elif fault == "wrong-branch": git(wt, "checkout", "-qb", "wrong")
    elif fault == "target-branch": git(repo, "checkout", "unrelated")
    elif fault.endswith("merge"):
        git(wt if fault.startswith("change") else repo, "merge", "--no-ff", "--no-commit",
            "main" if fault.startswith("change") else KEY, check=False)
        if fault.startswith("change"):
            merge_path = Path(git(wt, "rev-parse", "--git-path", "MERGE_HEAD").stdout.strip())
            merge_path.write_text(s.tips[role] + "\n")
    else:
        location = wt if fault.startswith("change") else repo
        if fault == "target-untracked":
            commit(wt, "new", "branch adds it")  # an unrelated untracked file now delivers
        (location / ("new" if fault.endswith("untracked") else "shared")).write_text("dirt")
        if fault.endswith("staged"): git(location, "add", "shared")
    before = {name: refusal_snapshot(s.repos[name], s.worktrees[name]) for name in s.repos}
    result = s.call()
    halt(result, "deliver-precondition-failed")
    assert refusal_reason(fault, role, repo, wt) in result.stderr, result.stderr
    assert not s.merges_called()
    assert not any("seal" in event for event in s.log())
    for name in s.repos:
        assert refusal_snapshot(s.repos[name], s.worktrees[name]) == before[name]
        assert s.worktrees[name].is_dir()
        assert git(s.repos[name], "show-ref", "--verify", f"refs/heads/{KEY}").returncode == 0


@pytest.mark.parametrize("fixed", [False, True])
def test_unrelated_uncommitted_work_in_primary_checkout_delivers(tmp_path, fixed):
    s = Scenario(tmp_path, fixed)
    for role, repo in s.repos.items():
        commit(repo, "other", "base\n")
        s.tips[role] = git(repo, "rev-parse", "main").stdout.strip()
        (repo / "other").write_text("my edit\n")
        (repo / "note").write_text("untracked\n")
    assert_success(s, s.call())
    for repo in s.repos.values():
        assert (repo / "other").read_text() == "my edit\n"
        assert (repo / "note").read_text() == "untracked\n"
        merged = git(repo, "show", "--stat", "--format=", "main").stdout
        assert "other" not in merged and "note" not in merged


@pytest.mark.parametrize("fixed", [False, True])
def test_unrelated_uncommitted_work_survives_a_bumped_merge(tmp_path, fixed):
    """CP-527 where the merge also bumps: the bump stages and commits its own file, and an
    unrelated edit or untracked file beside it still stays on disk and out of the merge commit."""
    s = Scenario(tmp_path, fixed)
    for role, repo in s.repos.items():
        s.merges[role]["bump"] = ["version.py=patch"]
        commit(repo, "other", "base\n")
        s.tips[role] = git(repo, "rev-parse", "main").stdout.strip()
        (repo / "other").write_text("my edit\n")
        (repo / "note").write_text("untracked\n")
    assert_success(s, s.call())
    for repo in s.repos.values():
        assert (repo / "other").read_text() == "my edit\n"
        assert (repo / "note").read_text() == "untracked\n"
        written = git(repo, "diff", "--name-only", "main^1", "main").stdout.split()
        assert "version.py" in written
        assert "other" not in written and "note" not in written
        assert git(repo, "show", "main:other").stdout == "base\n"


def test_staged_rename_is_named_with_both_paths(tmp_path):
    """change_text: a rename is written with both of its paths, the source first."""
    s = Scenario(tmp_path)
    repo = s.repos["instance"]
    commit(repo, "other", "base\n")
    git(repo, "mv", "other", "moved")
    result = s.call()
    halt(result, "deliver-precondition-failed")
    assert (f"instance primary checkout {repo} holds an uncommitted entry this delivery "
            "refuses: `other -> moved` (staged)") in result.stderr
    assert not s.merges_called()


def test_staged_entry_in_primary_checkout_refuses(tmp_path):
    s = Scenario(tmp_path)
    repo, wt = s.repos["instance"], s.worktrees["instance"]
    commit(repo, "other", "base\n")
    s.tips["instance"] = git(repo, "rev-parse", "main").stdout.strip()
    (repo / "other").write_text("staged edit\n")
    git(repo, "add", "other")
    before = refusal_snapshot(repo, wt)
    result = s.call()
    halt(result, "deliver-precondition-failed")
    assert "`other` (staged)" in result.stderr
    assert not s.merges_called() and not any("seal" in e for e in s.log())
    assert refusal_snapshot(repo, wt) == before


def collide(s, case):
    repo, wt = s.repos["instance"], s.worktrees["instance"]
    if case == "edit-branch-changed":
        (repo / "shared").write_text("dirt")
    elif case == "untracked-branch-added":
        commit(wt, "added", "x")
        (repo / "added").write_text("dirt")
    elif case == "edit-bump-path":
        s.merges["instance"]["bump"] = ["version.py=patch"]
        (repo / "version.py").write_text("dirt")
    elif case == "file-where-branch-adds-folder":
        (wt / "d").mkdir()
        commit(wt, "d/f", "x")
        (repo / "d").write_text("dirt")
    elif case == "folder-where-branch-adds-file":
        commit(wt, "d", "x")
        (repo / "d").mkdir()
        (repo / "d" / "f").write_text("dirt")


@pytest.mark.parametrize("case", ["edit-branch-changed", "untracked-branch-added",
    "edit-bump-path", "file-where-branch-adds-folder", "folder-where-branch-adds-file"])
def test_colliding_entry_in_primary_checkout_refuses(tmp_path, case):
    s = Scenario(tmp_path)
    collide(s, case)
    result = s.call()
    halt(result, "deliver-precondition-failed")
    assert "(collides with a path the merge writes)" in result.stderr
    assert not s.merges_called() and not any("seal" in e for e in s.log())
    s.assert_recovery("instance")


def test_path_the_seal_adds_is_checked_at_the_instance_merge(tmp_path):
    s = Scenario(tmp_path)
    repo = s.repos["instance"]
    s.set_seal(after=f"Path({str(repo / 'seal-content')!r}).write_text('dirt')")
    result = s.call()
    halt(result, "deliver-precondition-failed")
    assert "`seal-content` (collides with a path the merge writes)" in result.stderr
    assert not s.merges_called()
    assert git(repo, "rev-parse", "main").stdout.strip() == s.tips["instance"]


def test_refusal_names_each_entry_and_its_cause(tmp_path):
    s = Scenario(tmp_path)
    repo = s.repos["instance"]
    commit(repo, "other", "base\n")
    (repo / "other").write_text("edit\n")
    git(repo, "add", "other")
    (repo / "shared").write_text("dirt")
    result = s.call()
    halt(result, "deliver-precondition-failed")
    assert (f"instance primary checkout {repo} holds uncommitted entries this delivery "
            "refuses: `other` (staged), `shared` (collides with a path the merge writes)"
            ) in result.stderr


def test_change_worktree_still_refuses_any_entry(tmp_path):
    s = Scenario(tmp_path)
    (s.worktrees["instance"] / "unrelated").write_text("dirt")
    result = s.call()
    halt(result, "deliver-precondition-failed")
    assert f"instance dirty checkout: {s.worktrees['instance']}" in result.stderr
    assert not s.merges_called()


def test_teardown_ignores_unrelated_primary_entries(tmp_path):
    s = Scenario(tmp_path)
    repo = s.repos["instance"]
    s.hook("instance", "post-merge", f"printf keep > '{repo / 'unrelated'}'")
    assert_success(s, s.call())
    assert (repo / "unrelated").read_text() == "keep"


def test_entry_reading_keeps_a_first_unstaged_entry_unstaged():
    entries = deliver_change.parse_entries(" M path\0?? other\0")
    assert [(e.status, e.path) for e in entries] == [(" M", "path"), ("??", "other")]
    refused = deliver_change.refusing_entries(entries, {"path"})
    assert refused == [(entries[0], deliver_change.Cause.COLLISION)]


def test_untracked_is_never_staged_and_unrelated_entries_do_not_refuse():
    entries = deliver_change.parse_entries("?? a\0A  b\0")
    refused = deliver_change.refusing_entries(entries, set())
    assert [(e.path, c) for e, c in refused] == [("b", deliver_change.Cause.STAGED)]


def test_rename_source_path_counts():
    entries = deliver_change.parse_entries("R  new\0old\0")
    assert entries[0].source == "old" and entries[0].path == "new"
    entries = [deliver_change.Entry(" M", "new", "old")]
    refused = deliver_change.refusing_entries(entries, {"old"})
    assert [c for _, c in refused] == [deliver_change.Cause.COLLISION]


@pytest.mark.parametrize("entry,written,collides", [
    ("a", "ab", False), ("a", "a/b", True), ("a/b", "a", True), ("a", "a", True),
])
def test_collision_is_equality_or_folder_containment(entry, written, collides):
    refused = deliver_change.refusing_entries([deliver_change.Entry("??", entry)], {written})
    assert bool(refused) == collides


@pytest.mark.parametrize("role", ["product", "instance"])
def test_delivery_rejects_branch_already_contained_in_main(tmp_path, role):
    s = Scenario(tmp_path, True)
    git(s.repos[role], "merge", "--no-ff", KEY, "-m", "already delivered")
    before = {name: snapshot(repo) for name, repo in s.repos.items()}
    halt(s.call(), "deliver-precondition-failed")
    assert not s.merges_called() and not any("seal" in e for e in s.log())
    for name, repo in s.repos.items():
        assert snapshot(repo) == before[name]
        assert s.worktrees[name].is_dir()


def empty_product(s, *, main_moves_on=False):
    """Replace the product change branch with one that holds only its creation."""
    repo, worktree = s.repos["product"], s.worktrees["product"]
    git(repo, "worktree", "remove", "--force", str(worktree))
    git(repo, "branch", "-D", KEY)
    if main_moves_on:
        commit(repo, "later", "later\n")
    git(repo, "worktree", "add", "-qb", KEY, str(worktree), "main")
    s.tips["product"] = git(repo, "rev-parse", "main").stdout.strip()


EMPTY_BLOCK = "delivery: complete\ndelivered: instance\nempty: product\ncleanup: complete\n"


def assert_empty_product_delivered(s, result):
    assert result.returncode == 0, result.stderr
    assert result.stdout == EMPTY_BLOCK
    assert git(s.repos["product"], "rev-parse", "main").stdout.strip() == s.tips["product"]
    s.assert_cleaned("product")
    s.assert_cleaned("instance")
    parents = git(s.repos["instance"], "show", "-s", "--format=%P", "main").stdout.split()
    seal_sha = next(e["seal"] for e in s.log() if "seal" in e)
    assert parents == [s.tips["instance"], seal_sha]
    assert [Path(e["argv"][1]).name.split()[0] for e in s.merges_called()] == ["instance"]
    assert not any(e["argv"][1] == str(s.repos["product"]) for e in s.log() if "seal" not in e)


def test_empty_product_branch_delivers_instance_only(tmp_path):
    s = Scenario(tmp_path, True)
    empty_product(s)
    assert_empty_product_delivered(s, s.call())


def test_empty_product_branch_is_removed_before_the_seal(tmp_path):
    """change_text: with an empty product change branch, fixed delivery runs product cleanup →
    seal → instance merge → instance cleanup."""
    s = Scenario(tmp_path, True)
    empty_product(s)
    product, repo = str(s.worktrees["product"]), str(s.repos["product"])
    s.set_seal(before=f"assert not Path({product!r}).exists()\n"
               f"assert {product!r} not in subprocess.check_output(['git', '-C', {repo!r}, "
               "'worktree', 'list', '--porcelain'], text=True)\n"
               f"assert subprocess.run(['git', '-C', {repo!r}, 'show-ref', '--verify', "
               f"'refs/heads/{KEY}'], capture_output=True).returncode != 0")
    assert_empty_product_delivered(s, s.call())


def test_empty_product_bump_applies_to_no_merge(tmp_path):
    """Gap 3: a `bump` the empty product's merges record carries applies to no merge."""
    s = Scenario(tmp_path, True)
    empty_product(s)
    s.merges["product"]["bump"] = ["version.py=minor"]
    assert_empty_product_delivered(s, s.call())
    assert git(s.repos["product"], "show", "main:version.py").stdout == '__version__ = "1.0.0"\n'


@pytest.mark.parametrize("fault", ["missing", "wrong-type"])
def test_empty_product_merge_record_is_still_validated(tmp_path, fault):
    """Gap 3: the empty product's merges record is still required and validated as today."""
    s = Scenario(tmp_path, True)
    empty_product(s)
    if fault == "missing":
        del s.merges["product"]
    else:
        s.merges["product"]["bump"] = [42]
    refused_unchanged(s, "merge entries must match delivery roles exactly" if fault == "missing"
                      else "product merge bump has the wrong type")


def test_empty_product_branch_is_empty_after_main_moves_on(tmp_path):
    s = Scenario(tmp_path, True)
    empty_product(s, main_moves_on=True)
    assert_empty_product_delivered(s, s.call())


def refused_unchanged(s, cause):
    """CP-579: refused before any effect — no repository, worktree or branch changed."""
    before = {name: snapshot(repo) for name, repo in s.repos.items()}
    result = s.call()
    halt(result, "deliver-precondition-failed")
    assert cause in result.stderr
    assert not s.merges_called() and not any("seal" in e for e in s.log())
    for name, repo in s.repos.items():
        assert git(repo, "rev-parse", "main").stdout.strip() == s.tips[name]
        assert snapshot(repo) == before[name]
        assert s.worktrees[name].is_dir()


def test_product_branch_fast_forwarded_by_hand_refuses(tmp_path):
    s = Scenario(tmp_path, True)
    git(s.repos["product"], "merge", "--ff-only", KEY)
    s.tips["product"] = git(s.repos["product"], "rev-parse", "main").stdout.strip()
    refused_unchanged(s, "product change branch is already contained in main")


def test_contained_product_branch_without_reflog_refuses(tmp_path):
    s = Scenario(tmp_path, True)
    empty_product(s)
    git(s.repos["product"], "reflog", "expire", "--expire=now", "--all")
    assert git(s.repos["product"], "reflog", "show", f"refs/heads/{KEY}").stdout == ""
    refused_unchanged(s, "product change branch is already contained in main")


def test_product_branch_reset_to_its_creation_refuses(tmp_path):
    s = Scenario(tmp_path, True)
    empty_product(s)
    worktree = s.worktrees["product"]
    commit(worktree, "extra", "extra\n")
    git(worktree, "reset", "--hard", "-q", "main")
    refused_unchanged(s, "product change branch is already contained in main")


def test_product_branch_whose_only_entry_is_not_its_creation_refuses(tmp_path):
    """CP-576/CP-579: one reflog entry at the tip is not enough — it must record the creation."""
    s = Scenario(tmp_path, True)
    repo, worktree = s.repos["product"], s.worktrees["product"]
    git(repo, "worktree", "remove", "--force", str(worktree))
    git(repo, "branch", "-D", KEY)
    git(repo, "update-ref", "-m", "set by hand", f"refs/heads/{KEY}", "main")
    git(repo, "worktree", "add", "-q", str(worktree), KEY)
    s.tips["product"] = git(repo, "rev-parse", "main").stdout.strip()
    entries = git(repo, "reflog", "show", "--format=%H %gs", f"refs/heads/{KEY}").stdout
    assert entries.splitlines() == [f"{s.tips['product']} set by hand"]
    refused_unchanged(s, "product change branch is already contained in main")


def test_product_branch_whose_creation_names_another_commit_refuses(tmp_path):
    s = Scenario(tmp_path, True)
    empty_product(s)
    repo = s.repos["product"]
    git(repo, "update-ref", f"refs/heads/{KEY}", git(repo, "rev-parse", "main~1").stdout.strip())
    log = Path(git(repo, "rev-parse", "--git-common-dir").stdout.strip()) / "logs/refs/heads" / KEY
    log = log if log.is_absolute() else repo / log
    log.write_text(log.read_text().splitlines(keepends=True)[0])
    assert len(git(repo, "reflog", "show", f"refs/heads/{KEY}").stdout.splitlines()) == 1
    git(s.worktrees["product"], "reset", "--hard", "-q", KEY)
    refused_unchanged(s, "product change branch is already contained in main")


@pytest.mark.parametrize("dirt", ["tracked", "staged", "untracked"])
def test_empty_product_branch_with_uncommitted_work_refuses(tmp_path, dirt):
    s = Scenario(tmp_path, True)
    empty_product(s)
    worktree = s.worktrees["product"]
    if dirt == "untracked":
        (worktree / "new").write_text("x\n")
    else:
        (worktree / "shared").write_text("edit\n")
        if dirt == "staged":
            git(worktree, "add", "shared")
    refused_unchanged(s, "product dirty checkout")


@pytest.mark.parametrize("fixed", [False, True])
def test_empty_instance_branch_still_refuses(tmp_path, fixed):
    s = Scenario(tmp_path, fixed)
    repo, worktree = s.repos["instance"], s.worktrees["instance"]
    git(repo, "worktree", "remove", "--force", str(worktree))
    git(repo, "branch", "-D", KEY)
    git(repo, "worktree", "add", "-qb", KEY, str(worktree), "main")
    refused_unchanged(s, "instance change branch is already contained in main")


def test_halt_after_empty_product_keeps_todays_halt_block(tmp_path):
    s = Scenario(tmp_path, True)
    empty_product(s)
    s.hook("instance", "pre-merge-commit", '[ "$(git branch --show-current)" = "main" ] '
           "&& exit 23; exit 0")
    result = s.call()
    halt(result, "merge-hook-failed")
    assert "empty:" not in result.stdout and "instance-merge-after-product" not in result.stdout
    s.assert_cleaned("product")
    s.assert_recovery("instance")


def test_empty_product_teardown_failure_stops_before_seal(tmp_path):
    s = Scenario(tmp_path, True)
    empty_product(s)
    git(s.repos["product"], "worktree", "lock", str(s.worktrees["product"]))
    result = s.call()
    halt(result, "teardown-failed")
    for item in ("disk", "registration", "branch"):
        assert item in result.stderr
    assert not any("seal" in e for e in s.log()) and not s.merges_called()
    s.assert_recovery("instance")
    assert s.worktrees["product"].exists()


@pytest.mark.parametrize("fixed", [False, True])
@pytest.mark.parametrize("fault", ["nonzero", "no-commit", "launch", "branch", "rewrite", "edits",
                                   "merge"])
def test_seal_failure_preserves_recovery_state(tmp_path, fixed, fault):
    s = Scenario(tmp_path, fixed)
    if fault == "nonzero": s.set_seal(after="sys.exit(1)")
    elif fault == "no-commit": s.set_seal(before="sys.exit(0)")
    elif fault == "launch":
        executable = tmp_path / "disappearing-executable"
        executable.write_text("#!/bin/sh\nexit 0\n")
        executable.chmod(0o755)
        s.seal = {"argv": [str(executable)]}
        content = s.wrapper.read_text()
        s.wrapper.write_text(content.replace("sys.exit(r.returncode)",
            f"Path({str(executable)!r}).unlink(missing_ok=True)\nsys.exit(r.returncode)"))
    elif fault == "branch": s.set_seal(after="run('checkout', '-qb', 'wrong')")
    elif fault == "rewrite":
        old = s.tips["instance"]
        s.set_seal(before=f"run('checkout', '--orphan', 'replacement')\n"
                   "run('add', '.')\nrun('commit', '-qm', 'replacement')\n"
                   f"run('branch', '-D', {KEY!r})\nrun('branch', '-m', {KEY!r})")
    elif fault == "edits": s.set_seal(after="Path('uncommitted').write_text('keep')")
    else:
        s.set_seal(after="Path(run('rev-parse', '--git-path', 'MERGE_HEAD')).write_text("
                   "run('rev-parse', 'main') + '\\n')")
    result = s.call()
    halt(result, "instance-merge-after-product" if fixed else "delivery-failed",
         "product" if fixed else "none")
    assert "seal" in result.stderr
    if fault == "launch": assert "No such file" in result.stderr
    s.assert_recovery("instance")
    if fixed:
        s.assert_cleaned("product")
        product_sha = git(s.repos["product"], "rev-parse", "main").stdout.strip()
        assert product_sha in result.stderr and str(s.worktrees["instance"]) in result.stderr
    assert len(s.merges_called()) == int(fixed)


@pytest.mark.parametrize("fixed", [False, True])
@pytest.mark.parametrize("fault", ["dirt", "branch", "merge"])
def test_delivery_rechecks_instance_after_seal(tmp_path, fixed, fault):
    s = Scenario(tmp_path, fixed)
    repo = str(s.repos["instance"])
    after = f"target = Path({repo!r})\n"
    # The seal's own commit adds seal-content, so the merge writes that path; an unrelated file
    # in the primary checkout no longer refuses.
    if fault == "dirt": after += "(target / 'seal-content').write_text('keep')"
    elif fault == "branch":
        after += "subprocess.run(['git', '-C', str(target), 'checkout', 'unrelated'], check=True)"
    else:
        after += "p = subprocess.check_output(['git', '-C', str(target), 'rev-parse', "
        after += "'--git-path', 'MERGE_HEAD'], text=True).strip()\n"
        after += f"(target / p).write_text({s.tips['instance']!r} + '\\n')"
    s.set_seal(after=after)
    halt(s.call(), "instance-merge-after-product" if fixed else "deliver-precondition-failed",
         "product" if fixed else "none")
    assert not any(e["argv"][1] == repo for e in s.merges_called())
    assert s.worktrees["instance"].exists()


@pytest.mark.parametrize("product", [False, True])
@pytest.mark.parametrize("bump", [False, True])
def test_real_conflict_retains_unmerged_state(tmp_path, product, bump):
    s = Scenario(tmp_path, product)
    role = "product" if product else "instance"
    commit(s.repos[role], "shared", "target conflict\n")
    s.tips[role] = git(s.repos[role], "rev-parse", "main").stdout.strip()
    if bump: s.merges[role]["bump"] = ["version.py=minor"]
    result = s.call()
    halt(result, "merge-conflict")
    s.assert_recovery(role)
    assert git(s.repos[role], "ls-files", "-u").stdout
    assert git(s.repos[role], "rev-parse", "MERGE_HEAD").returncode == 0
    assert "MERGE_HEAD=present" in result.stderr
    assert len(s.merges_called()) == 1
    if product: assert not any("seal" in e for e in s.log())
    assert '"1.0.0"' in (s.repos[role] / "version.py").read_text()


@pytest.mark.parametrize("hook,body,bump", [
    ("commit-msg", "echo rejected >&2; exit 23", False),
    ("commit-msg", "exit 23", False), ("pre-commit", "exit 23", True),
    ("pre-merge-commit", "exit 23", False),
    ("prepare-commit-msg", "exit 23", False),
    ("prepare-commit-msg", "exit 23", True),
])
def test_blocking_hook_rejection_is_observed(tmp_path, hook, body, bump):
    s = Scenario(tmp_path)
    # Seal commits share hook configuration; reject only at the target main checkout.
    s.hook("instance", hook, '[ "$(git branch --show-current)" = "main" ] || exit 0\n' + body)
    if bump: s.merges["instance"]["bump"] = ["version.py=minor"]
    result = s.call()
    halt(result, "merge-hook-failed")
    assert hook in result.stderr and "MERGE_HEAD=present" in result.stderr
    s.assert_recovery("instance")
    assert len(s.merges_called()) == 1


@pytest.mark.parametrize("nested", [False, True])
def test_ignored_hook_failure_does_not_reject_landed_merge(tmp_path, nested):
    s = Scenario(tmp_path)
    if nested:
        hooks = tmp_path / "nested-hooks"
        hooks.mkdir()
        reject = hooks / "commit-msg"
        reject.write_text("#!/bin/sh\nexit 17\n")
        reject.chmod(0o755)
        s.hook("instance", "commit-msg", f"git -c core.hooksPath='{hooks}' commit "
               "--allow-empty -m nested >/dev/null 2>&1; exit 0")
    else: s.hook("instance", "post-merge", "exit 23")
    assert_success(s, s.call())


@pytest.mark.parametrize("hook", [False, True])
def test_instance_failure_after_product_retains_partial_delivery(tmp_path, hook):
    s = Scenario(tmp_path, True)
    if hook:
        s.hook("instance", "commit-msg", '[ "$(git branch --show-current)" = "main" ] '
               '&& exit 19; exit 0')
    else:
        commit(s.repos["instance"], "shared", "target conflict\n")
        s.tips["instance"] = git(s.repos["instance"], "rev-parse", "main").stdout.strip()
    result = s.call()
    halt(result, "instance-merge-after-product", "product")
    s.assert_recovery("instance")
    s.assert_cleaned("product")
    product_sha = git(s.repos["product"], "rev-parse", "main").stdout.strip()
    assert product_sha in result.stderr and str(s.worktrees["instance"]) in result.stderr
    assert ("merge-hook-failed" if hook else "merge-conflict") in result.stderr
    assert len(s.merges_called()) == 2
    assert git(s.repos["instance"], "rev-parse", "MERGE_HEAD").returncode == 0


def test_locked_instance_teardown_reports_all_survivors(tmp_path):
    s = Scenario(tmp_path, True)
    s.set_seal(after=f"run('worktree', 'lock', {str(s.worktrees['instance'])!r})")
    result = s.call()
    halt(result, "teardown-failed", "product,instance")
    for item in ("disk", "registration", "branch"): assert item in result.stderr
    assert s.worktrees["instance"].exists()
    s.assert_cleaned("product")
    assert git(s.repos["instance"], "show", "main:seal-content").returncode == 0


def test_product_teardown_failure_stops_before_seal(tmp_path):
    s = Scenario(tmp_path, True)
    git(s.repos["product"], "worktree", "lock", str(s.worktrees["product"]))
    halt(s.call(), "teardown-failed", "product")
    assert not any("seal" in e for e in s.log()) and len(s.merges_called()) == 1
    s.assert_recovery("instance")
    assert s.worktrees["product"].exists()


@pytest.mark.parametrize("content", ["tracked", "untracked"])
def test_cleanup_preserves_uncommitted_content(tmp_path, content):
    s = Scenario(tmp_path, True)
    wt = s.worktrees["product"]
    unrelated = tmp_path / "unrelated-worktree"
    git(s.repos["product"], "worktree", "add", str(unrelated), "unrelated")
    filename = "shared" if content == "tracked" else "keep"
    # A hook creates contents only after the merge has landed, before teardown.
    s.hook("product", "post-merge", f"printf keep > '{wt / filename}'")
    result = s.call()
    halt(result, "teardown-failed", "product")
    assert (wt / filename).read_text() == "keep"
    assert not any("seal" in e for e in s.log())
    assert git(s.repos["product"], "rev-parse", "unrelated").returncode == 0
    assert unrelated.is_dir()
    assert str(unrelated) in git(s.repos["product"], "worktree", "list", "--porcelain").stdout


@pytest.mark.parametrize("fixed", [False, True])
def test_cleanup_removes_ignored_content_a_suite_leaves(tmp_path, fixed):
    s = Scenario(tmp_path, fixed)
    for role, repo in s.repos.items():
        exclude = Path(git(repo, "rev-parse", "--git-path", "info/exclude").stdout.strip())
        exclude = exclude if exclude.is_absolute() else repo / exclude
        exclude.parent.mkdir(parents=True, exist_ok=True)
        exclude.write_text("__pycache__/\n.pytest_cache/\n")
        for cache in ("__pycache__/tool.cpython.pyc", ".pytest_cache/v/lastfailed"):
            path = s.worktrees[role] / cache
            path.parent.mkdir(parents=True)
            path.write_text("cache")
    assert_success(s, s.call())


def test_delivery_leaves_input_files_unchanged(tmp_path):
    s = Scenario(tmp_path)
    paths = s.write_inputs()
    before = [p.read_bytes() for p in paths]
    assert_success(s, s.call(paths=paths))
    assert [p.read_bytes() for p in paths] == before


@pytest.mark.parametrize("bad", [False, True])
def test_delivery_prints_exactly_one_result(tmp_path, bad):
    s = Scenario(tmp_path)
    if bad: s.seal["argv"] = [sys.executable, "-c", "print('child output'); raise SystemExit(1)"]
    result = s.call()
    if bad:
        halt(result, "delivery-failed")
        assert "child output" in result.stderr
    else: assert_success(s, result)
    assert result.stdout.count("delivery:") == 1 and "pending-seal" not in result.stdout


def test_delivery_diagnostics_identify_operation_and_state(tmp_path):
    s = Scenario(tmp_path, True)
    s.set_seal(before="raise SystemExit(9)")
    result = s.call()
    halt(result, "instance-merge-after-product", "product")
    for text in ("instance", "seal", "9", str(s.worktrees["instance"]),
                 git(s.repos["product"], "rev-parse", "main").stdout.strip()):
        assert text in result.stderr


def test_delivery_invocations_stay_within_scope(tmp_path):
    s = Scenario(tmp_path, True)
    assert_success(s, s.call())
    for e in s.log():
        if "seal" not in e:
            assert e["argv"][2] == "merge"
            assert "--target-branch" in e["argv"]
            assert e["argv"][e["argv"].index("--target-branch") + 1] == "main"
    assert len(s.merges_called()) == 2


# Fault seams preserve real repositories and real merges unless the test explicitly proves
# that a false-success process cannot authorize deletion.
def engine(s, *, fault="", role="instance", files_fault=""):
    import deliver_change as delivery

    class FaultProcesses(delivery.Processes):
        def __init__(self, *, environ):
            super().__init__(environ=environ)
            self.deletions = []

        def builder(self, builder, repo, key, metadata, *, check_only, trace=None):
            if not check_only and repo == s.repos[role]:
                if fault == "launch": raise OSError("injected process launch failure")
                if fault == "refusal":
                    return subprocess.CompletedProcess([], 1, "", "commit_builder: unknown actor")
                if fault == "non-refusal":
                    return subprocess.CompletedProcess([], 13, "", "process failed")
                if fault == "false-success": return subprocess.CompletedProcess([], 0, "", "")
            result = super().builder(
                builder, repo, key, metadata, check_only=check_only, trace=trace,
            )
            if not check_only and repo == s.repos[role]:
                if fault == "decode-landed":
                    raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid child output")
                if fault == "nonzero-landed":
                    return subprocess.CompletedProcess(
                        [], 13, result.stdout, "after landing failure",
                    )
                if fault == "wrong-parents":
                    tip = git(repo, "rev-parse", "main").stdout.strip()
                    tree = git(repo, "rev-parse", "main^{tree}").stdout.strip()
                    wrong = git(repo, "commit-tree", tree, "-p", tip, "-m", "wrong").stdout.strip()
                    git(repo, "update-ref", "refs/heads/main", wrong, tip)
                if fault == "missing-seal":
                    tip = git(repo, "rev-parse", "main").stdout.strip()
                    before_seal = git(s.worktrees[role], "rev-parse", "HEAD^").stdout.strip()
                    tree = git(repo, "rev-parse", "main^{tree}").stdout.strip()
                    without = git(repo, "commit-tree", tree, "-p", s.tips[role], "-p",
                                  before_seal, "-m", "without seal").stdout.strip()
                    git(repo, "update-ref", "refs/heads/main", without, tip)
                if fault == "unfinished":
                    merge_file = git(repo, "rev-parse", "--git-path", "MERGE_HEAD").stdout.strip()
                    (repo / merge_file).write_text(s.tips[role] + "\n")
            return result

        def remove_worktree(self, repo, worktree):
            if fault == "remove-success" and repo == s.repos[role]:
                return subprocess.CompletedProcess([], 0, "", "")
            return super().remove_worktree(repo, worktree)

        def delete_branch(self, repo, key):
            self.deletions.append((repo, key))
            if fault in ("delete-fail", "delete-success") and repo == s.repos[role]:
                return subprocess.CompletedProcess(
                    [], 1 if fault == "delete-fail" else 0, "", "ref kept",
                )
            return super().delete_branch(repo, key)

        def registrations(self, repo):
            entries = super().registrations(repo)
            if fault == "registration-survives" and not s.worktrees[role].exists():
                return [*entries, s.worktrees[role]]
            if fault == "evidence" and not s.worktrees[role].exists():
                raise OSError("cleanup evidence unreadable")
            return entries

    class FaultFiles(delivery.Files):
        def __init__(self):
            self.traces = []
            self.reads = 0

        def new_trace(self):
            path = super().new_trace()
            assert path.stat().st_mode & 0o777 == 0o600
            self.traces.append(path)
            return path

        def read_trace(self, path):
            self.reads += 1
            if files_fault == "trace-preflight": raise OSError("trace unavailable")
            # Preflight once; then product merge, then instance merge.
            if (files_fault == "trace-merge" and self.reads > 1) or (
                    files_fault == "trace-instance" and self.reads == 3):
                raise OSError("merge evidence unreadable")
            return super().read_trace(path)

        def exists(self, path):
            if files_fault == "disk-survives" and path == s.worktrees[role]: return True
            return super().exists(path)

    files = FaultFiles()
    return delivery.Delivery(files=files, processes=FaultProcesses(environ=dict(os.environ)),
                             builder=BUILDER), files


def assert_engine_halt(result, code, roles=()):
    assert result.state.value == "halt"
    assert result.code.value == code
    assert tuple(r.value for r in result.delivered) == roles
    assert result.diagnostics


@pytest.mark.parametrize("fault", ["launch", "non-refusal", "refusal"])
def test_unclassified_operational_failure_is_delivery_failed(tmp_path, fault):
    s = Scenario(tmp_path)
    e, _ = engine(s, fault=fault)
    result = e.deliver(s.contract, s.merges, s.seal)
    assert_engine_halt(result, "deliver-precondition-failed" if fault == "refusal"
                       else "delivery-failed")
    s.assert_recovery("instance")


@pytest.mark.parametrize("fault", ["false-success", "wrong-parents", "missing-seal", "unfinished"])
def test_merge_landing_requires_git_evidence(tmp_path, fault):
    s = Scenario(tmp_path)
    e, _ = engine(s, fault=fault)
    result = e.deliver(s.contract, s.merges, s.seal)
    assert_engine_halt(result, "delivery-failed")
    assert s.worktrees["instance"].exists()
    assert git(s.repos["instance"], "rev-parse", KEY).returncode == 0


@pytest.mark.parametrize("fault", ["nonzero-landed", "decode-landed"])
def test_nonzero_process_result_still_accounts_for_observed_landing(tmp_path, fault):
    s = Scenario(tmp_path)
    e, _ = engine(s, fault=fault)
    result = e.deliver(s.contract, s.merges, s.seal)
    assert_engine_halt(result, "delivery-failed", ("instance",))
    assert s.worktrees["instance"].exists()
    assert git(s.repos["instance"], "show", "main:seal-content").returncode == 0


@pytest.mark.parametrize("fault", ["launch", "refusal", "trace", "trace-instance"])
def test_partial_result_covers_later_precondition_and_operational_failure(tmp_path, fault):
    s = Scenario(tmp_path, True)
    e, _ = engine(s, fault="false-success" if fault == "trace-instance" else (
        "" if fault == "trace" else fault), files_fault=(
        "trace-merge" if fault == "trace" else
        "trace-instance" if fault == "trace-instance" else ""))
    result = e.deliver(s.contract, s.merges, s.seal)
    # For unreadable product trace, product landing is still accounted for, before cleanup.
    assert_engine_halt(result, "instance-merge-after-product", ("product",))
    s.assert_recovery("instance")
    assert git(s.repos["product"], "rev-parse", "main").stdout.strip() != s.tips["product"]


def test_failed_branch_deletion_reports_surviving_ref(tmp_path):
    s = Scenario(tmp_path)
    e, _ = engine(s, fault="delete-fail")
    result = e.deliver(s.contract, s.merges, s.seal)
    assert_engine_halt(result, "teardown-failed", ("instance",))
    assert not s.worktrees["instance"].exists()
    assert git(s.repos["instance"], "rev-parse", KEY).returncode == 0
    assert "branch" in "\n".join(result.diagnostics)


@pytest.mark.parametrize("fault", ["remove-success", "delete-success", "registration-survives",
                                   "evidence", "disk-survives"])
def test_cleanup_verifies_observations_after_successful_command(tmp_path, fault):
    s = Scenario(tmp_path)
    e, _ = engine(s, fault="" if fault == "disk-survives" else fault,
                  files_fault=fault if fault == "disk-survives" else "")
    result = e.deliver(s.contract, s.merges, s.seal)
    assert_engine_halt(result, "teardown-failed", ("instance",))
    if fault in ("remove-success", "registration-survives", "disk-survives"):
        assert not e.processes.deletions


@pytest.mark.parametrize("fault", ["", "trace-preflight", "trace-merge"])
def test_trace_files_are_private_and_disposed(tmp_path, fault):
    s = Scenario(tmp_path)
    e, files = engine(s, files_fault=fault)
    result = e.deliver(s.contract, s.merges, s.seal)
    assert files.traces and len(set(files.traces)) == len(files.traces)
    assert all(not p.exists() for p in files.traces)
    if fault:
        assert_engine_halt(result, "deliver-precondition-failed" if fault == "trace-preflight"
                           else "delivery-failed", () if fault == "trace-preflight"
                           else ("instance",))
    else: assert result.state.value == "complete"


def test_nested_or_unrelated_trace_cannot_prove_hook_rejection():
    import deliver_change as delivery
    def hook_events(sid, command, code=7, child=0):
        return [{"event": "cmd_name", "sid": sid, "name": command},
                {"event": "child_start", "sid": sid, "child_id": child,
                 "child_class": "hook", "hook_name": "commit-msg"},
                {"event": "child_exit", "sid": sid, "child_id": child, "code": code}]
    assert delivery.blocking_hook(hook_events("root/nested", "commit")) is None
    assert delivery.blocking_hook(hook_events("root", "status")) is None
    assert delivery.blocking_hook(hook_events("root", "merge", code=0)) is None
    mismatched = hook_events("root", "merge")
    mismatched[-1]["sid"] = "other"
    assert delivery.blocking_hook(mismatched) is None
    mismatched_child = hook_events("root", "merge")
    mismatched_child[-1]["child_id"] = 1
    assert delivery.blocking_hook(mismatched_child) is None
    nonblocking = hook_events("root", "merge")
    nonblocking[1]["hook_name"] = "post-merge"
    assert delivery.blocking_hook(nonblocking) is None
    assert delivery.blocking_hook(hook_events("root", "merge")) == "commit-msg"


@pytest.mark.parametrize("input_index", [0, 1, 2])
def test_delivery_refuses_input_files_inside_teardown_worktree(tmp_path, input_index):
    s = Scenario(tmp_path)
    paths = s.write_inputs()
    original = paths[input_index]
    protected = s.worktrees["instance"] / original.name
    commit(s.worktrees["instance"], original.name, original.read_text())
    paths[input_index] = protected
    before = protected.read_bytes()
    result = s.call(paths=paths)
    halt(result, "deliver-precondition-failed")
    assert protected.read_bytes() == before
    assert not s.merges_called() and not any("seal" in e for e in s.log())
    s.assert_recovery("instance")


def test_delivery_refuses_builder_removed_before_instance_delivery(tmp_path):
    s = Scenario(tmp_path, True)
    builder = s.worktrees["product"] / "record.py"
    commit(s.worktrees["product"], builder.name, s.wrapper.read_text())
    halt(s.call(builder=builder), "deliver-precondition-failed")
    for role in s.repos: s.assert_recovery(role)
    assert not s.merges_called()


@pytest.mark.parametrize("guard", ["root", "owner", "registration", "branch", "merge", "clean"])
def test_live_state_rules_are_independently_required(tmp_path, guard):
    import deliver_change as delivery
    s = Scenario(tmp_path)

    class Observations(delivery.Processes):
        def toplevel(self, path):
            return "wrong" if guard == "root" else super().toplevel(path)

        def main_worktree(self, path):
            return "wrong" if guard == "owner" else super().main_worktree(path)

        def registrations(self, repo):
            return [] if guard == "registration" else super().registrations(repo)

        def branch(self, path):
            return "wrong" if guard == "branch" else super().branch(path)

        def merge_head(self, repo):
            return True if guard == "merge" else super().merge_head(repo)

        def git(self, repo, *args, trace=None):
            if guard == "clean" and args[0] == "status": return "?? keep"
            return super().git(repo, *args, trace=trace)

    e = delivery.Delivery(files=delivery.Files(), processes=Observations(environ=dict(os.environ)),
                          builder=BUILDER)
    with pytest.raises(delivery.DeliveryError):
        e._live(s.contract, delivery.Role.INSTANCE)
    s.assert_recovery("instance")


@pytest.mark.parametrize("text", ["{", "[]\n[]", '{"event":"child_exit","sid":[]}',
                                  '{"event":"child_exit","child_id":[]}'])
def test_trace_reader_rejects_malformed_event_records(tmp_path, text):
    import deliver_change as delivery
    path = tmp_path / "trace"
    path.write_text(text)
    with pytest.raises(ValueError):
        delivery.Files().read_trace(path)


@pytest.mark.parametrize("guard", ["roles", "record", "fields", "no-identity", "two-identities",
                                  "value-type", "seal-fields", "seal-empty", "seal-type"])
def test_input_schema_rules_are_independently_required(tmp_path, guard):
    import deliver_change as delivery
    contract = {"delivery_repos": ["instance"]}
    merges = {"instance": {"description": "example", "merge_context": "example",
                           "surface": "Codex", "actor": "pm"}}
    seal = {"argv": ["python3"]}
    if guard == "roles": merges["product"] = merges["instance"]
    elif guard == "record": merges["instance"] = None
    elif guard == "fields": del merges["instance"]["surface"]
    elif guard == "no-identity": del merges["instance"]["actor"]
    elif guard == "two-identities": merges["instance"]["authorizer"] = "Product"
    elif guard == "value-type": merges["instance"]["bump"] = [42]
    elif guard == "seal-fields": seal["shell"] = True
    elif guard == "seal-empty": seal["argv"] = []
    elif guard == "seal-type": seal["argv"] = "python3"
    e = delivery.Delivery(files=delivery.Files(), processes=delivery.Processes(environ={}),
                          builder=tmp_path / "builder")
    with pytest.raises(delivery.DeliveryError):
        e._inputs(contract, merges, seal)


@pytest.mark.parametrize("operation", ["remove", "delete"])
def test_teardown_nonzero_after_effect_cannot_report_complete(tmp_path, operation):
    import deliver_change as delivery
    s = Scenario(tmp_path)

    class NonzeroAfterEffect(delivery.Processes):
        def remove_worktree(self, repo, worktree):
            result = super().remove_worktree(repo, worktree)
            assert result.returncode == 0
            return subprocess.CompletedProcess([], 1, "", "removal reported failure") \
                if operation == "remove" else result

        def delete_branch(self, repo, key):
            result = super().delete_branch(repo, key)
            assert result.returncode == 0
            return subprocess.CompletedProcess([], 1, "", "deletion reported failure")

    e = delivery.Delivery(files=delivery.Files(),
                          processes=NonzeroAfterEffect(environ=dict(os.environ)), builder=BUILDER)
    result = e.deliver(s.contract, s.merges, s.seal)
    assert_engine_halt(result, "teardown-failed", ("instance",))
    assert not s.worktrees["instance"].exists()
    present = git(s.repos["instance"], "show-ref", "--verify", "--quiet", f"refs/heads/{KEY}") \
        if operation == "remove" else None
    if present is None:
        assert git(s.repos["instance"], "show-ref", "--verify", "--quiet", f"refs/heads/{KEY}",
                   check=False).returncode == 1
    diagnostic = "worktree remove exited 1" if operation == "remove" else "branch deletion exited 1"
    assert diagnostic in "\n".join(result.diagnostics)
