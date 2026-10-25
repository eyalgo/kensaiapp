"""Characterization tests of `record_declarations`: the parser and the table of declared fields.

They pin today's scan as the module states it, and add no behaviour. What each real record reads as
is pinned by `test_record_readings.py` against its snapshot; these pin the parser and the table
themselves, on small bodies.
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

import chain_development
import record_declarations as rd

TOOLS = Path(__file__).resolve().parent


def texts(lines) -> list[str]:
    return [line.text for line in lines]


def test_a_dressed_line_reads_undressed_and_keeps_its_raw_form():
    # Spec I-3: whitespace off, then `*`, `_` and the backtick off both ends, then whitespace off
    # again. The expected text is written out, never computed with the parser's own rule.
    bodies = ["**Integrity: pass**", "`Integrity: pass`", "_Integrity: pass_",
              "    Integrity: pass  ", "  ** Integrity: pass **  "]
    for raw in bodies:
        line = rd.parse(f"# report\n{raw}\n").one(rd.INTEGRITY)
        assert line == rd.Line(raw=raw, text="Integrity: pass")


def test_a_mention_inside_a_line_is_not_a_declaration():
    assert rd.parse("see Environment: x").read(rd.ENVIRONMENT) == ()


def test_an_asterisk_bullet_counts_and_a_dash_or_quote_does_not():
    assert texts(rd.parse("* Environment: a").read(rd.ENVIRONMENT)) == ["Environment: a"]
    assert rd.parse("- Environment: a").read(rd.ENVIRONMENT) == ()
    assert rd.parse("> Environment: a").read(rd.ENVIRONMENT) == ()


def test_a_wrapped_prose_line_opening_with_a_quoted_prefix_is_read():
    # The rule's limit (change_spec.md, Out of Scope): a wrapped line that is the record's first
    # match still starts the run, because the reading is not quote-aware. The producing skills put
    # the block at the top, so no real record has this shape.
    record = rd.parse("`Environment:` lines below")
    assert texts(record.read(rd.ENVIRONMENT)) == ["Environment:` lines below"]


def test_a_wrapped_quoted_prefix_after_the_block_is_not_read():
    # The real report's shape: the verdict, the block of five lines, then prose whose wrapped
    # line opens with a quoted prefix. Only the five are read.
    body = (
        "Integrity: pass\n"
        "Environment: container — a-image, amd64\n"
        "Environment: container — a-image, arm64\n"
        "Environment: container — b-image, amd64\n"
        "Environment: container — b-image, arm64\n"
        "Environment: macos-guest — a-guest\n"
        "\n"
        "The report's head is read by the chain; the\n"
        "`Environment:` lines are the bare lines at the top of this report.\n"
    )
    read = rd.parse(body).read(rd.ENVIRONMENT)
    assert [line.text.split(" — ")[0] for line in read] == [
        "Environment: container", "Environment: container", "Environment: container",
        "Environment: container", "Environment: macos-guest"]


def test_a_first_run_field_reads_its_consecutive_lines():
    record = rd.parse("Environment: a\nEnvironment: b\n")
    assert texts(record.read(rd.ENVIRONMENT)) == ["Environment: a", "Environment: b"]
    record = rd.parse("Failing: a\nFailing: b\n")
    assert texts(record.read(rd.FAILING)) == ["Failing: a", "Failing: b"]


def test_a_blank_line_ends_the_first_run():
    record = rd.parse("Environment: a\n\nEnvironment: b\n")
    assert texts(record.read(rd.ENVIRONMENT)) == ["Environment: a"]
    record = rd.parse("Failing: a\n\nFailing: b\n")
    assert texts(record.read(rd.FAILING)) == ["Failing: a"]


def test_a_prose_line_ends_the_first_run_and_a_later_match_is_not_read():
    record = rd.parse("Environment: a\nsome prose\nEnvironment: b\n")
    assert texts(record.read(rd.ENVIRONMENT)) == ["Environment: a"]
    record = rd.parse("Failing: a\n# A heading\nFailing: b\n")
    assert texts(record.read(rd.FAILING)) == ["Failing: a"]


def test_a_run_starts_at_the_first_matching_line_not_the_first_line():
    record = rd.parse("Suite: red\n\nEnvironment: a\nEnvironment: b\nprose\nEnvironment: c\n")
    assert texts(record.read(rd.ENVIRONMENT)) == ["Environment: a", "Environment: b"]


def test_a_dressed_line_inside_the_run_belongs_to_it():
    record = rd.parse("Environment: a\n**Environment: b**\nEnvironment: c\n")
    assert texts(record.read(rd.ENVIRONMENT)) == [
        "Environment: a", "Environment: b", "Environment: c"]


def test_a_bullet_or_quote_ends_the_run():
    for ender in ("- Environment: x", "> Environment: x"):
        record = rd.parse(f"Environment: a\n{ender}\nEnvironment: b\n")
        assert texts(record.read(rd.ENVIRONMENT)) == ["Environment: a"], ender


def test_a_mid_line_mention_ends_the_run():
    # CP-856: a line that mentions the prefix after its start does not declare, so it ends the run.
    for field, prefix in ((rd.ENVIRONMENT, "Environment:"), (rd.FAILING, "Failing:")):
        record = rd.parse(f"{prefix} a\nThe {prefix} line above\n{prefix} b\n")
        assert texts(record.read(field)) == [f"{prefix} a"], prefix


def test_anywhere_rows_still_read_every_match():
    record = rd.parse("Deferred: a\nprose\n\nDeferred: b\n- Task 1 x\nsome\n- Task 2 y\n")
    assert texts(record.read(rd.DEFERRED)) == ["Deferred: a", "Deferred: b"]
    assert texts(record.read(rd.RELANE_NOTE)) == ["- Task 1 x", "- Task 2 y"]


def test_crlf_line_endings_read_like_lf():
    # `\r\n` splits like `\n`, so no line keeps a `\r` in the form the builder quotes back, and
    # a closing line ending makes no empty line.
    record = rd.parse("x\r\nSuite: green\r\n")
    assert record.lines == rd.parse("x\nSuite: green\n").lines
    assert record.lines == (rd.Line(raw="x", text="x"),
                            rd.Line(raw="Suite: green", text="Suite: green"))


def test_an_empty_body_has_no_lines():
    record = rd.parse("")
    assert record.lines == ()
    for field in rd.FIELDS:
        assert record.read(field) == ()
    assert record.one(rd.SUITE) is None


def test_a_first_row_reads_only_the_first_match():
    record = rd.parse("Suite: green\nnote\nSuite: red\n")
    assert texts(record.read(rd.SUITE)) == ["Suite: green"]
    assert record.one(rd.SUITE) == rd.Line(raw="Suite: green", text="Suite: green")


def test_an_all_row_reads_every_match_in_body_order():
    record = rd.parse("Environment: one\nDeferred: task 1\nEnvironment: two\nDeferred: task 2\n")
    # The `Environment:` lines are not consecutive, so `ENVIRONMENT` (a first-run field) reads only
    # the first; `DEFERRED` is read from anywhere and still reads both.
    assert texts(record.read(rd.ENVIRONMENT)) == ["Environment: one"]
    assert texts(record.read(rd.DEFERRED)) == ["Deferred: task 1", "Deferred: task 2"]


def test_one_on_an_all_row_is_refused():
    with pytest.raises(ValueError):
        rd.parse("Environment: one\n").one(rd.ENVIRONMENT)


def test_the_parsed_record_is_immutable():
    record = rd.parse("Suite: green\nEnvironment: a\nEnvironment: b\n")
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.lines = ()
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.lines[0].text = "x"
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.lines[0].raw = "x"
    assert isinstance(record.lines, tuple)
    assert all(isinstance(record.read(field), tuple) for field in rd.FIELDS)


def test_the_table_states_todays_reading():
    expected = [
        ("SUITE", "Suite:", rd.Place.ANYWHERE, rd.Count.FIRST),
        ("LANGUAGE_RESOLUTION", "Language resolution", rd.Place.ANYWHERE, rd.Count.ALL),
        ("ENVIRONMENT", "Environment:", rd.Place.FIRST_RUN, rd.Count.ALL),
        ("DEFERRED", "Deferred:", rd.Place.ANYWHERE, rd.Count.ALL),
        ("FAILING", "Failing:", rd.Place.FIRST_RUN, rd.Count.ALL),
        ("RELANE_NOTE", "- Task ", rd.Place.ANYWHERE, rd.Count.ALL),
        ("INTEGRITY", "Integrity:", rd.Place.ANYWHERE, rd.Count.FIRST),
        ("SECURITY", "Security:", rd.Place.ANYWHERE, rd.Count.FIRST),
        ("PUBLISHES_TEXT", "Publishes text:", rd.Place.ANYWHERE, rd.Count.FIRST),
        ("PLANNED_BY", "Planned by:", rd.Place.ANYWHERE, rd.Count.FIRST),
        ("REPAIR", "Repair:", rd.Place.ANYWHERE, rd.Count.FIRST),
    ]
    assert [(f.name, f.prefix, f.place, f.count) for f in rd.FIELDS] == expected
    for name, _prefix, _place, _count in expected:
        assert getattr(rd, name) is next(f for f in rd.FIELDS if f.name == name)


def test_prefixes_are_unique_and_by_prefix_is_complete_and_read_only():
    prefixes = [field.prefix for field in rd.FIELDS]
    assert len(set(prefixes)) == len(prefixes) == 11
    assert len(rd.BY_PREFIX) == 11
    assert all(rd.BY_PREFIX[field.prefix] is field for field in rd.FIELDS)
    with pytest.raises(TypeError):
        rd.BY_PREFIX["Suite:"] = rd.SECURITY
    with pytest.raises(TypeError):
        del rd.BY_PREFIX["Suite:"]


def test_every_prefix_the_chain_names_is_a_row():
    steps = chain_development.DEVELOPMENT_STEPS + chain_development.CHANGE_STEPS
    named = {step.declared_prefix for step in steps if step.declared_prefix}
    named |= {step.runs_when.prefix for step in steps if step.runs_when is not None}
    assert named, "the chain names no prefix, so this test would pass over nothing"
    assert named <= set(rd.BY_PREFIX)


def _imported_modules(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            found |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return found


def _tool_modules() -> set[str]:
    """Every tool module on disk, read from the folder rather than listed."""
    return {path.stem for path in TOOLS.glob("*.py")}


def test_the_parser_imports_no_engine_and_the_builder_no_chain():
    parser = _imported_modules(TOOLS / "record_declarations.py")
    assert not parser & {"chain_development", "chain", "commit_builder"}
    # change_design.md §3: "The module imports no other tool."
    assert not parser & (_tool_modules() - {"record_declarations"})
    builder = _imported_modules(TOOLS / "commit_builder.py")
    assert "record_declarations" in builder
    assert "chain_development" not in builder


def test_no_reader_writes_a_rows_prefix_of_its_own():
    # change_spec.md § Structural Goal: the table "is the one place each prefix string is
    # written". Every tool that reads through the parser is found on disk by its import, and none
    # of them may hold a row's prefix as a string literal of its own: it takes `<ROW>.prefix`.
    prefixes = {field.prefix for field in rd.FIELDS}
    readers = [path for path in sorted(TOOLS.glob("*.py"))
               if not path.name.startswith("test_") and path.stem != "record_declarations"
               and "record_declarations" in _imported_modules(path)]
    assert {"chain_development", "commit_builder", "record_readings"} <= {p.stem for p in readers}
    written = [
        f"{path.name}:{node.lineno}: {node.value!r}"
        for path in readers
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.Constant) and node.value in prefixes
    ]
    assert written == []
