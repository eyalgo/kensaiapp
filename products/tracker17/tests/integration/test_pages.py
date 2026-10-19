"""Integration tests of web's page builders, each page read back as a browser parses it (layer 4).

Checks SRS FR-10 and FR-11 (create and list projects), NFR-4 (no outside content or script) and
NFR-5 (typed text is shown as text), and acceptance criteria AC-6 and AC-12. Change spec rules CP-9
to CP-13, CP-17 to CP-20, CP-23 and CP-30 to CP-38 and NFDR QC-33 and QC-36 are the ones each test
names. The tests
check where a reason or a line sits and which control it describes, never its words, so they hold
against whatever the content stage supplies.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

import pytest

from application import LONG_TEXT_MAX, SHORT_TEXT_MAX, Project, TextField
from web import pages

VOID_TAGS = {"input", "meta", "link", "br", "img", "hr"}
HOSTILE = '<b>A&B</b> "quoted"'


class Element:
    def __init__(self, tag: str, attrs: dict[str, str | None], parent: Element | None) -> None:
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: list[Element | str] = []

    def text(self) -> str:
        return "".join(child if isinstance(child, str) else child.text() for child in self.children)

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Element):
                yield from child.walk()

    def find_all(self, tag: str) -> list[Element]:
        return [element for element in self.walk() if element.tag == tag]

    def by_id(self, identifier: str) -> Element | None:
        for element in self.walk():
            if element.attrs.get("id") == identifier:
                return element
        return None

    def described_by(self) -> list[Element]:
        root = self
        while root.parent is not None:
            root = root.parent
        identifiers = (self.attrs.get("aria-describedby") or "").split()
        return [found for found in (root.by_id(i) for i in identifiers) if found is not None]


class _Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Element("#document", {}, None)
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        element = Element(tag, dict(attrs), self.current)
        self.current.children.append(element)
        if tag not in VOID_TAGS:
            self.current = element

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        node = self.current
        while node.parent is not None and node.tag != tag:
            node = node.parent
        if node.parent is not None:
            self.current = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def parse(page: str) -> Element:
    parser = _Parser()
    parser.feed(page)
    parser.close()
    return parser.root


def textarea_value(textarea: Element) -> str:
    """The textarea's value as the HTML parser sets it: one leading line feed is dropped."""
    return textarea.text().removeprefix("\n")


def name_field(root: Element) -> Element:
    (field,) = [e for e in root.find_all("input") if e.attrs.get("name") == "name"]
    return field


def description_field(root: Element) -> Element:
    (field,) = [e for e in root.find_all("textarea") if e.attrs.get("name") == "description"]
    return field


def create_button(root: Element) -> Element:
    (button,) = root.find_all("button")
    return button


def main_text(root: Element) -> str:
    (main,) = root.find_all("main")
    return main.text()


PROJECTS = [
    Project(id=1, name="Alpha", description="first one"),
    Project(id=2, name="beta", description=""),
]


def all_pages() -> dict[str, str]:
    alpha = Project(id=1, name="Alpha", description="notes")
    return {
        "first run": pages.projects_page([]),
        "list": pages.projects_page(PROJECTS),
        "blank": pages.projects_page(PROJECTS, refusal=pages.BLANK_NAME, name=" ", description="d"),
        "in use": pages.projects_page(
            PROJECTS, refusal=pages.NAME_IN_USE, name="Alpha", description="d"
        ),
        "too long": pages.projects_page(
            PROJECTS, refusal=pages.TEXT_TOO_LONG, field=TextField.NAME
        ),
        "failed": pages.projects_page(PROJECTS, failed=True, name="Alpha", description="d"),
        "people": pages.people_page([]),
        "people list": pages.people_page(["Dana", "Ari"]),
        "people added": pages.people_page(["Dana"], added="Dana"),
        "project": pages.project_page(alpha),
        "created": pages.project_page(alpha, created=True),
        "not found": pages.not_found_page(),
    }


def test_the_note_number_equals_the_description_maxlength() -> None:
    """CP-11."""
    root = parse(pages.projects_page([]))
    description = description_field(root)
    notes = description.described_by()
    assert notes, "the description field has no note"
    numbers = [int(n) for note in notes for n in re.findall(r"\d+", note.text())]
    maxlength = int(description.attrs["maxlength"])
    assert maxlength == LONG_TEXT_MAX
    assert numbers == [maxlength]
    name = name_field(root)
    assert int(name.attrs["maxlength"]) == SHORT_TEXT_MAX
    assert name.described_by() == []
    assert str(SHORT_TEXT_MAX) not in main_text(root)


def test_every_page_has_a_header_with_the_projects_and_people_links() -> None:
    """CP-9, CP-80."""
    for label, page in all_pages().items():
        root = parse(page)
        (header,) = root.find_all("header")
        links = header.find_all("a")
        assert [(link.attrs["href"], link.text()) for link in links] == [
            ("/", "Projects"),
            ("/people", "People"),
        ], label
        assert header.text().startswith("tracker17"), label
        for link in root.find_all("a"):
            href = link.attrs["href"] or ""
            assert re.fullmatch(r"/|/people|/projects/\d+", href), (label, href)
        for forbidden in ("all tasks", "rename", "delete"):
            assert forbidden not in root.text().lower(), (label, forbidden)


def test_the_first_run_page_says_there_are_no_projects_and_has_the_form() -> None:
    """CP-10."""
    root = parse(pages.projects_page([]))
    assert "There are no projects yet. Type a name for your first project and press Create." in (
        main_text(root)
    )
    assert root.find_all("ul") == []
    (form,) = root.find_all("form")
    assert form.attrs["method"] == "post"
    assert form.attrs["action"] == "/projects"
    assert name_field(root).attrs["type"] == "text"
    assert create_button(root).text() == "Create"
    labels = {label.attrs["for"]: label.text() for label in root.find_all("label")}
    assert labels[name_field(root).attrs["id"]] == "Name"
    assert labels[description_field(root).attrs["id"]] == "Description"


def test_the_list_shows_names_as_links_in_order_with_descriptions() -> None:
    """CP-12. The page lists in the order handed; a project without a description shows none."""
    root = parse(pages.projects_page(PROJECTS))
    assert "There are no projects yet" not in main_text(root)
    (listing,) = root.find_all("ul")
    items = listing.find_all("li")
    assert [item.find_all("a")[0].text() for item in items] == ["Alpha", "beta"]
    assert [item.find_all("a")[0].attrs["href"] for item in items] == ["/projects/1", "/projects/2"]
    assert "first one" in items[0].text()
    assert items[1].text() == "beta"


def test_a_project_page_shows_name_description_the_invitation_and_only_the_add_form() -> None:
    """CP-17, CP-106, CP-126. The no-form and no-invitation clauses are replaced by the add form
    and the first-task invitation (design § 5); every excluded control is still absent."""
    root = parse(pages.project_page(Project(id=7, name="  Alpha  ", description="line1\nline2")))
    (heading,) = root.find_all("h1")
    assert heading.text() == "  Alpha  "
    assert "line1\nline2" in main_text(root)
    assert "This project has no tasks yet. Give the first task a title and press Add." in (
        main_text(root)
    )
    (form,) = root.find_all("form")
    assert form.attrs["action"] == "/projects/7/tasks"
    assert root.find_all("textarea") == [] and root.find_all("table") == []
    assert [e.attrs["name"] for e in form.find_all("input")] == ["title", "due_date"]
    assert [e.attrs["name"] for e in form.find_all("select")] == ["priority", "assignee"]
    (button,) = root.find_all("button")
    assert button.text() == "Add"
    assert [e.text() for e in root.find_all("title")] == ["  Alpha   - tracker17"]


def test_the_created_line_names_the_project() -> None:
    """CP-18."""
    project = Project(id=3, name=" Alpha ", description="")
    with_flag = parse(pages.project_page(project, created=True))
    without = parse(pages.project_page(project))
    assert "You created ' Alpha '." in with_flag.text()
    assert "You created" not in without.text()


def test_values_are_escaped_everywhere() -> None:
    """CP-23, QC-36."""
    project = Project(id=1, name=HOSTILE, description=HOSTILE)
    listed = pages.projects_page([project])
    on_project = pages.project_page(project, created=True)
    refused = pages.projects_page(
        [project], refusal=pages.NAME_IN_USE, name=HOSTILE, description=HOSTILE
    )
    failed = pages.projects_page([project], failed=True, name=HOSTILE, description=HOSTILE)
    for page in (listed, on_project, refused, failed):
        assert "<b>" not in page
        assert '"quoted"' not in page  # a bare quote would end an attribute early
    assert parse(listed).find_all("a")[2].text() == HOSTILE
    assert HOSTILE in main_text(parse(listed))
    project_root = parse(on_project)
    assert project_root.find_all("h1")[0].text() == HOSTILE
    assert HOSTILE in project_root.by_id("created-line").text()
    for page in (refused, failed):
        root = parse(page)
        assert name_field(root).attrs["value"] == HOSTILE
        assert textarea_value(description_field(root)) == HOSTILE
    assert HOSTILE in parse(refused).by_id("name-reason").text()
    assert HOSTILE in parse(failed).by_id("create-failure").text()


def test_a_description_starting_with_a_line_break_keeps_it() -> None:
    """The textarea start tag is followed by one line feed the parser drops, then the value."""
    description = "\nsecond line"
    page = pages.projects_page([], refusal=pages.BLANK_NAME, name=" ", description=description)
    assert textarea_value(description_field(parse(page))) == description
    assert re.search(r"<textarea[^>]*>\n\nsecond line</textarea>", page)
    project = Project(id=1, name="Alpha", description=description)
    shown = parse(pages.project_page(project))
    assert description in main_text(shown)


def test_no_page_has_a_script_a_meta_policy_or_an_outside_address() -> None:
    """QC-33, CP-23."""
    for label, page in all_pages().items():
        root = parse(page)
        assert root.find_all("script") == [], label
        for meta in root.find_all("meta"):
            assert "http-equiv" not in meta.attrs, label
        assert re.search(r"on[a-z]+\s*=", page) is None, label
        for element in root.walk():
            for attribute in ("src", "href", "action"):
                value = element.attrs.get(attribute)
                if value is not None:
                    assert value.startswith("/") and not value.startswith("//"), (label, value)
        assert "http://" not in page and "https://" not in page, label
        assert [e.attrs["href"] for e in root.find_all("link")] == ["/style.css"], label


@pytest.mark.parametrize("refusal", [pages.BLANK_NAME, pages.NAME_IN_USE])
def test_the_refused_page_puts_focus_and_the_reason_on_the_name_field(refusal: str) -> None:
    """CP-19."""
    name = " " if refusal == pages.BLANK_NAME else "Alpha"
    root = parse(pages.projects_page(PROJECTS, refusal=refusal, name=name, description="notes"))
    field = name_field(root)
    assert "autofocus" in field.attrs
    reasons = field.described_by()
    assert len(reasons) == 1 and reasons[0].text().strip()
    assert reasons[0] is root.by_id("name-reason")
    assert "autofocus" not in description_field(root).attrs
    assert "autofocus" not in create_button(root).attrs
    assert textarea_value(description_field(root)) == "notes"
    assert field.attrs["value"] == name
    # The reason sits beside the name field: both are in the same field group.
    assert reasons[0].parent is field.parent


@pytest.mark.parametrize(
    ("field", "focused", "other"),
    [(TextField.DESCRIPTION, "description", "name"), (TextField.NAME, "name", "description")],
)
def test_a_too_long_refusal_focuses_the_field_that_was_too_long(
    field: TextField, focused: str, other: str
) -> None:
    """CP-20. The page holds no typed values, and the reason names no sent text."""
    root = parse(pages.projects_page(PROJECTS, refusal=pages.TEXT_TOO_LONG, field=field))
    controls = {"name": name_field(root), "description": description_field(root)}
    assert "autofocus" in controls[focused].attrs
    assert "autofocus" not in controls[other].attrs
    reason_ids = {e.attrs.get("id") for e in controls[focused].described_by()}
    assert f"{focused}-reason" in reason_ids
    assert root.by_id(f"{focused}-reason").text().strip()
    assert "value" not in controls["name"].attrs or controls["name"].attrs["value"] == ""
    assert textarea_value(controls["description"]) == ""


def test_a_failed_page_focuses_the_create_button_and_keeps_typed_values() -> None:
    """EX-4, EX-14."""
    root = parse(pages.projects_page(PROJECTS, failed=True, name="Alpha", description="d\ne"))
    button = create_button(root)
    assert "autofocus" in button.attrs
    (failure,) = button.described_by()
    assert failure.text().strip()
    assert failure is root.by_id("create-failure")
    assert "autofocus" not in name_field(root).attrs
    assert name_field(root).attrs["value"] == "Alpha"
    assert textarea_value(description_field(root)) == "d\ne"
    for forbidden in ("Traceback", "Error:", "errno"):
        assert forbidden.lower() not in root.text().lower()


def test_the_created_project_page_opens_on_its_heading() -> None:
    """EX-5, EX-14."""
    project = Project(id=1, name="Alpha", description="")
    root = parse(pages.project_page(project, created=True))
    (heading,) = root.find_all("h1")
    assert "autofocus" in heading.attrs
    (line,) = heading.described_by()
    assert line is root.by_id("created-line")
    assert "Alpha" in line.text()
    plain = parse(pages.project_page(project))
    assert "autofocus" not in plain.find_all("h1")[0].attrs


def test_the_not_found_page_has_one_heading_and_one_link_to_projects() -> None:
    """CP-33, CP-34."""
    root = parse(pages.not_found_page())
    assert len(root.find_all("h1")) == 1
    (main,) = root.find_all("main")
    (link,) = main.find_all("a")
    assert link.attrs["href"] == "/"
    (header,) = root.find_all("header")
    assert [anchor.attrs["href"] for anchor in header.find_all("a")] == ["/", "/people"]
    assert len(root.find_all("a")) == 3
    assert root.find_all("form") == []


def test_the_not_found_page_gives_projects_in_a_paragraph_after_its_heading() -> None:
    """CP-33: the sentence, then Projects as the place to go, in a paragraph directly in main."""
    (main,) = parse(pages.not_found_page()).find_all("main")
    children = [child for child in main.children if isinstance(child, Element)]
    assert [child.tag for child in children] == ["h1", "p"]
    heading, paragraph = children
    assert heading.find_all("a") == []
    (link,) = paragraph.find_all("a")
    assert link.parent is paragraph


def test_the_not_found_page_has_no_form_or_control() -> None:
    """CP-34."""
    root = parse(pages.not_found_page())
    for tag in ("form", "input", "textarea", "button"):
        assert root.find_all(tag) == [], tag


def test_the_not_found_page_says_nothing_of_a_task() -> None:
    """CP-33."""
    text = main_text(parse(pages.not_found_page())).lower()
    assert "task" not in text
    assert "delete" not in text and "gone" not in text


def test_the_not_found_page_title_names_it() -> None:
    """CP-33."""
    title = parse(pages.not_found_page()).find_all("title")[0].text()
    assert title != parse(pages.projects_page([])).find_all("title")[0].text()
    assert title.endswith(" - tracker17")


def test_the_not_found_page_takes_no_address() -> None:
    """CP-33: no part of an address can reach the page."""
    with pytest.raises(TypeError):
        pages.not_found_page("/projects/99")  # type: ignore[call-arg]
