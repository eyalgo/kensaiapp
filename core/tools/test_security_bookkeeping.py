"""Tests for `security_bookkeeping.py` and for the text of the files that call it.

Unit tests hand `Bookkeeping` the three fakes from `security_bookkeeping_test_support.py`
and drive `run(...)`. Each port has one contract suite, a plain base class that pytest does not
collect, and two `Test...` subclasses that run it, one on the fake and one on the real port.
"""

from __future__ import annotations

import datetime
import http.server
import io
import json
import re
import subprocess
import sys
import threading
import tomllib
from pathlib import Path

import pytest

import security_bookkeeping as sb
import security_bookkeeping_test_support as support

# ---------------------------------------------------------------------------------------------
# The ports and their contract suites (layer 2)
# ---------------------------------------------------------------------------------------------


class FilesContract:
    """What every `Files` does, real or fake. `make` returns a `(files, root)` pair."""

    def make(self, tmp_path: Path):
        raise NotImplementedError

    def test_files_a_missing_path_reads_none(self, tmp_path):
        files, root = self.make(tmp_path)
        assert files.read_text(str(root / "nothing.txt")) is None

    def test_files_written_text_reads_back_exactly_crlf_included(self, tmp_path):
        files, root = self.make(tmp_path)
        path = str(root / "a.txt")
        files.write_text(path, "one\r\ntwo\nthree — ünï\r\n")
        assert files.read_text(path) == "one\r\ntwo\nthree — ünï\r\n"

    def test_files_a_write_replaces_the_whole_file(self, tmp_path):
        files, root = self.make(tmp_path)
        path = str(root / "a.txt")
        files.write_text(path, "first text that is long")
        files.write_text(path, "second")
        assert files.read_text(path) == "second"

    def test_files_a_write_makes_a_missing_parent_folder(self, tmp_path):
        files, root = self.make(tmp_path)
        path = str(root / "deep" / "er" / "a.txt")
        files.write_text(path, "x")
        assert files.read_text(path) == "x"

    def make_unreadable(self, files, path: str) -> None:
        """Leave `path` holding something the port cannot read as UTF-8 text."""
        raise NotImplementedError

    def make_unwritable(self, files, path: str) -> None:
        """Leave `path` somewhere the port cannot write."""
        raise NotImplementedError

    def test_files_an_unreadable_path_raises_the_port_error(self, tmp_path):
        files, root = self.make(tmp_path)
        path = str(root / "unreadable.txt")
        self.make_unreadable(files, path)
        with pytest.raises(sb.FileAccessError):
            files.read_text(path)

    def test_files_a_write_that_cannot_land_raises_the_port_error(self, tmp_path):
        files, root = self.make(tmp_path)
        path = str(root / "blocked" / "a.txt")
        self.make_unwritable(files, path)
        with pytest.raises(sb.FileAccessError):
            files.write_text(path, "x")


class TestFakeFiles(FilesContract):
    def make(self, tmp_path):
        return support.FakeFiles(), tmp_path

    def make_unreadable(self, files, path):
        files.fail_read(path, "'utf-8' codec can't decode byte 0xff in position 0")

    def make_unwritable(self, files, path):
        files.fail_write(path, "[Errno 20] Not a directory")


class TestRealFiles(FilesContract):
    def make(self, tmp_path):
        return sb.Files(), tmp_path

    def make_unreadable(self, files, path):
        Path(path).write_bytes(b"\xff\xfe not UTF-8")

    def make_unwritable(self, files, path):
        # A regular file where the parent folder should be: no folder can be made there.
        Path(path).parent.write_text("in the way", encoding="utf-8")

    def test_files_the_real_write_leaves_no_temporary_file_behind(self, tmp_path):
        files, root = self.make(tmp_path)
        files.write_text(str(root / "only.txt"), "x")
        assert [p.name for p in root.iterdir()] == ["only.txt"]

    def test_files_a_folder_read_as_a_file_raises_the_port_error(self, tmp_path):
        files, root = self.make(tmp_path)
        (root / "a-folder").mkdir()
        with pytest.raises(sb.FileAccessError):
            files.read_text(str(root / "a-folder"))

    def test_files_a_failed_real_write_leaves_what_was_in_the_way_unchanged(self, tmp_path):
        files, root = self.make(tmp_path)
        path = str(root / "blocked" / "a.txt")
        self.make_unwritable(files, path)
        with pytest.raises(sb.FileAccessError):
            files.write_text(path, "x")
        assert (root / "blocked").read_text(encoding="utf-8") == "in the way"
        assert sorted(p.name for p in root.iterdir()) == ["blocked"]


class AdvisoriesContract:
    """What every `Advisories` does. `make` returns `(advisories, serve)`; `serve(id, body)`
    seeds what the service holds for an id, `body` being the raw text it would send."""

    def make(self):
        raise NotImplementedError

    def test_advisories_a_served_record_comes_back_as_its_object(self):
        advisories, serve, stop = self.make()
        try:
            serve("GHSA-aaaa", json.dumps({"published": "2026-01-02T03:04:05Z", "id": "x"}))
            assert advisories.fetch("GHSA-aaaa") == {
                "published": "2026-01-02T03:04:05Z",
                "id": "x",
            }
        finally:
            stop()

    def test_advisories_a_404_a_non_json_body_and_a_json_array_each_raise_the_port_error(self):
        advisories, serve, stop = self.make()
        try:
            serve("NOT-JSON", "this is not json")
            serve("AN-ARRAY", "[1, 2]")
            for advisory_id in ("MISSING", "NOT-JSON", "AN-ARRAY"):
                with pytest.raises(sb.AdvisoryDataError):
                    advisories.fetch(advisory_id)
        finally:
            stop()


class TestFakeAdvisories(AdvisoriesContract):
    def make(self):
        fake = support.FakeAdvisories()
        return fake, fake.serve, lambda: None


class TestRealAdvisories(AdvisoriesContract):
    def make(self):
        held: dict[str, str] = {}
        # Ids whose reply promises more bytes than it sends, then closes.
        self.cut_short: set[str] = set()
        cut_short = self.cut_short

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                advisory_id = self.path.rsplit("/", 1)[-1]
                if advisory_id not in held:
                    self.send_response(404)
                    self.end_headers()
                    return
                body = held[advisory_id].encode()
                promised = len(body) + 50 if advisory_id in cut_short else len(body)
                self.send_response(200)
                self.send_header("Content-Length", str(promised))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def stop():
            server.shutdown()
            server.server_close()
            thread.join()

        base = f"http://127.0.0.1:{server.server_address[1]}/v1/vulns/"
        return sb.Advisories(base), held.__setitem__, stop

    def test_advisories_a_reply_cut_short_raises_the_port_error(self):
        advisories, serve, stop = self.make()
        try:
            serve("CUT-SHORT", json.dumps({"published": "2026-01-02T03:04:05Z"}))
            self.cut_short.add("CUT-SHORT")
            with pytest.raises(sb.AdvisoryDataError):
                advisories.fetch("CUT-SHORT")
        finally:
            stop()


class ClockContract:
    def make(self):
        raise NotImplementedError

    def test_clock_today_is_a_date_and_not_a_datetime(self):
        today = self.make().today()
        assert type(today) is datetime.date


class TestFakeClock(ClockContract):
    def make(self):
        return support.FakeClock(datetime.date(2026, 11, 10))


class TestRealClock(ClockContract):
    def make(self):
        return sb.Clock()


# ---------------------------------------------------------------------------------------------
# The entry layer, driven through `run` with the fakes (layer 1)
# ---------------------------------------------------------------------------------------------

TODAY = datetime.date(2026, 11, 10)


class Driven:
    """One `run` call: its exit status, the two streams, and the fakes it was handed."""

    def __init__(self, code, out, err, files, advisories):
        self.code = code
        self.out = out
        self.err = err
        self.files = files
        self.advisories = advisories


def drive(argv, *, held=None, advisories=None, today=TODAY, failing_reads=None,
          failing_writes=None):
    """Run the tool on `argv` over a `FakeFiles` seeded with `held` (path -> text), whose reads
    and writes of the paths in `failing_reads` and `failing_writes` (path -> reason) fail."""
    files = support.FakeFiles(held)
    for path, reason in (failing_reads or {}).items():
        files.fail_read(path, reason)
    for path, reason in (failing_writes or {}).items():
        files.fail_write(path, reason)
    advisories = advisories if advisories is not None else support.FakeAdvisories()
    bookkeeping = sb.Bookkeeping(
        files=files, advisories=advisories, clock=support.FakeClock(today)
    )
    out, err = io.StringIO(), io.StringIO()
    code = sb.run(argv, bookkeeping=bookkeeping, stdout=out, stderr=err)
    return Driven(code, out.getvalue(), err.getvalue(), files, advisories)


# --- check-verdict ----------------------------------------------------------------------------


def report_with(verdict_line):
    return {"r.md": f"# Security report\n\n{verdict_line}\n\nThe rest.\n"}


def test_check_verdict_passes_a_bare_security_line():
    result = drive(["check-verdict", "--report", "r.md"], held=report_with("Security: fixed"))
    assert (result.code, result.out, result.err) == (0, "Security: fixed\n", "")


@pytest.mark.parametrize("value", ["unmerged", "stopped", "merged"])
def test_check_verdict_passes_each_repair_value(value):
    result = drive(["check-verdict", "--report", "r.md"], held=report_with(f"Repair: {value}"))
    assert (result.code, result.out) == (0, f"Repair: {value}\n")


@pytest.mark.parametrize(
    "line", ["Repair: **merged**", "- Repair: merged", "Repair: merged today"]
)
def test_check_verdict_refuses_a_line_that_is_not_bare(line):
    result = drive(["check-verdict", "--report", "r.md"], held=report_with(line))
    assert result.code == 1
    assert result.out == ""
    assert result.err.startswith("security_bookkeeping: ")
    assert "is not bare" in result.err
    assert line in result.err


def test_check_verdict_refuses_a_value_outside_its_set():
    result = drive(["check-verdict", "--report", "r.md"], held=report_with("Security: dirty"))
    assert result.code == 1
    assert result.out == ""
    assert '"dirty" is not a Security verdict' in result.err
    assert "is not bare" not in result.err


def test_check_verdict_refuses_a_missing_file_a_missing_title_and_a_missing_verdict_line():
    missing = drive(["check-verdict", "--report", "gone.md"])
    assert missing.code == 1 and "there is no file at gone.md" in missing.err
    untitled = drive(["check-verdict", "--report", "r.md"], held={"r.md": "Security: fixed\n"})
    assert untitled.code == 1 and "has no title" in untitled.err
    empty = drive(["check-verdict", "--report", "r.md"], held={"r.md": ""})
    assert empty.code == 1 and "has no title" in empty.err
    bare_title = drive(["check-verdict", "--report", "r.md"], held={"r.md": "# T\n\n\n  \n"})
    assert bare_title.code == 1 and "has no verdict line" in bare_title.err


def test_a_refusal_prints_nothing_on_stdout_and_changes_no_file():
    held = report_with("Repair: **merged**")
    result = drive(["check-verdict", "--report", "r.md"], held=held)
    assert result.out == ""
    assert result.files.held == held
    assert result.files.written == []
    missing = drive(["check-verdict", "--report", "gone.md"])
    assert missing.files.held == {}


def test_an_argument_the_parser_rejects_exits_2_with_nothing_on_stdout():
    result = drive(["check-verdict"])
    assert result.code == 2
    assert result.out == ""
    assert "--report" in result.err


# --- read-record ------------------------------------------------------------------------------

RECORD_PATH = "rec.toml"
ENTRY_A = """[[exception]]
advisory = "GHSA-aaaa"
distribution = "jinja2"
published = 2026-10-01
reason = "not reached"
"""
RENEWAL_A = """
[[exception.renewal]]
on = 2026-10-20
reason = "still not reached"
"""
ENTRY_B = """
[[exception]]
advisory = "GHSA-bbbb"
distribution = "urllib3"
published = 2026-10-05
reason = "only in a test"
"""


def read_record(text):
    return drive(["read-record", "--record", RECORD_PATH], held={RECORD_PATH: text})


def test_read_record_prints_an_entry_with_its_renewal():
    result = read_record(ENTRY_A + RENEWAL_A)
    assert result.code == 0
    assert json.loads(result.out) == [
        {
            "advisory": "GHSA-aaaa",
            "distribution": "jinja2",
            "published": "2026-10-01",
            "reason": "not reached",
            "renewals": [{"on": "2026-10-20", "reason": "still not reached"}],
        }
    ]
    assert list(json.loads(result.out)[0]) == [
        "advisory", "distribution", "published", "reason", "renewals"
    ]
    assert result.out.endswith("\n") and result.out.startswith("[\n  {\n    ")


def test_read_record_on_a_missing_path_prints_an_empty_array():
    result = drive(["read-record", "--record", "none.toml"])
    assert (result.code, result.out, result.err) == (0, "[]\n", "")


def test_read_record_refuses_a_window_key_naming_the_entry_and_the_key():
    result = read_record(ENTRY_A + "window = 30\n")
    assert result.code == 1
    assert 'rec.toml, entry GHSA-aaaa: the key "window" is not in the record\'s shape' in result.err


def test_read_record_refuses_a_renewal_with_no_on():
    result = read_record(ENTRY_A + '\n[[exception.renewal]]\nreason = "x"\n')
    assert result.code == 1
    assert 'entry GHSA-aaaa, renewal 1: no "on" key' in result.err


def test_read_record_refuses_a_quoted_string_published():
    result = read_record(ENTRY_A.replace("published = 2026-10-01", 'published = "2026-10-01"'))
    assert result.code == 1
    assert '"published" is not a bare TOML date' in result.err


def test_read_record_refuses_a_datetime_published():
    result = read_record(ENTRY_A.replace("2026-10-01", "2026-10-01T10:00:00Z"))
    assert result.code == 1
    assert '"published" is not a bare TOML date' in result.err


def test_read_record_refuses_an_extra_top_level_key_and_an_extra_table():
    top = read_record('title = "x"\n' + ENTRY_A)
    assert top.code == 1 and 'holds the top-level key "title"' in top.err
    table = read_record(ENTRY_A + "\n[settings]\nx = 1\n")
    assert table.code == 1 and 'holds the top-level key "settings"' in table.err


def test_read_record_refuses_two_entries_for_one_advisory():
    result = read_record(ENTRY_A + ENTRY_A.replace("jinja2", "other"))
    assert result.code == 1
    assert "holds two entries for GHSA-aaaa" in result.err


def test_read_record_refuses_a_file_that_is_not_toml():
    result = read_record("[[exception\nbroken")
    assert result.code == 1
    assert "rec.toml is not valid TOML: " in result.err


def test_read_record_names_an_entry_with_no_advisory_by_its_position():
    result = read_record(ENTRY_A + ENTRY_B.replace('advisory = "GHSA-bbbb"\n', ""))
    assert result.code == 1
    assert 'rec.toml, entry 2: no "advisory" key' in result.err


def test_read_record_refuses_a_missing_key_a_non_string_and_a_non_list_exception():
    no_reason = read_record(ENTRY_A.replace('reason = "not reached"\n', ""))
    assert 'entry GHSA-aaaa: no "reason" key' in no_reason.err
    number = read_record(ENTRY_A.replace('distribution = "jinja2"', "distribution = 4"))
    assert '"distribution" is not a string' in number.err
    renewal_number = read_record(ENTRY_A + RENEWAL_A.replace('"still not reached"', "5"))
    assert 'renewal 1: "reason" is not a string' in renewal_number.err
    not_list = read_record("exception = 3\n")
    assert '"exception" is not a list of [[exception]] tables' in not_list.err


def test_a_refused_read_record_prints_nothing_on_stdout():
    text = ENTRY_A + "window = 30\n"
    result = read_record(text)
    assert (result.code, result.out) == (1, "")
    assert result.files.held == {RECORD_PATH: text}


# --- lapse-date -------------------------------------------------------------------------------


def listed(advisory="GHSA-x", severity="Critical", published="2026-11-03", **overrides):
    """One object of the shape `normalise` prints."""
    obj = {
        "advisory": advisory,
        "package": "jinja2",
        "version": "3.1.2",
        "severity": severity,
        "fixed": "3.1.6",
        "published": published,
    }
    obj.update(overrides)
    return obj


def lapse(obj, *extra, held=None):
    text = obj if isinstance(obj, str) else json.dumps(obj)
    return drive(["lapse-date", "--entry", text, *extra], held=held)


def test_lapse_date_critical_adds_seven_days():
    result = lapse(listed())
    assert result.code == 0
    assert json.loads(result.out) == {
        "advisory": "GHSA-x",
        "lapses": "2026-11-10",
        "from": "2026-11-03",
        "days": 7,
        "window": "default",
    }
    assert list(json.loads(result.out)) == ["advisory", "lapses", "from", "days", "window"]


def test_lapse_date_high_adds_thirty_days():
    out = json.loads(lapse(listed(severity="High", published="2026-10-15")).out)
    assert (out["lapses"], out["days"]) == ("2026-11-14", 30)


def test_lapse_date_unscored_adds_seven_days():
    out = json.loads(lapse(listed(severity="unscored", published="2026-02-25")).out)
    assert (out["lapses"], out["days"]) == ("2026-03-04", 7)


@pytest.mark.parametrize("severity", ["Medium", "Low"])
def test_lapse_date_medium_and_low_default_to_thirty_days(severity):
    assert json.loads(lapse(listed(severity=severity)).out)["days"] == 30


def test_lapse_date_runs_from_the_greatest_renewal_wherever_it_sits():
    record = (
        ENTRY_A
        + '\n[[exception.renewal]]\non = 2026-10-01\nreason = "later"\n'
        + '\n[[exception.renewal]]\non = 2026-09-01\nreason = "earlier"\n'
    )
    result = lapse(
        listed(advisory="GHSA-aaaa", severity="High", published="2026-08-01"),
        "--record", RECORD_PATH, held={RECORD_PATH: record},
    )
    out = json.loads(result.out)
    assert (out["from"], out["lapses"]) == ("2026-10-01", "2026-10-31")


def test_lapse_date_ignores_a_record_that_holds_no_renewal_for_the_advisory():
    result = lapse(
        listed(advisory="GHSA-other"), "--record", RECORD_PATH, held={RECORD_PATH: ENTRY_A}
    )
    assert json.loads(result.out)["from"] == "2026-11-03"
    missing = lapse(listed(), "--record", "none.toml")
    assert json.loads(missing.out)["from"] == "2026-11-03"


def test_lapse_date_uses_a_given_window():
    result = lapse(listed(severity="Low"), "--window", "Low=14", "--window", "High=20")
    out = json.loads(result.out)
    assert (out["days"], out["window"], out["lapses"]) == (14, "given", "2026-11-17")


def test_lapse_date_refuses_a_window_with_no_count_for_the_severity():
    result = lapse(
        listed(severity="Medium"), "--window", "Critical=3", "--window", "High=4"
    )
    assert result.code == 1 and result.out == ""
    assert "the window given has no count for Medium, the severity of GHSA-x." in result.err


@pytest.mark.parametrize(
    ("window", "fragment"),
    [
        (["--window", "Bogus=3"], 'names the severity "Bogus"'),
        (["--window", "Low=3", "--window", "Low=4"], "names Low twice"),
        (["--window", "Low=0"], "gives Low the count 0"),
        (["--window", "Low=-2"], "gives Low the count -2"),
        (["--window", "Low=2.5"], "gives Low the count 2.5"),
        (["--window", "Low=x"], "gives Low the count x"),
        (["--window", "Low"], "--window Low is not written as Severity=days"),
    ],
)
def test_lapse_date_refuses_an_unknown_a_repeated_or_a_non_positive_window(window, fragment):
    result = lapse(listed(severity="Low"), *window)
    assert result.code == 1 and result.out == ""
    assert fragment in result.err


@pytest.mark.parametrize(
    ("obj", "fragment"),
    [
        (listed(published=None), "the entry for GHSA-x has no publication date"),
        (listed(published="2026-02-30"), "the publication date 2026-02-30"),
        (listed(published="2026-2-3"), "the publication date 2026-2-3"),
        (listed(published="2026-11-03T00:00:00Z"), "which is not a real calendar date"),
        (listed(severity="Severe"), 'the severity "Severe", which is not Critical'),
    ],
)
def test_lapse_date_refuses_a_null_a_non_calendar_or_a_missing_published(obj, fragment):
    result = lapse(obj)
    assert result.code == 1 and result.out == ""
    assert fragment in result.err


def test_lapse_date_refuses_an_entry_that_is_not_whole():
    without = {key: value for key, value in listed().items() if key != "published"}
    result = lapse(without)
    assert 'the entry for GHSA-x has no "published" key' in result.err
    nameless = {key: value for key, value in listed().items() if key != "advisory"}
    assert 'the entry has no "advisory" key' in lapse(nameless).err
    for text in ("[1]", "nope", '"x"'):
        assert "--entry is not a JSON object" in lapse(text).err


def test_lapse_date_refuses_a_window_that_runs_past_the_calendar():
    # CP-1142: a count the calendar cannot hold is refused, never a traceback.
    past = lapse(listed(severity="Low"), "--window", "Low=999999999")
    assert past.code == 1 and past.out == ""
    assert past.err == (
        "security_bookkeeping: the window gives GHSA-x 999999999 days from 2026-11-03, which "
        "runs past the last date the calendar holds.\n"
    )
    huge = "9" * 5000
    beyond = lapse(listed(severity="Low"), "--window", f"Low={huge}")
    assert beyond.code == 1 and beyond.out == ""
    assert beyond.err == (
        f"security_bookkeeping: --window gives Low the count {huge}, which runs past the last "
        "date the calendar holds.\n"
    )


def test_find_lapsed_refuses_a_window_that_runs_past_the_calendar():
    listing = [listed(advisory="GHSA-aaaa", severity="Low")]
    result = lapsed(listing, ENTRY_A, "--window", "Low=3000000")
    assert result.code == 1 and result.out == ""
    assert "runs past the last date the calendar holds" in result.err


def test_lapse_date_refuses_a_record_in_another_shape():
    record = ENTRY_A + "window = 30\n"
    result = lapse(listed(), "--record", RECORD_PATH, held={RECORD_PATH: record})
    assert result.code == 1 and result.out == ""
    assert 'the key "window"' in result.err


# --- write-record -----------------------------------------------------------------------------


def write_entry(held=None, *, advisory="GHSA-new", reason="why it stands", **overrides):
    argv = {
        "--record": RECORD_PATH,
        "--advisory": advisory,
        "--distribution": "jinja2",
        "--published": "2026-10-09",
        "--reason": reason,
    }
    argv.update({f"--{key}": value for key, value in overrides.items()})
    flat = [part for pair in argv.items() for part in pair]
    return drive(["write-record", "entry", *flat], held=held)


def write_renewal(held=None, *, advisory="GHSA-aaaa", on="2026-11-02", reason="renewed"):
    argv = ["write-record", "renewal", "--record", RECORD_PATH, "--advisory", advisory]
    argv += ["--on", on, "--reason", reason]
    return drive(argv, held=held)


def test_write_entry_creates_a_missing_record_with_four_keys():
    result = write_entry()
    assert result.code == 0
    assert result.out == f"record created: {RECORD_PATH}\nentry written: GHSA-new\n"
    assert result.files.held[RECORD_PATH] == (
        "[[exception]]\n"
        'advisory = "GHSA-new"\n'
        'distribution = "jinja2"\n'
        "published = 2026-10-09\n"
        'reason = "why it stands"\n'
    )


def test_write_renewal_lands_after_the_target_entry_and_before_the_next_header():
    old = ENTRY_A + ENTRY_B
    result = write_renewal({RECORD_PATH: old})
    assert result.code == 0
    assert result.out == "renewal written: GHSA-aaaa on 2026-11-02\n"
    new = result.files.held[RECORD_PATH]
    cut = old.index("\n[[exception]]\nadvisory = \"GHSA-bbbb\"") + 1
    assert new == (
        old[:cut]
        + '[[exception.renewal]]\non = 2026-11-02\nreason = "renewed"\n\n'
        + old[cut:]
    )


def test_write_renewal_lands_after_the_last_existing_renewal():
    old = ENTRY_A + RENEWAL_A + ENTRY_B
    new = write_renewal({RECORD_PATH: old}).files.held[RECORD_PATH]
    cut = old.index('\n[[exception]]\nadvisory = "GHSA-bbbb"') + 1
    inserted = new[len(old[:cut]) : len(new) - len(old[cut:])]
    assert new == old[:cut] + inserted + old[cut:]
    assert inserted.startswith("[[exception.renewal]]\non = 2026-11-02")
    assert json.loads(read_record(new).out)[0]["renewals"][-1]["on"] == "2026-11-02"


def test_write_renewal_to_the_last_entry_goes_at_the_end_of_the_file():
    new = write_renewal({RECORD_PATH: ENTRY_A}, advisory="GHSA-aaaa").files.held[RECORD_PATH]
    assert new == ENTRY_A + '\n[[exception.renewal]]\non = 2026-11-02\nreason = "renewed"\n'


def test_write_entry_keeps_every_old_byte_comment_included():
    old = "# kept comment\n" + ENTRY_A + "# trailing note"
    new = write_entry({RECORD_PATH: old}).files.held[RECORD_PATH]
    assert new.startswith(old)
    assert new[len(old) :].startswith("\n\n[[exception]]\nadvisory = \"GHSA-new\"")
    assert len(json.loads(read_record(new).out)) == 2


def test_write_keeps_a_crlf_record_in_crlf():
    old = (ENTRY_A + ENTRY_B).replace("\n", "\r\n")
    entry = write_entry({RECORD_PATH: old}).files.held[RECORD_PATH]
    assert entry.startswith(old)
    assert entry.count("\n") == entry.count("\r\n")
    renewal = write_renewal({RECORD_PATH: old}).files.held[RECORD_PATH]
    assert renewal.count("\n") == renewal.count("\r\n")
    assert len(json.loads(read_record(renewal).out)[0]["renewals"]) == 1


def test_write_adds_no_window_severity_or_lapse_key():
    text = write_entry({RECORD_PATH: ENTRY_A}).files.held[RECORD_PATH]
    text = write_renewal({RECORD_PATH: text}).files.held[RECORD_PATH]
    assert not [line for line in text.splitlines() if line.startswith("window")]
    assert "severity" not in text and "lapse" not in text


def test_write_refuses_an_entry_already_held():
    result = write_entry({RECORD_PATH: ENTRY_A}, advisory="GHSA-aaaa")
    assert result.code == 1 and result.out == ""
    assert f"{RECORD_PATH} already holds an entry for GHSA-aaaa." in result.err
    assert result.files.held == {RECORD_PATH: ENTRY_A} and result.files.written == []


def test_write_refuses_a_renewal_for_an_advisory_not_held():
    result = write_renewal({RECORD_PATH: ENTRY_A}, advisory="GHSA-zzzz")
    assert result.code == 1 and result.out == ""
    assert f"{RECORD_PATH} holds no entry for GHSA-zzzz." in result.err
    assert result.files.held == {RECORD_PATH: ENTRY_A}
    missing = write_renewal(None)
    assert (
        f"there is no record at {RECORD_PATH}, so it holds no entry for GHSA-aaaa."
        in missing.err
    )
    assert missing.files.held == {}


def test_write_refuses_an_empty_value_and_a_non_calendar_date():
    empty = write_entry(reason="")
    assert empty.code == 1 and "--reason is empty." in empty.err and empty.files.held == {}
    blank = write_entry(advisory="   ")
    assert "--advisory is empty." in blank.err
    bad_date = write_entry(published="2026-02-30")
    assert "--published 2026-02-30 is not a real calendar date written YYYY-MM-DD." in bad_date.err
    assert bad_date.files.held == {} and bad_date.out == ""
    bad_on = write_renewal({RECORD_PATH: ENTRY_A}, on="2026-13-01")
    assert "--on 2026-13-01 is not a real calendar date" in bad_on.err
    assert bad_on.files.held == {RECORD_PATH: ENTRY_A}


def test_write_refuses_a_record_in_another_shape():
    shaped = ENTRY_A + "window = 30\n"
    for result in (write_entry({RECORD_PATH: shaped}), write_renewal({RECORD_PATH: shaped})):
        assert result.code == 1 and result.out == ""
        assert 'the key "window"' in result.err
        assert result.files.held == {RECORD_PATH: shaped}


def test_write_refuses_when_the_header_count_differs_from_the_parsed_entry_count():
    tricky = ENTRY_A.replace('reason = "not reached"', 'reason = """\n[[exception]]\n"""')
    result = write_renewal({RECORD_PATH: tricky})
    assert result.code == 1 and result.out == ""
    assert f"{RECORD_PATH} has 2 [[exception]] header lines and 1 entries" in result.err
    assert result.files.held == {RECORD_PATH: tricky}


INLINE_ENTRIES = (
    'exception = [{advisory = "GHSA-aaaa", distribution = "jinja2", published = 2026-10-01, '
    'reason = "not reached"}]\n'
)


def test_write_entry_refuses_a_record_whose_entries_are_an_inline_array():
    # CP-1157: the measured shape is [[exception]] tables; appending one after an inline array
    # would leave a file that is not valid TOML.
    result = write_entry({RECORD_PATH: INLINE_ENTRIES})
    assert result.code == 1 and result.out == ""
    assert result.err == (
        f'security_bookkeeping: {RECORD_PATH}: "exception" is not a list of [[exception]] '
        "tables.\n"
    )
    assert result.files.held == {RECORD_PATH: INLINE_ENTRIES}
    assert result.files.written == []


def test_write_renewal_refuses_an_entry_whose_renewals_are_an_inline_array():
    # CP-1157: the measured shape is [[exception.renewal]] tables; appending one after an inline
    # array would leave a file that is not valid TOML.
    record = ENTRY_A + 'renewal = [{on = 2026-10-20, reason = "still not reached"}]\n' + ENTRY_B
    result = write_renewal({RECORD_PATH: record})
    assert result.code == 1 and result.out == ""
    assert result.err == (
        f'security_bookkeeping: {RECORD_PATH}, entry GHSA-aaaa: the key "renewal" is not in the '
        "record's shape.\n"
    )
    assert result.files.held == {RECORD_PATH: record}


def test_every_written_record_reads_back_as_valid_toml():
    # The request: the record is written in its measured shape, so what a write leaves must be
    # a record `read-record` reads.
    text = write_entry({RECORD_PATH: ENTRY_A + RENEWAL_A + ENTRY_B}).files.held[RECORD_PATH]
    text = write_renewal({RECORD_PATH: text}, advisory="GHSA-bbbb").files.held[RECORD_PATH]
    text = write_renewal({RECORD_PATH: text}, advisory="GHSA-aaaa").files.held[RECORD_PATH]
    entries = json.loads(read_record(text).out)
    assert [entry["advisory"] for entry in entries] == ["GHSA-aaaa", "GHSA-bbbb", "GHSA-new"]
    assert [len(entry["renewals"]) for entry in entries] == [2, 1, 0]


def test_a_written_reason_reads_back_exactly():
    reason = 'the product calls "x" in C:\\y — non-ASCII \x01 and \x7f tab\there\nsecond line\r\n'
    written = write_entry(reason=reason).files.held[RECORD_PATH]
    assert "\n" not in written.split("reason = ", 1)[1].rstrip("\n")
    assert json.loads(read_record(written).out)[0]["reason"] == reason
    renewed = write_renewal({RECORD_PATH: written}, advisory="GHSA-new", reason=reason)
    assert json.loads(read_record(renewed.files.held[RECORD_PATH]).out)[0]["renewals"][0][
        "reason"
    ] == reason


def test_entry_then_renewal_into_a_record_on_disk_keep_the_measured_shape(tmp_path):
    record = str(tmp_path / "checks" / "deps" / "advisory_exceptions.toml")
    bookkeeping = sb.Bookkeeping(
        files=sb.Files(), advisories=support.FakeAdvisories(), clock=support.FakeClock(TODAY)
    )

    def call(*argv):
        out, err = io.StringIO(), io.StringIO()
        assert sb.run(argv, bookkeeping=bookkeeping, stdout=out, stderr=err) == 0, err.getvalue()
        return out.getvalue()

    call("write-record", "entry", "--record", record, "--advisory", "GHSA-1", "--distribution",
         "jinja2", "--published", "2026-10-01", "--reason", "not reached")
    call("write-record", "renewal", "--record", record, "--advisory", "GHSA-1", "--on",
         "2026-10-20", "--reason", "still not reached")
    with open(record, "rb") as handle:
        document = tomllib.load(handle)
    (entry,) = document["exception"]
    assert sorted(entry) == ["advisory", "distribution", "published", "reason", "renewal"]
    (renewal,) = entry["renewal"]
    assert sorted(renewal) == ["on", "reason"]
    assert not [line for line in Path(record).read_text().splitlines() if line.startswith("window")]


# --- find-lapsed ------------------------------------------------------------------------------

LIST_PATH = "advisories.json"


def lapsed(listing, record, *extra, today=TODAY):
    held = {LIST_PATH: json.dumps(listing)}
    if record is not None:
        held[RECORD_PATH] = record
    argv = ["find-lapsed", "--record", RECORD_PATH, "--list", LIST_PATH, *extra]
    return drive(argv, held=held, today=today)


THREE_ENTRIES = (
    ENTRY_A
    + ENTRY_B
    + """
[[exception]]
advisory = "GHSA-cccc"
distribution = "idna"
published = 2026-10-06
reason = "gone from the audit"
"""
)


def test_find_lapsed_sorts_each_exception_into_exactly_one_group_in_record_order():
    listing = [
        listed(advisory="GHSA-aaaa", severity="Critical", published="2026-11-03"),
        listed(advisory="GHSA-bbbb", severity="Critical", published="2026-11-04"),
    ]
    result = lapsed(listing, THREE_ENTRIES, "--date", "2026-11-10")
    assert result.code == 0
    assert json.loads(result.out) == {
        "lapsed": [{"advisory": "GHSA-aaaa", "distribution": "jinja2", "lapses": "2026-11-10"}],
        "holding": [{"advisory": "GHSA-bbbb", "distribution": "urllib3", "lapses": "2026-11-11"}],
        "unreported": [{"advisory": "GHSA-cccc", "distribution": "idna"}],
    }
    assert list(json.loads(result.out)) == ["lapsed", "holding", "unreported"]


def test_find_lapsed_without_a_date_uses_the_clock():
    listing = [listed(advisory="GHSA-aaaa", published="2026-11-03")]
    on_day = json.loads(lapsed(listing, ENTRY_A, today=datetime.date(2026, 11, 10)).out)
    assert [item["advisory"] for item in on_day["lapsed"]] == ["GHSA-aaaa"]
    day_before = json.loads(lapsed(listing, ENTRY_A, today=datetime.date(2026, 11, 9)).out)
    assert [item["advisory"] for item in day_before["holding"]] == ["GHSA-aaaa"]


def test_find_lapsed_on_a_missing_record_prints_three_empty_arrays():
    result = lapsed([listed()], None)
    assert json.loads(result.out) == {"lapsed": [], "holding": [], "unreported": []}


def test_find_lapsed_counts_an_exception_lapsed_on_its_lapse_day():
    listing = [listed(advisory="GHSA-aaaa", published="2026-11-03")]
    on = json.loads(lapsed(listing, ENTRY_A, "--date", "2026-11-10").out)
    after = json.loads(lapsed(listing, ENTRY_A, "--date", "2026-11-11").out)
    before = json.loads(lapsed(listing, ENTRY_A, "--date", "2026-11-09").out)
    assert (len(on["lapsed"]), len(after["lapsed"]), len(before["lapsed"])) == (1, 1, 0)


def test_find_lapsed_uses_an_exceptions_own_renewals():
    listing = [
        listed(advisory="GHSA-aaaa", published="2026-09-01"),
        listed(advisory="GHSA-bbbb", published="2026-09-01"),
    ]
    record = ENTRY_A + RENEWAL_A.replace("2026-10-20", "2026-11-08") + ENTRY_B
    out = json.loads(lapsed(listing, record, "--date", "2026-11-10").out)
    assert [item["advisory"] for item in out["holding"]] == ["GHSA-aaaa"]
    assert out["holding"][0]["lapses"] == "2026-11-15"
    assert [item["advisory"] for item in out["lapsed"]] == ["GHSA-bbbb"]


def test_find_lapsed_matches_by_advisory_id_alone_and_the_first_object_answers():
    listing = [
        listed(advisory="GHSA-aaaa", severity="Critical", published="2026-11-03"),
        listed(advisory="GHSA-aaaa", severity="Critical", published="2026-11-03", package="x"),
    ]
    out = json.loads(lapsed(listing, ENTRY_A, "--date", "2026-11-01").out)
    assert out["holding"][0]["distribution"] == "jinja2"


def test_find_lapsed_refuses_a_record_in_another_shape():
    result = lapsed([listed()], ENTRY_A + "window = 30\n")
    assert result.code == 1 and result.out == "" and 'the key "window"' in result.err


def test_find_lapsed_refuses_a_window_missing_a_severity_the_list_carries():
    listing = [listed(advisory="GHSA-aaaa", severity="Medium")]
    result = lapsed(listing, ENTRY_A, "--window", "Critical=5")
    assert result.code == 1 and result.out == ""
    assert "no count for Medium, the severity of GHSA-aaaa" in result.err


def test_find_lapsed_ignores_a_listed_severity_no_exception_needs():
    listing = [listed(advisory="GHSA-other", severity="Medium")]
    result = lapsed(listing, ENTRY_A, "--window", "Critical=5")
    assert result.code == 0
    assert [item["advisory"] for item in json.loads(result.out)["unreported"]] == ["GHSA-aaaa"]


def test_find_lapsed_refuses_a_list_that_is_not_normalises_output_and_a_bad_date():
    not_list = drive(
        ["find-lapsed", "--record", RECORD_PATH, "--list", LIST_PATH],
        held={LIST_PATH: '{"a": 1}'},
    )
    assert f"{LIST_PATH} does not hold a JSON list in the shape normalise prints." in not_list.err
    for text in ("not json", "[1]"):
        bad = drive(["find-lapsed", "--record", "r", "--list", LIST_PATH], held={LIST_PATH: text})
        assert bad.code == 1 and "does not hold a JSON list" in bad.err
    missing = drive(["find-lapsed", "--record", "r", "--list", "gone.json"])
    assert "there is no file at gone.json." in missing.err
    bad_date = lapsed([listed()], None, "--date", "2026-02-30")
    assert "--date 2026-02-30 is not a real calendar date" in bad_date.err


# --- write-upkeep -----------------------------------------------------------------------------

REGISTER_PATH = "upkeep.md"
HEADER_ROW = "| Task | Rule it serves | Cadence | Last done | Next due | What reminds the owner |"
SEPARATOR_ROW = "|---|---|---|---|---|---|"
REGISTER = f"""# Upkeep register

Some intro words.

{HEADER_ROW}
{SEPARATOR_ROW}
| Renew the first | rule one | monthly | 2026-10-01 | 2026-11-01 | the owner reads it |
| Renew the second | rule two | monthly | 2026-10-02 | 2026-11-02 | the owner reads it |

A closing paragraph.
"""


def upkeep(held=None, *, rule="rule three", **overrides):
    cells = {
        "register": REGISTER_PATH,
        "task": "Renew the third",
        "rule": rule,
        "cadence": "monthly",
        "last-done": "2026-10-03",
        "next-due": "2026-11-03",
        "reminds": "the owner reads it",
    }
    cells.update(overrides)
    argv = [part for key, value in cells.items() for part in (f"--{key}", value)]
    return drive(["write-upkeep", *argv], held=held)


def test_upkeep_adds_a_new_rule_after_the_last_row():
    result = upkeep({REGISTER_PATH: REGISTER})
    assert (result.code, result.out) == (0, "row written: rule three\n")
    new_row = (
        "| Renew the third | rule three | monthly | 2026-10-03 | 2026-11-03 "
        "| the owner reads it |\n"
    )
    assert result.files.held[REGISTER_PATH] == REGISTER.replace(
        "\n\nA closing", "\n" + new_row + "\nA closing"
    )


def test_upkeep_replaces_the_row_with_the_same_rule_where_it_stands():
    result = upkeep({REGISTER_PATH: REGISTER}, rule="rule one", **{"next-due": "2026-12-01"})
    assert (result.code, result.out) == (0, "row replaced: rule one\n")
    old_row = (
        "| Renew the first | rule one | monthly | 2026-10-01 | 2026-11-01 "
        "| the owner reads it |"
    )
    new_row = (
        "| Renew the third | rule one | monthly | 2026-10-03 | 2026-12-01 "
        "| the owner reads it |"
    )
    assert result.files.held[REGISTER_PATH] == REGISTER.replace(old_row, new_row)


def test_upkeep_creates_a_missing_register_with_its_fixed_lines():
    result = upkeep()
    assert (result.code, result.out) == (
        0, f"register created: {REGISTER_PATH}\nrow written: rule three\n"
    )
    assert result.files.held[REGISTER_PATH] == (
        "# Upkeep register\n\n"
        "The rule for this register, what it holds and what each row says, is "
        "`<CORE>/doctrine/setup/kensaiapp_structure.md` § App-level, at the `system/upkeep.md` "
        "entry.\n\n"
        f"{HEADER_ROW}\n{SEPARATOR_ROW}\n"
        "| Renew the third | rule three | monthly | 2026-10-03 | 2026-11-03 "
        "| the owner reads it |\n"
    )


def test_a_created_register_names_no_product_home_or_login():
    text = upkeep().files.held[REGISTER_PATH]
    for forbidden in ("products/", "/Users/", "/home/", "kensaiapp-"):
        assert forbidden not in text


def test_upkeep_escapes_a_pipe_and_keeps_six_cells():
    text = upkeep({REGISTER_PATH: REGISTER}, task="a|b").files.held[REGISTER_PATH]
    row = next(line for line in text.splitlines() if "rule three" in line)
    assert "| a\\|b |" in row
    assert len(re.split(r"(?<!\\)\|", row)) - 2 == 6


def test_upkeep_matches_a_row_by_its_rule_cell_as_written():
    register = REGISTER.replace("| rule two |", "| rule \\| two |")
    result = upkeep({REGISTER_PATH: register}, rule="rule | two")
    assert result.out == "row replaced: rule | two\n"
    assert result.files.held[REGISTER_PATH].count("rule \\| two") == 1


def test_upkeep_adds_after_the_separator_when_the_table_has_no_rows():
    register = f"# Upkeep register\n\n{HEADER_ROW}\n{SEPARATOR_ROW}\n\nafter\n"
    text = upkeep({REGISTER_PATH: register}).files.held[REGISTER_PATH]
    assert text == (
        f"# Upkeep register\n\n{HEADER_ROW}\n{SEPARATOR_ROW}\n"
        "| Renew the third | rule three | monthly | 2026-10-03 | 2026-11-03 "
        "| the owner reads it |\n"
        "\nafter\n"
    )


def test_upkeep_adds_to_a_table_that_ends_the_file_without_a_newline():
    register = (REGISTER.split("\n\nA closing")[0]).rstrip("\n")
    text = upkeep({REGISTER_PATH: register}).files.held[REGISTER_PATH]
    assert text.startswith(register + "\n| Renew the third | rule three |")


def test_upkeep_keeps_a_crlf_register_in_crlf():
    register = REGISTER.replace("\n", "\r\n")
    text = upkeep({REGISTER_PATH: register}).files.held[REGISTER_PATH]
    assert text.count("\n") == text.count("\r\n")


def test_upkeep_refuses_a_register_whose_header_differs():
    wrong = REGISTER.replace("Cadence", "Often")
    result = upkeep({REGISTER_PATH: wrong})
    assert result.code == 1 and result.out == ""
    assert f'{REGISTER_PATH} has no header row "{HEADER_ROW}".' in result.err
    assert result.files.held == {REGISTER_PATH: wrong}
    no_separator = REGISTER.replace(SEPARATOR_ROW, "no separator here")
    other = upkeep({REGISTER_PATH: no_separator})
    assert "the line after the header row is not the table's six-cell separator" in other.err
    assert other.files.held == {REGISTER_PATH: no_separator}


def test_upkeep_refuses_two_rows_already_matching_the_rule():
    doubled = REGISTER.replace("| rule two |", "| rule one |")
    result = upkeep({REGISTER_PATH: doubled}, rule="rule one")
    assert result.code == 1 and result.out == ""
    assert (
        f'{REGISTER_PATH} holds 2 rows whose "Rule it serves" cell is "rule one", so the tool '
        "cannot tell which one to replace."
    ) in result.err
    assert result.files.held == {REGISTER_PATH: doubled}


def test_upkeep_refuses_an_empty_value_and_a_value_with_a_line_break():
    empty = upkeep({REGISTER_PATH: REGISTER}, cadence="")
    assert empty.code == 1 and "--cadence is empty." in empty.err
    broken = upkeep({REGISTER_PATH: REGISTER}, reminds="two\nlines")
    assert broken.code == 1
    assert (
        "--reminds holds a line break, and a cell of the register must sit on one line."
        in broken.err
    )
    assert empty.files.reads == [] and broken.files.reads == []
    assert broken.files.held == {REGISTER_PATH: REGISTER} and broken.out == ""


# --- a file the tool cannot read or write (CP-1142) -------------------------------------------

UNREADABLE = "'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"
UNWRITABLE = "[Errno 13] Permission denied"


@pytest.mark.parametrize(
    "argv, path",
    [
        (["read-record", "--record", RECORD_PATH], RECORD_PATH),
        (["check-verdict", "--report", "r.md"], "r.md"),
        (["normalise", "--stdout", "audit-stdout.txt", "--stderr", "audit-stderr.txt"],
         "audit-stdout.txt"),
        (["find-lapsed", "--record", RECORD_PATH, "--list", "advisories.json"],
         "advisories.json"),
        (["write-record", "entry", "--record", RECORD_PATH, "--advisory", "GHSA-new",
          "--distribution", "jinja2", "--published", "2026-10-09", "--reason", "why"],
         RECORD_PATH),
        (["write-upkeep", "--register", "upkeep.md", "--task", "t", "--rule", "r",
          "--cadence", "c", "--last-done", "d", "--next-due", "n", "--reminds", "m"],
         "upkeep.md"),
    ],
)
def test_a_file_the_tool_cannot_read_is_refused_naming_it(argv, path):
    held = {"audit-stdout.txt": "", "audit-stderr.txt": "", "advisories.json": "[]"}
    result = drive(argv, held=held, failing_reads={path: UNREADABLE})
    assert result.code == 1
    assert result.out == ""
    assert result.err == f"security_bookkeeping: cannot read {path}: {UNREADABLE}\n"
    assert result.files.written == []


def test_a_record_write_that_cannot_land_is_refused_and_keeps_the_record():
    result = write_entry_failing({RECORD_PATH: ENTRY_A})
    assert result.code == 1
    assert result.out == ""
    assert result.err == f"security_bookkeeping: cannot write {RECORD_PATH}: {UNWRITABLE}\n"
    assert result.files.held == {RECORD_PATH: ENTRY_A}


def test_a_record_that_cannot_be_created_prints_no_confirmation():
    result = write_entry_failing(None)
    assert (result.code, result.out) == (1, "")
    assert "record created" not in result.err
    assert result.files.held == {}


def test_a_register_that_cannot_be_written_prints_no_confirmation():
    for held in (None, {REGISTER_PATH: REGISTER}):
        argv = ["write-upkeep", "--register", REGISTER_PATH, "--task", "t", "--rule", "r",
                "--cadence", "c", "--last-done", "d", "--next-due", "n", "--reminds", "m"]
        result = drive(argv, held=held, failing_writes={REGISTER_PATH: UNWRITABLE})
        assert (result.code, result.out) == (1, "")
        assert result.err == f"security_bookkeeping: cannot write {REGISTER_PATH}: {UNWRITABLE}\n"
        assert result.files.held == (held or {})


def write_entry_failing(held):
    argv = ["write-record", "entry", "--record", RECORD_PATH, "--advisory", "GHSA-new",
            "--distribution", "jinja2", "--published", "2026-10-09", "--reason", "why"]
    return drive(argv, held=held, failing_writes={RECORD_PATH: UNWRITABLE})


def test_a_record_on_disk_that_is_not_utf8_is_refused(tmp_path):
    # CP-1152: a file that is not valid TOML is refused; TOML is UTF-8, and a refusal is a
    # message on standard error, never a traceback (CP-1142).
    record = tmp_path / "advisory_exceptions.toml"
    record.write_bytes(b"\xff\xfe[[exception]]\n")
    bookkeeping = sb.Bookkeeping(
        files=sb.Files(), advisories=support.FakeAdvisories(), clock=support.FakeClock(TODAY)
    )
    out, err = io.StringIO(), io.StringIO()
    code = sb.run(["read-record", "--record", str(record)], bookkeeping=bookkeeping, stdout=out,
                  stderr=err)
    assert (code, out.getvalue()) == (1, "")
    assert err.getvalue().startswith(f"security_bookkeeping: cannot read {record}: ")
    assert err.getvalue().count("\n") == 1


# --- reading uv's audit text (task 8) ---------------------------------------------------------

JINJA2_BLOCK = """\
jinja2 3.1.2 has 2 known vulnerabilities:

- GHSA-cpwx-vrp4-4pq7: Jinja2 sandbox escape
  Fixed in: 3.1.6
  Advisory information: https://example.test/GHSA-cpwx-vrp4-4pq7

- PYSEC-2026-1471: Jinja2 sandbox escape
  Fixed in: 3.1.6
  Advisory information: https://example.test/PYSEC-2026-1471

"""
JINJA2_SUMMARY = "Found 2 known vulnerabilities and no adverse project statuses in 3 packages\n"


def printed(reading):
    return [(a.advisory, a.package, a.version, a.fixed) for a in reading.advisories]


def refusal_of(stdout, stderr):
    with pytest.raises(sb.BookkeepingRefusal) as raised:
        sb.parse_audit(stdout, stderr)
    return str(raised.value)


def test_parse_reads_two_aliases_under_one_heading_in_printed_order():
    reading = sb.parse_audit(JINJA2_BLOCK + JINJA2_SUMMARY, "")
    assert printed(reading) == [
        ("GHSA-cpwx-vrp4-4pq7", "jinja2", "3.1.2", "3.1.6"),
        ("PYSEC-2026-1471", "jinja2", "3.1.2", "3.1.6"),
    ]
    assert reading.adverse_statuses == 0


def test_parse_sets_fixed_to_none_when_no_fixed_in_line_is_printed():
    text = (
        "urllib3 1.26.5 has 2 known vulnerabilities:\n\n"
        "- GHSA-aaaa-bbbb-cccc: first\n"
        "  Advisory information: https://example.test/a\n\n"
        "- GHSA-dddd-eeee-ffff: second\n"
        "  Fixed in: 1.26.18\n"
        "  Advisory information: https://example.test/b\n\n"
        "Found 2 known vulnerabilities and no adverse project statuses in 3 packages\n"
    )
    reading = sb.parse_audit(text, "")
    assert printed(reading) == [
        ("GHSA-aaaa-bbbb-cccc", "urllib3", "1.26.5", None),
        ("GHSA-dddd-eeee-ffff", "urllib3", "1.26.5", "1.26.18"),
    ]


def test_parse_reads_advisories_under_two_headings_in_printed_order():
    text = (
        "alpha 1.0 has 1 known vulnerability:\n\n"
        "- GHSA-1111-1111-1111: one\n  Fixed in: 1.1\n\n"
        "beta 2.0 has 1 known vulnerability:\n\n"
        "- GHSA-2222-2222-2222: two\n  Fixed in: 2.1\n\n"
        "Found 2 known vulnerabilities and no adverse project statuses in 4 packages\n"
    )
    assert printed(sb.parse_audit(text, "")) == [
        ("GHSA-1111-1111-1111", "alpha", "1.0", "1.1"),
        ("GHSA-2222-2222-2222", "beta", "2.0", "2.1"),
    ]


def test_parse_reads_a_clean_summary_on_stderr_with_empty_stdout_as_no_advisories():
    reading = sb.parse_audit(
        "", "Found no known vulnerabilities and no adverse project statuses in 16 packages\n"
    )
    assert reading.advisories == ()
    assert reading.adverse_statuses == 0


@pytest.mark.parametrize(
    "summary, count, statuses",
    [
        ("Found 1 known vulnerability and no adverse project statuses in 1 package", 1, 0),
        ("Found 3 known vulnerabilities in 5 packages", 3, 0),
        ("Found 1 known vulnerability and 1 adverse project status in 2 packages", 1, 1),
    ],
)
def test_parse_reads_singular_and_plural_summaries(summary, count, statuses):
    advisories = "".join(
        f"pkg 1.0 has {count} known vulnerabilities:\n\n"
        + "".join(f"- GHSA-{n}{n}{n}{n}-xxxx-xxxx: t\n  Fixed in: 2.0\n\n" for n in range(count))
    )
    reading = sb.parse_audit(advisories + summary + "\n", "")
    assert len(reading.advisories) == count
    assert reading.adverse_statuses == statuses


def test_parse_reads_the_summary_whichever_stream_carries_it():
    reading = sb.parse_audit("", JINJA2_BLOCK + JINJA2_SUMMARY)
    assert len(reading.advisories) == 2


def test_parse_refuses_both_streams_empty():
    message = refusal_of("", "")
    assert message == "both audit output files are empty, so there is no audit output to read."
    assert refusal_of("\n  \n", "\n") == message


def test_parse_refuses_input_with_no_summary_line():
    message = refusal_of("some other tool's output\n", "")
    assert message == (
        'the audit output has no summary line "Found ... known vulnerabilities", so it cannot '
        "be read as a finished uv audit."
    )
    assert refusal_of(JINJA2_BLOCK, "") == message


def test_parse_refuses_a_count_mismatch_naming_both_counts():
    text = JINJA2_BLOCK + (
        "Found 3 known vulnerabilities and no adverse project statuses in 3 packages\n"
    )
    assert refusal_of(text, "") == (
        "the audit's summary counts 3 known vulnerabilities, and its output lists 2 advisories."
    )


def test_parse_refuses_a_summary_counting_none_beside_a_listed_advisory():
    text = JINJA2_BLOCK + (
        "Found no known vulnerabilities and no adverse project statuses in 3 packages\n"
    )
    assert refusal_of(text, "") == (
        "the audit's summary counts 0 known vulnerabilities, and its output lists 2 advisories."
    )


def test_parse_refuses_an_error_line_even_beside_advisories():
    error = "error: Failed to fetch https://example.test/advisories"
    assert refusal_of(JINJA2_BLOCK + JINJA2_SUMMARY, error + "\n") == (
        f"the audit printed an error, and the output of a failed audit is not read: {error}"
    )
    assert refusal_of(error + "\n", "").endswith(error)


def test_parse_never_reads_an_adverse_status_block_as_an_advisory():
    text = (
        "left-pad 1.0.0 has 1 known vulnerability:\n\n"
        "- GHSA-1111-2222-3333: bad\n  Fixed in: 1.0.1\n\n"
        "Adverse project statuses:\n\n"
        "old-lib 0.1 is deprecated:\n"
        "- the project is archived\n\n"
        "other-lib 0.2 is yanked:\n"
        "- the release was withdrawn\n\n"
        "Found 1 known vulnerability and 2 adverse project statuses in 3 packages\n"
    )
    reading = sb.parse_audit(text, "")
    assert printed(reading) == [("GHSA-1111-2222-3333", "left-pad", "1.0.0", "1.0.1")]
    assert reading.adverse_statuses == 2


# --- normalise (task 9) -----------------------------------------------------------------------

AUDIT_OUT = "audit-stdout.txt"
AUDIT_ERR = "audit-stderr.txt"
NORMALISE = ["normalise", "--stdout", AUDIT_OUT, "--stderr", AUDIT_ERR]
GHSA_ID = "GHSA-cpwx-vrp4-4pq7"
PYSEC_ID = "PYSEC-2026-1471"


def osv_record(*, published="2026-11-03T10:15:30Z", rating=None, vector=False, **extra):
    """The advisory data the service would send: a publication time, and optionally a named
    rating at database_specific.severity or a score vector at the top level."""
    record = {"id": "x", **extra}
    if published is not None:
        record["published"] = published
    if rating is not None:
        record["database_specific"] = {"severity": rating}
    if vector:
        record["severity"] = [{"type": "CVSS_V3", "score": "CVSS:3.1/AV:N/AC:L"}]
    return record


def jinja2_advisories(ghsa=None, pysec=None):
    advisories = support.FakeAdvisories()
    advisories.serve_record(GHSA_ID, ghsa if ghsa is not None else osv_record(rating="HIGH"))
    advisories.serve_record(
        PYSEC_ID, pysec if pysec is not None else osv_record(published="2026-11-04T00:00:00Z")
    )
    return advisories


def normalise(stdout_text, stderr_text, advisories=None, argv=None):
    return drive(
        argv or NORMALISE,
        held={AUDIT_OUT: stdout_text, AUDIT_ERR: stderr_text},
        advisories=advisories if advisories is not None else jinja2_advisories(),
    )


def test_normalise_prints_the_six_keys_for_the_jinja2_example():
    result = normalise(JINJA2_BLOCK + JINJA2_SUMMARY, "")
    assert result.code == 0
    assert result.err == ""
    assert json.loads(result.out) == [
        {
            "advisory": GHSA_ID, "package": "jinja2", "version": "3.1.2", "severity": "High",
            "fixed": "3.1.6", "published": "2026-11-03",
        },
        {
            "advisory": PYSEC_ID, "package": "jinja2", "version": "3.1.2",
            "severity": "unscored", "fixed": "3.1.6", "published": "2026-11-04",
        },
    ]
    assert list(json.loads(result.out)[0]) == list(sb.NORMALISED_KEYS)
    assert result.out.endswith("]\n") and result.out.startswith("[\n  {\n")


def test_normalise_maps_moderate_to_medium():
    advisories = jinja2_advisories(ghsa=osv_record(rating="MODERATE"))
    result = normalise(JINJA2_BLOCK + JINJA2_SUMMARY, "", advisories)
    assert json.loads(result.out)[0]["severity"] == "Medium"


@pytest.mark.parametrize(
    "rating, rank",
    [("CRITICAL", "Critical"), ("high", "High"), ("Medium", "Medium"), ("lOw", "Low")],
)
def test_normalise_maps_each_named_rating_without_regard_to_case(rating, rank):
    advisories = jinja2_advisories(ghsa=osv_record(rating=rating))
    result = normalise(JINJA2_BLOCK + JINJA2_SUMMARY, "", advisories)
    assert json.loads(result.out)[0]["severity"] == rank


def test_normalise_writes_unscored_only_when_the_data_carries_no_rating():
    advisories = jinja2_advisories(ghsa=osv_record(), pysec=osv_record(vector=False))
    result = normalise(JINJA2_BLOCK + JINJA2_SUMMARY, "", advisories)
    assert [item["severity"] for item in json.loads(result.out)] == ["unscored", "unscored"]


def test_normalise_refuses_an_unplaceable_rating_naming_the_advisory():
    advisories = jinja2_advisories(ghsa=osv_record(rating="URGENT"))
    result = normalise(JINJA2_BLOCK + JINJA2_SUMMARY, "", advisories)
    assert result.code == 1
    assert result.out == ""
    assert result.err == (
        f'security_bookkeeping: the published data rates {GHSA_ID} "URGENT", which the tool '
        "cannot place on Critical, High, Medium or Low.\n"
    )


def test_normalise_refuses_a_record_whose_only_rating_is_a_score_vector():
    advisories = jinja2_advisories(ghsa=osv_record(vector=True))
    result = normalise(JINJA2_BLOCK + JINJA2_SUMMARY, "", advisories)
    assert result.code == 1
    assert result.out == ""
    assert result.err == (
        f"security_bookkeeping: the published data rates {GHSA_ID} only by a score vector, and "
        "the tool does not turn a vector into Critical, High, Medium or Low.\n"
    )


def test_normalise_prefers_a_named_rating_over_a_score_vector():
    advisories = jinja2_advisories(ghsa=osv_record(rating="LOW", vector=True))
    result = normalise(JINJA2_BLOCK + JINJA2_SUMMARY, "", advisories)
    assert json.loads(result.out)[0]["severity"] == "Low"


def test_normalise_borrows_no_aliases_rating():
    advisories = jinja2_advisories(ghsa=osv_record(rating="CRITICAL", aliases=[PYSEC_ID]))
    result = normalise(JINJA2_BLOCK + JINJA2_SUMMARY, "", advisories)
    assert [item["severity"] for item in json.loads(result.out)] == ["Critical", "unscored"]


def test_normalise_refuses_an_unreadable_advisory_record_and_prints_no_array():
    advisories = jinja2_advisories()
    advisories.fail(PYSEC_ID, "HTTP Error 404: Not Found")
    result = normalise(JINJA2_BLOCK + JINJA2_SUMMARY, "", advisories)
    assert result.code == 1
    assert result.out == ""
    assert result.err == (
        f"security_bookkeeping: cannot read the published data for {PYSEC_ID}: "
        "HTTP Error 404: Not Found\n"
    )


@pytest.mark.parametrize(
    "published", [None, "", "2026-1", "not a date", "2026-02-30T00:00:00Z", 20261103]
)
def test_normalise_refuses_a_missing_or_malformed_published(published):
    advisories = jinja2_advisories(ghsa=osv_record(published=published, rating="HIGH"))
    result = normalise(JINJA2_BLOCK + JINJA2_SUMMARY, "", advisories)
    assert result.code == 1
    assert result.out == ""
    assert result.err == (
        f"security_bookkeeping: the published data for {GHSA_ID} carries no publication date "
        "the tool can read.\n"
    )


def test_normalise_prints_an_empty_array_for_a_clean_audit():
    clean = "Found no known vulnerabilities and no adverse project statuses in 16 packages\n"
    result = normalise("", clean)
    assert (result.code, result.out, result.err) == (0, "[]\n", "")
    assert result.advisories.fetched == []


@pytest.mark.parametrize(
    "stdout_text, stderr_text",
    [
        ("", ""),
        ("some other tool's output\n", ""),
        (JINJA2_BLOCK + "Found 3 known vulnerabilities in 3 packages\n", ""),
        (JINJA2_BLOCK + JINJA2_SUMMARY, "error: could not reach the advisory data\n"),
        ("", "error: could not reach the advisory data\n"),
    ],
)
def test_normalise_refuses_what_is_not_a_finished_audit_and_never_prints_an_empty_array(
    stdout_text, stderr_text
):
    result = normalise(stdout_text, stderr_text)
    assert result.code == 1
    assert result.out == ""
    assert result.err.startswith("security_bookkeeping: ")
    assert result.advisories.fetched == []


def test_normalise_refuses_a_stream_file_that_is_not_there():
    result = drive(NORMALISE, held={AUDIT_OUT: "x"})
    assert result.code == 1
    assert result.out == ""
    assert result.err == f"security_bookkeeping: there is no file at {AUDIT_ERR}.\n"


def test_normalise_notes_adverse_statuses_on_stderr_and_still_succeeds():
    text = (
        "left-pad 1.0.0 has 1 known vulnerability:\n\n"
        "- GHSA-1111-2222-3333: bad\n  Fixed in: 1.0.1\n\n"
        "old-lib 0.1 is deprecated:\n- archived\n\n"
        "other-lib 0.2 is yanked:\n- withdrawn\n\n"
        "Found 1 known vulnerability and 2 adverse project statuses in 3 packages\n"
    )
    advisories = support.FakeAdvisories()
    advisories.serve_record("GHSA-1111-2222-3333", osv_record(rating="LOW"))
    result = normalise(text, "", advisories)
    assert result.code == 0
    assert len(json.loads(result.out)) == 1
    assert result.err == (
        "security_bookkeeping: the audit reported 2 adverse project statuses. They are not "
        "advisories and are not in the list.\n"
    )


def test_normalise_notes_one_adverse_status_in_the_singular():
    clean = "Found no known vulnerabilities and 1 adverse project status in 4 packages\n"
    result = normalise("", clean)
    assert result.code == 0
    assert result.out == "[]\n"
    assert result.err == (
        "security_bookkeeping: the audit reported 1 adverse project status. It is not an "
        "advisory and is not in the list.\n"
    )


def test_normalise_fetches_one_id_once_when_it_is_printed_under_two_headings():
    text = (
        "alpha 1.0 has 1 known vulnerability:\n\n- GHSA-1111-2222-3333: one\n  Fixed in: 1.1\n\n"
        "beta 2.0 has 1 known vulnerability:\n\n- GHSA-1111-2222-3333: one\n  Fixed in: 2.1\n\n"
        "Found 2 known vulnerabilities and no adverse project statuses in 4 packages\n"
    )
    advisories = support.FakeAdvisories()
    advisories.serve_record("GHSA-1111-2222-3333", osv_record(rating="HIGH"))
    result = normalise(text, "", advisories)
    assert [item["package"] for item in json.loads(result.out)] == ["alpha", "beta"]
    assert advisories.fetched == ["GHSA-1111-2222-3333"]


def test_normalise_without_stderr_exits_2_with_nothing_on_stdout():
    result = drive(["normalise", "--stdout", AUDIT_OUT], held={AUDIT_OUT: "x"})
    assert result.code == 2
    assert result.out == ""
    assert "--stderr" in result.err


# --- normalise --from osv-scanner -------------------------------------------------------------

SCAN_OUT = "scan-stdout.json"
SCAN_ERR = "scan-stderr.txt"
SCAN_NORMALISE = ["normalise", "--from", "osv-scanner", "--stdout", SCAN_OUT, "--stderr", SCAN_ERR]
# The scanner's own progress lines, as a finished run prints them on standard error.
SCAN_PROGRESS = (
    "Starting filesystem walk for root: /\n"
    "Scanned uv.lock file and found 8 packages\n"
    "End status: 0 dirs visited, 1 inodes visited, 1 Extract calls\n"
)
SCAN_TRAILER = {"experimental_config": {"licenses": {"summary": False, "allowlist": None}}}
# A clean run of the installed scanner on this instance's `uv.lock`, standard output as printed.
CLEAN_SCAN = json.dumps({"results": [], **SCAN_TRAILER}, indent=2) + "\n"


def scan_vulnerability(advisory=GHSA_ID, *, fixed=("3.1.6",), affected_name="Jinja2", **extra):
    """One vulnerability as the scanner prints it: the id, its aliases, and one `affected` entry
    for `affected_name` whose range introduces at 0 and fixes in each of `fixed`."""
    events = [{"introduced": "0"}, *({"fixed": release} for release in fixed)]
    return {
        "id": advisory,
        "aliases": ["CVE-2026-0001"],
        "affected": [
            {
                "package": {"ecosystem": "PyPI", "name": affected_name},
                "ranges": [{"type": "ECOSYSTEM", "events": events}],
            }
        ],
        **extra,
    }


def scan_package(name="jinja2", version="3.1.2", vulnerabilities=(), **extra):
    return {
        "package": {"name": name, "version": version, "ecosystem": "PyPI"},
        "vulnerabilities": list(vulnerabilities),
        "groups": [{"ids": [vulnerability.get("id") for vulnerability in vulnerabilities]}],
        **extra,
    }


def scan_result(*packages):
    return {"source": {"path": "uv.lock", "type": "lockfile"}, "packages": list(packages)}


def scan_text(*results):
    return json.dumps({"results": list(results), **SCAN_TRAILER}, indent=2) + "\n"


def normalise_scan(stdout_text, stderr_text=SCAN_PROGRESS, advisories=None, argv=None):
    return drive(
        argv or SCAN_NORMALISE,
        held={SCAN_OUT: stdout_text, SCAN_ERR: stderr_text},
        advisories=advisories if advisories is not None else jinja2_advisories(),
    )


def test_a_clean_osv_scan_prints_an_empty_list_and_fetches_nothing():
    result = normalise_scan(CLEAN_SCAN)
    assert (result.code, result.out, result.err) == (0, "[]\n", "")
    assert result.advisories.fetched == []


def test_one_osv_advisory_prints_one_object_with_the_six_keys():
    scan = scan_text(scan_result(scan_package(vulnerabilities=[scan_vulnerability()])))
    result = normalise_scan(scan)
    assert (result.code, result.err) == (0, "")
    objects = json.loads(result.out)
    assert objects == [
        {
            "advisory": GHSA_ID, "package": "jinja2", "version": "3.1.2", "severity": "High",
            "fixed": "3.1.6", "published": "2026-11-03",
        }
    ]
    assert tuple(objects[0]) == sb.NORMALISED_KEYS
    assert result.advisories.fetched == [GHSA_ID]


def test_one_id_under_two_packages_gives_two_objects_and_one_fetch():
    scan = scan_text(
        scan_result(
            scan_package("alpha", "1.0.0", [scan_vulnerability(GHSA_ID, affected_name="alpha")]),
            scan_package("beta", "2.0.0", [scan_vulnerability(GHSA_ID, affected_name="beta")]),
        )
    )
    result = normalise_scan(scan)
    assert [(item["advisory"], item["package"]) for item in json.loads(result.out)] == [
        (GHSA_ID, "alpha"), (GHSA_ID, "beta"),
    ]
    assert result.advisories.fetched == [GHSA_ID]


def test_the_same_id_package_and_version_under_two_results_gives_one_object():
    both = [scan_vulnerability(GHSA_ID), scan_vulnerability(PYSEC_ID)]
    first = scan_package(vulnerabilities=both)
    second = scan_package(vulnerabilities=list(reversed(both)))
    result = normalise_scan(scan_text(scan_result(first), scan_result(second)))
    assert [item["advisory"] for item in json.loads(result.out)] == [GHSA_ID, PYSEC_ID]
    assert result.advisories.fetched == [GHSA_ID, PYSEC_ID]


def test_the_same_id_and_package_at_two_versions_gives_two_objects():
    scan = scan_text(
        scan_result(
            scan_package("jinja2", "3.1.2", [scan_vulnerability()]),
            scan_package("jinja2", "3.0.0", [scan_vulnerability()]),
        )
    )
    assert [item["version"] for item in json.loads(normalise_scan(scan).out)] == ["3.1.2", "3.0.0"]


def test_a_vulnerability_with_no_fixed_event_gives_null_fixed():
    unfixed = scan_vulnerability(fixed=())
    result = normalise_scan(scan_text(scan_result(scan_package(vulnerabilities=[unfixed]))))
    assert json.loads(result.out)[0]["fixed"] is None
    no_affected = {"id": GHSA_ID}
    result = normalise_scan(scan_text(scan_result(scan_package(vulnerabilities=[no_affected]))))
    assert json.loads(result.out)[0]["fixed"] is None


def test_the_fixed_releases_of_the_package_are_joined_in_data_order_without_repeats():
    vulnerability = scan_vulnerability(fixed=("3.1.6", "3.0.4", "3.1.6"))
    result = normalise_scan(scan_text(scan_result(scan_package(vulnerabilities=[vulnerability]))))
    assert json.loads(result.out)[0]["fixed"] == "3.1.6, 3.0.4"


def test_an_affected_entry_for_another_package_adds_no_fixed_release():
    vulnerability = scan_vulnerability(fixed=("9.9.9",), affected_name="markupsafe")
    result = normalise_scan(scan_text(scan_result(scan_package(vulnerabilities=[vulnerability]))))
    assert json.loads(result.out)[0]["fixed"] is None


@pytest.mark.parametrize(
    "affected_name, package_name",
    [("Jinja2", "jinja2"), ("zope.interface", "zope-interface"), ("My__Pkg", "my-pkg")],
)
def test_package_names_compare_after_pep_503_normalisation(affected_name, package_name):
    vulnerability = scan_vulnerability(fixed=("1.2.3",), affected_name=affected_name)
    package = scan_package(package_name, "1.0.0", [vulnerability])
    result = normalise_scan(scan_text(scan_result(package)))
    assert json.loads(result.out)[0]["fixed"] == "1.2.3"


def test_a_package_with_no_vulnerabilities_adds_no_object():
    quiet = scan_package("markupsafe", "3.0.0", [])
    loud = scan_package(vulnerabilities=[scan_vulnerability()])
    result = normalise_scan(scan_text(scan_result(quiet, loud)))
    assert [item["package"] for item in json.loads(result.out)] == ["jinja2"]
    only_quiet = normalise_scan(scan_text(scan_result(quiet)))
    assert (only_quiet.code, only_quiet.out) == (0, "[]\n")


def test_unread_fields_are_ignored():
    plain = scan_package(vulnerabilities=[scan_vulnerability()])
    noisy = scan_package(
        vulnerabilities=[
            scan_vulnerability(
                aliases=["CVE-1", "PYSEC-2"], summary="a summary", database_specific={"x": 1}
            )
        ],
        groups=[{"ids": ["unrelated"], "aliases": ["also-unrelated"], "max_severity": "9.9"}],
        licenses=["MIT"],
    )
    quiet = normalise_scan(scan_text(scan_result(plain)))
    loud = normalise_scan(scan_text(scan_result(noisy)))
    assert loud.out == quiet.out
    assert loud.advisories.fetched == quiet.advisories.fetched == [GHSA_ID]


def test_an_unplaceable_a_vector_only_and_an_unreadable_record_are_refused_on_this_path():
    scan = scan_text(scan_result(scan_package(vulnerabilities=[scan_vulnerability()])))
    cases = {
        "unplaceable": (
            jinja2_advisories(ghsa=osv_record(rating="SEVERE")),
            f'the published data rates {GHSA_ID} "SEVERE"',
        ),
        "vector only": (
            jinja2_advisories(ghsa=osv_record(vector=True)),
            f"the published data rates {GHSA_ID} only by a score vector",
        ),
        "unreadable": (
            jinja2_advisories(ghsa=osv_record(published=None)),
            f"the published data for {GHSA_ID} carries no publication date",
        ),
    }
    for name, (advisories, fragment) in cases.items():
        result = normalise_scan(scan, advisories=advisories)
        assert (result.code, result.out) == (1, ""), name
        assert result.err.startswith("security_bookkeeping: ") and fragment in result.err, name
    unreadable = support.FakeAdvisories()
    unreadable.fail(GHSA_ID, "HTTP Error 503: Service Unavailable")
    result = normalise_scan(scan, advisories=unreadable)
    assert (result.code, result.out) == (1, "")
    assert f"cannot read the published data for {GHSA_ID}" in result.err


SCAN_REFUSAL_PREFIX = "security_bookkeeping: "
GOOD_VULNERABILITY = scan_vulnerability()
A_PACKAGE = scan_package(vulnerabilities=[GOOD_VULNERABILITY])
TWO_VULNERABILITIES_SECOND_WITHOUT_ID = scan_package(
    vulnerabilities=[GOOD_VULNERABILITY, {"id": 5}]
)
NO_STDERR = object()


@pytest.mark.parametrize(
    "stdout_text, stderr_text, message",
    [
        ("", "", "the scan's standard output is empty, so there is no osv-scanner scan to read."),
        ("", SCAN_PROGRESS, "the scan's standard output is empty, so there is no osv-scanner"),
        ("some other tool's output\n", SCAN_PROGRESS, "the scan's standard output is not JSON,"),
        (
            scan_text(scan_result(A_PACKAGE))[:60], SCAN_PROGRESS,
            "the scan's standard output is not JSON,",
        ),
        ("[]\n", SCAN_PROGRESS, 'is not a JSON object with a "results" list,'),
        ("{}\n", SCAN_PROGRESS, 'is not a JSON object with a "results" list,'),
        ('{"results": {}}\n', SCAN_PROGRESS, 'is not a JSON object with a "results" list,'),
        (
            json.dumps({"results": [{"source": {}}]}), SCAN_PROGRESS,
            'result 1 of the scan has no "packages" list,',
        ),
        (
            json.dumps({"results": [scan_result(), {"packages": "none"}]}), SCAN_PROGRESS,
            'result 2 of the scan has no "packages" list,',
        ),
        (
            json.dumps({"results": [scan_result({"package": {"version": "1.0.0"}})]}),
            SCAN_PROGRESS,
            "package 1 of result 1 does not give the package's name and version as text,",
        ),
        (
            json.dumps({"results": [scan_result(A_PACKAGE, {"package": {"name": "x"}})]}),
            SCAN_PROGRESS,
            "package 2 of result 1 does not give the package's name and version as text,",
        ),
        (
            json.dumps({"results": [scan_result({"package": {"name": 7, "version": "1"}})]}),
            SCAN_PROGRESS,
            "package 1 of result 1 does not give the package's name and version as text,",
        ),
        (
            json.dumps({"results": [scan_result({"package": {"name": "x", "version": "1"}})]}),
            SCAN_PROGRESS,
            'package 1 of result 1 has no "vulnerabilities" list,',
        ),
        (
            json.dumps({"results": [scan_result(scan_package(vulnerabilities=[{"aliases": []}]))]}),
            SCAN_PROGRESS,
            'vulnerability 1 of package 1 in result 1 has no "id" as text,',
        ),
        (
            json.dumps({"results": [scan_result(TWO_VULNERABILITIES_SECOND_WITHOUT_ID)]}),
            SCAN_PROGRESS,
            'vulnerability 2 of package 1 in result 1 has no "id" as text,',
        ),
        (scan_text(scan_result(A_PACKAGE)), NO_STDERR, f"there is no file at {SCAN_ERR}."),
    ],
)
def test_output_that_is_not_a_finished_scan_is_refused(stdout_text, stderr_text, message):
    held = {SCAN_OUT: stdout_text}
    if stderr_text is not NO_STDERR:
        held[SCAN_ERR] = stderr_text
    result = drive(SCAN_NORMALISE, held=held, advisories=jinja2_advisories())
    assert result.code == 1
    assert result.out == ""
    assert result.err.startswith(SCAN_REFUSAL_PREFIX) and result.err.endswith("\n")
    assert result.err.count("\n") == 1
    assert message in result.err
    assert result.advisories.fetched == []


@pytest.mark.parametrize(
    "affected",
    ["a string", {"package": {"name": "jinja2"}}, ["not an object"], [{"ranges": "none"}],
     [{"package": "jinja2"}], [{"ranges": ["not an object"]}], [{"ranges": [{"events": "none"}]}],
     [{"ranges": [{"events": ["not an object"]}]}], [{"ranges": [{"events": [{"fixed": 3}]}]}]],
)
def test_affected_data_in_another_shape_is_refused_naming_where_it_sits(affected):
    vulnerability = {"id": GHSA_ID, "affected": affected}
    result = normalise_scan(scan_text(scan_result(scan_package(vulnerabilities=[vulnerability]))))
    assert result.code == 1
    assert result.out == ""
    assert (
        'vulnerability 1 of package 1 in result 1 has "affected" data the tool cannot read, '
        "so the output cannot be read as a finished osv-scanner scan." in result.err
    )
    assert result.advisories.fetched == []


def test_from_uv_audit_prints_what_the_call_without_from_prints():
    held = {AUDIT_OUT: JINJA2_BLOCK + JINJA2_SUMMARY, AUDIT_ERR: ""}
    plain = drive(NORMALISE, held=held, advisories=jinja2_advisories())
    named = drive(["normalise", "--from", "uv-audit", *NORMALISE[1:]], held=held,
                  advisories=jinja2_advisories())
    assert (plain.code, named.code) == (0, 0)
    assert named.out == plain.out != ""
    assert named.err == plain.err


def test_a_scan_is_not_read_as_a_uv_audit_and_an_audit_is_not_read_as_a_scan():
    as_audit = drive(NORMALISE, held={AUDIT_OUT: CLEAN_SCAN, AUDIT_ERR: SCAN_PROGRESS})
    assert (as_audit.code, as_audit.out) == (1, "")
    as_scan = drive(
        ["normalise", "--from", "osv-scanner", "--stdout", AUDIT_OUT, "--stderr", AUDIT_ERR],
        held={AUDIT_OUT: JINJA2_BLOCK + JINJA2_SUMMARY, AUDIT_ERR: ""},
    )
    assert (as_scan.code, as_scan.out) == (1, "")


def test_an_unknown_reader_exits_2_with_empty_stdout():
    result = drive(
        ["normalise", "--from", "bogus", "--stdout", SCAN_OUT, "--stderr", SCAN_ERR],
        held={SCAN_OUT: CLEAN_SCAN, SCAN_ERR: SCAN_PROGRESS},
    )
    assert result.code == 2
    assert result.out == ""
    assert "--from" in result.err and "bogus" in result.err
    assert result.advisories.fetched == []


# --- the surface and the tool-wide guards (task 10) -------------------------------------------

SEVEN_SUBCOMMANDS = (
    "normalise", "lapse-date", "read-record", "write-record", "find-lapsed", "write-upkeep",
    "check-verdict",
)


def test_the_parser_lists_exactly_seven_subcommands_each_naming_its_job():
    assert sorted(subcommand.name for subcommand in sb.SUBCOMMANDS) == sorted(SEVEN_SUBCOMMANDS)
    listing = " ".join(drive(["--help"]).out.split())
    for subcommand in sb.SUBCOMMANDS:
        assert subcommand.help.strip()
        assert f"{subcommand.name} {subcommand.help}" in listing
    assert drive(["bogus-subcommand"]).code == 2
    forms = " ".join(drive(["write-record", "--help"]).out.split())
    assert "entry add an entry" in forms and "renewal add a renewal" in forms


def _collapsed_help(form):
    result = drive(["write-record", form, "--help"])
    assert (result.code, result.err) == (0, "")
    return " ".join(result.out.split())


def test_the_renewal_help_does_not_say_a_record_is_created():
    text = _collapsed_help("renewal")
    assert "is created" not in text
    assert "the record's path; it must already hold the advisory's entry" in text


def test_the_entry_help_still_says_a_missing_record_is_created():
    text = _collapsed_help("entry")
    assert "a missing file is created with the entry" in text


def test_the_normalise_help_and_the_tool_description_name_both_readers():
    result = drive(["normalise", "--help"])
    assert (result.code, result.err) == (0, "")
    help_text = " ".join(result.out.split())
    assert "--from {uv-audit,osv-scanner}" in help_text
    assert "(default: uv-audit)" in help_text
    for reader in ("uv's audit", "osv-scanner"):
        assert reader in sb.TOOL_DESCRIPTION, reader


def test_the_tool_source_names_no_provider_model_or_agent():
    source = Path(__file__).with_name("security_bookkeeping.py").read_text(encoding="utf-8")
    assert re.search(r"claude|codex|anthropic|openai", source, re.IGNORECASE) is None


GUARD_RECORD = (
    '[[exception]]\nadvisory = "GHSA-aaaa"\ndistribution = "jinja2"\n'
    'published = 2026-11-03\nreason = "the product calls it only in a test"\n'
)
GUARD_LISTING = json.dumps([listed(advisory="GHSA-aaaa", published="2026-11-03")])
GUARD_REGISTER = f"# Upkeep register\n\n{HEADER_ROW}\n{SEPARATOR_ROW}\n"
GUARD_AUDIT = "Found no known vulnerabilities and 1 adverse project status in 4 packages\n"
ANSWER_WORDS = re.compile(
    r"\bfix\b|exception|question|report for the PM|\breached\b|not reached", re.IGNORECASE
)
GUARD_CASES = {
    "normalise": (NORMALISE, {AUDIT_OUT: "", AUDIT_ERR: GUARD_AUDIT}),
    "normalise osv-scanner": (SCAN_NORMALISE, {SCAN_OUT: CLEAN_SCAN, SCAN_ERR: SCAN_PROGRESS}),
    # `lapse-date` takes one object of the list, not the list.
    "lapse-date": (["lapse-date", "--entry", GUARD_LISTING[1:-1]], {}),
    "read-record": (["read-record", "--record", RECORD_PATH], {RECORD_PATH: GUARD_RECORD}),
    "write-record entry": (
        ["write-record", "entry", "--record", RECORD_PATH, "--advisory", "GHSA-bbbb",
         "--distribution", "jinja2", "--published", "2026-11-04", "--reason", "a stated reason"],
        {RECORD_PATH: GUARD_RECORD},
    ),
    "write-record renewal": (
        ["write-record", "renewal", "--record", RECORD_PATH, "--advisory", "GHSA-aaaa",
         "--on", "2026-11-09", "--reason", "a stated reason"],
        {RECORD_PATH: GUARD_RECORD},
    ),
    "find-lapsed": (
        ["find-lapsed", "--record", RECORD_PATH, "--list", LIST_PATH, "--date", "2026-11-20"],
        {RECORD_PATH: GUARD_RECORD, LIST_PATH: GUARD_LISTING},
    ),
    "write-upkeep": (
        ["write-upkeep", "--register", REGISTER_PATH, "--task", "Read the audit",
         "--rule", "the audit rule", "--cadence", "weekly", "--last-done", "2026-11-03",
         "--next-due", "2026-11-10", "--reminds", "the owner reads it"],
        {REGISTER_PATH: GUARD_REGISTER},
    ),
    "check-verdict": (
        ["check-verdict", "--report", "r.md"], report_with("Security: clean"),
    ),
}


@pytest.mark.parametrize("name", sorted(GUARD_CASES))
def test_no_subcommand_output_gives_an_advisory_an_answer(name):
    argv, held = GUARD_CASES[name]
    result = drive(argv, held=held)
    assert result.code == 0, result.err
    for line in (result.out + result.err).splitlines():
        # normalise's `fixed` key is a release field, and \bfix\b does not match it.
        assert ANSWER_WORDS.search(line) is None, line


def test_the_guard_cases_cover_every_subcommand():
    assert {name.split()[0] for name in GUARD_CASES} == set(SEVEN_SUBCOMMANDS)


def test_main_runs_a_job_through_the_real_ports(tmp_path, capsys):
    report = tmp_path / "report.md"
    report.write_text("# Security report\n\nRepair: merged\n\nThe rest.\n", encoding="utf-8")
    assert sb.main(["check-verdict", "--report", str(report)]) == 0
    captured = capsys.readouterr()
    assert captured.out == "Repair: merged\n"
    assert captured.err == ""


def test_main_turns_a_refusal_into_status_1_on_the_real_streams(tmp_path, capsys):
    missing = tmp_path / "nothing.md"
    assert sb.main(["check-verdict", "--report", str(missing)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"security_bookkeeping: there is no file at {missing}.\n"


def test_the_tool_runs_as_a_script(tmp_path):
    report = tmp_path / "report.md"
    report.write_text("# Security report\n\nSecurity: fixed\n", encoding="utf-8")
    script = Path(__file__).with_name("security_bookkeeping.py")
    finished = subprocess.run(
        [sys.executable, "-I", str(script), "check-verdict", "--report", str(report)],
        capture_output=True, text=True, check=False,
    )
    assert (finished.returncode, finished.stdout, finished.stderr) == (0, "Security: fixed\n", "")


# --- the text that calls the tool (tasks 11 to 13) --------------------------------------------

CORE_ROOT = Path(__file__).resolve().parents[1]
REPAIR_PROMPT = CORE_ROOT / "prompts" / "senior_engineer_repair_dependencies.md"
LOCKED_CALL = '"<CORE>/tools/locked_python.sh" "<CORE>/tools/security_bookkeeping.py"'


def committed_text(path):
    """A committed file's text with each run of whitespace made one space, so a sentence the
    file wraps is still found whole."""
    return " ".join(path.read_text(encoding="utf-8").split())


def test_the_prompt_names_the_tool_and_every_subcommand_the_parser_lists():
    text = committed_text(REPAIR_PROMPT)
    assert "security_bookkeeping" in text
    for subcommand in sb.SUBCOMMANDS:
        assert f"`{subcommand.name}`" in text or f"`{subcommand.name} " in text, subcommand.name


def test_the_prompt_calls_the_tool_only_through_the_locked_runner():
    calls = re.findall(r"^.*security_bookkeeping\.py.*$", REPAIR_PROMPT.read_text(), re.MULTILINE)
    assert calls
    assert all(call.startswith(LOCKED_CALL) for call in calls)
    assert "```sh invocation" not in REPAIR_PROMPT.read_text()


def test_the_prompt_no_longer_tells_the_model_to_compute_a_window_date():
    text = committed_text(REPAIR_PROMPT)
    assert "The window is a date you compute" not in text
    assert "The tool computes the lapse date" in text


def test_the_prompt_keeps_the_default_window_as_the_owners_ruling():
    text = committed_text(REPAIR_PROMPT)
    assert "**7 days for a Critical or unscored advisory**" in text
    assert "**30 days for a High one**" in text
    assert '"30 days for Medium and Low is fine"' in text


def test_the_prompt_sends_a_refusal_to_the_report_not_to_hand_work():
    text = committed_text(REPAIR_PROMPT)
    assert "**When the tool refuses, write nothing by hand for that job.**" in text
    assert "the report raises the refusal for the PM, quoting the tool's standard error" in text
    assert "A refusal from `normalise` is reported the way a command that cannot run is" in text


SKILLS_ROOT = CORE_ROOT.parent / "skills" / "senior-engineer" / ".claude" / "skills"
SECURITY_SKILL_TEXT = SKILLS_ROOT / "development-security" / "SKILL.md"


def fenced_blocks(path):
    """Each fenced block of the file as `(tag, body)`, the tag being the words after the fence."""
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks, opened = [], None
    for line in lines:
        if opened is None and line.startswith("```"):
            opened = (line[3:].strip(), [])
        elif opened is not None and line.startswith("```"):
            blocks.append((opened[0], "\n".join(opened[1])))
            opened = None
        elif opened is not None:
            opened[1].append(line)
    return blocks


def tool_blocks(path):
    return [(tag, body) for tag, body in fenced_blocks(path) if "security_bookkeeping.py" in body]


def test_development_security_names_the_tool_and_check_verdict():
    text = committed_text(SECURITY_SKILL_TEXT)
    assert "security_bookkeeping" in text
    assert "check-verdict" in text
    for subcommand in ("normalise", "find-lapsed", "lapse-date", "write-record", "write-upkeep"):
        assert f"`{subcommand}`" in text or f"`{subcommand} " in text, subcommand


def test_development_security_names_all_three_scanners():
    # Replaces `..._names_no_other_scanner`, whose assertion (SKILL.md names none of the three)
    # the owner's ruling of 2026-11-06 ended; this states its opposite.
    text = SECURITY_SKILL_TEXT.read_text(encoding="utf-8").lower()
    for scanner in ("osv-scanner", "semgrep", "gitleaks"):
        assert scanner in text, scanner


def test_development_security_still_holds_only_the_invocation_block_tag():
    tags = [tag for tag, _body in fenced_blocks(SECURITY_SKILL_TEXT)]
    assert tags.count("sh invocation") == 1
    assert tool_blocks(SECURITY_SKILL_TEXT)
    assert all(tag == "sh" for tag, _body in tool_blocks(SECURITY_SKILL_TEXT))
    text = committed_text(SECURITY_SKILL_TEXT)
    assert "into the report as a bullet, never as a bare line" in text
    assert "A red or refused run means the change it was proving" in text


def test_development_security_calls_the_tool_only_through_the_locked_runner():
    calls = re.findall(r"^.*security_bookkeeping\.py.*$", SECURITY_SKILL_TEXT.read_text(), re.M)
    assert calls
    assert all(call.startswith(LOCKED_CALL) for call in calls)


def test_development_security_checks_the_verdict_before_the_report_commit():
    text = SECURITY_SKILL_TEXT.read_text(encoding="utf-8")
    step_four = text[text.index("### 4."):text.index("### The suite")]
    assert step_four.index("check-verdict") < step_four.index("the `report` row")
    assert "is never committed with a verdict line the tool refuses" in " ".join(step_four.split())


def test_development_security_removes_its_scratch_folder_in_a_command_of_its_own():
    text = committed_text(SECURITY_SKILL_TEXT)
    assert "`mktemp -d`" in text
    assert '`rm -rf "<scratch>"`' in text or '(`rm -rf "<scratch>"`' in text


REPORT_SHAPE_TAG = "markdown"


def report_block():
    """The report shape `SKILL.md` gives: the one fenced block tagged `markdown`."""
    bodies = [body for tag, body in fenced_blocks(SECURITY_SKILL_TEXT) if tag == REPORT_SHAPE_TAG]
    assert len(bodies) == 1
    return bodies[0]


def test_the_report_block_holds_the_scanners_section_right_after_the_dependency_audit():
    block = report_block()
    headings = [line for line in block.splitlines() if line.startswith("## ")]
    assert headings.index("## Scanners") == headings.index("## Dependency audit") + 1
    heads = [block.index(head) for head in ("- osv-scanner: ", "- Semgrep CE: ", "- gitleaks: ")]
    assert heads == sorted(heads)
    collapsed = " ".join(block.split())
    for form in ("found nothing", "found no dependency set to scan", "did not run — "):
        assert form in collapsed, form


def test_the_advisories_header_carries_the_reporter_column():
    header = "| Advisory | Dependency | Reported by | Answer | What was done | Commit |"
    assert header in report_block()


def sh_blocks_naming(command):
    return [body for tag, body in fenced_blocks(SECURITY_SKILL_TEXT)
            if tag == "sh" and command in body]


def test_the_gitleaks_command_redacts():
    blocks = sh_blocks_naming("gitleaks dir ")
    assert blocks
    assert all("--redact" in block for block in blocks)


def test_the_osv_scanner_command_names_each_lockfile_and_normalise_passes_from():
    scans = sh_blocks_naming("osv-scanner scan source")
    assert scans
    assert all("--format json" in block and '--lockfile "<file>"' in block for block in scans)
    assert all("--recursive" not in block and " -r " not in block for block in scans)
    reads = sh_blocks_naming("security_bookkeeping.py")
    assert any("normalise --from osv-scanner" in block for block in reads)


def test_the_semgrep_command_is_the_one_that_needs_no_account():
    scans = sh_blocks_naming("semgrep scan")
    assert scans
    assert all("--config p/default" in block and "--metrics=off" in block for block in scans)
    for tag, body in fenced_blocks(SECURITY_SKILL_TEXT):
        assert "semgrep ci" not in body and "semgrep login" not in body


def test_the_verdict_table_names_a_scanner_that_did_not_run_and_clears_osv_scanner():
    rows = [line for line in SECURITY_SKILL_TEXT.read_text(encoding="utf-8").splitlines()
            if line.startswith("| `reported` |")]
    assert len(rows) == 1
    row = " ".join(rows[0].split())
    assert "a scanner that did not run" in row
    assert "`osv-scanner` is not an audit the NFDR does not name" in row


def test_the_skill_text_carries_the_scanner_rules_beyond_the_report_shape():
    text = committed_text(SECURITY_SKILL_TEXT)
    for anchor in (
        "**Run the three scanners on every run**",
        "**Answer `osv-scanner`'s advisories as the audit's**",
        "**A Semgrep or `gitleaks` finding is a candidate**",
        "**Never show a secret**",
        "**None named** → note it for the report. `osv-scanner` still runs (item 3).",
        "First run Semgrep CE and `gitleaks`",
        "`osv-scanner` running on every run is this skill's own departure",
        "a scanner that cannot run, a hole",
        "<tool> did not run: <why>.",
        "an audit that was skipped or could not run, a scanner that did not run",
    ):
        assert anchor in text, anchor


def scanners_bullets():
    """The lines of the report block's `## Scanners` section that open a bullet."""
    lines = report_block().splitlines()
    start = lines.index("## Scanners") + 1
    end = next(at for at in range(start, len(lines)) if lines[at].startswith("## "))
    return [line for line in lines[start:end] if line.startswith("- ")]


def test_the_scanners_section_holds_exactly_the_three_bullets():
    assert [line.split(":")[0] for line in scanners_bullets()] == [
        "- osv-scanner", "- Semgrep CE", "- gitleaks",
    ]


def test_the_scanners_section_gives_the_counted_form_and_names_where_the_counted_ones_are():
    collapsed = " ".join(report_block().split())
    for form in (
        '"<n> findings, <k> counted"',
        "listed in `## Advisories`",
        "listed in `## Holes in the code`",
        "A gitleaks finding is named by file, line and rule id, never by what it matched",
    ):
        assert form in collapsed, form


def test_the_skill_runs_osv_scanner_beside_the_audit_and_answers_one_id_once():
    text = committed_text(SECURITY_SKILL_TEXT)
    for anchor in (
        "beside the NFDR's audit and never in place of it",
        "One advisory id against one package takes one answer, even when both lists hold it",
    ):
        assert anchor in text, anchor


def test_semgrep_and_gitleaks_read_the_product_path_and_every_touched_file():
    assert all('"<product path>" "<touched file>"' in block
               for block in sh_blocks_naming("semgrep scan"))
    once_for_each = (
        "Run `gitleaks` once for each path: the product path, and each touched file outside it"
    )
    assert once_for_each in committed_text(SECURITY_SKILL_TEXT)


def test_no_line_of_the_skill_naming_a_scanner_names_a_provider():
    lines = [line for line in SECURITY_SKILL_TEXT.read_text(encoding="utf-8").splitlines()
             if any(scanner in line.lower() for scanner in THE_THREE_SCANNERS)]
    assert lines
    assert [line for line in lines if re.search(r"claude|codex", line, re.IGNORECASE)] == []


def test_the_skill_description_names_the_scanners_and_holds_no_colon_before_a_space():
    text = SECURITY_SKILL_TEXT.read_text(encoding="utf-8")
    frontmatter = text.split("---")[1]
    description = frontmatter[frontmatter.index("description:"):frontmatter.index("when_to_use:")]
    assert ": " not in description[len("description:"):]
    for scanner in ("osv-scanner", "Semgrep CE", "gitleaks"):
        assert scanner in description, scanner


SECURITY_PROMPT_TEXT = SKILLS_ROOT / "development-security" / "prompts" / "rich.md"
SCANNERS_HEADING = "## The three scanners"
THE_THREE_SCANNERS = ("osv-scanner", "semgrep", "gitleaks")


def scanners_section():
    """The `## The three scanners` section of `rich.md`, whitespace collapsed, up to the next
    second-level heading."""
    text = SECURITY_PROMPT_TEXT.read_text(encoding="utf-8")
    assert SCANNERS_HEADING in text
    start = text.index(SCANNERS_HEADING)
    end = text.find("\n## ", start + len(SCANNERS_HEADING))
    return " ".join(text[start:end if end != -1 else len(text)].split())


def test_rich_md_names_the_three_scanners():
    text = SECURITY_PROMPT_TEXT.read_text(encoding="utf-8").lower()
    for scanner in THE_THREE_SCANNERS:
        assert scanner in text, scanner


def test_rich_md_holds_the_scanners_section_and_it_names_no_provider():
    section = scanners_section()
    assert re.search(r"claude|codex", section, re.IGNORECASE) is None


def test_rich_md_names_the_2026_11_06_ruling_as_the_departure():
    assert "2026-11-06" in scanners_section()


SCANNER_RULE_ANCHORS = (
    "All three run whether or not the NFDR names a dependency audit",
    "they run the same way on every provider",
    "Each is a program the run starts from the shell",
    "the same four answers, in the same order",
    "excepted through `lapse-date`, `write-record entry` and `write-upkeep`",
    "it takes one answer",
    "Where the NFDR names no audit, `osv-scanner`'s advisories are the ones answered",
    "the report still says that the NFDR names no dependency audit",
    "proved by the search the shared file's answer 2 asks for",
    "only at the floor of 8 or above",
    "No finding is counted, fixed, excepted or dropped only because a scanner reported it",
    "None of them needs an account, a login, a token or a paid tier",
    "Semgrep runs as its community edition",
    "none that belongs to another product in the same repository",
    "every file the change's diff touches",
    "No line of the report quotes the matched text",
    "A scanner that cannot run is not a stop",
    "A run where all three found nothing, and nothing else is left, is `clean`",
    "that is a result, not a failed run",
)


@pytest.mark.parametrize("anchor", SCANNER_RULE_ANCHORS)
def test_rich_md_carries_the_anchors_the_scanner_rules_need(anchor):
    assert anchor in scanners_section()


REPAIR_SKILL_TEXT = SKILLS_ROOT / "dependency-repair" / "SKILL.md"


def test_dependency_repair_names_the_tool_and_check_verdict():
    text = committed_text(REPAIR_SKILL_TEXT)
    assert "security_bookkeeping" in text
    assert "check-verdict" in text
    for subcommand in ("normalise", "find-lapsed", "lapse-date", "write-record", "write-upkeep"):
        assert f"`{subcommand}`" in text or f"`{subcommand} " in text, subcommand


def test_dependency_repair_keeps_its_verdict_words():
    text = committed_text(REPAIR_SKILL_TEXT)
    for word in ("unmerged", "stopped", "merged", "nothing-to-repair"):
        assert word in text, word


def test_dependency_repair_calls_the_tool_only_through_the_locked_runner():
    calls = re.findall(r"^.*security_bookkeeping\.py.*$", REPAIR_SKILL_TEXT.read_text(), re.M)
    assert calls
    assert all(call.startswith(LOCKED_CALL) for call in calls)
    assert all(tag == "sh" for tag, _body in tool_blocks(REPAIR_SKILL_TEXT))


def test_dependency_repair_checks_the_verdict_before_the_report_commit():
    text = REPAIR_SKILL_TEXT.read_text(encoding="utf-8")
    step_five = text[text.index("### 5."):text.index("### 6.")]
    assert step_five.index("check-verdict") < step_five.index("the `report` row")
    assert "is never committed with a verdict line the tool refuses" in " ".join(step_five.split())


def test_no_file_under_development_security_contains_mcp():
    folder = SECURITY_SKILL_TEXT.parent
    files = [path for path in folder.rglob("*") if path.is_file()]
    assert files
    assert [path.name for path in files if "mcp" in path.read_text(encoding="utf-8").lower()] == []


def test_the_repair_side_names_none_of_the_scanners():
    repair_files = [path for path in REPAIR_SKILL_TEXT.parent.rglob("*") if path.is_file()]
    repair_files.append(REPAIR_PROMPT)
    for path in repair_files:
        text = path.read_text(encoding="utf-8").lower()
        assert [name for name in THE_THREE_SCANNERS if name in text] == [], path.name
    prompt = committed_text(REPAIR_PROMPT)
    assert "Run a dependency audit the NFDR does not name." in prompt
    assert "do not reach for a tool you happen to know" in prompt


def test_dependency_repair_answers_an_advisory_whose_exception_holds():
    text = committed_text(REPAIR_SKILL_TEXT)
    assert "An advisory whose entry comes back **holding** is answered." in text
    assert "Output that `normalise` refuses counts as an audit that cannot run" in text


def test_dependency_repair_removes_its_scratch_folder_in_a_command_of_its_own():
    text = committed_text(REPAIR_SKILL_TEXT)
    assert "`mktemp -d`" in text
    assert '(`rm -rf "<scratch>"`, in a command of its own)' in text


def test_dependency_repair_removes_its_scratch_folder_when_there_is_nothing_to_repair():
    # change_design.md Sub-job D captures the streams "the way C does", in a folder the run
    # "removes afterwards" — on the nothing-to-repair exit too, which ends the run at Step 2.
    text = REPAIR_SKILL_TEXT.read_text(encoding="utf-8")
    step_two = text[text.index("### 2."):text.index("### 3.")]
    exit_path = step_two[step_two.index("Then there is nothing this skill repairs"):]
    exit_path = " ".join(exit_path.split())
    assert '(`rm -rf "<scratch>"`, in a command of its own)' in exit_path


def test_dependency_repair_keeps_its_suite_call_and_report_layout():
    text = committed_text(REPAIR_SKILL_TEXT)
    assert "gate_suite.py" in text
    assert "Repair: <unmerged | stopped | merged>" in text
    assert "**The verdict line is bare**" in text
