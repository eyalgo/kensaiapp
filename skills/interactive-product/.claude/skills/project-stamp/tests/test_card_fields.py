"""The card's Type:, Definition:, Manages:, Source material: and Behave: lines.

The first four are what project-setup passes the stamper. Behave: is the one it passes nothing for:
the stamper copies the template's line unchanged and offers no option for it.

Intent source: core/templates/project_template.md (the fields and their comments) and
project-setup's screen 1, whose answers land here.
"""

from __future__ import annotations

from pathlib import Path


def _card(root) -> str:
    return (Path(root) / "system" / "projects" / "demo" / "project.md").read_text(encoding="utf-8")


def _field(card: str, label: str) -> str:
    for line in card.splitlines():
        if line.startswith(f"**{label}:**"):
            return line.split("**", 2)[2].split("<!--")[0].strip()
    raise AssertionError(f"no {label}: line in the card")


def test_defaults_are_software_managing_nothing_with_no_source(run):
    result = run("demo", "--placement", "internal")
    assert result.returncode == 0, result.stderr
    card = _card(run.root)
    assert _field(card, "Type") == "software"
    assert _field(card, "Definition") == "full"
    assert _field(card, "Manages") == "none"
    assert _field(card, "Source material") == "<blank>"


def test_the_three_flags_land_on_the_card_and_keep_each_comment(run):
    result = run("demo", "--placement", "internal", "--type", "no-code",
                 "--manages", "the public repository kensaiapp/kensaiapp",
                 "--source-material", "notes/brief.md — the owner's brief")
    assert result.returncode == 0, result.stderr
    card = _card(run.root)
    assert _field(card, "Type") == "no-code"
    assert _field(card, "Manages") == "the public repository kensaiapp/kensaiapp"
    assert _field(card, "Source material") == "notes/brief.md — the owner's brief"
    for label in ("Type", "Manages", "Source material"):
        line = next(l for l in card.splitlines() if l.startswith(f"**{label}:**"))
        assert "<!--" in line, f"{label}: lost its comment"


def test_a_stamped_card_carries_the_template_behave_line_after_test_command(run):
    result = run("demo", "--placement", "internal")
    assert result.returncode == 0, result.stderr
    template = (run.core / "templates" / "project_template.md").read_text(encoding="utf-8")
    template_behave = next(
        line for line in template.splitlines() if line.startswith("**Behave:**")
    )
    card_lines = _card(run.root).splitlines()
    test_command_at = next(
        i for i, line in enumerate(card_lines) if line.startswith("**Test command:**")
    )
    assert card_lines[test_command_at + 1] == template_behave


def test_the_scaffolder_offers_no_behave_option(run):
    result = run("--help")
    assert result.returncode == 0, result.stderr
    assert "behave" not in (result.stdout + result.stderr).lower()


def test_an_unknown_type_is_refused(run):
    result = run("demo", "--placement", "internal", "--type", "hardware")
    assert result.returncode == 2
    assert not (Path(run.root) / "system" / "projects" / "demo").exists()


def test_a_no_code_card_names_the_prd_and_finish_line_chain_with_no_flag(run):
    result = run("demo", "--placement", "internal", "--type", "no-code")
    assert result.returncode == 0, result.stderr
    line = next(l for l in _card(run.root).splitlines() if l.startswith("**Definition:**"))
    assert _field(_card(run.root), "Definition") == "prd-and-finish-line"
    assert "<!--" in line, "Definition: lost its comment"


def test_an_explicit_definition_overrides_the_type(run):
    result = run("demo", "--placement", "internal", "--type", "software", "--definition", "none")
    assert result.returncode == 0, result.stderr
    assert _field(_card(run.root), "Definition") == "none"


def test_an_unknown_definition_is_refused(run):
    result = run("demo", "--placement", "internal", "--definition", "partial")
    assert result.returncode == 2
    assert not (Path(run.root) / "system" / "projects" / "demo").exists()
