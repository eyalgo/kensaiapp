"""Integration tests of the Summary page builder, each page read back as a browser parses it (layer 4).

Checks SRS FR-38 (a project's summary as numbers, nine of them links), NFR-5 (typed text is shown
as text) and NFR-12 (state is carried by words, every control has a name). Change spec rules
CP-491, CP-492, CP-494, CP-496, CP-501, CP-502, CP-512 and CP-513 to CP-515 and CP-521 to CP-522,
and NFDR QC-36, are the ones each test names; the design rows are T01, T06, T08, T09 and T18. The
page is built from values handed in, so no rule is recomputed here.
"""

from __future__ import annotations

from test_pages import Element, parse

from application import (
    AssigneeCount,
    Priority,
    PriorityCount,
    Project,
    ProjectSummary,
    StatusCount,
    TaskStatus,
)
from web import pages

HOSTILE = '<b>&"x"</b>'
STATUS_WORDS = ("todo", "in-progress", "done", "cancelled")
PRIORITY_WORDS = ("low", "medium", "high", "critical")
GROUP_HEADINGS = ["Tasks by status", "Tasks by priority", "Due dates", "Open tasks by assignee"]


def make_summary(
    project: Project,
    *,
    statuses: tuple[int, int, int, int] = (2, 1, 1, 1),
    priorities: tuple[int, int, int, int] = (1, 1, 1, 2),
    overdue: int = 1,
    undated: int = 2,
    assignees: tuple[tuple[str | None, int], ...] = (("ari", 1), ("bo", 0), ("eve", 1), (None, 1)),
) -> ProjectSummary:
    return ProjectSummary(
        project=project,
        total=sum(statuses),
        status_counts=tuple(StatusCount(s, n) for s, n in zip(TaskStatus, statuses, strict=True)),
        priority_counts=tuple(
            PriorityCount(p, n) for p, n in zip(Priority, priorities, strict=True)
        ),
        overdue=overdue,
        no_due_date=undated,
        assignee_counts=tuple(AssigneeCount(name, n) for name, n in assignees),
    )


ALPHA = Project(id=1, name="Alpha", description="notes")


def groups(root: Element) -> list[Element]:
    return [e for e in root.find_all("section") if e.attrs.get("class") == "sheet summary-group"]


def rows_of(group: Element) -> list[tuple[str, str]]:
    return [
        (row.find_all("th")[0].text(), row.find_all("td")[0].text())
        for row in group.find_all("tr")
        if row.find_all("td")
    ]


def column_headers(group: Element) -> list[str]:
    return [cell.text() for cell in group.find_all("thead")[0].find_all("th")]


def main_links(root: Element) -> list[tuple[str, str]]:
    (main,) = root.find_all("main")
    return [(link.attrs["href"] or "", link.text()) for link in main.find_all("a")]


def count_cell_anchors(root: Element) -> list[Element]:
    """Every anchor that sits inside a count cell of a Summary group, in page order."""
    return [
        a for group in groups(root) for cell in group.find_all("td") for a in cell.find_all("a")
    ]


def count_links(root: Element) -> list[tuple[str, str, str]]:
    """Each count anchor as (address, accessible name, visible text), in page order."""
    return [
        (a.attrs["href"] or "", a.attrs.get("aria-label") or "", a.text())
        for a in count_cell_anchors(root)
    ]


def expected_name(count: int, singular: str, plural: str) -> str:
    """The change text's name for one link: the singular form at 1, the plural form otherwise."""
    return f"{count} {singular}" if count == 1 else f"{count} {plural}"


def expected_count_links(
    project_id: int,
    statuses: tuple[int, ...],
    priorities: tuple[int, ...],
    overdue: int,
) -> list[tuple[str, str, str]]:
    """The nine links of one Summary in page order, from the change text artifact's strings."""
    base = f"/projects/{project_id}"
    links = [
        (
            f"{base}?filter_status={word}",
            expected_name(n, f"task in {word}", f"tasks in {word}"),
            str(n),
        )
        for word, n in zip(STATUS_WORDS, statuses, strict=True)
    ]
    links += [
        (
            f"{base}?filter_priority={word}",
            expected_name(n, f"task with {word} priority", f"tasks with {word} priority"),
            str(n),
        )
        for word, n in zip(PRIORITY_WORDS, priorities, strict=True)
    ]
    links.append(
        (
            f"{base}?filter_overdue=on",
            expected_name(overdue, "overdue task", "overdue tasks"),
            str(overdue),
        )
    )
    return links


def test_summary_has_all_ordered_plain_rows_and_only_allowed_links() -> None:
    """CP-491, CP-494, CP-496, CP-513 to CP-515, CP-512, T01, T08: total first, every status and
    priority with its numeral, overdue, undated, the assignees last; one title; no form, script or
    refresh; the only links are the view pair and the nine count links, each holding only its
    numeral; no label, Total, no-due-date or assignee count sits inside a link or a control."""
    page = pages.summary_page(make_summary(ALPHA))
    root = parse(page)
    assert page.startswith('<!doctype html>\n<html lang="en">')
    assert [e.text() for e in root.find_all("title")] == ["Alpha: Summary - tracker17"]
    (heading,) = root.find_all("h1")
    assert heading.text() == "Alpha"
    nine = expected_count_links(1, (2, 1, 1, 1), (1, 1, 1, 2), 1)
    assert main_links(root) == [
        ("/projects/1", "Tasks"),
        ("/projects/1/summary", "Summary"),
        *[(href, text) for href, _, text in nine],
    ]
    assert count_links(root) == nine
    assert [e.text() for e in root.find_all("h2")] == GROUP_HEADINGS
    status, priority, due, assignee = groups(root)
    assert column_headers(status) == ["Status", "Tasks"]
    assert rows_of(status) == [
        ("Total", "5"),
        ("todo", "2"),
        ("in-progress", "1"),
        ("done", "1"),
        ("cancelled", "1"),
    ]
    assert column_headers(priority) == ["Priority", "Tasks"]
    assert rows_of(priority) == [("low", "1"), ("medium", "1"), ("high", "1"), ("critical", "2")]
    assert column_headers(due) == ["Due date", "Tasks"]
    assert rows_of(due) == [("Overdue", "1"), ("No due date", "2")]
    assert column_headers(assignee) == ["Assignee", "Open tasks"]
    assert rows_of(assignee) == [("ari", "1"), ("bo", "0"), ("eve", "1"), ("(unassigned)", "1")]
    for tag in ("form", "script", "button", "input", "select", "textarea"):
        assert root.find_all(tag) == [], tag
    assert [m for m in root.find_all("meta") if "http-equiv" in m.attrs] == []
    for cell in root.find_all("th"):
        node: Element | None = cell
        while node is not None:
            assert node.tag not in {"a", "button"}, cell.text()
            node = node.parent
    linked_rows = [row.find_all("th")[0].text() for row in root.find_all("tr") if row.find_all("a")]
    assert linked_rows == [
        "todo",
        "in-progress",
        "done",
        "cancelled",
        "low",
        "medium",
        "high",
        "critical",
        "Overdue",
    ]
    for anchor in count_cell_anchors(root):
        assert [c for c in anchor.children if isinstance(c, Element)] == []
        assert anchor.text().isdecimal()


def test_zero_rows_are_kept_and_the_populated_summary_has_no_invitation() -> None:
    """CP-496, CP-499, CP-513, CP-515, T01, T08: a zero is the numeral 0, never a blank or a
    missing row, and every selected zero count still has its link."""
    root = parse(
        pages.summary_page(make_summary(ALPHA, statuses=(3, 0, 0, 0), priorities=(0, 3, 0, 0)))
    )
    status, priority, _, _ = groups(root)
    assert rows_of(status)[1:] == [
        ("todo", "3"),
        ("in-progress", "0"),
        ("done", "0"),
        ("cancelled", "0"),
    ]
    assert rows_of(priority) == [("low", "0"), ("medium", "3"), ("high", "0"), ("critical", "0")]
    assert root.find_all("p") == []
    assert count_links(root) == expected_count_links(1, (3, 0, 0, 0), (0, 3, 0, 0), 1)


def test_empty_summary_invites_first_task_beside_all_zero_rows() -> None:
    """CP-502, CP-513, CP-515, T01, T08: every row reads 0 and every selected zero count keeps its
    link; the invitation's only link is the base Tasks address."""
    zero = make_summary(
        Project(id=3, name="Gamma", description=""),
        statuses=(0, 0, 0, 0),
        priorities=(0, 0, 0, 0),
        overdue=0,
        undated=0,
        assignees=(("ari", 0), (None, 0)),
    )
    root = parse(pages.summary_page(zero))
    sheets = groups(root)
    assert len(sheets) == 4
    for sheet in sheets:
        assert {count for _, count in rows_of(sheet)} == {"0"}
    assert rows_of(sheets[3]) == [("ari", "0"), ("(unassigned)", "0")]
    (invitation,) = root.find_all("p")
    assert invitation.text() == "This project has no tasks yet. Open Tasks to add the first task."
    (link,) = invitation.find_all("a")
    assert (link.attrs["href"], link.text()) == ("/projects/3", "Tasks")
    nine = expected_count_links(3, (0, 0, 0, 0), (0, 0, 0, 0), 0)
    assert count_links(root) == nine
    assert main_links(root) == [
        ("/projects/3", "Tasks"),
        ("/projects/3/summary", "Summary"),
        ("/projects/3", "Tasks"),
        *[(href, text) for href, _, text in nine],
    ]


def test_summary_count_names_identify_zero_one_and_many_tasks() -> None:
    """CP-521, CP-522, T06: every category names zero, one and many tasks with the change text's
    own strings, the numeral first and the visible text an unbroken prefix; 12 todo and 3 overdue
    are the two pinned examples; equal names imply equal addresses across the Summary's links, on
    a Summary whose nine counts share one numeral and on an empty one, whose two Tasks links share a
    name and an address."""
    for statuses, priorities, overdue in (
        ((0, 0, 0, 0), (0, 0, 0, 0), 0),
        ((1, 1, 1, 1), (1, 1, 1, 1), 1),
        ((12, 2, 5, 3), (4, 6, 7, 11), 3),
    ):
        summary = make_summary(
            ALPHA, statuses=statuses, priorities=priorities, overdue=overdue, undated=0
        )
        links = count_links(parse(pages.summary_page(summary)))
        assert links == expected_count_links(1, statuses, priorities, overdue)
        for _, name, visible in links:
            assert name.startswith(visible + " ")
    twelve = count_links(
        parse(pages.summary_page(make_summary(ALPHA, statuses=(12, 0, 0, 0), overdue=3)))
    )
    assert twelve[0][1] == "12 tasks in todo"
    assert twelve[8][1] == "3 overdue tasks"
    singular = count_links(
        parse(
            pages.summary_page(make_summary(ALPHA, statuses=(1, 1, 1, 1), priorities=(1, 1, 1, 1)))
        )
    )
    assert [name for _, name, _ in singular] == [
        "1 task in todo",
        "1 task in in-progress",
        "1 task in done",
        "1 task in cancelled",
        "1 task with low priority",
        "1 task with medium priority",
        "1 task with high priority",
        "1 task with critical priority",
        "1 overdue task",
    ]
    same_numeral = make_summary(ALPHA, statuses=(2, 2, 2, 2), priorities=(2, 2, 2, 2), overdue=2)
    empty = make_summary(
        Project(id=3, name="Gamma", description=""),
        statuses=(0, 0, 0, 0),
        priorities=(0, 0, 0, 0),
        overdue=0,
        undated=0,
        assignees=((None, 0),),
    )
    for summary in (same_numeral, empty):
        root = parse(pages.summary_page(summary))
        every = [
            (a.attrs["href"], a.attrs.get("aria-label") or a.text()) for a in root.find_all("a")
        ]
        for first in every:
            for second in every:
                if first[1] == second[1]:
                    assert first[0] == second[0], (first, second)
    # On the empty project the invitation's Tasks link shares the view link's name and address,
    # which CP-522 allows, and the nine 0 links still have nine names.
    empty_root = parse(pages.summary_page(empty))
    tasks_links = [a.attrs["href"] for a in empty_root.find_all("a") if a.text() == "Tasks"]
    assert tasks_links == ["/projects/3", "/projects/3"]
    assert len({name for _, name, _ in count_links(empty_root)}) == 9


def test_assignee_identity_never_selects_a_count_link() -> None:
    """CP-514, CP-515, T18, QC-36: listed and unlisted assignees spelled todo, low, Overdue and
    (unassigned) keep plain counts beside the real categories and the real unassigned bucket,
    and hostile text, padding and a long name stay text."""
    names = ("todo", "low", "Overdue", "(unassigned)", HOSTILE, f" {'n' * 300} ")
    summary = make_summary(
        ALPHA,
        assignees=tuple((name, index + 1) for index, name in enumerate(names)) + ((None, 9),),
    )
    root = parse(pages.summary_page(summary))
    assignee_group = groups(root)[3]
    assert assignee_group.find_all("a") == []
    assert rows_of(assignee_group) == [
        *[(name, str(index + 1)) for index, name in enumerate(names)],
        ("(unassigned)", "9"),
    ]
    assert count_links(root) == expected_count_links(1, (2, 1, 1, 1), (1, 1, 1, 2), 1)
    no_due = groups(root)[2]
    assert [row.find_all("a") for row in no_due.find_all("tr") if "No due date" in row.text()] == [
        []
    ]


def test_project_and_assignee_text_is_escaped_without_normalization() -> None:
    """CP-492, CP-501, QC-36, T09: markup characters, padding and long text come out as typed text
    in the heading, the title and the cells; a listed name spelled (unassigned) is a row of its own
    beside the real unassigned row."""
    long_name = "n" * 300
    padded = Project(id=2, name=f"  {HOSTILE}  ", description="")
    summary = make_summary(
        padded, assignees=((HOSTILE, 1), (f" {long_name} ", 2), ("(unassigned)", 3), (None, 4))
    )
    page = pages.summary_page(summary)
    assert "<b>" not in page and '"x"' not in page.split("<main>")[1]
    root = parse(page)
    assert [e.text() for e in root.find_all("title")] == [f"  {HOSTILE}  : Summary - tracker17"]
    (heading,) = root.find_all("h1")
    assert heading.text() == f"  {HOSTILE}  "
    assert root.find_all("b") == []
    assert rows_of(groups(root)[3]) == [
        (HOSTILE, "1"),
        (f" {long_name} ", "2"),
        ("(unassigned)", "3"),
        ("(unassigned)", "4"),
    ]
    for cell in groups(root)[3].find_all("th"):
        assert "pre-wrap" in (cell.attrs.get("class") or "") or cell.attrs.get("scope") == "col"


def test_project_page_title_and_pair_are_the_tasks_view_forms() -> None:
    """CP-491, CP-492, T09: the Tasks view is titled for its view, the pair sits under the heading,
    and the name's spaces are kept in the title."""
    root = parse(pages.project_page(Project(id=7, name="  Alpha  ", description="d"), task_count=0))
    assert [e.text() for e in root.find_all("title")] == ["  Alpha  : Tasks - tracker17"]
    assert main_links(root)[:2] == [("/projects/7", "Tasks"), ("/projects/7/summary", "Summary")]
    (main,) = root.find_all("main")
    elements = [child for child in main.children if isinstance(child, Element)]
    assert [e.tag for e in elements[:2]] == ["h1", "nav"]
    assert elements[1].attrs["aria-label"] == "Project views"
