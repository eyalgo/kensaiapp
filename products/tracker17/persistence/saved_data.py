"""The saved data: where the file is, its format, the read at start and the whole-state save.

Realizes SRS DR-2, DR-4, DR-6 and NFR-2. The file is `tracker.json` in one directory, a JSON object
holding the project counter, the projects, the assignee names in their order, the task counter, the
tasks and the operator name, and nothing else. Three older forms still read: data written before
the assignee list holds the project counter and the projects alone, data written before tasks adds
the assignees, and data written before the operator name holds both and the tasks. Each is read
as having no assignees, no tasks and a task counter of 1, or no operator name; a read never
rewrites it, and the first save writes the full form, which always carries `operator_name` as text
or null. The only rules applied here are the file's shape and types and the decoding of an
instant; every data rule, the operator name's included, comes from `domain.restore_state` and
`domain.restore_task`, whose refusal is reported as unreadable.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from domain import Comment, Refusal, Task, TrackerState, restore_state, restore_task
from errors import AppError

DEFAULT_LOCATION = Path(__file__).resolve().parent.parent / "data"
FILE_NAME = "tracker.json"
PARTIAL_FILE_NAME = "tracker.json.partial"
LEGACY_STATE_KEYS = {"next_project_id", "projects"}
PEOPLE_STATE_KEYS = LEGACY_STATE_KEYS | {"assignees"}
TASK_STATE_KEYS = PEOPLE_STATE_KEYS | {"next_task_id", "tasks"}
STATE_KEYS = TASK_STATE_KEYS | {"operator_name"}
SUPPORTED_STATE_KEYS = (LEGACY_STATE_KEYS, PEOPLE_STATE_KEYS, TASK_STATE_KEYS, STATE_KEYS)
PROJECT_KEYS = {"id", "name", "description"}
TASK_KEYS = {
    "id",
    "project_id",
    "title",
    "status",
    "priority",
    "assignee",
    "labels",
    "due_date",
    "created_at",
    "comments",
}
COMMENT_KEYS = {"text", "author", "created_at"}


class UnreadableData(AppError):
    """The saved data cannot be read in full, or breaks a rule. Carries where it is."""

    def __init__(self, location: Path) -> None:
        super().__init__(location)
        self.location = location


def _is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_text_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _encode_instant(instant: datetime) -> str:
    return instant.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _decode_instant(value: object) -> datetime:
    """The aware instant the text names, in UTC, or ValueError for anything else."""
    try:
        instant = datetime.fromisoformat(value)  # type: ignore[arg-type]
    except TypeError as error:
        raise ValueError("a saved instant is not text") from error
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("a saved instant names no time zone")
    return instant.astimezone(UTC)


class SavedData:
    """One saved-data location holding one file, `tracker.json`."""

    def __init__(self, location: Path) -> None:
        self.location = location

    def load(self) -> TrackerState | None:
        """The saved state, or None when no saved data exists yet. Never writes."""
        try:
            raw = (self.location / FILE_NAME).read_bytes()
        except FileNotFoundError:
            return None
        except OSError as error:
            raise UnreadableData(self.location) from error
        try:
            document = json.loads(raw.decode("utf-8"))
            projects, next_project_id, assignees, tasks, next_task_id, operator_name = self._unpack(
                document
            )
            return restore_state(
                projects,
                next_project_id,
                assignees,
                tasks=tasks,
                next_task_id=next_task_id,
                operator_name=operator_name,
            )
        except (ValueError, Refusal) as error:
            raise UnreadableData(self.location) from error

    def save(self, state: TrackerState) -> None:
        """Replace the saved data whole and atomically, creating the location when missing."""
        document = {
            "next_project_id": state.next_project_id,
            "projects": [
                {"id": project.id, "name": project.name, "description": project.description}
                for project in state.projects
            ],
            "assignees": list(state.assignees),
            "next_task_id": state.next_task_id,
            "tasks": [self._encode_task(task) for task in state.tasks],
            "operator_name": state.operator_name,
        }
        encoded = json.dumps(document, ensure_ascii=False, indent=2).encode("utf-8")
        self.location.mkdir(parents=True, exist_ok=True)
        partial = self.location / PARTIAL_FILE_NAME
        with open(partial, "wb") as partial_file:
            partial_file.write(encoded)
            partial_file.flush()
            os.fsync(partial_file.fileno())
        os.replace(partial, self.location / FILE_NAME)

    @staticmethod
    def _encode_task(task: Task) -> dict[str, object]:
        return {
            "id": task.id,
            "project_id": task.project_id,
            "title": task.title,
            "status": task.status.value,
            "priority": task.priority.value,
            "assignee": task.assignee,
            "labels": list(task.labels),
            "due_date": None if task.due_date is None else task.due_date.isoformat(),
            "created_at": _encode_instant(task.created_at),
            "comments": [
                {
                    "text": comment.text,
                    "author": comment.author,
                    "created_at": _encode_instant(comment.created_at),
                }
                for comment in task.comments
            ],
        }

    @staticmethod
    def _unpack(
        document: object,
    ) -> tuple[list[tuple[int, str, str]], int, list[str], list[Task], int, str | None]:
        if not isinstance(document, dict) or set(document) not in SUPPORTED_STATE_KEYS:
            raise ValueError("the saved data is not the expected shape")
        next_project_id = document["next_project_id"]
        entries = document["projects"]
        assignees = document.get("assignees", [])
        next_task_id = document.get("next_task_id", 1)
        task_entries = document.get("tasks", [])
        operator_name = document.get("operator_name")
        if not _is_integer(next_project_id) or not isinstance(entries, list):
            raise ValueError("the saved data is not the expected shape")
        if not isinstance(assignees, list) or not all(isinstance(name, str) for name in assignees):
            raise ValueError("the saved assignees are not a list of text")
        if operator_name is not None and not isinstance(operator_name, str):
            raise ValueError("the saved operator name is neither text nor null")
        if not _is_integer(next_task_id) or not isinstance(task_entries, list):
            raise ValueError("the saved tasks are not the expected shape")
        projects: list[tuple[int, str, str]] = []
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != PROJECT_KEYS:
                raise ValueError("a saved project is not the expected shape")
            identity, name, description = entry["id"], entry["name"], entry["description"]
            if (
                not _is_integer(identity)
                or not isinstance(name, str)
                or not isinstance(description, str)
            ):
                raise ValueError("a saved project is not the expected shape")
            projects.append((identity, name, description))
        tasks = [SavedData._decode_task(entry) for entry in task_entries]
        return projects, next_project_id, assignees, tasks, next_task_id, operator_name

    @staticmethod
    def _decode_task(entry: object) -> Task:
        """The shape and types of one saved task, then domain's own value rules over it."""
        if not isinstance(entry, dict) or set(entry) != TASK_KEYS:
            raise ValueError("a saved task is not the expected shape")
        text_fields = (entry["title"], entry["status"], entry["priority"])
        optional_text = (entry["assignee"], entry["due_date"])
        if (
            not _is_integer(entry["id"])
            or not _is_integer(entry["project_id"])
            or not all(isinstance(value, str) for value in text_fields)
            or not all(value is None or isinstance(value, str) for value in optional_text)
            or not _is_text_list(entry["labels"])
            or not isinstance(entry["comments"], list)
        ):
            raise ValueError("a saved task is not the expected shape")
        return restore_task(
            id=entry["id"],
            project_id=entry["project_id"],
            title=entry["title"],
            status=entry["status"],
            priority=entry["priority"],
            assignee=entry["assignee"],
            labels=entry["labels"],
            due_date=entry["due_date"],
            created_at=_decode_instant(entry["created_at"]),
            comments=[SavedData._decode_comment(comment) for comment in entry["comments"]],
        )

    @staticmethod
    def _decode_comment(entry: object) -> Comment:
        if (
            not isinstance(entry, dict)
            or set(entry) != COMMENT_KEYS
            or not isinstance(entry["text"], str)
            or not isinstance(entry["author"], str)
        ):
            raise ValueError("a saved comment is not the expected shape")
        return Comment(
            text=entry["text"],
            author=entry["author"],
            created_at=_decode_instant(entry["created_at"]),
        )
