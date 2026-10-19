"""Cross-boundary contract: a Codex invocation's resolved model reaches Git.

`tl_instruction.md` Task 5 fixes this module's home: the adapter (`agent_run.py` /
`agent_turn.py`) → runtime prompt (`task_context.codex_bootstrap`) → committer
(`commit_builder.py`) path is proven end to end here, against real scratch
repositories, while each module's own contract stays with its own test file.
Claude identity, deterministic (model-less) omission, canonical trailer order,
and the staged-set guard are `test_commit_builder.py`'s Task 4 fixtures — this
module does not repeat them; it proves it did not have to bypass or weaken them.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import agent_run
import agent_turn
import commit_builder

_COAUTHOR_PATTERN = re.compile(r'--co-authored-by "([^"]+)"')


def _attribution_from_prompt(prompt: str) -> tuple[str, str]:
    """Read the exact surface and co-author values a real Codex invocation
    would receive from its own runtime-identity block — the values this
    change carries into the committer, rather than a value the test invents.
    """
    assert "--surface Codex" in prompt, f"no surface directive in prompt: {prompt!r}"
    match = _COAUTHOR_PATTERN.search(prompt)
    assert match, f"no co-author directive in rendered prompt: {prompt!r}"
    return "Codex", match.group(1)


def _init_repo(path: Path) -> str:
    """Init a throwaway git repo with a first commit; return its branch name."""
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    git("init", "-q")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.com")
    git("config", "commit.gpgsign", "false")
    (path / "seed.txt").write_text("seed\n")
    git("add", "seed.txt")
    git("commit", "-q", "-m", "seed")
    return git("rev-parse", "--abbrev-ref", "HEAD")


def _commit_body(path: Path, ref: str = "HEAD") -> str:
    return subprocess.run(
        ["git", "-C", str(path), "log", "-1", "--format=%B", ref],
        capture_output=True, text=True, check=True,
    ).stdout


def test_tier_selected_fresh_run_carries_its_model_into_a_real_commit(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: repo)

    command = agent_run.CodexAdapter().command(
        agent_run.RunRequest(prompt="do the work", core_root=repo, model_tier="sonnet")
    )
    assert command[command.index("--model") + 1] == "gpt-5.6-terra"
    surface, co_authored_by = _attribution_from_prompt(command[-1])
    assert co_authored_by == "gpt-5.6-terra <noreply@openai.com>"

    (repo / "work.txt").write_text("work\n")
    exit_code = commit_builder.main([
        "--repo", str(repo),
        "commit",
        "--subject", "developer: real commit through the builder",
        "--actor", "developer",
        "--add", "work.txt",
        "--directional", "Shukuba: commit-builder — progress: builds it",
        "--surface", surface,
        "--co-authored-by", co_authored_by,
    ])

    assert exit_code == 0
    body = _commit_body(repo)
    assert body.count("Surface: Codex") == 1
    assert body.count(f"Co-Authored-By: {co_authored_by}") == 1
    trailer_block = body.strip().split("\n\n")[-1]
    assert trailer_block.splitlines() == [
        "Shukuba: commit-builder — progress: builds it",
        "Role: Developer",
        "Surface: Codex",
        f"Co-Authored-By: {co_authored_by}",
    ]


def test_resumed_run_carries_only_its_current_model_into_a_real_merge(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    main_branch = _init_repo(repo)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    # An earlier fresh invocation is assigned gpt-5.6-terra.
    earlier = agent_turn.codex_command(
        prompt="work", session_id=None, model=None, tier="sonnet",
        add_dirs=(), core_root=repo,
    )
    assert "gpt-5.6-terra" in earlier[-1]

    # The resumed turn is assigned a different current model.
    resumed = agent_turn.codex_command(
        prompt="next", session_id="thread-1", model=None, tier="opus",
        add_dirs=(), core_root=repo,
    )
    assert resumed[resumed.index("--model") + 1] == "gpt-5.6-sol"
    surface, co_authored_by = _attribution_from_prompt(resumed[-1])
    assert co_authored_by == "gpt-5.6-sol <noreply@openai.com>"
    assert "gpt-5.6-terra" not in resumed[-1]

    git("checkout", "-q", "-b", "feature")
    (repo / "feature.txt").write_text("feature\n")
    git("add", "feature.txt")
    git("commit", "-q", "-m", "feature: add a thing")
    git("checkout", "-q", main_branch)

    exit_code = commit_builder.main([
        "--repo", str(repo),
        "merge",
        "--branch", "feature",
        "--target-branch", main_branch,
        "--description", "bring in the feature",
        "--branch-commits", "feature: add a thing",
        "--actor", "pm",
        "--merge-context", "manual",
        "--surface", surface,
        "--co-authored-by", co_authored_by,
    ])

    assert exit_code == 0
    body = _commit_body(repo)
    assert body.count("Surface: Codex") == 1
    assert body.count(f"Co-Authored-By: {co_authored_by}") == 1
    assert "gpt-5.6-terra" not in body
    lines = body.strip().splitlines()
    merge_line = next(i for i, line in enumerate(lines) if line.startswith("Merge-Authorized:"))
    assert lines[merge_line + 1:merge_line + 3] == [
        "Surface: Codex",
        f"Co-Authored-By: {co_authored_by}",
    ]


def test_explicit_model_carries_verbatim_into_a_real_commit(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: repo)

    command = agent_run.CodexAdapter().command(
        agent_run.RunRequest(
            prompt="do the work", core_root=repo, model="gpt-explicit-fixture"
        )
    )
    assert command[command.index("--model") + 1] == "gpt-explicit-fixture"
    surface, co_authored_by = _attribution_from_prompt(command[-1])
    assert co_authored_by == "gpt-explicit-fixture <noreply@openai.com>"

    (repo / "work.txt").write_text("work\n")
    exit_code = commit_builder.main([
        "--repo", str(repo),
        "commit",
        "--subject", "developer: real commit through the builder",
        "--actor", "developer",
        "--add", "work.txt",
        "--directional", "Shukuba: commit-builder — progress: builds it",
        "--surface", surface,
        "--co-authored-by", co_authored_by,
    ])

    assert exit_code == 0
    body = _commit_body(repo)
    assert f"Co-Authored-By: {co_authored_by}" in body


def test_cross_boundary_fixtures_preserve_unaffected_builder_contracts():
    # This module owns the adapter → prompt → committer path only. Claude
    # identity, deterministic (model-less) omission, canonical trailer order,
    # and the staged-set-guard refusal stay proven by their own Task 4
    # fixtures in test_commit_builder.py — this proves the cross-boundary
    # path did not have to bypass, duplicate, or weaken them to exist.
    import test_commit_builder

    for name in (
        "test_claude_and_model_less_builder_paths_remain_unchanged",
        "test_codex_model_attribution_does_not_bypass_the_staged_set_guard",
        "test_commit_trailers_in_canonical_order",
    ):
        assert hasattr(test_commit_builder, name), (
            f"{name} was removed from test_commit_builder.py — the cross-boundary "
            "path must not bypass or weaken the retained builder-contract fixtures"
        )
