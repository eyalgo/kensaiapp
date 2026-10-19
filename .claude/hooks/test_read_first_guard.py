"""Tests for `read_first_guard.py` — the `PreToolUse` hook that refuses an agent run's acting calls
until it has read the files its agent file lists.

Runs the real entry point — JSON on stdin, JSON or silence on stdout — exactly as Claude Code does
with it, following `test_brief_anchor_guard.py`'s shape.

Each test fabricates a small instance (an `AGENTS.md` with a loader map, a `.env` naming the core,
and the files an agent file lists). Every case sets `TMPDIR` to a directory outside that instance,
because the hook keeps its per-session record of reads under the platform temp directory.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_GUARD = Path(__file__).resolve().parent / "read_first_guard.py"
_HOST = Path(__file__).resolve().parents[2]

_READ_INSTRUCTION = "Before doing anything else, Read these in full, in order:"

# The refusal as `change_text.md` publishes it, every character inside the fence.
_REFUSAL = (
    "This `{tool}` call is refused.\n"
    "`{agent_file}` tells a `{agent}` run to read the files listed below before it acts. "
    "No `Read` call in this session has named them:\n"
    "\n"
    "{owed}\n"
    "\n"
    "Read each file above with the `Read` tool, then make this call again. "
    "A `Read` with `offset` or `limit` counts. A `Grep` or `Glob` of a file does not count.\n"
    "This check never refuses `Read`, `Grep` or `Glob`. "
    "It refuses every other call until each file above has been read in this session. "
    "After that, it refuses no call in this session."
)


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("a file a run must read\n")
    return path


def _real_loader_rows() -> list[str]:
    """The loader-map rows of this host's `AGENTS.md`: the fixture copies them, so a row the real
    file lacks (there is none for `qa`) is lacking in the fixture too."""
    rows, in_map = [], False
    for line in (_HOST / "AGENTS.md").read_text().splitlines():
        if line.startswith("## "):
            in_map = line[3:].strip() == "Loader map"
        elif in_map and line.startswith("- `"):
            rows.append(line)
    return rows


class _Instance:
    """A directory shaped like an instance, and the paths a standard agent owes in it."""

    def __init__(self, tmp_path: Path, *, agent: str = "scrum-master", core_name: str = "core",
                 overlay_row: str | None = None, overlay_exists: bool = True,
                 cross_role: bool = True) -> None:
        stem = agent.replace("-", "_")
        self.agent = agent
        self.root = tmp_path / "instance"
        self.core = self.root / core_name if core_name == "core" else tmp_path / core_name
        self.tmpdir = tmp_path / "tmpdir"
        self.tmpdir.mkdir()
        self.root.mkdir()
        (self.root / ".env").write_text(f"CORE={self.core}\n")

        rows = [row for row in _real_loader_rows() if not row.startswith(f"- `{agent}:`")]
        mapped = overlay_row or f"system/loaders/{stem}.md"
        if agent != "qa":
            rows.append(f"- `{agent}:` → {mapped}")
        (self.root / "AGENTS.md").write_text(
            "# routing\n\n## Loader map\n\n" + "\n".join(rows) + "\n\n## Doctrine\n\n- `x.md`\n"
        )

        self.global_loader = _touch(self.core / "roles" / "loaders" / f"{stem}_global.md")
        self.overlay = self.root / mapped
        if overlay_exists:
            _touch(self.overlay)
        self.core_cross = _touch(self.core / "roles" / "CROSS_ROLE.md")
        self.root_cross = self.root / "system" / "CROSS_ROLE.md"
        if cross_role:
            _touch(self.root_cross)

    def standard_owed(self) -> list[str]:
        """What a standard agent owes, in the order its file lists it."""
        owed = (self.global_loader, self.overlay, self.core_cross, self.root_cross)
        return [str(path) for path in owed]

    def agent_file(self) -> str:
        return str(_HOST / "skills" / self.agent / ".claude" / "agents" / f"{self.agent}.md")

    def write_agent(self, name: str, body: str) -> Path:
        """An agent file of the instance's own, which `_agent_file` reads before the host's."""
        path = self.root / ".claude" / "agents" / f"{name}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\nname: {name}\n---\n\n{body}\n")
        return path


def _call(tool: str, *, agent: str | None = "scrum-master", session: str | None = "s1",
          **tool_input) -> dict:
    payload: dict = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input}
    if agent is not None:
        payload["agent_type"] = agent
    if session is not None:
        payload["session_id"] = session
    return payload


def _read(path: Path | str, **extra) -> dict:
    return _call("Read", file_path=str(path), **extra)


def _run(instance: _Instance, payload,
         *, tmpdir: Path | None = None) -> subprocess.CompletedProcess:
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(instance.root),
               TMPDIR=str(tmpdir or instance.tmpdir))
    return subprocess.run([sys.executable, str(_GUARD)], input=stdin, capture_output=True,
                          text=True, env=env)


def _assert_silent(result: subprocess.CompletedProcess) -> None:
    assert result.stdout == ""
    assert result.returncode == 0


def _reason(result: subprocess.CompletedProcess) -> str:
    """The refusal's message, after checking it is exactly the deny object and nothing else."""
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert set(out) == {"hookSpecificOutput"}
    body = out["hookSpecificOutput"]
    assert body["hookEventName"] == "PreToolUse"
    assert body["permissionDecision"] == "deny"
    return body["permissionDecisionReason"]


def _owed_lines(reason: str) -> list[str]:
    return [line[2:] for line in reason.splitlines() if line.startswith("  ")]


def _read_all(instance: _Instance, paths: list[str], *, session: str = "s1") -> None:
    for path in paths:
        _assert_silent(_run(instance, _read(path, agent=instance.agent, session=session)))


@pytest.fixture
def scrum(tmp_path: Path) -> _Instance:
    return _Instance(tmp_path)


# --- who owes what ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "agent, tool",
    [(None, "Bash"), ("", "Bash"), ("general-purpose", "Write")],
    ids=["no-agent-type", "empty-agent-type", "builtin-agent-without-a-file"],
)
def test_no_agent_type_is_silent(scrum, agent, tool):
    _assert_silent(_run(scrum, _call(tool, agent=agent, command="cat x")))


def test_agent_file_without_read_instruction_is_silent(scrum):
    scrum.write_agent("plain", "You are plain. Your task prompt says everything.")
    _assert_silent(_run(scrum, _call("Edit", agent="plain", file_path="/x")))


def test_overlay_the_instance_lacks_is_not_owed(tmp_path):
    instance = _Instance(tmp_path, overlay_exists=False)
    owed = _owed_lines(_reason(_run(instance, _call("Bash", command="ls"))))
    assert owed == [str(instance.global_loader), str(instance.core_cross), str(instance.root_cross)]


def test_missing_cross_role_overlay_is_not_owed(tmp_path):
    instance = _Instance(tmp_path, cross_role=False)
    owed = _owed_lines(_reason(_run(instance, _call("Bash", command="ls"))))
    assert owed == [str(instance.global_loader), str(instance.overlay), str(instance.core_cross)]


def test_core_path_is_owed_under_the_resolved_core(tmp_path):
    instance = _Instance(tmp_path, core_name="fixture-core")
    inside_the_instance = _touch(instance.root / "core" / "roles" / "CROSS_ROLE.md")
    _assert_silent(_run(instance, _read(inside_the_instance)))
    owed = _owed_lines(_reason(_run(instance, _call("Bash", command="ls"))))
    assert str(instance.core / "roles" / "CROSS_ROLE.md") in owed
    assert str(inside_the_instance) not in owed


def test_overlay_comes_from_the_loader_map_not_the_parenthetical(tmp_path):
    instance = _Instance(tmp_path, overlay_row="system/loaders/other.md")
    _touch(instance.root / "system" / "loaders" / "scrum_master.md")
    owed = _owed_lines(_reason(_run(instance, _call("Bash", command="ls"))))
    assert str(instance.root / "system" / "loaders" / "other.md") in owed
    assert str(instance.root / "system" / "loaders" / "scrum_master.md") not in owed
    assert str(instance.root / "AGENTS.md") not in owed


def test_scrum_master_refusal_names_the_owed_files_in_order(scrum):
    reason = _reason(_run(scrum, _call("Bash", command="cat system/CROSS_ROLE.md")))
    assert "`scrum-master`" in reason
    assert _owed_lines(reason) == scrum.standard_owed()


def test_refusal_is_the_published_string(scrum):
    reason = _reason(_run(scrum, _call("mcp__github__x", repo="r")))
    expected = _REFUSAL.format(
        tool="mcp__github__x",
        agent_file=scrum.agent_file(),
        agent="scrum-master",
        owed="\n".join(f"  {path}" for path in scrum.standard_owed()),
    )
    assert reason == expected


def test_refusal_lists_only_files_still_unread(scrum):
    owed = scrum.standard_owed()
    _read_all(scrum, owed[:2])
    result = _run(scrum, _call("Skill", skill="x"))
    assert _owed_lines(_reason(result)) == owed[2:]


def test_delegate_owes_its_contract_only(tmp_path):
    instance = _Instance(tmp_path, agent="delegate")
    contract = _touch(instance.core / "roles" / "delegate_contract.md")
    owed = _owed_lines(_reason(_run(instance, _call("Bash", agent="delegate", command="ls"))))
    assert owed == [str(contract)]


def test_kaizen_fix_author_owes_three_files_with_skills_once(tmp_path):
    instance = _Instance(tmp_path, agent="kaizen-fix-author")
    kaizen = instance.core / "doctrine" / "kaizen"
    expected = [
        str(_touch(kaizen / "fix_packet.md")),
        str(_touch(kaizen / "skills.md")),
        str(_touch(kaizen / "lenses" / "locate_layer.md")),
    ]
    result = _run(instance, _call("Write", agent="kaizen-fix-author", file_path="/x"))
    assert _owed_lines(_reason(result)) == expected


def test_kaizen_fixer_owes_skills_md_only(tmp_path):
    instance = _Instance(tmp_path, agent="kaizen-fixer")
    kaizen = instance.core / "doctrine" / "kaizen"
    skills = _touch(kaizen / "skills.md")
    _touch(kaizen / "fix_packet.md")
    refusal = _run(instance, _call("Bash", agent="kaizen-fixer", command="ls"))
    assert _owed_lines(_reason(refusal)) == [str(skills)]
    _assert_silent(_run(instance, _read(skills, agent="kaizen-fixer")))
    _assert_silent(_run(instance, _call("Edit", agent="kaizen-fixer", file_path="/x")))


def test_kensaiapp_auditor_owes_nothing(tmp_path):
    instance = _Instance(tmp_path, agent="kensaiapp-auditor")
    _touch(instance.core / "doctrine" / "kaizen" / "lenses" / "contract.md")
    _assert_silent(_run(instance, _call("Bash", agent="kensaiapp-auditor", command="ls")))


def test_qa_owes_global_loader_and_both_cross_role_files(tmp_path):
    instance = _Instance(tmp_path, agent="qa")
    owed = _owed_lines(_reason(_run(instance, _call("Bash", agent="qa", command="ls"))))
    assert owed == [str(instance.global_loader), str(instance.core_cross), str(instance.root_cross)]


def test_owed_file_named_twice_is_listed_once_in_agent_order(scrum):
    first, second = _touch(scrum.root / "docs" / "a.md"), _touch(scrum.root / "docs" / "b.md")
    scrum.write_agent(
        "twice",
        f"{_READ_INSTRUCTION}\n\n1. `docs/b.md` first\n2. `docs/a.md`, then `docs/b.md` again\n",
    )
    owed = _owed_lines(_reason(_run(scrum, _call("Bash", agent="twice", command="ls"))))
    assert owed == [str(second), str(first)]


# CP-456's first row, by name: every standard agent owes the same four files, its own stems.
_STANDARD_AGENTS = (
    "architect", "cdo", "content-editor", "content-manager", "cpo", "cto", "developer", "pm",
    "principal-architect", "principal-pm", "product-owner", "scrum-master", "senior-engineer",
    "tech-lead",
)


@pytest.mark.parametrize("agent", _STANDARD_AGENTS)
def test_every_standard_agent_owes_loader_overlay_and_both_cross_role_files(tmp_path, agent):
    instance = _Instance(tmp_path, agent=agent)
    owed = _owed_lines(_reason(_run(instance, _call("Bash", agent=agent, command="ls"))))
    assert owed == instance.standard_owed()


def test_instance_own_agent_file_is_read_before_the_group_file(scrum):
    own = scrum.write_agent("scrum-master", f"{_READ_INSTRUCTION}\n\n1. `system/CROSS_ROLE.md`\n")
    reason = _reason(_run(scrum, _call("Bash", command="ls")))
    assert _owed_lines(reason) == [str(scrum.root_cross)]
    assert f"`{own}` tells a `scrum-master` run" in reason


def test_item_naming_the_file_your_task_names_is_not_owed(scrum):
    contract, lens = _touch(scrum.root / "docs" / "a.md"), _touch(scrum.root / "docs" / "b.md")
    scrum.write_agent(
        "lensed",
        f"{_READ_INSTRUCTION}\n\n1. `docs/a.md`\n"
        "2. **Your lens** — the file your task names, such as `docs/b.md`.\n",
    )
    owed = _owed_lines(_reason(_run(scrum, _call("Bash", agent="lensed", command="ls"))))
    assert owed == [str(contract)]
    assert str(lens) not in owed


# --- reading and acting -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tool, tool_input",
    [("Read", {"file_path": "/etc/hosts"}), ("Grep", {"pattern": "x"}), ("Glob", {"pattern": "*"})],
)
def test_reading_calls_are_silent_while_files_unread(scrum, tool, tool_input):
    _assert_silent(_run(scrum, _call(tool, **tool_input)))


@pytest.mark.parametrize(
    "tool, tool_input",
    [("Bash", {"command": "cat system/CROSS_ROLE.md"}), ("ToolSearch", {"query": "x"}),
     ("mcp__github__x", {}), ("Edit", {"file_path": "/x"}), ("Write", {"file_path": "/x"}),
     ("Skill", {"skill": "x"}), ("Agent", {"prompt": "x"}), ("WebFetch", {"url": "https://x"}),
     ("WebSearch", {"query": "x"}), ("TodoWrite", {"todos": []})],
)
def test_acting_calls_are_refused_while_files_unread(scrum, tool, tool_input):
    reason = _reason(_run(scrum, _call(tool, **tool_input)))
    assert reason.startswith(f"This `{tool}` call is refused.\n")


def test_nothing_is_refused_once_every_owed_file_is_read(scrum):
    assert _reason(_run(scrum, _call("Bash", command="ls")))
    _read_all(scrum, scrum.standard_owed())
    for call in (_call("Bash", command="ls"), _call("Write", file_path="/x"),
                 _call("Skill", skill="x")):
        _assert_silent(_run(scrum, call))


def test_reads_in_another_session_do_not_count(scrum):
    _read_all(scrum, scrum.standard_owed(), session="s1")
    refusal = _run(scrum, _call("Bash", session="s2", command="ls"))
    assert _owed_lines(_reason(refusal)) == scrum.standard_owed()


def test_read_with_offset_and_limit_counts(scrum):
    _assert_silent(_run(scrum, _read(scrum.global_loader, offset=1, limit=40)))
    owed = _owed_lines(_reason(_run(scrum, _call("Bash", command="ls"))))
    assert owed == scrum.standard_owed()[1:]


def test_grep_and_glob_do_not_count_as_a_read(scrum):
    loader = scrum.global_loader
    _assert_silent(_run(scrum, _call("Grep", pattern="x", path=str(loader))))
    _assert_silent(_run(scrum, _call("Glob", pattern=loader.name, path=str(loader.parent))))
    owed = _owed_lines(_reason(_run(scrum, _call("Bash", command="ls"))))
    assert owed == scrum.standard_owed()


def test_read_through_symlink_or_dotdot_spelling_counts(scrum, tmp_path):
    link = tmp_path / "link.md"
    link.symlink_to(scrum.global_loader)
    dotdot = scrum.root / "system" / "loaders" / ".." / "loaders" / scrum.overlay.name
    _assert_silent(_run(scrum, _read(link)))
    _assert_silent(_run(scrum, _read(dotdot)))
    owed = _owed_lines(_reason(_run(scrum, _call("Bash", command="ls"))))
    assert owed == scrum.standard_owed()[2:]


# --- fail open ----------------------------------------------------------------------------------


def _unreadable(path: Path) -> None:
    path.chmod(0)
    if os.access(path, os.R_OK):  # running as a user the mode does not bind
        pytest.skip("cannot make a file unreadable for this user")


@pytest.mark.parametrize(
    "case",
    ["not-json", "empty-stdin", "no-session-id", "unreadable-agent-file", "unreadable-agents-md",
     "ledger-cannot-be-written"],
)
def test_malformed_input_is_silent(scrum, case):
    if case == "not-json":
        result = _run(scrum, "{not json")
    elif case == "empty-stdin":
        result = _run(scrum, "")
    elif case == "no-session-id":
        result = _run(scrum, _call("Bash", session=None, command="ls"))
    elif case == "unreadable-agent-file":
        _unreadable(scrum.write_agent("locked", f"{_READ_INSTRUCTION}\n\n1. `docs/a.md`\n"))
        result = _run(scrum, _call("Bash", agent="locked", command="ls"))
    elif case == "unreadable-agents-md":
        _unreadable(scrum.root / "AGENTS.md")
        result = _run(scrum, _call("Bash", command="ls"))
    else:
        broken = scrum.tmpdir / "broken"
        broken.mkdir()
        # The hook's own directory under the temp directory is a regular file, so nothing can be
        # recorded or looked up there: no refusal may follow, and neither may an error.
        _block_ledger(broken)
        _assert_silent(_run(scrum, _read(scrum.global_loader), tmpdir=broken))
        result = _run(scrum, _call("Bash", command="ls"), tmpdir=broken)
    _assert_silent(result)


def _block_ledger(tmpdir: Path) -> None:
    """Make the hook's ledger directory unusable: a file stands where it would go. The name is
    the hook's, imported rather than copied so the test follows it."""
    sys.path.insert(0, str(_GUARD.parent))
    try:
        import read_first_guard
    finally:
        sys.path.pop(0)
    (tmpdir / read_first_guard.LEDGER_DIRNAME).write_text("in the way\n")


def test_read_without_file_path_is_silent_and_records_nothing(scrum):
    _assert_silent(_run(scrum, _call("Read")))
    assert [p for p in scrum.tmpdir.rglob("*") if p.is_file()] == []


# --- no checkout is dirtied ---------------------------------------------------------------------


def test_hook_leaves_every_checkout_clean(scrum):
    def git(*args: str) -> str:
        done = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "user.name=t",
                               "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                               "-C", str(scrum.root), *args], capture_output=True, text=True)
        assert done.returncode == 0, done.stderr
        return done.stdout

    git("init", "-q")
    git("add", "-A")
    git("commit", "-q", "-m", "fixture")
    _assert_silent(_run(scrum, _read(scrum.global_loader)))
    assert _reason(_run(scrum, _call("Bash", command="ls")))
    _read_all(scrum, scrum.standard_owed())
    _assert_silent(_run(scrum, _call("Write", file_path="/x")))
    assert git("status", "--porcelain", "--untracked-files=all") == ""
    assert [p for p in scrum.tmpdir.rglob("*") if p.is_file()] != []
