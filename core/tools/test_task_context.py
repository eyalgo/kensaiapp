"""Contract tests for provider-neutral task and standing-rule context."""

from pathlib import Path

import pytest

import task_context


_MAP = """---
version: "1.0.0"
---

| When you're about to… | Consult | Layer | Fires |
|---|---|---|---|
| Commit anything | `commit_format.md` | governance |  |
| Find a defect while walking — decide where it belongs | `found_while_walking.md` | governance | unprompted |
| Bump a version | `versioning.md` | governance |  |
"""


def _core(tmp_path: Path, content: str = _MAP) -> Path:
    core_root = tmp_path / "core"
    doctrine = core_root / "doctrine"
    doctrine.mkdir(parents=True)
    (doctrine / "task_map.md").write_text(content, encoding="utf-8")
    return core_root


def test_routing_context_is_derived_from_every_map_row(tmp_path):
    context = task_context.routing_context(_core(tmp_path))

    assert task_context.TASK_MAP_SENTINEL in context
    assert "Commit anything → commit_format.md" in context
    assert "Find a defect while walking → found_while_walking.md" in context
    assert "Bump a version → versioning.md" in context
    assert "decide where it belongs" not in context


def test_standing_context_contains_only_unprompted_rows(tmp_path):
    context = task_context.standing_rules_context(_core(tmp_path))

    assert task_context.STANDING_RULES_SENTINEL in context
    assert "found_while_walking.md" in context
    assert "commit_format.md" not in context
    assert "versioning.md" not in context


_REPLY_DOCTRINE = """---
version: "1.0.0"
---

# Talking to the owner

Preamble that is not a rule.

## The rules

1. **The answer comes first.**
2. **Use everyday words.**

## Why

Background that is not a rule.
"""


def _with_reply_doctrine(core_root: Path, content: str = _REPLY_DOCTRINE) -> Path:
    path = core_root / task_context.OWNER_REPLY
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return core_root


def test_owner_reply_rules_are_the_rules_section_alone(tmp_path):
    rules = task_context.owner_reply_rules(_with_reply_doctrine(_core(tmp_path)))

    assert rules == "1. **The answer comes first.**\n2. **Use everyday words.**"


def test_standing_context_carries_the_owner_reply_rules_after_the_standing_rows(tmp_path):
    context = task_context.standing_rules_context(_with_reply_doctrine(_core(tmp_path)))

    assert task_context.OWNER_REPLY_SENTINEL in context
    assert "1. **The answer comes first.**" in context
    assert "Background that is not a rule." not in context
    assert context.index("found_while_walking.md") < context.index(
        task_context.OWNER_REPLY_SENTINEL)


def test_owner_reply_rules_reach_a_codex_launch(tmp_path):
    core_root = _with_reply_doctrine(_core(tmp_path))

    prompt = task_context.codex_bootstrap(core_root, "do the task", "gpt-5.6-terra")

    assert prompt.index("1. **The answer comes first.**") < prompt.index("do the task")


def test_owner_reply_rules_carry_alone_when_no_row_is_standing(tmp_path):
    core_root = _with_reply_doctrine(_core(tmp_path, _MAP.replace("unprompted", "")))

    context = task_context.standing_rules_context(core_root)

    assert task_context.STANDING_RULES_SENTINEL not in context
    assert context.startswith("How to reply to the owner")


def test_owner_reply_rules_reach_a_gemini_launch(tmp_path):
    core_root = _with_reply_doctrine(_core(tmp_path))

    prompt = task_context.gemini_bootstrap(core_root, "do the task", "gemini-3-pro")

    assert prompt.index("1. **The answer comes first.**") < prompt.index("do the task")


@pytest.mark.parametrize("variant", [
    _REPLY_DOCTRINE.replace("## The rules\n", "## The rules  \n"),
    "\ufeff" + _REPLY_DOCTRINE.split("---\n", 2)[2].lstrip(),
    _REPLY_DOCTRINE.replace("\n", "\r\n"),
])
def test_owner_reply_rules_survive_a_trailing_space_a_bom_and_crlf(tmp_path, variant):
    path = _core(tmp_path) / task_context.OWNER_REPLY
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(variant.encode("utf-8"))

    rules = task_context.owner_reply_rules(path.parents[2])

    assert rules.splitlines() == ["1. **The answer comes first.**", "2. **Use everyday words.**"]


@pytest.mark.parametrize("content", [None, "# Talking to the owner\n\nNo rules heading.\n"])
def test_owner_reply_rules_fail_empty(tmp_path, content):
    core_root = _core(tmp_path)
    if content is not None:
        _with_reply_doctrine(core_root, content)

    assert task_context.owner_reply_rules(core_root) == ""
    assert task_context.OWNER_REPLY_SENTINEL not in task_context.standing_rules_context(core_root)


def test_the_real_doctrine_has_a_rules_section():
    core_root = Path(task_context.__file__).resolve().parents[1]

    assert task_context.owner_reply_rules(core_root).startswith("1. **The answer comes first")


def test_missing_map_fails_empty(tmp_path):
    core_root = tmp_path / "core"

    assert task_context.routing_context(core_root) == ""
    assert task_context.standing_rules_context(core_root) == ""


def test_codex_bootstrap_places_context_before_the_task(tmp_path):
    core_root = _core(tmp_path)

    prompt = task_context.codex_bootstrap(core_root, "do the task", "gpt-5.6-terra")

    assert prompt.startswith(f"Kensaiapp core resolution: `<CORE>` = `{core_root}`.")
    assert "Execution surface: Codex." in prompt
    assert '`--co-authored-by "gpt-5.6-terra <noreply@openai.com>"`' in prompt
    assert prompt.index(task_context.TASK_MAP_SENTINEL) < prompt.index("do the task")
    assert prompt.index(task_context.STANDING_RULES_SENTINEL) < prompt.index("do the task")


def test_codex_bootstrap_renders_the_concrete_model_once(tmp_path):
    prompt = task_context.codex_bootstrap(_core(tmp_path), "do the task", "gpt-5.6-terra")

    assert prompt.count("gpt-5.6-terra") == 1
    assert "Execution surface: Codex." in prompt
    assert prompt.count("`--surface Codex`") == 1
    assert "Codex <noreply@openai.com>" not in prompt


def test_codex_bootstrap_without_a_model_gives_the_generic_codex_identity(tmp_path):
    prompt = task_context.codex_bootstrap(_core(tmp_path), "do the task", None)

    # commit_format.md § Filling the model: a Codex run with no assigned model still ran an AI,
    # so it writes the provider identity rather than omitting the line.
    assert "Execution surface: Codex." in prompt
    assert "`--surface Codex`" in prompt
    assert prompt.count('`--co-authored-by "Codex <noreply@openai.com>"`') == 1


def test_codex_bootstrap_preserves_context_order_and_collapsed_whitespace(tmp_path):
    core_root = _core(tmp_path)

    prompt = task_context.codex_bootstrap(core_root, "  do\n the\t task  ", "gpt-5.6-terra")

    assert prompt.index(f"`<CORE>` = `{core_root}`") < prompt.index("Execution surface: Codex.")
    assert prompt.index(task_context.TASK_MAP_SENTINEL) < prompt.index("do the task")
    assert prompt.index(task_context.STANDING_RULES_SENTINEL) < prompt.index("do the task")
    assert "\n" not in prompt
    assert "\t" not in prompt
    assert "  " not in prompt


def test_codex_bootstrap_renders_one_resolved_reasoning_effort_instruction(tmp_path):
    prompt = task_context.codex_bootstrap(
        _core(tmp_path), "do the task", "gpt-5.6-terra", "low"
    )

    assert prompt.count('`--reasoning-effort "low"`') == 1
    assert prompt.count("`--surface Codex`") == 1
    assert prompt.count('`--co-authored-by "gpt-5.6-terra <noreply@openai.com>"`') == 1


def test_codex_bootstrap_omits_reasoning_effort_when_none(tmp_path):
    prompt = task_context.codex_bootstrap(
        _core(tmp_path), "do the task", "gpt-5.6-terra", None
    )

    assert "--reasoning-effort" not in prompt
    assert prompt.count("`--surface Codex`") == 1
    assert prompt.count('`--co-authored-by "gpt-5.6-terra <noreply@openai.com>"`') == 1


def test_codex_bootstrap_keeps_runtime_attribution_before_routing_and_task_text(tmp_path):
    prompt = task_context.codex_bootstrap(
        _core(tmp_path), "  do\n the\t task  ", "gpt-5.6-terra", "high"
    )

    assert prompt.index('`--reasoning-effort "high"`') < prompt.index(task_context.TASK_MAP_SENTINEL)
    assert prompt.index(task_context.STANDING_RULES_SENTINEL) < prompt.index("do the task")
    assert "\n" not in prompt
    assert "\t" not in prompt
    assert "  " not in prompt


def test_codex_bootstrap_accepts_xhigh_as_an_already_resolved_value(tmp_path):
    prompt = task_context.codex_bootstrap(
        _core(tmp_path), "do the task", "gpt-5.6-sol", "xhigh"
    )

    assert prompt.count('`--reasoning-effort "xhigh"`') == 1


def test_gemini_bootstrap_renders_one_resolved_reasoning_effort_instruction(tmp_path):
    prompt = task_context.gemini_bootstrap(
        _core(tmp_path), "do the task", "gemini-3.8-flash-high", "medium"
    )

    assert prompt.count('`--reasoning-effort "medium"`') == 1
    assert prompt.count("`--surface Gemini`") == 1
    assert prompt.count('`--co-authored-by "gemini-3.8-flash-high <noreply@google.com>"`') == 1


def test_gemini_bootstrap_omits_reasoning_effort_when_none(tmp_path):
    core = _core(tmp_path)
    concrete = task_context.gemini_bootstrap(core, "do the task", "gemini-3.8-flash-high", None)
    generic = task_context.gemini_bootstrap(core, "do the task", None, None)

    assert concrete == task_context.gemini_bootstrap(core, "do the task", "gemini-3.8-flash-high")
    assert generic == task_context.gemini_bootstrap(core, "do the task", None)
    assert "--reasoning-effort" not in concrete
    assert "--reasoning-effort" not in generic
    assert concrete.count("`--surface Gemini`") == 1
    assert generic.count("`--surface Gemini`") == 1
    assert concrete.count('`--co-authored-by "gemini-3.8-flash-high <noreply@google.com>"`') == 1
    assert generic.count('`--co-authored-by "Gemini <noreply@google.com>"`') == 1


def test_gemini_bootstrap_keeps_runtime_attribution_before_routing_and_task_text(tmp_path):
    prompt = task_context.gemini_bootstrap(
        _core(tmp_path), "  do\n the\t task  ", "gemini-3.1-pro-high", "high"
    )

    assert prompt.index('`--reasoning-effort "high"`') < prompt.index(
        task_context.TASK_MAP_SENTINEL
    )
    assert prompt.index(task_context.STANDING_RULES_SENTINEL) < prompt.index("do the task")
    assert "\n" not in prompt
    assert "\t" not in prompt
    assert "  " not in prompt


def test_shared_commit_recipe_requires_runtime_provider_identity():
    repo_root = Path(__file__).resolve().parents[2]
    recipe = (
        repo_root / "core" / "doctrine" / "governance" / "commit_via_builder.md"
    ).read_text(encoding="utf-8")

    assert '--surface "<execution surface>"' in recipe
    assert '--co-authored-by "<runtime identity>"' in recipe
    assert '--surface "Claude Code"' not in recipe


def test_shared_commit_recipe_states_both_codex_identities():
    # commit_format.md § Filling the model: the assigned model id, or `Codex` when none was
    # assigned. The recipe states the same two values, and its example call stays a placeholder.
    repo_root = Path(__file__).resolve().parents[2]
    recipe = (
        repo_root / "core" / "doctrine" / "governance" / "commit_via_builder.md"
    ).read_text(encoding="utf-8")

    assert '--co-authored-by "<runtime identity>"' in recipe
    assert "`<assigned model id> <noreply@openai.com>`" in recipe
    assert "names no model\n  receives `Codex <noreply@openai.com>`" in recipe


def test_shared_commit_recipe_states_gemini_identities():
    repo_root = Path(__file__).resolve().parents[2]
    recipe = (
        repo_root / "core" / "doctrine" / "governance" / "commit_via_builder.md"
    ).read_text(encoding="utf-8")

    assert "`<assigned model id> <noreply@google.com>`" in recipe
    assert "names no model\n  receives `Gemini <noreply@google.com>`" in recipe


def test_shared_commit_recipe_names_the_reasoning_effort_flag():
    # Searched inside the section a caller reads for what to pass, not across the file: a mention
    # elsewhere would keep a whole-file search green after the entry itself was deleted.
    repo_root = Path(__file__).resolve().parents[2]
    recipe = (
        repo_root / "core" / "doctrine" / "governance" / "commit_via_builder.md"
    ).read_text(encoding="utf-8")
    heading = "## The variables the caller supplies\n"

    assert heading in recipe
    caller_variables = recipe.partition(heading)[2].partition("\n## ")[0]
    assert "--reasoning-effort" in caller_variables


# --- the Claude bootstrap, and the effort sentence's one owner --------------------------------

_EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")


def _effort_sentence(level):
    """The effort sentence as the change's spec writes it — the test's own copy, never read
    back from the module it checks."""
    return (
        f'Pass `--reasoning-effort "{level}"` to the builder; '
        "the launch already resolved this value."
    )


@pytest.mark.parametrize("level", _EFFORT_LEVELS)
def test_claude_bootstrap_appends_the_sentence_for_each_level(level):
    assert task_context.claude_bootstrap("work", level) == f"work {_effort_sentence(level)}"


def test_claude_bootstrap_with_no_level_returns_the_prompt_unchanged():
    prompt = task_context.claude_bootstrap("work", None)

    assert prompt == "work"
    assert "--reasoning-effort" not in prompt


def test_claude_bootstrap_keeps_the_prompt_byte_for_byte():
    # The Codex and Gemini bootstraps collapse whitespace; this one must not.
    launched = "  do\n\n the\t  task  \n"

    prompt = task_context.claude_bootstrap(launched, "high")

    assert prompt.startswith(launched)
    assert prompt == f"{launched} {_effort_sentence('high')}"
    assert task_context.claude_bootstrap(launched, None) == launched


def test_claude_bootstrap_does_not_special_case_an_empty_prompt():
    assert task_context.claude_bootstrap("", "low") == f" {_effort_sentence('low')}"


@pytest.mark.parametrize("level", (None, "low"))
def test_claude_bootstrap_adds_no_surface_identity_or_routing_context(level):
    prompt = task_context.claude_bootstrap("work", level)

    for absent in (
        "Execution surface:",
        "--surface",
        "--co-authored-by",
        task_context.TASK_MAP_SENTINEL,
        task_context.STANDING_RULES_SENTINEL,
    ):
        assert absent not in prompt


def test_the_sentence_is_the_same_text_in_all_three_bootstraps(tmp_path):
    core_root = _core(tmp_path)
    sentence = _effort_sentence("medium")

    for prompt in (
        task_context.claude_bootstrap("do the task", "medium"),
        task_context.codex_bootstrap(core_root, "do the task", "gpt-5.6-terra", "medium"),
        task_context.gemini_bootstrap(core_root, "do the task", "gemini-3.8-flash-high", "medium"),
    ):
        assert prompt.count(sentence) == 1
        assert prompt.count("--reasoning-effort") == 1


def test_the_sentence_is_written_once_in_the_module():
    # Three bootstraps carrying three equal copies would pass the test above by coincidence;
    # the sentence has one owner only while its wording appears once in the source.
    source = Path(task_context.__file__).read_text(encoding="utf-8")

    assert source.count("the launch already resolved this value") == 1
