"""The development chain's suite — driven through the ports it is given, never around them.

WHY THIS FILE LOOKS LIKE THIS
    `chain_development.py` decides a pipeline step is done by what is on disk, never by a
    message a run returns — a `claude --bg` run returns none. So every test here scripts a disk
    (an in-memory tree and an in-memory git) and asserts what the engine read off it, or the
    exact ordered `argv` the injected process port received. Nothing here monkeypatches the
    module under test; `core/tools/test_chain.py` states why that is the only honest shape.
"""

from __future__ import annotations

import json
import os
import re
import tomllib
from collections.abc import Iterable
from pathlib import Path

import pytest

import chain_development as cd
import completion_shim
from instance_test_support import scratch_instance
import product_checkout
import providers
import skill_path
import walk_stop
from test_providers import (COPY_COMMAND, DELIVERED_TEXT, EXAMPLE_FILE, ProviderText, edited_text,
                            provider_files)


# --- the fakes: one per port the engine is given ------------------------------------------


class FakeFiles:
    """An in-memory tree. `files` maps an absolute path to its text; a directory exists when
    something lives under it."""

    def __init__(self, files: dict[str, str] | None = None):
        self.files = {os.path.normpath(path): text for path, text in (files or {}).items()}
        self.executable: set[str] = set()

    def is_file(self, path: str) -> bool:
        return os.path.normpath(path) in self.files

    def is_dir(self, path: str) -> bool:
        prefix = os.path.normpath(path).rstrip("/") + "/"
        return any(key.startswith(prefix) for key in self.files)

    def list_dir(self, path: str) -> list[str]:
        prefix = os.path.normpath(path).rstrip("/") + "/"
        return sorted({key[len(prefix):].split("/", 1)[0]
                       for key in self.files if key.startswith(prefix)})

    def read_text(self, path: str) -> str | None:
        return self.files.get(os.path.normpath(path))

    def write_text(self, path: str, text: str) -> None:
        self.files[os.path.normpath(path)] = text

    def make_dirs(self, path: str) -> None:
        pass

    def make_executable(self, path: str) -> None:
        self.executable.add(os.path.normpath(path))

    def replace(self, source: str, destination: str) -> None:
        self.files[os.path.normpath(destination)] = self.files.pop(os.path.normpath(source))


class FakeGit:
    """Branches as data: `commits[branch]` is the `(sha, subject)` list a `main..branch` range
    holds, `paths[branch]` the set of paths that branch carries, and `bodies[sha]` the full
    commit body for one sha — a sha with none recorded reads as `""`, `commit_body`'s own
    absence answer. `times[sha]` is one commit's author time, and a sha with none recorded reads
    as `None`, `author_time`'s own. `repos[repo][branch]` is the same list for one repository by
    path, for the external-product case where the instance repo and the product repo hold
    different commits; a repo with no entry there reads `commits`."""

    def __init__(self, commits: dict | None = None, paths: dict | None = None,
                 bodies: dict | None = None, repos: dict | None = None,
                 times: dict | None = None, shukuba_keys: Iterable[str] = ()):
        self.repos = {repo: {branch: list(entries) for branch, entries in per_branch.items()}
                      for repo, per_branch in (repos or {}).items()}
        self.commits = {branch: list(entries) for branch, entries in (commits or {}).items()}
        self.paths = {branch: set(entries) for branch, entries in (paths or {}).items()}
        self.bodies = dict(bodies or {})
        self.times = dict(times or {})
        self.touched: dict[tuple[str, str], str] = {}
        # `shukuba_keys` are the units whose landed commits carry a `Shukuba:` trailer; every
        # question asked is recorded as `(repo, key)`. An unconfigured unit has none.
        self.shukuba_keys = set(shukuba_keys)
        self.shukuba_calls: list[tuple[str, str]] = []

    def commits_ahead(self, repo: str, base: str, branch: str) -> list[tuple[str, str]]:
        if repo in self.repos:
            return list(self.repos[repo].get(branch, []))
        return list(self.commits.get(branch, []))

    def branch_has_path(self, repo: str, branch: str, path: str) -> bool:
        return path in self.paths.get(branch, set())

    def commit_body(self, repo: str, sha: str) -> str:
        return self.bodies.get(sha, "")

    def author_time(self, repo: str, sha: str) -> int | None:
        return self.times.get(sha)

    def last_commit_touching(self, repo: str, branch: str, path: str) -> str | None:
        return self.touched.get((branch, path))

    def unit_has_shukuba(self, repo: str, key: str) -> bool:
        self.shukuba_calls.append((repo, key))
        return key in self.shukuba_keys


# --- the world ------------------------------------------------------------------------------


INSTANCE = "/instance"
INSTANCE_PROVIDER_FILE = providers.instance_file(INSTANCE)
PROJECT = "tracker"
KEY = "2026-09-15_add-due-dates"
TOBIISHI = f"{INSTANCE}/system/projects/{PROJECT}/journey/tobiishi"
SHUKUBA = f"{INSTANCE}/system/projects/{PROJECT}/journey/shukuba"
WORKTREE = f"{INSTANCE}/.worktrees/{KEY}"
CHANGE_REL = f"system/projects/{PROJECT}/journey/tobiishi/{KEY}"
BRANCH_CHANGE = f"{WORKTREE}/{CHANGE_REL}"
MARKER = ("a1b2c3", f"developer: {KEY} — implementation complete")
# The closing marker's body, the shape `.claude/skills/development-implementation/SKILL.md`
# Step 3 declares — both never-omitted lines, so a landed "implementation" step reads as the
# green, language-resolved case unless a test overrides `git.bodies[MARKER[0]]` itself.
# The environment line a closing marker and a passing report each carry (CP-628).
ENVIRONMENT_LINE = "Environment: owners-mac — no CI"
MARKER_BODY = ("Suite: green\n\nLanguage resolution:\n- python — declared in project.md\n\n"
               f"{ENVIRONMENT_LINE}\n")
# A report declaring a pass, and the environment of the run its verdict rests on.
PASSING_REPORT = f"Integrity: pass\n\n{ENVIRONMENT_LINE}\n"
PRODUCERS = ("development-specs", "development-design", "development-plan",
             "development-implementation")

# The header line `development-design` stamps, and the whole design a walk needs to pass the
# content step without a launch. Every fixture that lands a design carries it, so a walk that is
# not about the content step makes the launches it made before the step existed.
NO_TEXT_DESIGN = "# Change Design\n\n**Behaviour:** changing\n**Publishes text:** no\n"
TEXT_DESIGN = ("# Change Design\n\n**Behaviour:** changing\n"
               "**Publishes text:** yes — the glossary page\n")

_REPO = Path(__file__).resolve().parents[2]


def layout(key: str = KEY) -> cd.ChangeLayout:
    return cd.ChangeLayout(instance_root=INSTANCE, project=PROJECT, key=key)


def reader(files=None, git=None) -> cd.DiskReader:
    return cd.DiskReader(files=FakeFiles(files), git=git or FakeGit())


def step(step_id: str) -> cd.Step:
    return next(entry for entry in cd.DEVELOPMENT_STEPS if entry.id == step_id)


def change_step(step_id: str) -> cd.Step:
    return next(entry for entry in cd.CHANGE_STEPS if entry.id == step_id)


def keyless() -> cd.ChangeLayout:
    """The layout a walk holds before `tobiishi-open` has run — every key-derived path is
    nonsense, and the two journey steps must be answerable without touching one."""
    return cd.ChangeLayout(instance_root=INSTANCE, project=PROJECT, key="")


def audit_paths() -> set[str]:
    return {f"{CHANGE_REL}/flow_findings/{skill}.md" for skill in PRODUCERS}


def test_open_change_keys_skips_tobiishi_drop_even_with_a_change_request():
    files = {
        f"{TOBIISHI}/drop/change_request.md": "a dropped unit's request",
        f"{TOBIISHI}/drop/2026-09-01_dropped/change_request.md": "a dropped unit",
        f"{TOBIISHI}/{KEY}/change_request.md": "the open unit",
    }

    assert reader(files).open_change_keys(INSTANCE, PROJECT) == [KEY]


def audited_git(skills=PRODUCERS, marker=True) -> FakeGit:
    paths = {f"{KEY}__audit-{skill}": {f"{CHANGE_REL}/flow_findings/{skill}.md"}
             for skill in skills}
    bodies = {MARKER[0]: MARKER_BODY} if marker else {}
    return FakeGit(commits={KEY: [MARKER]} if marker else {}, paths=paths, bodies=bodies)


# --- the step table -------------------------------------------------------------------------


def test_the_steps_walk_the_pipeline_in_the_workflows_order():
    assert [entry.id for entry in cd.DEVELOPMENT_STEPS] == [
        "specs", "design", "plan", "content", "implementation", "code-integrity", "audit",
        "seal"]


def test_providers_steps_holds_one_content_entry_and_the_rest_unchanged():
    """CP-433: the delivered file carries one `content` entry naming a provider the file
    accepts, and the ten entries that were there keep the values they had."""
    steps = tomllib.loads(EXAMPLE_FILE.read_text(encoding="utf-8"))["steps"]

    assert steps.pop("content") in {"claude", "codex", "gemini"}
    assert steps == {"station": "claude", "change": "claude", "specs": "claude",
                     "design": "claude", "plan": "claude", "implementation": "claude",
                     "code-integrity": "claude", "audit": "claude", "seal": "claude",
                     "refine": "claude"}


def test_every_step_names_a_skill_that_declares_an_unattended_launch():
    """The chain starts each step through `core/launchers/skill/launcher.sh`, which refuses a
    skill with no `launcher.md` — so a step naming one is a walk that dies at that step. The skill
    is found the way that launcher finds it, flat or grouped (`core/tools/skill_path.py`)."""
    for entry in cd.DEVELOPMENT_STEPS:
        resolved = skill_path.resolve_skill_dir(_REPO, entry.skill)
        assert resolved.status == skill_path.FOUND, entry.skill
        assert (resolved.path / "launcher.md").is_file(), entry.skill


def test_only_specs_is_launched_without_the_change_key():
    """development-specs finds the active change itself; every later launcher.md takes the key."""
    assert [entry.id for entry in cd.DEVELOPMENT_STEPS if not entry.takes_key] == ["specs"]


def test_the_audit_fans_out_over_the_producer_steps_and_never_gates():
    audit = step("audit")

    assert audit.fans_out_over == PRODUCERS[:3] + ("development-content",) + PRODUCERS[3:]
    assert audit.gates is False
    assert all(entry.gates for entry in cd.DEVELOPMENT_STEPS if entry.id != "audit")


def test_every_step_declares_its_responsible_role():
    """Each `Step` carries the agent role responsible for it — the value
    `instrument_run.sh` stamps as `kensai.role` on every launch (CP-1)."""
    assert {entry.id: entry.role for entry in cd.DEVELOPMENT_STEPS} == {
        "specs": "product-owner",
        "design": "architect",
        "plan": "tech-lead",
        "content": "content-editor",
        "implementation": "developer",
        "code-integrity": "senior-engineer",
        "audit": "kensaiapp-auditor",
        "seal": "pm",
    }


# --- the change chain's two extra steps -------------------------------------------------------


def test_the_change_steps_are_the_two_journey_moves_ahead_of_the_pipeline_and_the_refine_after():
    """`chain-change` walks the same pipeline `chain-development` does, entered two steps
    earlier — the station the change reaches, then the change request itself — and re-reads the
    route once the seal lands."""
    assert [entry.id for entry in cd.CHANGE_STEPS] == [
        "station", "change",
        "specs", "design", "plan", "content", "implementation", "code-integrity", "audit", "seal",
        "refine"]
    assert cd.CHANGE_STEPS[2:-1] == cd.DEVELOPMENT_STEPS


def test_the_refine_step_runs_as_the_pm_and_takes_the_sealed_units_key():
    """`skills/pm/.claude/skills/shukuba-refine/launcher.md` declares `**Agent:** pm` and
    `**Arguments:** <project> [<unit-key>]` — the walk always names the unit it just sealed."""
    refine = change_step("refine")

    assert (refine.skill, refine.role, refine.takes_key, refine.gates) == (
        "shukuba-refine", "pm", True, True)


def test_the_two_journey_steps_run_as_the_pm_and_take_no_key():
    """Neither has a key to take — `station` runs before one exists and `change` is what
    creates it. `skills/pm/.claude/skills/{shukuba-open,tobiishi-open}/launcher.md` both
    declare `**Arguments:** <project>`."""
    assert {entry.id: (entry.skill, entry.role, entry.takes_key)
            for entry in cd.CHANGE_STEPS[:2]} == {
        "station": ("shukuba-open", "pm", False),
        "change": ("tobiishi-open", "pm", False),
    }


def test_every_change_step_names_a_skill_that_declares_an_unattended_launch():
    """The same contract the development steps are held to, over the two new ones."""
    for entry in cd.CHANGE_STEPS:
        resolved = skill_path.resolve_skill_dir(_REPO, entry.skill)
        assert resolved.status == skill_path.FOUND, entry.skill
        assert (resolved.path / "launcher.md").is_file(), entry.skill


# --- a step's role is held to the agent its launcher declares ---------------------------------

_AGENT_LABEL = "**Agent:**"
_COMMENT_OPENER = "<!--"


# `field Agent` of `core/launchers/skill/launcher.sh` restated in Python rather than called: no
# Python reader of a `launcher.md` field exists, and sharing one with the launcher would mean
# changing the launcher. So the rule lives twice, and the cases below hold this copy to the
# first's stated behaviour — not to its code.
def _launcher_agent(launcher_text: str) -> str | None:
    """The agent the unattended launcher would start a run under, or `None` when the launcher
    declares none: the first line that *begins* with the label, without the label and the
    whitespace after it, a trailing `<!-- … -->` and trailing whitespace."""
    for line in launcher_text.splitlines():
        if line.startswith(_AGENT_LABEL):
            return line[len(_AGENT_LABEL):].partition(_COMMENT_OPENER)[0].strip()
    return None


def _why_a_step_is_not_held(root: Path, entry: cd.Step) -> str | None:
    """What stops `entry`'s role being held to its launcher under `root`, or `None` when the
    launcher is found and its agent is exactly `entry.role`. A step that cannot be compared is
    answered with the reason, never skipped."""
    resolved = skill_path.resolve_skill_dir(root, entry.skill)
    if resolved.status != skill_path.FOUND:
        return f"its skill directory is {resolved.status} under {root}"
    launcher = resolved.path / "launcher.md"
    if not launcher.is_file():
        return f"{launcher} does not exist"
    agent = _launcher_agent(launcher.read_text(encoding="utf-8"))
    if agent is None:
        return f"{launcher} has no line beginning {_AGENT_LABEL}"
    if agent != entry.role:
        return f"{launcher} launches it as {agent!r}, and the step's role is {entry.role!r}"
    return None


def _steps_not_held_to_their_launcher(root: Path, steps: Iterable[cd.Step]) -> list[str]:
    """One finding per step of `steps` whose role is not held to its launcher under `root`, each
    leading with the step's skill name. Every step is walked before anything is returned. The
    only place a launcher is opened and the only place the comparison is made — it carries no
    list of expected agents or roles, so it holds whatever steps and tree it is handed."""
    findings = []
    for entry in steps:
        problem = _why_a_step_is_not_held(root, entry)
        if problem is not None:
            findings.append(f"{entry.skill}: {problem}")
    return findings


def _launcher_declaring(agent_lines: str) -> str:
    """A `launcher.md` body carrying `agent_lines` where the real ones carry their `**Agent:**`
    line, with the other two fields the launcher reads present either way."""
    return ("# unattended launch\n\n"
            f"{agent_lines}"
            "**Arguments:** <project>\n"
            "**Prompt:** invoke the skill for the {project} project.\n")


def _skill_dir(root: Path, skill: str, group: str | None = None) -> Path:
    """One skill directory under `root`, in either shape `skill_path` resolves: flat when no
    `group` is named, grouped under `skills/<group>/` when one is."""
    base = root if group is None else root / "skills" / group
    directory = base / ".claude" / "skills" / skill
    directory.mkdir(parents=True)
    return directory


def _write_launcher(root: Path, skill: str, agent_lines: str, group: str | None = None) -> None:
    (_skill_dir(root, skill, group) / "launcher.md").write_text(
        _launcher_declaring(agent_lines), encoding="utf-8")


def _step_run_as(skill: str, role: str) -> cd.Step:
    return cd.Step(skill, skill, role, cd.Evidence.CHANGE_FILE)


def test_a_launcher_agent_that_differs_from_the_step_role_is_named(tmp_path):
    """CP-235, CP-236: the launcher starts the run as one agent and the step is stamped as
    another — the case nothing caught before this check."""
    _write_launcher(tmp_path, "shukuba-open", "**Agent:** architect\n", group="pm")

    findings = _steps_not_held_to_their_launcher(tmp_path, [_step_run_as("shukuba-open", "pm")])

    assert len(findings) == 1
    assert "shukuba-open" in findings[0]


def test_a_launcher_and_step_changed_together_still_agree(tmp_path):
    """CP-237: the agent is read off the launcher, never off a table the check carries — so the
    real skill name under a role the real step does not have is held, with the check unedited."""
    _write_launcher(tmp_path, "shukuba-open", "**Agent:** architect\n", group="pm")

    assert _steps_not_held_to_their_launcher(
        tmp_path, [_step_run_as("shukuba-open", "architect")]) == []


def test_the_flat_development_audit_launcher_is_held_too(tmp_path):
    """CP-238: the one step whose launcher sits flat under `.claude/skills/` is compared the same
    as the grouped nine."""
    _write_launcher(tmp_path, "development-audit", "**Agent:** pm\n")

    findings = _steps_not_held_to_their_launcher(
        tmp_path, [_step_run_as("development-audit", "kensaiapp-auditor")])

    assert len(findings) == 1
    assert "development-audit" in findings[0]


def test_a_launcher_with_no_agent_line_is_a_finding_not_a_skip(tmp_path):
    """CP-239: a launcher with its other fields present and no `**Agent:**` line cannot be
    compared, and a step that cannot be compared is not a step that was held."""
    _write_launcher(tmp_path, "tobiishi-seal", "", group="pm")

    findings = _steps_not_held_to_their_launcher(tmp_path, [_step_run_as("tobiishi-seal", "pm")])

    assert len(findings) == 1
    assert "tobiishi-seal" in findings[0]


def _no_directory_for_the_skill(root: Path) -> None:
    _write_launcher(root, "shukuba-open", "**Agent:** pm\n", group="pm")


def _two_grouped_directories_for_the_skill(root: Path) -> None:
    _write_launcher(root, "shukuba-refine", "**Agent:** pm\n", group="pm")
    _write_launcher(root, "shukuba-refine", "**Agent:** pm\n", group="scrum-master")


def _a_directory_holding_no_launcher(root: Path) -> None:
    (_skill_dir(root, "shukuba-refine", group="pm") / "SKILL.md").write_text(
        "# shukuba-refine\n", encoding="utf-8")


@pytest.mark.parametrize("lay_out_the_tree", [
    _no_directory_for_the_skill,
    _two_grouped_directories_for_the_skill,
    _a_directory_holding_no_launcher,
], ids=["no-directory", "two-grouped-directories", "directory-without-launcher"])
def test_a_launcher_that_cannot_be_found_is_a_finding(tmp_path, lay_out_the_tree):
    """CP-239: each way `core/launchers/skill/launcher.sh` would fail to find the launcher is a
    finding naming the step — never an exception that escapes without the skill's name."""
    lay_out_the_tree(tmp_path)

    findings = _steps_not_held_to_their_launcher(tmp_path, [_step_run_as("shukuba-refine", "pm")])

    assert len(findings) == 1
    assert "shukuba-refine" in findings[0]


@pytest.mark.parametrize("agent_lines, held", [
    ("**Agent:** pm   <!-- note -->\n", True),
    ("**Agent:** pm<!-- note -->\n", True),
    ("**Agent:**pm\n", True),
    ("**Agent:** \t pm \t \n", True),
    ("**Agent:** pm\n**Agent:** architect\n", True),
    ("The launcher reads the **Agent:** architect line.\n**Agent:** pm\n", True),
    ("**Agent:**\n", False),
    ("**Agent:**   <!-- pm -->\n", False),
    ("**Agent:**\n**Agent:** pm\n", False),
    ("  **Agent:** pm\n", False),
], ids=["trailing-comment", "comment-flush-against-the-agent", "no-space-after-the-label",
        "whitespace-either-side", "first-of-two-lines-wins", "mid-line-mention-ahead",
        "nothing-after-the-label", "only-a-comment-after-the-label",
        "empty-first-line-still-wins", "indented-label-is-not-the-line"])
def test_the_agent_is_what_the_launcher_would_take_from_the_line(tmp_path, agent_lines, held):
    """CP-235's *the launcher's agent*: `field Agent` of `core/launchers/skill/launcher.sh` —
    the first line that begins with the label, without the label, the whitespace after it, a
    trailing `<!-- … -->` and trailing whitespace. A raw-line comparison would go red on a
    comment the launcher ignores; an empty agent equals no role, so it is a disagreement."""
    _write_launcher(tmp_path, "shukuba-open", agent_lines, group="pm")

    findings = _steps_not_held_to_their_launcher(tmp_path, [_step_run_as("shukuba-open", "pm")])

    assert (findings == []) is held, findings


def test_everything_after_a_comment_opens_is_dropped_even_past_its_close(tmp_path):
    """*The launcher's agent* again: the launcher drops from `<!--` to the end of the line, not
    only the comment — so text after a closed comment is no part of the agent it starts."""
    _write_launcher(
        tmp_path, "shukuba-open", "**Agent:** pm <!-- note --> architect\n", group="pm")

    assert _steps_not_held_to_their_launcher(tmp_path, [_step_run_as("shukuba-open", "pm")]) == []


@pytest.mark.parametrize("agent, role", [
    ("PM", "pm"),
    ("principal-pm", "pm"),
    ("pm", "principal-pm"),
    ("pm-lead", "pm"),
    ("tech lead", "tech-lead"),
], ids=["case-differs", "agent-ends-with-the-role", "role-ends-with-the-agent",
        "agent-begins-with-the-role", "space-for-a-hyphen"])
def test_the_agent_and_the_role_are_compared_as_exact_strings(tmp_path, agent, role):
    """CP-235: the two are equal or the check fails. A near match — another case, or one name
    inside the other, as `pm` is inside `principal-pm` — is a different agent: a disagreement."""
    _write_launcher(tmp_path, "shukuba-open", f"**Agent:** {agent}\n", group="pm")

    findings = _steps_not_held_to_their_launcher(tmp_path, [_step_run_as("shukuba-open", role)])

    assert len(findings) == 1
    assert findings[0].startswith("shukuba-open:")


def test_every_disagreement_is_reported_not_only_the_first(tmp_path):
    """Every step is walked before anything is reported, and each finding leads with its step's
    skill name — so one red run names all of what disagrees, in the order the steps were given."""
    _write_launcher(tmp_path, "shukuba-open", "**Agent:** architect\n", group="pm")
    _write_launcher(tmp_path, "tobiishi-open", "**Agent:** pm\n", group="pm")
    _write_launcher(tmp_path, "tobiishi-seal", "**Agent:** developer\n", group="pm")

    findings = _steps_not_held_to_their_launcher(tmp_path, [
        _step_run_as("shukuba-open", "pm"),
        _step_run_as("tobiishi-open", "pm"),
        _step_run_as("tobiishi-seal", "pm"),
    ])

    assert [finding.split(":")[0] for finding in findings] == ["shukuba-open", "tobiishi-seal"]


def test_every_chain_step_runs_as_the_agent_its_launcher_declares():
    """CP-235, CP-238: `Step.role` is what the chain stamps as `kensai.role`, and the launcher's
    `**Agent:**` line is what the run really starts under — two statements of one fact, compared
    here over this tree. The domain is every table the engine holds (`cd.STEP_TABLES`), so a
    step or a table added later is held the day it lands, with nothing here edited."""
    steps = [entry for table in cd.STEP_TABLES.values() for entry in table]

    findings = _steps_not_held_to_their_launcher(_REPO, steps)

    assert steps, "cd.STEP_TABLES holds no step — the check compared nothing"
    assert not findings, "\n".join(findings)


# --- the two journey steps are answered off the disk with no key ------------------------------


def test_a_station_file_at_the_shukuba_root_is_the_station_step_landing():
    """One `<date>_<slug>.md` at the root, which is the whole of what `shukuba-open` leaves
    (`skills/pm/.claude/skills/shukuba-open/SKILL.md` Step 3a)."""
    disk = reader({f"{SHUKUBA}/2026-09-17_the-chain-walks-a-station.md": "station"})

    assert disk.is_done(keyless(), change_step("station"))


def test_the_readme_the_parked_and_the_trail_are_not_an_open_station():
    """`project-stamp` writes the README, and the other two are where a station goes when it
    is parked or reached — a walk that read any of them as an open station would skip the one
    step that opens one."""
    disk = reader({
        f"{SHUKUBA}/README.md": "the stamped readme",
        f"{SHUKUBA}/parked/2026-09-01_paused.md": "parked",
        f"{SHUKUBA}/trail/2026-09-02_reached.md": "reached",
    })

    assert not disk.is_done(keyless(), change_step("station"))


def test_open_stations_lists_every_station_at_the_root_and_nothing_else():
    """A root holds one station; one holding two is a state a caller must see, not have picked
    for it — `open_station` answers whether one is open, this answers which."""
    disk = reader({
        f"{SHUKUBA}/README.md": "the stamped readme",
        f"{SHUKUBA}/2026-09-19_second.md": "station",
        f"{SHUKUBA}/2026-09-18_first.md": "station",
        f"{SHUKUBA}/trail/2026-09-02_reached.md": "reached",
    })

    assert disk.open_stations(INSTANCE, PROJECT) == ["2026-09-18_first.md", "2026-09-19_second.md"]


def test_the_change_step_lands_when_a_change_request_is_on_disk_with_no_key_in_hand():
    """`CHANGE_OPEN` is read exactly as `discover_key` reads it, so the step that creates the
    key is answered before the walk has one."""
    open_change = reader({f"{TOBIISHI}/{KEY}/change_request.md": "req"})
    sealed_only = reader({f"{TOBIISHI}/trail/2026-09-01_old/change_request.md": "sealed"})

    assert open_change.is_done(keyless(), change_step("change"))
    assert not sealed_only.is_done(keyless(), change_step("change"))


@pytest.mark.parametrize("files, entry", [
    ({}, "station"),
    ({f"{SHUKUBA}/2026-09-17_a-station.md": "station"}, "change"),
    ({f"{SHUKUBA}/2026-09-17_a-station.md": "station",
      f"{TOBIISHI}/{KEY}/change_request.md": "req"}, "specs"),
])
def test_a_change_walk_enters_at_the_first_journey_step_with_nothing_on_disk(files, entry):
    """The same derivation `chain-development` makes, over the longer table: no matter what is
    already there, a start works out where to continue from."""
    assert reader(files).entry_step(keyless(), cd.CHANGE_STEPS).id == entry


def test_a_change_walk_past_the_two_journey_steps_enters_where_the_development_walk_would():
    """Once a station and a change request exist, the two tables agree step for step — which
    is what makes `chain-change` a superset of `chain-development` rather than a rival."""
    files, git = _through("plan")
    files[f"{SHUKUBA}/2026-09-17_a-station.md"] = "station"
    disk = reader(files, git)

    assert disk.entry_step(layout(), cd.CHANGE_STEPS).id == "implementation"
    assert disk.entry_step(layout(), cd.DEVELOPMENT_STEPS).id == "implementation"


# --- the change's layout ----------------------------------------------------------------------


def test_the_layout_derives_every_path_from_the_key_alone():
    change = layout()

    assert change.worktree == WORKTREE
    assert change.branch_change_folder == BRANCH_CHANGE
    assert change.main_change_folder == f"{TOBIISHI}/{KEY}"
    assert change.trail_folder == f"{TOBIISHI}/trail/{KEY}"
    assert change.findings_path("development-plan") == f"{CHANGE_REL}/flow_findings/development-plan.md"
    assert change.audit_branch("development-plan") == f"{KEY}__audit-development-plan"


# --- discovering the change -------------------------------------------------------------------


def test_the_one_folder_holding_a_change_request_is_the_key():
    disk = reader({f"{TOBIISHI}/{KEY}/change_request.md": "req"})

    assert disk.discover_key(INSTANCE, PROJECT) == KEY


def test_the_trail_and_a_folder_without_a_change_request_are_not_changes():
    disk = reader({
        f"{TOBIISHI}/{KEY}/change_request.md": "req",
        f"{TOBIISHI}/trail/2026-09-01_old/change_request.md": "sealed",
        f"{TOBIISHI}/2026-09-02_notes/scratch.md": "not a change",
        f"{TOBIISHI}/README.md": "readme",
    })

    assert disk.discover_key(INSTANCE, PROJECT) == KEY


def test_no_active_change_is_refused_naming_where_it_looked():
    disk = reader({f"{TOBIISHI}/trail/2026-09-01_old/change_request.md": "sealed"})

    with pytest.raises(cd.ChainRefused, match="no active change"):
        disk.discover_key(INSTANCE, PROJECT)


def test_two_active_changes_are_refused_naming_both():
    disk = reader({
        f"{TOBIISHI}/{KEY}/change_request.md": "one",
        f"{TOBIISHI}/2026-09-16_other/change_request.md": "two",
    })

    with pytest.raises(cd.ChainRefused) as refused:
        disk.discover_key(INSTANCE, PROJECT)
    assert KEY in str(refused.value) and "2026-09-16_other" in str(refused.value)


# --- what counts as done, per step --------------------------------------------------------------


@pytest.mark.parametrize("step_id, artifact", [
    ("specs", "change_spec.md"),
    ("design", "change_design.md"),
    ("plan", "tl_instruction.md"),
    ("code-integrity", "code-integrity-report.md"),
])
def test_a_folder_step_is_done_when_its_artifact_is_on_the_change_branch(step_id, artifact):
    assert reader({f"{BRANCH_CHANGE}/{artifact}": "x"}).is_done(layout(), step(step_id))


@pytest.mark.parametrize("step_id, artifact", [
    ("specs", "change_spec.md"),
    ("code-integrity", "code-integrity-report.md"),
])
def test_an_artifact_only_on_main_is_not_the_step_being_done(step_id, artifact):
    """Every step writes on the branch in `.worktrees/<key>`; a file of the same name on the
    main checkout is some other state, never this step's output."""
    assert not reader({f"{TOBIISHI}/{KEY}/{artifact}": "x"}).is_done(layout(), step(step_id))


def test_implementation_is_done_when_its_closing_marker_is_on_the_branch():
    git = FakeGit(commits={KEY: [("0ff1ce", "task 3 — green"), MARKER]})

    disk = reader(git=git)

    assert disk.is_done(layout(), step("implementation"))
    assert disk.marker_commit(layout()) == "a1b2c3"


def test_implementation_without_the_marker_is_not_done():
    git = FakeGit(commits={KEY: [("0ff1ce", "task 3 — green")]})

    disk = reader(git=git)

    assert not disk.is_done(layout(), step("implementation"))
    assert disk.marker_commit(layout()) is None


def test_another_changes_marker_on_the_branch_is_not_this_changes_marker():
    """A branch rebuilt onto a base can carry another change's closing marker ahead of `main` —
    `2026-09-22_a-run-keeps-the-version-it-started-on` carried two of
    `2026-09-21_codex-assigned-model-attribution`'s and was walked into code-integrity after a
    pause. Only a subject naming this change's key closes it."""
    other = ("0babe1", "2026-09-21_other-change — implementation complete (suite re-run green)")
    git = FakeGit(commits={KEY: [("0ff1ce", "task 3 — green"), other]})

    disk = reader(git=git)

    assert not disk.is_done(layout(), step("implementation"))
    assert disk.marker_commit(layout()) is None


def test_another_changes_marker_does_not_hide_this_changes_pause():
    other = ("0babe1", "developer: 2026-09-21_other-change — implementation complete")
    pause = ("0cafe1", f"developer: {KEY} — implementation paused after task 7")
    git = FakeGit(commits={KEY: [other, pause]})

    assert reader(git=git).paused_after(layout(), PRODUCT) == 7


def test_another_changes_pause_is_not_this_changes_pause():
    pause = ("0cafe1", "developer: 2026-09-21_other-change — implementation paused after task 7")
    git = FakeGit(commits={KEY: [pause]})

    assert reader(git=git).paused_after(layout(), PRODUCT) is None


def test_a_suite_line_quoted_elsewhere_in_the_body_is_not_the_declaration():
    """A `Developer Review Notes` line that quotes an earlier draft's `Suite: red` must not be
    read as the declaration — only a line whose own stripped form starts with the literal
    `Suite:` prefix counts."""
    body = ("Suite: green\n\n"
            "Developer Review Notes:\n"
            '- earlier draft read "Suite: red" before the fix — reason: …\n')
    git = FakeGit(commits={KEY: [MARKER]}, bodies={MARKER[0]: body})

    assert reader(git=git).suite_verdict(layout()) == "green"


def test_an_audit_is_done_when_its_own_branch_carries_its_findings_file():
    disk = reader(git=audited_git(skills=("development-design",)))

    assert disk.audit_done(layout(), "development-design")
    assert not disk.audit_done(layout(), "development-plan")


def test_the_audit_step_is_done_only_when_all_four_findings_are_on_their_branches():
    assert reader(git=audited_git()).is_done(layout(), step("audit"))
    assert not reader(git=audited_git(skills=PRODUCERS[:3])).is_done(layout(), step("audit"))


def test_the_seal_is_done_when_the_change_sits_in_the_trail_on_main():
    sealed = reader({f"{TOBIISHI}/trail/{KEY}/change_request.md": "sealed"})

    assert sealed.is_done(layout(), step("seal"))
    assert not reader().is_done(layout(), step("seal"))


# --- where a walk enters ----------------------------------------------------------------------


def _through(step_id: str) -> tuple[dict, FakeGit]:
    """The disk as it stands once every step up to and including `step_id` has landed."""
    order = [entry.id for entry in cd.DEVELOPMENT_STEPS]
    landed = set(order[:order.index(step_id) + 1]) if step_id else set()
    files = {f"{TOBIISHI}/{KEY}/change_request.md": "req"}
    for landed_id, artifact in (("specs", "change_spec.md"), ("design", "change_design.md"),
                                ("plan", "tl_instruction.md"),
                                ("code-integrity", "code-integrity-report.md")):
        if landed_id in landed:
            content = {"code-integrity": PASSING_REPORT,
                       "design": NO_TEXT_DESIGN}.get(landed_id, "x")
            files[f"{BRANCH_CHANGE}/{artifact}"] = content
    git = audited_git(skills=PRODUCERS if "audit" in landed else (),
                      marker="implementation" in landed)
    return files, git


@pytest.mark.parametrize("landed_through, entry", [
    (None, "specs"),
    ("specs", "design"),
    ("design", "plan"),
    ("plan", "implementation"),
    ("implementation", "code-integrity"),
    ("code-integrity", "audit"),
    ("audit", "seal"),
])
def test_the_entry_step_is_the_first_whose_evidence_is_missing(landed_through, entry):
    files, git = _through(landed_through)

    assert reader(files, git).entry_step(layout(), cd.DEVELOPMENT_STEPS).id == entry


def test_a_sealed_change_has_no_entry_step():
    files, git = _through("audit")
    files[f"{TOBIISHI}/trail/{KEY}/change_request.md"] = "sealed"

    assert reader(files, git).entry_step(layout(), cd.DEVELOPMENT_STEPS) is None


# --- where a halt left its report ---------------------------------------------------------------


BRANCH_TRAIL = f"{WORKTREE}/system/projects/{PROJECT}/journey/tobiishi/trail/{KEY}"


@pytest.mark.parametrize("where", [
    f"{BRANCH_CHANGE}/halt_report.md",
    f"{BRANCH_TRAIL}/halt_report.md",
    f"{TOBIISHI}/{KEY}/halt_report.md",
    f"{TOBIISHI}/halt_report.md",
    f"{INSTANCE}/halt_report.md",
])
def test_a_halt_report_is_found_wherever_a_step_is_allowed_to_leave_it(where):
    """The branch's change folder for a step inside the worktree, and on the branch's
    `trail/<key>/` for a seal halt written after its folder move; the three pre-worktree homes
    development-specs names, deepest first."""
    assert reader({where: "halted"}).halt_report(layout()) == where


def test_a_seal_halt_after_the_move_is_named_not_reported_as_a_missing_trail():
    """Cold read 2026-09-29, D5: a two-repo seal that merged the product and then failed the
    instance merge writes its report into the moved folder on the branch. The owner reads that
    report — `instance-merge-after-product`, the product merge already landed — not "no trail/"."""
    walk = Walk(through="audit")
    report = f"{BRANCH_TRAIL}/halt_report.md"
    walk.files.write_text(report, "instance-merge-after-product")

    walk.advance("seal")

    assert walk.state["ended"] == "halted"
    assert report in walk.state["ended_reason"]
    assert "no trail/" not in walk.state["ended_reason"]


def test_a_pre_move_seal_report_wins_over_the_moved_folders():
    disk = reader({f"{BRANCH_CHANGE}/halt_report.md": "now",
                   f"{BRANCH_TRAIL}/halt_report.md": "earlier"})

    assert disk.halt_report(layout()) == f"{BRANCH_CHANGE}/halt_report.md"


def test_the_branch_report_wins_over_one_left_on_main():
    disk = reader({f"{BRANCH_CHANGE}/halt_report.md": "now",
                   f"{TOBIISHI}/{KEY}/halt_report.md": "earlier"})

    assert disk.halt_report(layout()) == f"{BRANCH_CHANGE}/halt_report.md"


def test_no_halt_report_anywhere_is_none():
    assert reader().halt_report(layout()) is None


# --- the ports a walk launches through ----------------------------------------------------------


class FakeProcesses:
    """Records every launch. `codes` scripts the exit status each successive call returns;
    `on_run` lets a test look at the world at the moment a launch happens."""

    def __init__(self, codes: list[int] | None = None, on_run=None):
        self.calls: list[dict] = []
        self.codes = list(codes or [])
        self.on_run = on_run

    def run(self, argv, *, cwd=None, env=None, capture=False, timeout=None) -> int:
        self.calls.append({"argv": list(argv), "cwd": cwd, "env": dict(env or {})})
        if self.on_run:
            self.on_run(list(argv))
        return self.codes.pop(0) if self.codes else 0

    @property
    def launched(self) -> list[list[str]]:
        return [call["argv"] for call in self.calls]


class FakeNotifier:
    def __init__(self):
        self.messages: list[str] = []

    def send(self, message: str) -> bool:
        self.messages.append(message)
        return True


class FakeWalkLog:
    """Records every line appended to a chain log, with the path it went to."""

    def __init__(self):
        self.lines: list[tuple[str, str]] = []

    def append(self, path: str, line: str) -> None:
        self.lines.append((path, line))


class FakeIdSource:
    def new_id(self) -> str:
        return "walk-1"


class FakeLock:
    """Records every hold, and whether one was open when something else happened."""

    def __init__(self):
        self.holds: list[str] = []
        self.held = False

    def hold(self, path: str):
        lock = self

        class _Held:
            def __enter__(self):
                lock.holds.append(path)
                lock.held = True

            def __exit__(self, *exc):
                lock.held = False
                return False

        return _Held()


class FakeCheckout:
    """The product checkout's port. `readings` scripts what each successive `entries` call
    answers (a list of porcelain lines, or `None` for a checkout it cannot read); once they are
    spent every call answers `[]`, a checkout that never changes. `read` records the path of
    every call, which is how a test names what the engine looked at."""

    def __init__(self, *readings):
        self.readings = list(readings)
        self.read: list[str] = []

    def entries(self, path: str):
        self.read.append(path)
        return self.readings.pop(0) if self.readings else []


class FakeProcessTable:
    """The process port a stop reaches through: `starts` maps a pid to the start time `ps` would
    read for it, and `stopped` records every `stop_group` in order. Stopping a pid ends it."""

    def __init__(self, starts: dict[int, str] | None = None):
        self.starts = dict(starts or {})
        self.stopped: list[int] = []

    def start_time(self, pid: int) -> str | None:
        return self.starts.get(pid)

    def stop_group(self, pid: int) -> None:
        self.stopped.append(pid)
        self.starts.pop(pid, None)


CORE = "/core"
PRODUCT = "/product"
LOGS = f"{INSTANCE}/system/logs"
STATE = f"{LOGS}/chain-development-{PROJECT}-state.json"
ENGINE = "/pinned/chain_development.py"
SKILL_LAUNCHER = f"{CORE}/launchers/skill/launcher.sh"


def build(files: FakeFiles, *, git=None, processes=None, notifier=None, lock=None, environ=None,
          log=None, steps=None, provider_port=None, process_table=None, checkout=None):
    return cd.DevelopmentChain(
        store=cd.StateStore(files, STATE),
        reader=cd.DiskReader(files=files, git=git or FakeGit()),
        files=files,
        processes=processes or FakeProcesses(),
        notifier=notifier or FakeNotifier(),
        lock=lock or FakeLock(),
        log=log or FakeWalkLog(),
        id_source=FakeIdSource(),
        environ={"PATH": "/usr/bin"} if environ is None else environ,
        engine_path=ENGINE,
        steps=cd.DEVELOPMENT_STEPS if steps is None else steps,
        providers=provider_files(port=provider_port),
        process_table=FakeProcessTable() if process_table is None else process_table,
        checkout=checkout or FakeCheckout(),
    )


def start(engine, product_path: str = PRODUCT, **kwargs):
    return engine.start(instance_root=INSTANCE, product_path=product_path, project=PROJECT,
                        core_dir=CORE, shim_dir=LOGS, **kwargs)


def identity_file(run: str, chain: str = "development") -> str:
    """Where the engine tells a launch to record itself: beside that run's shim."""
    return walk_stop.identity_path(f"{LOGS}/chain-{chain}-{PROJECT}-{run}.sh")


def fresh_change() -> dict:
    return {f"{TOBIISHI}/{KEY}/change_request.md": "req"}


def saved(files: FakeFiles) -> dict:
    import json
    return json.loads(files.files[STATE])


# --- starting a walk ----------------------------------------------------------------------------


def test_a_fresh_change_starts_at_specs_with_only_the_project():
    processes = FakeProcesses()

    start(build(FakeFiles(fresh_change()), processes=processes))

    assert processes.launched == [[SKILL_LAUNCHER, "development-specs", PROJECT]]
    assert processes.calls[0]["cwd"] == INSTANCE


def test_the_walk_enters_where_the_disk_says_and_passes_the_key():
    files, git = _through("plan")
    processes = FakeProcesses()

    start(build(FakeFiles(files), git=git, processes=processes))

    assert processes.launched == [[SKILL_LAUNCHER, "development-implementation", PROJECT, KEY]]


def test_keep_awake_is_handed_to_the_launcher_last():
    processes = FakeProcesses()

    start(build(FakeFiles(fresh_change()), processes=processes), keep_awake=True)

    assert processes.launched[0][-1] == "--keep-awake"


def test_the_launch_environment_points_the_watcher_at_this_runs_shim():
    processes = FakeProcesses()

    start(build(
        FakeFiles(fresh_change()),
        processes=processes,
        environ={"PATH": "/usr/bin", "KENSAIAPP_AGENT_PROVIDER": "codex"},
    ))

    env = processes.calls[0]["env"]
    assert env["DETACH_WATCHER_ON_COMPLETE"] == f"{LOGS}/chain-development-{PROJECT}-specs.sh"
    assert env["INSTRUMENT_RUN_CHAIN"] == "development"
    assert env["INSTRUMENT_RUN_WALK_ID"] == "walk-1"
    assert env["PATH"] == "/usr/bin"


# --- the provider: forced for the walk, else the provider file's entry, else a refusal ----------


# CP-275: the provider each step has as delivered — every step on claude, the owner's call of
# 2026-10-16.
DELIVERED_STEP_PROVIDERS = {step.id: "claude" for step in cd.CHANGE_STEPS}


def _launch_provider(processes: "FakeProcesses", index: int = 0) -> str:
    return processes.calls[index]["env"]["KENSAIAPP_AGENT_PROVIDER"]


def _entering_at(step_id: str, steps: tuple) -> tuple[dict, "FakeGit"]:
    """A disk from which a start over `steps` enters at `step_id`."""
    if step_id == "station":
        return {}, FakeGit()
    if step_id == "change":
        return {STATION: "station"}, FakeGit()
    if step_id == "refine":
        return just_sealed(), FakeGit()
    order = [entry.id for entry in cd.DEVELOPMENT_STEPS]
    previous = order[order.index(step_id) - 1] if order.index(step_id) else None
    disk, git = _through(previous)
    if step_id == "content":
        disk[f"{BRANCH_CHANGE}/change_design.md"] = TEXT_DESIGN
    if steps is cd.CHANGE_STEPS:
        disk[STATION] = "station"
    return disk, git


def _started_at(step_id: str, steps: tuple, **build_arguments) -> "FakeProcesses":
    disk, git = _entering_at(step_id, steps)
    processes = FakeProcesses()
    start(build(FakeFiles(disk), git=git, processes=processes, steps=steps, **build_arguments))
    return processes


@pytest.mark.parametrize("step_id", [step.id for step in cd.CHANGE_STEPS])
def test_every_step_launches_on_its_cp275_provider_in_both_tables(step_id):
    """CP-290(a): one assertion per step, over every table that holds it — a step both walks run
    has one entry, which governs it in both."""
    tables = [steps for steps in (cd.DEVELOPMENT_STEPS, cd.CHANGE_STEPS)
              if step_id in {step.id for step in steps}]
    for steps in tables:
        processes = _started_at(step_id, steps)
        skill = next(step.skill for step in steps if step.id == step_id)

        assert {argv[1] for argv in processes.launched} == {skill}
        assert {call["env"]["KENSAIAPP_AGENT_PROVIDER"] for call in processes.calls} == {
            DELIVERED_STEP_PROVIDERS[step_id]}


def _own_steps(steps: tuple) -> list[tuple[str, tuple]]:
    return [(step.id, steps) for step in steps]


@pytest.mark.parametrize("step_id, steps", [
    *_own_steps(cd.DEVELOPMENT_STEPS),
    *[(step.id, cd.CHANGE_STEPS) for step in cd.CHANGE_STEPS
      if step.id not in {entry.id for entry in cd.DEVELOPMENT_STEPS}],
])
def test_a_copy_lacking_an_own_step_refuses_describe_and_start_naming_it(step_id, steps):
    """CP-290(b), CP-281: refused before anything is written or launched, whichever step the
    walk would enter at."""
    lacking = edited_text({f"steps.{step_id}": None})
    disk = fresh_change() if steps is cd.DEVELOPMENT_STEPS else {}
    files, processes = FakeFiles(disk), FakeProcesses()
    engine = build(files, processes=processes, steps=steps, provider_port=ProviderText(lacking))

    with pytest.raises(cd.ChainRefused, match=f"steps\\.{step_id} is missing"):
        describe(engine)
    with pytest.raises(cd.ChainRefused, match=f"steps\\.{step_id} is missing"):
        start(engine)

    assert STATE not in files.files
    assert processes.calls == []


def test_a_development_walk_does_not_check_station_change_or_refine():
    """The development walk's own members are its own table's steps (design §4 D): the change
    walk's three journey steps are not a development walk's to refuse over."""
    lacking = edited_text({"steps.station": None, "steps.change": None, "steps.refine": None})
    processes = FakeProcesses()

    start(build(FakeFiles(fresh_change()), processes=processes,
                provider_port=ProviderText(lacking)))

    assert processes.launched == [[SKILL_LAUNCHER, "development-specs", PROJECT]]


def test_a_bad_value_and_a_missing_file_refuse_a_start():
    """CP-282 (Ex 14, 15)."""
    grok = build(FakeFiles(fresh_change()),
                 provider_port=ProviderText(edited_text({"steps.audit": "grok"})))
    with pytest.raises(cd.ChainRefused, match=r"steps\.audit names 'grok'"):
        start(grok)

    files, processes = FakeFiles({}), FakeProcesses()
    missing = build(files, processes=processes, steps=cd.CHANGE_STEPS,
                    provider_port=ProviderText(None))
    with pytest.raises(cd.ChainRefused, match=re.escape(INSTANCE_PROVIDER_FILE)):
        start(missing)
    assert STATE not in files.files
    assert processes.calls == []


@pytest.mark.parametrize("forced", ["codex", "claude"])
def test_a_forced_walk_never_reads_the_file(forced):
    """CP-290(c), CP-285: the force goes on every launch, and nothing about the file — a missing
    entry, another provider, or no file at all — refuses the walk or moves a launch."""
    lacking = edited_text({"steps.specs": None, "steps.code-integrity": "gemini"})
    for port in (ProviderText(lacking), ProviderText(None)):
        engine = build(FakeFiles(fresh_change()), provider_port=port)
        plan = engine.describe(instance_root=INSTANCE, project=PROJECT, forced_provider=forced)
        assert dict(plan.providers) == {step.id: forced for step in cd.DEVELOPMENT_STEPS}

        processes = FakeProcesses()
        start(build(FakeFiles(fresh_change()), processes=processes, provider_port=port),
              forced_provider=forced)
        assert _launch_provider(processes) == forced
        assert port.reads == 0

    walk = Walk(through="implementation", forced_provider=forced,
                provider_port=ProviderText(None))
    land(walk.files, walk.git, "code-integrity")
    walk.advance("code-integrity")
    assert {call["env"]["KENSAIAPP_AGENT_PROVIDER"] for call in walk.processes.calls} == {forced}
    assert len(walk.processes.calls) == 5


def test_the_describe_plan_of_an_unforced_walk_carries_each_steps_provider_in_table_order():
    """CP-287: the plan carries `(step, provider)` for every step of the walk's table, in order."""
    plan = build(FakeFiles({}), steps=cd.CHANGE_STEPS).describe(instance_root=INSTANCE,
                                                                project=PROJECT)

    assert plan.providers == tuple((step.id, DELIVERED_STEP_PROVIDERS[step.id])
                                   for step in cd.CHANGE_STEPS)


def test_an_engine_built_by_build_chain_resolves_every_step_at_the_instance_root(tmp_path):
    """CP-290(d), CP-483: the composition root hands the engine a port that answers for the
    instance root asked, so the file at that root is the one every step is resolved from."""
    instance = _instance_with_one_change(tmp_path)

    for steps in (cd.DEVELOPMENT_STEPS, cd.CHANGE_STEPS):
        engine = cd.build_chain(str(tmp_path / "state.json"), notifier_command="",
                                engine_path="/e", steps=steps)
        resolved = engine.providers.at(str(instance)).resolve(
            [providers.step(step.id) for step in steps])
        assert {member.key: value for member, value in resolved.items()} == {
            step.id: DELIVERED_STEP_PROVIDERS[step.id] for step in steps}


def test_the_composition_root_reads_any_instance_root(tmp_path):
    """CP-483, CP-484: the port answers `<root>/.providers.toml` for any root, and none of them
    sits under the engine's own directory."""
    engine_directory = Path(cd.__file__).resolve().parent

    for steps in (cd.DEVELOPMENT_STEPS, cd.CHANGE_STEPS):
        engine = cd.build_chain(str(tmp_path / "state.json"), notifier_command="",
                                engine_path="/e", steps=steps)
        for root in (tmp_path / "one", tmp_path / "two"):
            answered = engine.providers.at(str(root)).path
            assert answered == providers.instance_file(str(root))
            assert engine_directory not in Path(answered).parents


def test_describe_reads_the_instance_file_at_its_root():
    """CP-483: the plan's providers come from `<instance_root>/.providers.toml` and nowhere else."""
    class PathsRead(ProviderText):
        paths: list[str] = []

        def read_text(self, path):
            self.paths.append(path)
            return super().read_text(path)

    port = PathsRead()

    describe(build(FakeFiles({}), steps=cd.CHANGE_STEPS, provider_port=port))

    assert set(port.paths) == {INSTANCE_PROVIDER_FILE}


def test_describe_and_start_without_the_file_are_refused_naming_the_copy_command(
        tmp_path, capsys):
    """CP-486, main-level: an instance holding only the example is refused by both, naming the
    path and the command, and no state is written."""
    instance = _instance_with_one_change(tmp_path)
    (instance / ".providers.toml").rename(instance / ".providers.toml.example")
    state = instance / "system" / "logs" / "state.json"
    base = ["--instance-root", str(instance), "--project", PROJECT]

    assert cd.main(["--describe", str(state), *base]) == 3
    described = capsys.readouterr().err
    assert cd.main(["--start", str(state), *base, "--product-path", str(tmp_path / "product"),
                    "--core-dir", str(tmp_path / "no-core"), "--shim-dir", str(state.parent)]) == 3
    started = capsys.readouterr().err

    for refusal in (described, started):
        assert str(instance / ".providers.toml") in refusal
        assert COPY_COMMAND in refusal
    assert not state.exists()


def test_a_forced_start_without_the_file_starts(tmp_path):
    """CP-487: the same instance with `--provider codex` starts; the file is not read."""
    instance = _instance_with_one_change(tmp_path)
    (instance / ".providers.toml").unlink()
    state = instance / "system" / "logs" / "state.json"

    code = cd.main(["--start", str(state), "--instance-root", str(instance),
                    "--product-path", str(tmp_path / "product"), "--project", PROJECT,
                    "--core-dir", str(tmp_path / "no-core"), "--shim-dir", str(state.parent),
                    "--provider", "codex"])

    assert code == 0
    assert json.loads(state.read_text())["forced_provider"] == "codex"


def test_a_step_launch_reads_the_instance_file_as_edited_after_the_start():
    """CP-484: a step's provider follows an edit made after the start."""
    walk = Walk(through="specs")
    walk.provider_port.text = edited_text({"steps.plan": "claude"})
    land(walk.files, walk.git, "design")

    walk.advance("design")

    assert walk.skills_launched[-1] == "development-plan"
    assert _launch_provider(walk.processes, -1) == "claude"


def test_a_step_launch_halts_when_the_instance_file_is_gone():
    """CP-486: removed after the start, the file halts the walk at the step, naming the copy
    command, and nothing is launched."""
    walk = Walk(through="specs")
    launched = len(walk.processes.calls)
    walk.provider_port.text = None
    land(walk.files, walk.git, "design")

    walk.advance("design")

    assert len(walk.processes.calls) == launched
    assert walk.state["ended"] == "halted"
    assert COPY_COMMAND in walk.state["ended_reason"]
    assert walk.state["pending"] == {}


def test_a_copy_sets_design_and_audit_independently():
    """CP-276, CP-274 (Ex 4 and 6, the development half)."""
    copy = edited_text({"steps.design": "codex", "steps.audit": "gemini"})

    design = _started_at("design", cd.DEVELOPMENT_STEPS, provider_port=ProviderText(copy))
    audits = _started_at("audit", cd.DEVELOPMENT_STEPS, provider_port=ProviderText(copy))
    seal = _started_at("seal", cd.DEVELOPMENT_STEPS, provider_port=ProviderText(copy))

    assert _launch_provider(design) == "codex"
    assert len(audits.calls) == 4
    assert {call["env"]["KENSAIAPP_AGENT_PROVIDER"] for call in audits.calls} == {"gemini"}
    assert _launch_provider(seal) == "claude"


def test_an_entry_removed_before_a_launch_halts_the_walk_naming_it():
    """CP-283 (Ex 16): each launch reads the file as it stands; a launch whose entry has gone is
    not made, and the walk stops saying which entry."""
    walk = Walk(through="specs")
    launched = len(walk.processes.calls)
    walk.provider_port.text = edited_text({"steps.plan": None})
    land(walk.files, walk.git, "design")

    walk.advance("design")

    assert len(walk.processes.calls) == launched
    assert walk.state["ended"] == "halted"
    assert "steps.plan" in walk.state["ended_reason"]
    assert walk.state["pending"] == {}
    assert "steps.plan" in walk.notifier.messages[-1]


def test_a_valid_edit_is_taken_at_the_next_launch():
    """CP-283 (Ex 17): `seal` set to codex after the walk started puts seal on codex."""
    walk = Walk(through="code-integrity")
    walk.provider_port.text = edited_text({"steps.seal": "codex"})
    for audited in step("audit").fans_out_over:
        land(walk.files, walk.git, "audit", audited)
        walk.advance(f"audit-{audited}")

    assert walk.skills_launched[-1] == "tobiishi-seal"
    assert _launch_provider(walk.processes, -1) == "codex"


def test_an_audit_fan_out_reads_once():
    """Design §4 D: the four audit runs of one fan-out take one read, so a refusal cannot fall
    between two of them — here the file changes after that read, and no run sees the change."""
    walk = Walk(through="implementation")
    land(walk.files, walk.git, "code-integrity")
    before, reads = len(walk.processes.calls), walk.provider_port.reads
    walk.provider_port.then = [edited_text({"steps.audit": "gemini"})]

    walk.advance("code-integrity")

    audits = walk.processes.calls[before:]
    assert len(audits) == 4
    assert {call["env"]["KENSAIAPP_AGENT_PROVIDER"] for call in audits} == {"claude"}
    assert walk.provider_port.reads == reads + 1


@pytest.mark.parametrize("text, named", [
    (edited_text({"steps.plan": "grok"}), ["steps.plan", "'grok'"]),
    (None, [INSTANCE_PROVIDER_FILE]),
    ("[steps", [INSTANCE_PROVIDER_FILE]),
])
def test_a_provider_file_becoming_invalid_halts_before_the_next_step(text, named):
    """CP-283: invalid values, lost files and invalid TOML stop the next launch by name."""
    walk = Walk(through="specs")
    launched = len(walk.processes.calls)
    walk.provider_port.text = text
    land(walk.files, walk.git, "design")

    walk.advance("design")

    assert len(walk.processes.calls) == launched
    assert walk.state["ended"] == "halted"
    assert walk.state["pending"] == {}
    assert all(part in walk.state["ended_reason"] for part in named)
    assert all(part in walk.notifier.messages[-1] for part in named)


@pytest.mark.parametrize("forced", ["claude", "codex", "gemini"])
@pytest.mark.parametrize("step_id", [step.id for step in cd.CHANGE_STEPS])
def test_every_step_can_be_forced_without_a_provider_file(step_id, forced):
    """CP-285 and CP-290(c): the force covers every member, including all fan-out runs."""
    disk, git = _entering_at(step_id, cd.CHANGE_STEPS)
    port, processes = ProviderText(None), FakeProcesses()
    engine = build(FakeFiles(disk), git=git, processes=processes, steps=cd.CHANGE_STEPS,
                   provider_port=port)

    start(engine, forced_provider=forced)

    assert processes.calls
    assert {call["env"]["KENSAIAPP_AGENT_PROVIDER"] for call in processes.calls} == {forced}
    assert port.reads == 0


def test_an_environment_provider_never_reaches_a_launch():
    """CP-284: the engine's environment is the previous run's, so the variable it holds is never
    this step's provider."""
    processes = FakeProcesses()

    start(build(FakeFiles(fresh_change()), processes=processes,
                environ={"PATH": "/usr/bin", "KENSAIAPP_AGENT_PROVIDER": "gemini"}))

    assert _launch_provider(processes) == "claude"


def test_a_step_the_file_moves_is_launched_on_it_and_a_force_beats_it():
    copy = ProviderText(edited_text({"steps.specs": "codex"}))
    own, forced = FakeProcesses(), FakeProcesses()

    start(build(FakeFiles(fresh_change()), processes=own, provider_port=copy))
    start(build(FakeFiles(fresh_change()), processes=forced, provider_port=copy),
          forced_provider="gemini")

    assert _launch_provider(own) == "codex"
    assert _launch_provider(forced) == "gemini"


def test_a_forced_provider_is_kept_on_the_state_and_reaches_a_later_step():
    walk = Walk(through="plan", forced_provider="codex")
    land(walk.files, walk.git, "implementation")

    build(walk.files, git=walk.git, processes=walk.processes, notifier=walk.notifier,
          lock=walk.lock, environ={"PATH": "/usr/bin"}).advance("implementation", "completed")

    assert saved(walk.files)["forced_provider"] == "codex"
    assert _launch_provider(walk.processes, -1) == "codex"


def test_a_state_written_before_the_force_existed_loads_unforced():
    state = cd.WalkState(instance_root=INSTANCE, product_path=PRODUCT, project=PROJECT,
                         core_dir=CORE, shim_dir=LOGS, engine_path=ENGINE, key=KEY,
                         walk_id="walk-1", product_docs=f"{PRODUCT}/docs",
                         forced_provider="codex")

    assert cd.WalkState.from_json(state.to_json()).forced_provider == "codex"

    older = state.to_json()
    del older["forced_provider"]
    assert cd.WalkState.from_json(older).forced_provider == ""


def test_main_records_the_forced_provider_from_the_cli(tmp_path):
    code, state = _start_through_main(tmp_path, "--provider", "codex")

    assert code == 0
    assert json.loads(state.read_text())["forced_provider"] == "codex"


def test_main_records_no_force_when_none_is_given(tmp_path):
    code, state = _start_through_main(tmp_path)

    assert code == 0
    assert json.loads(state.read_text())["forced_provider"] == ""


def test_main_refuses_a_provider_it_does_not_know(tmp_path, capsys):
    with pytest.raises(SystemExit) as refused:
        _start_through_main(tmp_path, "--provider", "grok")

    assert refused.value.code != 0
    assert "--provider" in capsys.readouterr().err


# --- direct identity: every launch carries its role, an audit its producer target -------------


def test_a_producer_launch_carries_role_without_audit_target():
    """A representative producer launch (implementation, entered once plan has landed) carries
    its own direct role and no audit target; the existing chain and walk values are unaffected
    (CP-1, CP-2, CP-4, CP-5)."""
    files, git = _through("plan")
    processes = FakeProcesses()

    start(build(FakeFiles(files), git=git, processes=processes))

    env = processes.calls[0]["env"]
    assert env["INSTRUMENT_RUN_ROLE"] == "developer"
    assert "INSTRUMENT_RUN_AUDIT_TARGET" not in env
    assert env["INSTRUMENT_RUN_CHAIN"] == "development"
    assert env["INSTRUMENT_RUN_WALK_ID"] == "walk-1"


def test_each_audit_launch_carries_auditor_role_and_its_producer_target():
    """The four audit fan-out launches all carry the auditor role and each its own direct
    producer target (CP-1, CP-3, CP-4)."""
    files, git = _through("code-integrity")
    processes = FakeProcesses()

    start(build(FakeFiles(files), git=git, processes=processes))

    envs_by_target = {call["argv"][-1]: call["env"] for call in processes.calls}
    assert set(envs_by_target) == set(PRODUCERS)
    for producer, env in envs_by_target.items():
        assert env["INSTRUMENT_RUN_ROLE"] == "kensaiapp-auditor"
        assert env["INSTRUMENT_RUN_AUDIT_TARGET"] == producer


def test_code_integrity_and_seal_carry_their_roles():
    """The two non-producer, non-audit pipeline runs carry their own role and no audit target —
    completing the every-launch contract (CP-1, CP-4)."""
    files, git = _through("implementation")
    processes = FakeProcesses()
    start(build(FakeFiles(files), git=git, processes=processes))
    code_integrity_env = processes.calls[0]["env"]
    assert code_integrity_env["INSTRUMENT_RUN_ROLE"] == "senior-engineer"
    assert "INSTRUMENT_RUN_AUDIT_TARGET" not in code_integrity_env

    files, git = _through("code-integrity")
    processes = FakeProcesses(codes=[1, 1, 1, 1, 0])
    start(build(FakeFiles(files), git=git, processes=processes))
    assert processes.launched[-1] == [SKILL_LAUNCHER, "tobiishi-seal", PROJECT, KEY]
    seal_env = processes.calls[-1]["env"]
    assert seal_env["INSTRUMENT_RUN_ROLE"] == "pm"
    assert "INSTRUMENT_RUN_AUDIT_TARGET" not in seal_env


def test_launch_argv_is_unchanged_by_telemetry_identity():
    """Identity is not added as a positional argument — the launcher's argv keeps its existing
    skill/project/key/optional-audited shape (CP-2, CP-4)."""
    processes = FakeProcesses()
    start(build(FakeFiles(fresh_change()), processes=processes))
    assert processes.launched == [[SKILL_LAUNCHER, "development-specs", PROJECT]]

    files, git = _through("code-integrity")
    processes = FakeProcesses()
    start(build(FakeFiles(files), git=git, processes=processes))
    assert processes.launched == [
        [SKILL_LAUNCHER, "development-audit", PROJECT, KEY, skill] for skill in PRODUCERS]


@pytest.mark.parametrize("landed_through, skill, role", [
    (None, "development-specs", "product-owner"),
    ("specs", "development-design", "architect"),
    ("design", "development-plan", "tech-lead"),
])
def test_every_other_producer_launch_carries_its_role_without_audit_target(
        landed_through, skill, role):
    """Integrity review — the spec's first example ("A `development-specs` run in a chain walk:
    its records carry `kensai.role=product-owner` and no `kensai.audit_target`") and the rest of
    CP-1's every-launch contract: the three producers the representative-launch test does not
    reach, each on its own launch environment (CP-1, CP-4)."""
    files, git = _through(landed_through)
    processes = FakeProcesses()

    start(build(FakeFiles(files), git=git, processes=processes))

    assert processes.launched[0][1] == skill
    env = processes.calls[0]["env"]
    assert env["INSTRUMENT_RUN_ROLE"] == role
    assert "INSTRUMENT_RUN_AUDIT_TARGET" not in env


def test_an_audit_target_the_engine_inherited_never_reaches_a_non_audit_launch():
    """Integrity review — CP-4, "A non-audit run carries no `kensai.audit_target`". The seal is
    launched by the `--advance` the last audit's shim fires, and that process inherits the audit
    launch's own environment: `_launch_run` hands it to the launcher, `watch_agent.py`
    `run_on_complete_hook` runs the shim with no `env=`, the shim `nohup`s the engine, and
    `build_chain` reads `os.environ`. So the engine's environ holds that audit's
    `INSTRUMENT_RUN_AUDIT_TARGET`, and the seal must not pass it on — the same leak
    `test_chain.py` pins for an inherited walk key."""
    walk = Walk(through="code-integrity")
    for skill in PRODUCERS[:3]:
        land(walk.files, walk.git, "audit", skill)
        walk.advance(f"audit-{skill}")
    last = PRODUCERS[3]
    land(walk.files, walk.git, "audit", last)
    inherited = {"PATH": "/usr/bin", "INSTRUMENT_RUN_CHAIN": "development",
                 "INSTRUMENT_RUN_WALK_ID": "walk-1", "INSTRUMENT_RUN_ROLE": "kensaiapp-auditor",
                 "INSTRUMENT_RUN_AUDIT_TARGET": last}

    build(walk.files, git=walk.git, processes=walk.processes, notifier=walk.notifier,
          lock=walk.lock, environ=inherited).advance(f"audit-{last}", "completed")

    assert walk.processes.launched[-1] == [SKILL_LAUNCHER, "tobiishi-seal", PROJECT, KEY]
    seal_env = walk.processes.calls[-1]["env"]
    assert seal_env["INSTRUMENT_RUN_ROLE"] == "pm"
    assert "INSTRUMENT_RUN_AUDIT_TARGET" not in seal_env


def test_the_pending_run_is_on_disk_before_its_launcher_runs():
    """A crash between the save and the launch leaves a file the next call can act on; the
    reverse order leaves a run nobody is waiting for."""
    files = FakeFiles(fresh_change())
    seen = []
    processes = FakeProcesses(on_run=lambda argv: seen.append(saved(files)["pending"]))

    start(build(files, processes=processes))

    assert seen == [{"specs": {"step": "specs", "audited": None,
                               "identity": identity_file("specs"), "checkout_before": []}}]


def test_the_shim_detaches_the_engine_so_the_hooks_timeout_cannot_cut_a_fan_out_short():
    """`watch_agent.py` runs the hook under `timeout=60` with its output captured. After
    code-integrity one advance launches four audits, so the engine must outlive that bound —
    and its output must not ride the captured pipe, or `subprocess.run` waits on it anyway."""
    files = FakeFiles(fresh_change())

    start(build(files))

    shim = f"{LOGS}/chain-development-{PROJECT}-specs.sh"
    text = files.files[shim]
    assert shim in files.executable
    assert f"nohup python3 {ENGINE} --advance {STATE} specs \"$1\"" in text
    assert "</dev/null" in text
    assert f">>{LOGS}/chain-development-{PROJECT}.log 2>&1 &" in text


def test_the_development_shim_is_the_owners_rendering():
    files = FakeFiles(fresh_change())

    start(build(files))

    assert files.files[f"{LOGS}/chain-development-{PROJECT}-specs.sh"] == completion_shim.shim_text(
        ENGINE, ("--advance", STATE, "specs"), f"{LOGS}/chain-development-{PROJECT}.log")


def test_the_development_shim_preserves_its_pre_extraction_bytes():
    files = FakeFiles(fresh_change())

    start(build(files))

    assert files.files[f"{LOGS}/chain-development-{PROJECT}-specs.sh"] == (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f'nohup python3 {ENGINE} --advance {STATE} specs "$1" </dev/null '
        f">>{LOGS}/chain-development-{PROJECT}.log 2>&1 &\n"
    )


def test_the_walk_records_the_key_the_product_docs_and_the_walk_id():
    files = FakeFiles(fresh_change())

    start(build(files))

    state = saved(files)
    assert state["key"] == KEY
    assert state["product_docs"] == f"{PRODUCT}/docs"
    assert state["walk_id"] == "walk-1"
    assert state["ended"] is None


def test_starting_announces_the_change_and_the_step_it_enters_at_once():
    notifier = FakeNotifier()

    start(build(FakeFiles(fresh_change()), notifier=notifier))

    assert len(notifier.messages) == 1
    assert KEY in notifier.messages[0] and "specs" in notifier.messages[0]


def test_starting_marks_the_walk_in_the_chain_log():
    """The shims append every later advance to the same log, and one project's walks follow each
    other there — so without this line one walk's last advance reads as the next walk's first."""
    log = FakeWalkLog()

    start(build(FakeFiles(fresh_change()), log=log), started_at="2026-09-17T08:10:38+00:00")

    assert log.lines == [(f"{LOGS}/chain-development-{PROJECT}.log",
                          f"chain_development: started walk=walk-1 change={KEY} entry=specs "
                          f"at=2026-09-17T08:10:38+00:00")]


def test_the_start_line_names_the_step_the_walk_enters_at():
    files, git = _through("plan")
    log = FakeWalkLog()

    start(build(FakeFiles(files), git=git, log=log))

    assert " entry=implementation " in log.lines[0][1]


def test_a_refused_start_writes_nothing_to_the_chain_log():
    files = FakeFiles(fresh_change())
    start(build(files))
    log = FakeWalkLog()

    with pytest.raises(cd.ChainAlreadyWalking):
        start(build(files, log=log))

    assert log.lines == []


def test_the_walk_log_appends_a_line_and_keeps_what_was_there(tmp_path):
    path = tmp_path / "logs" / "chain.log"

    cd.WalkLog().append(str(path), "one")
    cd.WalkLog().append(str(path), "two")

    assert path.read_text() == "one\ntwo\n"


def test_starting_holds_the_state_lock():
    lock = FakeLock()

    start(build(FakeFiles(fresh_change()), lock=lock))

    assert lock.holds == [STATE]


def test_a_launcher_that_exits_non_zero_stops_the_walk_with_one_message():
    files = FakeFiles(fresh_change())
    notifier = FakeNotifier()

    start(build(files, processes=FakeProcesses(codes=[3]), notifier=notifier))

    state = saved(files)
    assert state["ended"] == "halted"
    assert "launcher exited 3" in state["ended_reason"]
    assert state["pending"] == {}
    assert len(notifier.messages) == 2
    assert "stopped at specs" in notifier.messages[1]


def test_a_live_walk_on_the_same_project_is_never_overwritten():
    files = FakeFiles(fresh_change())
    start(build(files))
    processes = FakeProcesses()

    with pytest.raises(cd.ChainAlreadyWalking):
        start(build(files, processes=processes))
    assert processes.launched == []


def test_an_ended_walk_does_not_block_a_new_one():
    files = FakeFiles(fresh_change())
    start(build(files, processes=FakeProcesses(codes=[1])))
    processes = FakeProcesses()

    start(build(files, processes=processes))

    assert processes.launched == [[SKILL_LAUNCHER, "development-specs", PROJECT]]


def test_no_active_change_refuses_before_writing_or_launching_anything():
    files = FakeFiles()
    processes = FakeProcesses()

    with pytest.raises(cd.ChainRefused):
        start(build(files, processes=processes))
    assert processes.launched == []
    assert STATE not in files.files


# --- the audit fan-out, entered at start ----------------------------------------------------


def test_after_code_integrity_all_four_audits_launch_one_per_producer_step():
    files, git = _through("code-integrity")
    processes = FakeProcesses()
    engine_files = FakeFiles(files)

    start(build(engine_files, git=git, processes=processes))

    assert processes.launched == [
        [SKILL_LAUNCHER, "development-audit", PROJECT, KEY, skill] for skill in PRODUCERS]
    assert set(saved(engine_files)["pending"]) == {f"audit-{skill}" for skill in PRODUCERS}


def test_an_audit_launcher_failing_is_recorded_and_never_halts():
    files, git = _through("code-integrity")
    engine_files = FakeFiles(files)

    start(build(engine_files, git=git, processes=FakeProcesses(codes=[0, 5, 0, 0])))

    state = saved(engine_files)
    assert state["ended"] is None
    assert len(state["pending"]) == 3
    assert state["audits"]["development-design"] == "launcher exited 5"


def test_when_every_audit_launcher_fails_the_seal_still_starts():
    files, git = _through("code-integrity")
    processes = FakeProcesses(codes=[1, 1, 1, 1, 0])

    start(build(FakeFiles(files), git=git, processes=processes))

    assert processes.launched[-1] == [SKILL_LAUNCHER, "tobiishi-seal", PROJECT, KEY]


# --- describing a start without making one ------------------------------------------------------
#
# What `--dry-run` asks. The answer is only worth having if it is the answer `start` would act on,
# so both read one set of checks — and a describe that wrote, launched, locked or spoke would be a
# start by another name.


def describe(engine):
    return engine.describe(instance_root=INSTANCE, project=PROJECT)


@pytest.mark.parametrize("landed_through, entry", [
    (None, "specs"),
    ("specs", "design"),
    ("plan", "implementation"),
    ("code-integrity", "audit"),
    ("audit", "seal"),
])
def test_describe_names_the_change_and_the_step_a_start_would_enter_at(landed_through, entry):
    files, git = _through(landed_through)

    plan = describe(build(FakeFiles(files), git=git))

    assert plan.key == KEY
    assert plan.entry == entry


@pytest.mark.parametrize("landed_through", [None, "plan", "code-integrity", "audit"])
def test_describe_and_start_agree_on_where_the_walk_enters(landed_through):
    files, git = _through(landed_through)
    processes = FakeProcesses()

    planned = describe(build(FakeFiles(files), git=git))
    start(build(FakeFiles(files), git=git, processes=processes))

    entered = next(entry for entry in cd.DEVELOPMENT_STEPS if entry.skill == processes.launched[0][1])
    assert entered.id == planned.entry


def test_describe_refuses_when_there_is_no_active_change():
    with pytest.raises(cd.ChainRefused, match="no active change"):
        describe(build(FakeFiles()))


def test_describe_refuses_two_active_changes():
    files = FakeFiles({f"{TOBIISHI}/{KEY}/change_request.md": "one",
                       f"{TOBIISHI}/2026-09-16_other/change_request.md": "two"})

    with pytest.raises(cd.ChainRefused, match="more than one active change"):
        describe(build(files))


def test_describe_refuses_a_change_that_is_already_sealed():
    files, git = _through("audit")
    files[f"{TOBIISHI}/trail/{KEY}/change_request.md"] = "sealed"

    with pytest.raises(cd.ChainRefused, match="already sealed"):
        describe(build(FakeFiles(files), git=git))


def test_describe_refuses_while_a_walk_is_live_and_so_does_start():
    files = FakeFiles(fresh_change())
    start(build(files))

    with pytest.raises(cd.ChainAlreadyWalking):
        describe(build(files))
    with pytest.raises(cd.ChainAlreadyWalking):
        start(build(files))


def test_describe_writes_launches_locks_and_says_nothing():
    files = FakeFiles(fresh_change())
    before = dict(files.files)
    processes, notifier, lock, log = FakeProcesses(), FakeNotifier(), FakeLock(), FakeWalkLog()

    describe(build(files, processes=processes, notifier=notifier, lock=lock, log=log))

    assert files.files == before
    assert log.lines == []
    assert files.executable == set()
    assert processes.calls == []
    assert notifier.messages == []
    assert lock.holds == []


# --- advancing on a run's end -------------------------------------------------------------------


def land(files: FakeFiles, git: FakeGit, step_id: str, audited: str | None = None) -> None:
    """Put on the disk exactly what that step leaves when it succeeds."""
    artifacts = {"specs": "change_spec.md", "design": "change_design.md",
                 "plan": "tl_instruction.md", "content": "change_text.md",
                 "code-integrity": "code-integrity-report.md"}
    if step_id in artifacts:
        content = {"code-integrity": PASSING_REPORT, "design": NO_TEXT_DESIGN}.get(step_id,
                                                                                      "x")
        files.write_text(f"{BRANCH_CHANGE}/{artifacts[step_id]}", content)
    elif step_id == "implementation":
        git.commits.setdefault(KEY, []).append(MARKER)
        git.bodies[MARKER[0]] = MARKER_BODY
    elif step_id == "audit":
        git.paths.setdefault(f"{KEY}__audit-{audited}", set()).add(
            f"{CHANGE_REL}/flow_findings/{audited}.md")
    elif step_id == "seal":
        files.write_text(f"{TOBIISHI}/trail/{KEY}/change_request.md", "sealed")


class Walk:
    """One engine over one scripted disk, started at whatever step the disk says."""

    # The table the engine walks; `None` is the development table. A class default, because
    # some walks are assembled without `__init__`.
    steps = None
    # The provider file's port; `None` is a fresh copy of the delivered file.
    provider_port = None
    # The process port every engine of this walk is handed; `None` is a fresh one per engine.
    table = None
    # The product checkout's port every engine of this walk reads; `None` is a checkout that never
    # changes.
    checkout = None

    def __init__(self, through: str | None = None, codes=None, product_path: str = PRODUCT,
                 steps=None, provider_port=None, table=None, checkout=None, **start_arguments):
        disk, git = _through(through)
        self.files = FakeFiles(disk)
        self.git = git
        self.processes = FakeProcesses(codes=codes)
        self.notifier = FakeNotifier()
        self.lock = FakeLock()
        self.steps = steps
        self.table = table or FakeProcessTable()
        self.checkout = checkout or FakeCheckout()
        # The provider file every engine of this walk reads; a test edits its `text` mid-walk.
        self.provider_port = provider_port or ProviderText()
        start(self.engine(), product_path=product_path, **start_arguments)

    def engine(self):
        return build(self.files, git=self.git, processes=self.processes, notifier=self.notifier,
                     lock=self.lock, steps=self.steps, provider_port=self.provider_port,
                     process_table=self.table, checkout=self.checkout)

    def advance(self, run: str, outcome: str = "completed"):
        return self.engine().advance(run, outcome)

    @property
    def state(self) -> dict:
        return saved(self.files)

    @property
    def skills_launched(self) -> list[str]:
        return [argv[1] for argv in self.processes.launched]


def test_a_landed_artifact_launches_the_next_step_with_the_key():
    walk = Walk()
    land(walk.files, walk.git, "specs")

    result = walk.advance("specs")

    assert result.acted is True
    assert walk.processes.launched[-1] == [SKILL_LAUNCHER, "development-design", PROJECT, KEY]
    assert walk.state["pending"] == {"design": {"step": "design", "audited": None,
                                                "identity": identity_file("design"),
                                                "checkout_before": []}}


def test_produced_nothing_is_read_as_a_finished_run_and_the_disk_decides():
    """The watcher says PRODUCED_NOTHING when the instance root's HEAD did not move — and every
    step commits inside `.worktrees/<key>`, so a step that did its whole job can read that way."""
    walk = Walk()
    land(walk.files, walk.git, "specs")

    walk.advance("specs", "produced_nothing")

    assert walk.skills_launched[-1] == "development-design"


@pytest.mark.parametrize("outcome", ["timeout", "vanished", "appear_error", "something-new"])
def test_a_run_that_did_not_finish_stops_the_walk_whatever_is_on_disk(outcome):
    walk = Walk()
    land(walk.files, walk.git, "specs")

    walk.advance("specs", outcome)

    assert walk.state["ended"] == "halted"
    assert f"the run ended {outcome}" in walk.state["ended_reason"]
    assert walk.skills_launched == ["development-specs"]


def test_a_finished_run_with_no_artifact_and_no_report_stops_naming_what_is_missing():
    walk = Walk()

    walk.advance("specs")

    assert walk.state["ended"] == "halted"
    assert "no change_spec.md" in walk.state["ended_reason"]


def test_a_finished_run_that_left_a_halt_report_stops_pointing_at_it():
    walk = Walk()
    report = f"{TOBIISHI}/{KEY}/halt_report.md"
    walk.files.write_text(report, "fdr-conflict")

    walk.advance("specs")

    assert walk.state["ended"] == "halted"
    assert report in walk.state["ended_reason"]
    assert report in walk.notifier.messages[-1]


def test_the_artifact_wins_over_a_halt_report_an_earlier_run_left_behind():
    """A pre-worktree halt report stays on main after the owner fixes the change and starts
    again; reading it first would stop every later walk at a step that has since succeeded."""
    walk = Walk()
    walk.files.write_text(f"{TOBIISHI}/{KEY}/halt_report.md", "an earlier halt")
    land(walk.files, walk.git, "specs")

    walk.advance("specs")

    assert walk.state["ended"] is None
    assert walk.skills_launched[-1] == "development-design"


def test_a_red_suite_on_the_marker_halts_the_walk():
    """CP-1: the marker's body declares `Suite: red` — the walk ends halted rather than
    reading the marker's mere presence as green."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = "Suite: red\n\nLanguage resolution:\n- python\n"

    walk.advance("implementation")

    assert walk.state["ended"] == "halted"
    assert "stopped at implementation: red-suite" in walk.state["ended_reason"]


def test_a_marker_with_no_suite_line_halts_as_missing():
    """CP-2: the marker's body carries a `Language resolution:` line and no `Suite:` line —
    a distinct halt from `red-suite`, because nothing declared a verdict at all."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = "Language resolution:\n- python\n"

    walk.advance("implementation")

    assert "stopped at implementation: missing-suite" in walk.state["ended_reason"]
    assert "red-suite" not in walk.state["ended_reason"]


def test_a_green_suite_on_the_marker_records_it_and_goes_on():
    """CP-4's suite half: `Suite: green` plus a `Language resolution:` line — the walk
    records the verdict and proceeds, rather than halting on it."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")

    walk.advance("implementation")

    assert walk.state["suite"] == "green"
    assert walk.state["marker"] == "a1b2c3"
    assert walk.state["ended"] is None
    assert walk.skills_launched[-1] == "development-code-integrity"


CARD = f"{INSTANCE}/system/projects/{PROJECT}/project.md"
BRANCH_CARD = f"{WORKTREE}/system/projects/{PROJECT}/project.md"
_NO_SUITE_MARKER = ("Suite: none\n\nLanguage resolution:\n- none — no language on the card\n\n"
                    "Environment: none — no suite\n")


@pytest.mark.parametrize("card_line", [
    "**Test command:** none\n",
    "**Test command:** `none`       <!-- a product with no code -->\n",
    "**Test command:** None\n",
])
def test_a_no_suite_marker_on_a_card_with_no_command_goes_on(card_line):
    """A product with no code has no suite. Its card says `Test command: none`, the developer
    declares `Suite: none`, and the walk records that and goes on rather than halting."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = _NO_SUITE_MARKER
    walk.files.write_text(CARD, "# Project Context — tracker\n\n" + card_line)

    walk.advance("implementation")

    assert walk.state["suite"] == "none"
    assert walk.state["ended"] is None
    assert walk.skills_launched[-1] == "development-code-integrity"


@pytest.mark.parametrize("card", [
    "# Project Context — tracker\n\n**Test command:** pytest tests/\n",
    "# Project Context — tracker\n\n**Test command:** pytest tests/   <!-- none of these -->\n",
    "# Project Context — tracker\n\n**Test command:**\n",
    "# Project Context — tracker\n\n**Test command:** none yet — set once the SDD settles\n",
    None,
], ids=["a-command", "none-only-in-the-comment", "blank", "a-stand-in", "no-card"])
def test_a_no_suite_marker_on_a_card_naming_a_command_halts_as_missing(card):
    """`Suite: none` is not a way past a red suite. Where the card names a command — or no card
    can be read — the declaration counts for nothing, and the walk halts `missing-suite`."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = _NO_SUITE_MARKER
    if card is not None:
        walk.files.write_text(CARD, card)

    walk.advance("implementation")

    assert "stopped at implementation: missing-suite" in walk.state["ended_reason"]


@pytest.mark.parametrize("main_card, branch_card, reason", [
    ("**Test command:** pytest tests/\n", "**Test command:** none\n", "missing-suite"),
    ("**Test command:** none\n", "**Test command:** pytest tests/\n", None),
], ids=["the-branch-says-none", "main-says-none-after-the-branch-was-cut"])
def test_the_card_that_allows_no_suite_is_mains_not_the_branchs(main_card, branch_card, reason):
    """The card is settled on `main`. A branch cut before that still says `pytest tests/`, and a
    developer run can edit the branch's card, so only `main`'s copy decides whether `Suite: none`
    passes."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = _NO_SUITE_MARKER
    walk.files.write_text(CARD, main_card)
    walk.files.write_text(BRANCH_CARD, branch_card)

    walk.advance("implementation")

    if reason is None:
        assert walk.state["ended"] is None
    else:
        assert f"stopped at implementation: {reason}" in walk.state["ended_reason"]


def test_a_marker_with_no_language_resolution_halts_the_walk():
    """CP-3: the marker's body declares `Suite: green` and carries no `Language resolution:`
    line — checked after the suite, so a green suite does not mask a missing language read."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = "Suite: green\n"

    walk.advance("implementation")

    assert "stopped at implementation: missing-language" in walk.state["ended_reason"]


def test_a_marker_missing_both_lines_reports_the_suite_first():
    """CP-5: neither line is present — the walk reports `missing-suite`, not
    `missing-language`, because the suite is read first."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = "Developer Review Notes:\n- nothing declared\n"

    walk.advance("implementation")

    assert "missing-suite" in walk.state["ended_reason"]
    assert "missing-language" not in walk.state["ended_reason"]


def test_a_suite_line_declaring_nothing_halts_as_missing():
    """CP-2 again, at the other shape an absent verdict takes: the `Suite:` line is there and
    declares no value. What CP-2 calls absent is the *verdict*, not the line — a marker whose
    line says nothing has told the chain nothing, so it halts the same way."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = "Suite:\n\nLanguage resolution:\n- python\n"

    walk.advance("implementation")

    assert "stopped at implementation: missing-suite" in walk.state["ended_reason"]


def test_a_verdict_that_is_not_green_never_takes_the_green_path():
    """CP-4 gates the green path on the marker carrying `Suite: green`. A word that is neither
    verdict was declared by nobody, so it must not seal: the walk halts, records no suite, and
    does not launch the next skill."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = "Suite: passed\n\nLanguage resolution:\n- python\n"

    walk.advance("implementation")

    assert walk.state["ended"] == "halted"
    assert "stopped at implementation" in walk.state["ended_reason"]
    assert walk.state["suite"] is None
    assert walk.skills_launched[-1] != "development-code-integrity"



@pytest.mark.parametrize("word", ["passed", "Green", "RED", "None"])
def test_a_word_that_is_neither_verdict_halts_as_missing_suite(word):
    """CP-7: only exactly `green`, `red` or `none` is a verdict. Anything else — a synonym, a different
    capitalisation of either word — was declared by nobody and is read as absent, so it names
    `missing-suite` rather than a reason of its own."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = f"Suite: {word}\n\nLanguage resolution:\n- python\n"

    walk.advance("implementation")

    assert "stopped at implementation: missing-suite" in walk.state["ended_reason"]


def test_a_red_suite_is_reported_even_where_the_language_line_is_missing():
    """CP-5 beyond the both-absent case: a red suite and a missing language resolution both
    apply, and the suite is decided first, so the reason is `red-suite` and never
    `missing-language`."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = "Suite: red\n"

    walk.advance("implementation")

    assert "stopped at implementation: red-suite" in walk.state["ended_reason"]
    assert "missing-language" not in walk.state["ended_reason"]


# --- a relaunch refuses on a bad verdict it would walk past (skipped-step verdict reads) ------


def _bad_verdict_cases() -> list[tuple[object, str]]:
    """One mutator per CP-13/14/15 case, paired with the halt reason `describe`/`start` must
    name for it. Each mutates a world already landed through `audit`, so every later step's
    own evidence is on disk and only the named verdict is bad."""

    def red_suite(files, git):
        git.bodies[MARKER[0]] = "Suite: red\n\nLanguage resolution:\n- python\n"

    def missing_suite(files, git):
        git.bodies[MARKER[0]] = "Language resolution:\n- python\n"

    def missing_language(files, git):
        git.bodies[MARKER[0]] = "Suite: green\n"

    def integrity_stopped(files, git):
        files[f"{BRANCH_CHANGE}/code-integrity-report.md"] = "Integrity: stopped\n"

    def missing_integrity(files, git):
        files[f"{BRANCH_CHANGE}/code-integrity-report.md"] = "no such line here\n"

    return [
        (red_suite, "stopped at implementation: red-suite"),
        (missing_suite, "stopped at implementation: missing-suite"),
        (missing_language, "stopped at implementation: missing-language"),
        (integrity_stopped, "stopped at code-integrity: integrity-stopped"),
        (missing_integrity, "stopped at code-integrity: missing-integrity"),
    ]


_BAD_VERDICT_CASES = _bad_verdict_cases()
_BAD_VERDICT_IDS = ["red-suite", "missing-suite", "missing-language", "integrity-stopped",
                    "missing-integrity"]


def _bad_verdict_world(make_bad):
    """A world through `audit` with one verdict made bad by `make_bad`."""
    files, git = _through("audit")
    make_bad(files, git)
    return files, git


@pytest.mark.parametrize("make_bad, reason", _BAD_VERDICT_CASES, ids=_BAD_VERDICT_IDS)
def test_a_relaunch_refuses_on_a_bad_verdict_it_would_walk_past(make_bad, reason):
    """CP-13, CP-14: a world landed through `audit` — so every later step's evidence is on
    disk — with one verdict made bad. `start` refuses before writing, launching or messaging
    anything, and the file tree is exactly what it was before."""
    files, git = _bad_verdict_world(make_bad)
    disk = FakeFiles(files)
    before = dict(disk.files)
    processes, notifier = FakeProcesses(), FakeNotifier()

    with pytest.raises(cd.ChainRefused, match=reason):
        start(build(disk, git=git, processes=processes, notifier=notifier))

    assert disk.files == before
    assert processes.calls == []
    assert notifier.messages == []


def test_the_earliest_bad_verdict_is_the_one_a_refusal_names():
    """CP-15: both the marker and the report declare bad verdicts — the refusal names the
    earlier step in pipeline order, never the later one."""
    files, git = _through("audit")
    git.bodies[MARKER[0]] = "Suite: red\n"
    files[f"{BRANCH_CHANGE}/code-integrity-report.md"] = "Integrity: stopped\n"

    with pytest.raises(cd.ChainRefused,
                       match="stopped at implementation: red-suite") as excinfo:
        start(build(FakeFiles(files), git=git))

    assert "code-integrity" not in str(excinfo.value)


# Integrity review (development-code-integrity): the request's own scenario — "a walk relaunched
# on a branch that already carries a bad verdict should halt on it again" — where the walk really
# halted, so its state file is on disk and the next step's evidence is not: a red marker today
# enters at `code-integrity`, a stopped report at `audit` (change_request.md).
_HALTED_WALKS = [
    ("plan", "implementation", "Suite: red\n\nLanguage resolution:\n- python\n", "red-suite"),
    ("plan", "implementation", "Language resolution:\n- python\n", "missing-suite"),
    ("plan", "implementation", "Suite: green\n", "missing-language"),
    ("implementation", "code-integrity", "Integrity: stopped\n", "integrity-stopped"),
    ("implementation", "code-integrity", "no verdict here\n", "missing-integrity"),
]


@pytest.mark.parametrize("through, halted_at, declared, reason", _HALTED_WALKS,
                         ids=[case[3] for case in _HALTED_WALKS])
def test_a_walk_halted_on_a_bad_verdict_refuses_its_relaunch_and_keeps_its_state(
        through, halted_at, declared, reason):
    """CP-13, CP-14, Locked Answer Gap 1: the walk halts on the verdict at its step's end; the
    relaunch refuses with the same `stopped at <step>: <reason>`, launches nothing, sends
    nothing, and leaves the halted walk's own state file exactly as it was."""
    walk = Walk(through=through)
    land(walk.files, walk.git, halted_at)
    if halted_at == "implementation":
        walk.git.bodies[MARKER[0]] = declared
    else:
        walk.files.write_text(f"{BRANCH_CHANGE}/code-integrity-report.md", declared)
    walk.advance(halted_at)
    expected = f"stopped at {halted_at}: {reason}"
    assert walk.state["ended"] == "halted" and expected in walk.state["ended_reason"]
    state_before = walk.files.files[STATE]
    launched, messages = list(walk.processes.launched), list(walk.notifier.messages)

    with pytest.raises(cd.ChainRefused, match=expected):
        start(walk.engine())
    with pytest.raises(cd.ChainRefused, match=expected):
        describe(walk.engine())

    assert walk.files.files[STATE] == state_before
    assert walk.processes.launched == launched
    assert walk.notifier.messages == messages


@pytest.mark.parametrize("marker_body, report, reason", [
    ("Suite: Green\n\nLanguage resolution:\n- python\n", "Integrity: pass\n",
     "stopped at implementation: missing-suite"),
    (MARKER_BODY, "Integrity: passed\n", "stopped at code-integrity: missing-integrity"),
    (MARKER_BODY, "Integrity: stopped\n\nIntegrity: pass\n",
     "stopped at code-integrity: integrity-stopped"),
], ids=["suite-not-exactly-green", "integrity-not-exactly-pass", "first-integrity-line-wins"])
def test_a_relaunch_reads_a_verdict_exactly_as_declared(marker_body, report, reason):
    """CP-13: a `Suite:` value other than exactly `green`, `red` or `none` is `missing-suite`. CP-14: a
    value other than exactly `pass` or `stopped` is `missing-integrity`, and the report's
    first `Integrity:` line is the one read."""
    files, git = _through("audit")
    git.bodies[MARKER[0]] = marker_body
    files[f"{BRANCH_CHANGE}/code-integrity-report.md"] = report

    with pytest.raises(cd.ChainRefused, match=reason):
        start(build(FakeFiles(files), git=git))


def test_implementation_with_no_marker_stops_after_one_recovery_naming_the_marker():
    walk = Walk(through="plan")

    walk.advance("implementation")
    walk.advance("implementation-recovery")

    assert walk.state["ended"] == "halted"
    assert "closing marker" in walk.state["ended_reason"]


def test_a_second_delivery_of_the_same_end_does_nothing():
    walk = Walk()
    land(walk.files, walk.git, "specs")
    walk.advance("specs")

    result = walk.advance("specs")

    assert result.acted is False
    assert walk.skills_launched == ["development-specs", "development-design"]


def test_an_end_arriving_after_the_walk_ended_is_counted_and_ignored():
    walk = Walk()
    walk.advance("specs", "timeout")

    result = walk.advance("specs")

    assert result.acted is False
    assert walk.state["reentries"] == 1
    assert len(walk.notifier.messages) == 2


def test_advancing_holds_the_state_lock():
    walk = Walk()
    land(walk.files, walk.git, "specs")
    walk.lock.holds.clear()

    walk.advance("specs")

    assert walk.lock.holds == [STATE]


def test_code_integrity_landing_fans_out_the_four_audits():
    walk = Walk(through="implementation")
    land(walk.files, walk.git, "code-integrity")

    walk.advance("code-integrity")

    assert walk.skills_launched[-4:] == ["development-audit"] * 4
    assert set(walk.state["pending"]) == {f"audit-{skill}" for skill in PRODUCERS}


def test_a_declared_stop_halts_the_walk_at_code_integrity():
    """CP-8: the report declares `Integrity: stopped` — the walk halts before the audits fan
    out."""
    walk = Walk(through="implementation")
    walk.files.write_text(f"{BRANCH_CHANGE}/code-integrity-report.md", "Integrity: stopped\n")

    walk.advance("code-integrity")

    assert "stopped at code-integrity: integrity-stopped" in walk.state["ended_reason"]
    assert "development-audit" not in walk.skills_launched
    assert "tobiishi-seal" not in walk.skills_launched


@pytest.mark.parametrize("body", [
    "no such line here\n",
    "Integrity:\n",
    "Integrity: Pass\n",
    "Integrity: passed\n",
])
def test_a_verdict_the_chain_cannot_read_halts_as_missing(body):
    """CP-9: a report with no `Integrity:` line, one whose line declares no value, and a value
    that is neither exactly `pass` nor `stopped` — every one of these was declared by nobody
    and halts the same way, never raising on the typo."""
    walk = Walk(through="implementation")
    walk.files.write_text(f"{BRANCH_CHANGE}/code-integrity-report.md", body)

    walk.advance("code-integrity")

    assert "stopped at code-integrity: missing-integrity" in walk.state["ended_reason"]
    assert "development-audit" not in walk.skills_launched


def test_the_first_integrity_line_is_the_declaration():
    """CP-11: the report's top line declares `Integrity: stopped`; a later line beginning
    `Integrity: pass` does not overrule it — the first declared line wins, the same rule the
    closing marker's own scan already applies."""
    walk = Walk(through="implementation")
    walk.files.write_text(f"{BRANCH_CHANGE}/code-integrity-report.md",
                          "Integrity: stopped\n\nnotes\nIntegrity: pass\n")

    walk.advance("code-integrity")

    assert "stopped at code-integrity: integrity-stopped" in walk.state["ended_reason"]


def test_a_later_quoted_stop_does_not_overrule_a_declared_pass():
    """CP-11, the other direction: the report declares `Integrity: pass` and later quotes an
    earlier run's `Integrity: stopped` — the quote is not the declaration, so the audits fan out.
    A reader that halts on any `stopped` line anywhere passes the case above and fails this one."""
    walk = Walk(through="implementation")
    walk.files.write_text(f"{BRANCH_CHANGE}/code-integrity-report.md",
                          f"{PASSING_REPORT}\nthe earlier run declared\nIntegrity: stopped\n")

    walk.advance("code-integrity")

    assert walk.state["ended"] is None
    assert walk.skills_launched[-4:] == ["development-audit"] * 4


@pytest.mark.parametrize("body", [
    "**Integrity: pass**\n",
    "`Integrity: pass`\n",
    "*Integrity: pass*\n",
    "__Integrity: pass__\n",
], ids=["bold", "code", "italic", "underscores"])
def test_a_verdict_dressed_in_markdown_still_declares_itself(body):
    """A verdict the writer emphasised is still the verdict. The report is markdown and its
    author is a model writing prose, so `**Integrity: pass**` is the natural way to put a line
    that the skill itself only ever shows inside backticks — and it cost a real walk: a
    `chain-change` walk, 2026-09-17, whose green suite and passing report halted
    `missing-integrity`. The value is read past the wrapper, never the wrapper past the value."""
    walk = Walk(through="implementation")
    walk.files.write_text(f"{BRANCH_CHANGE}/code-integrity-report.md",
                          f"{body}\n{ENVIRONMENT_LINE}\n")

    walk.advance("code-integrity")

    assert walk.state["ended"] is None
    assert walk.skills_launched[-4:] == ["development-audit"] * 4


def test_emphasis_does_not_turn_a_stop_into_a_pass():
    """The other direction of the rule above: reading past the wrapper reads the STOP too. A
    normaliser that dropped the line instead of undressing it would pass the case above by
    halting nothing and fail here by halting `missing-integrity` rather than on the stop."""
    walk = Walk(through="implementation")
    walk.files.write_text(f"{BRANCH_CHANGE}/code-integrity-report.md", "**Integrity: stopped**\n")

    walk.advance("code-integrity")

    assert "stopped at code-integrity: integrity-stopped" in walk.state["ended_reason"]
    assert "development-audit" not in walk.skills_launched


def test_a_suite_verdict_followed_by_its_evidence_still_reads_as_the_verdict():
    """The developer writes the marker by hand and reaches for the evidence: twice in one day a
    marker carried `Suite: green — python3 -m pytest … 5083 passed` and halted the walk as
    missing-suite. The verdict is the value's first word; what follows it is the record."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = (
        "Suite: green — python3 -m pytest core/launchers/ -q, 5083 passed, 1 skipped\n\n"
        f"Language resolution:\n- python\n\n{ENVIRONMENT_LINE}\n")

    walk.advance("implementation")

    assert walk.state["ended"] is None
    assert walk.state["suite"] == "green"
    assert walk.skills_launched[-1] == "development-code-integrity"


def test_a_red_verdict_with_its_evidence_still_halts():
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = (
        "Suite: red — 2 failed, 3645 passed\n\nLanguage resolution:\n- python\n")

    walk.advance("implementation")

    assert walk.state["ended"] == "halted"


def test_a_dressed_marker_declares_its_suite_and_language_too():
    """One parser, two bodies — so the closing marker's own lines read past the same wrappers.
    The developer writes that body by hand and nothing stops them bolding it either."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = ("**Suite: green**\n\n**Language resolution:**\n- python\n\n"
                                  f"**{ENVIRONMENT_LINE}**\n")

    walk.advance("implementation")

    assert walk.state["ended"] is None
    assert walk.skills_launched[-1] == "development-code-integrity"


def test_a_labelled_language_heading_declares_the_language():
    """A close after pauses that carries each pause's record under its own label still declares
    the block — a satellite's close halted as missing-language on 2026-10-01 with both present."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = ("Suite: green\n\n"
                                  "Language resolution (tasks 1 to 3, from f6f9135):\n- python\n\n"
                                  "Language resolution (tasks 4 to 6, from 790cde6):\n- python\n"
                                  f"\n{ENVIRONMENT_LINE}\n")

    walk.advance("implementation")

    assert walk.state["ended"] is None
    assert walk.skills_launched[-1] == "development-code-integrity"


def test_a_language_mention_without_its_colon_is_not_the_declaration():
    """The label is the only thing allowed between the words and the colon, so a sentence in the
    notes that names the block still reads as no block."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = ("Suite: green\n\n"
                                  "Language resolution was carried from the pauses\n")

    walk.advance("implementation")

    assert "stopped at implementation: missing-language" in walk.state["ended_reason"]


def test_the_code_integrity_step_alone_declares_a_prefix():
    """The prefix lives on `Step`, set only on the code-integrity entry — not a branch on
    `step.id` inside `_settle`."""
    assert step("code-integrity").declared_prefix == cd._INTEGRITY_PREFIX
    assert all(entry.declared_prefix == "" for entry in cd.DEVELOPMENT_STEPS
               if entry.id != "code-integrity")


def _skill_section(text: str, heading: str) -> str:
    """The text of the section headed `heading`, cut at the next `## ` heading — so a match
    anywhere else in the file does not count."""
    start = text.index(heading) + len(heading)
    rest = text[start:]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def test_the_integrity_skill_declares_the_verdict_the_chain_reads():
    """CP-12: the skill's § *Always write the `code-integrity-report`* carries the chain's own
    prefix with both verdict words, and its § *When to STOP* says a STOP still writes
    `Integrity: stopped` — each read within its own section, so the form has one owner and the
    two files cannot drift apart."""
    text = (_REPO / "skills" / "senior-engineer" / ".claude" / "skills" / "development-code-integrity" / "SKILL.md").read_text(
        encoding="utf-8")

    report_section = _skill_section(text, "## Always write the `code-integrity-report`")
    assert f"{cd._INTEGRITY_PREFIX} pass" in report_section
    assert f"{cd._INTEGRITY_PREFIX} stopped" in report_section

    stop_section = _skill_section(text, "## When to STOP")
    assert f"{cd._INTEGRITY_PREFIX} stopped" in stop_section


def test_the_seal_waits_until_every_audit_run_has_ended():
    walk = Walk(through="code-integrity")
    for skill in PRODUCERS[:3]:
        land(walk.files, walk.git, "audit", skill)
        walk.advance(f"audit-{skill}")

    assert "tobiishi-seal" not in walk.skills_launched

    land(walk.files, walk.git, "audit", PRODUCERS[3])
    walk.advance(f"audit-{PRODUCERS[3]}")

    assert walk.processes.launched[-1] == [SKILL_LAUNCHER, "tobiishi-seal", PROJECT, KEY]


def test_an_audit_that_failed_or_wrote_nothing_is_recorded_and_never_stops_the_walk():
    walk = Walk(through="code-integrity")
    land(walk.files, walk.git, "audit", "development-specs")
    walk.advance("audit-development-specs")
    walk.advance("audit-development-design")                 # ended, no findings file
    walk.advance("audit-development-plan", "timeout")
    land(walk.files, walk.git, "audit", "development-implementation")
    walk.advance("audit-development-implementation", "produced_nothing")

    assert walk.state["ended"] is None
    assert walk.state["audits"] == {
        "development-specs": "findings recorded",
        "development-design": "no findings file",
        "development-plan": "the run ended timeout",
        "development-implementation": "findings recorded",
    }
    assert walk.skills_launched[-1] == "tobiishi-seal"


def test_the_seal_landing_ends_the_walk_sealed():
    walk = Walk(through="audit")
    land(walk.files, walk.git, "seal")

    walk.advance("seal")

    assert walk.state["ended"] == "sealed"
    assert walk.state["pending"] == {}
    assert f"sealed {KEY}" in walk.notifier.messages[-1]


def test_a_seal_that_did_not_reach_the_trail_stops_the_walk():
    walk = Walk(through="audit")

    walk.advance("seal")

    assert walk.state["ended"] == "halted"
    assert f"trail/{KEY}" in walk.state["ended_reason"]


def test_a_whole_walk_runs_every_step_in_order_and_speaks_exactly_twice():
    """Start to sealed through the engine alone — the level `core/tools/test_chain.py`'s header
    names as the one its predecessor was missing."""
    walk = Walk()
    for step_id in ("specs", "design", "plan", "implementation", "code-integrity"):
        land(walk.files, walk.git, step_id)
        walk.advance(step_id)
    for skill in PRODUCERS:
        land(walk.files, walk.git, "audit", skill)
        walk.advance(f"audit-{skill}")
    land(walk.files, walk.git, "seal")
    walk.advance("seal")

    assert walk.skills_launched == [
        "development-specs", "development-design", "development-plan",
        "development-implementation", "development-code-integrity",
        "development-audit", "development-audit", "development-audit", "development-audit",
        "tobiishi-seal"]
    assert walk.state["ended"] == "sealed"
    assert len(walk.notifier.messages) == 2
    assert "suite green" in walk.notifier.messages[-1]


# --- the real ports, against a real repository and a real file --------------------------------


import json
import subprocess
import sys


def _git(repo: Path, *args: str) -> str:
    """No host hook and no host identity reaches the scratch repository."""
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "core.hooksPath=/dev/null", "-c", "user.name=t",
         "-c", "user.email=t@example.invalid", *args],
        check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "instance"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "commit", "-q", "--allow-empty", "-m", "root")
    _git(root, "checkout", "-q", "-b", KEY)
    (root / "code.py").write_text("x = 1\n")
    _git(root, "add", "code.py")
    _git(root, "commit", "-q", "-m", "task 1 — green")
    _git(root, "commit", "-q", "--allow-empty", "-m", MARKER[1], "-m", MARKER_BODY)
    _git(root, "checkout", "-q", "main")
    return root


def test_the_real_git_lists_only_the_commits_the_branch_carries_past_main(repo):
    ahead = cd.Git().commits_ahead(str(repo), "main", KEY)

    assert [subject for _, subject in ahead] == [MARKER[1], "task 1 — green"]
    assert all(len(sha) == 40 for sha, _ in ahead)


def test_the_real_reader_finds_an_external_products_landed_task_in_its_own_repo(tmp_path):
    """Two real repositories: the instance's `<key>` branch carries only pipeline commits, the
    product's carries the per-task commits. The failure resume reads the product's (D1)."""
    from chain import Files

    instance, product = tmp_path / "instance", tmp_path / "product"
    for root in (instance, product):
        root.mkdir()
        _git(root, "init", "-q", "-b", "main")
        _git(root, "commit", "-q", "--allow-empty", "-m", "root")
        _git(root, "branch", KEY)
    _git(instance, "commit", "-q", "--allow-empty", "-m", "plan: tl_instruction")
    _git(product, "checkout", "-q", KEY)
    for subject in ("developer: task 1 x — red", "developer: task 1 x — green",
                    "developer: task 2 y — red", "developer: task 2 y — green",
                    "developer: task 3 z — red"):
        _git(product, "commit", "-q", "--allow-empty", "-m", subject)
    _git(product, "checkout", "-q", "main")
    reader = cd.DiskReader(files=Files(), git=cd.Git())
    change = cd.ChangeLayout(str(instance), PROJECT, KEY)

    assert reader.resumable_task(change, str(product)) == 2
    assert reader.resumable_task(change, str(instance / "product")) is None


def test_the_real_git_answers_no_commits_for_a_branch_that_does_not_exist(repo):
    assert cd.Git().commits_ahead(str(repo), "main", "2026-01-01_never") == []


def test_the_real_git_reads_a_path_off_a_branch_without_checking_it_out(repo):
    git = cd.Git()

    assert git.branch_has_path(str(repo), KEY, "code.py")
    assert not git.branch_has_path(str(repo), "main", "code.py")
    assert not git.branch_has_path(str(repo), "2026-01-01_never", "code.py")


def test_the_real_git_reads_a_commit_body(repo):
    sha = _git(repo, "rev-parse", KEY)

    body = cd.Git().commit_body(str(repo), sha)
    assert body.splitlines()[0] == MARKER[1]
    assert "Suite: green" in body
    assert cd.Git().commit_body(str(repo), "0" * 40) == ""


def test_the_real_git_reads_a_commit_author_time(repo):
    """Author time, never committer time: a commit dated to 1_000_000_000 by `--date` keeps its
    committer time at now, so reading `%ct` instead would miss by decades."""
    _git(repo, "commit", "-q", "--allow-empty", "--date=@1000000000", "-m", "dated")
    dated = _git(repo, "rev-parse", "HEAD")

    assert isinstance(cd.Git().author_time(str(repo), _git(repo, "rev-parse", KEY)), int)
    assert cd.Git().author_time(str(repo), dated) == 1_000_000_000
    assert cd.Git().author_time(str(repo), "0" * 40) is None


def test_the_fake_git_reads_a_recorded_author_time_and_none_for_an_unrecorded_sha():
    git = FakeGit(times={"0cafe1": 100})

    assert git.author_time(INSTANCE, "0cafe1") == 100
    assert git.author_time(INSTANCE, "0ff1ce") is None


def test_the_real_disk_reader_reads_both_verdicts_off_a_real_branch(repo):
    """The real ports wired to the real reader — the marker found off a real branch the way the
    seal does, and both verdicts read off its real body."""
    from chain import Files

    reader = cd.DiskReader(files=Files(), git=cd.Git())
    change = cd.ChangeLayout(str(repo), PROJECT, KEY)

    assert reader.is_done(change, step("implementation"))
    assert reader.suite_verdict(change) == "green"
    assert reader.language_resolved(change)


@pytest.mark.parametrize("verdict", ["pass", "stopped"])
def test_the_real_files_port_reads_the_declared_integrity_verdict(tmp_path, verdict):
    """`DiskReader` with the real `Files()` reads the declared verdict — a pass, and the STOP's
    own form the request asks to see read off disk — from a report written at
    `ChangeLayout(str(tmp_path), PROJECT, KEY).branch_change_folder`."""
    from chain import Files

    change = cd.ChangeLayout(str(tmp_path), PROJECT, KEY)
    report_path = os.path.join(change.branch_change_folder, "code-integrity-report.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    Path(report_path).write_text(f"# Code integrity report\n\nIntegrity: {verdict}\n")

    reader = cd.DiskReader(files=Files(), git=cd.Git())

    assert reader.declared_verdict(change, step("code-integrity")) == verdict


def test_the_real_lock_is_exclusive_while_held(tmp_path):
    import fcntl

    state = tmp_path / "logs" / "state.json"
    with cd.FileLock().hold(str(state)):
        handle = os.open(f"{state}.lock", os.O_RDWR)
        try:
            with pytest.raises(BlockingIOError):
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(handle)

    handle = os.open(f"{state}.lock", os.O_RDWR)
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        os.close(handle)


# --- the command line ---------------------------------------------------------------------------


@pytest.fixture
def notifier_log(tmp_path):
    """A notifier that records its one argument, so a refusal reaching the owner is observable
    without any real channel being touched."""
    log = tmp_path / "notified.log"
    script = tmp_path / "notify.sh"
    script.write_text(f"#!/usr/bin/env bash\nprintf '%s\\n' \"$1\" >> {log}\n")
    script.chmod(0o755)
    return script, log


def test_start_and_advance_together_is_a_usage_error(capsys):
    assert cd.main(["--start", "/s", "--advance", "/s", "specs", "completed"]) == 2
    assert "mutually exclusive" in capsys.readouterr().err


def test_no_entry_point_at_all_is_a_usage_error_naming_all_three(capsys):
    assert cd.main([]) == 2
    err = capsys.readouterr().err
    assert "--start" in err and "--advance" in err and "--describe" in err


def test_start_names_every_required_flag_it_was_not_given(capsys):
    assert cd.main(["--start", "/s", "--project", PROJECT]) == 2
    err = capsys.readouterr().err
    for flag in ("--instance-root", "--product-path", "--core-dir", "--shim-dir"):
        assert flag in err


def test_start_with_no_active_change_refuses_to_stderr_and_the_owner(tmp_path, capsys,
                                                                     notifier_log):
    script, log = notifier_log
    instance = tmp_path / "instance"
    (instance / "system" / "projects" / PROJECT / "journey" / "tobiishi").mkdir(parents=True)
    state = instance / "system" / "logs" / "state.json"

    code = cd.main(["--start", str(state), "--instance-root", str(instance),
                    "--product-path", str(tmp_path / "product"), "--project", PROJECT,
                    "--core-dir", str(tmp_path / "core"), "--shim-dir", str(state.parent),
                    "--notifier", str(script)])

    assert code == 3
    err = capsys.readouterr().err
    assert "no active change" in err and "Traceback" not in err
    assert "no active change" in log.read_text()
    assert not state.exists()


def test_advance_with_no_state_file_refuses_without_a_traceback(tmp_path, capsys):
    code = cd.main(["--advance", str(tmp_path / "missing.json"), "specs", "completed"])

    assert code == 3
    err = capsys.readouterr().err
    assert "no development chain state" in err and "Traceback" not in err


def _state_file(tmp_path, **overrides) -> Path:
    instance = tmp_path / "instance"
    instance.mkdir(exist_ok=True)
    state = cd.WalkState(instance_root=str(instance), product_path=str(tmp_path / "product"),
                         project=PROJECT, core_dir=str(tmp_path / "core"),
                         shim_dir=str(tmp_path / "logs"), engine_path="/pinned", key=KEY,
                         walk_id="walk-1", product_docs=str(tmp_path / "product" / "docs"))
    for name, value in overrides.items():
        setattr(state, name, value)
    path = tmp_path / "logs" / "state.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(state.to_json()))
    return path


def test_advance_on_an_ended_walk_is_counted_through_the_real_composition(tmp_path, capsys):
    path = _state_file(tmp_path, ended="halted")

    assert cd.main(["--advance", str(path), "specs", "completed"]) == 0

    assert json.loads(path.read_text())["reentries"] == 1


def test_advance_on_a_run_that_timed_out_halts_through_the_real_composition(tmp_path,
                                                                          notifier_log):
    """Every real port wired by `build_chain`, on a path that launches nothing."""
    script, log = notifier_log
    path = _state_file(tmp_path, notifier=str(script),
                       pending={"specs": {"step": "specs", "audited": None}})

    assert cd.main(["--advance", str(path), "specs", "timeout"]) == 0

    state = json.loads(path.read_text())
    assert state["ended"] == "halted"
    assert "stopped at specs: the run ended timeout" in log.read_text()


# --- --describe: what the launcher's dry run asks ----------------------------------------------


def _with_a_provider_file(instance: Path) -> Path:
    """`instance` holding its own `.providers.toml` — the delivered text, unless a case already
    wrote its own. An unforced walk reads it at the instance root and nowhere else (CP-483)."""
    instance.mkdir(parents=True, exist_ok=True)
    if not (instance / ".providers.toml").exists():
        (instance / ".providers.toml").write_text(DELIVERED_TEXT, encoding="utf-8")
    return instance


def _instance_with_one_change(tmp_path) -> Path:
    instance = tmp_path / "instance"
    change = instance / "system" / "projects" / PROJECT / "journey" / "tobiishi" / KEY
    change.mkdir(parents=True)
    (change / "change_request.md").write_text("req\n")
    return _with_a_provider_file(instance)


@pytest.mark.parametrize("other", [["--start", "/s"], ["--advance", "/s", "specs", "completed"]])
def test_describe_with_another_entry_point_is_a_usage_error(other, capsys):
    assert cd.main(["--describe", "/s", *other]) == 2
    assert "mutually exclusive" in capsys.readouterr().err


def test_describe_names_every_required_flag_it_was_not_given(capsys):
    assert cd.main(["--describe", "/s"]) == 2
    err = capsys.readouterr().err
    assert "--instance-root" in err and "--project" in err


def test_describe_prints_the_change_and_the_entry_step_and_writes_no_state(tmp_path, capsys):
    instance = _instance_with_one_change(tmp_path)
    state = instance / "system" / "logs" / "chain-development-state.json"

    code = cd.main(["--describe", str(state), "--instance-root", str(instance),
                    "--project", PROJECT])

    assert code == 0
    assert capsys.readouterr().out.splitlines()[:2] == [f"key={KEY}", "entry=specs"]
    assert not state.exists()
    assert not (instance / "system" / "logs").exists()


def test_describe_with_no_active_change_refuses_to_stderr_without_a_traceback(tmp_path, capsys):
    instance = tmp_path / "instance"
    (instance / "system" / "projects" / PROJECT / "journey" / "tobiishi").mkdir(parents=True)

    code = cd.main(["--describe", str(tmp_path / "state.json"), "--instance-root", str(instance),
                    "--project", PROJECT])

    assert code == 3
    captured = capsys.readouterr()
    assert "no active change" in captured.err and "Traceback" not in captured.err
    assert captured.out == ""


def test_describe_refusing_a_live_walk_never_messages_the_owner(tmp_path, capsys, notifier_log):
    """The state names a notifier, as a real walk's does; `--start` and `--advance` would send a
    refusal to it. A dry run is the owner asking a question, so the answer goes to their terminal
    and nowhere else."""
    script, log = notifier_log
    path = _state_file(tmp_path, notifier=str(script),
                       pending={"specs": {"step": "specs", "audited": None}})

    code = cd.main(["--describe", str(path), "--instance-root", str(tmp_path / "instance"),
                    "--project", PROJECT])

    assert code == 3
    assert "still walking" in capsys.readouterr().err
    assert not log.exists()


# --- development-code-integrity, 2026-09-15: tests derived from the plan and the contracts ------
#
# Each test below is written from the approved plan
# (`~/.claude/plans/plan-something-like-development-frolicking-crystal.md`) or from a contract the
# engine relies on, quoting the literal it checks — never from `chain_development.py`'s own paths.


def test_the_sealed_message_reads_the_way_the_plan_states_it():
    """Plan § Design, One terminal writer: `<instance> · <p> · development chain — sealed <key>`."""
    walk = Walk(through="audit")
    land(walk.files, walk.git, "seal")

    walk.advance("seal")

    assert walk.notifier.messages[-1].startswith(
        f"instance · {PROJECT} · development chain — sealed {KEY}")


def test_a_relaunch_past_implementation_records_the_suite_it_read():
    """CP-18: a walk entering past `implementation` — over the default green marker — records
    the suite and marker it read, the same record `_settle` makes when implementation lands,
    once `start` returns."""
    walk = Walk(through="audit")

    assert walk.state["suite"] == "green"
    assert walk.state["marker"] == "a1b2c3"


def test_a_relaunch_that_seals_names_its_suite_in_the_sealed_message():
    """CP-18: a walk entering past `implementation` that goes on to seal names the suite it
    read at entry in its sealed message — never `unrecorded`, which `_sealed_summary` falls
    back to only when nothing was ever recorded."""
    walk = Walk(through="audit")
    land(walk.files, walk.git, "seal")

    walk.advance("seal")

    assert "suite green (marker a1b2c3)" in walk.notifier.messages[-1]
    assert "unrecorded" not in walk.notifier.messages[-1]


def test_a_relaunch_entering_at_code_integrity_also_records_the_suite_it_read():
    """CP-18, the nearer edge: `code-integrity` (index 4) is already past the marker step
    `implementation` (index 3) — the record is not reserved for a walk that skips all the way
    to `seal`; it is set as soon as the entry is past the marker, whichever step that is."""
    walk = Walk(through="implementation")

    assert walk.state["suite"] == "green"
    assert walk.state["marker"] == "a1b2c3"
    assert "unrecorded" not in walk.notifier.messages[-1]


def test_the_stopped_message_reads_the_way_the_plan_states_it():
    """Plan § Design, One terminal writer: the same headline, then
    `— stopped at <step>: <reason>`."""
    walk = Walk()

    walk.advance("specs", "timeout")

    assert walk.notifier.messages[-1].startswith(
        f"instance · {PROJECT} · development chain — stopped at specs: ")


def test_a_walk_that_halted_on_a_missing_artifact_is_re_entered_at_that_step():
    """Plan § Verification 4: the chain stops with one message naming the step, and a re-run of
    the launcher picks up from that step."""
    walk = Walk(through="specs")
    walk.advance("design")                                      # the run ended, no change_design.md
    assert walk.state["ended"] == "halted"
    assert [message for message in walk.notifier.messages if "stopped at" in message] == [
        walk.notifier.messages[-1]]
    assert "stopped at design" in walk.notifier.messages[-1]

    start(walk.engine())

    assert walk.processes.launched[-1] == [SKILL_LAUNCHER, "development-design", PROJECT, KEY]
    assert walk.state["ended"] is None


def test_every_argv_the_engine_builds_is_accepted_by_the_real_skill_launcher(tmp_path):
    """Plan § Launching a step: `core/launchers/skill/launcher.sh <skill> <args> [--keep-awake]`.
    The engine's argv is run, dry, through the real launcher against this repository's real
    `launcher.md` files — so an argument count or shape a launcher.md does not declare is refused
    here, not on the first real walk."""
    walk = Walk()
    for step_id in ("specs", "design", "plan", "implementation", "code-integrity"):
        land(walk.files, walk.git, step_id)
        walk.advance(step_id)
    for skill in PRODUCERS:
        land(walk.files, walk.git, "audit", skill)
        walk.advance(f"audit-{skill}")

    env = dict(os.environ)
    env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(tmp_path / "no-instrument-endpoint")
    env["HOME"] = str(tmp_path)
    env.pop("LAUNCH_SKILL_NOTIFIER", None)
    real_launcher = _REPO / "core" / "launchers" / "skill" / "launcher.sh"
    real_project = "example-product"
    instance = scratch_instance(tmp_path, real_project)
    assert len(walk.processes.launched) == 10
    for argv in walk.processes.launched:
        assert argv[0] == SKILL_LAUNCHER and argv[2] == PROJECT
        real = [str(real_launcher), argv[1], real_project, *argv[3:], "--keep-awake",
                "--provider", "claude", "--dry-run"]   # forced: this suite holds no instance file

        result = subprocess.run(real, cwd=str(instance), capture_output=True, text=True, env=env)

        assert result.returncode == 0, (argv, result.stderr)
        assert "DRY RUN" in result.stdout
        assert f"Argument:  <project> {real_project}" in result.stdout, argv
        if argv[1] != "development-specs":
            assert f"Argument:  <key> {KEY}" in result.stdout, argv
        if argv[1] == "development-audit":
            assert f"Argument:  <step> {argv[4]}" in result.stdout, argv


# The stub every real-port test below starts steps through: it records the launcher argv it was
# given, and — when `STUB_DESIGN_RELEASE` names a file — holds development-design until that file
# exists, or for `_STUB_HOLD_CAP` seconds at most, so a test can see whether the hook waited on it.
_STUB_HOLD_CAP = 30
_SKILL_LAUNCHER_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$(dirname "$0")/calls.log"
if [ "$1" = development-design ] && [ -n "${STUB_DESIGN_RELEASE:-}" ]; then
  for _ in $(seq $((HOLD_CAP * 20))); do [ -e "$STUB_DESIGN_RELEASE" ] && break; sleep 0.05; done
fi
exit 0
""".replace("HOLD_CAP", str(_STUB_HOLD_CAP))

_REAL_ENGINE = str(Path(cd.__file__).resolve())


def _stub_core(root: Path) -> Path:
    launcher = root / "launchers" / "skill" / "launcher.sh"
    launcher.parent.mkdir(parents=True)
    launcher.write_text(_SKILL_LAUNCHER_STUB)
    launcher.chmod(0o755)
    return root


def _calls(core: Path) -> list[str]:
    log = core / "launchers" / "skill" / "calls.log"
    return log.read_text().splitlines() if log.exists() else []


def _wait_for(predicate, seconds: float = 20.0) -> bool:
    import time

    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.1)
    return predicate()


def test_the_shim_fired_by_the_real_watcher_hook_returns_at_once_and_advances_the_walk(
        tmp_path, monkeypatch):
    """Plan § Launching a step: the shim is what `DETACH_WATCHER_ON_COMPLETE` names, and
    `watch_agent.py` `run_on_complete_hook` runs it as `[hook, outcome]` with output captured and
    `timeout=60`, from the watcher's own working directory. Driven here through that real function,
    from a different cwd, with spaces in every path: the hook returns while the next step's launcher
    is still running, and the detached engine still launches that step and writes its log."""
    import time

    import watch_agent

    instance = tmp_path / "an instance"
    core = _stub_core(tmp_path / "a core")
    logs = instance / "system" / "logs"
    state_path = logs / f"chain-development-{PROJECT}-state.json"
    request = instance / "system" / "projects" / PROJECT / "journey" / "tobiishi" / KEY
    request.mkdir(parents=True)
    (request / "change_request.md").write_text("req")
    _with_a_provider_file(instance)
    release = tmp_path / "release design"
    monkeypatch.setenv("STUB_DESIGN_RELEASE", str(release))

    chain = cd.build_chain(str(state_path), notifier_command="", engine_path=_REAL_ENGINE)
    chain.start(instance_root=str(instance), product_path=str(tmp_path / "product"),
                project=PROJECT, core_dir=str(core), shim_dir=str(logs))
    shim = logs / f"chain-development-{PROJECT}-specs.sh"
    assert os.access(shim, os.X_OK)

    # development-specs' contract: change_spec.md on the branch, in `<repo>/.worktrees/<key>`.
    spec = (instance / ".worktrees" / KEY / "system" / "projects" / PROJECT / "journey"
            / "tobiishi" / KEY)
    spec.mkdir(parents=True)
    (spec / "change_spec.md").write_text("spec")
    elsewhere = tmp_path / "watcher cwd"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    began = time.monotonic()
    ran = watch_agent.run_on_complete_hook(str(shim), watch_agent.HookOutcome.COMPLETED)
    elapsed = time.monotonic() - began

    # The design launcher is held until `release` exists, and nothing writes it before the hook
    # returns — so a hook that waited on the engine waits out the stub's whole cap. The bound is
    # that cap less a margin, not a guess at how fast a process starts: the first exec of a
    # freshly written script alone has measured over 3s under a full parallel suite.
    assert ran is True
    assert elapsed < _STUB_HOLD_CAP - 10, (
        f"the hook waited {elapsed:.1f}s on the engine it should have detached")
    release.write_text("")
    assert _wait_for(lambda: "launched design" in json.loads(state_path.read_text())["history"])
    assert any(line.startswith("development-design ") for line in _calls(core))
    assert (logs / f"chain-development-{PROJECT}.log").read_text().startswith(
        "chain_development: started walk=")


def test_four_audit_ends_arriving_together_release_exactly_one_seal(tmp_path):
    """Plan § Launching a step / `--advance`: the four audits run in parallel and the seal starts
    only once all four have stopped; the `flock` on `<state>.lock` is what makes that hold when
    four real engine processes wake at the same moment. Each end is then delivered a second time,
    which must launch nothing."""
    instance = _with_a_provider_file(tmp_path / "instance")
    core = _stub_core(tmp_path / "core")
    logs = tmp_path / "logs"
    state = cd.WalkState(instance_root=str(instance), product_path=str(tmp_path / "product"),
                         project=PROJECT, core_dir=str(core), shim_dir=str(logs),
                         engine_path=_REAL_ENGINE, key=KEY, walk_id="walk-1",
                         product_docs=str(tmp_path / "product" / "docs"),
                         pending={f"audit-{skill}": {"step": "audit", "audited": skill}
                                  for skill in PRODUCERS})
    state_path = logs / "state.json"
    logs.mkdir()
    state_path.write_text(json.dumps(state.to_json()))

    def deliver_all():
        runs = [subprocess.Popen([sys.executable, _REAL_ENGINE, "--advance", str(state_path),
                                  f"audit-{skill}", "completed"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                for skill in PRODUCERS]
        return [(run.wait(timeout=60), run.stderr.read()) for run in runs]

    for code, err in deliver_all():
        assert code == 0, err

    saved_state = json.loads(state_path.read_text())
    assert set(saved_state["audits"]) == set(PRODUCERS)
    assert list(saved_state["pending"]) == ["seal"]
    assert [line for line in _calls(core) if line.startswith("tobiishi-seal ")] == [
        f"tobiishi-seal {PROJECT} {KEY}"]

    for code, err in deliver_all():
        assert code == 0, err
    assert len(_calls(core)) == 1


def test_a_whole_walk_reaches_sealed_against_a_real_repository_laid_down_by_the_contracts(
        tmp_path):
    """Plan § Facts, What each step leaves on disk — each step's evidence put on a real git
    repository with the commands and the literal paths its own skill states, never with the
    engine's `ChangeLayout`:
    - create_change_worktree.py: branch `<key>`, worktree `<repo>/.worktrees/<key>`;
    - development-specs § Outputs: `$WORKTREE/system/projects/<project>/journey/tobiishi/<key>/`;
    - development-implementation Step 3: subject `developer: <key> — implementation complete`;
    - development-code-integrity: `code-integrity-report.md` in that same folder, declaring
      `Integrity: pass`;
    - development-audit Step 0: branch `<key>__audit-<step>` cut from `<key>`, worktree
      `$REPO_ROOT/.worktrees/$AUDIT_BRANCH`, committing `flow_findings/<step>.md`;
    - tobiishi-seal Steps 1b-4: join each audit branch, `git mv` the folder to `trail/<key>`,
      `--no-ff` merge into `main`, remove the worktrees and branches.
    """
    repo = tmp_path / "instance"
    repo.mkdir()
    rel = f"system/projects/{PROJECT}/journey/tobiishi"
    _git(repo, "init", "-q", "-b", "main")
    (repo / rel / KEY).mkdir(parents=True)
    (repo / rel / KEY / "change_request.md").write_text("req\n")
    _git(repo, "add", f"{rel}/{KEY}/change_request.md")
    _git(repo, "commit", "-q", "-m", f"open: {KEY}")

    from chain import Files

    files = Files()
    processes = FakeProcesses()
    notifier = FakeNotifier()
    state_path = tmp_path / "logs" / "state.json"
    chain = cd.DevelopmentChain(
        store=cd.StateStore(files, str(state_path)),
        reader=cd.DiskReader(files=files, git=cd.Git()),
        files=files, processes=processes, notifier=notifier, lock=cd.FileLock(),
        log=cd.WalkLog(), id_source=FakeIdSource(), environ={}, engine_path=_REAL_ENGINE,
        steps=cd.DEVELOPMENT_STEPS, providers=provider_files(),
        process_table=FakeProcessTable(), checkout=product_checkout.Checkout())
    chain.start(instance_root=str(repo), product_path=str(repo / "product"), project=PROJECT,
                core_dir=CORE, shim_dir=str(tmp_path / "logs"))

    worktree = repo / ".worktrees" / KEY

    def commit_in(tree: Path, name: str, subject: str, folder: str = f"{rel}/{KEY}",
                 content: str | None = None) -> None:
        (tree / folder).mkdir(parents=True, exist_ok=True)
        (tree / folder / name).write_text(content if content is not None else f"{name}\n")
        _git(tree, "add", f"{folder}/{name}")
        _git(tree, "commit", "-q", "-m", subject)

    _git(repo, "worktree", "add", "-q", "-b", KEY, str(worktree))
    commit_in(worktree, "change_spec.md", f"po: {KEY} — change spec")
    chain.advance("specs", "produced_nothing")
    commit_in(worktree, "change_design.md", f"architect: {KEY} — design",
              content=NO_TEXT_DESIGN)
    chain.advance("design", "completed")
    commit_in(worktree, "tl_instruction.md", f"tech lead: {KEY} — plan")
    chain.advance("plan", "completed")
    commit_in(worktree, "code.py", "task 1 — green", folder="product")
    _git(worktree, "commit", "-q", "--allow-empty", "-m",
         f"developer: {KEY} — implementation complete", "-m", MARKER_BODY)
    chain.advance("implementation", "completed")
    commit_in(worktree, "code-integrity-report.md", f"senior engineer: {KEY} — integrity",
             content=PASSING_REPORT)
    chain.advance("code-integrity", "completed")

    assert [argv[1:] for argv in processes.launched[-4:]] == [
        ["development-audit", PROJECT, KEY, skill] for skill in PRODUCERS]
    for skill in PRODUCERS:
        audit_branch = f"{KEY}__audit-{skill}"
        audit_tree = repo / ".worktrees" / audit_branch
        _git(repo, "worktree", "add", "-q", "-b", audit_branch, str(audit_tree), KEY)
        commit_in(audit_tree, f"{skill}.md", f"auditor: {KEY} — {skill}",
                  folder=f"{rel}/{KEY}/flow_findings")
        chain.advance(f"audit-{skill}", "completed")

    assert json.loads(state_path.read_text())["audits"] == {
        skill: "findings recorded" for skill in PRODUCERS}
    assert processes.launched[-1][1:] == ["tobiishi-seal", PROJECT, KEY]

    for skill in PRODUCERS:
        _git(worktree, "merge", "-q", "--no-ff", "-m", f"merge audit {skill}",
             f"{KEY}__audit-{skill}")
    (worktree / rel / "trail").mkdir()
    _git(worktree, "mv", f"{rel}/{KEY}", f"{rel}/trail/{KEY}")
    _git(worktree, "commit", "-q", "-m", f"seal: {KEY} — accepted, moved to trail/")
    _git(repo, "merge", "-q", "--no-ff", "-m", f"merge: {KEY} → main", KEY)
    _git(repo, "worktree", "remove", str(worktree))
    _git(repo, "branch", "-q", "-d", KEY)
    for skill in PRODUCERS:
        _git(repo, "worktree", "remove", str(repo / ".worktrees" / f"{KEY}__audit-{skill}"))
        _git(repo, "branch", "-q", "-d", f"{KEY}__audit-{skill}")
    chain.advance("seal", "completed")

    final = json.loads(state_path.read_text())
    assert final["ended"] == "sealed", final["ended_reason"]
    assert len(final["marker"]) == 40
    assert f"sealed {KEY}" in notifier.messages[-1]
    assert len(notifier.messages) == 2

    with pytest.raises(cd.ChainRefused, match="no active change"):
        chain.start(instance_root=str(repo), product_path=str(repo / "product"), project=PROJECT,
                    core_dir=CORE, shim_dir=str(tmp_path / "logs"))


# --- development-code-integrity, 2026-09-15: the dry run's describe, tested from its plan --------
#
# Each test below is written from the approved plan `plan-something-like-development-frolicking-
# crystal.md` § Design 1 and § Tests — "describe and start read one set of checks", "`describe`
# touches nothing", "It never builds a notifier and never sends", "A dry run has no reason to wait
# on a live walk's lock" — and not from the implementation.


def _answer(call):
    """`("ok", value)` or `("raised", exception type, message)`: every way a check can answer, so
    two callers can be compared on all of them at once."""
    try:
        return ("ok", call())
    except Exception as exc:
        return ("raised", type(exc).__name__, str(exc))


def _describe_and_start(disk: dict, git, state_text):
    """What `describe` answers, and what `start` does, on two identical copies of one world."""
    def world():
        files = dict(disk)
        if state_text is not None:
            files[STATE] = state_text
        return FakeFiles(files)

    described = _answer(lambda: describe(build(world(), git=git)).entry)
    processes = FakeProcesses()

    def started():
        start(build(world(), git=git, processes=processes))
        return next(entry.id for entry in cd.DEVELOPMENT_STEPS
                    if entry.skill == processes.launched[0][1])

    return described, _answer(started)


@pytest.mark.parametrize("state_text", [
    None,
    "",
    "{not json",
    "null",
    "[]",
    '["specs"]',
    '{"schema_version": 99}',
    '{"schema_version": 99, "key": "k", "pending": {"specs": {"step": "specs"}}}',
    '{"key": "k", "pending": {}}',
    '{"key": "k", "pending": null}',
    '{"key": "k", "ended": "halted", "pending": {"specs": {"step": "specs"}}}',
    '{"key": "k", "ended": "sealed", "pending": {}}',
    '{"key": "k", "ended": null, "pending": {"plan": {"step": "plan"}}}',
], ids=["missing", "empty", "unparseable", "json-null", "empty-list", "non-empty-list",
        "wrong-schema", "wrong-schema-pending", "pending-empty", "pending-null",
        "ended-with-pending", "sealed-ended", "live"])
def test_describe_and_start_answer_alike_on_every_shape_of_state_file(state_text):
    """Plan § Design 1: `start` calls `describe`, "so the dry run and the real start cannot drift
    apart". Whatever the state file holds — nothing, garbage, another schema, an ended walk, an
    empty `pending` — both refuse with the same exception and message, or both enter at the same
    step. (A shape that breaks one breaks the other identically; that is still agreement.)"""
    files, git = _through("plan")

    described, started = _describe_and_start(files, git, state_text)

    assert described == started


@pytest.mark.parametrize("landed_through", [
    None, "specs", "design", "plan", "implementation", "code-integrity", "audit"])
def test_describe_and_start_agree_at_each_of_the_seven_entry_steps(landed_through):
    """Plan § Tests: "`describe` on each disk state returns the same entry as `start` launches".
    The implementer's agreement test covered four of the seven states."""
    files, git = _through(landed_through)

    described, started = _describe_and_start(files, git, None)

    assert described[0] == "ok"
    assert described == started


def _two_changes():
    return {f"{TOBIISHI}/{KEY}/change_request.md": "one",
            f"{TOBIISHI}/2026-09-16_other/change_request.md": "two"}, FakeGit()


def _sealed():
    """A world through `audit`, sealed, whose marker declares `Suite: red` — so a refusal that
    still reads `already sealed` proves the sealed check comes before any verdict is read."""
    files, git = _through("audit")
    files[f"{TOBIISHI}/trail/{KEY}/change_request.md"] = "sealed"
    git.bodies[MARKER[0]] = "Suite: red\n"
    return files, git


def test_a_newer_green_marker_over_an_older_red_one_lets_the_relaunch_enter():
    """CP-17: two closing markers on the branch, newest first — the order `commits_ahead`
    returns — the older declaring `Suite: red`, the newer `Suite: green` with a `Language
    resolution:` line. `marker_commit` already reads the first (newest) match, so `describe`
    and `start` both answer `seal` rather than reading the older, red one."""
    files, git = _through("audit")
    older = ("z9y8x7", f"developer: {KEY} — implementation complete")
    git.commits[KEY] = [MARKER, older]
    git.bodies[older[0]] = "Suite: red\n"
    # git.bodies[MARKER[0]] is already MARKER_BODY (green, language-resolved) from _through.

    described, started = _describe_and_start(files, git, None)

    assert described == ("ok", "seal")
    assert started == ("ok", "seal")


def test_a_sealed_change_refuses_as_sealed_whatever_its_verdicts():
    """CP-17: `_sealed()`'s marker declares `Suite: red`; `describe` and `start` both raise
    `ChainRefused` naming `already sealed`, and neither message reads `stopped at` — the sealed
    check refuses before any verdict is read, on both callers alike."""
    files, git = _sealed()

    described, started = _describe_and_start(files, git, None)

    for outcome in (described, started):
        assert outcome[0] == "raised"
        assert "already sealed" in outcome[2]
        assert "stopped at" not in outcome[2]


@pytest.mark.parametrize("world", [
    lambda: ({}, FakeGit()), _two_changes, _sealed,
    *[(lambda make_bad=make_bad: _bad_verdict_world(make_bad))
      for make_bad, _ in _BAD_VERDICT_CASES],
], ids=["no-active-change", "two-changes", "sealed", *_BAD_VERDICT_IDS])
def test_a_refusal_reads_word_for_word_the_same_from_describe_and_from_start(world):
    """Plan outcome: a dry run "fails with the same reason the real start would give" — the same
    reason, not a similar one. CP-16: `world` carries the five bad-verdict shapes too, each its
    own id."""
    files, git = world()

    described, started = _describe_and_start(files, git, None)

    assert described[0] == "raised"
    assert described == started


@pytest.mark.parametrize("given, missing, present", [
    (["--project", PROJECT], "--instance-root", "--project"),
    (["--instance-root", "/i"], "--project", "--instance-root"),
])
def test_describe_names_only_the_flag_it_was_not_given(given, missing, present, capsys):
    """Plan § Design 1: "A missing flag names itself and returns 2"."""
    assert cd.main(["--describe", "/s", *given]) == 2
    err = capsys.readouterr().err
    assert missing in err
    assert present not in err


def test_describe_that_crashes_sends_nothing_even_when_the_state_names_a_notifier(tmp_path,
                                                                                capsys,
                                                                                notifier_log):
    """Plan § Design 1: `--describe` "never builds a notifier and never sends" — so not on its
    crash path either, where `--start` and `--advance` both message the owner. A `pending` that
    cannot be sorted is a state shape the live-walk check cannot read."""
    script, log = notifier_log
    path = _state_file(tmp_path, notifier=str(script), pending=[1, "specs"])

    code = cd.main(["--describe", str(path), "--instance-root", str(tmp_path / "instance"),
                    "--project", PROJECT])

    assert code != 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err != ""
    assert not log.exists()


def test_a_notifier_handed_to_describe_is_never_invoked(tmp_path, capsys, notifier_log):
    """The CLI accepts `--notifier` beside any entry point. Handing one to `--describe` must not
    turn its refusal into a message: "It never builds a notifier and never sends"."""
    script, log = notifier_log
    instance = tmp_path / "instance"
    (instance / "system" / "projects" / PROJECT / "journey" / "tobiishi").mkdir(parents=True)

    code = cd.main(["--describe", str(tmp_path / "state.json"), "--instance-root", str(instance),
                    "--project", PROJECT, "--notifier", str(script)])

    assert code != 0
    assert "no active change" in capsys.readouterr().err
    assert not log.exists()


def test_describe_does_not_wait_on_a_lock_a_live_walk_holds(tmp_path):
    """Plan § Design 1: "A dry run has no reason to wait on a live walk's lock". The real `flock`
    is held here, in this process, while the real engine answers `--describe` in another; a
    describe that took the lock would hang until the timeout fails the test."""
    instance = _instance_with_one_change(tmp_path)
    state = instance / "system" / "logs" / "chain-development-state.json"
    engine = Path(cd.__file__).resolve()

    with cd.FileLock().hold(str(state)):
        result = subprocess.run(
            [sys.executable, str(engine), "--describe", str(state), "--instance-root",
             str(instance), "--project", PROJECT],
            capture_output=True, text=True, timeout=15)

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[:2] == [f"key={KEY}", "entry=specs"]


# --- the change chain: the key arrives mid-walk --------------------------------------------------
#
# `chain-development` resolves the key at the start and every path hangs off it. A `chain-change`
# walk entering at `station` has no key to resolve — `tobiishi-open` is the step that makes one. So
# the walk starts keyless, and the key is read off the disk the moment that step lands.


STATION = f"{SHUKUBA}/2026-09-17_a-station.md"


def change_build(files, **kwargs):
    return build(files, steps=cd.CHANGE_STEPS, **kwargs)


@pytest.mark.parametrize("files, key, entry", [
    ({}, "", "station"),
    ({STATION: "station"}, "", "change"),
    ({STATION: "station", **{f"{TOBIISHI}/{KEY}/change_request.md": "req"}}, KEY, "specs"),
])
def test_describe_names_no_key_until_the_change_step_has_landed(files, key, entry):
    plan = describe(change_build(FakeFiles(files)))

    assert plan.key == key
    assert plan.entry == entry


def test_a_development_walk_still_refuses_when_no_change_is_open():
    """The key stays required for the table that does not open one — `chain-development`'s
    refusal is what tells a caller to run tobiishi-open first, and it must survive this."""
    with pytest.raises(cd.ChainRefused, match="no active change"):
        describe(build(FakeFiles({STATION: "station"})))


def test_a_change_walk_still_refuses_two_active_changes():
    """Keylessness is not permission to carry an ambiguous disk: the moment a change exists at
    all, discover_key decides, and it refuses more than one."""
    files = FakeFiles({STATION: "station",
                       f"{TOBIISHI}/{KEY}/change_request.md": "one",
                       f"{TOBIISHI}/2026-09-16_other/change_request.md": "two"})

    with pytest.raises(cd.ChainRefused, match="more than one active change"):
        describe(change_build(files))


def test_a_keyless_start_launches_shukuba_open_with_only_the_project():
    files = FakeFiles()
    processes = FakeProcesses()

    start(change_build(files, processes=processes))

    assert processes.launched == [[SKILL_LAUNCHER, "shukuba-open", PROJECT]]
    assert saved(files)["key"] == ""


def test_the_change_step_landing_writes_the_key_and_hands_it_to_specs():
    """The one moment the key arrives. `development-specs` is launched without it — it finds the
    change itself — but every step after reads `state.key`, so it has to be on the state before
    the walk moves on."""
    files = FakeFiles({STATION: "station"})
    processes = FakeProcesses()
    lock = FakeLock()
    start(change_build(files, processes=processes, lock=lock))
    files.write_text(f"{TOBIISHI}/{KEY}/change_request.md", "req")

    change_build(files, processes=processes, lock=lock).advance("change", "completed")

    assert saved(files)["key"] == KEY
    assert processes.launched[-1] == [SKILL_LAUNCHER, "development-specs", PROJECT]


@pytest.mark.parametrize("step_id, skill, missing", [
    ("station", "shukuba-open", "a station at"),
    ("change", "tobiishi-open", "change_request.md under"),
])
def test_a_journey_step_that_leaves_nothing_halts_naming_what_it_owed(step_id, skill, missing):
    """The halt has to name what the owner should look for. Neither shape exists in the
    development table, so neither has a message yet."""
    files = FakeFiles({STATION: "station"} if step_id == "change" else {})
    notifier = FakeNotifier()
    lock = FakeLock()
    start(change_build(files, lock=lock))

    change_build(files, notifier=notifier, lock=lock).advance(step_id, "completed")

    state = saved(files)
    assert state["ended"] == "halted"
    assert missing in state["ended_reason"]
    assert f"stopped at {step_id}" in state["ended_reason"]


# --- a walk's own name -----------------------------------------------------------------------
#
# `development` was a module constant, so every walk wore it: the shim, the log, the telemetry tag
# and the owner's message. Two tables means two walks, and the owner reading a phone has to be able
# to tell which one stopped.


def test_a_change_walk_names_itself_everywhere_a_development_walk_names_itself():
    files = FakeFiles()
    processes = FakeProcesses()
    notifier = FakeNotifier()

    start(change_build(files, processes=processes, notifier=notifier))

    env = processes.calls[0]["env"]
    assert env["INSTRUMENT_RUN_CHAIN"] == "change"
    assert env["DETACH_WATCHER_ON_COMPLETE"] == f"{LOGS}/chain-change-{PROJECT}-station.sh"
    assert f">>{LOGS}/chain-change-{PROJECT}.log 2>&1 &" in files.files[
        f"{LOGS}/chain-change-{PROJECT}-station.sh"]
    assert notifier.messages[0].startswith(f"instance · {PROJECT} · change chain started")


def test_a_development_walk_keeps_every_name_it_had():
    """The regression this task is most likely to cause: the sibling launcher's paths, telemetry
    and message are what its own suite and the owner's channel already read."""
    files = FakeFiles(fresh_change())
    processes = FakeProcesses()
    notifier = FakeNotifier()

    start(build(files, processes=processes, notifier=notifier))

    env = processes.calls[0]["env"]
    assert env["INSTRUMENT_RUN_CHAIN"] == "development"
    assert env["DETACH_WATCHER_ON_COMPLETE"] == f"{LOGS}/chain-development-{PROJECT}-specs.sh"
    assert notifier.messages[0].startswith(f"instance · {PROJECT} · development chain started")


def test_the_walks_name_is_on_the_state_so_a_fresh_advance_still_knows_it():
    """Every advance re-enters as a fresh process holding one run id and one outcome. A name the
    engine derived at start time and kept in memory would be gone by then."""
    files = FakeFiles()
    start(change_build(files))

    assert saved(files)["chain_name"] == "change"


# --- --steps: which of the two tables this walk is ---------------------------------------------
#
# The flag picks one of two literals the engine holds. It is not a spine handed in — a caller
# cannot reach into either table — and it defaults to `development`, so `chain-development`'s own
# invocation is unchanged by any of this.


def test_build_chain_defaults_to_the_development_table():
    engine = cd.build_chain("/s", notifier_command="", engine_path="/e")

    assert engine.steps is cd.DEVELOPMENT_STEPS
    assert engine.chain_name == "development"


def test_build_chain_takes_the_change_table_and_its_name():
    engine = cd.build_chain("/s", notifier_command="", engine_path="/e", steps=cd.CHANGE_STEPS)

    assert engine.steps is cd.CHANGE_STEPS
    assert engine.chain_name == "change"


def test_an_unknown_steps_value_is_a_usage_error_naming_both_tables(capsys):
    """Refused by the parser, like every other malformed argument here (`--advance`'s arity is
    the same shape) — exit 2, and the message names the two walks that exist."""
    with pytest.raises(SystemExit) as refused:
        cd.main(["--describe", "/s", "--instance-root", "/i", "--project", PROJECT,
                 "--steps", "journey"])

    assert refused.value.code == 2
    err = capsys.readouterr().err
    assert "development" in err and "change" in err


def _instance_with_one_station(tmp_path) -> Path:
    instance = tmp_path / "instance"
    shukuba = instance / "system" / "projects" / PROJECT / "journey" / "shukuba"
    shukuba.mkdir(parents=True)
    (shukuba / "README.md").write_text("the stamped readme\n")
    (instance / "system" / "projects" / PROJECT / "journey" / "tobiishi").mkdir(parents=True)
    return _with_a_provider_file(instance)


def test_describe_over_the_change_table_names_an_empty_key_and_the_station_step(tmp_path, capsys):
    """A dry run before anything is open. The key line is still printed — a launcher parsing the
    output reads a field that is there and empty, never a field that vanished."""
    instance = _instance_with_one_station(tmp_path)

    code = cd.main(["--describe", str(tmp_path / "state.json"), "--instance-root", str(instance),
                    "--project", PROJECT, "--steps", "change"])

    assert code == 0
    assert capsys.readouterr().out.splitlines()[:2] == ["key=", "entry=station"]


def test_describe_over_the_change_table_names_the_key_once_a_change_is_open(tmp_path, capsys):
    instance = _instance_with_one_change(tmp_path)
    shukuba = instance / "system" / "projects" / PROJECT / "journey" / "shukuba"
    shukuba.mkdir(parents=True)
    (shukuba / "2026-09-17_a-station.md").write_text("station\n")

    code = cd.main(["--describe", str(tmp_path / "state.json"), "--instance-root", str(instance),
                    "--project", PROJECT, "--steps", "change"])

    assert code == 0
    assert capsys.readouterr().out.splitlines()[:2] == [f"key={KEY}", "entry=specs"]


def test_describe_says_which_provider_each_step_would_run_on(tmp_path, capsys):
    instance = _instance_with_one_change(tmp_path)
    base = ["--describe", str(tmp_path / "state.json"), "--instance-root", str(instance),
            "--project", PROJECT]

    assert cd.main(base) == 0
    own = capsys.readouterr().out.splitlines()[2]
    assert cd.main([*base, "--provider", "codex"]) == 0
    forced = capsys.readouterr().out.splitlines()[2]

    steps = [step.id for step in cd.DEVELOPMENT_STEPS]
    assert own == ("providers=specs=claude design=claude plan=claude content=claude "
                   "implementation=claude code-integrity=claude audit=claude seal=claude")
    assert forced == "providers=" + " ".join(f"{step}=codex" for step in steps)


def _copy_of_the_file(tmp_path, changes: dict) -> Path:
    """The instance's own `.providers.toml`, edited by `changes`, written where the `main`-level
    cases look for it: at the root of the instance `_instance_with_one_change` makes. The engine
    reads the file at the instance root it is given and takes no flag or variable for it."""
    instance = tmp_path / "instance"
    instance.mkdir(parents=True, exist_ok=True)
    copy = instance / ".providers.toml"
    copy.write_text(edited_text(changes), encoding="utf-8")
    return copy


def test_describe_over_the_change_table_prints_every_steps_provider(tmp_path, capsys):
    """CP-287 (Ex 27), from the delivered file."""
    instance = _instance_with_one_change(tmp_path)
    shukuba = instance / "system" / "projects" / PROJECT / "journey" / "shukuba"
    shukuba.mkdir(parents=True)
    (shukuba / "2026-09-17_a-station.md").write_text("station\n")

    code = cd.main(["--describe", str(tmp_path / "state.json"), "--instance-root", str(instance),
                    "--project", PROJECT, "--steps", "change"])

    assert code == 0
    assert capsys.readouterr().out.splitlines()[2] == (
        "providers=station=claude change=claude specs=claude design=claude plan=claude "
        "content=claude implementation=claude code-integrity=claude audit=claude seal=claude "
        "refine=claude")


def test_describe_prints_what_a_copy_of_the_file_says(tmp_path, capsys):
    _copy_of_the_file(tmp_path, {"steps.audit": "gemini"})
    instance = _instance_with_one_change(tmp_path)

    code = cd.main(["--describe", str(tmp_path / "state.json"), "--instance-root", str(instance),
                    "--project", PROJECT])

    assert code == 0
    assert "audit=gemini" in capsys.readouterr().out.splitlines()[2].split()


def test_describe_refuses_with_exit_3_naming_a_missing_entry(tmp_path, capsys):
    """CP-281 (Ex 11, engine level): the launcher's dry run turns this exit and stderr into
    `a start would be refused — `; forced, the same copy describes."""
    _copy_of_the_file(tmp_path, {"steps.code-integrity": None})
    instance = _instance_with_one_change(tmp_path)
    base = ["--describe", str(tmp_path / "state.json"), "--instance-root", str(instance),
            "--project", PROJECT]

    assert cd.main(base) == 3
    captured = capsys.readouterr()
    assert "steps.code-integrity is missing" in captured.err
    assert captured.out == ""
    assert not (tmp_path / "state.json").exists()

    assert cd.main([*base, "--provider", "codex"]) == 0
    assert capsys.readouterr().out.splitlines()[2] == "providers=" + " ".join(
        f"{step.id}=codex" for step in cd.DEVELOPMENT_STEPS)


def test_main_refuses_a_start_naming_a_missing_entry(tmp_path, capsys, notifier_log):
    """CP-281 through the real composition: exit 3, the entry on stderr and on the owner's
    channel, and no state written."""
    script, log = notifier_log
    _copy_of_the_file(tmp_path, {"steps.specs": None})

    code, state = _start_through_main(tmp_path, "--notifier", str(script))

    assert code == 3
    assert "steps.specs is missing" in capsys.readouterr().err
    assert "steps.specs is missing" in log.read_text()
    assert not state.exists()


def test_a_refused_change_walk_says_which_chain_refused(tmp_path, capsys, notifier_log):
    """The owner's channel carries both walks. A message that named neither would leave them
    reading the state files to find out which one stopped."""
    script, log = notifier_log
    instance = _instance_with_one_station(tmp_path)
    (instance / "system" / "projects" / PROJECT / "journey" / "tobiishi" / KEY).mkdir()
    (instance / "system" / "projects" / PROJECT / "journey" / "tobiishi" / KEY
     / "change_request.md").write_text("one\n")
    other = instance / "system" / "projects" / PROJECT / "journey" / "tobiishi" / "2026-09-16_two"
    other.mkdir()
    (other / "change_request.md").write_text("two\n")
    state = instance / "system" / "logs" / "state.json"

    code = cd.main(["--start", str(state), "--instance-root", str(instance),
                    "--product-path", str(tmp_path / "product"), "--project", PROJECT,
                    "--core-dir", str(tmp_path / "core"), "--shim-dir", str(state.parent),
                    "--steps", "change", "--notifier", str(script)])

    assert code == 3
    assert "change chain refused to start" in log.read_text()
    assert "more than one active change" in capsys.readouterr().err


def test_a_missing_state_file_names_the_walk_that_has_none(tmp_path, capsys):
    """The last message task 3 left wearing `development`. An advance is the one entry that can
    arrive with no state at all, and for a change walk it was saying the wrong walk's name — the
    path beside it already said `chain-change-`."""
    code = cd.main(["--advance", str(tmp_path / "missing.json"), "station", "completed",
                    "--steps", "change"])

    assert code == 3
    err = capsys.readouterr().err
    assert "no change chain state" in err and "Traceback" not in err


def test_a_change_walk_advances_on_its_own_table_when_the_shim_names_none(tmp_path, notifier_log):
    """The shim fires `--advance <state> <run> <outcome>` and nothing else, so the table is read
    off the state the walk wrote at its start. Measured on a satellite, 2026-09-18: the first
    change walk that entered at `change` crashed on its first advance — `StopIteration`, because
    the development table, which the flag's default picked, has no `change` step. Walks entered
    at a step both tables share had hidden it."""
    script, log = notifier_log
    path = _state_file(tmp_path, notifier=str(script), chain_name="change", key="",
                       pending={"change": {"step": "change", "audited": None}})

    assert cd.main(["--advance", str(path), "change", "timeout"]) == 0

    state = json.loads(path.read_text())
    assert state["ended"] == "halted"
    assert "stopped at change: the run ended timeout" in log.read_text()
    assert "crashed" not in log.read_text()


def test_an_advance_whose_flag_contradicts_its_state_follows_the_state(tmp_path, notifier_log):
    script, log = notifier_log
    path = _state_file(tmp_path, notifier=str(script), chain_name="change", key="",
                       pending={"station": {"step": "station", "audited": None}})

    assert cd.main(["--advance", str(path), "station", "timeout", "--steps", "development"]) == 0

    assert "stopped at station" in log.read_text()


def test_a_crash_with_no_message_still_names_what_raised(tmp_path, notifier_log, monkeypatch):
    """`StopIteration` carries no text, so the satellite's crash message ended in a bare dash."""
    script, log = notifier_log
    path = _state_file(tmp_path, notifier=str(script),
                       pending={"specs": {"step": "specs", "audited": None}})

    def boom(self, run, outcome):
        raise StopIteration

    monkeypatch.setattr(cd.DevelopmentChain, "advance", boom)
    assert cd.main(["--advance", str(path), "specs", "completed"]) == 5
    assert log.read_text().rstrip().endswith("— StopIteration")


# --- the change chain refines the route after the seal -------------------------------------------
#
# `chain-change` does not end at the seal of a unit that serves a station: `shukuba-refine`
# re-reads the project's route from what the unit left. A walk started on a project whose last unit
# is sealed, not yet refined and serving a station — the chain that sealed it ended before this
# step existed, or was `chain-development` — picks up there, off the unit `CONTEXT_PM.md` names,
# the same default `shukuba-refine` itself takes. A unit that serves no station is owed no refine.


NEMAWASHI = f"{INSTANCE}/system/projects/{PROJECT}/journey/nemawashi"
CONTEXT_PM = f"{INSTANCE}/system/projects/{PROJECT}/contexts/CONTEXT_PM.md"
SEED = "2026-09-10_due-dates"


def context_pm(status: str = "Sealed", key: str = KEY) -> str:
    return (f"# CONTEXT_PM\n\n## Current change — PM view\n\n**Status:** {status}\n\n"
            f"`{key}` — the one change reaching station `2026-09-17_a-station`.\n")


UNRELATED_STATION = "an open station that does not name the unit"


def just_sealed(**extra) -> dict:
    """A project whose change was sealed a moment ago: the folder under `trail/`, no change open,
    the worktree and its artifacts gone, the station still open — and naming the unit, so the
    unit serves it — and the context flipped."""
    return {STATION: f"the station {KEY} was cut for",
            f"{TOBIISHI}/trail/{KEY}/change_request.md": "sealed",
            CONTEXT_PM: context_pm(), **extra}


def just_sealed_serving_no_station(**extra) -> dict:
    """`just_sealed`, but the open station is some other one: no station file names the unit."""
    return just_sealed(**{STATION: UNRELATED_STATION, **extra})


def refine_report(home: str = "") -> dict:
    folder = f"{NEMAWASHI}/{home}/{SEED}" if home else f"{NEMAWASHI}/{SEED}"
    return {f"{folder}/{KEY}_report.md": "report", f"{folder}/seed.md": "seed"}


@pytest.mark.parametrize("home", ["", "unpicked", "trail", "drop"])
def test_a_refine_report_in_the_seed_folder_wherever_it_sits_is_the_refine_landing(home):
    assert reader(refine_report(home)).is_done(layout(), change_step("refine"))


def test_another_units_report_is_not_this_units_refine():
    other = {f"{NEMAWASHI}/{SEED}/2026-09-01_older_report.md": "report"}

    assert not reader(other).is_done(layout(), change_step("refine"))


def test_the_sealed_unit_the_context_names_is_owed_a_refine():
    assert reader(just_sealed()).unrefined_sealed_key(INSTANCE, PROJECT) == KEY


@pytest.mark.parametrize("files", [
    {STATION: "station"},
    {STATION: "station", CONTEXT_PM: context_pm(status="Open"),
     f"{TOBIISHI}/trail/{KEY}/change_request.md": "s"},
    {STATION: "station", CONTEXT_PM: context_pm()},
    {**just_sealed(), **refine_report()},
    {k: v for k, v in just_sealed().items() if k != STATION},
], ids=["no-context", "open", "key-not-in-trail", "already-refined", "station-closed"])
def test_no_unit_is_owed_a_refine_unless_the_context_names_a_sealed_unrefined_one(files):
    assert reader(files).unrefined_sealed_key(INSTANCE, PROJECT) is None


def test_a_status_line_carrying_more_after_sealed_still_reads_sealed():
    files = just_sealed()
    files[CONTEXT_PM] = context_pm(status="Sealed — 2026-09-18")

    assert reader(files).unrefined_sealed_key(INSTANCE, PROJECT) == KEY


def test_an_old_sealed_unit_whose_station_closed_lets_the_walk_open_the_next_station():
    """The projects sealed before this step existed: the context still names their last unit, but
    the station is closed and the seed retired, where `shukuba-refine` would stop without a report.
    The walk goes to `station`, as it did before, rather than halting at `refine` on every start."""
    files = {k: v for k, v in just_sealed().items() if k != STATION}

    plan = describe(change_build(FakeFiles(files)))

    assert (plan.key, plan.entry) == ("", "station")


def test_the_station_the_context_names_is_not_mistaken_for_the_unit():
    """The context names the station's stem too; only a token that resolves under `trail/` is
    the unit."""
    files = just_sealed()
    files[CONTEXT_PM] = context_pm().replace(
        f"`{KEY}`", f"station `2026-09-17_a-station`, unit `{KEY}`")

    assert reader(files).unrefined_sealed_key(INSTANCE, PROJECT) == KEY


def test_a_sealed_change_enters_the_change_walk_at_refine_and_ends_after_it():
    assert reader(just_sealed()).entry_step(layout(), cd.CHANGE_STEPS).id == "refine"
    assert reader({**just_sealed(), **refine_report()}).entry_step(
        layout(), cd.CHANGE_STEPS) is None


def test_running_the_change_walk_on_a_just_sealed_project_enters_at_refine():
    """The owner's case: `chain-change <project>` right after a seal carries the sealed unit's
    key into `refine` — not `tobiishi-open` for the next change, and not a refusal over the
    code-integrity report the removed worktree no longer holds."""
    plan = describe(change_build(FakeFiles(just_sealed())))

    assert (plan.key, plan.entry) == (KEY, "refine")


def test_once_refined_the_change_walk_moves_on_to_the_next_change():
    plan = describe(change_build(FakeFiles({**just_sealed(), **refine_report()})))

    assert (plan.key, plan.entry) == ("", "change")


def test_a_development_walk_never_refines_and_still_refuses_with_no_change_open():
    with pytest.raises(cd.ChainRefused, match="no active change"):
        describe(build(FakeFiles(just_sealed())))


def test_a_start_on_a_just_sealed_project_launches_shukuba_refine_with_the_key():
    files = FakeFiles(just_sealed())
    processes = FakeProcesses()

    start(change_build(files, processes=processes))

    assert processes.launched == [[SKILL_LAUNCHER, "shukuba-refine", PROJECT, KEY]]
    assert saved(files)["key"] == KEY


# The two marks that make a sealed unit serve a station, and the cases around them. Each is the
# disk, and the units whose landed commits carry a `Shukuba:` trailer, that `kind` describes.
SERVES_A_STATION = ["file", "trailer"]


def _station_marks(kind: str | None) -> tuple[dict, set[str]]:
    if kind == "file":
        return {STATION: f"the station {KEY} was cut for"}, set()
    if kind == "trailer":
        return {STATION: UNRELATED_STATION}, {KEY}
    if kind == "two-files":
        return {STATION: f"one station for {KEY}",
                f"{SHUKUBA}/parked/2026-09-18_b.md": f"another station for {KEY}"}, set()
    return {STATION: UNRELATED_STATION}, set()


def _change_walk_through_audit(kind: str | None = "file"):
    """A `chain-change` walk entering at the seal, over a unit whose station marks are `kind`'s
    — a station file naming it by default, so it serves a station."""
    disk, git = _through("audit")
    marks, trailers = _station_marks(kind)
    git.shukuba_keys.update(trailers)
    files = FakeFiles({**disk, **marks})
    processes, notifier, lock = FakeProcesses(), FakeNotifier(), FakeLock()
    start(change_build(files, git=git, processes=processes, notifier=notifier, lock=lock))
    return files, git, processes, notifier, lock


def test_the_seal_landing_on_a_change_walk_launches_the_refine_instead_of_ending():
    files, git, processes, notifier, lock = _change_walk_through_audit()
    land(files, git, "seal")

    change_build(files, git=git, processes=processes, notifier=notifier, lock=lock).advance(
        "seal", "completed")

    assert saved(files)["ended"] is None
    assert processes.launched[-1] == [SKILL_LAUNCHER, "shukuba-refine", PROJECT, KEY]


def test_the_refine_landing_ends_the_change_walk_sealed():
    files, git, processes, notifier, lock = _change_walk_through_audit()
    land(files, git, "seal")
    engine = lambda: change_build(files, git=git, processes=processes, notifier=notifier,
                                  lock=lock)
    engine().advance("seal", "completed")
    for path, text in refine_report().items():
        files.write_text(path, text)

    engine().advance("refine", "completed")

    assert saved(files)["ended"] == "sealed"
    ordinary = _the_sealed_end_of_a_development_walk().split(" — ", 1)[1]
    assert notifier.messages[-1] == f"instance · {PROJECT} · change chain — {ordinary}"


def test_a_refine_that_left_no_report_halts_naming_it():
    files, git, processes, notifier, lock = _change_walk_through_audit()
    land(files, git, "seal")
    engine = lambda: change_build(files, git=git, processes=processes, notifier=notifier,
                                  lock=lock)
    engine().advance("seal", "completed")

    engine().advance("refine", "completed")

    state = saved(files)
    assert state["ended"] == "halted"
    assert f"stopped at refine: no {KEY}_report.md" in state["ended_reason"]


# --- the refine is owed only by a unit that serves a station --------------------------------------
#
# `shukuba-refine` finds its station through two marks and stops without a report when it finds
# none. A hand-opened change has neither, so a walk that launched the refine for it would end
# `halted` on a walk that sealed cleanly. After the seal has landed the walk asks whether the unit
# serves a station: a unit that does goes on to its refine, one that does not ends `sealed`.


def _skills_launched(processes: "FakeProcesses") -> list[str]:
    return [argv[1] for argv in processes.launched if argv[0] == SKILL_LAUNCHER]


def _seal_landing(kind: str | None, **walk_arguments) -> "HookedWalk":
    """A `chain-change` walk entering at the seal over a unit with `kind`'s station marks, whose
    seal has just landed and been delivered to the engine."""
    walk = HookedWalk(steps=cd.CHANGE_STEPS, station_marks=kind, **walk_arguments)
    land(walk.files, walk.git, "seal")
    walk.engine().advance("seal", "completed")
    return walk


def _the_sealed_end_of_a_development_walk() -> str:
    """What `chain-development` tells the owner when the same unit's seal lands: the ordinary
    sealed message every sealed walk sends."""
    walk = Walk(through="audit")
    land(walk.files, walk.git, "seal")
    walk.advance("seal")
    return walk.notifier.messages[-1]


def test_no_station_change_ends_sealed_without_refine():
    """The walk's one end message reads as any sealed walk's does, and the hook runs once."""
    walk = _seal_landing(None)

    assert saved(walk.files)["ended"] == "sealed"
    assert "shukuba-refine" not in _skills_launched(walk.processes)
    ordinary = _the_sealed_end_of_a_development_walk().split(" — ", 1)[1]
    assert walk.notifier.messages[-1] == f"instance · {PROJECT} · change chain — {ordinary}"
    assert [call["argv"] for call in walk.hook_calls] == [[*HOOK_ARGV, "sealed"]]


@pytest.mark.parametrize("kind", SERVES_A_STATION)
def test_station_served_change_waits_for_refine_report(kind):
    files, git, processes, notifier, lock = _change_walk_through_audit(kind)
    land(files, git, "seal")
    engine = lambda: change_build(files, git=git, processes=processes, notifier=notifier,
                                  lock=lock)

    engine().advance("seal", "completed")

    assert saved(files)["ended"] is None
    assert not any("sealed" in message for message in notifier.messages)
    assert processes.launched[-1] == [SKILL_LAUNCHER, "shukuba-refine", PROJECT, KEY]
    for path, text in refine_report().items():
        files.write_text(path, text)

    engine().advance("refine", "completed")

    assert saved(files)["ended"] == "sealed"
    assert f"sealed {KEY}" in notifier.messages[-1]


@pytest.mark.parametrize("kind", ["two-files", "trailer"],
                         ids=["several-matching-files", "trailer-naming-no-station"])
def test_unresolved_station_membership_still_requires_a_refine_report(kind):
    """The refine's own stop on more than one station, or on none it can find, is a finding the
    walk reports; the walk does not decide it."""
    files, git, processes, notifier, lock = _change_walk_through_audit(kind)
    land(files, git, "seal")
    engine = lambda: change_build(files, git=git, processes=processes, notifier=notifier,
                                  lock=lock)
    engine().advance("seal", "completed")
    assert processes.launched[-1] == [SKILL_LAUNCHER, "shukuba-refine", PROJECT, KEY]

    engine().advance("refine", "completed")

    state = saved(files)
    assert state["ended"] == "halted"
    assert state["ended_reason"].startswith(f"stopped at refine: no {KEY}_report.md")


def _seal_failed(kind: str | None, failure: str):
    files, git, processes, notifier, lock = _change_walk_through_audit(kind)
    outcome = "completed"
    if failure == "run-ended-failed":
        outcome = "timeout"
    elif failure == "no-main-trail":
        pass
    else:
        folder = (BRANCH_CHANGE if failure == "report-before-move"
                  else f"{WORKTREE}/system/projects/{PROJECT}/journey/tobiishi/trail/{KEY}")
        files.write_text(f"{folder}/halt_report.md", "the seal halted")
    change_build(files, git=git, processes=processes, notifier=notifier, lock=lock).advance(
        "seal", outcome)
    return files, git, processes


@pytest.mark.parametrize("failure", ["run-ended-failed", "no-main-trail", "report-before-move",
                                     "report-after-move"])
def test_seal_failures_halt_before_station_membership_is_read(failure):
    """Whether the unit serves a station changes nothing about why the seal stopped."""
    reasons = set()
    for kind in [None, "file", "trailer"]:
        files, git, processes = _seal_failed(kind, failure)

        state = saved(files)
        assert state["ended"] == "halted"
        assert state["ended_reason"].startswith("stopped at seal: ")
        assert "shukuba-refine" not in _skills_launched(processes)
        assert git.shukuba_calls == []
        reasons.add(state["ended_reason"])

    assert len(reasons) == 1


@pytest.mark.parametrize("kind, ends", [(None, "sealed"), ("file", None), ("trailer", None)],
                         ids=["no-station", "station-file", "station-trailer"])
def test_inherited_halt_report_does_not_veto_an_evidenced_seal(kind, ends):
    """A seal that completed and left its folder under `trail/` is evidenced, whatever an earlier
    run's report still says: the artifact wins over the report, as it does before this change."""
    files, git, processes, notifier, lock = _change_walk_through_audit(kind)
    land(files, git, "seal")
    files.write_text(f"{TOBIISHI}/{KEY}/halt_report.md", "an earlier run's halt")

    change_build(files, git=git, processes=processes, notifier=notifier, lock=lock).advance(
        "seal", "completed")

    assert saved(files)["ended"] == ends
    assert ("shukuba-refine" in _skills_launched(processes)) is (ends is None)


@pytest.mark.parametrize("files, entry, launched", [
    (just_sealed_serving_no_station(), "change", "tobiishi-open"),
    ({k: v for k, v in just_sealed_serving_no_station().items() if k != STATION}, "station",
     "shukuba-open"),
], ids=["with-an-unrelated-open-station", "with-no-open-station"])
def test_no_station_sealed_unit_starts_without_its_old_key(files, entry, launched):
    plan = describe(change_build(FakeFiles(files)))
    processes = FakeProcesses()

    start(change_build(FakeFiles(files), processes=processes))

    assert (plan.key, plan.entry) == ("", entry)
    assert processes.launched == [[SKILL_LAUNCHER, launched, PROJECT]]


@pytest.mark.parametrize("kind", SERVES_A_STATION)
def test_station_served_sealed_unit_starts_at_refine(kind):
    marks, trailers = _station_marks(kind)
    files = FakeFiles(just_sealed(**marks))
    git = FakeGit(shukuba_keys=trailers)
    processes = FakeProcesses()

    plan = describe(change_build(files, git=git))
    start(change_build(files, git=git, processes=processes))

    assert (plan.key, plan.entry) == (KEY, "refine")
    assert processes.launched == [[SKILL_LAUNCHER, "shukuba-refine", PROJECT, KEY]]


@pytest.mark.parametrize("files", [
    {STATION: "station"},
    {STATION: "station", CONTEXT_PM: context_pm(status="Open"),
     f"{TOBIISHI}/trail/{KEY}/change_request.md": "s"},
    {STATION: "station", CONTEXT_PM: context_pm()},
    {**just_sealed(), **refine_report()},
    {k: v for k, v in just_sealed().items() if k != STATION},
], ids=["no-context", "open", "key-not-in-trail", "already-refined", "station-closed"])
def test_restart_retains_context_trail_report_and_closed_station_gates(files):
    """A unit that serves a station is still owed nothing when the context, the trail, its report
    or its open station says the route has moved on — marks alone never revive a refine."""
    git = FakeGit(shukuba_keys={KEY})

    assert reader(files, git=git).unrefined_sealed_key(INSTANCE, PROJECT) is None


def test_another_units_report_does_not_settle_this_units_refine():
    other = {f"{NEMAWASHI}/{SEED}/2026-09-01_older_report.md": "report"}

    assert reader(just_sealed(**other)).unrefined_sealed_key(INSTANCE, PROJECT) == KEY


def test_a_closed_station_that_names_the_unit_still_lets_the_walk_open_the_next_one():
    """The station moved to `trail/` still names the unit, so the unit serves it. The route has
    moved on all the same, and the walk goes to `station`."""
    files = {k: v for k, v in just_sealed().items() if k != STATION}
    files[f"{SHUKUBA}/trail/2026-09-17_a-station.md"] = f"closed — {KEY}"

    plan = describe(change_build(FakeFiles(files)))

    assert (plan.key, plan.entry) == ("", "station")


def test_sealed_key_stays_available_after_refinement_and_station_closure():
    """`build-idea` reads the sealed unit through it: no mark, no open station and no missing
    report are asked of it — a no-station unit included."""
    refined = reader({**just_sealed_serving_no_station(), **refine_report()})
    closed = reader({k: v for k, v in just_sealed_serving_no_station().items() if k != STATION})

    assert refined.sealed_key(INSTANCE, PROJECT) == KEY
    assert closed.sealed_key(INSTANCE, PROJECT) == KEY


def test_development_walk_seals_without_reading_station_membership():
    files, git = _through("audit")
    walk_files = FakeFiles(files)
    processes, notifier, lock = FakeProcesses(), FakeNotifier(), FakeLock()
    start(build(walk_files, git=git, processes=processes, notifier=notifier, lock=lock))
    land(walk_files, git, "seal")

    build(walk_files, git=git, processes=processes, notifier=notifier, lock=lock).advance(
        "seal", "completed")

    assert saved(walk_files)["ended"] == "sealed"
    assert git.shukuba_calls == []
    assert "refine" not in [entry.id for entry in cd.DEVELOPMENT_STEPS]
    assert "shukuba-refine" not in _skills_launched(processes)


def test_no_station_ending_ignores_duplicate_and_stale_callbacks():
    walk = _seal_landing(None)
    messages, hooks, launches = (len(walk.notifier.messages), len(walk.hook_calls),
                                 len(walk.processes.launched))

    walk.engine().advance("seal", "completed")
    walk.engine().advance("refine", "completed")
    walk.engine().advance("never-launched", "completed")

    assert (len(walk.notifier.messages), len(walk.hook_calls),
            len(walk.processes.launched)) == (messages, hooks, launches)
    assert saved(walk.files)["ended"] == "sealed"
    assert walk.state_when_hook_ran == ["sealed"]
    assert walk.lock_held_when_hook_ran == [False]


# --- the two reads a queue over a refine report reuses --------------------------------------------
#
# `build-idea` starts from a unit that is already refined and whose station may already be closed —
# the two states `unrefined_sealed_key` answers `None` for. So the unit's key and its report's path
# are read by two methods that carry neither gate, and the two older reads are built on top of them.


def test_sealed_key_names_the_sealed_unit_even_once_refined():
    disk = reader({**just_sealed(), **refine_report()})

    assert disk.sealed_key(INSTANCE, PROJECT) == KEY
    assert disk.unrefined_sealed_key(INSTANCE, PROJECT) is None


def test_sealed_key_does_not_need_an_open_station():
    files = {k: v for k, v in just_sealed().items() if k != STATION}

    assert reader(files).sealed_key(INSTANCE, PROJECT) == KEY
    assert reader(files).unrefined_sealed_key(INSTANCE, PROJECT) is None


@pytest.mark.parametrize("files", [
    {STATION: "station"},
    {CONTEXT_PM: context_pm(status="Open"), f"{TOBIISHI}/trail/{KEY}/change_request.md": "s"},
    {CONTEXT_PM: context_pm()},
], ids=["no-context", "not-sealed", "key-not-in-trail"])
def test_sealed_key_is_none_without_a_sealed_status_or_a_trail_folder(files):
    assert reader(files).sealed_key(INSTANCE, PROJECT) is None


@pytest.mark.parametrize("home", ["", "unpicked", "trail", "drop"])
def test_report_path_finds_the_report_in_each_seed_home(home):
    folder = f"{NEMAWASHI}/{home}/{SEED}" if home else f"{NEMAWASHI}/{SEED}"

    assert reader(refine_report(home)).report_path(layout()) == f"{folder}/{KEY}_report.md"


def test_report_path_is_none_when_no_seed_holds_the_report():
    other = {f"{NEMAWASHI}/{SEED}/2026-09-01_older_report.md": "report"}

    assert reader(other).report_path(layout()) is None


# --- a sealed unit serves a station when a mark says so -------------------------------------------
#
# `shukuba-refine` finds a unit's station by two marks: a `Shukuba:` trailer on the commits the unit
# landed, or the one station file naming its key. The walk reads exactly those two, so a unit with
# neither is the one whose refine could only stop without a report.


def _serving(files: dict | None = None, *, git: FakeGit | None = None,
             key: str = KEY) -> tuple[bool, FakeGit]:
    git = git or FakeGit()
    answer = cd.DiskReader(files=FakeFiles(files), git=git).serves_station(layout(key))
    return answer, git


def _station_in(home: str, text: str = f"a station for {KEY}") -> dict:
    folder = f"{SHUKUBA}/{home}" if home else SHUKUBA
    return {f"{folder}/2026-09-17_a-station.md": text}


def test_change_with_no_station_marks_serves_no_station():
    unrelated_root_station = {f"{SHUKUBA}/2026-09-17_a-station.md": "an unrelated station"}

    answer, _ = _serving(unrelated_root_station)

    assert answer is False


@pytest.mark.parametrize("files, trailer", [
    ({}, True),
    (_station_in(""), False),
    (_station_in("trail"), False),
    (_station_in("parked"), False),
    (_station_in("trail"), True),
    ({**_station_in(""), f"{SHUKUBA}/trail/2026-09-01_old.md": f"also {KEY}"}, False),
], ids=["trailer-only", "root-file", "trail-file", "parked-file", "both-marks", "two-files"])
def test_any_station_mark_establishes_membership(files, trailer):
    git = FakeGit(shukuba_keys={KEY} if trailer else ())

    answer, _ = _serving(files, git=git)

    assert answer is True


def test_trailer_membership_does_not_require_a_resolvable_station():
    """A trailer naming a station that is not on disk — or naming none — still counts: the refine
    runs and its own stop on a missing station stands (the ambiguous-marks case)."""
    answer, _ = _serving({}, git=FakeGit(shukuba_keys={KEY}))

    assert answer is True


@pytest.mark.parametrize("files", [
    {f"{SHUKUBA}/README.md": f"mentions {KEY}"},
    {f"{SHUKUBA}/trail/README.md": f"mentions {KEY}"},
    {f"{NEMAWASHI}/{SEED}/seed.md": f"mentions {KEY}"},
    {CONTEXT_PM: context_pm()},
    {f"{SHUKUBA}/2026-09-17_a-station.md": "names another unit 2026-09-01_other"},
    {f"{SHUKUBA}/2026-09-17_a-station.txt": f"not markdown, names {KEY}"},
    {f"{SHUKUBA}/trail/2026-09-17_a-folder.md/inner.txt": f"a directory, names {KEY}"},
    {f"{SHUKUBA}/trail/notes/inner.md": f"nested, names {KEY}"},
    {f"{SHUKUBA}/other/2026-09-17_a-station.md": f"not a station home, names {KEY}"},
], ids=["root-readme", "trail-readme", "seed", "context", "unrelated-station", "non-markdown",
        "directory-named-md", "nested-file", "foreign-home"])
def test_non_station_mentions_do_not_establish_membership(files):
    answer, _ = _serving(files)

    assert answer is False


def test_an_empty_key_cannot_establish_membership():
    """Not even a mark that would match every key, and the history is not asked."""
    files = _station_in("", text="every station mentions the empty string")
    git = FakeGit(shukuba_keys={""})

    answer, git = _serving(files, git=git, key="")

    assert answer is False
    assert git.shukuba_calls == []


def test_membership_history_is_read_from_the_instance_repository():
    """The unit's commits land in the instance's history even when the product lives in another
    repository, so the question names the instance root and the unit's key — and an external
    product's own marks are not consulted."""
    git = FakeGit(shukuba_keys={KEY}, repos={PRODUCT: {"main": []}})

    answer, git = _serving({}, git=git)

    assert answer is True
    assert git.shukuba_calls == [(INSTANCE, KEY)]


# The real adapter, over disposable repositories: the unit's branch is gone after delivery, so the
# merge's second-parent range is the only record of what the unit landed.


def _commit(root: Path, subject: str, trailer: str | None = None) -> None:
    message = subject if trailer is None else f"{subject}\n\n{trailer}"
    _git(root, "commit", "-q", "--allow-empty", "-m", message)


def _delivered(root: Path, key: str, *messages: tuple[str, str | None],
               wrapper: str | None = None) -> None:
    """Land `key` on `main` the way the seal does: a branch of commits merged `--no-ff`, whose
    subject is `merge: <key> → main`, then the branch removed."""
    _git(root, "checkout", "-q", "-b", key, "main")
    for subject, trailer in messages:
        _commit(root, subject, trailer)
    _git(root, "checkout", "-q", "main")
    note = f"merge: {key} → main" if wrapper is None else f"merge: {key} → main\n\n{wrapper}"
    _git(root, "merge", "-q", "--no-ff", "-m", note, key)
    _git(root, "branch", "-q", "-D", key)


@pytest.fixture
def history(tmp_path):
    root = tmp_path / "instance"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _commit(root, "root")
    return root


STATION_TRAILER = "Shukuba: 2026-09-17_a-station — progress: step"


def test_landed_commit_trailer_establishes_membership_after_branch_deletion(history):
    _delivered(history, KEY, ("open", None), ("task", STATION_TRAILER), ("seal", None))

    assert cd.Git().unit_has_shukuba(str(history), KEY) is True


def test_the_trailer_value_is_never_read(history):
    """Present is what counts: an empty value, and a value naming no station."""
    _delivered(history, KEY, ("open", "Shukuba:"))

    assert cd.Git().unit_has_shukuba(str(history), KEY) is True


def test_a_unit_without_a_trailer_serves_no_station_by_its_history(history):
    _delivered(history, KEY, ("open", "Agari: tracker — progress: step"), ("seal", None))

    assert cd.Git().unit_has_shukuba(str(history), KEY) is False


def test_unrelated_history_and_delivery_wrapper_do_not_establish_membership(history):
    """A station trailer on another unit's commit, on a commit made directly on `main`, and on the
    delivery merge itself all sit outside the range the unit landed."""
    _commit(history, "direct on main", STATION_TRAILER)
    _delivered(history, "2026-09-01_other", ("other open", STATION_TRAILER))
    _delivered(history, KEY, ("open", None), ("seal", None), wrapper=STATION_TRAILER)

    assert cd.Git().unit_has_shukuba(str(history), KEY) is False


def test_newest_matching_delivery_merge_supplies_station_evidence(history):
    """The unit was delivered twice: an older delivery that carried the trailer, then a newer one
    that did not. Only the newest merge's range answers."""
    _delivered(history, KEY, ("first", STATION_TRAILER))
    _delivered(history, KEY, ("second", None))

    assert cd.Git().unit_has_shukuba(str(history), KEY) is False


def test_the_newest_merge_wins_in_the_other_direction_too(history):
    _delivered(history, KEY, ("first", None))
    _delivered(history, KEY, ("second", STATION_TRAILER))

    assert cd.Git().unit_has_shukuba(str(history), KEY) is True


@pytest.mark.parametrize("later_key", [f"{KEY}-two", f"{KEY}__audit-development-specs"],
                         ids=["a-longer-key", "an-audit-branch"])
def test_a_later_merge_whose_key_only_begins_with_this_one_is_not_its_delivery(history,
                                                                               later_key):
    """The delivery merge is `merge: <key> →` — the key, then the arrow. A newer merge of a branch
    whose name merely starts with the key is another unit's, and its range is not this unit's."""
    _delivered(history, KEY, ("seal", STATION_TRAILER))
    _delivered(history, later_key, ("other", None))

    assert cd.Git().unit_has_shukuba(str(history), KEY) is True


def test_legacy_message_key_history_supplies_station_evidence(history):
    """With no delivery merge, only reachable commits whose messages name this key count."""
    _commit(history, f"tools: open change {KEY}", STATION_TRAILER)
    _commit(history, "tools: another unit", STATION_TRAILER)

    assert cd.Git().unit_has_shukuba(str(history), KEY) is True
    assert cd.Git().unit_has_shukuba(str(history), "2026-09-01_third") is False


def test_legacy_history_ignores_another_keys_trailer_and_a_key_with_no_trailer(history):
    _commit(history, f"tools: open change {KEY}", "Agari: tracker — progress: step")
    _commit(history, "tools: open change 2026-09-01_other", STATION_TRAILER)

    assert cd.Git().unit_has_shukuba(str(history), KEY) is False


def test_body_prose_is_not_a_station_trailer(history):
    _delivered(history, KEY,
               ("open", None),
               ("prose\n\nThe line `Shukuba: x` is mentioned here, mid-paragraph.\n\n"
                "Agari: tracker — progress: step", None))

    assert cd.Git().unit_has_shukuba(str(history), KEY) is False


def test_an_empty_key_or_a_missing_history_is_no_membership(history, tmp_path):
    _delivered(history, KEY, ("open", STATION_TRAILER))
    not_a_repository = tmp_path / "plain"
    not_a_repository.mkdir()

    assert cd.Git().unit_has_shukuba(str(history), "") is False
    assert cd.Git().unit_has_shukuba(str(not_a_repository), KEY) is False


# --- the walk's end runs an optional hook ---------------------------------------------------------
#
# `chain-change` wires its walk's end to `build-idea`: when the walk ends, sealed or halted, the
# command it was started with runs once with that end appended. The hook is carried on the walk's
# state, because the run that ends a walk is a fresh process that was handed only a state path.

HOOK = "/hooks/next-queue.sh --chain-ended"
HOOK_ARGV = ["/hooks/next-queue.sh", "--chain-ended"]


class HookedWalk:
    """One engine over one scripted disk, started with `on_end` and entering at `seal` — the one
    step from which a single landing ends a walk sealed."""

    def __init__(self, on_end: str = HOOK, through: str = "audit", codes=None, steps=None,
                 environ=None, station_marks: str | None = None, **start_arguments):
        disk, self.git = _through(through)
        marks, trailers = _station_marks(station_marks) if steps else ({}, set())
        self.git.shukuba_keys.update(trailers)
        self.files = FakeFiles({**disk, **marks})
        self.notifier = FakeNotifier()
        self.processes = FakeProcesses(codes=codes, on_run=self._look_at_the_state)
        self.steps = steps
        self.environ = environ
        self.lock = FakeLock()
        self.state_when_hook_ran: list = []
        self.lock_held_when_hook_ran: list = []
        start(self.engine(), on_end=on_end, **start_arguments)

    def _look_at_the_state(self, argv):
        if argv[:2] == HOOK_ARGV:
            self.state_when_hook_ran.append(saved(self.files)["ended"])
            self.lock_held_when_hook_ran.append(self.lock.held)

    def engine(self):
        return build(self.files, git=self.git, processes=self.processes, notifier=self.notifier,
                     lock=self.lock, steps=self.steps, environ=self.environ)

    @property
    def hook_calls(self) -> list[dict]:
        return [call for call in self.processes.calls if call["argv"][:2] == HOOK_ARGV]


def test_a_sealed_walk_runs_its_on_end_hook_once_with_sealed_appended():
    walk = HookedWalk()
    land(walk.files, walk.git, "seal")

    walk.engine().advance("seal", "completed")

    assert saved(walk.files)["ended"] == "sealed"
    assert [call["argv"] for call in walk.hook_calls] == [[*HOOK_ARGV, "sealed"]]
    assert walk.hook_calls[0]["cwd"] == INSTANCE


def test_the_on_end_hook_of_an_unforced_walk_carries_no_provider():
    """The hook starts the next queue, whose chains read the variable as a force — and the one
    the engine inherited is only the last step's provider."""
    walk = HookedWalk(environ={"PATH": "/usr/bin", "KENSAIAPP_AGENT_PROVIDER": "codex"})
    land(walk.files, walk.git, "seal")

    walk.engine().advance("seal", "completed")

    assert "KENSAIAPP_AGENT_PROVIDER" not in walk.hook_calls[0]["env"]
    assert walk.hook_calls[0]["env"]["PATH"] == "/usr/bin"


def test_the_on_end_hook_of_a_forced_walk_carries_the_force():
    walk = HookedWalk(forced_provider="codex")
    land(walk.files, walk.git, "seal")

    walk.engine().advance("seal", "completed")

    assert walk.hook_calls[0]["env"]["KENSAIAPP_AGENT_PROVIDER"] == "codex"


def test_a_halted_walk_runs_its_on_end_hook_with_halted_appended():
    walk = HookedWalk()

    walk.engine().advance("seal", "timeout")

    assert saved(walk.files)["ended"] == "halted"
    assert [call["argv"] for call in walk.hook_calls] == [[*HOOK_ARGV, "halted"]]


def test_a_halt_raised_inside_start_runs_the_hook_too():
    """The first launcher exiting non-zero ends the walk before any advance can."""
    walk = HookedWalk(through=None, codes=[3])

    assert saved(walk.files)["ended"] == "halted"
    assert [call["argv"] for call in walk.hook_calls] == [[*HOOK_ARGV, "halted"]]


def test_the_hook_runs_after_the_ended_state_is_saved():
    """A hook that starts the next queue reads this walk's state, so it must read an ended one."""
    walk = HookedWalk()
    land(walk.files, walk.git, "seal")

    walk.engine().advance("seal", "completed")

    assert walk.state_when_hook_ran == ["sealed"]


def test_the_hook_runs_after_the_advance_releases_the_state_lock():
    """A hook that starts the next walk on the same project takes this state file's lock. Run
    under the lock, it waits on the process that is waiting on it: build-idea's first loop hung
    this way on 2026-09-18."""
    walk = HookedWalk()
    land(walk.files, walk.git, "seal")

    walk.engine().advance("seal", "completed")

    assert walk.lock_held_when_hook_ran == [False]


def test_the_hook_runs_after_a_start_that_halts_releases_the_state_lock():
    walk = HookedWalk(through=None, codes=[3])

    assert saved(walk.files)["ended"] == "halted"
    assert walk.lock_held_when_hook_ran == [False]


def test_a_walk_with_no_hook_runs_no_extra_process():
    walk = HookedWalk(on_end="", through=None, codes=[3])

    assert saved(walk.files)["ended"] == "halted"
    assert walk.processes.launched == [[SKILL_LAUNCHER, "development-specs", PROJECT]]


@pytest.mark.parametrize("hook_exit", [1, -1])
def test_a_failing_hook_sends_one_message_and_leaves_the_end_untouched(hook_exit):
    """`-1` is `Processes.run`'s answer for a command that could not be started at all."""
    walk = HookedWalk(through=None, codes=[3, hook_exit])
    before = saved(walk.files)

    messages = [message for message in walk.notifier.messages if HOOK in message]

    assert len(messages) == 1 and f"exited {hook_exit}" in messages[0]
    assert (before["ended"], before["ended_reason"]) == (
        "halted", "stopped at specs: launcher exited 3")


def test_a_hook_that_cannot_be_parsed_is_reported_and_raises_nothing():
    walk = HookedWalk(on_end="'/hooks/unbalanced.sh --chain-ended", through=None, codes=[3])

    assert saved(walk.files)["ended"] == "halted"
    assert len([m for m in walk.notifier.messages if "unbalanced.sh" in m]) == 1
    assert walk.processes.launched == [[SKILL_LAUNCHER, "development-specs", PROJECT]]


def test_the_hook_is_split_the_way_a_shell_quotes_it():
    walk = HookedWalk(on_end="'/a dir/hook.sh' --chain-ended", through=None, codes=[3])

    assert walk.processes.launched[-1] == ["/a dir/hook.sh", "--chain-ended", "halted"]


def test_the_hook_survives_the_advance_boundary():
    """Set at `--start`, it fires from a later `advance` in a fresh engine built off the state."""
    walk = HookedWalk()
    assert saved(walk.files)["on_end"] == HOOK
    land(walk.files, walk.git, "seal")

    walk.engine().advance("seal", "completed")

    assert len(walk.hook_calls) == 1


def test_a_state_written_without_on_end_still_loads():
    state = cd.WalkState(instance_root=INSTANCE, product_path=PRODUCT, project=PROJECT,
                         core_dir=CORE, shim_dir=LOGS, engine_path=ENGINE, key=KEY,
                         walk_id="walk-1", product_docs=f"{PRODUCT}/docs")
    older = state.to_json()
    older.pop("on_end", None)

    assert cd.WalkState.from_json(older).on_end == ""


def test_main_passes_on_end_from_the_cli_to_start(tmp_path):
    """The real composition end to end: the first launcher cannot start (no core on disk), so the
    walk halts inside `start`, and the hook the command line carried runs with `halted`."""
    instance = _instance_with_one_change(tmp_path)
    log = tmp_path / "hook.log"
    hook = tmp_path / "hook.sh"
    hook.write_text(f"#!/usr/bin/env bash\nprintf '%s\\n' \"$@\" >> {log}\n")
    hook.chmod(0o755)
    state = instance / "system" / "logs" / "state.json"

    code = cd.main(["--start", str(state), "--instance-root", str(instance),
                    "--product-path", str(tmp_path / "product"), "--project", PROJECT,
                    "--core-dir", str(tmp_path / "no-core"), "--shim-dir", str(state.parent),
                    "--on-end", str(hook)])

    assert code == 0
    assert log.read_text().splitlines() == ["halted"]
    assert json.loads(state.read_text())["on_end"] == str(hook)


def test_describe_ignores_on_end(tmp_path):
    instance = _instance_with_one_change(tmp_path)
    log = tmp_path / "hook.log"
    hook = tmp_path / "hook.sh"
    hook.write_text(f"#!/usr/bin/env bash\nprintf '%s\\n' \"$@\" >> {log}\n")
    hook.chmod(0o755)

    code = cd.main(["--describe", str(tmp_path / "state.json"), "--instance-root", str(instance),
                    "--project", PROJECT, "--on-end", str(hook)])

    assert code == 0
    assert not log.exists()


# --- the developer's context cap: carried on the walk, set on the implementation run only -------


CAP_VARIABLE = "KENSAIAPP_CONTEXT_CAP"


def _start_through_main(tmp_path, *extra) -> tuple[int, Path]:
    """The real composition, as `test_main_passes_on_end_from_the_cli_to_start` builds it: no core
    on disk, so the first launch halts inside `start` and the state it wrote can be read back."""
    instance = _instance_with_one_change(tmp_path)
    state = instance / "system" / "logs" / "state.json"
    code = cd.main(["--start", str(state), "--instance-root", str(instance),
                    "--product-path", str(tmp_path / "product"), "--project", PROJECT,
                    "--core-dir", str(tmp_path / "no-core"), "--shim-dir", str(state.parent),
                    *extra])
    return code, state


def test_context_cap_defaults_to_250000(tmp_path):
    code, state = _start_through_main(tmp_path)

    assert code == 0
    assert cd.DEFAULT_CONTEXT_CAP == 250000
    assert json.loads(state.read_text())["context_cap"] == 250000


def test_context_cap_is_recorded_from_the_flag(tmp_path):
    code, state = _start_through_main(tmp_path, "--context-cap", "80000")

    assert code == 0
    assert json.loads(state.read_text())["context_cap"] == 80000


@pytest.mark.parametrize("bad", ["abc", "0", "-5", "1.5", ""])
def test_a_context_cap_that_is_not_a_positive_integer_is_refused(tmp_path, capsys, bad):
    with pytest.raises(SystemExit) as refused:
        _start_through_main(tmp_path, "--context-cap", bad)

    assert refused.value.code != 0
    refusal = capsys.readouterr().err
    assert "--context-cap" in refusal and "positive integer" in refusal
    assert not (tmp_path / "instance" / "system" / "logs" / "state.json").exists()


def test_a_rebuilt_walk_state_keeps_its_cap():
    state = cd.WalkState(instance_root=INSTANCE, product_path=PRODUCT, project=PROJECT,
                         core_dir=CORE, shim_dir=LOGS, engine_path=ENGINE, key=KEY,
                         walk_id="walk-1", product_docs=f"{PRODUCT}/docs", context_cap=80000)

    assert cd.WalkState.from_json(state.to_json()).context_cap == 80000

    older = state.to_json()
    del older["context_cap"]
    assert cd.WalkState.from_json(older).context_cap == cd.DEFAULT_CONTEXT_CAP


def test_the_implementation_run_gets_the_cap_in_its_environment():
    files, git = _through("plan")
    processes = FakeProcesses()

    start(build(FakeFiles(files), git=git, processes=processes), context_cap=80000)

    assert processes.launched == [[SKILL_LAUNCHER, "development-implementation", PROJECT, KEY]]
    assert processes.calls[0]["env"][CAP_VARIABLE] == "80000"


def test_no_other_step_inherits_the_cap():
    """The engine's environment is the previous run's — an `--advance` is fired by that run's
    shim, which inherits its launch environment — so the step after implementation is launched
    from a process that holds the cap, and must not pass it on."""
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    inherited = {"PATH": "/usr/bin", CAP_VARIABLE: "80000"}

    build(walk.files, git=walk.git, processes=walk.processes, notifier=walk.notifier,
          lock=walk.lock, environ=inherited).advance("implementation", "completed")

    assert walk.processes.launched[-1][1] == "development-code-integrity"
    assert CAP_VARIABLE not in walk.processes.calls[-1]["env"]


def test_a_first_step_started_from_a_capped_environment_carries_no_cap():
    processes = FakeProcesses()

    start(build(FakeFiles(fresh_change()), processes=processes,
                environ={"PATH": "/usr/bin", CAP_VARIABLE: "80000"}))

    assert processes.launched == [[SKILL_LAUNCHER, "development-specs", PROJECT]]
    assert CAP_VARIABLE not in processes.calls[0]["env"]


# --- a pause is not an end: the developer run that stopped at the cap is relaunched --------------


def _pause(after: int, sha: str = "9a75e0") -> tuple[str, str]:
    """The pause commit a developer run past the cap leaves — `SKILL.md` Step 2 § Pausing at the
    context cap: an empty commit whose subject names the last task it committed."""
    return (sha, f"developer: {KEY} — implementation paused after task {after}")


TASK_COMMITS = [("7a5c03", "developer: task 3 tidy — green"),
                ("7a5c02", "developer: task 3 tidy — red"),
                ("7a5c01", "developer: task 2 tidy — green")]


def test_a_pause_commit_is_not_the_closing_marker():
    git = FakeGit(commits={KEY: [_pause(3), *TASK_COMMITS]})

    disk = reader(git=git)

    assert disk.marker_commit(layout()) is None
    assert not disk.is_done(layout(), step("implementation"))
    assert disk.paused_after(layout(), PRODUCT) == 3


def test_a_paused_run_relaunches_the_developer_after_its_task():
    walk = Walk(through="plan")
    walk.git.commits[KEY] = [_pause(3), *TASK_COMMITS]

    walk.advance("implementation")

    assert walk.processes.launched[-1] == [SKILL_LAUNCHER, "development-implementation",
                                           PROJECT, KEY, "3"]
    assert walk.state["ended"] is None
    assert list(walk.state["pending"]) == ["implementation"]
    assert walk.state["paused_after"] == 3
    assert any(message.endswith("paused after task 3 — resuming")
               for message in walk.notifier.messages)


def test_a_relaunch_enters_through_entry_step():
    files, git = _through("plan")
    git.commits[KEY] = [_pause(3), *TASK_COMMITS]

    assert reader(files, git).entry_step(layout(), cd.DEVELOPMENT_STEPS).id == "implementation"


def test_a_marker_newer_than_a_pause_completes_the_step():
    walk = Walk(through="plan")
    walk.git.commits[KEY] = [MARKER, _pause(3), *TASK_COMMITS]
    walk.git.bodies[MARKER[0]] = MARKER_BODY

    assert reader(git=walk.git).paused_after(layout(), PRODUCT) is None

    walk.advance("implementation")

    assert walk.skills_launched[-1] == "development-code-integrity"
    assert walk.state["ended"] is None
    assert walk.state["paused_after"] is None


def test_two_pauses_then_a_close_reaches_code_integrity():
    """The walk the 2026-10-01 finding asked for: the developer pauses after task 3, is relaunched,
    pauses after task 6, is relaunched, and the third run closes carrying each pause's record under
    its own labelled heading — the body that halted as missing-language, and the reason this test
    fails without `_LANGUAGE_HEADING`."""
    walk = Walk(through="plan")
    first, second = _pause(3), _pause(6, "9a75e1")
    later = [("7a5c06", "developer: task 6 tidy — green"),
             ("7a5c05", "developer: task 6 tidy — red")]
    walk.git.commits[KEY] = [first, *TASK_COMMITS]
    walk.advance("implementation")
    walk.git.commits[KEY] = [second, *later, first, *TASK_COMMITS]
    walk.advance("implementation")
    assert walk.processes.launched[-1][-1] == "6"

    walk.git.commits[KEY] = [MARKER, second, *later, first, *TASK_COMMITS]
    walk.git.bodies[MARKER[0]] = ("Suite: green\n\n"
                                  "Language resolution (tasks 1 to 3, from 9a75e0):\n- python\n\n"
                                  "Language resolution (tasks 4 to 6, from 9a75e1):\n- python\n"
                                  f"\n{ENVIRONMENT_LINE}\n")
    walk.advance("implementation")

    assert walk.state["ended"] is None
    assert walk.skills_launched[-1] == "development-code-integrity"


@pytest.mark.parametrize("second", [3, 2])
def test_a_pause_that_does_not_advance_halts(second):
    walk = Walk(through="plan")
    walk.git.commits[KEY] = [_pause(3), *TASK_COMMITS]
    walk.advance("implementation")
    launched_before = len(walk.processes.launched)
    walk.git.commits[KEY] = [_pause(second, "9a75e1"), _pause(3), *TASK_COMMITS]

    walk.advance("implementation")

    assert walk.state["ended"] == "halted"
    reason = walk.state["ended_reason"]
    assert reason.startswith("stopped at implementation:")
    assert f"task {second}" in reason and "task 3" in reason
    assert len(walk.processes.launched) == launched_before


def test_a_pause_that_advances_is_relaunched_again():
    walk = Walk(through="plan")
    walk.git.commits[KEY] = [_pause(3), *TASK_COMMITS]
    walk.advance("implementation")
    walk.git.commits[KEY] = [_pause(5, "9a75e1"), _pause(3), *TASK_COMMITS]

    walk.advance("implementation")

    assert walk.processes.launched[-1][-1] == "5"
    assert walk.state["paused_after"] == 5
    assert walk.state["ended"] is None


def test_a_relaunch_after_a_pause_carries_the_cap_the_walk_started_with():
    """CP-57: the cap a walk starts with holds for every developer run in it, including one
    launched after the walk is rebuilt from disk — which is what every relaunch is, since an
    `--advance` is a fresh engine over the state file."""
    disk, git = _through("plan")
    files = FakeFiles(disk)
    processes = FakeProcesses()
    start(build(files, git=git, processes=processes), context_cap=80000)
    git.commits[KEY] = [_pause(3), *TASK_COMMITS]

    # A fresh engine over the same state file, fired from an environment that holds no cap.
    build(files, git=git, processes=processes,
          environ={"PATH": "/usr/bin"}).advance("implementation", "completed")

    assert processes.launched[-1][-1] == "3"
    assert processes.calls[-1]["env"][CAP_VARIABLE] == "80000"


def test_no_marker_and_no_commit_recovers_once_from_the_first_task():
    walk = Walk(through="plan")
    walk.git.commits[KEY] = []
    walk.files.write_text(f"{BRANCH_CHANGE}/tl_instruction.md", _instruction(1, 2))

    walk.advance("implementation")

    assert walk.state["ended"] is None
    assert walk.state["marker_recoveries"] == 1
    assert walk.state["paused_after"] is None
    assert walk.processes.launched[-1] == _HEAD
    assert walk.state["pending"] == {
        "implementation-recovery": {"step": "implementation", "audited": None,
                                    "identity": identity_file("implementation-recovery"),
                                    "checkout_before": []}}
    assert walk.git.commits[KEY] == []

    # A stale callback cannot consume the new run's completion.
    assert walk.advance("implementation").acted is False
    assert len(walk.processes.launched) == 2
    walk.advance("implementation-recovery")
    assert walk.state["ended"] == "halted"
    assert "closing marker" in walk.state["ended_reason"]
    assert len(walk.processes.launched) == 2


@pytest.mark.parametrize("commits, after", [
    ([("d1", "developer: task 1 x — deferred")], []),
    ([("g3", "developer: task 3 x — green"), ("d2", "developer: task 2 x — deferred"),
      ("g1", "developer: task 1 x — green")], ["1"]),
    ([(f"g{n}", f"developer: task {n} x — green") for n in (3, 2, 1)], ["3"]),
])
def test_marker_recovery_reads_the_external_product_first_unfinished_task(commits, after):
    walk = Walk(through="plan")
    walk.files.write_text(f"{BRANCH_CHANGE}/tl_instruction.md", _instruction(1, 2, 3))
    walk.git.repos[PRODUCT] = {KEY: commits}

    walk.advance("implementation")

    assert walk.state["ended"] is None
    assert walk.processes.launched[-1] == [*_HEAD, *after]
    assert walk.state["marker_recoveries"] == 1


@pytest.mark.parametrize("commits", [[], TASK_COMMITS])
def test_explicit_developer_halt_prevents_marker_recovery_or_task_resume(commits):
    walk = Walk(through="plan")
    walk.git.commits[KEY] = list(commits)
    report = f"{BRANCH_CHANGE}/halt_report.md"
    walk.files.write_text(report, "No task could land: a product decision is required.")

    walk.advance("implementation")

    assert walk.state["ended"] == "halted"
    assert report in walk.state["ended_reason"]
    assert len(walk.processes.launched) == 1


def _walk_with_prior_developer_halt():
    disk, git = _through("plan")
    disk[f"{BRANCH_CHANGE}/halt_report.md"] = "An earlier content decision was missing."
    disk[f"{BRANCH_CHANGE}/tl_instruction.md"] = _instruction(1, 2, 3)
    walk = Walk.__new__(Walk)
    walk.files, walk.git = FakeFiles(disk), git
    walk.processes, walk.notifier, walk.lock = FakeProcesses(), FakeNotifier(), FakeLock()
    start(walk.engine())
    return walk


def test_an_inherited_unchanged_halt_does_not_suppress_missing_marker_recovery():
    walk = _walk_with_prior_developer_halt()
    walk.git.repos[PRODUCT] = {KEY: [_task(2, "green"), _task(1, "green")]}

    walk.advance("implementation")

    assert walk.state["ended"] is None
    assert walk.processes.launched[-1] == [*_HEAD, "2"]
    assert walk.state["marker_recoveries"] == 1
    assert walk.files.read_text(f"{BRANCH_CHANGE}/halt_report.md") == (
        "An earlier content decision was missing.")
    walk.advance("implementation-recovery")
    assert walk.state["ended"] == "halted"
    assert "closing marker" in walk.state["ended_reason"]
    assert len(walk.processes.launched) == 2


def test_a_revised_inherited_halt_is_current_and_stops_recovery():
    walk = _walk_with_prior_developer_halt()
    report = f"{BRANCH_CHANGE}/halt_report.md"
    walk.files.write_text(report, "A new incompatible prerequisite blocks all tasks.")

    walk.advance("implementation")

    assert walk.state["ended"] == "halted"
    assert report in walk.state["ended_reason"]
    assert len(walk.processes.launched) == 1


def test_a_state_without_a_halt_baseline_preserves_explicit_halts():
    walk = _walk_with_prior_developer_halt()
    state = walk.state
    state.pop("developer_halt_before", None)
    walk.files.write_text(STATE, json.dumps(state))

    walk.advance("implementation")

    assert walk.state["ended"] == "halted"
    assert "halt_report.md" in walk.state["ended_reason"]


def test_a_recovered_marker_still_requires_a_good_suite_verdict():
    walk = Walk(through="plan")
    walk.advance("implementation")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = MARKER_BODY.replace("Suite: green", "Suite: red")

    walk.advance("implementation-recovery")

    assert walk.state["ended"] == "halted"
    assert "red-suite" in walk.state["ended_reason"]
    assert len(walk.processes.launched) == 2


def test_a_recovery_that_closes_advances_normally():
    walk = Walk(through="plan")
    walk.advance("implementation")
    land(walk.files, walk.git, "implementation")

    walk.advance("implementation-recovery")

    assert walk.state["ended"] is None
    assert walk.skills_launched[-1] == "development-code-integrity"


def test_older_state_without_marker_recovery_counter_can_recover():
    walk = Walk(through="plan")
    state = walk.state
    state.pop("marker_recoveries", None)
    walk.files.write_text(STATE, json.dumps(state))

    walk.advance("implementation")

    assert walk.state["ended"] is None
    assert walk.state["marker_recoveries"] == 1


@pytest.mark.parametrize("product_path", [PRODUCT, f"{INSTANCE}/product"])
def test_no_pause_recovers_first_unfinished_task_in_the_owning_repo(product_path):
    walk = Walk(through="plan")
    state = walk.state
    state["product_path"] = product_path
    walk.files.write_text(STATE, json.dumps(state))
    walk.files.write_text(f"{BRANCH_CHANGE}/tl_instruction.md", _instruction(1, 2, 3, 4))
    commits = [_task(3, "green"), _task(2, "deferred"), _task(1, "green")]
    if product_path == PRODUCT:
        walk.git.repos[PRODUCT] = {KEY: commits}
    else:
        walk.git.commits[KEY] = commits

    walk.advance("implementation")

    assert walk.processes.launched[-1] == [*_HEAD, "1"]
    assert walk.state["ended"] is None
    assert walk.state["paused_after"] is None
    assert walk.state["marker_recoveries"] == 1
    # Even later task commits do not buy another unexplained-marker recovery.
    commits.insert(0, _task(4, "green"))
    walk.advance("implementation-recovery")
    assert walk.state["ended"] == "halted"
    assert len(walk.processes.launched) == 2


def test_a_failed_run_with_a_landed_task_resumes_once():
    walk = Walk(through="plan")
    walk.git.commits[KEY] = list(TASK_COMMITS)

    walk.advance("implementation", "failed")

    assert walk.processes.launched[-1][-1] == "3"
    assert walk.state["ended"] is None
    assert walk.state["failure_resumes"] == 1
    assert walk.state["paused_after"] == 3
    assert any(message.endswith("failed after task 3 — resuming")
               for message in walk.notifier.messages)


def test_a_second_failure_halts_even_when_a_later_task_landed():
    walk = Walk(through="plan")
    walk.git.commits[KEY] = list(TASK_COMMITS)
    walk.advance("implementation", "failed")
    launched_before = len(walk.processes.launched)
    walk.git.commits[KEY] = [("7a5c05", "developer: task 5 tidy — green"), *TASK_COMMITS]

    walk.advance("implementation", "failed")

    assert walk.state["ended"] == "halted"
    assert "failed again after one resume" in walk.state["ended_reason"]
    assert len(walk.processes.launched) == launched_before


def _external_walk(product_tasks: list, instance_commits: list | None = None) -> "Walk":
    """A walk at implementation on an external product: its task commits on the product repo's
    `<key>` branch, and only what `instance_commits` names on the instance's — where the
    developer's pipeline commits, the pause and the marker, land (`development-implementation`
    § *Where each commit goes*)."""
    walk = Walk(through="plan")
    walk.git.repos[PRODUCT] = {KEY: list(product_tasks)}
    walk.git.repos[INSTANCE] = {KEY: list(instance_commits or [])}
    return walk


def test_a_failed_run_on_an_external_product_resumes_from_the_product_branch():
    """Cold read 2026-09-29, D1: the resume read the instance repo only, where an external
    product's task commits never are, so the same failure that resumes in one repo halted."""
    walk = _external_walk(list(TASK_COMMITS))

    walk.advance("implementation", "failed")

    assert walk.processes.launched[-1] == [*_HEAD, "3"]
    assert walk.state["ended"] is None
    assert walk.state["failure_resumes"] == 1


def test_a_failed_run_on_an_external_product_with_nothing_landed_halts():
    walk = _external_walk([], instance_commits=list(TASK_COMMITS))

    walk.advance("implementation", "failed")

    assert walk.state["ended"] == "halted"
    assert walk.state["ended_reason"] == "stopped at implementation: the run ended failed"


def test_a_failed_run_on_an_in_repo_product_reads_the_instance_branch_only():
    walk = Walk(through="plan")
    state = walk.state
    state["product_path"] = f"{INSTANCE}/product"
    walk.files.write_text(STATE, json.dumps(state))
    walk.git.repos[INSTANCE] = {KEY: list(TASK_COMMITS)}
    walk.git.repos[f"{INSTANCE}/product"] = {KEY: []}

    walk.advance("implementation", "failed")

    assert walk.processes.launched[-1] == [*_HEAD, "3"]


def test_an_external_products_marker_on_the_instance_branch_owns_the_resume():
    """Two repos' commits have no order between them, so a marker of this change's on the
    instance branch is read as newer than every task commit — the one-repo reading of a marker
    newer than the task, and what a failure then does there: halt."""
    git = FakeGit(repos={PRODUCT: {KEY: list(TASK_COMMITS)}, INSTANCE: {KEY: [MARKER]}})

    assert reader(git=git).resumable_task(layout(), PRODUCT) is None
    assert reader(git=git).resumable_task(layout(), f"{INSTANCE}/product") is None


def test_a_failed_run_with_nothing_landed_halts():
    walk = Walk(through="plan")
    walk.git.commits[KEY] = []

    walk.advance("implementation", "failed")

    assert walk.state["ended"] == "halted"
    assert walk.state["ended_reason"] == "stopped at implementation: the run ended failed"
    assert walk.state["failure_resumes"] == 0
    assert walk.skills_launched == ["development-implementation"]


def test_a_timeout_with_a_landed_task_is_not_resumed():
    walk = Walk(through="plan")
    walk.git.commits[KEY] = list(TASK_COMMITS)

    walk.advance("implementation", "timeout")

    assert walk.state["ended"] == "halted"
    assert walk.state["ended_reason"] == "stopped at implementation: the run ended timeout"
    assert walk.state["failure_resumes"] == 0


def test_a_launch_on_no_pause_passes_no_after():
    files, git = _through("plan")
    processes = FakeProcesses()

    start(build(FakeFiles(files), git=git, processes=processes), keep_awake=True)

    assert processes.launched == [[SKILL_LAUNCHER, "development-implementation", PROJECT, KEY,
                                   "--keep-awake"]]


def test_a_relaunch_keeps_the_keep_awake_flag_last():
    files, git = _through("plan")
    walk_processes = FakeProcesses()
    engine = build(FakeFiles(files), git=git, processes=walk_processes)
    start(engine, keep_awake=True)
    git.commits[KEY] = [_pause(3), *TASK_COMMITS]

    build(engine.files, git=git, processes=walk_processes).advance("implementation", "completed")

    assert walk_processes.launched[-1] == [SKILL_LAUNCHER, "development-implementation", PROJECT,
                                           KEY, "3", "--keep-awake"]


def test_a_pause_over_an_earlier_step_gone_missing_halts_as_today():
    """The relaunch goes through `entry_step`, so it can only ever restart the step that ended.
    Were the plan's artifact gone, `entry_step` would answer the plan — and launching that with a
    task number would send a different step somewhere it was never asked to go."""
    walk = Walk(through="plan")
    del walk.files.files[f"{BRANCH_CHANGE}/tl_instruction.md"]
    walk.git.commits[KEY] = [_pause(3), *TASK_COMMITS]

    walk.advance("implementation")

    assert walk.state["ended"] == "halted"
    assert walk.state["ended_reason"].startswith("stopped at implementation: no developer closing")
    assert walk.skills_launched == ["development-implementation"]
    assert walk.state["paused_after"] is None


def test_a_run_that_did_not_finish_is_not_relaunched_after_a_pause():
    """A pause commit says the run stopped on purpose. A run that timed out did not, and whatever
    it left on the branch, the walk halts on the outcome as it always has."""
    walk = Walk(through="plan")
    walk.git.commits[KEY] = [_pause(3), *TASK_COMMITS]

    walk.advance("implementation", "timeout")

    assert walk.state["ended"] == "halted"
    assert walk.state["ended_reason"] == "stopped at implementation: the run ended timeout"
    assert walk.skills_launched == ["development-implementation"]
    assert walk.state["paused_after"] is None


def test_a_relaunch_whose_launcher_fails_halts_naming_it():
    walk = Walk(through="plan", codes=[0, 3])
    walk.git.commits[KEY] = [_pause(3), *TASK_COMMITS]

    walk.advance("implementation")

    assert walk.state["ended"] == "halted"
    assert walk.state["ended_reason"] == "stopped at implementation: launcher exited 3"
    assert walk.state["pending"] == {}


# --- a blocked task is deferred, and the marker that says so lands ---------------------------------
#
# The closing marker's body carries one `Deferred:` line per deferred task and, when the suite is
# red, one `Failing:` line per failing case naming its task
# (`.claude/skills/development-implementation/SKILL.md` Step 3). The engine runs no tests, so it can
# only compare those declarations: a red suite lands only when every failing case belongs to a task
# some `Deferred:` line names.

_LANGUAGE = "Language resolution:\n- python — declared in project.md\n"
_DEFERRED_THREE = "Deferred: task 3 — the CP-15 case — docs/record.md § halts\n"
_DEFERRED_FOUR = "Deferred: task 4 — depends on task 3 — docs/record.md § halts\n"


def _marker_with(*lines: str, suite: str = "red") -> str:
    """A closing-marker body: the two never-omitted lines, then `lines` verbatim."""
    return (f"Suite: {suite}\n\n{_LANGUAGE}\n" + "".join(f"{line}\n" for line in lines)
            + f"\n{ENVIRONMENT_LINE}\n")


def _walk_with_marker(body: str) -> Walk:
    walk = Walk(through="plan")
    land(walk.files, walk.git, "implementation")
    walk.git.bodies[MARKER[0]] = body
    return walk


def test_a_marker_carrying_deferred_lines_lands_and_the_walk_advances():
    walk = _walk_with_marker(_marker_with(
        _DEFERRED_THREE.strip(), _DEFERRED_FOUR.strip(),
        "Failing: tests/test_bundle.py::test_cp_15 — task 3"))

    walk.advance("implementation")

    assert walk.state["ended"] is None
    assert walk.skills_launched[-1] == "development-code-integrity"


def test_a_green_marker_with_a_deferred_line_lands():
    walk = _walk_with_marker(_marker_with(_DEFERRED_THREE.strip(), suite="green"))

    walk.advance("implementation")

    assert walk.state["ended"] is None
    assert walk.skills_launched[-1] == "development-code-integrity"


def test_a_start_over_a_deferred_red_marker_enters_past_it():
    files, git = _through("implementation")
    git.bodies[MARKER[0]] = _marker_with(_DEFERRED_THREE.strip(),
                                         "Failing: tests/test_bundle.py::test_cp_15 — task 3")

    plan = describe(build(FakeFiles(files), git=git))

    assert plan.entry == "code-integrity"


@pytest.mark.parametrize("failing", [
    ["Failing: tests/test_a.py::test_a — task 3", "Failing: tests/test_b.py::test_b — task 1"],
    ["Failing: tests/test_a.py::test_a — task 3", "Failing: tests/test_b.py::test_b — no task"],
], ids=["a-failing-case-of-an-undeferred-task", "a-failing-case-of-no-task"])
def test_a_failing_case_outside_the_deferred_tasks_halts_red_suite(failing):
    walk = _walk_with_marker(_marker_with(_DEFERRED_THREE.strip(), *failing))

    walk.advance("implementation")

    assert walk.state["ended"] == "halted"
    assert "stopped at implementation: red-suite" in walk.state["ended_reason"]


def test_failing_lines_do_not_rescue_a_red_marker_with_no_deferral():
    walk = _walk_with_marker(_marker_with("Failing: tests/test_a.py::test_a — task 3"))

    walk.advance("implementation")

    assert "stopped at implementation: red-suite" in walk.state["ended_reason"]


def test_a_red_marker_with_deferrals_and_no_failing_line_halts():
    walk = _walk_with_marker(_marker_with(_DEFERRED_THREE.strip()))

    walk.advance("implementation")

    assert "stopped at implementation: red-suite" in walk.state["ended_reason"]


def test_an_unparseable_failing_task_halts():
    walk = _walk_with_marker(_marker_with(_DEFERRED_THREE.strip(),
                                          "Failing: tests/test_a.py::test_a — task x"))

    walk.advance("implementation")

    assert "stopped at implementation: red-suite" in walk.state["ended_reason"]


def test_an_unparseable_deferred_line_is_not_a_halt():
    walk = _walk_with_marker(_marker_with("Deferred: nonsense", suite="green"))

    walk.advance("implementation")

    assert walk.state["ended"] is None
    assert walk.skills_launched[-1] == "development-code-integrity"


def test_task_numbers_match_as_whole_tokens():
    walk = _walk_with_marker(_marker_with(_DEFERRED_THREE.strip(),
                                          "Failing: tests/test_a.py::test_a — task 30"))

    walk.advance("implementation")

    assert "stopped at implementation: red-suite" in walk.state["ended_reason"]


def test_deferred_and_failing_lines_are_read_past_emphasis_and_only_at_line_start():
    body = _marker_with(
        "**Deferred: task 3 — the CP-15 case — docs/record.md**",
        "`Failing: tests/test_a.py::test_a — task 3`",
        "Developer Review Notes: I wrote Deferred: task 9 — mid-line — nowhere here")
    disk = reader(git=FakeGit(commits={KEY: [MARKER]}, bodies={MARKER[0]: body}))

    assert disk.deferrals(layout()) == ["Deferred: task 3 — the CP-15 case — docs/record.md"]
    assert disk.failing_cases(layout()) == ["Failing: tests/test_a.py::test_a — task 3"]


def test_a_reader_with_no_marker_reads_no_deferrals_and_no_failing_cases():
    disk = reader(git=FakeGit())

    assert disk.deferrals(layout()) == []
    assert disk.failing_cases(layout()) == []


# --- the deferrals are kept on the walk's state and named in the sealed message -------------------


_TWO_DEFERRALS = [_DEFERRED_THREE.strip(), _DEFERRED_FOUR.strip()]


def _deferred_body(suite: str = "red") -> str:
    failing = ["Failing: tests/test_bundle.py::test_cp_15 — task 3"] if suite == "red" else []
    return _marker_with(*_TWO_DEFERRALS, *failing, suite=suite)


def test_the_deferrals_survive_a_rebuilt_walk_state():
    walk = _walk_with_marker(_deferred_body())

    walk.advance("implementation")
    rebuilt = cd.StateStore(walk.files, STATE).load()

    assert walk.state["deferrals"] == _TWO_DEFERRALS
    assert rebuilt.deferrals == _TWO_DEFERRALS


def test_a_start_past_implementation_records_the_marker_deferrals():
    files, git = _through("implementation")
    git.bodies[MARKER[0]] = _deferred_body()
    disk = FakeFiles(files)

    start(build(disk, git=git))

    assert saved(disk)["deferrals"] == _TWO_DEFERRALS


def test_a_state_file_without_deferrals_loads_empty():
    walk = Walk(through="plan")
    stored = walk.state
    del stored["deferrals"]
    walk.files.write_text(STATE, json.dumps(stored))

    assert cd.StateStore(walk.files, STATE).load().deferrals == []


def test_a_walk_sealed_with_deferrals_says_so():
    walk = _sealed_over(_deferred_body(suite="green"))

    message = walk.notifier.messages[-1]

    assert "with deferrals" in message
    assert "task 3" in message and "task 4" in message


def test_a_walk_sealed_without_deferrals_sends_todays_message():
    walk = _sealed_over(MARKER_BODY)

    assert walk.notifier.messages[-1] == (
        f"instance · {PROJECT} · development chain — sealed {KEY} — suite green "
        "(marker a1b2c3); audits: none recorded")


def _sealed_over(marker_body: str) -> Walk:
    """A walk entered at the seal, over `marker_body`, that then lands the seal."""
    disk, git = _through("audit")
    git.bodies[MARKER[0]] = marker_body
    walk = Walk.__new__(Walk)
    walk.files, walk.git = FakeFiles(disk), git
    walk.processes, walk.notifier, walk.lock = FakeProcesses(), FakeNotifier(), FakeLock()
    start(walk.engine())
    land(walk.files, walk.git, "seal")
    walk.advance("seal")
    return walk


# --- a start at implementation tells the developer where to begin --------------------------------
#
# The first task in the instruction with no landing commit on the branch. A commit lands task N when
# its subject is `developer: task <N> <slug>` (or `task-<N>`) and has no ` — ` suffix, or its last
# suffix is exactly `green` or `refactor`; any other suffix reads as not landed
# (`.claude/skills/development-implementation/SKILL.md`, the per-task commit forms).


def _instruction(*numbers: int) -> str:
    return "# Tech Lead instruction\n\n" + "".join(
        f"### Task {number}: a task\n\n**Dependencies:** None\n\n" for number in numbers)


def _task(number: int, suffix: str = "", slug: str = "x", form: str = "task {n}") -> tuple:
    """One per-task commit, `(sha, subject)`: `developer: task <N> <slug> — <suffix>`."""
    subject = " ".join(part for part in (f"developer: {form.format(n=number)}", slug) if part)
    return (f"t{number}-{suffix or 'plain'}", f"{subject} — {suffix}" if suffix else subject)


def _launched_after(commits: list, numbers=(1, 2, 3, 4, 5), *, git=None,
                    product_path: str = PRODUCT) -> list[str]:
    """The argv a start at implementation launches, for a branch holding `commits` (newest
    first) over an instruction listing `numbers`."""
    files, scripted = _through("plan")
    files[f"{BRANCH_CHANGE}/tl_instruction.md"] = _instruction(*numbers)
    scripted.commits[KEY] = list(commits)
    processes = FakeProcesses()
    build(FakeFiles(files), git=git or scripted, processes=processes).start(
        instance_root=INSTANCE, product_path=product_path, project=PROJECT, core_dir=CORE,
        shim_dir=LOGS)
    return processes.launched[-1]


_HEAD = [SKILL_LAUNCHER, "development-implementation", PROJECT, KEY]


def test_a_walk_halted_on_a_missing_marker_re_enters_at_implementation():
    commits = [_task(3, "red"), _task(2, "green"), _task(2, "red"), _task(1, "green"),
               _task(1, "red")]

    assert _launched_after(commits) == [*_HEAD, "2"]


def test_a_start_with_no_task_commit_passes_no_after():
    assert _launched_after([]) == _HEAD


def test_a_start_with_every_task_landed_passes_the_last_task():
    commits = [_task(number, "green") for number in (5, 4, 3, 2, 1)]

    assert _launched_after(commits) == [*_HEAD, "5"]


def test_plain_and_refactor_commits_land_a_task_and_a_red_only_task_does_not():
    commits = [_task(3, "red"), _task(2, "refactor", form="task-{n}", slug=""),
               _task(1, slug="x")]

    assert _launched_after(commits) == [*_HEAD, "2"]


def test_a_commit_with_an_unstated_suffix_does_not_land_its_task():
    commits = [_task(4, "green except the real bundle (CP-15 halt)"), _task(4, "red"),
               _task(3, "green"), _task(2, "green"), _task(1, "green")]

    assert _launched_after(commits, numbers=(1, 2, 3, 4, 5, 6)) == [*_HEAD, "3"]


def test_a_deferred_suffix_does_not_land_its_task():
    commits = [_task(3, "deferred"), _task(3, "red"), _task(2, "green"), _task(1, "green")]

    assert _launched_after(commits) == [*_HEAD, "2"]


@pytest.mark.parametrize("commits, numbers, expected", [
    ([_task(12, "green")], (1, 12), []),
    ([_task(1, "green")], (12,), []),
], ids=["task-12-does-not-land-task-1", "heading-task-12-is-not-task-1"])
def test_task_numbers_in_subjects_and_headings_are_whole_tokens(commits, numbers, expected):
    assert _launched_after(commits, numbers) == [*_HEAD, *expected]


def test_pause_and_marker_subjects_are_not_task_commits():
    # A start with a marker on the branch enters past implementation, so the marker is read at the
    # reader; the pause is read through a start, which is where a branch holding one gets here.
    disk = reader(files={f"{BRANCH_CHANGE}/tl_instruction.md": _instruction(1, 2, 3)},
                  git=FakeGit(commits={KEY: [MARKER, _pause(3)]}))

    assert disk.resume_after(layout(), PRODUCT) is None
    assert _launched_after([_pause(3), _task(1, "green")]) == [*_HEAD, "1"]


def test_an_unreadable_instruction_reads_no_resume_point():
    disk = reader(files={}, git=FakeGit(commits={KEY: [_task(1, "green")]}))

    assert disk.resume_after(layout(), PRODUCT) is None


def test_an_instruction_listing_no_task_reads_no_resume_point():
    disk = reader(files={f"{BRANCH_CHANGE}/tl_instruction.md": "# nothing to do\n"},
                  git=FakeGit(commits={KEY: [_task(1, "green")]}))

    assert disk.resume_after(layout(), PRODUCT) is None


def test_a_start_reads_landing_commits_from_an_external_product_repo():
    git = FakeGit(repos={PRODUCT: {KEY: [_task(2, "green"), _task(1, "green")]},
                         INSTANCE: {KEY: []}})

    assert _launched_after([], git=git) == [*_HEAD, "2"]


@pytest.mark.parametrize("product_path, read_from", [
    ("/instance-other", "product"),
    ("/instance/product", "instance"),
], ids=["a-sibling-sharing-the-instance-prefix-is-external", "a-folder-inside-is-not"])
def test_the_product_repo_is_read_only_when_the_product_lies_outside_the_instance(
        product_path, read_from):
    landed = [_task(2, "green"), _task(1, "green")]
    git = FakeGit(repos={product_path: {KEY: landed if read_from == "product" else []},
                         INSTANCE: {KEY: landed if read_from == "instance" else []}})

    assert _launched_after([], git=git, product_path=product_path) == [*_HEAD, "2"]


@pytest.mark.parametrize("active", [[], ["open"], ["first", "second"]])
def test_list_open_changes_cli_uses_request_files_and_preserves_residue(tmp_path, active):
    import json
    import subprocess
    import sys

    root = tmp_path / "instance"
    base = root / "system/projects/tracker/journey/tobiishi"
    for relative in ["sealed/halt_report.md", "trail/change_request.md",
                     "trail/old/change_request.md", "drop/change_request.md",
                     "drop/abandoned/change_request.md"]:
        path = base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("evidence")
    for key in active:
        path = base / key / "change_request.md"
        path.parent.mkdir(parents=True)
        path.write_text("request")
    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    result = subprocess.run(
        [sys.executable, cd.__file__, "--list-open-changes", "--instance-root", str(root),
         "--project", "tracker"], capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == sorted(active)
    assert {str(p.relative_to(root)): p.read_bytes()
            for p in root.rglob("*") if p.is_file()} == before


def test_list_open_changes_requires_project_and_instance(capsys):
    assert cd.main(["--list-open-changes"]) == 2
    assert "--instance-root" in capsys.readouterr().err


def test_list_open_changes_cannot_start_a_chain(capsys):
    assert cd.main(["--list-open-changes", "--start", "/unused"]) == 2
    assert "mutually exclusive" in capsys.readouterr().err


def test_discovery_does_not_treat_unlistable_directory_as_empty(tmp_path):
    base = tmp_path / "system/projects/tracker/journey/tobiishi"
    base.parent.mkdir(parents=True)
    base.write_text("not a directory")
    with pytest.raises(NotADirectoryError):
        cd.DiskReader(files=cd.Files(), git=cd.Git()).open_change_keys(str(tmp_path), "tracker")


def test_discovery_allows_a_missing_journey_directory(tmp_path):
    assert cd.DiskReader(files=cd.Files(), git=cd.Git()).open_change_keys(
        str(tmp_path), "tracker") == []


# Owner-started recovery retains the stop until a developer produces a new marker.
def _stopped_deferred_change():
    files, git = _through("code-integrity")
    files[f"{SHUKUBA}/2026-09-15_due-dates.md"] = "station"
    files[f"{BRANCH_CHANGE}/code-integrity-report.md"] = "Integrity: stopped\n"
    files[f"{BRANCH_CHANGE}/tl_instruction.md"] = (
        "### Task 1: store\n### Task 2: route\n")
    git.bodies[MARKER[0]] = (
        "Suite: red\nLanguage resolution:\n- Python\n"
        "Deferred: task 2 — unfinished route tests — tl_instruction.md\n"
        "Failing: tests/test_route.py::test_return — task 2\n"
        f"\n{ENVIRONMENT_LINE}\n")
    git.commits[KEY].append(("task-one", "developer: task 1 store — green"))
    return FakeFiles(files), git


def test_explicit_restart_of_rejected_deferral_enters_developer_without_editing_evidence():
    files, git = _stopped_deferred_change()
    processes = FakeProcesses()
    engine = build(files, git=git, processes=processes, steps=cd.CHANGE_STEPS)
    report = files.read_text(f"{BRANCH_CHANGE}/code-integrity-report.md")

    assert engine.describe(instance_root=INSTANCE, project=PROJECT).entry == "implementation"
    assert STATE not in files.files
    start(engine)

    assert processes.launched == [
        [SKILL_LAUNCHER, "development-implementation", PROJECT, KEY, "1"]]
    assert files.read_text(f"{BRANCH_CHANGE}/code-integrity-report.md") == report
    assert git.commits[KEY][0] == MARKER


def _reclosed_after_the_stop():
    """The stopped deferral, then the integrity commit that wrote the stop, then a re-close: a
    newer closing marker made after the developer put the blocked case in the tree."""
    files, git = _stopped_deferred_change()
    # The subject need not name the key: integrity's subjects do not always (CP review, 2026-10-13).
    git.commits[KEY].insert(0, ("integrity-stop", "code-integrity: stream labels — stopped"))
    git.commits[KEY].insert(0, ("reclose", f"developer: {KEY} — implementation complete"))
    git.bodies["reclose"] = git.bodies[MARKER[0]]
    git.touched[(KEY, f"{CHANGE_REL}/code-integrity-report.md")] = "integrity-stop"
    return files, git


def test_a_reclose_after_the_stop_reenters_code_integrity():
    """A start after the developer re-closed over a stopped integrity verdict runs integrity
    again: the newest marker postdates the report, so the unfinished work it asked for is done.
    Before, every start re-entered implementation and spent a developer run on a re-close that
    had already happened (a satellite walk, 2026-10-13)."""
    files, git = _reclosed_after_the_stop()
    processes = FakeProcesses()
    engine = build(files, git=git, processes=processes, steps=cd.CHANGE_STEPS)

    assert engine.describe(instance_root=INSTANCE, project=PROJECT).entry == "code-integrity"
    start(engine)

    assert processes.launched[0][1] == "development-code-integrity"


def test_a_report_no_branch_commit_wrote_still_reenters_implementation():
    """Fail safe: with no commit on the branch known to have written the report, a newer marker
    proves nothing, and the start keeps sending the developer back."""
    files, git = _reclosed_after_the_stop()
    del git.touched[(KEY, f"{CHANGE_REL}/code-integrity-report.md")]
    engine = build(files, git=git, processes=FakeProcesses(), steps=cd.CHANGE_STEPS)

    assert engine.describe(instance_root=INSTANCE, project=PROJECT).entry == "implementation"


def test_a_marker_older_than_the_stop_still_reenters_implementation():
    files, git = _stopped_deferred_change()
    git.commits[KEY].insert(0, ("integrity-stop", f"code-integrity: {KEY} — stopped"))
    git.touched[(KEY, f"{CHANGE_REL}/code-integrity-report.md")] = "integrity-stop"
    engine = build(files, git=git, processes=FakeProcesses(), steps=cd.CHANGE_STEPS)

    assert engine.describe(instance_root=INSTANCE, project=PROJECT).entry == "implementation"


def test_restarted_developer_cannot_reuse_the_rejected_marker():
    files, git = _stopped_deferred_change()
    processes = FakeProcesses()
    engine = build(files, git=git, processes=processes, steps=cd.CHANGE_STEPS)
    start(engine)

    engine.advance("implementation", "completed")

    assert saved(files)["ended"] == "halted"
    assert "new developer closing marker" in saved(files)["ended_reason"]
    assert len(processes.launched) == 1


def test_repaired_marker_requires_integrity_again_before_any_audit():
    files, git = _stopped_deferred_change()
    processes = FakeProcesses()
    engine = build(files, git=git, processes=processes, steps=cd.CHANGE_STEPS)
    start(engine)
    replacement = ("new-marker", MARKER[1])
    git.commits[KEY].insert(0, replacement)
    git.bodies[replacement[0]] = MARKER_BODY

    engine.advance("implementation", "completed")

    assert [args[1] for args in processes.launched] == [
        "development-implementation", "development-code-integrity"]
    assert saved(files)["marker"] == "new-marker"
    assert saved(files)["deferrals"] == []
    engine.advance("code-integrity", "completed")
    assert saved(files)["ended"] == "halted"
    assert saved(files)["ended_reason"] == "stopped at code-integrity: integrity-stopped"
    assert len(processes.launched) == 2


def test_repaired_change_with_new_integrity_pass_can_reach_audits():
    files, git = _stopped_deferred_change()
    processes = FakeProcesses()
    engine = build(files, git=git, processes=processes, steps=cd.CHANGE_STEPS)
    start(engine)
    git.commits[KEY].insert(0, ("repaired", MARKER[1]))
    git.bodies["repaired"] = MARKER_BODY
    engine.advance("implementation", "completed")
    files.write_text(f"{BRANCH_CHANGE}/code-integrity-report.md", PASSING_REPORT)

    engine.advance("code-integrity", "completed")

    assert [args[1] for args in processes.launched] == [
        "development-implementation", "development-code-integrity",
        *("development-audit" for _ in PRODUCERS)]
    assert saved(files)["ended"] is None


def test_restarted_developer_can_pause_after_an_inherited_marker():
    files, git = _stopped_deferred_change()
    processes = FakeProcesses()
    engine = build(files, git=git, processes=processes, steps=cd.CHANGE_STEPS)
    start(engine)
    git.commits[KEY].insert(0, (
        "pause", f"developer: {KEY} — implementation paused after task 1"))

    engine.advance("implementation", "completed")

    assert saved(files)["ended"] is None
    assert len(processes.launched) == 2
    assert processes.launched[-1] == [
        SKILL_LAUNCHER, "development-implementation", PROJECT, KEY, "1"]


# --- a pause is read only where it ended the run (CP-182..CP-186) ------------------------------
#
# A pause stands as the run's end only while it is the newest developer commit: any `developer:`
# subject of this change's above it, on the instance branch or (by author time) on an external
# product's, buries it. A buried pause is history, and the run goes the way a bare end goes.


IN_REPO_PRODUCT = f"{INSTANCE}/product"
MISSING_MARKER_HALT = (f"stopped at implementation: no developer closing marker commit on {KEY} "
                       "after the run ended")
# A branch whose newest developer commit is a task commit above an older pause (spec, Examples).
BURIED_PAUSE = [_task(4, "green"), _pause(3), _task(3, "green"), _task(2, "green"),
                _task(1, "green")]


def _walk_started_on(commits: list, numbers=(1, 2, 3, 4, 5),
                     product_path: str = IN_REPO_PRODUCT) -> Walk:
    """A walk started at implementation over a branch that already holds `commits`."""
    disk, git = _through("plan")
    disk[f"{BRANCH_CHANGE}/tl_instruction.md"] = _instruction(*numbers)
    git.commits[KEY] = list(commits)
    walk = Walk.__new__(Walk)
    walk.files, walk.git = FakeFiles(disk), git
    walk.processes, walk.notifier, walk.lock = FakeProcesses(), FakeNotifier(), FakeLock()
    start(walk.engine(), product_path=product_path)
    return walk


def _relaunched_after_a_pause_then_task_4() -> Walk:
    """In-repo: tasks 1-3 land, the run pauses after 3 and is relaunched with `3`, and the
    relaunched run lands task 4 and ends with neither marker nor pause (request item 1)."""
    walk = Walk(through="plan", product_path=IN_REPO_PRODUCT)
    walk.files.write_text(f"{BRANCH_CHANGE}/tl_instruction.md", _instruction(1, 2, 3, 4, 5))
    walk.git.commits[KEY] = [_pause(3), _task(3, "green"), _task(2, "green"), _task(1, "green")]
    walk.advance("implementation")
    assert walk.processes.launched[-1] == [*_HEAD, "3"]
    walk.git.commits[KEY].insert(0, _task(4, "green"))
    return walk


def _spend_the_recovery(walk: Walk) -> None:
    state = walk.state
    state["marker_recoveries"] = 1
    walk.files.write_text(STATE, json.dumps(state))


def test_a_relaunched_run_that_lands_a_task_and_ends_bare_halts_on_the_missing_marker():
    walk = _relaunched_after_a_pause_then_task_4()
    _spend_the_recovery(walk)
    launched_before = len(walk.processes.launched)

    walk.advance("implementation")

    assert walk.state["ended"] == "halted"
    assert walk.state["ended_reason"] == MISSING_MARKER_HALT
    assert "no progress" not in walk.state["ended_reason"]
    assert "last pause" not in walk.state["ended_reason"]
    assert len(walk.processes.launched) == launched_before


def test_a_relaunched_run_that_lands_a_task_and_ends_bare_recovers_once_from_the_task_after_it():
    walk = _relaunched_after_a_pause_then_task_4()

    walk.advance("implementation")

    assert walk.state["ended"] is None
    assert walk.processes.launched[-1] == [*_HEAD, "4"]
    assert walk.state["pending"] == {
        "implementation-recovery": {"step": "implementation", "audited": None,
                                    "identity": identity_file("implementation-recovery"),
                                    "checkout_before": []}}
    assert walk.state["marker_recoveries"] == 1
    assert walk.notifier.messages[-1].endswith("missing developer closing marker — recovering once")


def test_a_fresh_walk_does_not_relaunch_after_a_pause_a_task_commit_has_passed():
    walk = _walk_started_on(BURIED_PAUSE)
    assert walk.processes.launched[-1] == [*_HEAD, "4"]

    walk.advance("implementation")

    assert all(argv[-1] != "3" for argv in walk.processes.launched)
    assert walk.processes.launched[-1] == [*_HEAD, "4"]
    assert list(walk.state["pending"]) == ["implementation-recovery"]
    assert walk.state["paused_after"] is None


def test_a_failed_run_over_a_buried_pause_resumes_from_the_newest_landed_task():
    walk = _walk_started_on(BURIED_PAUSE)

    walk.advance("implementation", "failed")

    assert walk.processes.launched[-1] == [*_HEAD, "4"]
    assert walk.state["failure_resumes"] == 1
    assert all(argv[-1] != "3" for argv in walk.processes.launched)


@pytest.mark.parametrize("above", [
    _task(4, "red"),
    ("e1", "developer: the derived edge cases, each proved by mutation"),
    _task(4, "green"),
], ids=["red-task", "task-less", "green-task"])
def test_a_developer_commit_above_the_pause_is_not_a_pause(above):
    git = FakeGit(commits={KEY: [above, _pause(3), *TASK_COMMITS]})

    assert reader(git=git).paused_after(layout(), IN_REPO_PRODUCT) is None


def test_a_red_task_commit_above_the_pause_takes_the_recovery_not_the_pause():
    walk = _walk_started_on([_task(4, "red"), _pause(3), _task(3, "green"), _task(2, "green"),
                             _task(1, "green")])

    walk.advance("implementation")

    assert list(walk.state["pending"]) == ["implementation-recovery"]
    assert walk.state["marker_recoveries"] == 1
    assert walk.state["paused_after"] is None
    assert not any(message.endswith("paused after task 3 — resuming")
                   for message in walk.notifier.messages)


def test_another_changes_developer_commit_above_the_pause_does_not_bury_it():
    other = ("o4", "developer: task 4 2026-09-21_other-change tidy — green")
    git = FakeGit(commits={KEY: [other, _pause(3), *TASK_COMMITS]})

    assert reader(git=git).paused_after(layout(), IN_REPO_PRODUCT) == 3


def test_a_commit_that_is_not_the_developers_above_the_pause_does_not_bury_it():
    """Only a `developer:` subject says the developer went on working (CP-182). A merge from
    `main`, or anyone else's commit, above the pause leaves it the run's end."""
    merge = ("m1", f"Merge branch 'main' into {KEY}")
    git = FakeGit(commits={KEY: [merge, _pause(3), *TASK_COMMITS]})

    assert reader(git=git).paused_after(layout(), IN_REPO_PRODUCT) == 3


def test_a_product_branch_task_commit_after_the_instance_pause_buries_it():
    walk = Walk(through="plan")
    walk.files.write_text(f"{BRANCH_CHANGE}/tl_instruction.md", _instruction(1, 2, 3, 4, 5))
    walk.git.repos[INSTANCE] = {KEY: [_pause(3)]}
    walk.git.repos[PRODUCT] = {KEY: [_task(3, "green"), _task(2, "green"), _task(1, "green")]}
    walk.git.times.update({_pause(3)[0]: 100, "t3-green": 90, "t2-green": 80, "t1-green": 70})
    walk.advance("implementation")
    assert walk.processes.launched[-1] == [*_HEAD, "3"]
    walk.git.repos[PRODUCT][KEY].insert(0, _task(4, "green"))
    walk.git.times["t4-green"] = 200
    _spend_the_recovery(walk)

    walk.advance("implementation")

    assert walk.state["ended"] == "halted"
    assert walk.state["ended_reason"] == MISSING_MARKER_HALT
    assert "no progress" not in walk.state["ended_reason"]


def test_an_instance_branch_developer_commit_after_the_pause_buries_it_for_an_external_product():
    above = ("e1", "developer: the derived edge cases, each proved by mutation")
    git = FakeGit(repos={INSTANCE: {KEY: [above, _pause(3)]}, PRODUCT: {KEY: []}})

    assert reader(git=git).paused_after(layout(), PRODUCT) is None


@pytest.mark.parametrize("product_commits, times", [
    ([_task(3, "green"), _task(2, "green")], {"9a75e0": 100, "t3-green": 90, "t2-green": 80}),
    ([_task(4, "green"), _task(3, "green")], {"9a75e0": 100, "t4-green": 100, "t3-green": 90}),
    ([_task(4, "green"), _task(3, "green")], {"9a75e0": 100, "t3-green": 90}),
    ([_task(4, "green")], {"t4-green": 200}),
    ([("o4", "developer: task 4 2026-09-21_other-change tidy — green")], {"9a75e0": 100,
                                                                          "o4": 200}),
    ([("m1", f"Merge branch 'main' into {KEY}")], {"9a75e0": 100, "m1": 200}),
], ids=["all-before", "tie", "product-time-unread", "pause-time-unread", "another-change",
        "not-the-developer"])
def test_an_external_pause_stands_unless_a_product_commit_is_strictly_later(product_commits, times):
    git = FakeGit(repos={INSTANCE: {KEY: [_pause(3)]}, PRODUCT: {KEY: list(product_commits)}},
                  times=times)

    assert reader(git=git).paused_after(layout(), PRODUCT) == 3


def test_a_failed_external_run_over_a_buried_pause_resumes_from_the_product_branch():
    """External: the instance pause is buried by a product-branch task authored after it, so it
    owns no resume, and the failure resume reads the product branch's newest landed task."""
    walk = Walk(through="plan")
    walk.git.repos[INSTANCE] = {KEY: [_pause(3)]}
    walk.git.repos[PRODUCT] = {KEY: [_task(4, "green"), _task(3, "green"), _task(2, "green"),
                                     _task(1, "green")]}
    walk.git.times.update({_pause(3)[0]: 100, "t4-green": 200, "t3-green": 90, "t2-green": 80,
                           "t1-green": 70})

    walk.advance("implementation", "failed")

    assert walk.processes.launched[-1] == [*_HEAD, "4"]
    assert walk.state["failure_resumes"] == 1


def test_a_failed_in_repo_run_resumes_past_a_pause_buried_under_an_unlanded_task():
    """The one-repo loop reads newest first, so a `red` task commit above the pause used to reach
    the pause before any landed task and decline the resume. A buried pause owns nothing
    (CP-184): the newest landed task beneath it is what the resume passes."""
    walk = _walk_started_on([_task(4, "red"), _pause(3), _task(3, "green"), _task(2, "green"),
                             _task(1, "green")])

    assert len(walk.processes.launched) == 1

    walk.advance("implementation", "failed")

    assert len(walk.processes.launched) == 2
    assert walk.processes.launched[-1] == [*_HEAD, "3"]
    assert walk.state["failure_resumes"] == 1
    assert walk.state["ended"] is None


@pytest.mark.parametrize("product_path", [IN_REPO_PRODUCT, PRODUCT], ids=["in-repo", "external"])
def test_a_failed_run_that_ended_on_its_pause_resumes_after_the_pause(product_path):
    """CP-182 holds "whether it finished or was reported `failed`": a failed run whose end is
    its pause resumes after that pause's `N` — 4 here, a task the run deferred — never after 3,
    the newest landed task beneath it, which is the resume of a run that ended on no pause."""
    commits = [_pause(4), _task(4, "deferred"), _task(3, "green"), _task(2, "green"),
               _task(1, "green")]
    walk = _walk_started_on(commits, product_path=product_path)
    if product_path == PRODUCT:
        walk.git.repos[INSTANCE] = {KEY: [_pause(4)]}
        walk.git.repos[PRODUCT] = {KEY: commits[1:]}
        walk.git.times.update({"9a75e0": 100, "t4-deferred": 95, "t3-green": 90, "t2-green": 80,
                               "t1-green": 70})

    walk.advance("implementation", "failed")

    assert walk.processes.launched[-1] == [*_HEAD, "4"]
    assert walk.state["failure_resumes"] == 1
    assert walk.state["ended"] is None


@pytest.mark.parametrize("later", [
    _task(4, "red"),
    ("e1", "developer: the derived edge cases, each proved by mutation"),
    _task(4, "green"),
], ids=["red-task", "task-less", "green-task"])
def test_any_product_branch_developer_commit_authored_after_the_pause_buries_it(later):
    """CP-182: "the developer's commits on the product's branch count as well as those on the
    instance branch", and a developer commit is any `developer:` subject — not only a landed
    task. One authored a second after the instance pause buries it."""
    git = FakeGit(repos={INSTANCE: {KEY: [_pause(3)]},
                         PRODUCT: {KEY: [later, _task(3, "green")]}},
                  times={"9a75e0": 100, later[0]: 101, "t3-green": 90})

    assert reader(git=git).paused_after(layout(), PRODUCT) is None


# --- guards for two resume behaviours that already hold (CP-185, CP-187) ----------------------


def test_a_pause_subject_is_never_counted_as_a_landed_task_at_a_start():
    """Request item 3 (CP-185): tasks 1 and 2 landed, the pause after 3 above them, instruction
    1-3 — the start launches `2`. It guards `_landed_tasks` counting a pause's `N` as landed:
    every task would land here and the launch would end `3`. The older guard,
    `test_pause_and_marker_subjects_are_not_task_commits`, passes with that rule broken, because
    over its instruction of five a landed task 3 still leaves task 2 the first unlanded."""
    commits = [_pause(3), _task(2, "green"), _task(1, "green")]

    assert _launched_after(commits, numbers=(1, 2, 3)) == [*_HEAD, "2"]


def test_a_pause_after_the_last_task_relaunches_and_the_walk_seals():
    """Request item 4 (CP-187): a pause after the instruction's last task is relaunched like any
    other, and the run it relaunches closes the change — no task left after `N` is not a halt."""
    walk = Walk(through="plan")
    walk.files.write_text(f"{BRANCH_CHANGE}/tl_instruction.md", _instruction(1, 2, 3))
    walk.git.commits[KEY] = [_pause(3), _task(3, "green"), _task(2, "green"), _task(1, "green")]

    walk.advance("implementation")

    assert walk.processes.launched[-1] == [*_HEAD, "3"]
    assert walk.notifier.messages[-1].endswith("paused after task 3 — resuming")
    walk.git.commits[KEY].insert(0, MARKER)
    walk.git.bodies[MARKER[0]] = MARKER_BODY
    walk.advance("implementation")
    assert walk.state["ended"] is None
    land(walk.files, walk.git, "code-integrity")
    walk.advance("code-integrity")
    for audited in PRODUCERS:
        land(walk.files, walk.git, "audit", audited)
        walk.advance(f"audit-{audited}")
        assert walk.state["ended"] is None
    land(walk.files, walk.git, "seal")
    walk.advance("seal")

    assert walk.state["ended"] == "sealed", walk.state.get("ended_reason")
    assert walk.skills_launched == ["development-implementation", "development-implementation",
                                    "development-code-integrity",
                                    *("development-audit" for _ in PRODUCERS), "tobiishi-seal"]


# --- the commit shape is checked too: a TDD-lane task lands only after its red commit ------------
#
# `development-implementation/SKILL.md` Step 2 routes a task into one of six lanes by its gate
# header and its `#### Implement` marker. Only lane (e), the TDD lane, owes a red commit before its
# landing; the other five land as one plain commit. The engine reads the lane off the change's own
# `tl_instruction.md`, so these plans are written in the real heading shape `development-plan`
# writes.

_BEHAVIOURS = ("#### Behaviours to verify (developer adds tests to `tests/test_parse.py`)\n\n"
               "- `test_parse_reads_the_flag` — the flag is read\n\n")
_VERIFICATION = "#### Verification gate\n\nRun `python3 -m pytest -q`.\n\n"
_INFER = "Infer from failing tests."
# The five one-commit markers, verbatim from `development-implementation/SKILL.md` Step 2.
_ONE_COMMIT_MARKERS = ("No spec tests — implement per project layout above.",
                       "Verified by review — no test.",
                       "Tests cannot go red.",
                       "No new tests — TDD under green",
                       "Tests are red at baseline.")


def _implement(body: str) -> str:
    return f"#### Implement\n\n{body}\n\n"


def _plan_task(number: int, *sections: str) -> str:
    """One `### Task <N>` block in the shape `development-plan` writes."""
    return (f"### Task {number}: a task (`core/tools/parse.py`)\n\n**Dependencies:** None\n\n"
            f"**What to build:** a parser.\n\n" + "".join(sections) + "---\n\n")


def _tdd_task(number: int) -> str:
    return _plan_task(number, _BEHAVIOURS, _implement(_INFER), _VERIFICATION)


def _plan(*tasks: str, tail: str = "") -> str:
    return ("# Tech Lead instruction — parse\n\n**Category:** feature\n\n## Project layout\n\n"
            "```\ncore/tools/parse.py  ← new\n```\n\n## TL Review Notes\n\n- none\n\n---\n\n"
            + "".join(tasks) + tail)


def _plan_reader(text: str | None, git=None) -> cd.DiskReader:
    files = {} if text is None else {f"{BRANCH_CHANGE}/tl_instruction.md": text}
    return reader(files, git)


def test_tdd_lane_task_with_behaviours_and_infer_implement_is_read():
    assert _plan_reader(_plan(_tdd_task(1))).tdd_lane_tasks(layout()) == [1]


def test_behaviours_heading_with_a_parenthetical_is_read():
    """Row 22: the real heading carries a parenthetical after its words; a bare one reads too."""
    bare = _plan_task(2, "#### Behaviours to verify\n\n- `test_x` — x\n\n", _implement(_INFER))

    assert _plan_reader(_plan(_tdd_task(1), bare)).tdd_lane_tasks(layout()) == [1, 2]


@pytest.mark.parametrize("marker", _ONE_COMMIT_MARKERS,
                         ids=["no-test", "review-verified", "already-green", "preserving",
                              "red-at-baseline"])
def test_each_one_commit_lane_marker_exempts_its_task(marker):
    """Rows 6–9: the Behaviours heading is kept on purpose, so the marker alone is what exempts."""
    exempt = _plan_task(1, _BEHAVIOURS, _implement(f"{marker}\nReason: already true."),
                        _VERIFICATION)

    assert _plan_reader(_plan(exempt, _tdd_task(2))).tdd_lane_tasks(layout()) == [2]


@pytest.mark.parametrize("dressed", ["`Tests cannot go red.`", "**Tests cannot go red.**",
                                     "**`No new tests — TDD under green`**"])
def test_marker_wrapped_in_backticks_or_bold_still_exempts(dressed):
    """Row 24."""
    exempt = _plan_task(1, _BEHAVIOURS, _implement(dressed), _VERIFICATION)

    assert _plan_reader(_plan(exempt)).tdd_lane_tasks(layout()) == []


def test_task_with_behaviours_but_no_implement_heading_is_in_no_lane():
    """Row 25: CP-188 reads "an `#### Implement` that carries none" — no heading, no lane."""
    headless = _plan_task(1, _BEHAVIOURS, _VERIFICATION)

    assert _plan_reader(_plan(headless)).tdd_lane_tasks(layout()) == []


def test_task_without_behaviours_is_in_no_lane():
    """Row 15."""
    bare = _plan_task(1, _implement(_INFER), _VERIFICATION)

    assert _plan_reader(_plan(bare)).tdd_lane_tasks(layout()) == []


def test_an_implement_heading_is_not_read_off_a_longer_word():
    """`#### Implementation notes` is not the `#### Implement` heading, so a task carrying only it
    has no `#### Implement` and is in no lane."""
    notes = _plan_task(1, _BEHAVIOURS, "#### Implementation notes\n\nInfer from failing tests.\n\n")

    assert _plan_reader(_plan(notes)).tdd_lane_tasks(layout()) == []


def test_a_trailing_h2_section_does_not_extend_the_last_task():
    """Row 23: the last task has no Behaviours of its own; a `## TL Review Notes` after it that
    quotes the heading must not lend it one."""
    tail = "## TL Review Notes\n\n" + _BEHAVIOURS + _implement(_INFER)
    last = _plan_task(1, _implement(_INFER), _VERIFICATION)

    assert _plan_reader(_plan(last, tail=tail)).tdd_lane_tasks(layout()) == []


def test_only_the_task_whose_own_block_holds_behaviours_is_returned():
    """Row 23: task 1's block has no Behaviours; task 2's has. A block ends at the next level-2 or
    level-3 heading, so task 2's heading is read as task 2's alone."""
    no_lane = _plan_task(1, _implement(_INFER), _VERIFICATION)

    assert _plan_reader(_plan(no_lane, _tdd_task(2))).tdd_lane_tasks(layout()) == [2]


def test_tasks_come_back_in_plan_order():
    plan = _plan(_tdd_task(3), _tdd_task(1), _tdd_task(2))

    assert _plan_reader(plan).tdd_lane_tasks(layout()) == [3, 1, 2]


def test_plan_with_no_task_heading_returns_an_empty_list():
    """Row 20."""
    assert _plan_reader(_plan()).tdd_lane_tasks(layout()) == []
    assert _plan_reader("x").tdd_lane_tasks(layout()) == []


def test_absent_plan_returns_none():
    """Row 19: absent is not empty — `None`, so the verdict can tell the two apart."""
    assert _plan_reader(None).tdd_lane_tasks(layout()) is None


def test_implement_body_ends_at_the_next_heading_of_level_four_or_higher():
    """A marker's words under `#### Verification gate`, after the Implement body, do not exempt."""
    gate = "#### Verification gate\n\nTests cannot go red.\n\n"
    task = _plan_task(1, _BEHAVIOURS, _implement(_INFER), gate)

    assert _plan_reader(_plan(task)).tdd_lane_tasks(layout()) == [1]


def test_a_hint_heading_inside_implement_does_not_lose_the_marker_before_it():
    """The real Implement body carries a `# Hint:` line after its marker (`development-plan`'s
    shape). The marker before it still exempts; a TDD body with a hint is still TDD."""
    exempt = _plan_task(1, _BEHAVIOURS, _implement("Tests cannot go red.\n\n# Hint: read it."))
    tdd = _plan_task(2, _BEHAVIOURS, _implement(f"{_INFER}\n\n# Hint: parse by heading."))

    assert _plan_reader(_plan(exempt, tdd)).tdd_lane_tasks(layout()) == [2]


def _marker_reader(*note_lines: str) -> cd.DiskReader:
    """A reader over a branch whose closing marker carries `note_lines` under its review notes."""
    body = (MARKER_BODY + "\nDeveloper Review Notes (vs tl_instruction.md):\n"
            + "".join(f"{line}\n" for line in note_lines))
    return reader(git=FakeGit(commits={KEY: [MARKER]}, bodies={MARKER[0]: body}))


def test_lane_d_note_for_a_task_relanes_it():
    """Row 10: the lane-(d) note form `development-implementation/SKILL.md` Step 3 fixes."""
    notes = _marker_reader("- Task 1 no red (lane d) — the flag already parsed, confirmed")

    assert notes.relaned_tasks(layout()) == {1}


def test_lane_f_note_for_a_task_relanes_it():
    """A TDD-lane task whose failing tests were already on `main` re-lanes to (f), whose note is
    the same line form with its own lane words."""
    notes = _marker_reader("- Task 3 red at baseline (lane f) — 32 listed tests red before, "
                           "green after, confirmed")

    assert notes.relaned_tasks(layout()) == {3}


def test_a_lane_f_note_with_a_blank_reason_relanes_nothing():
    assert _marker_reader("- Task 3 red at baseline (lane f) — ").relaned_tasks(layout()) == set()


def test_a_note_naming_another_lane_relanes_nothing():
    """Only the two lanes whose red the developer cannot commit re-lane a task."""
    for lane in ("no red (lane c)", "red at baseline (lane d)", "no red (lane f)"):
        notes = _marker_reader(f"- Task 1 {lane} — why")

        assert notes.relaned_tasks(layout()) == set(), lane


def test_a_note_for_task_1_does_not_relane_task_10_or_11():
    """Row 11: the number is a whole token, both ways."""
    assert _marker_reader("- Task 1 no red (lane d) — why").relaned_tasks(layout()) == {1}
    assert _marker_reader("- Task 11 no red (lane d) — why").relaned_tasks(layout()) == {11}


def test_a_note_with_a_blank_reason_relanes_nothing():
    """Row 12: the line strip takes the trailing space, so no ` — ` is left to split on."""
    assert _marker_reader("- Task 1 no red (lane d) — ").relaned_tasks(layout()) == set()


def test_a_note_whose_reason_is_only_whitespace_or_emphasis_relanes_nothing():
    for reason in ("\t  ", " ", "**"):
        notes = _marker_reader(f"- Task 1 no red (lane d) — {reason}")

        assert notes.relaned_tasks(layout()) == set(), repr(reason)


def test_a_note_whose_lane_carries_a_qualifier_relanes_its_task():
    """A qualifier after the lane letter, set off by a comma or semicolon, is still the note: the
    line a satellite product's developer wrote (2026-10-12, task 15) halted the walk
    missing-red-commit while its reason stood."""
    line = ("- Task 15 no red (lane d, re-laned; the plan did not predict it) — the package was "
            "built by tasks 8-12, so the comparisons passed the moment they were written")
    assert _marker_reader(line).relaned_tasks(layout()) == {15}
    assert _marker_reader(
        "- Task 3 red at baseline (lane f; re-laned) — the listed tests were red on main"
    ).relaned_tasks(layout()) == {3}


def test_a_lane_letter_run_on_into_other_text_is_not_the_note():
    """Only a comma or semicolon opens a qualifier, so `(lane d2)` or `(lane dx)` names no lane."""
    for lane in ("(lane d2)", "(lane dx)", "(lane d re-laned)"):
        notes = _marker_reader(f"- Task 1 no red {lane} — why")

        assert notes.relaned_tasks(layout()) == set(), lane


def test_a_note_with_no_em_dash_relanes_nothing():
    assert _marker_reader("- Task 1 no red (lane d)").relaned_tasks(layout()) == set()
    assert _marker_reader("- Task 1 no red (lane d) because").relaned_tasks(layout()) == set()


def test_two_notes_relane_two_tasks():
    notes = _marker_reader("- Task 1 no red (lane d) — one", "- Task 4 no red (lane d) — four")

    assert notes.relaned_tasks(layout()) == {1, 4}


def test_a_note_quoted_inside_another_line_relanes_nothing():
    """Anchored on the note's own start: prose that mentions the form is not the note."""
    notes = _marker_reader("- Task 2 re-laned; see `- Task 1 no red (lane d) — x` above")

    assert notes.relaned_tasks(layout()) == set()


def test_no_marker_returns_an_empty_set():
    body = "- Task 1 no red (lane d) — why\n"
    unmarked = reader(git=FakeGit(commits={KEY: [("f00d", "developer: task 1 x")]},
                                  bodies={"f00d": body}))

    assert unmarked.relaned_tasks(layout()) == set()


def _shape(commits: list, tasks=(1,), repo: str = INSTANCE, git=None) -> list[int]:
    """`landed_without_red` over a branch holding `commits`, newest first."""
    scripted = git or FakeGit(commits={KEY: list(commits)})
    return reader(git=scripted).landed_without_red(repo, KEY, list(tasks))


def test_red_then_green_is_not_returned():
    """Row 1."""
    assert _shape([_task(1, "green", slug="parse"), _task(1, "red", slug="parse")]) == []


def test_one_plain_commit_is_returned():
    """Row 2."""
    assert _shape([_task(1, slug="parse")]) == [1]


def test_green_with_no_red_is_returned():
    """Row 3."""
    assert _shape([_task(1, "green")]) == [1]


def test_a_red_newer_than_the_landing_is_returned():
    """Row 4: green, then red — a red written after the task landed proves no red phase."""
    assert _shape([_task(1, "red"), _task(1, "green")]) == [1]


def test_plain_landing_then_red_then_green_is_returned():
    """Row 28: the red must be older than the task's OLDEST landing, not its newest."""
    assert _shape([_task(1, "green"), _task(1, "red"), _task(1)]) == [1]


def test_a_red_of_another_task_does_not_count():
    """Row 27."""
    assert _shape([_task(2, "red"), _task(1)], tasks=(1, 2)) == [1]


def test_task_numbers_are_whole_tokens_both_ways():
    """Row 26: the `task-<N>` form lands and reds its task; task 11's commits are never task 1's."""
    assert _shape([_task(1, "green", form="task-{n}"), _task(1, "red", form="task-{n}")]) == []
    assert _shape([_task(1, "green"), _task(11, "red")], tasks=(1, 11)) == [1]
    assert _shape([_task(11, "green"), _task(1, "red")], tasks=(1, 11)) == [11]


def test_a_task_with_no_landing_is_not_returned():
    """Row 14: only a red, or no commit at all — a missing landing is another obligation."""
    assert _shape([_task(1, "red")]) == []
    assert _shape([]) == []


def test_a_deferred_subject_is_neither_a_landing_nor_a_red():
    """Row 13, the commit half: `— deferred` does not land the task, and is not its red."""
    assert _shape([_task(1, "deferred"), _task(1, "red")]) == []
    assert _shape([_task(1, "green"), _task(1, "deferred")]) == [1]


def test_a_refactor_suffix_counts_as_a_landing():
    assert _shape([_task(1, "refactor")]) == [1]
    assert _shape([_task(1, "refactor"), _task(1, "green"), _task(1, "red")]) == []


def test_a_red_suffix_must_be_exactly_red():
    """CP-191: the last ` — ` suffix is exactly `red`; `red (partial)` is not a red commit."""
    assert _shape([_task(1, "green"), _task(1, "red (partial)")]) == [1]


def test_several_failing_tasks_come_back_ascending():
    """Row 5: each failing task once, in ascending order, whatever order the tasks arrive in."""
    commits = [_task(4), _task(2, "green"), _task(2, "red"), _task(1), _task(1, "green")]

    assert _shape(commits, tasks=(4, 1, 2, 4)) == [1, 4]


def test_only_the_tasks_asked_about_are_judged():
    assert _shape([_task(3), _task(1, "green"), _task(1, "red")], tasks=(1,)) == []


def test_the_named_repo_is_the_one_read():
    """CP-192's read: commits present in another repo are not seen."""
    git = FakeGit(repos={PRODUCT: {KEY: [_task(1)]}, INSTANCE: {KEY: []}})

    assert _shape([], repo=INSTANCE, git=git) == []
    assert _shape([], repo=PRODUCT, git=git) == [1]


# The verdict: once the closing marker lands, every judged TDD-lane task must carry a red commit
# older than its first landing, or the walk stops at `implementation` naming the tasks (CP-193).

_MISSING_RED = "stopped at implementation: missing-red-commit"
_TDD_ONE = _plan(_tdd_task(1))


def _shape_walk(plan: str | None, task_commits: list, body: str = MARKER_BODY,
                *, steps=None, product_path: str = PRODUCT) -> Walk:
    """A walk that entered at implementation, whose developer run then left `task_commits` (newest
    first) under a closing marker carrying `body`, over the branch plan `plan` (`None`: absent)."""
    walk = Walk(through="plan", product_path=product_path) if steps is None else _change_walk()
    plan_path = f"{BRANCH_CHANGE}/tl_instruction.md"
    if plan is None:
        walk.files.files.pop(os.path.normpath(plan_path), None)
    else:
        walk.files.write_text(plan_path, plan)
    walk.git.commits[KEY] = [MARKER, *task_commits]
    walk.git.bodies[MARKER[0]] = body
    walk.advance("implementation")
    return walk


def _change_walk() -> Walk:
    """`_shape_walk`'s world on `CHANGE_STEPS`: the station and change open, specs to plan
    landed."""
    walk = Walk.__new__(Walk)
    disk, walk.git = _through("plan")
    walk.files = FakeFiles({**disk, STATION: "station"})
    walk.processes, walk.notifier, walk.lock = FakeProcesses(), FakeNotifier(), FakeLock()
    walk.engine = lambda: change_build(walk.files, git=walk.git, processes=walk.processes,
                                       notifier=walk.notifier, lock=walk.lock)
    start(walk.engine())
    assert walk.skills_launched == ["development-implementation"]
    return walk


def _passed(walk: Walk) -> bool:
    return (walk.state["ended"] is None
            and walk.skills_launched[-1] == "development-code-integrity")


def test_red_then_green_advances_to_code_integrity():
    """Row 1."""
    walk = _shape_walk(_TDD_ONE, [_task(1, "green", slug="parse"), _task(1, "red", slug="parse")])

    assert _passed(walk)


def test_one_plain_commit_halts_at_implementation_naming_the_task():
    """Row 2."""
    walk = _shape_walk(_TDD_ONE, [_task(1, slug="parse")])

    assert walk.state["ended"] == "halted"
    assert walk.state["ended_reason"] == f"{_MISSING_RED} — task 1"
    assert walk.skills_launched == ["development-implementation"]
    assert walk.notifier.messages[-1].endswith(f"{_MISSING_RED} — task 1")


def test_green_with_no_red_halts():
    """Row 3."""
    walk = _shape_walk(_TDD_ONE, [_task(1, "green", slug="parse")])

    assert walk.state["ended_reason"] == f"{_MISSING_RED} — task 1"


def test_a_red_newer_than_the_landing_halts():
    """Row 4."""
    walk = _shape_walk(_TDD_ONE, [_task(1, "red"), _task(1, "green")])

    assert walk.state["ended_reason"] == f"{_MISSING_RED} — task 1"


def test_failing_tasks_are_named_once_in_ascending_order():
    """Row 5: tasks 4 and 1 each one plain commit; task 2 red then green."""
    plan = _plan(_tdd_task(4), _tdd_task(1), _tdd_task(2))
    walk = _shape_walk(plan, [_task(4), _task(2, "green"), _task(2, "red"), _task(1)])

    assert walk.state["ended_reason"] == f"{_MISSING_RED} — task 1, task 4"


_ONE_COMMIT_LANES = [
    ("no-test", _plan_task(1, _implement(_ONE_COMMIT_MARKERS[0]), _VERIFICATION)),
    ("review-verified", _plan_task(
        1, "#### Deliverables verified by review\n\n- the pin is 1.2.3\n\n",
        _implement(_ONE_COMMIT_MARKERS[1]), _VERIFICATION)),
    ("already-green", _plan_task(
        1, _BEHAVIOURS, _implement(f"{_ONE_COMMIT_MARKERS[2]}\nReason: the flag already parses."),
        _VERIFICATION)),
    ("preserving", _plan_task(
        1, "#### Invariant gate\n\nThe existing suite passes unchanged.\n\n",
        _implement(f"Move per §3.\n\n{_ONE_COMMIT_MARKERS[3]}"), _VERIFICATION)),
    # The failing tests a predecessor change left on `main` are this task's red, so it lands as one
    # commit.
    ("red-at-baseline", _plan_task(
        1, "#### Behaviours to verify (existing tests; the developer adds none)\n\n"
           "- Red at baseline: `tests/test_parse.py::test_parse_reads_the_flag`\n\n",
        _implement(f"{_ONE_COMMIT_MARKERS[4]}\nReason: deferred by the change before."),
        _VERIFICATION)),
]


@pytest.mark.parametrize("task", [lane for _, lane in _ONE_COMMIT_LANES],
                         ids=[name for name, _ in _ONE_COMMIT_LANES])
def test_each_one_commit_lane_lands_as_one_plain_commit_and_passes(task):
    """Rows 6–9, each lane in the shape `development-plan` writes it."""
    assert _passed(_shape_walk(_plan(task), [_task(1)]))


def _notes(*lines: str) -> str:
    return (MARKER_BODY + "\nDeveloper Review Notes (vs tl_instruction.md):\n"
            + "".join(f"{line}\n" for line in lines))


def test_a_recorded_relane_passes():
    """Row 10."""
    body = _notes("- Task 1 no red (lane d) — the flag already parsed, confirmed")

    assert _passed(_shape_walk(_TDD_ONE, [_task(1)], body))


def test_a_recorded_red_at_baseline_relane_passes():
    body = _notes("- Task 1 red at baseline (lane f) — the listed test red before, green after")

    assert _passed(_shape_walk(_TDD_ONE, [_task(1)], body))


def test_a_relane_of_task_1_does_not_exempt_task_10():
    """Row 11."""
    walk = _shape_walk(_plan(_tdd_task(10)), [_task(10)],
                       _notes("- Task 1 no red (lane d) — the flag already parsed"))

    assert walk.state["ended_reason"] == f"{_MISSING_RED} — task 10"


def test_a_relane_with_a_blank_reason_still_halts():
    """Row 12."""
    walk = _shape_walk(_TDD_ONE, [_task(1)], _notes("- Task 1 no red (lane d) — "))

    assert walk.state["ended_reason"] == f"{_MISSING_RED} — task 1"


def test_a_deferred_task_with_red_and_deferred_commits_passes():
    """Row 13: the deferred task is declared unlanded, so it is not judged."""
    body = _marker_with("Deferred: task 1 — the blocked case — docs/record.md § halts",
                        "Failing: tests/test_parse.py::test_flag — task 1")
    walk = _shape_walk(_TDD_ONE, [_task(1, "deferred"), _task(1, "red")], body)

    assert _passed(walk)


def test_a_deferred_task_with_a_plain_landing_is_not_judged():
    """CP-189's second condition, on its own: a landing commit exists, and the `Deferred:` line
    alone is what keeps the task out of the check."""
    body = _marker_with("Deferred: task 1 — the blocked case — docs/record.md § halts",
                        suite="green")

    assert _passed(_shape_walk(_TDD_ONE, [_task(1)], body))


def test_a_tdd_task_with_no_commit_and_no_deferral_passes():
    """Row 14."""
    assert _passed(_shape_walk(_TDD_ONE, []))


def test_a_task_in_no_lane_passes_on_one_plain_commit():
    """Row 15."""
    plan = _plan(_plan_task(1, _implement(_INFER), _VERIFICATION))

    assert _passed(_shape_walk(plan, [_task(1)]))


def test_missing_suite_is_reported_before_missing_red_commit():
    """Row 16."""
    walk = _shape_walk(_TDD_ONE, [_task(1)], "Language resolution:\n- python\n")

    assert walk.state["ended_reason"] == "stopped at implementation: missing-suite"


def test_red_suite_is_reported_before_missing_red_commit():
    """Row 29: a red no deferral owns."""
    walk = _shape_walk(_TDD_ONE, [_task(1)], "Suite: red\n\nLanguage resolution:\n- python\n")

    assert walk.state["ended_reason"] == "stopped at implementation: red-suite"


def test_missing_language_is_reported_before_missing_red_commit():
    """Row 30."""
    walk = _shape_walk(_TDD_ONE, [_task(1)], "Suite: green\n")

    assert walk.state["ended_reason"] == "stopped at implementation: missing-language"


def test_a_pause_with_no_closing_marker_relaunches_without_the_shape_check():
    """Row 17: no marker, the newest developer commit is the pause after task 1 — relaunched
    exactly as before this check existed."""
    walk = Walk(through="plan")
    walk.files.write_text(f"{BRANCH_CHANGE}/tl_instruction.md", _plan(_tdd_task(1), _tdd_task(2)))
    walk.git.commits[KEY] = [_pause(1), _task(1, slug="parse")]

    walk.advance("implementation")

    assert walk.processes.launched[-1] == [*_HEAD, "1"]
    assert walk.state["ended"] is None
    assert walk.state["paused_after"] == 1
    assert "missing-red-commit" not in walk.state["ended_reason"]


def test_external_product_commits_are_read_on_the_product_repo_on_advance():
    """Row 18, CP-192 on the advance path: the per-task commits are on the product repo's branch,
    the marker on the instance's. The instance branch alone would show no landing at all."""
    good = _external_walk([_task(1, "green"), _task(1, "red")], instance_commits=[MARKER])
    good.files.write_text(f"{BRANCH_CHANGE}/tl_instruction.md", _TDD_ONE)
    good.git.bodies[MARKER[0]] = MARKER_BODY
    good.advance("implementation")
    bad = _external_walk([_task(1)], instance_commits=[MARKER])
    bad.files.write_text(f"{BRANCH_CHANGE}/tl_instruction.md", _TDD_ONE)
    bad.git.bodies[MARKER[0]] = MARKER_BODY
    bad.advance("implementation")

    assert _passed(good)
    assert bad.state["ended_reason"] == f"{_MISSING_RED} — task 1"


def test_an_in_repo_product_reads_the_instance_branch():
    """A product path inside the instance shares the instance's branch."""
    walk = _shape_walk(_TDD_ONE, [_task(1)], product_path=f"{INSTANCE}/product")

    assert walk.state["ended_reason"] == f"{_MISSING_RED} — task 1"


def test_an_absent_plan_at_advance_halts_unreadable_plan():
    """Row 19."""
    walk = _shape_walk(None, [_task(1)])

    assert walk.state["ended_reason"] == "stopped at implementation: unreadable-plan"


def test_a_readable_plan_with_no_task_heading_passes():
    """Row 20."""
    assert _passed(_shape_walk(_plan(), [_task(1)]))


def test_chain_change_halts_at_implementation_with_the_same_line():
    """Row 22."""
    walk = _shape_walk(_TDD_ONE, [_task(1, slug="parse")], steps=cd.CHANGE_STEPS)

    assert walk.state["ended_reason"] == f"{_MISSING_RED} — task 1"
    assert walk.state["chain_name"] == "change"


# `describe` reads the product path too, so a dry run and a start judge the same repo (CP-192 on the
# describe path). Empty means the product lives in the instance.


def _row_two_disk(commits: list | None = None) -> tuple[dict, FakeGit]:
    """Row 2's branch as a start meets it: every step through implementation landed, and task 1 of
    a TDD-lane plan landed as one plain commit."""
    files, git = _through("implementation")
    files[f"{BRANCH_CHANGE}/tl_instruction.md"] = _TDD_ONE
    git.commits[KEY] = [MARKER, *(commits if commits is not None else [_task(1, slug="parse")])]
    return files, git


def _real_row_two(tmp_path) -> Path:
    """Row 2 on a real disk: the change's artifacts in its worktree folder, and a real instance repo
    whose `<key>` branch holds one plain task commit under the closing marker."""
    instance = _instance_with_one_change(tmp_path)
    folder = instance / ".worktrees" / KEY / CHANGE_REL
    folder.mkdir(parents=True)
    for name, text in (("change_spec.md", "x"), ("change_design.md", NO_TEXT_DESIGN),
                       ("tl_instruction.md", _TDD_ONE)):
        (folder / name).write_text(text)
    _git(instance, "init", "-q", "-b", "main")
    _git(instance, "commit", "-q", "--allow-empty", "-m", "root")
    _git(instance, "checkout", "-q", "-b", KEY)
    _git(instance, "commit", "-q", "--allow-empty", "-m", "developer: task 1 parse")
    _git(instance, "commit", "-q", "--allow-empty", "-m", MARKER[1], "-m", MARKER_BODY)
    _git(instance, "checkout", "-q", "main")
    return instance


def test_describe_over_a_missing_red_commit_prints_the_line_and_exits_three(tmp_path, capsys):
    """Row 21, through the real composition."""
    instance = _real_row_two(tmp_path)

    code = cd.main(["--describe", str(tmp_path / "state.json"), "--instance-root", str(instance),
                    "--project", PROJECT])

    captured = capsys.readouterr()
    assert code == 3
    assert captured.err.strip() == f"chain_development: {_MISSING_RED} — task 1"
    assert captured.out == ""


def test_start_over_a_missing_red_commit_refuses_and_writes_nothing():
    """CP-193, start: the entry lies past implementation, so the start refuses with row 2's line."""
    files, git = _row_two_disk()
    disk = FakeFiles(files)
    before = dict(disk.files)
    processes, notifier = FakeProcesses(), FakeNotifier()

    with pytest.raises(cd.ChainRefused) as refused:
        start(build(disk, git=git, processes=processes, notifier=notifier))

    assert str(refused.value) == f"{_MISSING_RED} — task 1"
    assert disk.files == before
    assert processes.calls == []
    assert notifier.messages == []


def _external_row_two() -> tuple[dict, FakeGit]:
    files, _ = _row_two_disk()
    git = FakeGit(repos={PRODUCT: {KEY: [_task(1, slug="parse")]}, INSTANCE: {KEY: [MARKER]}},
                  bodies={MARKER[0]: MARKER_BODY})
    return files, git


def test_a_start_on_an_external_product_judges_the_product_repo():
    """`_start` hands its own product path to `describe`: the plain commit is on the product
    repo."""
    files, git = _external_row_two()

    with pytest.raises(cd.ChainRefused, match=f"{_MISSING_RED} — task 1"):
        start(build(FakeFiles(files), git=git), product_path=PRODUCT)


def test_external_describe_with_a_product_path_reads_the_product_repo():
    files, git = _external_row_two()
    engine = build(FakeFiles(files), git=git)

    with pytest.raises(cd.ChainRefused, match=f"{_MISSING_RED} — task 1"):
        engine.describe(instance_root=INSTANCE, project=PROJECT, product_path=PRODUCT)


def test_external_describe_without_a_product_path_reads_the_instance():
    """The documented default: no product path is the instance, whose branch holds no landing."""
    files, git = _external_row_two()

    plan = describe(build(FakeFiles(files), git=git))

    assert plan.entry == "code-integrity"


def test_describe_still_works_without_a_product_path():
    files, git = _row_two_disk([_task(1, "green"), _task(1, "red")])

    plan = build(FakeFiles(files), git=git).describe(instance_root=INSTANCE, project=PROJECT)

    assert (plan.key, plan.entry) == (KEY, "code-integrity")


def test_main_describe_accepts_product_path_and_does_not_require_it(tmp_path, capsys):
    instance = _real_row_two(tmp_path)
    product = tmp_path / "product"
    product.mkdir()
    _git(product, "init", "-q", "-b", "main")
    _git(product, "commit", "-q", "--allow-empty", "-m", "root")
    _git(product, "checkout", "-q", "-b", KEY)
    for subject in ("developer: task 1 parse — red", "developer: task 1 parse — green"):
        _git(product, "commit", "-q", "--allow-empty", "-m", subject)
    base = ["--describe", str(tmp_path / "state.json"), "--instance-root", str(instance),
            "--project", PROJECT]

    assert cd.main([*base, "--product-path", str(product)]) == 0
    assert capsys.readouterr().out.splitlines()[:2] == [f"key={KEY}", "entry=code-integrity"]
    assert cd.main([*base, "--product-path", str(instance)]) == 3
    assert cd.main(base) == 3
    capsys.readouterr()
    assert cd.main(["--describe", "/s", "--product-path", str(product)]) == 2
    assert capsys.readouterr().err.strip() == (
        "chain_development: --describe requires --instance-root, --project")


def test_an_empty_product_path_is_never_treated_as_the_repo():
    git = FakeGit(repos={INSTANCE: {KEY: [_task(1)]}, "": {KEY: []}})
    disk = reader(git=git)

    assert disk.code_repo(layout(), "") == INSTANCE
    assert disk.landed_without_red(disk.code_repo(layout(), ""), KEY, [1]) == [1]


# --- code-integrity additions (senior-engineer, 2026-09-30) --------------------------------------


def test_a_deferral_exempts_only_the_task_it_names():
    """CP-189: a task is left out of the check only when a `Deferred:` line names *that* task.
    Task 2 is deferred; task 1, also one plain commit, is still judged — and task 10's deferral
    is not task 1's."""
    plan = _plan(_tdd_task(1), _tdd_task(2))
    body = _marker_with("Deferred: task 2 — the blocked case — docs/record.md § halts",
                        suite="green")
    walk = _shape_walk(plan, [_task(2), _task(1)], body)

    assert walk.state["ended_reason"] == f"{_MISSING_RED} — task 1"

    plan = _plan(_tdd_task(1), _tdd_task(10))
    body = _marker_with("Deferred: task 10 — the blocked case — docs/record.md § halts",
                        suite="green")
    walk = _shape_walk(plan, [_task(10), _task(1)], body)

    assert walk.state["ended_reason"] == f"{_MISSING_RED} — task 1"


def _real_dated_branch(tmp_path, dated_subjects: list[tuple[str, str]]) -> Path:
    """A real instance whose `<key>` branch holds `dated_subjects` in commit order (oldest first),
    each `(subject, date)` committed with that author and committer date, then the closing
    marker — over a one-task TDD-lane plan."""
    instance = _instance_with_one_change(tmp_path)
    folder = instance / ".worktrees" / KEY / CHANGE_REL
    folder.mkdir(parents=True)
    for name, text in (("change_spec.md", "x"), ("change_design.md", NO_TEXT_DESIGN),
                       ("tl_instruction.md", _TDD_ONE)):
        (folder / name).write_text(text)
    _git(instance, "init", "-q", "-b", "main")
    _git(instance, "commit", "-q", "--allow-empty", "-m", "root")
    _git(instance, "checkout", "-q", "-b", KEY)
    for subject, date in dated_subjects:
        subprocess.run(
            ["git", "-C", str(instance), "-c", "core.hooksPath=/dev/null", "-c", "user.name=t",
             "-c", "user.email=t@example.invalid", "commit", "-q", "--allow-empty", "-m", subject],
            check=True, capture_output=True,
            env={**os.environ, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})
    _git(instance, "commit", "-q", "--allow-empty", "-m", MARKER[1], "-m", MARKER_BODY)
    _git(instance, "checkout", "-q", "main")
    return instance


@pytest.mark.parametrize("dated_subjects, refused", [
    # The red is NEWER on the branch than the landing, though its clock reads earlier: halts.
    ([("developer: task 1 parse — green", "2026-01-02T00:00:00Z"),
      ("developer: task 1 parse — red", "2026-01-01T00:00:00Z")], True),
    # The red is OLDER on the branch than the landing, though its clock reads later: passes.
    ([("developer: task 1 parse — red", "2026-01-02T00:00:00Z"),
      ("developer: task 1 parse — green", "2026-01-01T00:00:00Z")], False),
    # Both on one clock second, the tie a real red/green pair routinely makes: branch order rules.
    ([("developer: task 1 parse — green", "2026-01-01T00:00:00Z"),
      ("developer: task 1 parse — red", "2026-01-01T00:00:00Z")], True),
    ([("developer: task 1 parse — red", "2026-01-01T00:00:00Z"),
      ("developer: task 1 parse — green", "2026-01-01T00:00:00Z")], False),
], ids=["red-newer-clock-older", "red-older-clock-newer", "tie-red-newer", "tie-red-older"])
def test_older_is_read_by_branch_order_on_a_real_repo_never_by_date(tmp_path, capsys,
                                                                     dated_subjects, refused):
    """CP-191: a red counts when it is older *on that branch* than the task's oldest landing — the
    order the commits were made in, which a skewed or tied clock does not change. Through the real
    git adapter, not a scripted list."""
    instance = _real_dated_branch(tmp_path, dated_subjects)

    code = cd.main(["--describe", str(tmp_path / "state.json"), "--instance-root", str(instance),
                    "--project", PROJECT])

    captured = capsys.readouterr()
    if refused:
        assert code == 3
        assert captured.err.strip() == f"chain_development: {_MISSING_RED} — task 1"
    else:
        assert code == 0, captured.err
        assert captured.out.splitlines()[:2] == [f"key={KEY}", "entry=code-integrity"]


# --- a stop ends the walk (CP-373 to CP-383) ----------------------------------------------------
#
# A stop reaches a launch through the identity file its run recorded, and signals a process only
# while its pid still has the start time written there. `FakeProcessTable` stands for the system's
# process table: a test records the identity the run launcher would have written, then changes the
# table to say what became of the processes.

STOP_AT = "2026-10-02T15:30:00+00:00"
RUN_START, WATCHER_START = "Fri Oct  2 15:24:58 2026", "Fri Oct  2 15:24:59 2026"
BOTH_TABLES = [pytest.param(cd.DEVELOPMENT_STEPS, "development", id="development"),
               pytest.param(cd.CHANGE_STEPS, "change", id="change")]


def record_identity(walk, run: str, run_pid: int, watcher_pid: int, chain: str = "development"):
    """What the run launcher writes for a launch: both pids, each with its start time."""
    walk.table.starts[run_pid], walk.table.starts[watcher_pid] = RUN_START, WATCHER_START
    walk.files.write_text(identity_file(run, chain),
                          walk_stop.identity_text(walk.table, run_pid, watcher_pid))


def a_walk_over(steps, table=None) -> Walk:
    """A walk of the given table, started at its first step on a scripted disk."""
    if steps is cd.CHANGE_STEPS:
        return _started_change_walk(table)
    return Walk(table=table)


def _started_change_walk(table) -> Walk:
    walk = Walk.__new__(Walk)
    walk.files, walk.git = FakeFiles(), FakeGit()
    walk.processes, walk.notifier, walk.lock = FakeProcesses(), FakeNotifier(), FakeLock()
    walk.steps, walk.table = cd.CHANGE_STEPS, table or FakeProcessTable()
    walk.provider_port = ProviderText()
    start(walk.engine())
    return walk


def test_each_launch_records_its_identity_file_on_pending_and_in_its_environment():
    files = FakeFiles({**fresh_change(), identity_file("specs"): "left by an earlier launch"})
    seen = []
    processes = FakeProcesses(
        on_run=lambda argv: seen.append(files.read_text(identity_file("specs"))))

    start(build(files, processes=processes,
                environ={"PATH": "/usr/bin", "DETACHED_RUN_PID": "999",
                         "DETACH_PROCESS_WATCHER_PID": "998"}))

    env = processes.calls[0]["env"]
    assert saved(files)["pending"]["specs"]["identity"] == identity_file("specs")
    assert env[walk_stop.IDENTITY_VARIABLE] == identity_file("specs")
    assert "DETACHED_RUN_PID" not in env and "DETACH_PROCESS_WATCHER_PID" not in env
    assert seen == [""]


def test_a_stop_ends_a_live_walk_stopping_its_watcher_then_its_run():
    walk = Walk()
    record_identity(walk, "specs", run_pid=100, watcher_pid=101)

    walk.engine().stop(STOP_AT)

    assert walk.table.stopped == [101, 100]
    assert STATE in walk.files.files
    assert walk.state["ended"] == "stopped"
    assert walk.state["pending"] == {}
    assert STOP_AT in walk.state["ended_reason"] and "stopped" in walk.state["ended_reason"]


def test_a_stop_stops_every_run_of_the_audit_fan_out():
    walk = Walk(through="code-integrity")
    for index, skill in enumerate(PRODUCERS):
        record_identity(walk, f"audit-{skill}", run_pid=200 + 2 * index,
                        watcher_pid=201 + 2 * index)
    messages_before = len(walk.notifier.messages)

    walk.engine().stop(STOP_AT)

    assert len(walk.table.stopped) == 8
    assert len(walk.notifier.messages) == messages_before + 1
    assert walk.state["pending"] == {}


def test_a_stop_on_a_walk_whose_run_and_watcher_are_gone_ends_it_at_once():
    walk = Walk()
    record_identity(walk, "specs", run_pid=100, watcher_pid=101)
    walk.table.starts.clear()

    walk.engine().stop(STOP_AT)

    assert walk.table.stopped == []
    assert walk.state["ended"] == "stopped"
    assert "already gone" in walk.state["ended_reason"]


def test_a_stop_never_signals_a_recycled_pid():
    walk = Walk()
    record_identity(walk, "specs", run_pid=100, watcher_pid=101)
    walk.table.starts[100] = "Sat Oct  3 09:00:00 2026"
    walk.table.starts[101] = "Sat Oct  3 09:00:01 2026"

    walk.engine().stop(STOP_AT)

    assert walk.table.stopped == []
    assert walk.state["ended"] == "stopped"


@pytest.mark.parametrize("how", ["no identity key", "empty file"])
def test_a_stop_on_a_launch_with_no_recorded_identity_signals_nothing_and_says_so(how):
    walk = Walk()
    walk.table.starts[100] = RUN_START
    if how == "no identity key":
        pre_change = walk.state
        del pre_change["pending"]["specs"]["identity"]
        walk.files.write_text(STATE, json.dumps(pre_change))

    message = walk.engine().stop(STOP_AT)

    assert walk.table.stopped == []
    assert "no recorded identity" in walk.state["ended_reason"]
    assert "no recorded identity" in message


def test_a_stop_on_an_ended_walk_changes_nothing_and_names_its_end():
    walk = Walk()
    walk.advance("specs", "timeout")
    before = walk.files.files[STATE]

    message = walk.engine().stop(STOP_AT)

    assert walk.files.files[STATE] == before
    assert "halted" in message
    assert walk.table.stopped == []


def test_a_stop_with_no_state_says_there_is_no_walk_and_writes_nothing():
    files = FakeFiles()

    message = build(files).stop(STOP_AT)

    assert "no development walk" in message
    assert files.files == {}


def test_a_stop_sends_one_message_and_returns_it():
    walk = Walk()
    messages_before = len(walk.notifier.messages)

    message = walk.engine().stop(STOP_AT)

    assert walk.notifier.messages[messages_before:] == [message]


def test_a_stop_runs_the_on_end_command_once_with_stopped_after_releasing_the_lock():
    walk = HookedWalk()

    walk.engine().stop(STOP_AT)

    assert [call["argv"] for call in walk.hook_calls] == [[*HOOK_ARGV, "stopped"]]
    assert walk.state_when_hook_ran == ["stopped"]
    assert walk.lock_held_when_hook_ran == [False]


def test_a_stop_holds_the_state_lock():
    walk = Walk()
    holds_before = len(walk.lock.holds)

    walk.engine().stop(STOP_AT)

    assert walk.lock.holds[holds_before:] == [STATE]


def test_a_finish_delivered_after_a_stop_is_a_counted_reentry():
    walk = Walk()
    walk.engine().stop(STOP_AT)

    result = walk.advance("specs", "failed")

    assert result.acted is False
    assert walk.state["reentries"] == 1
    assert walk.state["ended"] == "stopped"


@pytest.mark.parametrize("steps, chain", BOTH_TABLES)
def test_a_start_after_a_stop_is_accepted(steps, chain):
    walk = a_walk_over(steps)
    walk.engine().stop(STOP_AT)
    launches_before = len(walk.processes.launched)

    start(walk.engine())

    assert len(walk.processes.launched) == launches_before + 1
    assert walk.state["ended"] is None


@pytest.mark.parametrize("steps, chain", BOTH_TABLES)
def test_the_refusal_names_the_stop_command_and_never_deleting(steps, chain):
    walk = a_walk_over(steps)

    with pytest.raises(cd.ChainAlreadyWalking) as refused:
        start(walk.engine())

    assert f"{CORE}/launchers/chain-{chain}/launcher.sh {PROJECT} --stop" in str(refused.value)
    assert "delete" not in str(refused.value).lower()


def test_the_refusal_says_nothing_will_finish_a_walk_whose_processes_are_gone():
    walk = Walk()
    record_identity(walk, "specs", run_pid=100, watcher_pid=101)
    walk.table.starts.clear()

    with pytest.raises(cd.ChainAlreadyWalking, match="(?i)nothing will finish"):
        start(walk.engine())


def test_the_refusal_over_a_walk_with_a_live_run_says_to_let_it_finish_or_stop_it():
    walk = Walk()
    record_identity(walk, "specs", run_pid=100, watcher_pid=101)

    with pytest.raises(cd.ChainAlreadyWalking, match="(?i)let it finish"):
        start(walk.engine())


def test_main_stop_reads_the_table_from_the_state_and_exits_0(tmp_path, capsys):
    path = _state_file(tmp_path, chain_name="change",
                       pending={"change": {"step": "change", "audited": None}})

    assert cd.main(["--stop", str(path)]) == 0

    assert "change chain" in capsys.readouterr().out
    state = json.loads(path.read_text())
    assert state["ended"] == "stopped" and state["pending"] == {}


def test_main_stop_uses_the_notifier_it_is_given_and_otherwise_the_states(tmp_path, notifier_log):
    script, log = notifier_log
    path = _state_file(tmp_path, notifier=str(script),
                       pending={"specs": {"step": "specs", "audited": None}})

    assert cd.main(["--stop", str(path)]) == 0
    assert "stopped" in log.read_text()

    other = tmp_path / "other-notify.sh"
    other_log = tmp_path / "other.log"
    other.write_text(f"#!/usr/bin/env bash\nprintf '%s\\n' \"$1\" >> {other_log}\n")
    other.chmod(0o755)
    again = _state_file(tmp_path, notifier=str(script),
                        pending={"specs": {"step": "specs", "audited": None}})
    assert cd.main(["--stop", str(again), "--notifier", str(other)]) == 0
    assert "stopped" in other_log.read_text()


def test_main_stop_with_no_state_exits_0_and_says_there_is_no_walk(tmp_path, capsys):
    missing = tmp_path / "logs" / "state.json"

    assert cd.main(["--stop", str(missing)]) == 0

    assert "no development walk" in capsys.readouterr().out
    assert not missing.exists()


@pytest.mark.parametrize("other", [["--start", "/s"], ["--advance", "/s", "specs", "completed"],
                                   ["--describe", "/s"]])
def test_main_stop_is_exclusive_with_start_advance_and_describe(other, capsys):
    assert cd.main(["--stop", "/s", *other]) == 2
    assert "mutually exclusive" in capsys.readouterr().err


# --- the content step: a text change runs the Content Editor, any other passes it --------------
#
# `Publishes text:` in `change_design.md` is the one fact the step turns on. These tests pin what
# the engine does with each answer — run, pass, or halt before any launch — over the same fakes
# every other walk here uses.

DESIGN_PATH = f"{BRANCH_CHANGE}/change_design.md"
ENGINE_REPORT = f"{BRANCH_CHANGE}/halt_report.md"
MOVED_REPORT = f"{STATE}.content-halt-report.md"
NO_VERDICT_DESIGN = "# Change Design\n\n**Behaviour:** changing\n"


def _plan_landed(design: str | None) -> tuple[dict, FakeGit]:
    """The disk once `plan` has landed, with `design` as the whole of `change_design.md` — or no
    such file at all for `None`."""
    files, git = _through("plan")
    if design is None:
        del files[DESIGN_PATH]
    else:
        files[DESIGN_PATH] = design
    return files, git


def _started_with(design: str | None, **extra_files) -> tuple[FakeFiles, FakeProcesses, FakeGit]:
    """A walk started (not advanced) on a change whose plan has landed."""
    files, git = _plan_landed(design)
    files.update(extra_files)
    disk, processes = FakeFiles(files), FakeProcesses()
    start(build(disk, git=git, processes=processes))
    return disk, processes, git


def _advanced_past_plan(design: str | None) -> Walk:
    """A walk started at `plan` whose run has ended with the plan on disk — the `_after(plan)`
    path into the step. `design` replaces the one `_through` wrote."""
    walk = Walk(through="design")
    if design is None:
        del walk.files.files[os.path.normpath(DESIGN_PATH)]
    else:
        walk.files.write_text(DESIGN_PATH, design)
    land(walk.files, walk.git, "plan")
    walk.advance("plan")
    return walk


def test_the_content_step_is_in_both_tables_with_the_content_editor_role():
    for table in (cd.DEVELOPMENT_STEPS, cd.CHANGE_STEPS):
        assert [entry.id for entry in table if entry.role == "content-editor"] == ["content"]
        assert [entry.id for entry in table if entry.id != "content"] == [
            entry.id for entry in table if entry.id in
            {"station", "change", "specs", "design", "plan", "implementation",
             "code-integrity", "audit", "seal", "refine"}]
    seven = ["specs", "design", "plan", "implementation", "code-integrity", "audit", "seal"]
    assert [entry.id for entry in cd.DEVELOPMENT_STEPS if entry.id != "content"] == seven
    assert [entry.id for entry in cd.CHANGE_STEPS if entry.id != "content"] == [
        "station", "change", *seven, "refine"]
    assert cd.CHANGE_STEPS[2:-1] == cd.DEVELOPMENT_STEPS


def test_a_no_text_change_passes_the_content_step_without_a_launch():
    walk = _advanced_past_plan(NO_TEXT_DESIGN)

    assert walk.skills_launched == ["development-plan", "development-implementation"]
    assert walk.processes.launched[-1] == [SKILL_LAUNCHER, "development-implementation", PROJECT,
                                           KEY]
    assert "content passed — Publishes text: no" in walk.state["history"]
    assert walk.state["ended"] is None
    assert set(walk.state["pending"]) == {"implementation"}

    files, git = _plan_landed(NO_TEXT_DESIGN)
    assert describe(build(FakeFiles(files), git=git)).entry == "implementation"
    processes = FakeProcesses()
    start(build(FakeFiles(files), git=git, processes=processes))
    assert processes.launched == [[SKILL_LAUNCHER, "development-implementation", PROJECT, KEY]]


def test_a_text_change_launches_the_content_editor_once():
    walk = _advanced_past_plan(TEXT_DESIGN)

    assert walk.skills_launched == ["development-plan", "development-content"]
    assert walk.processes.launched[-1] == [SKILL_LAUNCHER, "development-content", PROJECT, KEY]
    assert walk.processes.calls[-1]["env"]["INSTRUMENT_RUN_ROLE"] == "content-editor"
    assert "content passed — Publishes text: no" not in walk.state["history"]

    land(walk.files, walk.git, "content")
    walk.advance("content")

    assert walk.skills_launched == ["development-plan", "development-content",
                                    "development-implementation"]
    assert walk.state["ended"] is None


def test_a_text_change_whose_text_landed_is_not_run_again():
    files, git = _plan_landed(TEXT_DESIGN)
    files[f"{BRANCH_CHANGE}/change_text.md"] = "the text"

    assert reader(files).is_done(layout(), step("content"))
    assert describe(build(FakeFiles(files), git=git)).entry == "implementation"
    processes = FakeProcesses()
    start(build(FakeFiles(files), git=git, processes=processes))
    assert processes.launched == [[SKILL_LAUNCHER, "development-implementation", PROJECT, KEY]]


_UNSETTLED = [
    pytest.param(NO_VERDICT_DESIGN, id="no-line"),
    pytest.param("**Publishes text:** maybe\n", id="maybe"),
    pytest.param("**Publishes text:** Yes\n", id="capitalised"),
    pytest.param("**Publishes text:**\n", id="empty-value"),
    pytest.param(None, id="no-design-file"),
]


@pytest.mark.parametrize("design", _UNSETTLED)
def test_an_unsettled_verdict_halts_at_content_before_any_launch_after_the_plan(design):
    walk = _advanced_past_plan(design)

    assert walk.skills_launched == ["development-plan"]
    assert walk.state["ended"] == "halted"
    assert "stopped at content: missing-text-verdict" in walk.state["ended_reason"]
    assert f"halt_report.md at {ENGINE_REPORT}" in walk.state["ended_reason"]
    report = walk.files.read_text(ENGINE_REPORT)
    assert report.splitlines()[0] == cd.engine_report_marker(step("content"))
    assert "Publishes text:" in report


@pytest.mark.parametrize("design", [case for case in _UNSETTLED
                                    if case.values[0] is not None])
def test_an_unsettled_verdict_halts_at_content_before_any_launch_on_a_start(design):
    """A start whose entry is `content`. A change with no `change_design.md` cannot enter here:
    its entry is `design`, the first step whose evidence is missing."""
    disk, processes, _ = _started_with(design)

    assert processes.calls == []
    assert saved(disk)["ended"] == "halted"
    assert "stopped at content: missing-text-verdict" in saved(disk)["ended_reason"]
    report = disk.read_text(ENGINE_REPORT)
    assert report.splitlines()[0] == cd.engine_report_marker(step("content"))
    assert "Publishes text:" in report


def test_the_verdict_reads_past_its_markdown():
    def verdict(design: str) -> cd.RunVerdict:
        return reader({DESIGN_PATH: design}).run_verdict(layout(), step("content"))

    assert verdict("**Publishes text:** no\n") is cd.RunVerdict.PASS
    assert verdict("Publishes text: yes — two pages\n") is cd.RunVerdict.RUN
    # The first line that starts with the prefix is the verdict; a later one is body.
    assert verdict("**Publishes text:** no\n\nPublishes text: yes\n") is cd.RunVerdict.PASS
    # A mention that does not start a line is not a verdict at all.
    assert verdict("# Design\n\nThe Publishes text: yes line is stamped by the architect.\n"
                   ) is cd.RunVerdict.UNSETTLED


def test_a_bare_yes_runs_the_step_and_a_no_with_a_reason_passes_it():
    def verdict(design: str) -> cd.RunVerdict:
        return reader({DESIGN_PATH: design}).run_verdict(layout(), step("content"))

    assert verdict("**Publishes text:** yes\n") is cd.RunVerdict.RUN
    assert verdict("**Publishes text:** no — nothing user-facing\n") is cd.RunVerdict.PASS


def test_a_verdict_dressed_in_emphasis_reads_as_its_word():
    """`change_design.md` § 3 Sub-job A: the value is undressed before its first word is read, so
    emphasis on the value — not only on the label — settles nothing differently. Undressing never
    widens the word: `Yes` stays unsettled however it is dressed."""
    def verdict(design: str) -> cd.RunVerdict:
        return reader({DESIGN_PATH: design}).run_verdict(layout(), step("content"))

    assert verdict("Publishes text: **no**\n") is cd.RunVerdict.PASS
    assert verdict("**Publishes text: no**\n") is cd.RunVerdict.PASS
    assert verdict("Publishes text: _no_\n") is cd.RunVerdict.PASS
    assert verdict("**Publishes text:** *yes* — the glossary page\n") is cd.RunVerdict.RUN
    assert verdict("**Publishes text:** `yes` — the glossary page\n") is cd.RunVerdict.RUN
    assert verdict("**Publishes text:** **Yes**\n") is cd.RunVerdict.UNSETTLED


def test_the_engine_never_overwrites_a_halt_report_it_did_not_write():
    other = "wrong-posture\n"
    disk, processes, _ = _started_with(NO_VERDICT_DESIGN, **{ENGINE_REPORT: other})

    assert disk.read_text(ENGINE_REPORT) == other
    assert processes.calls == []
    assert saved(disk)["ended"] == "halted"
    assert f"halt_report.md at {ENGINE_REPORT}" in saved(disk)["ended_reason"]


@pytest.mark.parametrize("design, launches", [
    pytest.param(NO_TEXT_DESIGN, ["development-implementation"], id="a-later-pass"),
    pytest.param(TEXT_DESIGN, ["development-content"], id="a-later-launch"),
])
def test_the_engine_moves_its_own_report_once_the_verdict_is_settled(design, launches):
    own = cd.engine_report_marker(step("content")) + "\n\nthe engine's report\n"
    disk, processes, _ = _started_with(design, **{ENGINE_REPORT: own})

    assert not disk.is_file(ENGINE_REPORT)
    assert disk.read_text(MOVED_REPORT) == own
    assert [argv[1] for argv in processes.launched] == launches


def test_an_engine_report_committed_on_the_branch_is_left_in_place():
    own = cd.engine_report_marker(step("content")) + "\n\ncommitted by an owner\n"
    files, git = _plan_landed(NO_TEXT_DESIGN)
    files[ENGINE_REPORT] = own
    git.paths[KEY] = {f"{CHANGE_REL}/halt_report.md"}
    disk, processes = FakeFiles(files), FakeProcesses()

    start(build(disk, git=git, processes=processes))

    assert disk.read_text(ENGINE_REPORT) == own
    assert not disk.is_file(MOVED_REPORT)
    assert [argv[1] for argv in processes.launched] == ["development-implementation"]


@pytest.mark.parametrize("design, launched", [
    pytest.param(TEXT_DESIGN, "development-content", id="yes"),
    pytest.param(NO_TEXT_DESIGN, "development-implementation", id="no"),
])
def test_a_walk_halted_for_a_missing_verdict_resumes_once_the_line_is_added(design, launched):
    files, git = _plan_landed(NO_VERDICT_DESIGN)
    disk, processes = FakeFiles(files), FakeProcesses()
    start(build(disk, git=git, processes=processes))
    assert saved(disk)["ended"] == "halted"
    assert processes.calls == []

    disk.write_text(DESIGN_PATH, design)
    start(build(disk, git=git, processes=processes))

    assert [argv[1] for argv in processes.launched] == [launched]
    assert saved(disk)["ended"] is None
    assert not disk.is_file(ENGINE_REPORT)


@pytest.mark.parametrize("landed_through, entry", [
    pytest.param("implementation", "code-integrity", id="marker"),
    pytest.param("code-integrity", "audit", id="integrity-report"),
    pytest.param("audit", "seal", id="audits"),
])
def test_a_change_past_the_content_step_is_never_entered_there(landed_through, entry):
    files, git = _through(landed_through)
    files[DESIGN_PATH] = NO_VERDICT_DESIGN
    assert f"{BRANCH_CHANGE}/change_text.md" not in files
    processes = FakeProcesses()

    assert describe(build(FakeFiles(files), git=git)).entry == entry
    disk = FakeFiles(files)
    start(build(disk, git=git, processes=processes))

    assert saved(disk)["ended"] is None
    assert processes.calls and processes.launched[0][1] == next(
        candidate.skill for candidate in cd.DEVELOPMENT_STEPS if candidate.id == entry)
    assert not disk.is_file(ENGINE_REPORT)


def test_a_content_run_with_no_output_halts_the_walk():
    walk = _advanced_past_plan(TEXT_DESIGN)

    walk.advance("content")

    assert walk.state["ended"] == "halted"
    assert "no change_text.md after the run ended" in walk.state["ended_reason"]
    assert "development-implementation" not in walk.skills_launched


def test_a_content_run_that_left_a_halt_report_stops_the_walk():
    walk = _advanced_past_plan(TEXT_DESIGN)
    walk.files.write_text(ENGINE_REPORT, "wrong-posture\n")

    walk.advance("content")

    assert walk.state["ended"] == "halted"
    assert f"halt_report.md at {ENGINE_REPORT}" in walk.state["ended_reason"]
    assert "development-implementation" not in walk.skills_launched


def test_the_audit_fans_out_over_the_content_step_too():
    audit = step("audit")
    assert audit.fans_out_over == ("development-specs", "development-design", "development-plan",
                                   "development-content", "development-implementation")


def test_a_no_text_change_audits_only_the_four_steps_it_ran():
    walk = Walk(through="design")
    for step_id in ("plan", "implementation", "code-integrity"):
        land(walk.files, walk.git, step_id)
        walk.advance(step_id)
    for skill in PRODUCERS:
        land(walk.files, walk.git, "audit", skill)
        walk.advance(f"audit-{skill}")

    assert walk.skills_launched == [
        "development-plan", "development-implementation", "development-code-integrity",
        *["development-audit"] * 4, "tobiishi-seal"]
    assert walk.state["ended"] is None


def test_a_text_change_audits_its_text_as_a_fifth_run():
    walk = _advanced_past_plan(TEXT_DESIGN)
    for step_id in ("content", "implementation", "code-integrity"):
        land(walk.files, walk.git, step_id)
        walk.advance(step_id)
    audited = [args[-1] for args in walk.processes.launched if args[1] == "development-audit"]

    assert audited == ["development-specs", "development-design", "development-plan",
                       "development-content", "development-implementation"]
    assert not cd.DiskReader(files=walk.files, git=walk.git).is_done(layout(), step("audit"))
    for skill in audited:
        land(walk.files, walk.git, "audit", skill)
        walk.advance(f"audit-{skill}")

    assert walk.skills_launched[-1] == "tobiishi-seal"
    assert walk.state["ended"] is None


def test_describe_refuses_a_file_without_the_content_entry(tmp_path, capsys):
    _copy_of_the_file(tmp_path, {"steps.content": None})
    instance = _instance_with_one_change(tmp_path)

    code = cd.main(["--describe", str(tmp_path / "state.json"), "--instance-root", str(instance),
                    "--project", PROJECT])

    assert code == 3
    assert "steps.content is missing" in capsys.readouterr().err


# --- the product checkout: a run that leaves it dirtier halts the walk at its own step ----------


DIRTY = ["?? stray.txt", " M kept.md"]


def _recorded_nothing(walk: "Walk", run: str) -> None:
    """The walk's saved state as one written before the check existed: `run`'s pending entry holds
    no reading of the checkout."""
    state = walk.state
    del state["pending"][run]["checkout_before"]
    walk.files.write_text(STATE, json.dumps(state))


def test_a_launch_records_the_product_checkout_on_its_pending_run():
    checkout = FakeCheckout(["?? already.txt"])

    walk = Walk(checkout=checkout)

    assert walk.state["pending"]["specs"]["checkout_before"] == ["?? already.txt"]
    assert checkout.read == [PRODUCT]


def test_a_step_that_leaves_the_product_checkout_dirtier_halts_naming_the_step():
    walk = Walk(checkout=FakeCheckout([], DIRTY))
    land(walk.files, walk.git, "specs")

    walk.advance("specs")

    assert walk.state["ended"] == "halted"
    assert walk.state["ended_reason"] == (
        "stopped at specs: " + product_checkout.left_dirty([], DIRTY, PRODUCT))
    assert "`?? stray.txt`" in walk.notifier.messages[-1]
    assert len(walk.processes.launched) == 1


def test_a_dirty_failed_developer_run_is_not_resumed():
    walk = Walk(through="plan", checkout=FakeCheckout([], DIRTY))
    walk.git.commits[KEY] = list(TASK_COMMITS)

    walk.advance("implementation", "failed")

    assert walk.state["ended"] == "halted"
    assert walk.state["failure_resumes"] == 0
    assert len(walk.processes.launched) == 1


def test_a_dirty_paused_developer_run_is_not_relaunched():
    walk = Walk(through="plan", checkout=FakeCheckout([], DIRTY))
    walk.git.commits[KEY] = [_pause(3), *TASK_COMMITS]

    walk.advance("implementation")

    assert walk.state["ended"] == "halted"
    assert walk.state["paused_after"] is None
    assert len(walk.processes.launched) == 1


def test_a_dirty_bare_developer_run_gets_no_missing_marker_recovery():
    walk = Walk(through="plan", checkout=FakeCheckout([], DIRTY))
    walk.files.write_text(f"{BRANCH_CHANGE}/tl_instruction.md", _instruction(1, 2, 3, 4))
    walk.git.repos[PRODUCT] = {KEY: [_task(3, "green"), _task(2, "deferred"), _task(1, "green")]}

    walk.advance("implementation")

    assert walk.state["ended"] == "halted"
    assert walk.state["marker_recoveries"] == 0
    assert len(walk.processes.launched) == 1


def test_an_audit_run_that_leaves_the_product_checkout_dirtier_halts_the_walk():
    walk = Walk(through="code-integrity", checkout=FakeCheckout([], [], [], [], DIRTY))

    walk.advance(f"audit-{PRODUCERS[0]}")

    assert walk.state["ended"] == "halted"
    assert walk.state["ended_reason"].startswith("stopped at audit: ")
    assert "`?? stray.txt`" in walk.state["ended_reason"]
    later = walk.advance(f"audit-{PRODUCERS[1]}")
    assert later.acted is False
    assert walk.state["reentries"] == 1


def test_an_empty_product_path_reads_the_instance_checkout():
    checkout = FakeCheckout()

    Walk(product_path="", checkout=checkout)

    assert checkout.read == [INSTANCE]


def test_a_step_that_leaves_the_product_checkout_as_found_walks_on():
    walk = Walk(checkout=FakeCheckout(["?? already.txt"], ["?? already.txt"]))
    land(walk.files, walk.git, "specs")

    walk.advance("specs")

    assert walk.state["ended"] is None
    assert walk.processes.launched[-1] == [SKILL_LAUNCHER, "development-design", PROJECT, KEY]


def test_a_pending_run_with_no_recorded_checkout_is_not_checked():
    walk = Walk(checkout=FakeCheckout([], DIRTY))
    _recorded_nothing(walk, "specs")
    land(walk.files, walk.git, "specs")

    walk.advance("specs")

    assert walk.state["ended"] is None
    assert walk.processes.launched[-1][1] == "development-design"


def test_an_unreadable_checkout_at_launch_records_nothing_and_checks_nothing():
    walk = Walk(checkout=FakeCheckout(None, DIRTY))
    assert "checkout_before" not in walk.state["pending"]["specs"]
    land(walk.files, walk.git, "specs")

    walk.advance("specs")

    assert walk.state["ended"] is None


def test_a_checkout_unreadable_after_the_run_halts_the_walk():
    walk = Walk(checkout=FakeCheckout([], None))
    land(walk.files, walk.git, "specs")

    walk.advance("specs")

    assert walk.state["ended"] == "halted"
    assert f"the product checkout {PRODUCT} could not be read" in walk.state["ended_reason"]


def test_build_chain_wires_a_real_checkout(tmp_path):
    engine = cd.build_chain(str(tmp_path / "state.json"), notifier_command="",
                            engine_path="/pinned/chain_development.py")

    assert isinstance(engine.checkout, product_checkout.Checkout)


# --- added by the code-integrity review ----------------------------------------------------


def test_a_dirty_run_halts_with_the_dirt_whatever_its_outcome():
    """tl_instruction.md, TL Review Notes: a dirty checkout halts with the dirt as its reason,
    never the outcome's — a `failed` end included."""
    walk = Walk(checkout=FakeCheckout([], DIRTY))

    walk.advance("specs", "failed")

    assert walk.state["ended_reason"] == (
        "stopped at specs: " + product_checkout.left_dirty([], DIRTY, PRODUCT))


def test_a_relaunch_takes_its_own_reading_of_the_product_checkout():
    """tl_instruction.md, task 3: every launch and relaunch takes its own reading (CP-508), so a
    relaunched run is compared with the checkout it found, not the one the first launch found."""
    walk = Walk(through="plan", checkout=FakeCheckout([], [], ["?? between.txt"]))
    walk.git.commits[KEY] = [_pause(3), *TASK_COMMITS]

    walk.advance("implementation")

    assert walk.processes.launched[-1] == [SKILL_LAUNCHER, "development-implementation",
                                           PROJECT, KEY, "3"]
    assert walk.state["pending"]["implementation"]["checkout_before"] == ["?? between.txt"]


# --- the environment a record names (CP-628) --------------------------------------------


_ENV_HEAD = "Suite: green\n\nLanguage resolution:\n- python — declared in project.md\n"
_REAL_ENVIRONMENTS = [
    "Environment: macos-guest — swift-guest",
    "Environment: container — python:3.12, arm64",
    "Environment: owners-mac — no CI",
    "Environment: owners-mac — owner's ask",
]
_NOT_ENVIRONMENTS = [
    "",
    "Environment:",
    "Environment: vm — somewhere",
    "Environment: Container — python:3.12, arm64",
    "Environment: OWNERS-MAC — no CI",
    "Environment: unresolved — the runner cannot be read from the product's CI configuration",
    "Environment: none — no suite",  # `none` passes only beside a card on main reading `none`
]
_NO_COMMAND_CARD = "# Project Context — tracker\n\n**Test command:** none\n"


def _marker_walk(body: str, *, card: str | None = None, branch_card: str | None = None) -> Walk:
    walk = _walk_with_marker(body)
    if card is not None:
        walk.files.write_text(CARD, card)
    if branch_card is not None:
        walk.files.write_text(BRANCH_CARD, branch_card)
    walk.advance("implementation")
    return walk


def _report_walk(report: str, *, card: str | None = None, marker: str = MARKER_BODY) -> Walk:
    walk = Walk(through="implementation")
    walk.git.bodies[MARKER[0]] = marker
    land(walk.files, walk.git, "code-integrity")
    walk.files.write_text(f"{BRANCH_CHANGE}/code-integrity-report.md", report)
    if card is not None:
        walk.files.write_text(CARD, card)
    walk.advance("code-integrity")
    return walk


def _reason(walk: Walk) -> str:
    return walk.state["ended_reason"] or ""


def _went_on(walk: Walk) -> bool:
    return walk.state["ended"] is None


MISSING_ENVIRONMENT = "missing-environment"


@pytest.mark.parametrize("environment", _NOT_ENVIRONMENTS)
def test_marker_requires_a_real_environment_kind(environment):
    walk = _marker_walk(_ENV_HEAD + environment + "\n")

    assert f"stopped at implementation: {MISSING_ENVIRONMENT}" in _reason(walk)


@pytest.mark.parametrize("environment", _NOT_ENVIRONMENTS)
def test_report_requires_a_real_environment_kind(environment):
    walk = _report_walk("Integrity: pass\n" + environment + "\n")

    assert f"stopped at code-integrity: {MISSING_ENVIRONMENT}" in _reason(walk)


@pytest.mark.parametrize("environment", _REAL_ENVIRONMENTS)
def test_each_real_environment_kind_passes_without_a_fresh_resolution(environment):
    assert _went_on(_marker_walk(_ENV_HEAD + environment + "\n"))
    assert _went_on(_report_walk("Integrity: pass\n" + environment + "\n"))


@pytest.mark.parametrize("line", [
    "**Environment: owners-mac — no CI**",
    "*Environment: owners-mac — no CI*",
    "`Environment: owners-mac — no CI`",
    "__Environment: owners-mac — no CI__",
    "* Environment: owners-mac — no CI",
])
def test_a_dressed_environment_declaration_counts(line):
    assert _went_on(_marker_walk(_ENV_HEAD + line + "\n"))
    assert _went_on(_report_walk("Integrity: pass\n" + line + "\n"))


@pytest.mark.parametrize("line", [
    "The Environment: owners-mac — no CI line is what a record carries.",
    "- Environment: owners-mac — no CI",
    "> Environment: owners-mac — no CI",
    "## Environment: owners-mac — no CI",
    "| Environment: owners-mac — no CI |",
])
def test_a_mention_that_is_not_a_declaration_does_not_declare(line):
    assert MISSING_ENVIRONMENT in _reason(_marker_walk(_ENV_HEAD + line + "\n"))
    assert MISSING_ENVIRONMENT in _reason(_report_walk("Integrity: pass\n" + line + "\n"))


def test_the_first_environment_declaration_wins_over_a_later_one():
    bad_then_good = ("Environment: unresolved — the runner cannot be read\n"
                     "Environment: owners-mac — no CI\n")
    good_then_bad = ("Environment: owners-mac — no CI\n"
                     "Environment: unresolved — the runner cannot be read\n")

    assert MISSING_ENVIRONMENT in _reason(_marker_walk(_ENV_HEAD + bad_then_good))
    assert MISSING_ENVIRONMENT in _reason(_report_walk("Integrity: pass\n" + bad_then_good))
    assert _went_on(_marker_walk(_ENV_HEAD + good_then_bad))
    assert _went_on(_report_walk("Integrity: pass\n" + good_then_bad))


# `none` is a kind only beside the card on main that has no command.


def test_none_environment_passes_beside_a_main_card_with_no_command():
    none = "Environment: none — no suite\n"

    assert _went_on(_marker_walk(_NO_SUITE_MARKER + none, card=_NO_COMMAND_CARD))
    assert _went_on(_report_walk("Integrity: pass\n" + none, card=_NO_COMMAND_CARD,
                                 marker=_NO_SUITE_MARKER + none))


@pytest.mark.parametrize("card", [
    "# Project Context — tracker\n\n**Test command:** pytest tests/\n",
    None,
], ids=["a-command", "no-card"])
def test_none_environment_fails_beside_a_card_with_a_command_or_no_card(card):
    none = "Environment: none — no suite\n"

    assert MISSING_ENVIRONMENT in _reason(_marker_walk(_ENV_HEAD + none, card=card))
    assert MISSING_ENVIRONMENT in _reason(_report_walk("Integrity: pass\n" + none, card=card))


def test_the_card_that_allows_a_none_environment_is_mains_not_the_branchs():
    none = "Environment: none — no suite\n"
    command = "# Project Context — tracker\n\n**Test command:** pytest tests/\n"

    assert MISSING_ENVIRONMENT in _reason(
        _marker_walk(_ENV_HEAD + none, card=command, branch_card=_NO_COMMAND_CARD))
    assert _went_on(_marker_walk(_NO_SUITE_MARKER + none, card=_NO_COMMAND_CARD,
                                 branch_card=command))


# Every halt reason the chain gives today keeps its trigger and its order.


@pytest.mark.parametrize("body, reason", [
    ("Suite: red\n\nLanguage resolution:\n- python\n", "red-suite"),
    ("Language resolution:\n- python\n", "missing-suite"),
    ("Suite: green\n", "missing-language"),
    ("Suite: none\n\nLanguage resolution:\n- python\n", "missing-suite"),
], ids=["red-suite", "missing-suite-line", "missing-language", "none-beside-a-command-card"])
def test_existing_marker_failures_precede_environment(body, reason):
    # Each marker has no environment line, so the reason stays today's own.
    assert f"stopped at implementation: {reason}" in _reason(_marker_walk(body))


def test_a_deferred_red_marker_with_no_environment_reaches_the_new_gate():
    body = ("Suite: red\n\nLanguage resolution:\n- python\n"
            "Deferred: task 1 — the blocked case — docs/record.md § halts\n"
            "Failing: tests/test_parse.py::test_flag — task 1\n")

    assert MISSING_ENVIRONMENT in _reason(_marker_walk(body))


def test_an_unreadable_plan_and_a_missing_red_commit_precede_environment():
    unreadable = _shape_walk(None, [], _ENV_HEAD)
    no_red = _shape_walk(_TDD_ONE, [_task(1)], _ENV_HEAD)

    assert _reason(unreadable) == "stopped at implementation: unreadable-plan"
    assert _reason(no_red) == f"{_MISSING_RED} — task 1"


def test_a_marker_that_passes_every_check_but_names_no_environment_halts_after_commit_shape():
    walk = _shape_walk(_TDD_ONE, [_task(1, "green"), _task(1, "red")], _ENV_HEAD)

    assert _reason(walk) == f"stopped at implementation: {MISSING_ENVIRONMENT}"


@pytest.mark.parametrize("report, reason", [
    ("Integrity: stopped\n", "integrity-stopped"),
    ("Integrity: passed\n", "missing-integrity"),
    ("no verdict here\n", "missing-integrity"),
], ids=["stopped", "not-exactly-pass", "no-line"])
def test_existing_integrity_failures_precede_environment(report, reason):
    assert f"stopped at code-integrity: {reason}" in _reason(_report_walk(report))


def test_only_a_previously_passing_report_reaches_the_environment_refusal():
    assert f"stopped at code-integrity: {MISSING_ENVIRONMENT}" in _reason(
        _report_walk("Integrity: pass\n"))


# The refusal holds on a settle and on a start or describe that enters beyond the step.


def _world_beyond(step_id: str, *, steps: tuple, marker: str | None = None,
                  report: str | None = None) -> tuple[dict, "FakeGit"]:
    disk, git = _entering_at("seal", steps)
    if marker is not None:
        git.bodies[MARKER[0]] = marker
    if report is not None:
        disk[f"{BRANCH_CHANGE}/code-integrity-report.md"] = report
    return disk, git


@pytest.mark.parametrize("steps", [cd.DEVELOPMENT_STEPS, cd.CHANGE_STEPS],
                         ids=["development-table", "change-table"])
@pytest.mark.parametrize("which, reason", [
    ("marker", "stopped at implementation: missing-environment"),
    ("report", "stopped at code-integrity: missing-environment"),
])
def test_missing_environment_refuses_start_and_describe_past_the_step(steps, which, reason):
    marker = _ENV_HEAD if which == "marker" else None
    report = "Integrity: pass\n" if which == "report" else None
    disk, git = _world_beyond("seal", steps=steps, marker=marker, report=report)

    with pytest.raises(cd.ChainRefused, match=reason):
        start(build(FakeFiles(dict(disk)), git=git, steps=steps))
    with pytest.raises(cd.ChainRefused, match=reason):
        describe(build(FakeFiles(dict(disk)), git=git, steps=steps))


def test_a_change_walk_settles_a_missing_environment_in_the_change_table_too():
    walk = _shape_walk(_TDD_ONE, [_task(1, "green"), _task(1, "red")], _ENV_HEAD,
                       steps=cd.CHANGE_STEPS)

    assert _reason(walk) == f"stopped at implementation: {MISSING_ENVIRONMENT}"


def test_the_newest_own_marker_is_the_one_the_environment_is_read_from():
    older = ("z9y8x7", f"developer: {KEY} — implementation complete")
    named = _ENV_HEAD + "Environment: owners-mac — no CI\n"

    files, git = _through("audit")
    git.commits[KEY] = [MARKER, older]
    git.bodies[MARKER[0]], git.bodies[older[0]] = _ENV_HEAD, named
    with pytest.raises(cd.ChainRefused, match=MISSING_ENVIRONMENT):
        start(build(FakeFiles(dict(files)), git=git))

    files, git = _through("audit")
    git.commits[KEY] = [MARKER, older]
    git.bodies[MARKER[0]], git.bodies[older[0]] = named, _ENV_HEAD
    assert describe(build(FakeFiles(dict(files)), git=git)).entry == "seal"


def test_a_re_close_is_not_grandfathered_by_the_marker_it_supersedes():
    superseded = ("z9y8x7", f"developer: {KEY} — implementation complete")
    walk = Walk(through="plan")
    walk.git.commits[KEY] = [MARKER, superseded]
    walk.git.bodies[superseded[0]] = _ENV_HEAD + "Environment: owners-mac — no CI\n"
    walk.git.bodies[MARKER[0]] = _ENV_HEAD

    walk.advance("implementation")

    assert f"stopped at implementation: {MISSING_ENVIRONMENT}" in _reason(walk)


def test_positive_fixture_updates_preserve_existing_assertions():
    # The shared passing fixtures name an environment, so every earlier positive test still
    # reaches the end it asserted; the failing-record fixtures are untouched.
    assert "Environment: " in MARKER_BODY
    assert "Environment: none — no suite" in _NO_SUITE_MARKER
    walk = Walk(through="implementation")
    land(walk.files, walk.git, "code-integrity")
    report = walk.files.files[os.path.normpath(f"{BRANCH_CHANGE}/code-integrity-report.md")]
    assert report.startswith("Integrity: pass\n") and "Environment: " in report


# --- the owner's ask for a Mac run: carried on the walk, set on the three gate consumers only ----


ASK_VARIABLE = "KENSAIAPP_GATE_OWNERS_MAC"
_ASK_CONSUMERS = ("implementation", "code-integrity", "seal")


def _a_walk_state(**overrides) -> "cd.WalkState":
    return cd.WalkState(instance_root=INSTANCE, product_path=PRODUCT, project=PROJECT,
                        core_dir=CORE, shim_dir=LOGS, engine_path=ENGINE, key=KEY,
                        walk_id="walk-1", product_docs=f"{PRODUCT}/docs", **overrides)


def test_explicit_start_ask_round_trips_in_state(tmp_path):
    code, asked = _start_through_main(tmp_path, "--gate-owners-mac")
    assert code == 0
    assert json.loads(asked.read_text())["gate_owners_mac"] is True

    code, unasked = _start_through_main(tmp_path / "other")
    assert code == 0
    assert json.loads(unasked.read_text())["gate_owners_mac"] is False

    assert cd.WalkState.from_json(_a_walk_state(gate_owners_mac=True).to_json()).gate_owners_mac
    older = _a_walk_state().to_json()
    del older["gate_owners_mac"]
    assert cd.WalkState.from_json(older).gate_owners_mac is False


def _ask_in(processes, index: int = -1):
    return processes.calls[index]["env"].get(ASK_VARIABLE)


@pytest.mark.parametrize("steps", [cd.DEVELOPMENT_STEPS, cd.CHANGE_STEPS])
@pytest.mark.parametrize("step_id", [entry.id for entry in cd.CHANGE_STEPS])
def test_only_gate_consumers_receive_stored_ask(steps, step_id):
    if step_id in {"station", "change", "refine"} and steps is cd.DEVELOPMENT_STEPS:
        pytest.skip("not a step of the development table")
    disk, git = _entering_at(step_id, steps)
    asked, unasked, stale = FakeProcesses(), FakeProcesses(), FakeProcesses()

    start(build(FakeFiles(dict(disk)), git=git, processes=asked, steps=steps),
          gate_owners_mac=True)
    start(build(FakeFiles(dict(disk)), git=git, processes=unasked, steps=steps))
    # The engine's own environment is the previous run's: it may hold the ask the walk never made.
    start(build(FakeFiles(dict(disk)), git=git, processes=stale, steps=steps,
                environ={"PATH": "/usr/bin", ASK_VARIABLE: "1"}))

    assert {call["env"].get(ASK_VARIABLE) for call in asked.calls} == (
        {"1"} if step_id in _ASK_CONSUMERS else {None})
    assert {call["env"].get(ASK_VARIABLE) for call in unasked.calls} == {None}
    assert {call["env"].get(ASK_VARIABLE) for call in stale.calls} == {None}


def test_every_audit_run_drops_an_inherited_ask_even_when_the_walk_asked():
    walk = Walk(through="implementation", gate_owners_mac=True)
    land(walk.files, walk.git, "code-integrity")
    inherited = {"PATH": "/usr/bin", ASK_VARIABLE: "1"}
    before = len(walk.processes.calls)

    build(walk.files, git=walk.git, processes=walk.processes, notifier=walk.notifier,
          lock=walk.lock, environ=inherited).advance("code-integrity", "completed")

    audits = walk.processes.calls[before:]
    assert len(audits) == 4
    assert [call["env"].get(ASK_VARIABLE) for call in audits] == [None] * 4


def test_advance_resume_and_recovery_keep_walk_ask():
    ambient = {"PATH": "/usr/bin"}
    walk = Walk(through="plan", gate_owners_mac=True)
    assert _ask_in(walk.processes) == "1"

    # A fresh process over the same state, whose own environment says nothing of the ask.
    walk.git.commits[KEY] = [_pause(3), *TASK_COMMITS]
    build(walk.files, git=walk.git, processes=walk.processes, environ=ambient).advance(
        "implementation", "completed")
    assert walk.processes.launched[-1][-1] == "3"
    assert _ask_in(walk.processes) == "1"

    # A failed run resumed from its last commit.
    walk.git.commits[KEY] = [_pause(3), *TASK_COMMITS]
    build(walk.files, git=walk.git, processes=walk.processes, environ=ambient).advance(
        "implementation", "failed")
    assert _ask_in(walk.processes) == "1"

    # A missing marker recovered once.
    recovery = Walk(through="plan", gate_owners_mac=True)
    recovery.git.commits[KEY] = []
    recovery.files.write_text(f"{BRANCH_CHANGE}/tl_instruction.md", _instruction(1, 2))
    build(recovery.files, git=recovery.git, processes=recovery.processes,
          environ=ambient).advance("implementation", "completed")
    assert recovery.state["marker_recoveries"] == 1
    assert _ask_in(recovery.processes) == "1"

    # An ordinary advance past the developer, into the next consumer.
    landed = Walk(through="plan", gate_owners_mac=True)
    land(landed.files, landed.git, "implementation")
    build(landed.files, git=landed.git, processes=landed.processes, environ=ambient).advance(
        "implementation", "completed")
    assert landed.processes.launched[-1][1] == "development-code-integrity"
    assert _ask_in(landed.processes) == "1"

    # A walk that never asked stays unasked whatever its later environment holds.
    unasked = Walk(through="plan")
    land(unasked.files, unasked.git, "implementation")
    build(unasked.files, git=unasked.git, processes=unasked.processes,
          environ={"PATH": "/usr/bin", ASK_VARIABLE: "1"}).advance("implementation", "completed")
    assert _ask_in(unasked.processes) is None


def test_product_records_and_card_cannot_create_owner_ask():
    disk, git = _through("plan")
    disk[f"{INSTANCE}/system/projects/{PROJECT}/project.md"] = (
        "**Test command:** pytest\n**Gate owners mac:** yes\nKENSAIAPP_GATE_OWNERS_MAC=1\n")
    disk[f"{PRODUCT}/docs/adr.md"] = (
        "Run the gate on the owner's Mac. KENSAIAPP_GATE_OWNERS_MAC=1\n"
    )
    processes = FakeProcesses()

    files = FakeFiles(disk)

    start(build(files, git=git, processes=processes))

    assert _ask_in(processes) is None
    assert saved(files)["gate_owners_mac"] is False


def test_describe_with_ask_remains_read_only(tmp_path, capsys):
    instance = _instance_with_one_change(tmp_path)
    state = instance / "system" / "logs" / "chain-development-state.json"

    code = cd.main(["--describe", str(state), "--instance-root", str(instance),
                    "--project", PROJECT, "--gate-owners-mac"])

    assert code == 0
    assert "key=" in capsys.readouterr().out
    assert not state.exists()


def test_a_start_only_ask_on_an_advance_does_not_replace_the_stored_authority(tmp_path):
    code, state = _start_through_main(tmp_path)
    assert code == 0
    stored = json.loads(state.read_text())
    assert stored["gate_owners_mac"] is False

    cd.main(["--advance", str(state), next(iter(stored["pending"] or {"specs": 0})), "completed",
             "--gate-owners-mac"])

    assert json.loads(state.read_text())["gate_owners_mac"] is False
