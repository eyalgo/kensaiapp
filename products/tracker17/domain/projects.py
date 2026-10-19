"""The Projects feature entry point: the project entity and the rules that accept or refuse one.

Realizes SRS FR-10, FR-11, FR-39 and FR-40 and data requirement DR-1.

Taking part: application/tracker.py applies these rules and saves the result; web/pages.py shows
the projects and the create form, and web/routes.py turns a submission into a create and a refusal
into its reason. persistence/saved_data.py restores a saved state through restore_state.

Checked by: tests/unit/test_projects.py and tests/unit/test_state.py (the rules),
tests/integration/test_tracker.py, tests/integration/test_pages.py and
tests/integration/test_routes.py (the actions and pages), and tests/e2e/test_first_project.py (the
whole path in a browser).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from domain.refusals import BlankName, NameInUse, TextField
from domain.text import LONG_TEXT_MAX, SHORT_TEXT_MAX, ensure_within

if TYPE_CHECKING:
    from domain.state import TrackerState


@dataclass(frozen=True)
class Project:
    """A project. An empty description means the project has none."""

    id: int
    name: str
    description: str


def check_project_values(name: str, description: str) -> None:
    """Apply the rules every project value obeys, in the order that fixes which refusal wins.

    Over-long comes before blank, so a submission that is over-long and also blank gives the
    over-long reason, and the name wins when both values are over-long (CP-20).
    """
    ensure_within(TextField.NAME, name, SHORT_TEXT_MAX)
    ensure_within(TextField.DESCRIPTION, description, LONG_TEXT_MAX)
    if all(character.isspace() for character in name):
        raise BlankName()


def create_project(
    state: TrackerState, name: str, description: str
) -> tuple[TrackerState, Project]:
    """Return the state after creating the project, and the project, or raise a refusal."""
    check_project_values(name, description)
    if any(existing.name == name for existing in state.projects):
        raise NameInUse()
    project = Project(id=state.next_project_id, name=name, description=description)
    new_state = replace(
        state,
        projects=(*state.projects, project),
        next_project_id=state.next_project_id + 1,
    )
    return new_state, project


def list_projects(state: TrackerState) -> tuple[Project, ...]:
    """Every project by name with letter case ignored; the exact name breaks a tie."""
    return tuple(
        sorted(state.projects, key=lambda project: (project.name.casefold(), project.name))
    )


def find_project(state: TrackerState, project_id: int) -> Project | None:
    """The project with this identity, or None."""
    for project in state.projects:
        if project.id == project_id:
            return project
    return None
