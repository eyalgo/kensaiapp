"""Contract tests for the forward-only resolved-core indirection gate."""

from __future__ import annotations

import subprocess
from pathlib import Path

import core_indirection

HOOK = Path(__file__).resolve().parents[1] / "githooks" / "pre-commit"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    baseline = repo / "AGENTS.md"
    baseline.write_text("existing literal: core/tools/old.py\n", encoding="utf-8")
    _git(repo, "add", "AGENTS.md")
    _git(repo, "commit", "-qm", "baseline")
    return repo


def _stage(repo: Path, relative: str, text: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    _git(repo, "add", relative)


def test_existing_literal_is_not_retried_on_every_commit(tmp_path):
    repo = _repo(tmp_path)
    _stage(repo, "AGENTS.md", "existing literal: core/tools/old.py\nclean addition\n")

    assert core_indirection.scan_staged(repo) == []


def test_new_literal_is_refused_with_its_new_side_line(tmp_path):
    repo = _repo(tmp_path)
    _stage(repo, "AGENTS.md", "existing literal: core/tools/old.py\nsee core/tools/new.py\n")

    assert core_indirection.scan_staged(repo) == [
        core_indirection.Hit("AGENTS.md", 2, "see core/tools/new.py")
    ]


def test_resolved_token_is_accepted(tmp_path):
    repo = _repo(tmp_path)
    _stage(repo, "AGENTS.md", "read <CORE>/tools/new.py\n")

    assert core_indirection.scan_staged(repo) == []


def test_shell_variable_named_core_is_not_a_hardcoded_path(tmp_path):
    repo = _repo(tmp_path)
    _stage(repo, "hook.sh", 'exec "$core/tools/check.py"\n')

    assert core_indirection.scan_staged(repo) == []


def test_unstaged_literal_is_not_a_commit_refusal(tmp_path):
    repo = _repo(tmp_path)
    (repo / "AGENTS.md").write_text("see core/tools/new.py\n", encoding="utf-8")

    assert core_indirection.scan_staged(repo) == []


def test_rules_tests_and_records_are_exempt(tmp_path):
    repo = _repo(tmp_path)
    for relative in (
        "core/doctrine/setup/rule.md",
        "core/tools/test_example.py",
        ".claude/skills/demo/evidence/run.md",
        "docs/code-integrity-report.md",
        ".claude/skills/demo/references/demo_ratification_verdict.md",
    ):
        _stage(repo, relative, "mentions core/tools/example.py\n")

    assert core_indirection.scan_staged(repo) == []


def test_change_request_template_keeps_its_working_command_example(tmp_path):
    repo = _repo(tmp_path)
    _stage(
        repo,
        "core/templates/change_request_template.md",
        "run core/launchers/chain-development/launcher.sh <project>\n",
    )

    assert core_indirection.scan_staged(repo) == []


def test_other_templates_still_require_resolved_core(tmp_path):
    repo = _repo(tmp_path)
    _stage(repo, "core/templates/example.md", "read core/tools/example.py\n")

    assert core_indirection.scan_staged(repo) == [
        core_indirection.Hit(
            "core/templates/example.md", 1, "read core/tools/example.py"
        )
    ]


def test_cli_refuses_and_names_the_repair(tmp_path, capsys):
    repo = _repo(tmp_path)
    _stage(repo, ".claude/agents/demo.md", "read core/roles/demo.md\n")

    assert core_indirection.main(["--repo", str(repo), "--staged"]) == 1
    error = capsys.readouterr().err
    assert ".claude/agents/demo.md:1" in error
    assert "use <CORE>" in error


def test_cli_requires_the_explicit_staged_mode(tmp_path, capsys):
    repo = _repo(tmp_path)

    assert core_indirection.main(["--repo", str(repo)]) == 2
    assert "--staged is required" in capsys.readouterr().err


def test_git_precommit_keeps_written_forward_without_core_path_enforcement():
    body = HOOK.read_text(encoding="utf-8")

    assert 'exec "$core/tools/written_forward.py" --staged --repo "$repo"' in body
    assert "core_indirection.py" not in body
