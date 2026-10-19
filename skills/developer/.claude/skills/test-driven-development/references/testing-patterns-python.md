# Testing Patterns — Python

Quick reference for common testing patterns in Python with pytest. Use alongside the `test-driven-development` skill.

## Table of Contents

- [Test Structure (Arrange-Act-Assert)](#test-structure-arrange-act-assert)
- [Test Naming Conventions](#test-naming-conventions)
- [Common Assertions](#common-assertions)
- [Fake Implementations (prefer over mocks)](#fake-implementations-prefer-over-mocks)
- [Mocking Patterns](#mocking-patterns)
- [Parametrize](#parametrize)
- [Fixtures](#fixtures)
- [Integration Testing](#integration-testing)
- [CLI Testing](#cli-testing)
- [Test Anti-Patterns](#test-anti-patterns)

---

## Test Structure (Arrange-Act-Assert)

```python
def test_creates_task_with_default_status():
    # Arrange: set up test data and preconditions
    repo = InMemoryTaskRepository()
    service = TaskService(repo)

    # Act: perform the action being tested
    task = service.create_task(title="Buy groceries")

    # Assert: verify the outcome
    assert task.title == "Buy groceries"
    assert task.status == TaskStatus.TODO
    assert task.id is not None
```

---

## Test Naming Conventions

```python
# Pattern: test_<what>_<expected behavior>_<condition if any>
class TestTaskServiceCreate:
    def test_creates_task_with_default_todo_status(self): ...
    def test_raises_value_error_when_title_is_empty(self): ...
    def test_trims_whitespace_from_title(self): ...
    def test_assigns_unique_id_to_each_task(self): ...

# Module-level: same pattern
def test_task_complete_sets_status_to_done(): ...
def test_task_complete_records_completed_at_timestamp(): ...
```

---

## Common Assertions

```python
# Equality
assert result == expected
assert result != unexpected

# None
assert result is None
assert result is not None

# Boolean
assert condition
assert not condition

# Exceptions
with pytest.raises(ValueError):
    Task(title="")

with pytest.raises(ValueError, match="Title is required"):
    Task(title="")

with pytest.raises(TaskNotFoundError) as exc_info:
    service.get_task("nonexistent-id")
assert "nonexistent-id" in str(exc_info.value)

# Containers
assert item in collection
assert item not in collection
assert len(collection) == 3
assert collection == [task_a, task_b, task_c]

# Approximate equality (floats)
assert result == pytest.approx(0.3, abs=1e-6)

# Dataclass field access
assert task.status == TaskStatus.DONE
assert task.title == "Buy groceries"
assert task.completed_at is not None
```

---

## Fake Implementations (prefer over mocks)

Use in-memory fakes for repositories and services. They have real behavior, run fast, and don't break on refactors.

```python
class InMemoryTaskRepository:
    def __init__(self):
        self._store: dict[str, Task] = {}

    def save(self, task: Task) -> Task:
        self._store[task.id] = task
        return task

    def find_by_id(self, task_id: str) -> Task | None:
        return self._store.get(task_id)

    def find_all(self) -> list[Task]:
        return list(self._store.values())

    def delete(self, task_id: str) -> None:
        self._store.pop(task_id, None)


# Use in tests — no patching needed
def test_saves_and_retrieves_task():
    repo = InMemoryTaskRepository()
    task = Task(title="Test")

    repo.save(task)

    assert repo.find_by_id(task.id) == task
```

**Fake a clock** (instead of mocking `datetime.now`):

```python
from abc import abstractmethod, ABC

class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime: ...

class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now()

class FakeClock(Clock):
    def __init__(self, fixed: datetime):
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed


def test_completed_at_matches_clock():
    fixed_time = datetime(2025, 1, 15, 10, 30)
    clock = FakeClock(fixed_time)
    service = TaskService(repo=InMemoryTaskRepository(), clock=clock)

    task = service.create_task("Test")
    completed = service.complete_task(task.id)

    assert completed.completed_at == fixed_time
```

---

## Mocking Patterns

Use `unittest.mock` (stdlib) or `pytest-mock` (`mocker` fixture). Prefer fakes; reach for mocks only at system boundaries.

### When mocks are appropriate

```
Mock these:                        Don't mock these:
├── External HTTP APIs             ├── In-memory repositories
├── File system (in some cases)    ├── Business logic
├── Email / SMS senders            ├── Data transformations
├── External payment services      ├── Domain entities
└── Non-deterministic system calls └── Pure functions
```

### `unittest.mock`

```python
from unittest.mock import MagicMock, patch

# Mock a collaborator directly
def test_notifies_assignee_on_task_complete():
    notifier = MagicMock()
    service = TaskService(repo=InMemoryTaskRepository(), notifier=notifier)

    task = service.create_task("Test", assignee="alice")
    service.complete_task(task.id)

    notifier.notify.assert_called_once_with(
        user="alice",
        message=f"Task '{task.title}' completed"
    )

# Patch a module-level dependency
def test_logs_completion():
    with patch("tracker2.application.logger") as mock_logger:
        service = TaskService(repo=InMemoryTaskRepository())
        service.complete_task("some-id")
        mock_logger.info.assert_called()
```

### `pytest-mock`

```python
def test_sends_email_on_assignment(mocker):
    mock_send = mocker.patch("tracker2.notifications.send_email")
    service = TaskService(repo=InMemoryTaskRepository())

    service.assign_task("task-id", assignee="alice@example.com")

    mock_send.assert_called_once_with(
        to="alice@example.com",
        subject=mocker.ANY,
    )
```

---

## Parametrize

```python
@pytest.mark.parametrize("title,expected_error", [
    ("", "Title is required"),
    ("   ", "Title is required"),
    ("a" * 256, "Title too long"),
])
def test_task_title_validation(title: str, expected_error: str):
    with pytest.raises(ValueError, match=expected_error):
        Task(title=title)


@pytest.mark.parametrize("status", [
    TaskStatus.TODO,
    TaskStatus.IN_PROGRESS,
    TaskStatus.ON_HOLD,
])
def test_incomplete_statuses_are_not_done(status: TaskStatus):
    task = Task(title="Test", status=status)
    assert not task.is_done


# Parametrize with IDs for readable test names
@pytest.mark.parametrize("priority,expected_score", [
    pytest.param(Priority.HIGH, 3, id="high"),
    pytest.param(Priority.MEDIUM, 2, id="medium"),
    pytest.param(Priority.LOW, 1, id="low"),
])
def test_priority_score(priority: Priority, expected_score: int):
    assert priority.score == expected_score
```

---

## Fixtures

```python
# conftest.py — shared fixtures
import pytest

@pytest.fixture
def repo() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()

@pytest.fixture
def service(repo: InMemoryTaskRepository) -> TaskService:
    return TaskService(repo=repo)

@pytest.fixture
def existing_task(repo: InMemoryTaskRepository) -> Task:
    task = Task(title="Existing task")
    repo.save(task)
    return task


# Use in tests
def test_complete_existing_task(service: TaskService, existing_task: Task):
    completed = service.complete_task(existing_task.id)
    assert completed.status == TaskStatus.DONE
```

**Scope fixtures** to control lifetime:

```python
@pytest.fixture(scope="session")   # once per test session
@pytest.fixture(scope="module")    # once per test module
@pytest.fixture(scope="function")  # default: once per test
```

---

## Integration Testing

Integration tests hit real dependencies (real file I/O, real JSON persistence). Keep them in a separate directory and run them with a marker.

```python
# tests/integration/test_json_repository.py
import pytest
from pathlib import Path

@pytest.mark.integration
def test_persists_and_loads_tasks(tmp_path: Path):
    db_file = tmp_path / "tasks.json"
    repo = JsonTaskRepository(db_file)

    task = Task(title="Persisted task")
    repo.save(task)

    # Load a fresh repo from the same file
    repo2 = JsonTaskRepository(db_file)
    loaded = repo2.find_by_id(task.id)

    assert loaded == task


@pytest.mark.integration
def test_handles_missing_file_gracefully(tmp_path: Path):
    db_file = tmp_path / "nonexistent.json"
    repo = JsonTaskRepository(db_file)

    result = repo.find_all()

    assert result == []
```

Run unit tests only (default): `pytest tests/unit/`  
Run integration tests: `pytest tests/integration/ -m integration`

---

## CLI Testing

Test CLI commands with `subprocess` or a framework-native runner.

```python
# With subprocess (works for any CLI)
import subprocess
import sys

def test_cli_create_task(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "tracker2", "task", "add", "Buy groceries"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Buy groceries" in result.stdout


# With Click's test runner (if using Click)
from click.testing import CliRunner
from tracker2.cli import app

def test_cli_add_task():
    runner = CliRunner(mix_stderr=False)
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["task", "add", "Buy groceries"])

    assert result.exit_code == 0
    assert "Buy groceries" in result.output
```

---

## Test Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| `assert mock.called` without specifics | Doesn't verify arguments | Use `assert_called_once_with(...)` |
| Mocking internals | Tests break on refactor even if behavior is unchanged | Mock at system boundaries only |
| `time.sleep` in tests | Slow, non-deterministic | Inject a `FakeClock` |
| `datetime.now()` in production code | Untestable | Inject a `Clock` abstraction |
| Shared mutable fixtures | Tests pollute each other | Use function-scoped fixtures or copy data |
| Testing `__repr__` or `__str__` | Tests framework behavior | Only test YOUR logic |
| Catching and silencing exceptions | Masks real failures | Let tests fail loudly |
| `monkeypatch` on everything | Same problems as mocking internals | Use fakes instead |
