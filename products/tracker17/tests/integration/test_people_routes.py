"""Integration tests of web's People requests, run in one process with no socket (layer 3).

Checks SRS FR-20 and FR-22 (the assignee list and removing a name), FR-27 (the operator's name),
FR-39 and FR-40 (refusals and the maximum length), NFR-4 (a request from another site is refused),
NFR-8 (a failed save leaves the state as it was), DR-4 (the assignee list) and DR-5 (the operator
name). Change spec rules CP-80, CP-82, CP-86, CP-88 to CP-93, CP-95 to CP-101, CP-216 to CP-223,
CP-225, CP-226, CP-232 and CP-238 and NFDR QC-7, QC-8, QC-31, QC-34, QC-35, QC-53, QC-56 and QC-57
are the ones each test names. The handed fakes are the savers; no product name is patched. The real
listener tests serve the real Site on a loopback port and speak HTTP to it.
"""

from __future__ import annotations

import http.client
import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlencode, urlsplit

import pytest
from test_pages import Element, parse
from test_routes import (
    FORM,
    HOST,
    SAME_ORIGIN,
    FixedClock,
    RecordingSaver,
    get,
    header,
    make_site,
    page,
)

from application import SHORT_TEXT_MAX, Saver, Tracker
from domain import empty_state
from persistence import SavedData
from web import Response, Site, listen

LEGACY = {
    "next_project_id": 3,
    "projects": [
        {"id": 1, "name": "Alpha", "description": "first"},
        {"id": 2, "name": "Beta", "description": ""},
    ],
}


def submit(
    site: Site,
    path: str,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    **f: str,
) -> Response:
    sent = urlencode(f).encode("utf-8") if body is None else body
    return site.handle("POST", path, {**(headers or SAME_ORIGIN), **FORM}, sent)


def add(site: Site, name: str) -> Response:
    return submit(site, "/assignees", name=name)


def remove(site: Site, name: str) -> Response:
    return submit(site, "/assignees/remove", name=name)


def location(response: Response) -> str:
    assert response.status == 303
    return header(response, "Location") or ""


def follow(site: Site, response: Response) -> str:
    return page(get(site, location(response)))


def spans(root: Element) -> list[str]:
    return [e.text() for e in root.find_all("span") if "assignee-name" in (e.attrs["class"] or "")]


def focused(root: Element) -> list[Element]:
    return [element for element in root.walk() if "autofocus" in element.attrs]


def names(site: Site) -> list[str]:
    return spans(parse(page(get(site, "/people"))))


def state_of(tracker: Tracker) -> tuple[object, ...]:
    return (tracker.projects(), tracker.assignees())


def test_people_get_and_header_navigation_write_nothing() -> None:
    """CP-80, CP-81."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    empty = parse(page(get(site, "/people")))
    assert [e.text() for e in empty.find_all("h1")] == ["People"]
    submit(site, "/projects", name="Alpha", description="")
    add(site, "Dana")
    saves = len(saver.saved)
    before = state_of(tracker)
    for target in ("/", "/projects/1", "/people", "/nowhere", "/projects/99?created"):
        shown = get(site, target).body.decode("utf-8")
        links = [e for e in parse(shown).find_all("header")[0].find_all("a")]
        assert [link.attrs["href"] for link in links] == ["/", "/people"], target
        opened = get(site, links[1].attrs["href"] or "")
        assert opened.status == 200, target
        assert spans(parse(opened.body.decode("utf-8"))) == ["Dana"]
    assert len(saver.saved) == saves and state_of(tracker) == before


def test_assignee_submissions_redirect_to_people_and_do_not_repeat() -> None:
    """CP-86, CP-93."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    added = add(site, "Dana")
    assert location(added) == "/people?added=Dana"
    saves = len(saver.saved)
    first = follow(site, added)
    for _ in range(2):
        assert follow(site, added) == first
    assert tracker.assignees() == ("Dana",) and len(saver.saved) == saves
    removed = remove(site, "Dana")
    assert location(removed) == "/people?removed=Dana"
    assert "#" not in location(added) + location(removed)
    saves = len(saver.saved)
    shown = follow(site, removed)
    assert follow(site, removed) == shown
    assert tracker.assignees() == () and len(saver.saved) == saves
    assert tracker.projects() == () and saves == 2


def test_assignee_requests_preserve_exact_matching_and_order() -> None:
    """CP-82, CP-88, CP-95."""
    site, tracker = make_site()
    for name in ("Dana", "dana", "Dana ", "Ari"):
        assert add(site, name).status == 303
    assert names(site) == ["Dana", "dana", "Dana ", "Ari"]
    remove(site, "Dana")
    assert names(site) == ["dana", "Dana ", "Ari"]
    add(site, "Dana")
    assert names(site) == ["dana", "Dana ", "Ari", "Dana"]
    for name in ("dana", "Dana ", "Ari", "Dana"):
        remove(site, name)
    shown = page(get(site, "/people"))
    assert names(site) == [] and tracker.assignees() == ()
    assert "There are no assignees yet." in shown and 'action="/assignees"' in shown


def test_stale_assignee_requests_check_current_state() -> None:
    """CP-92, CP-96."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    add(site, "Eve")
    saves = len(saver.saved)
    duplicate = add(site, "Eve")
    assert len(saver.saved) == saves
    assert location(duplicate) == "/people?refused=assignee-name-in-use&name=Eve"
    remove(site, "Eve")
    saves = len(saver.saved)
    stale = remove(site, "Eve")
    assert location(stale) == "/people?refused=assignee-not-found&name=Eve"
    root = parse(follow(site, stale))
    (target,) = focused(root)
    assert target.tag == "h2"
    (link,) = target.described_by()[0].find_all("a")
    assert link.attrs["href"] == "/people"
    assert names(site) == [] and len(saver.saved) == saves
    add(site, "Dana")
    remove(site, "Dana")
    add(site, "Dana")
    assert location(remove(site, "Dana")) == "/people?removed=Dana"
    assert tracker.assignees() == ()


@pytest.mark.parametrize("sent", [None, "", " \t ", "  "], ids=["absent", "empty", "ws", "uni"])
def test_add_refusals_keep_the_field_and_focus_description(sent: str | None) -> None:
    """CP-89, CP-90."""
    saver = RecordingSaver()
    site, _ = make_site(saver)
    add(site, "Dana")
    saves = len(saver.saved)
    response = (
        submit(site, "/assignees", body=b"")
        if sent is None
        else submit(site, "/assignees", name=sent)
    )
    expected = "" if sent is None else sent
    assert location(response).startswith("/people?refused=blank-name")
    root = parse(follow(site, response))
    (target,) = focused(root)
    assert target.tag == "input" and target.attrs["value"] == expected
    assert target.described_by()
    assert len(saver.saved) == saves


def test_a_duplicate_add_keeps_the_typed_name_and_the_reason() -> None:
    """CP-90."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    add(site, "Dana ")
    saves = len(saver.saved)
    response = add(site, "Dana ")
    assert location(response) == "/people?refused=assignee-name-in-use&name=Dana+"
    root = parse(follow(site, response))
    (target,) = focused(root)
    assert target.tag == "input" and target.attrs["value"] == "Dana "
    assert "'Dana '" in target.described_by()[0].text()
    assert len(saver.saved) == saves and tracker.assignees() == ("Dana ",)
    assert add(site, "Dana").status == 303 and tracker.assignees() == ("Dana ", "Dana")


@pytest.mark.parametrize(
    ("filler", "refused_filler"),
    [("ç", "ö"), ("\U0001d11e", "\U0001d11f")],
    ids=["bmp", "non-bmp"],
)
def test_length_refusal_wins_and_omits_all_submitted_text(filler: str, refused_filler: str) -> None:
    """CP-91."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    assert location(add(site, filler * 200)) == f"/people?added={quote_plus(filler * 200)}"
    assert tracker.assignees() == (filler * 200,)
    saves = len(saver.saved)
    for sent in (refused_filler * 201, " " * 201):
        response = add(site, sent)
        assert location(response) == "/people?refused=too-long"
        shown = follow(site, response)
        assert refused_filler not in shown and 'value=""' in shown
        assert quote_plus(refused_filler) not in location(response)
        assert "autofocus" in shown
    assert len(saver.saved) == saves
    hand_built = page(
        get(site, "/people?refused=too-long&name=Leaked&added=Added&removed=Removed&failed=add")
    )
    for payload in ("Leaked", "Added", "Removed"):
        assert payload not in hand_built
    assert len(saver.saved) == saves


@pytest.mark.parametrize("path", ["/assignees", "/assignees/remove"])
@pytest.mark.parametrize(
    "body",
    [
        b"name=\xff\xfe",
        b"name=%FF",
        b"name=Dana%C3",
        b"name=%ED%A0%80",
    ],
    ids=["raw", "percent-ff", "cut-sequence", "surrogate"],
)
def test_assignee_forms_reject_bad_utf8(path: str, body: bytes) -> None:
    """Design T11: no typed value is changed, so no action runs and nothing is saved."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    add(site, "Dana")
    saves = len(saver.saved)
    response = submit(site, path, body=body)
    assert response.status == 400 and response.body == b""
    assert len(saver.saved) == saves and tracker.assignees() == ("Dana",)


def test_assignee_forms_normalize_newlines_only() -> None:
    """CP-88: CR LF and a lone CR both become LF; spaces and every other character stay."""
    site, tracker = make_site()
    add(site, " a\r\nb ")
    add(site, "c\rd")
    assert tracker.assignees() == (" a\nb ", "c\nd")
    assert remove(site, " a\r\nb ").status == 303 and tracker.assignees() == ("c\nd",)
    assert location(remove(site, "c\rd")) == "/people?removed=c%0Ad"
    assert tracker.assignees() == ()


class RaisingSaver:
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.calls = 0

    def save(self, state: object) -> None:
        self.calls += 1
        raise self.error


@pytest.mark.parametrize(
    ("error", "error_line"),
    [
        (PermissionError("the disk said no"), "PermissionError: the disk said no"),
        (OSError(), "OSError"),
    ],
    ids=["with-text", "kind-only"],
)
def test_failed_assignee_actions_keep_state_and_report_plain_failure(
    tmp_path: Path, error: Exception, error_line: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-97, QC-56, QC-57: the file written before the failure is the one still there."""
    data = tmp_path / "data"
    seeded = Tracker(empty_state(), SavedData(data), FixedClock())
    seeded.add_assignee("Ari")
    seeded.add_assignee(" Dana ")
    saved_file = data / "tracker.json"
    before = saved_file.read_bytes()
    state = SavedData(data).load()
    assert state is not None
    failing = RaisingSaver(error)
    site = Site(Tracker(state, failing, FixedClock()), HOST)
    capsys.readouterr()

    added = add(site, " Cy ")
    err = capsys.readouterr().err.splitlines()
    assert location(added) == "/people?failed=add&name=+Cy+"
    assert err == [
        "The tracker couldn't add ' Cy ' to the assignees, and nothing was changed.",
        error_line,
    ]
    shown = follow(site, added)
    root = parse(shown)
    (target,) = focused(root)
    assert target.tag == "button" and target.text() == "Add"
    (form,) = [f for f in root.find_all("form") if f.attrs.get("action") == "/assignees"]
    (field,) = [e for e in form.find_all("input") if e.attrs.get("type") == "text"]
    assert field.attrs["value"] == " Cy "
    for forbidden in ("Traceback", "PermissionError", "the disk said no", "OSError"):
        assert forbidden not in shown

    removed = remove(site, " Dana ")
    err = capsys.readouterr().err.splitlines()
    assert location(removed) == "/people?failed=remove&name=+Dana+"
    assert err == [
        "The tracker couldn't remove ' Dana ' from the assignees, and nothing was changed.",
        error_line,
    ]
    root = parse(follow(site, removed))
    (target,) = focused(root)
    assert target.tag == "button" and target.attrs["aria-label"].startswith("Remove ' Dana '")
    assert spans(root) == ["Ari", " Dana "]
    assert failing.calls == 2
    assert saved_file.read_bytes() == before
    assert json.loads(before)["assignees"] == ["Ari", " Dana "]


@pytest.mark.parametrize("path", ["/assignees", "/assignees/remove"])
@pytest.mark.parametrize("mark", ["cross-site", "same-site", "none", "", None])
def test_assignee_submission_origin_checks_run_first(path: str, mark: str | None) -> None:
    """CP-98."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    add(site, "Dana")
    saves = len(saver.saved)
    marks = {"Host": HOST} if mark is None else {"Host": HOST, "Sec-Fetch-Site": mark}
    response = submit(site, path, headers=marks, name="Dana")
    assert response.status == 403 and response.body == b""
    assert len(saver.saved) == saves and tracker.assignees() == ("Dana",)


@pytest.mark.parametrize("host", ["evil.example", "127.0.0.1:9999", "localhost:8017", None])
def test_assignee_submissions_with_a_wrong_or_missing_host_are_refused(host: str | None) -> None:
    """QC-31."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    add(site, "Dana")
    saves = len(saver.saved)
    marks = {"Sec-Fetch-Site": "same-origin"}
    if host is not None:
        marks["Host"] = host
    for path in ("/assignees", "/assignees/remove"):
        assert submit(site, path, headers=marks, name="Dana").status == 403
    assert get(site, "/people", marks).status == 403
    assert len(saver.saved) == saves and tracker.assignees() == ("Dana",)


def test_same_origin_assignee_submissions_are_accepted() -> None:
    """CP-98."""
    site, tracker = make_site()
    assert add(site, "Dana").status == 303
    assert remove(site, "Dana").status == 303 and tracker.assignees() == ()


PLAIN = "/people"


def _view(site: Site, target: str) -> Element:
    return parse(page(get(site, target)))


def test_people_outcome_queries_obey_precedence_without_mutation() -> None:
    """Design T18."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    add(site, "Dana")
    saves, before = len(saver.saved), state_of(tracker)
    plain = page(get(site, PLAIN))
    for unknown in ("?refused=nonsense", "?failed=other", "?refused=&failed=", "?x=1"):
        assert page(get(site, PLAIN + unknown)) == plain, unknown
    combined = _view(site, "/people?refused=blank-name&failed=add&added=Zed&removed=Yan&name=+")
    assert [e.tag for e in focused(combined)] == ["input"]
    shown = page(get(site, "/people?refused=blank-name&failed=add&added=Zed&removed=Yan&name=+"))
    assert "Zed" not in shown and "Yan" not in shown
    failure = _view(site, "/people?failed=add&added=Zed&removed=Yan&name=Cy")
    assert [e.tag for e in focused(failure)] == ["button"]
    success = _view(site, "/people?added=Dana&removed=Dana")
    (target,) = focused(success)
    assert target.tag == "span" and target.text() == "Dana"
    gone = _view(site, "/people?added=Gone")
    (target,) = focused(gone)
    assert target.tag == "h2" and "'Gone'" in target.described_by()[0].text()
    later = _view(site, "/people?failed=remove&name=Gone")
    (target,) = focused(later)
    assert target.tag == "h2" and "'Gone'" in target.described_by()[0].text()
    assert len(saver.saved) == saves and state_of(tracker) == before


def test_people_survives_real_save_and_restart(tmp_path: Path) -> None:
    """CP-99, CP-100; design T8."""
    data = tmp_path / "data"
    saved = SavedData(data)
    site = Site(Tracker(empty_state(), saved, FixedClock()), HOST)
    submit(site, "/projects", name="Alpha", description="")
    for name in ("Dana", " Ari ", "<b>A&B</b>", "Zoë"):
        add(site, name)
    remove(site, "Dana")
    add(site, "Dana")
    state = saved.load()
    assert state is not None
    restarted = Site(Tracker(state, SavedData(data), FixedClock()), HOST)
    assert names(restarted) == [" Ari ", "<b>A&B</b>", "Zoë", "Dana"]
    assert "Alpha" in page(get(restarted, "/"))

    legacy_location = tmp_path / "legacy"
    legacy_location.mkdir()
    legacy_file = legacy_location / "tracker.json"
    legacy_file.write_bytes(json.dumps(LEGACY).encode("utf-8"))
    before = legacy_file.read_bytes()
    loaded = SavedData(legacy_location).load()
    assert loaded is not None
    legacy_site = Site(Tracker(loaded, SavedData(legacy_location), FixedClock()), HOST)
    listed = page(get(legacy_site, "/"))
    assert "Alpha" in listed and "Beta" in listed
    assert names(legacy_site) == []
    assert "There are no assignees yet." in page(get(legacy_site, "/people"))
    assert legacy_file.read_bytes() == before


NON_BMP = "\U0001f600"
BLANK_FORMS = ("", "   ", "\t", "\u00a0", "\u3000")
OVERLONG_FORMS = ("x" * (SHORT_TEXT_MAX + 1), " " * (SHORT_TEXT_MAX + 1))
BLANK_REASON = "Your name can't be blank. Type a name."
TOO_LONG_REASON = f"Your name can't be longer than {SHORT_TEXT_MAX} characters. Type a shorter one."
COMPLETED = "You set your name to '{name}'."
FAILED = (
    "The tracker couldn't set your name to '{name}', and nothing was changed. "
    "What you typed is still in the form. Try again."
)


def set_name(site: Site, name: str) -> Response:
    return submit(site, "/operator-name", name=name)


def query_of(response: Response) -> dict[str, list[str]]:
    return parse_qs(urlsplit(location(response)).query, keep_blank_values=True)


def operator_field(root: Element) -> Element:
    found = root.by_id("operator-name")
    assert found is not None
    return found


def described(element: Element) -> str:
    return " ".join(line.text() for line in element.described_by())


def named_site(saver: Saver | None = None, name: str | None = None) -> tuple[Site, Tracker]:
    site, tracker = make_site(saver)
    if name is not None:
        tracker.set_operator_name(name)
    return site, tracker


@pytest.mark.parametrize("starting", [None, "Sam"], ids=["unset", "saved"])
def test_operator_name_post_sets_and_replaces_exact_text(starting: str | None) -> None:
    """CP-216, CP-217: a POST then the redirect shows the changed name and the quoted completion,
    case and surrounding spaces survive, and only line breaks are normalized."""
    saver = RecordingSaver()
    site, tracker = named_site(saver, starting)
    saves = len(saver.saved)
    for submitted in (" Sam Lee ", "sAm LEE"):
        response = set_name(site, submitted)
        assert urlsplit(location(response)).path == "/people"
        assert query_of(response) == {"operator_saved": [submitted]}
        root = parse(follow(site, response))
        assert operator_field(root).attrs["value"] == submitted
        (target,) = focused(root)
        assert target is operator_field(root)
        assert described(target) == COMPLETED.format(name=submitted)
        assert tracker.operator_name() == submitted
    assert len(saver.saved) == saves + 2


def test_same_saved_name_redirects_without_save_or_outcome() -> None:
    """CP-218: the exact saved name redirects to plain People and saves nothing; a trailing space
    still makes a different name."""
    saver = RecordingSaver()
    site, tracker = named_site(saver, "Sam")
    saves = len(saver.saved)
    same = set_name(site, "Sam")
    assert location(same) == "/people"
    shown = follow(site, same)
    assert shown == page(get(site, "/people"))
    root = parse(shown)
    assert focused(root) == [] and root.by_id("operator-name-outcome") is None
    assert len(saver.saved) == saves and tracker.operator_name() == "Sam"
    spaced = set_name(site, "Sam ")
    assert query_of(spaced) == {"operator_saved": ["Sam "]}
    assert tracker.operator_name() == "Sam " and len(saver.saved) == saves + 1


def test_stale_people_name_submission_compares_with_current_name() -> None:
    """CP-218: two pages opened before another change compare with the name saved at the moment of
    the action; no shown-name value rides in the form."""
    saver = RecordingSaver()
    site, tracker = named_site(saver)
    older = parse(page(get(site, "/people")))
    (form,) = [f for f in older.find_all("form") if f.attrs.get("action") == "/operator-name"]
    assert [e.attrs["name"] for e in form.find_all("input")] == ["name"]
    set_name(site, "Other")
    saves = len(saver.saved)
    assert location(set_name(site, "Other")) == "/people"
    assert len(saver.saved) == saves
    assert query_of(set_name(site, "Older")) == {"operator_saved": ["Older"]}
    assert tracker.operator_name() == "Older" and len(saver.saved) == saves + 1


@pytest.mark.parametrize("starting", [None, "Sam"], ids=["unset", "saved"])
def test_empty_name_refusal_retains_empty_field_and_saved_state(
    starting: str | None, tmp_path: Path
) -> None:
    """CP-219, CP-220: an empty name is refused as blank from both starts; the empty typed value is
    in the address, the field shows it, and the saved file and name are unchanged."""
    saved = SavedData(tmp_path)
    site, tracker = named_site(saved, starting)
    before = (tmp_path / "tracker.json").read_bytes() if starting else None
    response = set_name(site, "")
    assert query_of(response) == {"operator_refused": ["blank-name"], "operator_typed": [""]}
    root = parse(follow(site, response))
    (target,) = focused(root)
    assert target is operator_field(root) and target.attrs["value"] == ""
    assert described(target) == BLANK_REASON
    assert tracker.operator_name() == starting
    assert ((tmp_path / "tracker.json").read_bytes() if starting else None) == before
    assert starting or not (tmp_path / "tracker.json").exists()


@pytest.mark.parametrize("starting", [None, "Sam"], ids=["unset", "saved"])
@pytest.mark.parametrize("blank", BLANK_FORMS[1:])
def test_whitespace_name_refusal_retains_text_and_saved_state(
    starting: str | None, blank: str, tmp_path: Path
) -> None:
    """CP-220: each whitespace-only form is refused as blank, kept exactly in the field, and the
    saved name and file are unchanged."""
    saved = SavedData(tmp_path)
    site, tracker = named_site(saved, starting)
    before = (tmp_path / "tracker.json").read_bytes() if starting else None
    response = set_name(site, blank)
    assert query_of(response) == {"operator_refused": ["blank-name"], "operator_typed": [blank]}
    root = parse(follow(site, response))
    (target,) = focused(root)
    assert target is operator_field(root) and target.attrs["value"] == blank
    assert described(target) == BLANK_REASON
    assert tracker.operator_name() == starting
    assert ((tmp_path / "tracker.json").read_bytes() if starting else None) == before


def test_missing_name_field_is_empty_refusal() -> None:
    """CP-220: a POST without the field follows the empty-name rule."""
    saver = RecordingSaver()
    site, tracker = named_site(saver, "Sam")
    saves = len(saver.saved)
    response = submit(site, "/operator-name", body=b"")
    assert query_of(response) == {"operator_refused": ["blank-name"], "operator_typed": [""]}
    assert tracker.operator_name() == "Sam" and len(saver.saved) == saves


@pytest.mark.parametrize("starting", [None, "Sam"], ids=["unset", "saved"])
@pytest.mark.parametrize("sent", OVERLONG_FORMS, ids=["characters", "spaces"])
def test_overlong_name_refusal_omits_payload_and_keeps_fallback(
    starting: str | None, sent: str
) -> None:
    """CP-221: 201 characters or 201 spaces get the too-long reason before blankness; neither the
    address nor the page carries the sent text; the field holds the saved name or nothing."""
    saver = RecordingSaver()
    site, tracker = named_site(saver, starting)
    saves = len(saver.saved)
    response = set_name(site, sent)
    assert query_of(response) == {"operator_refused": ["too-long"]}
    assert sent not in location(response) and quote_plus(sent) not in location(response)
    shown = follow(site, response)
    assert sent not in shown
    root = parse(shown)
    (target,) = focused(root)
    assert target is operator_field(root) and target.attrs["value"] == (starting or "")
    assert described(target) == TOO_LONG_REASON
    assert tracker.operator_name() == starting and len(saver.saved) == saves


def test_name_submission_normalizes_only_line_breaks() -> None:
    """CP-217: CR LF and a lone CR become LF and nothing else changes; U+200B alone is accepted,
    and so is exactly 200 code points including one outside the Basic Multilingual Plane."""
    site, tracker = named_site()
    set_name(site, " a\r\nb\rc ")
    assert tracker.operator_name() == " a\nb\nc "
    assert set_name(site, "\u200b").status == 303 and tracker.operator_name() == "\u200b"
    boundary = NON_BMP + "x" * (SHORT_TEXT_MAX - 1)
    response = set_name(site, boundary)
    assert query_of(response) == {"operator_saved": [boundary]}
    assert tracker.operator_name() == boundary


@pytest.mark.parametrize(
    ("error", "error_line"),
    [
        (PermissionError("the disk said no"), "PermissionError: the disk said no"),
        (OSError(), "OSError"),
    ],
    ids=["with-text", "kind-only"],
)
@pytest.mark.parametrize("starting", [None, "Sam"], ids=["unset", "saved"])
def test_failed_name_save_keeps_typed_text_and_reports_action(
    tmp_path: Path,
    error: Exception,
    error_line: str,
    starting: str | None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CP-222, QC-56, QC-57: the state and file stay, the typed text stays, Save has focus and
    the failure line, the console names the action then the error, and the page shows no error."""
    data = tmp_path / "data"
    seeded = Tracker(empty_state(), SavedData(data), FixedClock())
    if starting is not None:
        seeded.set_operator_name(starting)
    loaded = SavedData(data).load()
    before = (data / "tracker.json").read_bytes() if starting else None
    failing = RaisingSaver(error)
    site = Site(Tracker(loaded or empty_state(), failing, FixedClock()), HOST)
    capsys.readouterr()
    response = set_name(site, " Lee ")
    assert capsys.readouterr().err.splitlines() == [
        "The tracker couldn't set your name to ' Lee ', and nothing was changed.",
        error_line,
    ]
    assert query_of(response) == {"operator_failed": ["save"], "operator_typed": [" Lee "]}
    shown = follow(site, response)
    root = parse(shown)
    (target,) = focused(root)
    assert target.tag == "button" and target.text() == "Save"
    assert operator_field(root).attrs["value"] == " Lee "
    assert described(target) == FAILED.format(name=" Lee ")
    for forbidden in ("Traceback", "PermissionError", "the disk said no", "OSError"):
        assert forbidden not in shown
    assert failing.calls == 1
    assert ((data / "tracker.json").read_bytes() if starting else None) == before
    unchanged = parse(page(get(site, "/people")))
    assert operator_field(unchanged).attrs["value"] == (starting or "")


def test_operator_query_presence_unknown_codes_and_precedence() -> None:
    """CP-220 to CP-222: an empty typed value differs from none, which falls back to the saved
    name; unknown codes and forged too-long text are ignored; refusal, failure and completion, and
    operator against assignee outcomes, give exactly the designed outcome and focus; no GET
    saves."""
    saver = RecordingSaver()
    site, tracker = named_site(saver, "Sam")
    saves = len(saver.saved)
    plain = page(get(site, "/people"))

    def view(target: str) -> Element:
        return parse(page(get(site, target)))

    assert (
        operator_field(view("/people?operator_refused=blank-name&operator_typed=")).attrs["value"]
        == ""
    )
    assert operator_field(view("/people?operator_refused=blank-name")).attrs["value"] == "Sam"
    assert operator_field(view("/people?operator_failed=save&operator_typed=")).attrs["value"] == ""
    assert operator_field(view("/people?operator_failed=save")).attrs["value"] == "Sam"
    for unknown in (
        "?operator_refused=nonsense&operator_typed=PAYLOAD",
        "?operator_failed=other&operator_typed=PAYLOAD",
        "?operator_typed=PAYLOAD",
        "?operator_saved=",
        "?operator_saved=&operator_typed=PAYLOAD",
    ):
        assert page(get(site, "/people" + unknown)) == plain, unknown
    forged = page(
        get(
            site,
            "/people?operator_refused=too-long&operator_typed=PAYLOAD&operator_failed=save"
            "&operator_saved=PAYLOAD2",
        )
    )
    assert "PAYLOAD" not in forged
    root = parse(forged)
    (target,) = focused(root)
    assert target is operator_field(root) and target.attrs["value"] == "Sam"
    assert described(target) == TOO_LONG_REASON
    refusal = "/people?operator_refused=blank-name&operator_failed=save&operator_saved=Zed"
    shown = page(get(site, refusal + "&operator_typed=+"))
    assert "Zed" not in shown
    (target,) = focused(parse(shown))
    assert target.tag == "input" and described(target) == BLANK_REASON
    failure = page(get(site, "/people?operator_failed=save&operator_saved=Zed&operator_typed=Cy"))
    assert "Zed" not in failure
    (target,) = focused(parse(failure))
    assert target.tag == "button" and described(target) == FAILED.format(name="Cy")
    completed = view("/people?operator_saved=Zed")
    (target,) = focused(completed)
    assert target is operator_field(completed) and target.attrs["value"] == "Sam"
    assert described(target) == COMPLETED.format(name="Zed")
    mixed = page(
        get(
            site,
            "/people?refused=blank-name&failed=add&added=Zed2&removed=Yan&name=+"
            "&operator_saved=Lee",
        )
    )
    assert "Zed2" not in mixed and "Yan" not in mixed
    (target,) = focused(parse(mixed))
    assert target.tag == "input" and described(target) == COMPLETED.format(name="Lee")
    tracker.add_assignee("Dana")
    (target,) = focused(view("/people?added=Dana"))
    assert target.tag == "span" and target.text() == "Dana"
    assert tracker.operator_name() == "Sam" and len(saver.saved) == saves + 1


@pytest.mark.parametrize(
    "body",
    [b"name=\xff", b"name=%FF", b"name=%E2%82", b"name=%ED%A0%80", b"name=ok%C0%80"],
    ids=["raw", "percent", "incomplete", "surrogate", "overlong-encoding"],
)
def test_operator_name_form_rejects_malformed_utf8_without_saving(body: bytes) -> None:
    """CP-217, CP-223: invalid UTF-8 gets the existing 400 and runs no action."""
    saver = RecordingSaver()
    site, tracker = named_site(saver, "Sam")
    saves = len(saver.saved)
    response = submit(site, "/operator-name", body=body)
    assert response.status == 400 and response.body == b""
    assert tracker.operator_name() == "Sam" and len(saver.saved) == saves


def test_name_landing_gets_never_repeat_save() -> None:
    """CP-216: repeated landing GETs, a reload and a history return save nothing again."""
    saver = RecordingSaver()
    site, tracker = named_site(saver)
    landing = location(set_name(site, "Sam"))
    saves = len(saver.saved)
    first = page(get(site, landing))
    for _ in range(3):
        assert page(get(site, landing)) == first
    assert get(site, "/").status == 200 and get(site, "/people").status == 200
    assert page(get(site, landing)) == first
    assert len(saver.saved) == saves and tracker.operator_name() == "Sam"


@contextmanager
def served(tracker: Tracker) -> Iterator[tuple[str, int]]:
    listener = listen(("127.0.0.1", 0), tracker)
    thread = threading.Thread(target=listener.serve_forever, daemon=True)
    thread.start()
    try:
        yield str(listener.server_address[0]), int(listener.server_address[1])
    finally:
        listener.shutdown()
        thread.join(timeout=10)
        listener.server_close()


def exchange(
    address: tuple[str, int], method: str, target: str, **fields: str
) -> tuple[int, dict[str, str], str]:
    """One request over the socket; a submission carries the same-origin mark a form sends."""
    connection = http.client.HTTPConnection(address[0], address[1], timeout=10)
    headers: dict[str, str] = {}
    body = None
    if method == "POST":
        headers = {
            "Sec-Fetch-Site": "same-origin",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        body = urlencode(fields).encode("utf-8")
    try:
        connection.request(method, target, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read().decode("utf-8")
    finally:
        connection.close()


def listener_name(address: tuple[str, int], name: str) -> tuple[Element, dict[str, list[str]]]:
    """POST the name over the socket, follow the redirect, and return the parsed landing page."""
    status, headers, _ = exchange(address, "POST", "/operator-name", name=name)
    assert status == 303
    landing = headers["Location"]
    status, _, shown = exchange(address, "GET", landing)
    assert status == 200
    return parse(shown), parse_qs(urlsplit(landing).query, keep_blank_values=True)


@pytest.mark.parametrize("starting", [None, "Sam"], ids=["unset", "saved"])
def test_real_listener_people_shows_and_sets_operator_name(starting: str | None) -> None:
    """CP-211, CP-216, CP-220, CP-232: over a real bound listener, People shows the section, a
    name is set and replaced, and the empty and whitespace refusals leave the saved name alone."""
    saver = RecordingSaver()
    _, tracker = named_site(saver, starting)
    with served(tracker) as address:
        status, _, shown = exchange(address, "GET", "/people")
        assert status == 200
        root = parse(shown)
        assert operator_field(root).attrs["value"] == (starting or "")
        for expected in ("Your name", "Save", "Comments you've already written keep the name"):
            assert expected in root.by_id("your-name").text()  # type: ignore[union-attr]
        landed, query = listener_name(address, "Sam Lee")
        assert query == {"operator_saved": ["Sam Lee"]}
        assert operator_field(landed).attrs["value"] == "Sam Lee"
        assert described(focused(landed)[0]) == COMPLETED.format(name="Sam Lee")
        landed, _ = listener_name(address, "Lee")
        assert operator_field(landed).attrs["value"] == "Lee"
        for blank in ("", "   "):
            landed, query = listener_name(address, blank)
            assert query == {"operator_refused": ["blank-name"], "operator_typed": [blank]}
            (target,) = focused(landed)
            assert target is operator_field(landed) and target.attrs["value"] == blank
            assert described(target) == BLANK_REASON
        assert tracker.operator_name() == "Lee"


def test_operator_name_survives_real_save_and_restart(tmp_path: Path) -> None:
    """CP-226, CP-232: a name saved through the real listener and SavedData is the field's value
    after a fresh tracker and listener start, with the rest of the saved data intact."""
    data = tmp_path / "data"
    saved = SavedData(data)
    tracker = Tracker(empty_state(), saved, FixedClock())
    tracker.create_project("Alpha", "first")
    tracker.add_assignee("Dana")
    tracker.add_task(1, "Write it", "high", "Dana", "2026-12-01")
    tracker.add_task_label(1, "ui")
    with served(tracker) as address:
        listener_name(address, " <b>Sam</b> ")
    state = SavedData(data).load()
    assert state is not None and state.operator_name == " <b>Sam</b> "
    restarted = Tracker(state, SavedData(data), FixedClock())
    with served(restarted) as address:
        status, _, shown = exchange(address, "GET", "/people")
        assert status == 200
        root = parse(shown)
        assert operator_field(root).attrs["value"] == " <b>Sam</b> "
        assert root.find_all("b") == []
        assert spans(root) == ["Dana"]
    assert state.projects == tracker.projects() and restarted.assignees() == ("Dana",)
    assert restarted.project_tasks(1) == tracker.project_tasks(1)
