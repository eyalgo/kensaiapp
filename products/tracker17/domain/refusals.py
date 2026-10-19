"""One typed refusal per refused condition (SRS FR-39).

Every refusal derives from Refusal, so a part that must tell a refusal from any other failure can do
it by type alone. No refusal carries wording shown to the operator: the words are the content
stage's, and `web` maps each type to its reason.
"""

from __future__ import annotations

from enum import Enum

from errors import AppError


class TextField(str, Enum):
    """The text fields a length maximum applies to. The values are what an address carries."""

    NAME = "name"
    DESCRIPTION = "description"
    TITLE = "title"
    LABEL = "label"
    COMMENT = "comment"


class Refusal(AppError):
    """Base of every refusal: a value the rules do not accept."""


class BlankName(Refusal):
    """The name has no character other than whitespace, or is empty."""


class NameInUse(Refusal):
    """Another project already has exactly this name."""


class AssigneeNameInUse(Refusal):
    """The assignee list already holds exactly this name."""


class AssigneeNotFound(Refusal):
    """The assignee list holds no name exactly equal to the one to remove."""


class BlankTitle(Refusal):
    """The task title has no character other than whitespace, or is empty."""


class ProjectNotFound(Refusal):
    """No project holds the identity a task refers to."""


class AssigneeNotListed(Refusal):
    """The assignee list does not hold the name a task is given or changed to. Carries the name."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.name = name


class TaskNotFound(Refusal):
    """No task holds the identity an edit refers to."""


class EmptyLabel(Refusal):
    """The label holds no character at all. A label of spaces is a label."""


class LabelNotCarried(Refusal):
    """The task carries no label exactly equal to the one to remove."""


class RepeatedSavedLabel(Refusal):
    """Saved data holds one task carrying the same label twice, compared exactly."""


class BlankComment(Refusal):
    """The comment text has no character other than whitespace, or is empty."""


class OperatorNameNotSet(Refusal):
    """A comment is added while no operator name is saved, so it has no author."""


class InvalidPriority(Refusal):
    """The priority is not one of the four."""


class InvalidDueDate(Refusal):
    """The due date is not a calendar date written `YYYY-MM-DD`."""


class InvalidTaskStatus(Refusal):
    """The status is not one of the four."""


class TextTooLong(Refusal):
    """A value is longer than its field's maximum."""

    def __init__(self, field: TextField, maximum: int) -> None:
        super().__init__(field, maximum)
        self.field = field
        self.maximum = maximum


class IdentityReused(Refusal):
    """Saved data holds two projects or two tasks with one identity, or one not below its counter.

    A task identity that is not a positive integer, or a counter below 1, is refused the same way.
    """
