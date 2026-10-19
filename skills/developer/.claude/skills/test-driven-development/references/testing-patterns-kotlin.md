# Testing Patterns — Kotlin

Quick reference for common testing patterns in Kotlin with JUnit 5 and MockK. Use alongside the `test-driven-development` skill.

## Table of Contents

- [Test Structure (Arrange-Act-Assert)](#test-structure-arrange-act-assert)
- [Test Naming Conventions](#test-naming-conventions)
- [Common Assertions](#common-assertions)
- [Fake Implementations (prefer over mocks)](#fake-implementations-prefer-over-mocks)
- [Mocking Patterns (MockK)](#mocking-patterns-mockk)
- [Parametrized Tests](#parametrized-tests)
- [Test Fixtures and Lifecycle](#test-fixtures-and-lifecycle)
- [Integration Testing](#integration-testing)
- [Test Anti-Patterns](#test-anti-patterns)

---

## Test Structure (Arrange-Act-Assert)

```kotlin
@Test
fun `creates task with default TODO status`() {
    // Arrange: set up test data and preconditions
    val repo = InMemoryTaskRepository()
    val service = TaskService(repo)

    // Act: perform the action being tested
    val task = service.createTask(title = "Buy groceries")

    // Assert: verify the outcome
    assertEquals("Buy groceries", task.title)
    assertEquals(TaskStatus.TODO, task.status)
    assertNotNull(task.id)
}
```

---

## Test Naming Conventions

```kotlin
// Backtick names read like specifications
class TaskServiceCreateTest {
    @Test fun `creates task with default TODO status`() {}
    @Test fun `throws IllegalArgumentException when title is empty`() {}
    @Test fun `trims whitespace from title`() {}
    @Test fun `assigns unique id to each task`() {}
}

// Nested classes for grouping behaviors
class TaskTest {
    @Nested
    inner class Complete {
        @Test fun `sets status to DONE`() {}
        @Test fun `records completedAt timestamp`() {}
        @Test fun `is idempotent when task is already done`() {}
    }

    @Nested
    inner class Validation {
        @Test fun `throws when title is blank`() {}
        @Test fun `throws when title exceeds 255 characters`() {}
    }
}
```

---

## Common Assertions

```kotlin
// JUnit 5 (org.junit.jupiter.api.Assertions)
assertEquals(expected, actual)
assertNotEquals(unexpected, actual)
assertNull(result)
assertNotNull(result)
assertTrue(condition)
assertFalse(condition)

// Exception assertions
val exception = assertThrows<IllegalArgumentException> {
    Task(title = "")
}
assertTrue(exception.message!!.contains("Title is required"))

// Multiple assertions (all run even if one fails)
assertAll(
    { assertEquals(TaskStatus.DONE, task.status) },
    { assertNotNull(task.completedAt) },
    { assertEquals("Buy groceries", task.title) }
)

// Collection assertions
assertEquals(3, tasks.size)
assertTrue(task in tasks)
assertFalse(deletedTask in tasks)
assertEquals(listOf(task1, task2), tasks)

// Approximate equality (Double)
assertEquals(0.3, result, 1e-6)
```

### With assertk (recommended addition)

```kotlin
// assertk gives richer failure messages
import assertk.assertThat
import assertk.assertions.*

assertThat(task.title).isEqualTo("Buy groceries")
assertThat(task.status).isEqualTo(TaskStatus.TODO)
assertThat(task.id).isNotNull()
assertThat(tasks).hasSize(3)
assertThat(tasks).contains(task)
assertThat { Task(title = "") }.isFailure()
    .hasClass(IllegalArgumentException::class)
    .hasMessage("Title is required")
```

---

## Fake Implementations (prefer over mocks)

```kotlin
// In-memory repository — real behavior, no I/O
class InMemoryTaskRepository : TaskRepository {
    private val store = mutableMapOf<String, Task>()

    override fun save(task: Task): Task = task.also { store[it.id] = it }
    override fun findById(id: String): Task? = store[id]
    override fun findAll(): List<Task> = store.values.toList()
    override fun delete(id: String) { store.remove(id) }
}

// Use in tests
@Test
fun `saves and retrieves task by id`() {
    val repo = InMemoryTaskRepository()
    val task = Task(title = "Test")

    repo.save(task)

    assertEquals(task, repo.findById(task.id))
}
```

**Fake a clock** (instead of mocking `LocalDateTime.now()`):

```kotlin
interface Clock {
    fun now(): LocalDateTime
}

class SystemClock : Clock {
    override fun now(): LocalDateTime = LocalDateTime.now()
}

class FakeClock(private val fixed: LocalDateTime) : Clock {
    override fun now(): LocalDateTime = fixed
}


@Test
fun `completed_at matches clock time`() {
    val fixedTime = LocalDateTime.of(2025, 1, 15, 10, 30)
    val service = TaskService(
        repo = InMemoryTaskRepository(),
        clock = FakeClock(fixedTime)
    )

    val task = service.createTask("Test")
    val completed = service.completeTask(task.id)

    assertEquals(fixedTime, completed.completedAt)
}
```

---

## Mocking Patterns (MockK)

Use [MockK](https://mockk.io) for mocking in Kotlin. Prefer fakes; reach for mocks only at system boundaries.

### When mocks are appropriate

```
Mock these:                        Don't mock these:
├── External HTTP APIs             ├── In-memory repositories
├── File system (in some cases)    ├── Business logic
├── Email / SMS senders            ├── Data transformations
├── External payment services      ├── Domain entities
└── Non-deterministic system calls └── Pure functions
```

### MockK basics

```kotlin
import io.mockk.*

@Test
fun `notifies assignee on task completion`() {
    val notifier = mockk<Notifier>()
    every { notifier.notify(any(), any()) } just Runs

    val service = TaskService(
        repo = InMemoryTaskRepository(),
        notifier = notifier
    )
    val task = service.createTask("Test", assignee = "alice")
    service.completeTask(task.id)

    verify(exactly = 1) {
        notifier.notify(
            user = "alice",
            message = match { it.contains("Test") }
        )
    }
}

// Stubbing return values
val repo = mockk<TaskRepository>()
every { repo.findById("id-1") } returns Task(id = "id-1", title = "Test")
every { repo.findAll() } returns emptyList()

// Stubbing exceptions
every { repo.findById("bad-id") } throws TaskNotFoundException("bad-id")

// Verify no interaction
verify { notifier wasNot Called }

// Relaxed mock (all calls return defaults)
val mock = mockk<TaskRepository>(relaxed = true)
```

### Spy (partial mock)

```kotlin
val service = spyk(TaskService(repo = InMemoryTaskRepository()))
every { service.sendNotification(any()) } just Runs

service.completeTask("task-id")

verify { service.sendNotification(any()) }
```

---

## Parametrized Tests

```kotlin
// JUnit 5 @ParameterizedTest
@ParameterizedTest
@ValueSource(strings = ["", "   ", "\t"])
fun `throws when title is blank`(title: String) {
    assertThrows<IllegalArgumentException> { Task(title = title) }
}

// With a method source
companion object {
    @JvmStatic
    fun invalidTitles() = Stream.of(
        Arguments.of("", "Title is required"),
        Arguments.of("   ", "Title is required"),
        Arguments.of("a".repeat(256), "Title too long"),
    )
}

@ParameterizedTest
@MethodSource("invalidTitles")
fun `validates title correctly`(title: String, expectedMessage: String) {
    val exception = assertThrows<IllegalArgumentException> { Task(title = title) }
    assertTrue(exception.message!!.contains(expectedMessage))
}

// With a data class for readability
data class PriorityCase(val priority: Priority, val expectedScore: Int)

@ParameterizedTest
@MethodSource("priorityCases")
fun `priority maps to correct score`(case: PriorityCase) {
    assertEquals(case.expectedScore, case.priority.score)
}

companion object {
    @JvmStatic
    fun priorityCases() = listOf(
        PriorityCase(Priority.HIGH, 3),
        PriorityCase(Priority.MEDIUM, 2),
        PriorityCase(Priority.LOW, 1),
    )
}
```

---

## Test Fixtures and Lifecycle

```kotlin
class TaskServiceTest {
    private lateinit var repo: InMemoryTaskRepository
    private lateinit var service: TaskService

    @BeforeEach
    fun setUp() {
        repo = InMemoryTaskRepository()
        service = TaskService(repo)
    }

    @AfterEach
    fun tearDown() {
        // Clean up resources if needed
    }

    @Test
    fun `creates task`() {
        val task = service.createTask("Test")
        assertNotNull(task.id)
    }
}

// Companion object for once-per-class setup
companion object {
    @JvmStatic
    @BeforeAll
    fun setUpClass() { /* expensive shared setup */ }
}
```

**Builder / factory helpers for readable tests:**

```kotlin
// Test factory with sensible defaults
fun aTask(
    title: String = "Default title",
    status: TaskStatus = TaskStatus.TODO,
    assignee: String? = null,
    id: String = UUID.randomUUID().toString(),
) = Task(id = id, title = title, status = status, assignee = assignee)

// Use in tests
@Test
fun `project summary counts only open tasks`() {
    val repo = InMemoryTaskRepository()
    repo.save(aTask(status = TaskStatus.TODO))
    repo.save(aTask(status = TaskStatus.IN_PROGRESS))
    repo.save(aTask(status = TaskStatus.DONE))

    val summary = ProjectSummary.from(repo.findAll())

    assertEquals(2, summary.openTaskCount)
}
```

---

## Integration Testing

Integration tests hit real I/O (file system, actual JSON). Separate them from unit tests with a tag.

```kotlin
@Tag("integration")
class JsonTaskRepositoryTest {

    @Test
    fun `persists and loads tasks across instances`(@TempDir tempDir: Path) {
        val dbFile = tempDir.resolve("tasks.json")
        val repo = JsonTaskRepository(dbFile)

        val task = Task(title = "Persisted task")
        repo.save(task)

        // Fresh instance from same file
        val repo2 = JsonTaskRepository(dbFile)
        val loaded = repo2.findById(task.id)

        assertEquals(task, loaded)
    }

    @Test
    fun `returns empty list when file does not exist`(@TempDir tempDir: Path) {
        val dbFile = tempDir.resolve("nonexistent.json")
        val repo = JsonTaskRepository(dbFile)

        assertEquals(emptyList(), repo.findAll())
    }
}
```

Run unit tests only: `./gradlew test --exclude-tags integration`  
Run integration tests: `./gradlew test --include-tags integration`

---

## Test Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| `verify { mock.method(any()) }` without checking arguments | Doesn't verify correctness | Match specific expected arguments |
| Mocking data classes / value objects | Fragile, unnecessary | Use real instances — data classes are cheap |
| Mocking everything | Tests pass but production breaks | Use in-memory fakes for repositories |
| `LocalDateTime.now()` in domain code | Untestable | Inject a `Clock` interface |
| `Thread.sleep` in tests | Slow, non-deterministic | Use FakeClock or deterministic coroutine dispatchers |
| Shared mutable state between tests | Tests pollute each other | Reconstruct repos in `@BeforeEach` |
| Testing `toString()` or `equals()` from data classes | Testing compiler-generated code | Only test YOUR logic |
| Deeply nested `@Nested` classes (>2 levels) | Hard to read | Flatten or split into separate test classes |
