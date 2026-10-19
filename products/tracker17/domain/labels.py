"""The Labels feature entry point: the rules that accept or refuse a label and keep a task's labels.

Realizes SRS FR-23 (a task's labels are added and removed one at a time, each kept exactly as typed
and compared exactly), FR-39 and FR-40 (refusals and the label maximum), DR-6 (saved labels are
checked by the same rules) and NFR-9 (the trace from the requirement to this code).

Taking part: domain/tasks.py applies these rules to a task and checks the labels a saved task
carries; application/tracker.py saves a change the rules report and publishes it, and
application/__init__.py hands the refusal types on; web/pages.py shows the label area, and
web/routes.py turns a submission into an add or a remove and each refusal into its reason.

Checked by: tests/unit/test_labels.py and tests/unit/test_tasks.py (the rules and the task actions),
tests/architecture/test_shapes.py and tests/architecture/test_trace.py (the entry and the shape),
tests/integration/test_label_tracker.py (the actions through the Tracker),
tests/integration/test_label_pages.py (the label area), tests/integration/test_label_routes.py and
tests/integration/test_routes.py (the requests), tests/integration/test_label_listener.py (the real
listener), tests/integration/test_saved_data.py and tests/integration/test_start.py (the saved
labels and the start), tests/e2e/test_labels.py (the browser), and
tests/integration/test_timed_run.py with tests/timed_run.py (the timed harness at task volume).
"""

from __future__ import annotations

from collections.abc import Iterable

from domain.refusals import EmptyLabel, LabelNotCarried, RepeatedSavedLabel, TextField
from domain.text import SHORT_TEXT_MAX, ensure_within


def check_label(value: str) -> str:
    """The label as given, or raise EmptyLabel or TextTooLong.

    Nothing is stripped, case-folded or shortened: a label of spaces is accepted, and a label is as
    long as its Unicode code points.
    """
    ensure_within(TextField.LABEL, value, SHORT_TEXT_MAX)
    if value == "":
        raise EmptyLabel()
    return value


def check_saved_labels(labels: Iterable[str]) -> tuple[str, ...]:
    """The labels as a tuple in the order given, or the refusal of the first one that breaks a rule.

    Each label must keep the rules an add applies, and no label may be given twice. Two labels are
    one only when they are exactly equal; an empty collection is readable.
    """
    checked: list[str] = []
    seen: set[str] = set()
    for label in labels:
        check_label(label)
        if label in seen:
            raise RepeatedSavedLabel()
        seen.add(label)
        checked.append(label)
    return tuple(checked)


def add_label(labels: tuple[str, ...], label: str) -> tuple[tuple[str, ...], bool]:
    """The labels with the new one last and True, or the same labels and False when already carried.

    The label is checked first. A label the task already carries, compared exactly, is no change.
    """
    check_label(label)
    if label in labels:
        return labels, False
    return (*labels, label), True


def remove_label(labels: tuple[str, ...], label: str) -> tuple[str, ...]:
    """The labels without the exactly matching one, the others in their order, or raise
    LabelNotCarried.

    Membership alone decides: a value no task could carry is a label not carried, not an add error.
    """
    if label not in labels:
        raise LabelNotCarried()
    return tuple(carried for carried in labels if carried != label)
