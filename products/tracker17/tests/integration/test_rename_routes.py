"""Integration tests of web's project rename request, run in one process with no socket (layer 3).

Checks SRS FR-9 (an action is reported done only after the save), FR-10 and FR-39 (the naming rules
and their refusals), FR-11 (every page shows the project's current name), FR-12 (renaming leaves
the project's tasks the same tasks), NFR-4 (a request from another site is refused), NFR-5 (typed
text is shown as text), NFR-8 (a failed save leaves the state as it was), and acceptance criteria
AC-12 and AC-18. Change spec rules CP-550 to CP-559, CP-561 and CP-563 and NFDR QC-31, QC-36, QC-49
and QC-56 are the ones each test names. Pages are read through the real Site, Tracker and SavedData
with an injected Clock; the handed fake is the saver, and no product name is patched.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, quote, urlencode, urlsplit

import pytest
from test_pages import HOSTILE, Element, parse
from test_routes import FORM, HOST, SAME_ORIGIN, get, header, page
from test_task_routes import World, add_task, focused, make_world

from web import Response, pages

OLD_NAME = "Alpha"
BLANK_REASON = "A project needs a name. Type one."
TOO_LONG_REASON = "A project name can't be longer than 200 characters. Type a shorter one."
FAILURE_LINE = (
    "The tracker couldn't rename the project to 'Beta', and nothing was changed. "
    "What you typed is still in the form. Try again."
)


def rename(
    world: World,
    project_id: int | str = 1,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    **fields: str,
) -> Response:
    sent = urlencode(fields).encode("utf-8") if body is None else body
    target = f"/projects/{project_id}/rename"
    return world.site.handle("POST", target, {**(headers or SAME_ORIGIN), **FORM}, sent)


def landed(world: World, response: Response) -> Element:
    assert response.status == 303
    return parse(page(get(world.site, header(response, "Location") or "")))


def project_view(world: World, query: str = "", project_id: int = 1) -> Element:
    return parse(page(get(world.site, f"/projects/{project_id}{query}")))


def rename_form(root: Element) -> Element:
    (form,) = [f for f in root.find_all("form") if (f.attrs["action"] or "").endswith("/rename")]
    return form


def name_field(root: Element) -> Element:
    (field,) = rename_form(root).find_all("input")
    return field


def save_button(root: Element) -> Element:
    (button,) = rename_form(root).find_all("button")
    return button


def line_of(element: Element) -> str:
    (line,) = element.described_by()
    return line.text()


def names_on_projects(world: World) -> list[str]:
    root = parse(page(get(world.site, "/")))
    return [
        a.text() for a in root.find_all("a") if (a.attrs.get("class") or "").startswith("project")
    ]


def state_of(world: World) -> tuple[object, ...]:
    tracker = world.tracker
    return (tracker.projects(), tracker.project_tasks(1), tracker.assignees())


def test_a_successful_rename_lands_once_with_one_described_completion(tmp_path: Path) -> None:
    """CP-549, CP-550: one press saves once, lands on the unfiltered project address with the
    new heading and title, the field holding the new name and described by the one line."""
    world = make_world(tmp_path)
    saves = world.saver.saves
    response = rename(world, name="Beta")
    assert world.saver.saves == saves + 1
    assert response.status == 303
    address = header(response, "Location") or ""
    parts = urlsplit(address)
    assert parts.path == "/projects/1" and parts.fragment == "" and "#" not in address
    assert parse_qs(parts.query) == {"rename_saved": ["Beta"], "rename_from": ["Alpha"]}
    root = landed(world, response)
    assert [h.text() for h in root.find_all("h1")] == ["Beta"]
    assert [t.text() for t in root.find_all("title")] == ["Beta: Tasks - tracker17"]
    field = name_field(root)
    assert focused(root) == [field] and field.attrs["value"] == "Beta"
    assert line_of(field) == "You renamed 'Alpha' to 'Beta'."


def test_the_completion_and_a_refusal_reload_without_saving(tmp_path: Path) -> None:
    """CP-550, CP-553, CP-556: reloading either location shows the same line, the same field and
    the same focus and saves nothing; the own name redirects bare and shows neither line nor focus."""
    world = make_world(tmp_path, projects=("Alpha", "Beta"))
    done = rename(world, name="Gamma")
    refused = rename(world, project_id=2, name="Gamma")
    saves = world.saver.saves
    for response in (done, refused):
        address = header(response, "Location") or ""
        first = page(get(world.site, address))
        for _ in range(2):
            assert page(get(world.site, address)) == first
    assert world.saver.saves == saves
    unchanged = rename(world, name="Gamma")
    assert header(unchanged, "Location") == "/projects/1"
    root = landed(world, unchanged)
    assert world.saver.saves == saves
    assert focused(root) == [] and "aria-describedby" not in name_field(root).attrs
    assert "renamed" not in root.text() and name_field(root).attrs["value"] == "Gamma"


def test_a_renamed_project_is_current_on_every_page(tmp_path: Path) -> None:
    """CP-551, CP-554: Alpha becomes Zed beside Gamma and delta; Projects order, the Tasks and
    Summary headings and titles, All tasks, each task's page and every address follow."""
    world = make_world(tmp_path, projects=("Alpha", "Gamma", "delta", "Empty"))
    add_task(world.site, title="One")
    add_task(world.site, title="Two")
    before_tasks = world.tracker.project_tasks(1)
    rename(world, name="Zed")
    assert names_on_projects(world) == ["delta", "Empty", "Gamma", "Zed"]
    tasks_view = project_view(world)
    assert [h.text() for h in tasks_view.find_all("h1")] == ["Zed"]
    summary = parse(page(get(world.site, "/projects/1/summary")))
    assert [h.text() for h in summary.find_all("h1")] == ["Zed"]
    assert [t.text() for t in summary.find_all("title")] == ["Zed: Summary - tracker17"]
    everything = page(get(world.site, "/tasks"))
    assert "Zed" in everything and "Alpha" not in everything
    for task in (1, 2):
        shown = page(get(world.site, f"/tasks/{task}"))
        assert "Zed" in shown and "Alpha" not in shown
    assert [t.text() for t in project_view(world, project_id=1).find_all("title")] == [
        "Zed: Tasks - tracker17"
    ]
    assert world.tracker.project_tasks(1) == before_tasks
    renamed_empty = rename(world, project_id=4, name="Hollow")
    assert [h.text() for h in landed(world, renamed_empty).find_all("h1")] == ["Hollow"]
    assert "Empty" not in names_on_projects(world)


@pytest.mark.parametrize(
    "sent", ["", "   ", "\t \n", "　  "], ids=["empty", "ascii", "mixed", "uni"]
)
def test_blank_rename_keeps_saved_data_and_typed_text(tmp_path: Path, sent: str) -> None:
    """CP-555, CP-556, CP-563: the creation reason beside the field, the typed text kept and
    focused, the heading and title as they were, saved bytes and state unchanged, zero saves."""
    world = make_world(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves, state_of(world))
    response = rename(world, name=sent)
    address = header(response, "Location") or ""
    assert parse_qs(urlsplit(address).query, keep_blank_values=True)["rename_refused"] == [
        "blank-name"
    ]
    root = landed(world, response)
    field = name_field(root)
    assert focused(root) == [field] and field.attrs["value"] == sent
    assert line_of(field) == BLANK_REASON
    assert [h.text() for h in root.find_all("h1")] == [OLD_NAME]
    assert [t.text() for t in root.find_all("title")] == ["Alpha: Tasks - tracker17"]
    assert (world.bytes_on_disk(), world.saver.saves, state_of(world)) == before


def test_duplicate_rename_keeps_saved_data_and_typed_text(tmp_path: Path) -> None:
    """CP-555, CP-556, CP-563: another project's exact name is refused with creation's reason,
    the typed text kept; a case or space variant is a different name and is accepted."""
    world = make_world(tmp_path, projects=("Alpha", "Beta"))
    before = (world.bytes_on_disk(), world.saver.saves, state_of(world))
    response = rename(world, name="Beta")
    root = landed(world, response)
    field = name_field(root)
    assert focused(root) == [field] and field.attrs["value"] == "Beta"
    assert line_of(field) == "A project named 'Beta' already exists. Choose a different name."
    assert [h.text() for h in root.find_all("h1")] == [OLD_NAME]
    assert (world.bytes_on_disk(), world.saver.saves, state_of(world)) == before
    for variant in ("beta", "Beta "):
        assert "rename_saved" in (header(rename(world, name=variant), "Location") or "")
        rename(world, name="Alpha")


@pytest.mark.parametrize("sent", ["ç" * 201, " " * 201, "x" * 201], ids=["ç", "spaces", "ascii"])
def test_an_overlong_rename_discards_all_submitted_text(tmp_path: Path, sent: str) -> None:
    """CP-555, CP-556, CP-563: a request no page sends is refused as too long before blank, with
    the saved name in the field and none of the sent text in the page or the address."""
    world = make_world(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves, state_of(world))
    response = rename(world, name=sent)
    address = header(response, "Location") or ""
    assert parse_qs(urlsplit(address).query, keep_blank_values=True) == {
        "rename_refused": ["too-long"]
    }
    shown = page(get(world.site, address))
    root = parse(shown)
    field = name_field(root)
    assert focused(root) == [field] and field.attrs["value"] == OLD_NAME
    assert line_of(field) == TOO_LONG_REASON
    assert (
        sent not in shown
        and quote(sent) not in address
        and (not sent.strip() or sent.strip() not in shown)
    )
    assert [h.text() for h in root.find_all("h1")] == [OLD_NAME]
    assert (world.bytes_on_disk(), world.saver.saves, state_of(world)) == before
    exact = rename(world, name="ç" * 200)
    assert "rename_saved" in (header(exact, "Location") or "")


@pytest.mark.parametrize("project", ["99", "0", "9" * 5000], ids=["absent", "zero", "huge"])
def test_a_missing_rename_project_answers_404_without_saving(tmp_path: Path, project: str) -> None:
    """CP-558, CP-563: the existing project not-found page, no Location, nothing saved, and no
    refusal wording of its own, even for an invalid name."""
    world = make_world(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    for sent in ("Beta", "", "x" * 201):
        response = rename(world, project_id=project, name=sent)
        assert response.status == 404 and header(response, "Location") is None
        assert response.body == pages.not_found_page().encode("utf-8")
    assert (world.bytes_on_disk(), world.saver.saves) == before


def test_a_stale_rename_checks_the_current_saved_state(tmp_path: Path) -> None:
    """CP-550, CP-553, CP-555: the typed name is compared with the name saved at that moment, never
    with the name the page showed."""
    world = make_world(tmp_path)
    world.tracker.create_project("Gamma", "")
    assert "rename_refused=name-in-use" in (header(rename(world, name="Gamma"), "Location") or "")
    world.tracker.rename_project(1, "Beta")
    done = rename(world, name="Delta")
    assert "rename_from=Beta" in (header(done, "Location") or "")
    world.tracker.rename_project(1, "Beta")
    back = rename(world, name="Alpha")
    assert "rename_from=Beta" in (header(back, "Location") or "")
    project = world.tracker.project(1)
    assert project is not None and project.name == "Alpha"
    saves = world.saver.saves
    assert header(rename(world, name="Alpha"), "Location") == "/projects/1"
    assert world.saver.saves == saves


def test_a_failed_rename_retains_text_and_focuses_save(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-557, QC-49, QC-56: nothing changes anywhere, the console names the rename then the
    error, Save takes focus described by the failure line, the field holds what was typed, and no
    Python text reaches the page or the address. Every page that shows the project's name still
    shows the old one."""
    world = make_world(tmp_path)
    add_task(world.site, title="One")
    before = (world.bytes_on_disk(), state_of(world))
    world.saver.failing = True
    capsys.readouterr()
    response = rename(world, name="Beta")
    assert capsys.readouterr().err.splitlines() == [
        "The tracker couldn't rename the project to 'Beta', and nothing was changed.",
        "PermissionError: the disk said no",
    ]
    address = header(response, "Location") or ""
    assert parse_qs(urlsplit(address).query) == {
        "rename_failed": ["save"],
        "rename_typed": ["Beta"],
    }
    shown = page(get(world.site, address))
    for leaked in ("PermissionError", "disk said no", "Traceback"):
        assert leaked not in shown and leaked not in address, leaked
    root = parse(shown)
    assert focused(root) == [save_button(root)]
    assert line_of(save_button(root)) == FAILURE_LINE
    assert name_field(root).attrs["value"] == "Beta"
    assert [h.text() for h in root.find_all("h1")] == [OLD_NAME]
    assert names_on_projects(world) == [OLD_NAME]
    summary = parse(page(get(world.site, "/projects/1/summary")))
    assert [h.text() for h in summary.find_all("h1")] == [OLD_NAME]
    assert [t.text() for t in summary.find_all("title")] == ["Alpha: Summary - tracker17"]
    for other in ("/tasks", "/tasks/1"):
        elsewhere = page(get(world.site, other))
        assert OLD_NAME in elsewhere and "Beta" not in elsewhere, other
    assert (world.bytes_on_disk(), state_of(world)) == before
    world.saver.failing = False
    assert "rename_saved=Beta" in (header(rename(world, name="Beta"), "Location") or "")


@pytest.mark.parametrize(
    "marks",
    [
        {"Host": HOST, "Sec-Fetch-Site": "cross-site"},
        {"Host": HOST, "Sec-Fetch-Site": "same-site"},
        {"Host": HOST, "Sec-Fetch-Site": "none"},
        {"Host": HOST},
        {"Host": "evil.example:8017", "Sec-Fetch-Site": "same-origin"},
    ],
    ids=["cross-site", "same-site", "none", "absent", "bad-host"],
)
def test_a_rename_passes_the_existing_request_checks(tmp_path: Path, marks: dict[str, str]) -> None:
    """CP-559, QC-31: refused before the body is read and before any action, nothing saved."""
    world = make_world(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves, state_of(world))
    for body in (b"name=Sneaky", b"name=%FF"):
        response = rename(world, headers=marks, body=body)
        assert response.status == 403 and response.body == b""
    assert (world.bytes_on_disk(), world.saver.saves, state_of(world)) == before
    assert header(rename(world, name="Fine"), "Location") is not None


def test_a_rename_normalizes_line_breaks_once_and_keeps_everything_else(tmp_path: Path) -> None:
    """RT-10, CP-552: CR LF and a lone CR are saved as LF; spaces and case stay as sent."""
    world = make_world(tmp_path)
    rename(world, body=b"name=%20a%0D%0Ab%0Dc%0Ad%20")
    project = world.tracker.project(1)
    assert project is not None and project.name == " a\nb\nc\nd "
    rename(world, name="alpha")
    project = world.tracker.project(1)
    assert project is not None and project.name == "alpha"


def test_a_rename_shows_hostile_text_literally(tmp_path: Path) -> None:
    """CP-561, CP-555: `<`, `&`, quotes and edge spaces show as typed in the field, heading, title,
    completion, Projects and the duplicate reason, which equals creation's for the same name."""
    world = make_world(tmp_path)
    name = f"  {HOSTILE}  "
    response = rename(world, name=name)
    shown = page(get(world.site, header(response, "Location") or ""))
    root = parse(shown)
    assert "<b>A&B</b>" not in shown
    assert name_field(root).attrs["value"] == name
    assert [h.text() for h in root.find_all("h1")] == [name]
    assert [t.text() for t in root.find_all("title")] == [f"{name}: Tasks - tracker17"]
    assert line_of(name_field(root)) == f"You renamed 'Alpha' to '{name}'."
    assert names_on_projects(world) == [name]
    world.tracker.create_project("Other", "")
    refused = landed(world, rename(world, project_id=2, name=name))
    reason = line_of(name_field(refused))
    creation = parse(page(get(world.site, _create_refusal_address(world, name))))
    (create_reason,) = [p for p in creation.find_all("p") if p.attrs.get("id") == "name-reason"]
    assert (
        reason
        == create_reason.text()
        == f"A project named '{name}' already exists. Choose a different name."
    )


def _create_refusal_address(world: World, name: str) -> str:
    response = world.site.handle(
        "POST",
        "/projects",
        {**SAME_ORIGIN, **FORM},
        urlencode({"name": name, "description": ""}).encode(),
    )
    return header(response, "Location") or ""


@pytest.mark.parametrize(
    "query",
    [
        "?rename_refused=too-long&rename_typed=Forged",
        "?rename_refused=bogus&rename_typed=Forged",
        "?rename_failed=other&rename_typed=Forged",
        "?rename_saved=Forged",
        "?rename_typed=Forged",
    ],
    ids=["too-long-typed", "unknown-refusal", "unknown-failure", "saved-alone", "typed-alone"],
)
def test_forged_or_unknown_rename_markers_render_the_ordinary_area(
    tmp_path: Path, query: str
) -> None:
    """CP-556: a forged too-long address drops the typed text, and a code the page does not know
    is inert: the field holds the saved name, with no line and no autofocus."""
    world = make_world(tmp_path)
    root = project_view(world, query)
    assert "Forged" not in page(get(world.site, f"/projects/1{query}"))
    assert name_field(root).attrs["value"] == OLD_NAME
    if "too-long" in query:
        assert line_of(name_field(root)) == TOO_LONG_REASON
    else:
        assert focused(root) == [] and "aria-describedby" not in name_field(root).attrs
