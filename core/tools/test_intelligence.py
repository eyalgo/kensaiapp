"""Tests for `intelligence.py` — the reader of `<skill dir>/intelligence/<provider>.md`, the one
place a chain run's model and effort are declared (CP-169, CP-170).

Task 2 covers the reader and its command line. Tasks 8 and 9 each append their own section
below: the shipped files and the set they belong to, and the agent files that no longer carry
a model.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import agent_run
import build_idea
import chain
import chain_development
import intelligence
import providers
import skill_path
from test_providers import EXAMPLE_FILE

_SCRIPT = Path(__file__).resolve().parent / "intelligence.py"
_REPO = Path(__file__).resolve().parents[2]


def _skill_with(tmp_path: Path, provider: str, text: str) -> Path:
    """A skill directory whose `intelligence/<provider>.md` holds `text`."""
    skill_dir = tmp_path / "some-skill"
    (skill_dir / "intelligence").mkdir(parents=True)
    (skill_dir / "intelligence" / f"{provider}.md").write_text(text)
    return skill_dir


# --- read ------------------------------------------------------------------------------------


def test_reads_the_model_and_the_effort(tmp_path):
    skill_dir = _skill_with(tmp_path, "claude", "**Model:** claude-opus-5-5\n**Effort:** high\n")

    result = intelligence.read(skill_dir, "claude")

    assert result == intelligence.Intelligence(
        model="claude-opus-5-5",
        effort=agent_run.Effort.HIGH,
        path=skill_dir / "intelligence" / "claude.md",
    )


def test_a_trailing_comment_is_stripped_from_a_field(tmp_path):
    skill_dir = _skill_with(
        tmp_path, "claude",
        "**Model:** claude-sonnet-5-5 <!-- the cheap one -->\n**Effort:** low <!-- why -->\n",
    )

    result = intelligence.read(skill_dir, "claude")

    assert result.model == "claude-sonnet-5-5"
    assert result.effort is agent_run.Effort.LOW


@pytest.mark.parametrize("effort_lines", [
    "",
    "**Effort:**\n",
    "**Effort:** <!-- only -->\n",
], ids=["no line", "empty value", "only a comment"])
def test_an_absent_or_empty_effort_reads_as_none(tmp_path, effort_lines):
    skill_dir = _skill_with(tmp_path, "claude", "**Model:** claude-haiku-5\n" + effort_lines)

    assert intelligence.read(skill_dir, "claude").effort is None


def test_only_the_first_line_bearing_a_label_is_read(tmp_path):
    skill_dir = _skill_with(
        tmp_path, "claude",
        "# heading\n"
        "This prose mentions Model: gpt-4 and **Model:** inside a sentence.\n"
        "**Model:** claude-opus-5-5\n"
        "**Effort:** medium\n"
        "## Why\n"
        "**Model:** claude-haiku-5\n"
        "**Effort:** low\n",
    )

    result = intelligence.read(skill_dir, "claude")

    assert result.model == "claude-opus-5-5"
    assert result.effort is agent_run.Effort.MEDIUM


def test_an_absent_folder_reads_as_none(tmp_path):
    skill_dir = tmp_path / "some-skill"
    skill_dir.mkdir()

    assert intelligence.read(skill_dir, "claude") is None


def test_a_folder_without_the_providers_file_raises_missing_naming_the_path(tmp_path):
    skill_dir = _skill_with(tmp_path, "claude", "**Model:** claude-opus-5-5\n")

    with pytest.raises(intelligence.MissingIntelligence) as raised:
        intelligence.read(skill_dir, "codex")

    assert str(skill_dir / "intelligence" / "codex.md") in str(raised.value)
    assert isinstance(raised.value, ValueError)


@pytest.mark.parametrize("text", [
    "**Effort:** high\n",
    "**Model:**\n**Effort:** high\n",
    "**Model:** two words\n",
    "**Model:** claude-opus-5-5\n**Effort:** ultra\n",
    "**Model:** claude-opus-5-5\n**Effort:** Low\n",
], ids=["no model", "empty model", "two words", "effort ultra", "effort Low"])
def test_a_malformed_file_raises_naming_it(tmp_path, text):
    skill_dir = _skill_with(tmp_path, "claude", text)

    with pytest.raises(intelligence.MalformedIntelligence) as raised:
        intelligence.read(skill_dir, "claude")

    assert str(skill_dir / "intelligence" / "claude.md") in str(raised.value)
    assert isinstance(raised.value, ValueError)


@pytest.mark.parametrize("level", ["low", "medium", "high", "xhigh", "max"])
def test_a_claude_file_may_declare_any_of_the_five_efforts(tmp_path, level):
    skill_dir = _skill_with(tmp_path, "claude", f"**Model:** claude-opus-5-5\n**Effort:** {level}\n")

    assert intelligence.read(skill_dir, "claude").effort is agent_run.Effort(level)


@pytest.mark.parametrize("provider", ["codex", "gemini"])
@pytest.mark.parametrize("level", ["xhigh", "max"])
def test_a_codex_or_gemini_file_refuses_a_claude_only_effort(tmp_path, provider, level):
    skill_dir = _skill_with(tmp_path, provider, f"**Model:** some-model\n**Effort:** {level}\n")

    with pytest.raises(intelligence.MalformedIntelligence) as raised:
        intelligence.read(skill_dir, provider)

    assert str(skill_dir / "intelligence" / f"{provider}.md") in str(raised.value)
    assert repr(level) in str(raised.value)


@pytest.mark.parametrize("provider", ["codex", "gemini"])
def test_a_codex_or_gemini_file_still_takes_low_medium_high(tmp_path, provider):
    for level in ("low", "medium", "high"):
        skill_dir = _skill_with(
            tmp_path / level, provider, f"**Model:** some-model\n**Effort:** {level}\n"
        )
        assert intelligence.read(skill_dir, provider).effort is agent_run.Effort(level)


@pytest.mark.parametrize("alias", ["fable", "opus", "sonnet", "haiku", "claude-opus", "claude-"])
def test_a_claude_file_refuses_a_floating_alias_naming_the_file_and_value(tmp_path, alias):
    skill_dir = _skill_with(tmp_path, "claude", f"**Model:** {alias}\n")

    with pytest.raises(intelligence.MalformedIntelligence) as raised:
        intelligence.read(skill_dir, "claude")

    assert str(skill_dir / "intelligence" / "claude.md") in str(raised.value)
    assert repr(alias) in str(raised.value)


@pytest.mark.parametrize("provider", ["codex", "gemini"])
def test_the_alias_rule_is_claudes_alone(tmp_path, provider):
    skill_dir = _skill_with(tmp_path, provider, "**Model:** gpt-5.6-sol\n")

    assert intelligence.read(skill_dir, provider).model == "gpt-5.6-sol"


@pytest.mark.parametrize("provider", ["../x", "a/b", ""], ids=["dotdot", "slash", "empty"])
def test_a_path_shaped_provider_is_refused(tmp_path, provider):
    skill_dir = _skill_with(tmp_path, "claude", "**Model:** claude-opus-5-5\n")
    # Where `intelligence/../x.md` resolves: without the refusal this file would be read.
    (skill_dir / "x.md").write_text("**Model:** outside\n")

    with pytest.raises(ValueError) as raised:
        intelligence.read(skill_dir, provider)

    # A `MissingIntelligence` is a ValueError too — it would mean the name was joined onto a path.
    assert type(raised.value) is ValueError


# --- the command line ------------------------------------------------------------------------


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args], capture_output=True, text=True,
    )


def test_the_cli_prints_model_and_effort_and_exits_0(tmp_path):
    skill_dir = _skill_with(tmp_path, "claude", "**Model:** claude-opus-5-5\n**Effort:** high\n")

    done = _run_cli("--skill-dir", str(skill_dir), "--provider", "claude")

    assert done.returncode == 0
    assert done.stdout.splitlines() == ["model=claude-opus-5-5", "effort=high"]


def test_the_cli_prints_an_empty_effort_when_none_is_declared(tmp_path):
    skill_dir = _skill_with(tmp_path, "claude", "**Model:** claude-haiku-5\n")

    done = _run_cli("--skill-dir", str(skill_dir), "--provider", "claude")

    assert done.returncode == 0
    assert done.stdout.splitlines() == ["model=claude-haiku-5", "effort="]


def test_the_runner_entry_is_gone_from_the_reader_and_its_command_line(tmp_path):
    """The second entry existed only for the runner launcher that has been removed: `read` takes no
    `entry`, the module names none, and `--entry` is a usage error of the argument parser."""
    skill_dir = _skill_with(tmp_path, "claude", "**Model:** claude-opus-5-5\n")

    with pytest.raises(TypeError):
        intelligence.read(skill_dir, "claude", entry="runner")
    assert not hasattr(intelligence, "RUNNER_ENTRY")
    done = _run_cli("--skill-dir", str(skill_dir), "--provider", "claude", "--entry", "runner")
    assert done.returncode == 2
    assert done.stdout == ""
    assert "unrecognized arguments: --entry runner" in done.stderr


def test_the_cli_exits_3_silently_for_an_absent_folder(tmp_path):
    (tmp_path / "bare").mkdir()

    done = _run_cli("--skill-dir", str(tmp_path / "bare"), "--provider", "claude")

    assert done.returncode == 3
    assert done.stdout == ""


def test_the_cli_exits_4_naming_the_missing_path(tmp_path):
    skill_dir = _skill_with(tmp_path, "claude", "**Model:** claude-opus-5-5\n")

    done = _run_cli("--skill-dir", str(skill_dir), "--provider", "codex")

    assert done.returncode == 4
    assert done.stdout == ""
    assert str(skill_dir / "intelligence" / "codex.md") in done.stderr


def test_the_cli_exits_2_naming_a_malformed_file(tmp_path):
    skill_dir = _skill_with(tmp_path, "claude", "**Model:** two words\n")

    done = _run_cli("--skill-dir", str(skill_dir), "--provider", "claude")

    assert done.returncode == 2
    assert done.stdout == ""
    assert str(skill_dir / "intelligence" / "claude.md") in done.stderr


# --- the shipped files (Task 8) --------------------------------------------------------------

_OPUS, _SONNET, _FABLE = "claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5-1"
_HAIKU = "claude-haiku-5-5"
HIGH, MEDIUM, LOW = agent_run.Effort.HIGH, agent_run.Effort.MEDIUM, agent_run.Effort.LOW

# The 28 chain skills that carry `intelligence/claude.md`, with the values CP-171 states —
# written out, never derived. nemawashi-retire departs from CP-171: Haiku, the owner's call of
# 2026-10-16.
_CLAUDE_INTELLIGENCE = {
    "product-prd": (_OPUS, HIGH),
    "project-agari": (_OPUS, HIGH),
    "product-srs": (_OPUS, HIGH),
    "product-uxd": (_OPUS, HIGH),
    "product-design": (_OPUS, HIGH),
    "product-fdr": (_OPUS, HIGH),
    "product-architecture": (_OPUS, HIGH),
    "development-specs": (_OPUS, HIGH),
    "development-design": (_OPUS, HIGH),
    "development-implementation": (_SONNET, MEDIUM),
    "development-code-integrity": (_OPUS, HIGH),
    "development-security": (_FABLE, MEDIUM),
    "shukuba-refine": (_OPUS, MEDIUM),
    "nemawashi-refine": (_OPUS, MEDIUM),
    "product-content": (_SONNET, MEDIUM),
    "development-plan": (_SONNET, MEDIUM),
    "development-content": (_OPUS, HIGH),
    "development-audit": (_SONNET, MEDIUM),
    "tobiishi-open": (_SONNET, MEDIUM),
    "tobiishi-seal": (_SONNET, MEDIUM),
    "shukuba-open": (_SONNET, MEDIUM),
    "nemawashi-pick": (_SONNET, MEDIUM),
    "seeds-from-product-docs": (_SONNET, MEDIUM),
    "stations-from-seed": (_SONNET, MEDIUM),
    "nemawashi-retire": (_HAIKU, LOW),
    "shukuba-retire": (_SONNET, LOW),
    "readme-status": (_SONNET, MEDIUM),
    "product-sdd": (_FABLE, HIGH),
}

# The 29 skills the chains launch: the 28 above, plus the one that carries no folder.
_CHAIN_LAUNCHED = frozenset(_CLAUDE_INTELLIGENCE) | {"companion-self-answer"}

# The skills outside the chains that carry a folder, which `skill_intelligence.md` § *Scope*
# permits where a launcher reads it — written out, never derived.
_OUT_OF_CHAIN_INTELLIGENCE = {
    "kensaiapp-writing-bar": (_OPUS, HIGH),
    "experience-visual": (_OPUS, HIGH),
    "experience-voice": (_SONNET, MEDIUM),
    "first-what-left": (_OPUS, HIGH),
    "ad-hoc-plan": (_OPUS, MEDIUM),
    "dependency-repair": (_HAIKU, MEDIUM),
}


def _skill_dir(name: str) -> Path:
    resolved = skill_path.resolve_skill_dir(_REPO, name).path
    assert resolved is not None, f"{name} resolves to no skill directory under {_REPO}"
    return resolved


def _engine_launched_skills() -> set[str]:
    """What the chain engines launch, read off their own tables — `chain.py`'s document registry,
    `chain_development.py`'s change steps, `build_idea.py`'s `RUN_SKILL` kinds — and the
    `companion-self-answer` step `chain.py` runs between documents."""
    documents = {spec.skill for spec in chain.DOCUMENT_REGISTRY.values()}
    steps = {step.skill for step in chain_development.CHANGE_STEPS}
    kinds = {kind.arguments[0] for kind in build_idea.KINDS.values()
             if kind.disposition is build_idea.Disposition.RUN_SKILL}
    return documents | steps | kinds | {"companion-self-answer"}


def test_the_chain_launched_set_is_the_twenty_nine_skills():
    derived = _engine_launched_skills()

    assert len(_CHAIN_LAUNCHED) == 29
    assert "readme-status" in derived
    assert derived == _CHAIN_LAUNCHED


def test_the_expected_claude_intelligence_map_includes_readme_status():
    assert _CLAUDE_INTELLIGENCE["readme-status"] == (_SONNET, MEDIUM)
    assert len(_CLAUDE_INTELLIGENCE) == 28


@pytest.mark.parametrize("provider", ["claude", "codex", "gemini", "ollama"])
def test_each_readme_status_intelligence_file_is_read_by_the_real_reader_without_error(provider):
    found = intelligence.read(_skill_dir("readme-status"), provider)

    assert found is not None and found.model
    assert "## Why" in found.path.read_text()
    assert found.path.name == f"{provider}.md"


def test_first_what_left_is_registered_out_of_chain():
    assert _OUT_OF_CHAIN_INTELLIGENCE["first-what-left"] == (_OPUS, HIGH)
    assert "first-what-left" not in _engine_launched_skills()


@pytest.mark.parametrize("provider", ["claude", "codex", "gemini", "ollama"])
def test_first_what_left_intelligence_reads_for_each_provider(provider):
    namesake = intelligence.read(_skill_dir("project-agari"), provider)

    found = intelligence.read(_skill_dir("first-what-left"), provider)

    assert found is not None and found.model
    assert "## Why" in found.path.read_text()
    assert (found.effort is None) == (provider == "ollama")
    assert (found.effort is None) == (namesake.effort is None)


@pytest.mark.parametrize("provider", ["claude", "codex", "gemini", "ollama"])
def test_no_first_what_left_intelligence_file_credits_its_vendor_with_the_selection(provider):
    # These four files were written by one development run, so none of the vendors chose its own
    # entry, and none of the files may say it did.
    found = intelligence.read(_skill_dir("first-what-left"), provider)

    why = found.path.read_text().split("## Why", 1)[1]

    assert f"selection by {provider}" not in why.lower()


def test_each_chain_skill_carries_its_claude_intelligence():
    read = {}
    for name in _CLAUDE_INTELLIGENCE:
        found = intelligence.read(_skill_dir(name), "claude")
        read[name] = (found.model, found.effort)

    assert read == _CLAUDE_INTELLIGENCE


def test_product_sdd_declares_one_claude_run():
    sdd_dir = _skill_dir("product-sdd")

    run = intelligence.read(sdd_dir, "claude")

    assert (run.model, run.effort) == ("claude-fable-5-1", HIGH)


def test_companion_self_answer_carries_no_intelligence_folder():
    assert not (_skill_dir("companion-self-answer") / "intelligence").exists()


def _every_intelligence_folder() -> list[Path]:
    return sorted(_REPO.glob("skills/*/.claude/skills/*/intelligence")) + sorted(
        _REPO.glob(".claude/skills/*/intelligence")
    )


def test_no_other_skill_carries_an_intelligence_folder():
    owners = {folder.parent.name for folder in _every_intelligence_folder()}

    assert owners == set(_CLAUDE_INTELLIGENCE) | set(_OUT_OF_CHAIN_INTELLIGENCE)


def _a_launcher_reads_its_intelligence(name: str) -> bool:
    """The skill launcher starts a skill that holds a `launcher.md`; otherwise the skill's own
    launcher must resolve through `run_intelligence.py`."""
    if (_skill_dir(name) / "launcher.md").is_file():
        return True
    own = _REPO / "core" / "launchers" / name / "launcher.sh"
    return own.is_file() and "run_intelligence.py" in own.read_text()


def test_a_skill_outside_the_chains_carries_a_folder_only_where_a_launcher_reads_it():
    assert not set(_OUT_OF_CHAIN_INTELLIGENCE) & _engine_launched_skills()

    read = {}
    for name in _OUT_OF_CHAIN_INTELLIGENCE:
        assert _a_launcher_reads_its_intelligence(name), name
        found = intelligence.read(_skill_dir(name), "claude")
        read[name] = (found.model, found.effort)

    assert read == _OUT_OF_CHAIN_INTELLIGENCE


def test_every_intelligence_folder_carries_claude_and_codex():
    """Every folder carries both, and nothing but vendor files: `skill_intelligence.md` § *Where a
    skill declares it* names `claude.md`, and a file per other vendor "when that vendor is given one" —
    so a `gemini.md`, an `hf.md` or an `ollama.md` is a file a folder may hold, and anything else is
    not."""
    for folder in _every_intelligence_folder():
        names = {file.name for file in folder.iterdir()}
        vendor_files = {"claude.md", "codex.md", "gemini.md", "hf.md", "ollama.md"}
        assert {"claude.md", "codex.md"} <= names <= vendor_files, folder


def test_each_chain_skill_carries_readable_codex_intelligence():
    for name in _engine_launched_skills() - {"companion-self-answer"}:
        found = intelligence.read(_skill_dir(name), "codex")

        assert found is not None, name
        assert found.model in {"gpt-6-astra", "gpt-6.1-sol", "gpt-6-luna"}, name
        assert found.effort in {LOW, MEDIUM, HIGH}, name
        assert "## Why" in found.path.read_text(), name


def _entries_naming_a_provider() -> list[tuple[str, str]]:
    """Every (skill, provider) the delivered provider file assigns an unforced launch — one per
    skill-launching member of the three tables `_engine_launched_skills` reads. The owed-item
    entry is left out: it names no skill of its own, only the launcher an owed bullet quotes."""
    delivered = providers.ProviderFile(str(EXAMPLE_FILE), chain.Files())

    def provider_of(member: providers.Member) -> str:
        return delivered.launch_provider("", member)

    documents = [(spec.skill, provider_of(providers.document(name)))
                 for name, spec in chain.DOCUMENT_REGISTRY.items()]
    steps = [(step.skill, provider_of(providers.step(step.id)))
             for step in chain_development.CHANGE_STEPS]
    kinds = [(kind.arguments[0], provider_of(providers.build_idea_row(name)))
             for name, kind in build_idea.KINDS.items()
             if kind.disposition is build_idea.Disposition.RUN_SKILL]
    return documents + steps + kinds


def _without_intelligence(entries: list[tuple[str, str]]) -> list[tuple[str, str]]:
    missing = []
    for skill, provider in entries:
        try:
            intelligence.read(_skill_dir(skill), provider)
        except intelligence.MissingIntelligence:
            missing.append((skill, provider))
    return missing


def test_a_step_assigned_a_provider_has_that_providers_intelligence():
    """A step whose table entry names a provider is refused at launch when the skill has no file
    for it (`skill_intelligence.md` § When it is missing) — so the assignment is checked here,
    where it is made, rather than found by a walk."""
    assert _without_intelligence(_entries_naming_a_provider()) == []


def test_the_check_above_sees_a_provider_a_skill_has_no_file_for():
    """`development-audit` carries no `gemini.md`; the assignment that would need one is caught."""
    assert not (_skill_dir("development-audit") / "intelligence" / "gemini.md").exists()
    assert _without_intelligence([("development-audit", "gemini"),
                                  ("development-audit", "codex")]) == [
        ("development-audit", "gemini")]


def test_product_sdd_declares_one_codex_run():
    sdd_dir = _skill_dir("product-sdd")

    run = intelligence.read(sdd_dir, "codex")

    assert (run.model, run.effort) == ("gpt-6-astra", HIGH)


def test_product_sdd_declares_one_gemini_run():
    sdd_dir = _skill_dir("product-sdd")

    run = intelligence.read(sdd_dir, "gemini")

    assert (run.model, run.effort) == ("gemini-3.1-pro-high", HIGH)


# --- the agent files (Task 9) ----------------------------------------------------------------


def _frontmatter_lines(path: Path) -> list[str]:
    lines = path.read_text().splitlines()
    assert lines and lines[0].strip() == "---", f"{path} has no frontmatter"
    end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    return lines[1:end]


def _grouped_agent_files():
    return sorted((_REPO / "skills").glob("*/.claude/agents/*.md"))


def test_intelligence_reads_groups():
    # The no-`model:`-line clause below is proved over the grouped agents; a glob that finds none
    # would prove it over nothing.
    assert len(_grouped_agent_files()) == 19


def test_no_agent_file_carries_a_model_line():
    agents = _grouped_agent_files()
    assert agents, "no agent files found"

    carrying = [
        agent.name for agent in agents
        if any(line.startswith("model:") for line in _frontmatter_lines(agent))
    ]

    assert carrying == []
