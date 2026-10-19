"""Tests for `experience_gate.py`'s layer handle — Task 1.

Every test builds its own fixture layer tree under pytest's `tmp_path`. No test in this
file reads, globs, or asserts anything about the `system/experience/` of the repo it runs
from — the live layer is touched exactly once, by hand, outside this suite.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import experience_gate as eg


# --- read_document — the layer handle ---------------------------------------------------


class TestReadDocument:
    def test_named_document_in_a_fixture_layer_is_returned_verbatim(self, tmp_path):
        layer = tmp_path / "system" / "experience"
        layer.mkdir(parents=True)
        (layer / "visual_restrictions.md").write_text("known text\nsecond line\n", encoding="utf-8")

        result = eg.read_document(tmp_path, "visual_restrictions.md")

        assert result.ok
        assert result.text == "known text\nsecond line\n"

    def test_absent_document_is_a_not_readable_outcome_naming_its_absolute_path(self, tmp_path):
        layer = tmp_path / "system" / "experience"
        layer.mkdir(parents=True)

        result = eg.read_document(tmp_path, "voice_restrictions.md")

        assert not result.ok
        expected_path = (layer / "voice_restrictions.md").resolve()
        assert str(expected_path) in result.reason

    def test_absent_layer_directory_is_a_not_readable_outcome_naming_the_directory(self, tmp_path):
        result = eg.read_document(tmp_path, "visual_restrictions.md")

        assert not result.ok
        layer = tmp_path / "system" / "experience"
        assert str(layer) in result.reason
        assert "visual_restrictions.md" not in result.reason

    def test_a_path_that_exists_but_is_not_a_directory_is_a_not_readable_outcome_naming_it(self, tmp_path):
        (tmp_path / "system").mkdir()
        (tmp_path / "system" / "experience").write_text("not a directory", encoding="utf-8")

        result = eg.read_document(tmp_path, "visual_restrictions.md")

        assert not result.ok
        layer = tmp_path / "system" / "experience"
        assert str(layer) in result.reason

    def test_a_document_with_non_utf8_bytes_is_a_not_readable_outcome_naming_it(self, tmp_path):
        layer = tmp_path / "system" / "experience"
        layer.mkdir(parents=True)
        target = layer / "voice_direction.md"
        target.write_bytes(b"\xff\xfe\x00")

        result = eg.read_document(tmp_path, "voice_direction.md")

        assert not result.ok
        assert str(target.resolve()) in result.reason

    def test_the_root_comes_from_the_argument_never_from_the_modules_location(self, tmp_path_factory):
        root_a = tmp_path_factory.mktemp("root_a")
        root_b = tmp_path_factory.mktemp("root_b")
        (root_a / "system" / "experience").mkdir(parents=True)
        (root_a / "system" / "experience" / "voice_direction.md").write_text("A", encoding="utf-8")
        (root_b / "system" / "experience").mkdir(parents=True)
        (root_b / "system" / "experience" / "voice_direction.md").write_text("B", encoding="utf-8")

        result_a = eg.read_document(root_a, "voice_direction.md")
        result_b = eg.read_document(root_b, "voice_direction.md")

        assert result_a.text == "A"
        assert result_b.text == "B"

    def test_a_relative_root_resolves_against_the_process_cwd_and_the_reported_path_is_absolute(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "myroot" / "system" / "experience").mkdir(parents=True)

        result = eg.read_document("myroot", "visual_restrictions.md")

        assert not result.ok
        reported_path = (tmp_path / "myroot" / "system" / "experience" / "visual_restrictions.md").resolve()
        assert str(reported_path) in result.reason

    def test_an_unresolvable_root_is_a_not_readable_outcome_naming_the_root_not_the_layer(
        self, tmp_path
    ):
        missing_root = tmp_path / "no-such-root"

        result = eg.read_document(missing_root, "visual_restrictions.md")

        assert not result.ok
        assert str(missing_root.resolve()) in result.reason
        assert "layer" not in result.reason

    def test_a_root_that_exists_but_is_a_file_is_a_not_readable_outcome_naming_the_root(
        self, tmp_path
    ):
        file_root = tmp_path / "not-a-dir"
        file_root.write_text("x", encoding="utf-8")

        result = eg.read_document(file_root, "visual_restrictions.md")

        assert not result.ok
        assert str(file_root.resolve()) in result.reason
        assert "not a directory" in result.reason
        assert "layer" not in result.reason


# --- check_companions — question (a) -----------------------------------------------------


class TestCheckCompanions:
    def _layer(self, tmp_path):
        layer = tmp_path / "system" / "experience"
        layer.mkdir(parents=True)
        return layer

    def test_a_layer_directory_with_no_companion_passes_and_names_nothing(self, tmp_path):
        self._layer(tmp_path)

        result = eg.check_companions(tmp_path)

        assert result.verdict is eg.Verdict.PASS
        assert result.detail == ()

    def test_one_companion_fails_and_names_that_filename(self, tmp_path):
        layer = self._layer(tmp_path)
        (layer / "voice_direction_open_issues.md").write_text("x", encoding="utf-8")

        result = eg.check_companions(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert result.detail == ("voice_direction_open_issues.md",)

    def test_four_companions_fail_and_names_all_four(self, tmp_path):
        layer = self._layer(tmp_path)
        names = (
            "visual_direction_open_issues.md",
            "visual_restrictions_open_issues.md",
            "voice_direction_open_issues.md",
            "voice_restrictions_open_issues.md",
        )
        for name in names:
            (layer / name).write_text("x", encoding="utf-8")

        result = eg.check_companions(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert set(result.detail) == set(names)
        assert len(result.detail) == 4

    def test_a_subdirectory_is_not_scanned_a_retired_companion_never_turns_the_gate_red(self, tmp_path):
        layer = self._layer(tmp_path)
        trail = layer / "trail/visual"
        trail.mkdir(parents=True)
        (trail / "cycle-1.md").write_text("x", encoding="utf-8")
        (trail / "visual_restrictions_open_issues.md").write_text("x", encoding="utf-8")

        result = eg.check_companions(tmp_path)

        assert result.verdict is eg.Verdict.PASS
        assert result.detail == ()

    def test_the_glob_is_the_literal_pattern_open_issues_with_leading_underscore_required(self, tmp_path):
        layer = self._layer(tmp_path)
        (layer / "open_issues.md").write_text("x", encoding="utf-8")
        (layer / "anything_open_issues.md").write_text("x", encoding="utf-8")

        result = eg.check_companions(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert result.detail == ("anything_open_issues.md",)

    def test_a_directory_whose_name_matches_the_glob_is_not_counted_as_a_companion(self, tmp_path):
        layer = self._layer(tmp_path)
        (layer / "voice_direction_open_issues.md").mkdir()

        result = eg.check_companions(tmp_path)

        assert result.verdict is eg.Verdict.PASS
        assert result.detail == ()

    def test_an_absent_layer_directory_makes_this_question_not_asked_naming_the_directory(self, tmp_path):
        result = eg.check_companions(tmp_path)

        assert result.verdict is eg.Verdict.NOT_ASKED
        layer = tmp_path / "system" / "experience"
        assert str(layer) in result.reason

    def test_a_root_that_does_not_exist_makes_this_question_not_asked_naming_the_root(
        self, tmp_path
    ):
        missing_root = tmp_path / "no-such-root"

        result = eg.check_companions(missing_root)

        assert result.verdict is eg.Verdict.NOT_ASKED
        assert str(missing_root.resolve()) in result.reason
        assert "layer" not in result.reason


# --- parse_contract_rows / parse_entry_slugs — Task 3's pure parsers --------------------


class TestParseContractRows:
    HEADER = "| Slug | Kind | Mediums | Reason |\n|---|---|---|---|\n"

    def test_a_well_formed_table_yields_its_rows_in_document_order_backticks_stripped(self):
        text = self.HEADER + (
            "| `alpha` | `limit` | `visual` | first |\n"
            "| `beta` | `limit` | `voice` | second |\n"
        )

        rows = eg.parse_contract_rows(text)

        assert rows == [
            eg.ContractRow(slug="alpha", kind="limit", mediums=frozenset({"visual"})),
            eg.ContractRow(slug="beta", kind="limit", mediums=frozenset({"voice"})),
        ]

    def test_the_header_row_and_the_separator_row_are_not_rows(self):
        text = self.HEADER

        rows = eg.parse_contract_rows(text)

        assert rows == []

    def test_a_table_with_a_header_and_no_data_rows_yields_an_empty_list(self):
        text = "intro text\n\n" + self.HEADER + "\ntrailing text\n"

        rows = eg.parse_contract_rows(text)

        assert rows == []

    def test_each_admitted_mediums_cell_parses_to_its_set(self):
        text = self.HEADER + (
            "| `a` | `limit` | `visual` | r |\n"
            "| `b` | `limit` | `voice` | r |\n"
            "| `c` | `limit` | `visual + voice` | r |\n"
        )

        rows = eg.parse_contract_rows(text)

        assert [r.mediums for r in rows] == [
            frozenset({"visual"}),
            frozenset({"voice"}),
            frozenset({"visual", "voice"}),
        ]

    def test_an_unrecognised_mediums_token_yields_a_malformed_row_naming_slug_and_cell(self):
        text = self.HEADER + "| `a` | `limit` | `audio` | r |\n"

        rows = eg.parse_contract_rows(text)

        assert len(rows) == 1
        assert isinstance(rows[0], eg.MalformedRow)
        assert rows[0].slug == "a"
        assert "audio" in rows[0].reason

    def test_an_empty_mediums_cell_yields_a_malformed_row(self):
        text = self.HEADER + "| `a` | `limit` |  | r |\n"

        rows = eg.parse_contract_rows(text)

        assert len(rows) == 1
        assert isinstance(rows[0], eg.MalformedRow)
        assert rows[0].slug == "a"

    def test_a_row_with_fewer_than_four_cells_is_a_malformed_row(self):
        text = self.HEADER + "| `a` | `limit` | `visual` |\n"

        rows = eg.parse_contract_rows(text)

        assert len(rows) == 1
        assert isinstance(rows[0], eg.MalformedRow)

    def test_pipe_leading_lines_outside_the_table_are_read_and_reported_if_they_do_not_fit(self):
        text = (
            self.HEADER
            + "| `a` | `limit` | `visual` | r |\n"
            + "\nSome other table elsewhere:\n\n"
            + "| one | two |\n|---|---|\n| x | y |\n"
        )

        rows = eg.parse_contract_rows(text)

        assert eg.ContractRow(slug="a", kind="limit", mediums=frozenset({"visual"})) in rows
        malformed = [r for r in rows if isinstance(r, eg.MalformedRow)]
        assert len(malformed) >= 1


class TestParseContractRowsHeaderNotFound:
    """An unfindable header is a state of its own — distinct from a header found with zero
    rows beneath it, which stays `[]` (a legitimate complete state, per the module's own
    docstring)."""

    def test_a_header_whose_fourth_column_is_not_reason_is_not_found(self):
        text = (
            "| Slug | Kind | Mediums | Why |\n"
            "|---|---|---|---|\n"
            "| `alpha` | `limit` | `visual + voice` | a reason |\n"
        )

        result = eg.parse_contract_rows(text)

        assert isinstance(result, eg.HeaderNotFound)

    def test_a_lowercase_header_is_not_found(self):
        text = "| slug | kind | mediums | reason |\n|---|---|---|---|\n"

        result = eg.parse_contract_rows(text)

        assert isinstance(result, eg.HeaderNotFound)

    def test_a_header_whose_columns_are_reordered_is_not_found(self):
        text = "| Reason | Kind | Mediums | Slug |\n|---|---|---|---|\n"

        result = eg.parse_contract_rows(text)

        assert isinstance(result, eg.HeaderNotFound)

    def test_prose_with_no_pipe_table_at_all_is_not_found(self):
        text = "This document carries no table, just prose about the contract.\n"

        result = eg.parse_contract_rows(text)

        assert isinstance(result, eg.HeaderNotFound)

    def test_the_parser_is_unchanged_where_the_header_is_found_a_good_row_and_a_malformed_row(
        self,
    ):
        text = (
            "| Slug | Kind | Mediums | Reason |\n"
            "|---|---|---|---|\n"
            "| `alpha` | `limit` | `visual` | first |\n"
            "| `beta` | `limit` | `audio` | second |\n"
        )

        rows = eg.parse_contract_rows(text)

        assert rows == [
            eg.ContractRow(slug="alpha", kind="limit", mediums=frozenset({"visual"})),
            eg.MalformedRow(
                raw="| `beta` | `limit` | `audio` | second |",
                reason="unrecognised Mediums cell: 'audio'",
                slug="beta",
            ),
        ]


class TestParseEntrySlugs:
    def test_entry_headings_yield_their_slugs_in_document_order(self):
        text = "### `alpha` — first\n\nbody\n\n### `beta` — second\n"

        slugs = eg.parse_entry_slugs(text)

        assert slugs == ("alpha", "beta")

    def test_a_heading_not_followed_by_a_backtick_is_not_an_entry(self):
        text = "### alpha — no backtick\n"

        slugs = eg.parse_entry_slugs(text)

        assert slugs == ()

    def test_two_and_four_hash_headings_are_not_entries(self):
        text = "## `alpha` — two hash\n#### `beta` — four hash\n"

        slugs = eg.parse_entry_slugs(text)

        assert slugs == ()

    def test_a_document_with_no_entries_yields_an_empty_list(self):
        text = "# Title\n\nNo entries here.\n"

        slugs = eg.parse_entry_slugs(text)

        assert slugs == ()


# --- check_pairing — question (b) --------------------------------------------------------


def _contract_text(rows):
    """rows: iterable of (slug, kind, mediums_literal)."""
    lines = ["| Slug | Kind | Mediums | Reason |", "|---|---|---|---|"]
    for slug, kind, mediums in rows:
        lines.append(f"| `{slug}` | `{kind}` | `{mediums}` | reason |")
    return "\n".join(lines) + "\n"


def _restrictions_text(slugs):
    lines = []
    for slug in slugs:
        lines.append(f"### `{slug}` — title")
        lines.append("")
        lines.append("- **The limit.** x")
        lines.append("")
    return "\n".join(lines) + "\n"


class TestCheckPairing:
    def _write_layer(self, tmp_path, contract=None, visual=None, voice=None):
        layer = tmp_path / "system" / "experience"
        layer.mkdir(parents=True)
        if contract is not None:
            (layer / "visual_voice_contract.md").write_text(contract, encoding="utf-8")
        if visual is not None:
            (layer / "visual_restrictions.md").write_text(visual, encoding="utf-8")
        if voice is not None:
            (layer / "voice_restrictions.md").write_text(voice, encoding="utf-8")
        return layer

    def test_the_live_shape_passes(self, tmp_path):
        contract = _contract_text(
            [("alpha", "limit", "visual + voice"), ("beta", "limit", "visual + voice")]
        )
        self._write_layer(
            tmp_path,
            contract=contract,
            visual=_restrictions_text(["alpha", "beta"]),
            voice=_restrictions_text(["alpha", "beta"]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.PASS
        assert result.detail == ()

    def test_a_single_medium_row_passes_when_stated_only_in_that_mediums_document(self, tmp_path):
        contract = _contract_text([("alpha", "limit", "visual")])
        self._write_layer(
            tmp_path,
            contract=contract,
            visual=_restrictions_text(["alpha"]),
            voice=_restrictions_text([]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.PASS

    def test_an_entry_with_no_row_is_unrowed_entry_naming_the_slug_and_the_document(self, tmp_path):
        self._write_layer(
            tmp_path,
            contract=_contract_text([]),
            visual=_restrictions_text(["orphan"]),
            voice=_restrictions_text([]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert any("unrowed entry" in d and "orphan" in d for d in result.detail)

    def test_a_row_reaching_voice_whose_voice_document_is_silent_is_unmet_reach(self, tmp_path):
        contract = _contract_text([("alpha", "limit", "voice")])
        self._write_layer(
            tmp_path,
            contract=contract,
            visual=_restrictions_text([]),
            voice=_restrictions_text([]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert any("unmet reach" in d and "alpha" in d for d in result.detail)

    def test_a_slug_in_both_documents_whose_row_names_only_visual_is_unclaimed_medium_on_voice(
        self, tmp_path
    ):
        contract = _contract_text([("alpha", "limit", "visual")])
        self._write_layer(
            tmp_path,
            contract=contract,
            visual=_restrictions_text(["alpha"]),
            voice=_restrictions_text(["alpha"]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert any("unclaimed medium" in d and "alpha" in d for d in result.detail)

    def test_both_differences_at_once_are_both_reported(self, tmp_path):
        contract = _contract_text([("alpha", "limit", "visual"), ("beta", "limit", "voice")])
        self._write_layer(
            tmp_path,
            contract=contract,
            visual=_restrictions_text(["alpha"]),
            voice=_restrictions_text(["alpha"]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert any("unclaimed medium" in d for d in result.detail)
        assert any("unmet reach" in d and "beta" in d for d in result.detail)

    def test_a_row_with_kind_direction_is_bad_kind_and_still_checked_for_its_reaches(self, tmp_path):
        contract = _contract_text([("alpha", "direction", "voice")])
        self._write_layer(
            tmp_path,
            contract=contract,
            visual=_restrictions_text([]),
            voice=_restrictions_text([]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert any("bad kind" in d and "alpha" in d for d in result.detail)
        assert any("unmet reach" in d and "alpha" in d for d in result.detail)

    def test_two_rows_with_one_slug_is_duplicate_row(self, tmp_path):
        contract = _contract_text(
            [("alpha", "limit", "visual"), ("alpha", "limit", "visual")]
        )
        self._write_layer(
            tmp_path,
            contract=contract,
            visual=_restrictions_text(["alpha"]),
            voice=_restrictions_text([]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert any("duplicate row" in d and "alpha" in d for d in result.detail)

    def test_two_entries_with_one_slug_in_one_document_is_duplicate_entry(self, tmp_path):
        contract = _contract_text([("alpha", "limit", "visual")])
        self._write_layer(
            tmp_path,
            contract=contract,
            visual=_restrictions_text(["alpha", "alpha"]),
            voice=_restrictions_text([]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert any("duplicate entry" in d and "alpha" in d for d in result.detail)

    def test_an_empty_contract_and_two_empty_restrictions_documents_pass(self, tmp_path):
        self._write_layer(
            tmp_path,
            contract=_contract_text([]),
            visual=_restrictions_text([]),
            voice=_restrictions_text([]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.PASS
        assert result.detail == ()

    def test_an_empty_contract_with_one_stated_entry_is_unrowed_entry_not_a_pass(self, tmp_path):
        self._write_layer(
            tmp_path,
            contract=_contract_text([]),
            visual=_restrictions_text(["lonely"]),
            voice=_restrictions_text([]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.FAIL

    def test_any_of_the_three_documents_absent_makes_this_question_not_asked_naming_which(
        self, tmp_path
    ):
        self._write_layer(
            tmp_path,
            visual=_restrictions_text([]),
            voice=_restrictions_text([]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.NOT_ASKED
        assert "visual_voice_contract.md" in result.reason

    def test_a_document_that_does_not_decode_as_utf8_makes_this_question_not_asked_naming_it(
        self, tmp_path
    ):
        layer = self._write_layer(
            tmp_path,
            contract=_contract_text([]),
            voice=_restrictions_text([]),
        )
        (layer / "visual_restrictions.md").write_bytes(b"\xff\xfe\x00")

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.NOT_ASKED
        assert "visual_restrictions.md" in result.reason

    def test_a_malformed_row_is_reported_as_a_malformed_row_finding(self, tmp_path):
        """Task 4's findings table lists `malformed row` — "whatever Task 3 returned as
        malformed" — as one of question (b)'s named findings."""
        self._write_layer(
            tmp_path,
            contract=_contract_text([("alpha", "limit", "audio")]),
            visual=_restrictions_text([]),
            voice=_restrictions_text([]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert any("malformed row" in d and "alpha" in d for d in result.detail)

    def test_the_seed_fixture_an_unfindable_header_fails_pairing_naming_the_document(
        self, tmp_path
    ):
        contract = (
            "| Slug | Kind | Mediums | Why |\n"
            "|---|---|---|---|\n"
            "| `alpha` | `limit` | `visual + voice` | a reason |\n"
        )
        self._write_layer(
            tmp_path,
            contract=contract,
            visual=_restrictions_text([]),
            voice=_restrictions_text([]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert len(result.detail) == 1
        assert "visual_voice_contract.md" in result.detail[0]
        assert "Slug" in result.detail[0] and "Reason" in result.detail[0]

    def test_the_control_with_reason_as_the_fourth_column_discriminates(self, tmp_path):
        contract = (
            "| Slug | Kind | Mediums | Reason |\n"
            "|---|---|---|---|\n"
            "| `alpha` | `limit` | `visual + voice` | a reason |\n"
        )
        self._write_layer(
            tmp_path,
            contract=contract,
            visual=_restrictions_text([]),
            voice=_restrictions_text([]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert any("unmet reach" in d and "alpha" in d and "visual" in d for d in result.detail)
        assert any("unmet reach" in d and "alpha" in d and "voice" in d for d in result.detail)
        assert not any("header not found" in d for d in result.detail)

    def test_a_contract_with_no_pipe_table_at_all_is_the_same_single_finding(self, tmp_path):
        self._write_layer(
            tmp_path,
            contract="This document carries no table, just prose about the contract.\n",
            visual=_restrictions_text([]),
            voice=_restrictions_text([]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert len(result.detail) == 1
        assert "visual_voice_contract.md" in result.detail[0]

    def test_the_one_finding_stands_alone_even_when_restrictions_state_entries(self, tmp_path):
        contract = "| Slug | Kind | Mediums | Why |\n|---|---|---|---|\n"
        self._write_layer(
            tmp_path,
            contract=contract,
            visual=_restrictions_text(["orphan", "ghost"]),
            voice=_restrictions_text([]),
        )

        result = eg.check_pairing(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert len(result.detail) == 1
        assert not any("unrowed entry" in d for d in result.detail)


# --- check_reaches — question (c) --------------------------------------------------------


class TestCheckReaches:
    def _write_layer(self, tmp_path, visual="clean\n", voice="clean\n"):
        layer = tmp_path / "system" / "experience"
        layer.mkdir(parents=True)
        (layer / "visual_restrictions.md").write_text(visual, encoding="utf-8")
        (layer / "voice_restrictions.md").write_text(voice, encoding="utf-8")
        return layer

    def test_two_clean_documents_pass_and_name_nothing(self, tmp_path):
        self._write_layer(tmp_path)

        result = eg.check_reaches(tmp_path)

        assert result.verdict is eg.Verdict.PASS
        assert result.detail == ()

    def test_one_document_carrying_the_literal_fails_naming_document_and_line_number(self, tmp_path):
        self._write_layer(tmp_path, visual="line one\n<The medium: `visual only`>\nline three\n")

        result = eg.check_reaches(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert any("visual_restrictions.md" in d and ":2" in d for d in result.detail)

    def test_both_documents_carrying_it_fail_naming_both(self, tmp_path):
        self._write_layer(
            tmp_path,
            visual="<The medium: x>\n",
            voice="<The medium: y>\n",
        )

        result = eg.check_reaches(tmp_path)

        assert result.verdict is eg.Verdict.FAIL
        assert any("visual_restrictions.md" in d for d in result.detail)
        assert any("voice_restrictions.md" in d for d in result.detail)

    def test_the_match_is_case_sensitive(self, tmp_path):
        self._write_layer(tmp_path, visual="<the medium: lowercase t>\n")

        result = eg.check_reaches(tmp_path)

        assert result.verdict is eg.Verdict.PASS

    def test_the_match_is_a_fixed_string_not_a_regex(self, tmp_path):
        self._write_layer(
            tmp_path,
            visual="<The medium. no colon>\nThe medium: no angle bracket\n",
        )

        result = eg.check_reaches(tmp_path)

        assert result.verdict is eg.Verdict.PASS

    def test_a_hit_anywhere_in_the_document_counts(self, tmp_path):
        self._write_layer(tmp_path, visual="not in a Reaches bullet at all: <The medium: x>\n")

        result = eg.check_reaches(tmp_path)

        assert result.verdict is eg.Verdict.FAIL

    def test_either_document_absent_makes_this_question_not_asked_naming_it(self, tmp_path):
        layer = tmp_path / "system" / "experience"
        layer.mkdir(parents=True)
        (layer / "visual_restrictions.md").write_text("clean\n", encoding="utf-8")

        result = eg.check_reaches(tmp_path)

        assert result.verdict is eg.Verdict.NOT_ASKED
        assert "voice_restrictions.md" in result.reason

    def test_a_document_that_does_not_decode_as_utf8_makes_this_question_not_asked_naming_it(
        self, tmp_path
    ):
        layer = self._write_layer(tmp_path)
        (layer / "voice_restrictions.md").write_bytes(b"\xff\xfe\x00")

        result = eg.check_reaches(tmp_path)

        assert result.verdict is eg.Verdict.NOT_ASKED
        assert "voice_restrictions.md" in result.reason


# --- main / CLI — Task 6 ------------------------------------------------------------------


def _green_layer(tmp_path):
    """A fixture layer that answers all three questions PASS."""
    layer = tmp_path / "system" / "experience"
    layer.mkdir(parents=True)
    contract = _contract_text([("alpha", "limit", "visual + voice")])
    (layer / "visual_voice_contract.md").write_text(contract, encoding="utf-8")
    (layer / "visual_restrictions.md").write_text(
        "### `alpha` — title\n\n- **The limit.** x\n- **Reaches.** every product visual only\n",
        encoding="utf-8",
    )
    (layer / "voice_restrictions.md").write_text(
        "### `alpha` — title\n\n- **The limit.** x\n- **Reaches.** every product voice only\n",
        encoding="utf-8",
    )
    return layer


class TestMain:
    def test_a_green_fixture_layer_exits_0(self, tmp_path, capsys):
        _green_layer(tmp_path)

        code = eg.main(["--instance-root", str(tmp_path)])

        out = capsys.readouterr().out
        assert code == 0
        assert "GREEN — all three questions passed" in out
        assert out.count(": PASS") == 3

    def test_a_fixture_with_one_open_companion_exits_1(self, tmp_path, capsys):
        layer = _green_layer(tmp_path)
        (layer / "voice_direction_open_issues.md").write_text("x", encoding="utf-8")

        code = eg.main(["--instance-root", str(tmp_path)])

        out = capsys.readouterr().out
        assert code == 1
        assert "(a) companions: FAIL" in out
        assert "voice_direction_open_issues.md" in out
        assert "RED — 1 of 3 questions failed" in out

    def test_a_fixture_failing_two_questions_exits_1_and_says_2_of_3(self, tmp_path, capsys):
        layer = _green_layer(tmp_path)
        (layer / "voice_direction_open_issues.md").write_text("x", encoding="utf-8")
        visual = (layer / "visual_restrictions.md").read_text(encoding="utf-8")
        (layer / "visual_restrictions.md").write_text(visual + "<The medium: x>\n", encoding="utf-8")

        code = eg.main(["--instance-root", str(tmp_path)])

        out = capsys.readouterr().out
        assert code == 1
        assert "RED — 2 of 3 questions failed" in out

    def test_a_fixture_with_no_contract_exits_2_and_names_the_missing_file(self, tmp_path, capsys):
        layer = _green_layer(tmp_path)
        (layer / "visual_voice_contract.md").unlink()

        code = eg.main(["--instance-root", str(tmp_path)])

        out = capsys.readouterr().out
        assert code == 2
        assert "(b) pairing: NOT ASKED" in out
        assert "visual_voice_contract.md" in out
        assert "NOT EVALUATED — 1 of 3 questions could not be asked" in out

    def test_2_dominates_1_open_companion_and_absent_contract_exits_2(self, tmp_path, capsys):
        layer = _green_layer(tmp_path)
        (layer / "voice_direction_open_issues.md").write_text("x", encoding="utf-8")
        (layer / "visual_voice_contract.md").unlink()

        code = eg.main(["--instance-root", str(tmp_path)])

        out = capsys.readouterr().out
        assert code == 2
        assert "(a) companions: FAIL" in out

    def test_an_absent_layer_directory_exits_2_with_all_three_not_asked(self, tmp_path, capsys):
        code = eg.main(["--instance-root", str(tmp_path)])

        out = capsys.readouterr().out
        assert code == 2
        assert out.count("NOT ASKED") == 3
        assert "NOT EVALUATED — 3 of 3 questions could not be asked" in out

    def test_instance_root_is_honoured_from_an_unrelated_cwd(self, tmp_path, monkeypatch, tmp_path_factory):
        _green_layer(tmp_path)
        elsewhere = tmp_path_factory.mktemp("elsewhere")
        monkeypatch.chdir(elsewhere)

        code = eg.main(["--instance-root", str(tmp_path)])

        assert code == 0

    def test_the_default_root_is_the_process_cwd(self, tmp_path, monkeypatch, capsys):
        _green_layer(tmp_path)
        monkeypatch.chdir(tmp_path)

        code = eg.main([])

        assert code == 0

    def test_the_header_line_names_the_layer_directory_absolutely(self, tmp_path, capsys):
        _green_layer(tmp_path)

        eg.main(["--instance-root", str(tmp_path)])

        out = capsys.readouterr().out
        expected = tmp_path / "system" / "experience"
        assert f"experience-gate: {expected}" in out

    def test_an_unfindable_contract_header_exits_1_with_pairing_fail_naming_the_document(
        self, tmp_path, capsys
    ):
        layer = _green_layer(tmp_path)
        (layer / "visual_voice_contract.md").write_text(
            "| Slug | Kind | Mediums | Why |\n"
            "|---|---|---|---|\n"
            "| `alpha` | `limit` | `visual + voice` | a reason |\n",
            encoding="utf-8",
        )

        code = eg.main(["--instance-root", str(tmp_path)])

        out = capsys.readouterr().out
        assert code == 1
        assert "(b) pairing: FAIL" in out
        assert "visual_voice_contract.md" in out

    def test_the_reason_control_exits_1_with_the_unmet_reaches_and_no_header_finding(
        self, tmp_path, capsys
    ):
        """The seed fixture's control arm, end to end: the *identical* layer with the
        fourth column named `Reason` still exits 1 — but with the two `unmet reach`
        findings it produces today and no header finding. Without this arm the exit-1
        assertion above cannot be told apart from an exit 1 raised for some other
        reason."""
        layer = tmp_path / "system" / "experience"
        layer.mkdir(parents=True)
        (layer / "visual_voice_contract.md").write_text(
            "| Slug | Kind | Mediums | Reason |\n"
            "|---|---|---|---|\n"
            "| `alpha` | `limit` | `visual + voice` | a reason |\n",
            encoding="utf-8",
        )
        (layer / "visual_restrictions.md").write_text(_restrictions_text([]), encoding="utf-8")
        (layer / "voice_restrictions.md").write_text(_restrictions_text([]), encoding="utf-8")

        code = eg.main(["--instance-root", str(tmp_path)])

        out = capsys.readouterr().out
        assert code == 1
        assert "(b) pairing: FAIL" in out
        assert "unmet reach: alpha — row reaches visual" in out
        assert "unmet reach: alpha — row reaches voice" in out
        assert "header not found" not in out

    def test_run_as_a_subprocess_exit_codes_are_0_1_2(self, tmp_path):
        import subprocess
        import sys

        module_path = Path(eg.__file__)

        _green_layer(tmp_path)
        result = subprocess.run(
            [sys.executable, str(module_path), "--instance-root", str(tmp_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        (tmp_path / "system" / "experience" / "voice_direction_open_issues.md").write_text(
            "x", encoding="utf-8"
        )
        result = subprocess.run(
            [sys.executable, str(module_path), "--instance-root", str(tmp_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

        empty_root = tmp_path / "empty_root"
        empty_root.mkdir()
        result = subprocess.run(
            [sys.executable, str(module_path), "--instance-root", str(empty_root)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2


def _not_asked_reasons(out):
    """The reason text of every `NOT ASKED` line in a report — the part after the marker.

    An assertion over the whole report cannot prove a reason names anything: the report's
    header line prints the *layer* path on every run whatever the root, and that path
    carries the root as its own prefix. So `str(root) in out` is true even when no reason
    mentions the root at all. Reading the reasons is what makes the assertion real.
    """
    marker = f"{eg.Verdict.NOT_ASKED.value} — "
    return [line.split(marker, 1)[1] for line in out.splitlines() if marker in line]


class TestUnresolvableInstanceRoot:
    """Task 2 — the root itself gets its own words, distinct from an existing root that
    simply holds no `system/experience/`. Both stay three NOT ASKED and exit 2 — only the
    words move."""

    def test_a_root_that_does_not_exist_names_the_root_not_the_layer(self, tmp_path, capsys):
        missing_root = tmp_path / "no-such-root"

        code = eg.main(["--instance-root", str(missing_root)])

        out = capsys.readouterr().out
        assert code == 2
        assert out.count("NOT ASKED") == 3
        expected_root = missing_root.resolve()
        reasons = _not_asked_reasons(out)
        assert len(reasons) == 3
        # Every reason, not merely the output as a whole — all three questions read
        # through the root, so all three must say the root and none may say the layer.
        assert all(str(expected_root) in reason for reason in reasons)
        assert all("does not exist" in reason for reason in reasons)
        assert all("layer" not in reason for reason in reasons)
        assert "layer directory does not exist" not in out

    def test_an_existing_root_with_no_layer_is_unchanged(self, tmp_path, capsys):
        code = eg.main(["--instance-root", str(tmp_path)])

        out = capsys.readouterr().out
        assert code == 2
        assert out.count("NOT ASKED") == 3
        layer = tmp_path / "system" / "experience"
        assert f"layer directory does not exist: {layer}" in out

    def test_the_two_root_states_are_told_apart_from_the_output_alone(self, tmp_path, capsys):
        missing_root = tmp_path / "no-such-root"
        eg.main(["--instance-root", str(missing_root)])
        missing_out = capsys.readouterr().out

        empty_root = tmp_path / "empty-root"
        empty_root.mkdir()
        eg.main(["--instance-root", str(empty_root)])
        empty_out = capsys.readouterr().out

        # A literal difference-by-path alone (the two roots are different paths) would
        # make any two reason lines "differ" without the fix actually distinguishing
        # them — so this asserts the *wording* differs, not merely the path.
        assert "layer directory does not exist" not in missing_out
        assert "layer directory does not exist" in empty_out

    def test_a_root_that_exists_but_is_a_file_names_the_root_as_not_a_directory(
        self, tmp_path, capsys
    ):
        file_root = tmp_path / "not-a-dir"
        file_root.write_text("x", encoding="utf-8")

        code = eg.main(["--instance-root", str(file_root)])

        out = capsys.readouterr().out
        assert code == 2
        assert "instance root is not a directory" in out
        assert str(file_root.resolve()) in out

    def test_the_layer_path_is_not_a_directory_case_is_untouched(self, tmp_path, capsys):
        (tmp_path / "system").mkdir()
        (tmp_path / "system" / "experience").write_text("x", encoding="utf-8")

        code = eg.main(["--instance-root", str(tmp_path)])

        out = capsys.readouterr().out
        assert code == 2
        layer = tmp_path / "system" / "experience"
        assert f"layer path is not a directory: {layer}" in out

    def test_a_relative_root_that_does_not_exist_names_the_absolute_root(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)

        code = eg.main(["--instance-root", "no-such-root"])

        out = capsys.readouterr().out
        assert code == 2
        expected = (tmp_path / "no-such-root").resolve()
        reasons = _not_asked_reasons(out)
        assert len(reasons) == 3
        # The absolute path must be in the *reason*, not merely in the report's header
        # line — which prints it as the layer path's prefix on every run, fix or no fix.
        assert all(str(expected) in reason for reason in reasons)
        assert all("layer" not in reason for reason in reasons)


# --- the exit-code contract's literal surface --------------------------------------------
#
# The plan's § *The exit-code contract* calls these literals "the machine-readable surface
# seed 5 may read, and the tests assert them verbatim". Everything below is asserted against
# that section's own printed block, never against what the module happens to emit.


class TestOutputShape:
    def test_the_whole_report_is_the_documented_literal_block(self, tmp_path, capsys):
        layer = _green_layer(tmp_path)
        for name in (
            "visual_direction_open_issues.md",
            "visual_restrictions_open_issues.md",
            "voice_direction_open_issues.md",
            "voice_restrictions_open_issues.md",
        ):
            (layer / name).write_text("x", encoding="utf-8")

        code = eg.main(["--instance-root", str(tmp_path)])

        assert code == 1
        assert capsys.readouterr().out == (
            f"experience-gate: {layer}\n"
            "(a) companions: FAIL — 4 open companion(s)\n"
            "    visual_direction_open_issues.md\n"
            "    visual_restrictions_open_issues.md\n"
            "    voice_direction_open_issues.md\n"
            "    voice_restrictions_open_issues.md\n"
            "(b) pairing: PASS\n"
            "(c) reaches: PASS\n"
            "RED — 1 of 3 questions failed\n"
        )

    def test_the_header_is_first_the_verdict_is_last_and_each_question_is_one_line(
        self, tmp_path, capsys
    ):
        _green_layer(tmp_path)

        eg.main(["--instance-root", str(tmp_path)])

        lines = capsys.readouterr().out.splitlines()
        assert lines[0].startswith("experience-gate: ")
        assert lines[1] == "(a) companions: PASS"
        assert lines[2] == "(b) pairing: PASS"
        assert lines[3] == "(c) reaches: PASS"
        assert lines[4] == "GREEN — all three questions passed"
        assert len(lines) == 5

    def test_a_pairing_failure_names_its_findings_indented_exactly_four_spaces(
        self, tmp_path, capsys
    ):
        layer = _green_layer(tmp_path)
        (layer / "voice_restrictions.md").write_text("no entries here\n", encoding="utf-8")

        code = eg.main(["--instance-root", str(tmp_path)])

        lines = capsys.readouterr().out.splitlines()
        assert code == 1
        pairing = [line for line in lines if line.startswith("(b) pairing: ")]
        assert len(pairing) == 1
        assert pairing[0].startswith("(b) pairing: FAIL — ")
        detail = [line for line in lines if line.startswith(" ")]
        assert detail
        for line in detail:
            assert line.startswith("    ") and line[4] != " "
        assert (
            "    unmet reach: alpha — row reaches voice, voice_restrictions.md does not state it"
            in detail
        )

    def test_2_dominates_1_and_all_three_question_lines_are_still_printed(self, tmp_path, capsys):
        layer = _green_layer(tmp_path)
        (layer / "voice_direction_open_issues.md").write_text("x", encoding="utf-8")
        (layer / "visual_voice_contract.md").unlink()

        code = eg.main(["--instance-root", str(tmp_path)])

        lines = capsys.readouterr().out.splitlines()
        assert code == 2
        assert any(line.startswith("(a) companions: FAIL — ") for line in lines)
        assert any(line.startswith("(b) pairing: NOT ASKED — ") for line in lines)
        assert "(c) reaches: PASS" in lines
        assert lines[-1] == "NOT EVALUATED — 1 of 3 questions could not be asked"


class TestOneStreamIsOneContract:
    """The plan: everything the caller reads goes to stdout, nothing to stderr."""

    def _run(self, tmp_path, root):
        import subprocess
        import sys

        return subprocess.run(
            [sys.executable, str(Path(eg.__file__)), "--instance-root", str(root)],
            capture_output=True,
            text=True,
        )

    def test_nothing_reaches_stderr_on_any_of_the_three_codes(self, tmp_path):
        layer = _green_layer(tmp_path)

        green = self._run(tmp_path, tmp_path)
        assert green.returncode == 0
        assert green.stderr == ""
        assert green.stdout.endswith("GREEN — all three questions passed\n")

        (layer / "voice_direction_open_issues.md").write_text("x", encoding="utf-8")
        red = self._run(tmp_path, tmp_path)
        assert red.returncode == 1
        assert red.stderr == ""

        (layer / "visual_voice_contract.md").unlink()
        not_evaluated = self._run(tmp_path, tmp_path)
        assert not_evaluated.returncode == 2
        assert not_evaluated.stderr == ""


class TestTheOneArgument:
    def test_there_is_no_positional_argument(self, tmp_path):
        """Task 6 states one argument, --instance-root PATH, and no positional."""
        with pytest.raises(SystemExit) as excinfo:
            eg.main([str(tmp_path)])

        assert excinfo.value.code == 2


def test_the_module_carries_a_well_formed_version_marker():
    """`versioning.md` § Where the test lands — a Python script's marker is `__version__ = "x.y.z"`. The real
    job here is that the module carries one and that it is well formed, not pinning a
    literal that a bump on `main` (never on this branch — `versioning.md` § Bump semantics) would
    turn red. True at 1.0.0, true at 1.1.0, true at every bump after."""
    parts = eg.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


class TestTheDirectionDocumentsAreNeverOpened:
    """The plan states it twice: a value in `visual_direction.md` or `voice_direction.md`
    carries no slug and no reach, gets no row, and "the tool never opens either direction
    document". A direction document that would break every other question if it were read
    must therefore change nothing.
    """

    def test_unreadable_direction_documents_carrying_slugs_change_no_answer(
        self, tmp_path, capsys
    ):
        layer = _green_layer(tmp_path)
        (layer / "visual_direction.md").write_bytes(b"\xff\xfe\x00")
        (layer / "voice_direction.md").write_text(
            "### `ghost` — a direction value that is not an entry\n<The medium: unfilled>\n",
            encoding="utf-8",
        )

        code = eg.main(["--instance-root", str(tmp_path)])

        out = capsys.readouterr().out
        assert code == 0
        assert "GREEN — all three questions passed" in out
        assert "ghost" not in out
