"""Integration tests of a task page's comment area, read back as a browser parses it (layer 4).

Checks SRS FR-28 (a comment shows its author and the time it was written), FR-29 (comments in the
order written), FR-30 (a comment keeps the name it was written under), FR-39 and FR-40 (a refusal's
reason beside the field, and the comment maximum), NFR-4 (no script), NFR-5 (typed text is shown as
text), NFR-14 (the time in local time) and AC-20 (a comment at its maximum). Change spec rules
CP-240 to CP-248, CP-250, CP-255 to CP-257, CP-260 and CP-268 and NFDR QC-9, QC-36 and QC-44 are
the ones each test names. The real Site, Tracker and SavedData are used, with an injected clock and
a saver that count their calls; comments are restored from valid saved values, so no submission is
needed to show them. Where a test checks words, they are the strings of this change's text record.
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from test_pages import Element, parse, textarea_value
from test_routes import HOST, get, page
from test_task_pages import ALPHA, a_task, context_of

from application import LONG_TEXT_MAX, Comment, Task, Tracker, TrackerState
from domain import restore_state
from persistence import SavedData
from web import Site, pages

TITLE = "Set up CI"
WRITTEN = datetime(2026, 10, 12, 12, 32, tzinfo=UTC)
HEADING = "Comments"
EMPTY_NAMED = "This task has no comments yet. Type a comment and press Add."
EMPTY_UNNAMED = "This task has no comments yet."
NOTICE = "You need a name to comment. Set your name on the People page."
MAXIMUM = f"A comment can hold up to {LONG_TEXT_MAX} characters."
TOO_LONG_REASON = f"A comment can't be longer than {LONG_TEXT_MAX} characters. Type a shorter one."
BLANK_REASON = "A comment can't be blank. Type a comment."
NO_NAME_REASON = "A comment needs your name. Set it on the People page, then add the comment."
FAILURE_LINE = (
    f"The tracker couldn't add your comment to '{TITLE}', and nothing was changed. "
    "What you typed is still in the form. Try again."
)
COMPLETION_LINE = f"You added a comment to '{TITLE}'."
ADD_NAME = f"Add comment to '{TITLE}'"


@contextmanager
def machine_zone(name: str) -> Iterator[None]:
    """The machine's time zone is this one while the block runs; no product clock is patched."""
    earlier = os.environ.get("TZ")
    os.environ["TZ"] = name
    time.tzset()
    try:
        yield
    finally:
        if earlier is None:
            del os.environ["TZ"]
        else:
            os.environ["TZ"] = earlier
        time.tzset()


@pytest.fixture(autouse=True)
def utc_machine() -> Iterator[None]:
    """Every page here is read on a machine whose local time is UTC unless a test says otherwise."""
    with machine_zone("UTC"):
        yield


class CountingClock:
    def __init__(self) -> None:
        self.reads = 0

    def now(self) -> datetime:
        self.reads += 1
        return WRITTEN


class CountingSaver:
    """Saves through the real SavedData and counts the saves; it has nothing to read."""

    def __init__(self, inner: SavedData) -> None:
        self._inner = inner
        self.saves = 0

    def save(self, state: TrackerState) -> None:
        self._inner.save(state)
        self.saves += 1


@dataclass
class World:
    site: Site
    tracker: Tracker
    clock: CountingClock
    saver: CountingSaver


def comment(text: str, author: str = "Sam", written: datetime = WRITTEN) -> Comment:
    return Comment(text=text, author=author, created_at=written)


def world_with(
    tmp_path: Path,
    comments: tuple[Comment, ...] = (),
    *,
    name: str | None = "Sam",
    labels: tuple[str, ...] = (),
) -> World:
    base = a_task(1, TITLE, labels=labels)
    task = Task(**{**base.__dict__, "comments": comments})
    state = restore_state(
        [(ALPHA.id, ALPHA.name, ALPHA.description)],
        2,
        (),
        tasks=[task],
        next_task_id=2,
        operator_name=name,
    )
    clock, saver = CountingClock(), CountingSaver(SavedData(tmp_path / "data"))
    tracker = Tracker(state, saver, clock)
    return World(Site(tracker, HOST), tracker, clock, saver)


def root_of(world: World, query: str = "") -> Element:
    return parse(page(get(world.site, f"/tasks/1{query}")))


def comments_section(root: Element) -> Element:
    (found,) = [e for e in root.find_all("section") if e.attrs.get("id") == "comments"]
    return found


def items(root: Element) -> list[Element]:
    return comments_section(root).find_all("li")


def add_form(root: Element) -> Element:
    (found,) = [f for f in root.find_all("form") if f.attrs.get("action") == "/tasks/1/comments"]
    return found


def text_field(root: Element) -> Element:
    (found,) = add_form(root).find_all("textarea")
    return found


def add_button(root: Element) -> Element:
    (found,) = add_form(root).find_all("button")
    return found


def focused(root: Element) -> list[Element]:
    return [element for element in root.walk() if "autofocus" in element.attrs]


def description(element: Element) -> str:
    return " ".join(found.text() for found in element.described_by())


def meta_of(item: Element) -> str:
    (meta,) = [p for p in item.find_all("p") if "comment-meta" in (p.attrs.get("class") or "")]
    return meta.text()


def body_of(item: Element) -> str:
    (body,) = [p for p in item.find_all("p") if "comment-text" in (p.attrs.get("class") or "")]
    return body.text()


def test_task_comments_are_between_labels_and_the_add_form(tmp_path: Path) -> None:
    """CP-240, CP-241: heading, then flat comments, then the form, below the fields and labels."""
    world = world_with(
        tmp_path, (comment("first", "Sam"), comment("second", "Lee")), labels=("ui",)
    )
    root = root_of(world)
    area = comments_section(root)
    assert [h.text() for h in area.find_all("h2")] == [HEADING]
    (edit,) = [f for f in root.find_all("form") if f.attrs.get("action") == "/tasks/1"]
    (labels,) = [e for e in root.find_all("section") if e.attrs.get("id") == "labels"]
    order = [e for e in root.walk() if e in (edit, labels, area)]
    assert order == [edit, labels, area]
    inside = [e for e in area.walk() if e.tag in ("h2", "ol", "li", "form")]
    assert [e.tag for e in inside][:2] == ["h2", "ol"]
    assert inside[-1] is add_form(root)
    assert [e.tag for e in inside].count("ol") == 1
    shown = items(root)
    assert [body_of(item) for item in shown] == ["first", "second"]
    for item, author in zip(shown, ("Sam", "Lee"), strict=True):
        assert meta_of(item).startswith(f"{author}, ")
    assert all(item.find_all("li") == [item] and item.find_all("ol") == [] for item in shown)
    list_end = next(e for e in area.walk() if e.tag == "ol")
    assert add_form(root) not in list(list_end.walk())


def test_comment_page_preserves_append_order_when_times_disagree(tmp_path: Path) -> None:
    """CP-241, CP-268: the order added, whatever the times; a GET reads no clock and saves none."""
    later = WRITTEN + timedelta(hours=1)
    comments = (
        comment("a", "Sam", later),
        comment("b", "Lee", WRITTEN),
        comment("c", "Sam", WRITTEN),
        comment("a", "Sam", WRITTEN),
    )
    world = world_with(tmp_path, comments)
    first = page(get(world.site, "/tasks/1"))
    assert page(get(world.site, "/tasks/1")) == first
    assert [body_of(item) for item in items(parse(first))] == ["a", "b", "c", "a"]
    assert (world.clock.reads, world.saver.saves) == (0, 0)


def test_comment_time_is_machine_local_in_the_required_format(tmp_path: Path) -> None:
    """CP-242: `2026-10-12T12:32:00Z` on a UTC+2 machine shows `2026-10-12 14:32`, and no more."""
    world = world_with(
        tmp_path,
        (
            comment("one", "Sam", WRITTEN),
            comment("two", "Sam", datetime(2026, 10, 12, 12, 32, 59, tzinfo=UTC)),
            comment("three", "Sam", datetime(2026, 10, 12, 23, 30, tzinfo=UTC)),
        ),
    )
    with machine_zone("Etc/GMT-2"):
        shown = [meta_of(item) for item in items(root_of(world))]
    assert shown == [
        "Sam, 2026-10-12 14:32",
        "Sam, 2026-10-12 14:32",
        "Sam, 2026-10-13 01:30",
    ]
    first, *_ = items(root_of(world))
    assert meta_of(first) == "Sam, 2026-10-12 12:32"


def test_comment_page_preserves_spaces_line_breaks_and_markup_as_text(tmp_path: Path) -> None:
    """CP-243, QC-36: author and text exactly as saved, once escaped, with their line breaks."""
    text = "\n  <b>A&B</b> \"q\" 's'  \nline two\n"
    author = " Sam <i> "
    world = world_with(tmp_path, (comment(text, author),))
    shown_page = page(get(world.site, "/tasks/1"))
    assert "<b>A&B</b>" not in shown_page and "<i>" not in shown_page
    assert "&lt;b&gt;A&amp;B&lt;/b&gt;" in shown_page
    root = parse(shown_page)
    (item,) = items(root)
    assert body_of(item) == text
    assert meta_of(item) == f"{author}, 2026-10-12 12:32"
    assert [e for e in item.walk() if e.tag in ("b", "i")] == []
    for paragraph in item.find_all("p"):
        assert "pre-wrap" in paragraph.attrs["class"].split()


def test_comment_form_has_one_label_and_one_shared_maximum(tmp_path: Path) -> None:
    """CP-244 to CP-246, QC-9: a labelled four-line field, its maximum, a text-only submission."""
    world = world_with(tmp_path, (comment("first"), comment("second")))
    root = root_of(world)
    form = add_form(root)
    assert form.attrs["method"] == "post"
    field = text_field(root)
    assert field.attrs["name"] == "text" and field.attrs["rows"] == "4"
    assert field.attrs["maxlength"] == str(LONG_TEXT_MAX)
    labels = [x for x in form.find_all("label") if x.attrs.get("for") == field.attrs["id"]]
    assert [x.text() for x in labels] == ["Comment"] and len(form.find_all("label")) == 1
    (sentence,) = [e for e in form.find_all("p") if "note" in (e.attrs.get("class") or "")]
    assert sentence.text() == MAXIMUM
    assert str(LONG_TEXT_MAX) in sentence.text()
    assert description(field) == MAXIMUM
    button = add_button(root)
    assert button.text() == "Add" and button.attrs["type"] == "submit"
    assert button.attrs["aria-label"] == ADD_NAME
    for control in form.walk():
        assert "required" not in control.attrs and "disabled" not in control.attrs
    assert [e.attrs.get("name") for e in form.walk() if e.tag in ("input", "textarea")] == ["text"]
    assert form.find_all("input") == []
    shown = items(root)
    assert shown[-1] in list(comments_section(root).walk())
    order = [e for e in comments_section(root).walk() if e in (shown[-1], form, button)]
    assert order == [shown[-1], form, button]


def test_empty_comments_show_the_approved_empty_line_and_form(tmp_path: Path) -> None:
    """CP-244, CP-246: no comments say so, in both name states, with the form in view."""
    named = root_of(world_with(tmp_path, ()))
    area = comments_section(named)
    assert EMPTY_NAMED in area.text() and EMPTY_UNNAMED in area.text()
    assert [e for e in area.walk() if e.tag in ("ol", "ul", "li")] == []
    assert text_field(named).attrs["name"] == "text" and add_button(named).text() == "Add"
    assert focused(named) == []
    unnamed = root_of(world_with(tmp_path, (), name=None))
    unnamed_area = comments_section(unnamed)
    assert EMPTY_NAMED not in unnamed_area.text() and EMPTY_UNNAMED in unnamed_area.text()
    assert add_button(unnamed).text() == "Add" and focused(unnamed) == []


def test_comment_name_notice_matches_the_current_saved_name(tmp_path: Path) -> None:
    """CP-246: the notice and its one People link above the form while no name is saved."""
    world = world_with(tmp_path, (comment("hi"),), name=None)
    root = root_of(world)
    area = comments_section(root)
    (notice,) = [e for e in area.walk() if e.tag == "p" and NOTICE == e.text()]
    (link,) = area.find_all("a")
    assert link.attrs["href"] == "/people" and link.text() == "People"
    assert link.parent is notice
    assert [e for e in area.walk() if e in (notice, add_form(root))] == [notice, add_form(root)]
    assert [a.attrs["href"] for a in root.find_all("main")[0].find_all("a")] == ["/people"]
    world.tracker.set_operator_name("Sam")
    named = root_of(world)
    assert NOTICE not in comments_section(named).text()
    assert named.find_all("main")[0].find_all("a") == []
    world.tracker.set_operator_name("Lee")
    assert NOTICE not in comments_section(root_of(world)).text()


@pytest.mark.parametrize(
    ("query", "reason"),
    [
        ("comment_refused=blank&comment_text=%0A%20kept", BLANK_REASON),
        ("comment_refused=no-name&comment_text=%0A%20kept", NO_NAME_REASON),
    ],
    ids=["blank", "no-name"],
)
def test_comment_refusal_focuses_and_describes_the_textarea(
    tmp_path: Path, query: str, reason: str
) -> None:
    """CP-255, CP-256: the exact text kept, one field focus target and one reason describing it."""
    root = root_of(world_with(tmp_path, (comment("first"),), name=None), f"?{query}")
    field = text_field(root)
    assert focused(root) == [field]
    assert textarea_value(field) == "\n kept"
    assert description(field) == reason
    assert len(field.described_by()) == 1


def test_too_long_refusal_ignores_retained_text(tmp_path: Path) -> None:
    """CP-257: the reason beside the field, and none of a forged retained text."""
    query = "?comment_refused=too-long&comment_text=forged"
    shown_page = page(get(world_with(tmp_path).site, f"/tasks/1{query}"))
    assert "forged" not in shown_page
    root = parse(shown_page)
    field = text_field(root)
    assert focused(root) == [field] and textarea_value(field) == ""
    assert description(field) == TOO_LONG_REASON


def test_comment_failure_focuses_and_describes_add(tmp_path: Path) -> None:
    """CP-260: the text kept, Add focused, one failure line describing it, the line itself not."""
    root = root_of(world_with(tmp_path), "?comment_failed=add&comment_text=kept%0Atext")
    button = add_button(root)
    assert focused(root) == [button]
    assert description(button) == FAILURE_LINE and len(button.described_by()) == 1
    assert textarea_value(text_field(root)) == "kept\ntext"
    (line,) = button.described_by()
    assert "autofocus" not in line.attrs and "tabindex" not in line.attrs
    assert text_field(root).attrs.get("aria-describedby") != button.attrs["aria-describedby"]


def test_comment_added_outcome_focuses_the_addressed_position(tmp_path: Path) -> None:
    """CP-250: the addressed comment takes focus and one completion line describes it."""
    three = (comment("one"), comment("two"), comment("one"))
    root = root_of(world_with(tmp_path, three), "?comment_added=2")
    (target,) = focused(root)
    assert target is items(root)[1] and target.attrs["tabindex"] == "-1"
    assert description(target) == COMPLETION_LINE and len(target.described_by()) == 1
    (line,) = target.described_by()
    assert "autofocus" not in line.attrs and "tabindex" not in line.attrs
    assert textarea_value(text_field(root)) == ""
    four = (*three, comment("later", "Lee"))
    after = root_of(world_with(tmp_path, four), "?comment_added=2")
    (still,) = focused(after)
    assert still is items(after)[1] and body_of(still) == "two"


@pytest.mark.parametrize(
    "query",
    [
        "comment_refused=bogus",
        "comment_refused=",
        "comment_failed=bogus",
        "comment_failed=remove",
        "comment_added=abc",
        "comment_added=",
        "comment_added=0",
        "comment_added=-1",
        "comment_added=2.0",
        "comment_added=%202",
        "comment_added=4",
        pytest.param("comment_added=" + "9" * 5000, id="comment_added=a-position-beyond-int"),
        "comment_text=orphan",
        "comment_refused=bogus&comment_text=orphan",
    ],
)
def test_comment_query_accepts_only_recognized_outcomes(tmp_path: Path, query: str) -> None:
    """CP-250, CP-257: anything not a recognized outcome gives the ordinary comment area."""
    three = (comment("one"), comment("two"), comment("three"))
    shown_page = page(get(world_with(tmp_path, three).site, f"/tasks/1?{query}"))
    assert "orphan" not in shown_page
    root = parse(shown_page)
    assert focused(root) == [] and textarea_value(text_field(root)) == ""
    assert [e for e in comments_section(root).walk() if e.attrs.get("class") == "reason"] == []


def test_comment_query_precedence_between_outcomes(tmp_path: Path) -> None:
    """CP-250, CP-255, CP-260: refusal, then failure, then a valid position; comment first."""
    world = world_with(tmp_path, (comment("one"), comment("two")), labels=("ui",))
    both = root_of(
        world, "?comment_refused=blank&comment_failed=add&comment_added=1&comment_text=x"
    )
    assert focused(both) == [text_field(both)] and description(text_field(both)) == BLANK_REASON
    failed = root_of(world, "?comment_failed=add&comment_added=1&comment_text=x")
    assert focused(failed) == [add_button(failed)]
    added = root_of(world, "?comment_added=1&comment_failed=bogus")
    assert focused(added) == [items(added)[0]]
    crowded = root_of(
        world,
        "?comment_added=2&label_added=ui&added&saved&edit_refused=blank-title&title=zz"
        "&label_refused=empty",
    )
    assert focused(crowded) == [items(crowded)[1]]
    shown_ids = {e.attrs["id"] for e in crowded.walk() if "id" in e.attrs}
    assert shown_ids.isdisjoint({"label-added-line", "added-line", "saved-line", "label-reason"})
    other = root_of(world, "?comment_refused=bogus&label_removed=ui")
    (target,) = focused(other)
    assert target.tag == "h1" and "removed" in description(target)


def test_written_comments_offer_no_edit_delete_or_reply_control(tmp_path: Path) -> None:
    """CP-241, CP-247: nothing acts on a written comment; the label controls keep their scope."""
    world = world_with(tmp_path, (comment("a"), comment("b"), comment("c")), labels=("ui", "bug"))
    root = root_of(world)
    for item in items(root):
        interactive = ("a", "button", "form", "input", "textarea", "select")
        assert [e for e in item.walk() if e.tag in interactive] == []
    actions = [f.attrs["action"] for f in root.find_all("form")]
    assert actions == [
        "/tasks/1",
        "/tasks/1/move",
        "/tasks/1/move",
        "/tasks/1/labels/remove",
        "/tasks/1/labels/remove",
        "/tasks/1/labels",
        "/tasks/1/comments",
    ]
    removers = [f for f in root.find_all("form") if f.attrs["action"].endswith("/labels/remove")]
    assert [f.find_all("input")[0].attrs["value"] for f in removers] == ["ui", "bug"]
    text = root.text().lower()
    for absent in ("delete", "reply", "edit comment"):
        assert absent not in text, absent


def test_comment_outcomes_keep_one_focus_target_and_the_existing_page_contract(
    tmp_path: Path,
) -> None:
    """CP-250, CP-274: one focus target and no script, table or fragment; old outcomes unchanged."""
    world = world_with(tmp_path, (comment("a"), comment("b")), labels=("ui",))
    queries = {
        "?comment_refused=blank": 1,
        "?comment_refused=too-long": 1,
        "?comment_failed=add": 1,
        "?comment_added=2": 1,
        "?comment_added=2&comment_failed=add": 1,
        "?comment_refused=no-name&label_added=ui": 1,
        "?added": 1,
        "?saved": 1,
        "?label_added=ui": 1,
        "": 0,
    }
    for query, expected in queries.items():
        root = root_of(world, query)
        assert len(focused(root)) == expected, query
        for tag in ("script", "table"):
            assert root.find_all(tag) == [], (query, tag)
        facts = [dl for dl in root.find_all("dl") if "task-facts" in (dl.attrs.get("class") or "")]
        assert [[dt.text() for dt in dl.find_all("dt")] for dl in facts] == [["Project"]], query
        assert [
            a.attrs["href"] for a in root.find_all("a") if a.attrs["href"].startswith("#")
        ] == []
        for line in (p for p in root.find_all("p") if "reason" in (p.attrs.get("class") or "")):
            assert "autofocus" not in line.attrs and "tabindex" not in line.attrs
    added = root_of(world, "?added")
    (heading,) = focused(added)
    assert heading.tag == "h1" and "You added" in description(heading)
    labelled = root_of(world, "?label_added=ui")
    assert focused(labelled)[0].attrs["class"].split()[0] == "label-text"


def test_comment_presentation_vocabulary_is_closed() -> None:
    """CP-250, CP-255 to CP-260: the three refusal codes, and an area empty by default."""
    assert {member.value for member in pages.CommentRefusal} == {"too-long", "blank", "no-name"}
    area = pages.CommentArea()
    assert (area.text, area.refusal, area.failed, area.added_position) == ("", None, False, None)
    with pytest.raises(AttributeError):
        area.text = "changed"  # type: ignore[misc]
    assert "<h2>Comments</h2>" in pages.task_page(context_of(a_task(1, TITLE)))


HOSTILE_TITLE = "<b>A&B</b> \"quoted\" 'single'"


@pytest.mark.parametrize(
    ("area", "focus", "line"),
    [
        (
            pages.CommentArea(failed=True, text="kept"),
            "add-comment",
            (
                f"The tracker couldn't add your comment to '{HOSTILE_TITLE}', and nothing was "
                "changed. What you typed is still in the form. Try again."
            ),
        ),
        (
            pages.CommentArea(added_position=1),
            "comment-1",
            f"You added a comment to '{HOSTILE_TITLE}'.",
        ),
    ],
    ids=["failed", "added"],
)
def test_comment_lines_and_add_name_show_the_title_as_text(
    area: pages.CommentArea, focus: str, line: str
) -> None:
    """CP-243, CP-248, QC-36, SDD SEC-4: the title a comment line or Add's accessible name quotes is
    shown whole and as typed, as text, between the straight single quotes the text record gives."""
    base = a_task(1, HOSTILE_TITLE)
    task = Task(**{**base.__dict__, "comments": (comment("one"),)})
    html = pages.task_page(context_of(task), comment_area=area, operator_name="Sam")
    assert "<b>" not in html
    root = parse(html)
    assert add_button(root).attrs["aria-label"] == f"Add comment to '{HOSTILE_TITLE}'"
    (target,) = focused(root)
    assert target.attrs["id"] == focus
    assert description(target) == line
    identifiers = [e.attrs["id"] for e in root.walk() if "id" in e.attrs]
    assert len(identifiers) == len(set(identifiers))
