"""The language-packet family's audit must actually audit, and its indexes must actually resolve.

WHY THIS EXISTS
    `core/doctrine/engineering/languages/README.md` declares that it owns "the audit that keeps a
    language's router honest against its folder", and states three checks *with their commands*.
    A check stated as prose is a wish; a check stated as a command is a check only if the command
    runs and only if it stays quiet against a tree that is correct. Both halves are load-bearing,
    and the second is the one that rots silently: an audit that reports findings against a
    known-good tree is worse than no audit, because the first reader learns to skip it and every
    reader after inherits that habit.

    These assertions are derived from the implementation plan at
    `docs/proposals/language-packets-v2/ad_hoc_plan.md` — Task 1's "#### Verification gate" and the
    "Trap fences" section above it — never from the file they check. A test read off the artifact
    would ratify whatever the artifact happens to say, which is the one outcome that proves
    nothing.

HOW THE AUDIT COMMANDS ARE TESTED
    Each command is extracted from the § Audit section and run against a synthetic repo root that
    mirrors the real layout: a copy of the registry README with rows appended, beside language
    folders that do or do not match those rows. That gives every check both cases — a correct tree
    it must stay silent on, and a broken tree it must speak up about. Running them only against
    the live tree would test one case, and while the registry is empty it would be the case where
    a command that matches nothing and a command that works are indistinguishable.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PACKET_DIR = "core/doctrine/engineering/languages"
REGISTRY = REPO / PACKET_DIR / "README.md"

# Task 1: "the fixed six-concern set", named in the plan's order.
CONCERN_FILES = (
    "toolchain.md",
    "layout.md",
    "quality_gates.md",
    "conventions.md",
    "errors_logging.md",
    "testing.md",
)

# Trap fence 3: a doctrine file names another doctrine by bare filename, resolvable through
# `core/doctrine/README.md`. A literal path to one is the drift this catches. Shell commands are
# exempt — a command has to name a real path to run.
DOCTRINE_PATH_REF = re.compile(r"`core/doctrine/[a-z_]+/[a-z_]+\.md`")


def _registry_text() -> str:
    return REGISTRY.read_text(encoding="utf-8")


def _audit_section() -> str:
    text = _registry_text()
    assert "## Audit" in text, "the registry README states no § Audit"
    return text.split("## Audit", 1)[1]


def _audit_commands() -> list[str]:
    """The command under each numbered audit item, from a fenced block or an inline span."""
    items = re.split(r"^\d+\.\s", _audit_section(), flags=re.MULTILINE)[1:]
    commands = []
    for item in items:
        fenced = re.findall(r"```[a-z]*\n(.*?)```", item, flags=re.DOTALL)
        if fenced:
            commands.append(fenced[0].strip())
            continue
        spans = re.findall(r"`([^`\n]+)`", item)
        commands.append(max(spans, key=len) if spans else "")
    return commands


def _run(command: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "-c", command], cwd=cwd, capture_output=True, text=True, timeout=30
    )


def _tree(tmp_path: Path, rows: list[tuple[str, str, str]], folders: list[str]) -> Path:
    """A synthetic repo root: the real registry README plus rows, beside real folders."""
    root = tmp_path / "repo"
    packets = root / PACKET_DIR
    packets.mkdir(parents=True)

    text = _registry_text()
    header = "| Language | Folder | File extensions |"
    assert header in text, "the registry table's header is not the three columns Task 1 names"
    separator_end = text.index("\n", text.index(header) + len(header)) + 1
    separator_end = text.index("\n", separator_end) + 1  # past the |---|---|---| row

    # Drop the LIVE registry's data rows before appending this fixture's own. Without this the
    # synthetic repo inherits every real language as a row whose folder was never created here, so
    # check 1 reports each one and the fixture fails for a reason the test is not about. It passed
    # only while the registry was empty: the first two rows landed 2026-08-21 and took two tests red
    # with them, and a third row took a third. A fixture that breaks when its subject grows is
    # measuring the subject, not the check.
    rest = text[separator_end:]
    while rest.startswith("|"):
        rest = rest[rest.index("\n") + 1:]

    added = "".join(f"| {lang} | {folder} | {ext} |\n" for lang, folder, ext in rows)
    (packets / "README.md").write_text(text[:separator_end] + added + rest)

    for folder in folders:
        (packets / folder).mkdir()
        # The real routers carry a two-column table and check 3 reads its Destination column, so a
        # fixture router has to be one too. A bullet list passed only while the check grepped the
        # whole file, which is the defect this shape exists to let the tests see.
        rows_md = "\n".join(f"| {c[:-3]} | `{c}` |" for c in CONCERN_FILES)
        (packets / folder / "README.md").write_text(
            f"| Concern | Destination |\n|---|---|\n{rows_md}\n"
        )
    return root


# --- Task 1: the file exists and carries what its intent says ------------------------------


def test_registry_exists_with_a_frontmatter_version():
    text = _registry_text()
    assert text.startswith("---\n"), "no frontmatter at byte 0"
    assert re.search(r'^version: "\d+\.\d+\.\d+"$', text, flags=re.MULTILINE)


def test_registry_carries_no_status_field():
    """Trap fence 1: nothing this plan lands announces its own state."""
    assert not re.search(r"^\s*\*{0,2}status:", _registry_text(), flags=re.MULTILINE | re.IGNORECASE)


def test_the_six_concerns_are_named_with_what_each_owns_and_must_not_carry():
    text = _registry_text()
    for concern in CONCERN_FILES:
        assert f"`{concern}`" in text, f"concern file {concern} is not named"
    assert "It must not carry" in text, "no column states what a concern must not carry"


def test_the_four_step_resolution_chain_is_in_order():
    section = _registry_text().split("## The resolution chain", 1)[1].split("\n## ", 1)[0]
    steps = [
        section.index("`project.md` `Languages:`"),
        section.index("plan or invocation"),
        section.index("inference from the file extensions"),
        section.index("no packet"),
    ]
    assert steps == sorted(steps), "the chain's four steps are not stated in order"


def test_a_missing_packet_is_explicitly_never_a_stop():
    assert re.search(r"never a \*{0,2}STOP", _registry_text())


def test_precedence_and_the_lifecycle_travel_rule_are_stated():
    text = _registry_text()
    assert "## Precedence" in text
    assert "travel together" in text, "the row-and-folder-travel-together rule is not stated"


def test_the_floor_is_named_by_its_instance_relative_path():
    """Trap fence 3: a doctrine file names the floor by its full `<CORE>` path, never a bare filename."""
    text = _registry_text()
    assert "<CORE>/doctrine/engineering/languages/developer_standards.md" in text
    bare = re.findall(r"(?<![/\w-])developer-standards\.md", text)
    assert not bare, "the floor is named as a bare filename somewhere"


def test_no_doctrine_is_named_by_a_literal_path_outside_a_command():
    """Trap fence 3: a doctrine file names another doctrine by bare filename."""
    prose = _registry_text().split("## Audit", 1)[0]
    assert not DOCTRINE_PATH_REF.findall(prose)


# --- Task 1: the audit, with its commands --------------------------------------------------


def test_the_audit_states_three_checks():
    assert len(_audit_commands()) == 3


@pytest.mark.parametrize("index", [0, 1, 2])
def test_each_audit_command_is_recoverable_as_one_command(index):
    command = _audit_commands()[index]
    assert command, f"audit check {index + 1} carries no command"
    syntax = subprocess.run(
        ["bash", "-n"], input=command.replace("<language>", "python"),
        capture_output=True, text=True,
    )
    assert syntax.returncode == 0, (
        f"audit check {index + 1} does not parse as one command — {syntax.stderr.strip()}. "
        "A markdown code span cannot hold an escaped backtick, so a command containing one is "
        "truncated at the first backtick and cannot be copied out."
    )


def test_check_one_is_silent_when_every_row_has_its_folder(tmp_path):
    root = _tree(tmp_path, rows=[("Python", "python", "`.py`")], folders=["python"])
    result = _run(_audit_commands()[0], root)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "", f"false positives against a correct tree:\n{result.stdout}"


def test_check_one_reports_a_row_whose_folder_is_missing(tmp_path):
    root = _tree(tmp_path, rows=[("Python", "python", "`.py`")], folders=[])
    result = _run(_audit_commands()[0], root)
    assert "python" in result.stdout, "a row with no folder went unreported"


def test_check_one_is_silent_on_an_empty_registry(tmp_path):
    """The state this change lands in: a header row, no data rows, no folders."""
    root = _tree(tmp_path, rows=[], folders=[])
    result = _run(_audit_commands()[0], root)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "", f"false positives against an empty registry:\n{result.stdout}"


def test_check_two_runs_and_is_silent_when_every_folder_has_its_row(tmp_path):
    root = _tree(tmp_path, rows=[("Python", "python", "`.py`")], folders=["python"])
    result = _run(_audit_commands()[1], root)
    assert result.returncode == 0, result.stderr
    assert "unknown primary" not in result.stderr, (
        "audit check 2 uses a GNU-only find primary and does not run on this host"
    )
    assert result.stderr.strip() == "", result.stderr
    assert result.stdout.strip() == "", f"false positives against a correct tree:\n{result.stdout}"


def test_check_two_reports_a_folder_with_no_row(tmp_path):
    root = _tree(tmp_path, rows=[], folders=["python"])
    result = _run(_audit_commands()[1], root)
    assert "python" in result.stdout, "a folder with no registry row went unreported"


def test_check_three_runs_and_is_silent_when_the_router_names_every_file(tmp_path):
    root = _tree(tmp_path, rows=[("Python", "python", "`.py`")], folders=["python"])
    for concern in CONCERN_FILES:
        (root / PACKET_DIR / "python" / concern).write_text("x\n")
    command = _audit_commands()[2].replace("<language>", "python")
    result = _run(command, root)
    assert "unknown primary" not in result.stderr, (
        "audit check 3 uses a GNU-only find primary and does not run on this host"
    )
    assert result.stderr.strip() == "", result.stderr
    assert result.stdout.strip() == "", f"false positives against a correct tree:\n{result.stdout}"


def test_check_three_reports_a_file_the_router_does_not_name(tmp_path):
    """The dangerous one: a file nothing points at, which nothing else ever complains about."""
    root = _tree(tmp_path, rows=[("Python", "python", "`.py`")], folders=["python"])
    (root / PACKET_DIR / "python" / "orphan.md").write_text("x\n")
    command = _audit_commands()[2].replace("<language>", "python")
    result = _run(command, root)
    assert "orphan.md" in result.stdout, "an unreachable packet file went unreported"


def test_check_three_is_not_fooled_by_a_filename_in_the_router_s_prose(tmp_path):
    """The false negative that was live on `python/` until 2026-08-21.

    A concern dropped from the router's table but still named in its prose is exactly the
    silently-unreachable file check 3 exists to catch. While the check grepped the whole router, the
    prose mention counted as a destination and the check stayed silent — measured on the merged
    python packet, whose router mentioned `testing.md` in prose, routed no such file and held none.
    """
    root = _tree(tmp_path, rows=[("Python", "python", "`.py`")], folders=["python"])
    router = root / PACKET_DIR / "python" / "README.md"
    for concern in CONCERN_FILES:
        (root / PACKET_DIR / "python" / concern).write_text("x\n")

    dropped = "errors_logging.md"
    kept = [line for line in router.read_text().splitlines() if f"`{dropped}`" not in line]
    router.write_text(
        "\n".join(kept) + f"\n\nA sentence of prose that merely mentions {dropped}.\n"
    )

    command = _audit_commands()[2].replace("<language>", "python")
    result = _run(command, root)
    assert dropped in result.stdout, (
        "a concern file the router names only in prose is unreachable and went unreported"
    )


# --- Tasks 1-6: the mechanic is reachable from every index and every consumer ---------------


@pytest.mark.parametrize(
    "path,needle",
    [
        ("core/doctrine/task_map.md", "`languages/README.md`"),
        ("core/doctrine/README.md", "`languages/`"),
        ("core/doctrine/setup/kensaiapp_structure.md", "`languages/`"),
        ("core/templates/project_template.md", "**Languages:**"),
        ("skills/developer/.claude/skills/development-implementation/SKILL.md", "<CORE>/doctrine/engineering/languages/README.md"),
        ("skills/senior-engineer/.claude/skills/development-code-integrity/SKILL.md", "<CORE>/doctrine/engineering/languages/README.md"),
        ("core/doctrine/engineering/languages/developer_standards.md", "<CORE>/doctrine/engineering/languages/README.md"),
    ],
)
def test_the_family_is_named_where_its_readers_look(path, needle):
    assert needle in (REPO / path).read_text(encoding="utf-8"), f"{path} does not name the family"


def test_the_task_map_carries_exactly_one_row_for_the_whole_family():
    """One row, never one per language — the registry owns the per-language set."""
    text = (REPO / "core/doctrine/task_map.md").read_text(encoding="utf-8")
    assert text.count("`languages/README.md`") == 1


def test_the_doctrine_index_carries_one_folder_row_not_two():
    text = (REPO / "core/doctrine/README.md").read_text(encoding="utf-8")
    assert len([l for l in text.splitlines() if "languages/" in l]) == 1


def test_the_structure_manifest_lists_the_folder_and_no_packet_file():
    """The doctrine layer is enumerated per subfolder, so no packet file is named."""
    lines = [
        l
        for l in (REPO / "core/doctrine/setup/kensaiapp_structure.md")
        .read_text(encoding="utf-8")
        .splitlines()
        if "languages" in l
    ]
    assert len(lines) == 1
    assert not re.search(r"languages/[a-z_]+\.md", lines[0])


@pytest.mark.parametrize(
    "path",
    [
        "skills/developer/.claude/skills/development-implementation/SKILL.md",
        "skills/senior-engineer/.claude/skills/development-code-integrity/SKILL.md",
        "core/doctrine/engineering/languages/developer_standards.md",
    ],
)
def test_a_skill_names_core_through_the_token_never_a_literal_path(path):
    """Trap fence 3: skills are in the closed <CORE> substitution set."""
    text = (REPO / path).read_text(encoding="utf-8")
    assert "core/doctrine/engineering/languages" not in text.replace(
        "<CORE>/doctrine/engineering/languages", ""
    )


def test_the_project_card_declares_the_field_with_every_fact_the_plan_names():
    line = next(
        l
        for l in (REPO / "core/templates/project_template.md").read_text(encoding="utf-8").splitlines()
        if "**Languages:**" in l
    )
    assert "optional" in line
    assert "comma-separated" in line
    assert "order carries no meaning" in line
    assert "languages/README.md" in line
    assert "core/" not in line, "a stamped template may not carry a literal core/ path"


def test_the_floor_states_the_rule_its_exception_and_where_the_language_half_lives():
    """Task 6: the rule, the one exception named, and the pointer — three things, no more."""
    text = (REPO / "core/doctrine/engineering/languages/developer_standards.md").read_text(encoding="utf-8")
    rule = next(l for l in text.splitlines() if "comment" in l.lower())
    assert "what" in rule
    assert "why" in rule, "the exception clause is missing — the rule condemns its own repo without it"
    assert "commit_builder.py" in rule and "launcher.sh" in rule
    assert "conventions.md" in rule


# --- The mandate: resolving is owed, the packet's absence still is not a STOP (2026-08-21) ---
#
# These derive from the approved plan for station `the-language-step-is-mandatory`, not from the files
# they check. What they pin is the distinction the whole change turns on: a run that RESOLVED and found
# nothing has something to say, a run that NEVER LOOKED has nothing to say, and nothing on disk could
# tell those apart until now. Each assertion below is one half of that — the obligation is stated, and
# the escape hatch that satisfied it by inaction is gone.

IMPLEMENTATION_SKILLS = [
    "skills/developer/.claude/skills/development-implementation/SKILL.md",
]
CONSUMER_SKILLS = IMPLEMENTATION_SKILLS + ["skills/senior-engineer/.claude/skills/development-code-integrity/SKILL.md"]


def _language_rows(path: str) -> list[str]:
    """The Inputs-table rows naming the family — where the optionality markers used to live."""
    return [
        line
        for line in (REPO / path).read_text(encoding="utf-8").splitlines()
        if line.lstrip().startswith("|") and "languages/README.md" in line
    ]


def test_the_doctrine_states_the_obligation_unconditionally():
    """The half that was missing: every prior obligation was conditional on the branch taken, so a run
    that never resolved owed nothing under any of them."""
    text = (REPO / "core/doctrine/engineering/languages/README.md").read_text(encoding="utf-8")
    assert "Resolving the chain is not optional" in text
    assert "must not look the same on disk" in text
    # The retired clause must survive ONLY as a named quotation — `kaizen/skills.md` requires a new rule
    # to name the rule it replaces. Twice would mean it is also still standing as a live rule.
    assert text.count("not to require it") == 1, (
        "the inverted clause appears more than once — one of them is still a live rule"
    )
    assert "This inverts what this section used to say" in text


def test_the_doctrine_ranks_the_packet_above_the_files_own_style():
    text = (REPO / "core/doctrine/engineering/languages/README.md").read_text(encoding="utf-8")
    assert "outranks the surrounding code's own habits" in text


@pytest.mark.parametrize("path", IMPLEMENTATION_SKILLS)
def test_no_language_input_row_is_marked_optional(path):
    """The exact marker the run of 2026-08-21 obeyed. A row may still *mention* the retired rule by
    name — naming what it replaces is required — so this reads the table row only."""
    rows = _language_rows(path)
    assert rows, f"{path} has no Inputs row naming the family"
    for row in rows:
        assert "*(optional)*" not in row, f"{path}: the language row is still marked optional"
        assert "optional context" not in row, f"{path}: the language row is still optional context"


@pytest.mark.parametrize("path", CONSUMER_SKILLS)
def test_the_resolution_sits_inside_the_ordered_workflow(path):
    """Placement is the measured difference: the one skill carrying this inside a numbered step fired,
    and the two carrying it as orientation did not."""
    text = (REPO / path).read_text(encoding="utf-8")
    steps_at = min(
        (text.index(h) for h in ("## Workflow", "## The work, in order") if h in text),
        default=-1,
    )
    assert steps_at >= 0, f"{path} has no ordered-workflow section"
    # "every run, no exceptions" is the workflow step's own wording. A looser needle matches the
    # Inputs row too, which sits upstream and would pass this test against the exact shape it exists
    # to reject.
    needle = "every run, no exceptions"
    mandate_at = text.index(needle) if needle in text else -1
    assert mandate_at > steps_at, (
        f"{path}: the mandate sits upstream of the ordered workflow, which is the shape that did not fire"
    )


@pytest.mark.parametrize("path", IMPLEMENTATION_SKILLS)
def test_the_closing_commit_carries_an_unconditional_language_block(path):
    """Removing the marker alone would not have closed the hole: both Review Notes blocks are
    explicitly omittable, so a compliant run with nothing to report still emitted nothing."""
    text = (REPO / path).read_text(encoding="utf-8")
    assert "Language resolution:" in text, f"{path}: no language block in the closing template"
    line = next(l for l in text.splitlines() if l.startswith("Language resolution:"))
    assert "omit this block" not in line, f"{path}: the language block carries the omittable marker"
    assert "NEVER omitted" in line, f"{path}: the block does not say it is never omitted"


def test_the_integrity_report_records_the_resolution_whatever_it_found():
    text = (REPO / "skills/senior-engineer/.claude/skills/development-code-integrity/SKILL.md").read_text(encoding="utf-8")
    assert "- **The language resolution**" in text, (
        "the report's fixed required list has no language slot, so the note it is told to write "
        "elsewhere has nowhere to land"
    )


@pytest.mark.parametrize("path", CONSUMER_SKILLS)
def test_a_missing_packet_is_still_never_a_stop_in_every_consumer(path):
    """The surviving half. A change that made an absent packet block a run has missed the point."""
    assert "never a\nSTOP" in (REPO / path).read_text(encoding="utf-8").replace(
        "never a STOP", "never a\nSTOP"
    )
