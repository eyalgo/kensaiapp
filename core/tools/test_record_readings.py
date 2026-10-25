"""The record readings: what today's readers return for the instance's real records, pinned.

WHY THIS FILE LOOKS LIKE THIS
    `record_readings.py` calls the chain's and the commit builder's readers unchanged, so the
    unit tests here hand it synthetic markers and reports and a throwaway git repository, and
    assert the stored form it makes of what the readers return. Nothing here patches the module
    under test: the git runner, the snapshot path and the output stream are handed to it.
"""

from __future__ import annotations

import io
import json
import re
import subprocess
from pathlib import Path

import pytest

import record_readings as rr

KEY = "2026-10-24_some-change"
MARKER_SUBJECT = f"developer: {KEY} — implementation complete"
HEX_40 = re.compile(r"\b[0-9a-f]{40}\b")

MARKER_MESSAGE = f"""{MARKER_SUBJECT}

Suite: green — 7803 passed, 10 skipped
Environment: container — img:1, arm64
Language resolution: python — declared in project.md

Deferred: task 4 — unique-deferral-prose — core/tools/x.md
Failing: tests/test_x.py::test_a — task 4

Developer Review Notes (vs tl_instruction.md):
- Task 2 no red (lane d) — the subject already satisfied it, confirmed
"""

REPORT_TEXT = """# Report

Integrity: pass
Security: reported
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.test", *args],
        capture_output=True, text=True, check=True,
    ).stdout


def _new_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    return repo


def _commit(repo: Path, subject: str, body: str = "") -> None:
    message = [subject] if not body else [subject, body]
    arguments = ["commit", "--quiet", "--allow-empty"]
    for paragraph in message:
        arguments += ["-m", paragraph]
    _git(repo, *arguments)


def _commit_file(repo: Path, relative: str, text: str) -> None:
    target = repo / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    _git(repo, "add", relative)
    _git(repo, "commit", "--quiet", "-m", f"add {relative}")


def _trail(project: str, key: str, name: str) -> str:
    return f"system/projects/{project}/journey/tobiishi/trail/{key}/{name}"


# --- the readings of one record ---------------------------------------------------------------


def test_marker_readings_report_every_reader() -> None:
    readings = rr.marker_readings(MARKER_MESSAGE)

    assert readings["suite_verdict"] == "green"
    assert readings["environment_kinds"] == ["container"]
    assert readings["language_resolved"] is True
    assert readings["relaned_tasks"] == [2]
    for line_reading in ("deferrals", "failing_cases", "builder_environment", "builder_failing"):
        assert readings[line_reading]["count"] == 1, line_reading


def test_marker_with_no_declarations_reads_absent() -> None:
    readings = rr.marker_readings(f"{MARKER_SUBJECT}\n\nNothing declared here.\n")

    assert readings["suite_verdict"] is None
    assert readings["environment_kinds"] == []
    assert readings["language_resolved"] is False
    assert readings["relaned_tasks"] == []
    for line_reading in ("deferrals", "failing_cases", "builder_environment", "builder_failing"):
        assert readings[line_reading]["count"] == 0, line_reading


def test_integrity_report_reads_its_integrity_line() -> None:
    readings = rr.report_readings(REPORT_TEXT, rr.SECTION_CODE_INTEGRITY)

    assert readings["declared_verdict"] == "pass"


def test_security_report_reads_its_security_line() -> None:
    readings = rr.report_readings(REPORT_TEXT, rr.SECTION_SECURITY)

    assert readings["declared_verdict"] == "reported"


def test_wrapped_environment_mention_after_the_block_is_not_read() -> None:
    text = "Environment: owners-mac — no CI\nmore prose\n`Environment:` line above is the run's\n"

    readings = rr.report_readings(text, rr.SECTION_CODE_INTEGRITY)

    assert readings["environment_kinds"] == ["owners-mac"]


def test_line_readings_are_stored_as_count_and_digest() -> None:
    stored = json.dumps(rr.marker_readings(MARKER_MESSAGE))
    changed = MARKER_MESSAGE.replace("unique-deferral-prose", "another-reason")

    for prose in ("unique-deferral-prose", "tests/test_x.py", "img:1", "arm64"):
        assert prose not in stored
    assert (rr.marker_readings(MARKER_MESSAGE)["deferrals"]["sha256"]
            != rr.marker_readings(changed)["deferrals"]["sha256"])


def test_multiword_verdict_is_stored_as_a_digest() -> None:
    readings = rr.report_readings("Integrity: pass with notes\n", rr.SECTION_CODE_INTEGRITY)

    stored = readings["declared_verdict"]
    assert set(stored) == {"count", "sha256"}
    assert "notes" not in json.dumps(readings)


def test_word_with_a_slash_is_stored_as_a_digest() -> None:
    readings = rr.report_readings("Environment: some/where — x\n", rr.SECTION_CODE_INTEGRITY)

    (kind,) = readings["environment_kinds"]
    assert set(kind) == {"count", "sha256"}
    assert "some/where" not in json.dumps(readings)


def test_a_word_over_thirty_two_characters_is_stored_as_a_digest() -> None:
    long_word = "w" * 33

    assert rr.stored_form(long_word) != long_word
    assert rr.stored_form("w" * 32) == "w" * 32


# --- finding the records ----------------------------------------------------------------------


def test_markers_are_found_by_exact_subject(tmp_path: Path) -> None:
    repo = _new_repo(tmp_path)
    _commit(repo, MARKER_SUBJECT, "Suite: green\n")
    wanted = _git(repo, "rev-parse", "HEAD").strip()
    _commit(repo, f"{MARKER_SUBJECT} (re-run)")
    _commit(repo, f"{KEY} — implementation complete")
    _commit(repo, "developer: task 1 x — green")

    records = rr.find_records(repo, rr.run_git)

    assert list(records.markers) == [wanted]
    assert records.markers[wanted].startswith(MARKER_SUBJECT)
    assert "Suite: green" in records.markers[wanted]


def test_reports_are_found_under_trail_only(tmp_path: Path) -> None:
    repo = _new_repo(tmp_path)
    _commit_file(repo, _trail("p", "k", "code-integrity-report.md"), "Integrity: pass\n")
    _commit_file(repo, _trail("p", "k/deeper", "security-report.md"), "Security: pass\n")
    _commit_file(repo, "system/projects/p/journey/tobiishi/k/code-integrity-report.md", "x\n")
    _commit_file(repo, _trail("p", "k", "other-report.md"), "Integrity: pass\n")
    integrity_blob = _git(
        repo, "rev-parse", f"HEAD:{_trail('p', 'k', 'code-integrity-report.md')}").strip()
    security_blob = _git(
        repo, "rev-parse", f"HEAD:{_trail('p', 'k/deeper', 'security-report.md')}").strip()

    records = rr.find_records(repo, rr.run_git)

    assert records.code_integrity_reports == {integrity_blob: "Integrity: pass\n"}
    assert records.security_reports == {security_blob: "Security: pass\n"}


def test_a_marker_text_is_the_body_the_chain_reads(tmp_path: Path) -> None:
    repo = _new_repo(tmp_path)
    _commit(repo, MARKER_SUBJECT, "Suite: green\n\nDeferred: task 1 — x — y.md\n")
    marker_id = _git(repo, "rev-parse", "HEAD").strip()

    records = rr.find_records(repo, rr.run_git)

    assert records.markers == {marker_id: _git(repo, "log", "-1", "--format=%B", marker_id)}


def test_a_report_directly_under_trail_is_found(tmp_path: Path) -> None:
    repo = _new_repo(tmp_path)
    path = "system/projects/p/journey/tobiishi/trail/code-integrity-report.md"
    _commit_file(repo, path, "Integrity: pass\n")

    records = rr.find_records(repo, rr.run_git)

    assert records.code_integrity_reports == {
        _git(repo, "rev-parse", f"HEAD:{path}").strip(): "Integrity: pass\n"}


def test_a_blob_under_both_report_names_is_found_in_both_sections(tmp_path: Path) -> None:
    repo = _new_repo(tmp_path)
    _commit_file(repo, _trail("p", "k", "code-integrity-report.md"), REPORT_TEXT)
    _commit_file(repo, _trail("p", "k", "security-report.md"), REPORT_TEXT)
    blob = _git(repo, "rev-parse", f"HEAD:{_trail('p', 'k', 'security-report.md')}").strip()

    records = rr.find_records(repo, rr.run_git)

    assert records.code_integrity_reports == {blob: REPORT_TEXT}
    assert records.security_reports == {blob: REPORT_TEXT}


def test_relaned_tasks_are_stored_as_sorted_numbers() -> None:
    message = (f"{MARKER_SUBJECT}\n\n- Task 5 no red (lane d) — already held\n"
               "- Task 3 red at baseline (lane f) — red before the change\n")

    assert rr.marker_readings(message)["relaned_tasks"] == [3, 5]


def test_a_report_is_decoded_as_utf8(tmp_path: Path) -> None:
    repo = _new_repo(tmp_path)
    _commit_file(repo, _trail("p", "k", "code-integrity-report.md"), "Integrity: pass — ok\n")

    records = rr.find_records(repo, rr.run_git)

    assert list(records.code_integrity_reports.values()) == ["Integrity: pass — ok\n"]


# --- the snapshot and the comparison ----------------------------------------------------------


def _records(marker_text: str = MARKER_MESSAGE) -> rr.Records:
    return rr.Records(
        markers={"a" * 40: marker_text},
        code_integrity_reports={"b" * 40: REPORT_TEXT},
        security_reports={"c" * 40: REPORT_TEXT},
    )


def test_compare_names_the_record_and_reading_that_differ() -> None:
    snapshot = rr.snapshot_of(_records())
    snapshot[rr.SECTION_MARKERS]["a" * 40]["suite_verdict"] = "red"

    result = rr.compare(_records(), snapshot)

    assert result.unknown == []
    (mismatch,) = result.mismatches
    assert (mismatch.section, mismatch.record_id, mismatch.reading) == (
        rr.SECTION_MARKERS, "a" * 40, "suite_verdict")
    assert (mismatch.stored, mismatch.read) == ("red", "green")


def test_compare_is_clean_against_its_own_snapshot() -> None:
    result = rr.compare(_records(), rr.snapshot_of(_records()))

    assert result.mismatches == []
    assert result.unknown == []


def test_compare_lists_records_the_snapshot_lacks() -> None:
    snapshot = rr.snapshot_of(_records())
    del snapshot[rr.SECTION_SECURITY]["c" * 40]

    result = rr.compare(_records(), snapshot)

    assert result.mismatches == []
    assert result.unknown == [(rr.SECTION_SECURITY, "c" * 40)]


def test_compare_ignores_snapshot_ids_not_found() -> None:
    snapshot = rr.snapshot_of(_records())
    snapshot[rr.SECTION_MARKERS]["d" * 40] = {"suite_verdict": "red"}

    result = rr.compare(_records(), snapshot)

    assert result.mismatches == []
    assert result.unknown == []


def test_loading_a_missing_snapshot_raises(tmp_path: Path) -> None:
    with pytest.raises(rr.SnapshotError):
        rr.load_snapshot(tmp_path / "absent.json")


def test_loading_an_unparsable_snapshot_raises(tmp_path: Path) -> None:
    broken = tmp_path / "snapshot.json"
    broken.write_text("{not json", encoding="utf-8")

    with pytest.raises(rr.SnapshotError):
        rr.load_snapshot(broken)


def test_loading_a_snapshot_without_its_sections_raises(tmp_path: Path) -> None:
    partial = tmp_path / "snapshot.json"
    partial.write_text('{"markers": {}}\n', encoding="utf-8")

    with pytest.raises(rr.SnapshotError):
        rr.load_snapshot(partial)


# --- the command ------------------------------------------------------------------------------


def _repo_with_records(tmp_path: Path) -> Path:
    repo = _new_repo(tmp_path)
    _commit(repo, MARKER_SUBJECT, MARKER_MESSAGE.split("\n\n", 1)[1])
    _commit_file(repo, _trail("p", "k", "code-integrity-report.md"), REPORT_TEXT)
    _commit_file(repo, _trail("p", "k", "security-report.md"), REPORT_TEXT + "more\n")
    return repo


def _write(repo: Path, snapshot_path: Path) -> tuple[int, str]:
    out = io.StringIO()
    status = rr.run(["--write"], repo_root=repo, snapshot_path=snapshot_path, git=rr.run_git,
                    out=out)
    return status, out.getvalue()


def test_writing_twice_is_byte_identical(tmp_path: Path) -> None:
    repo = _repo_with_records(tmp_path)
    snapshot_path = tmp_path / "snapshot.json"

    _write(repo, snapshot_path)
    first = snapshot_path.read_bytes()
    _write(repo, snapshot_path)

    assert snapshot_path.read_bytes() == first
    assert first.endswith(b"\n")
    text = first.decode("utf-8")
    assert len(HEX_40.findall(text)) == 3
    assert all(len(HEX_40.findall(line)) <= 1 for line in text.splitlines())
    sections = json.loads(text)
    assert set(sections) == {rr.SECTION_MARKERS, rr.SECTION_CODE_INTEGRITY, rr.SECTION_SECURITY}
    assert [len(sections[name]) for name in sorted(sections)] == [1, 1, 1]


def test_write_prints_counts_and_exits_zero(tmp_path: Path) -> None:
    repo = _repo_with_records(tmp_path)

    status, printed = _write(repo, tmp_path / "snapshot.json")

    assert status == 0
    assert printed.splitlines() == [
        f"{rr.SECTION_MARKERS}: 1",
        f"{rr.SECTION_CODE_INTEGRITY}: 1",
        f"{rr.SECTION_SECURITY}: 1",
    ]


def test_without_write_the_command_is_a_usage_error(tmp_path: Path) -> None:
    repo = _new_repo(tmp_path)

    with pytest.raises(SystemExit) as raised:
        rr.run([], repo_root=repo, snapshot_path=tmp_path / "snapshot.json", git=rr.run_git,
               out=io.StringIO())

    assert raised.value.code == 2
    assert not (tmp_path / "snapshot.json").exists()


# --- this instance's real records, against the committed snapshot -----------------------------

_REPO = Path(__file__).resolve().parents[2]
_COMMITTED_SNAPSHOT = Path(__file__).with_name(rr.SNAPSHOT_FILE_NAME)
_REAL_RECORDS = rr.find_records(_REPO, rr.run_git)
_PINNED = [(section, record_id)
           for section in rr.SECTIONS
           for record_id in sorted(_REAL_RECORDS.section(section))]
_DIGEST_HEX = re.compile(r"[0-9a-f]{64}")
_READING_NAMES = {
    rr.SECTION_MARKERS: {
        "suite_verdict", "environment_kinds", "language_resolved", "deferrals", "failing_cases",
        "relaned_tasks", "builder_environment", "builder_failing"},
    rr.SECTION_CODE_INTEGRITY: {"environment_kinds", "declared_verdict"},
    rr.SECTION_SECURITY: {"environment_kinds", "declared_verdict"},
}


@pytest.fixture(scope="module")
def committed_snapshot() -> dict[str, dict[str, dict[str, object]]]:
    return rr.load_snapshot(_COMMITTED_SNAPSHOT)


@pytest.mark.parametrize(
    ("section", "record_id"),
    _PINNED,
    ids=[f"{section}-{record_id}" for section, record_id in _PINNED],
)
def test_every_pinned_record_reads_as_stored(
    section: str, record_id: str, committed_snapshot: dict[str, dict[str, dict[str, object]]]
) -> None:
    one_record = {name: ({record_id: _REAL_RECORDS.section(name)[record_id]}
                         if name == section else {}) for name in rr.SECTIONS}

    result = rr.compare(rr.Records(**one_record), committed_snapshot)

    if result.unknown:
        pytest.skip(f"record {record_id} is not in the committed snapshot")
    assert result.mismatches == [], (
        f"{section} {record_id} reads differently from its snapshot: "
        + ", ".join(f"{m.reading} stored {m.stored!r}, read {m.read!r}"
                    for m in result.mismatches))


def test_the_committed_snapshot_exists_and_loads() -> None:
    assert _COMMITTED_SNAPSHOT.is_file(), f"{_COMMITTED_SNAPSHOT.name} is not committed"
    assert set(rr.load_snapshot(_COMMITTED_SNAPSHOT)) == set(rr.SECTIONS)


def _stored_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _stored_strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _stored_strings(item)]
    return []


def test_the_committed_snapshot_holds_no_text_and_no_path() -> None:
    snapshot = rr.load_snapshot(_COMMITTED_SNAPSHOT)

    assert set(snapshot) == set(rr.SECTIONS)
    for section, records in snapshot.items():
        for record_id, readings in records.items():
            assert HEX_40.fullmatch(record_id), record_id
            assert set(readings) <= _READING_NAMES[section], (section, record_id)
            for text in _stored_strings(readings):
                assert _DIGEST_HEX.fullmatch(text) or (
                    0 < len(text) <= 32 and not re.search(r"[\s/]", text)), (section, record_id)
