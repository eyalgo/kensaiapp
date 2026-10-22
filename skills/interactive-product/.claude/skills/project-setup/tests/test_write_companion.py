"""write_companion.py renders a round-0 companion in its template's exact shape.

Intent source: project-setup SKILL.md § Write the two companions, and the two companion
templates under core/templates/, which own the shape.
"""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
SCRIPT = HERE.parents[1] / "scripts" / "write_companion.py"
CORE = HERE.parents[6] / "core"
PRD_TEMPLATE = CORE / "templates" / "product-templates" / "prd_open_issues_template.md"
AGARI_TEMPLATE = CORE / "templates" / "project-templates" / "agari_open_issues_template.md"

ANSWERS = [
    {"question": "Who is it for?", "why": "PRD: Target Users", "answer": "Solo founders"},
    {"question": "What problem does it remove?", "why": "PRD: Problem Statement",
     "answer": "Plans scattered across five apps"},
]


def _run(tmp_path, template, answers=ANSWERS, out_name="companion.md"):
    answers_file = tmp_path / "answers.json"
    answers_file.write_text(json.dumps(answers), encoding="utf-8")
    out = tmp_path / "docs" / out_name
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--template", str(template), "--out", str(out),
         "--name", "demo", "--answers", str(answers_file)],
        capture_output=True, text=True)
    return result, out


def _headings(text, prefix):
    return [l for l in text.splitlines() if l.startswith(prefix)]


def test_every_bucket_heading_of_the_template_survives(tmp_path):
    for template in (PRD_TEMPLATE, AGARI_TEMPLATE):
        result, out = _run(tmp_path, template, out_name=template.name)
        assert result.returncode == 0, result.stderr
        assert _headings(out.read_text(), "## ") == _headings(template.read_text(), "## ")


def test_metadata_is_dropped_and_the_title_names_the_project(tmp_path):
    result, out = _run(tmp_path, PRD_TEMPLATE)
    text = out.read_text()
    assert not text.startswith("---")
    assert "template-file metadata" not in text
    assert text.splitlines()[0] == "# PRD open issues — demo"
    assert "Round 0." in text


def test_bucket_one_holds_one_answered_item_per_answer_and_nothing_else(tmp_path):
    result, out = _run(tmp_path, PRD_TEMPLATE)
    text = out.read_text()
    items = _headings(text, "### ")
    assert items == ["### 1.1 Who is it for?", "### 1.2 What problem does it remove?"]
    assert "- **Answer:** Solo founders" in text
    assert "- **Why it matters:** PRD: Problem Statement" in text
    assert "<the owner fills this in>" not in text


def test_slot_labels_come_from_the_template(tmp_path):
    """The Agari's bucket 1 carries two slots, the PRD's three — read, not assumed."""
    _, prd = _run(tmp_path, PRD_TEMPLATE, out_name="prd.md")
    _, agari = _run(tmp_path, AGARI_TEMPLATE, out_name="agari.md")
    assert "Reasoning / what would settle it" in prd.read_text()
    assert "Reasoning / what would settle it" not in agari.read_text()


def test_an_existing_companion_is_never_overwritten(tmp_path):
    out = tmp_path / "docs" / "companion.md"
    out.parent.mkdir(parents=True)
    out.write_text("a round in progress\n")
    result, _ = _run(tmp_path, PRD_TEMPLATE)
    assert result.returncode == 3
    assert out.read_text() == "a round in progress\n"


def test_an_empty_answer_is_refused(tmp_path):
    result, out = _run(tmp_path, PRD_TEMPLATE,
                       answers=[{"question": "Who?", "why": "x", "answer": "  "}])
    assert result.returncode == 2
    assert not out.exists()


def test_an_adopted_suggestion_is_marked_and_the_owners_words_are_not(tmp_path):
    answers = [
        {"question": "Who is it for?", "why": "PRD: Target Users", "answer": "Solo founders",
         "suggested": "accepted"},
        {"question": "What is it not?", "why": "PRD: Out of Scope", "answer": "Not a CRM",
         "suggested": "edited"},
        {"question": "What problem does it remove?", "why": "PRD: Problem Statement",
         "answer": "Plans scattered across five apps"},
    ]
    result, out = _run(tmp_path, AGARI_TEMPLATE, answers=answers)
    assert result.returncode == 0, result.stderr
    text = out.read_text()
    assert ("- **Answer:** Solo founders *(the session's suggestion, accepted by the owner as "
            "shown)*") in text
    assert ("- **Answer:** Not a CRM *(the session's suggestion, edited by the owner)*") in text
    assert "- **Answer:** Plans scattered across five apps\n" in text


def test_the_round_zero_line_no_longer_claims_every_answer_is_the_owners_own(tmp_path):
    _, out = _run(tmp_path, PRD_TEMPLATE)
    text = out.read_text()
    assert "every answer below is the owner's own, given" not in text
    assert ("Every answer below is the owner's own, except any marked as the session's "
            "suggestion") in text


def test_an_unknown_suggested_value_is_refused(tmp_path):
    for value in ("maybe", None, ["accepted"], {"a": 1}):
        result, out = _run(tmp_path, PRD_TEMPLATE,
                           answers=[{"question": "Who?", "why": "x", "answer": "y",
                                     "suggested": value}])
        assert result.returncode == 2, (value, result.stderr)
        assert not out.exists()


def test_a_non_string_field_is_refused_not_crashed(tmp_path):
    for bad in ({"question": "Who?", "why": "x", "answer": 3},
                {"question": None, "why": "x", "answer": "y"}):
        result, out = _run(tmp_path, PRD_TEMPLATE, answers=[bad])
        assert result.returncode == 2, (bad, result.stderr)
        assert not out.exists()
