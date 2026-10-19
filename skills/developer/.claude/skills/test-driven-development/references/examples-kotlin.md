# TDD Examples — Kotlin

Kotlin equivalents of the patterns in `SKILL.md`. Same cycle, idiomatic Kotlin.

## RED — Write a Failing Test

```kotlin
// RED: This test fails because Task doesn't exist yet
@Test
fun `creates task with title and default status`() {
    val task = Task(title = "Buy groceries")

    assertNotNull(task.id)
    assertEquals("Buy groceries", task.title)
    assertEquals(TaskStatus.TODO, task.status)
    assertNotNull(task.createdAt)
}
```

## GREEN — Minimal Implementation

```kotlin
// GREEN: Minimal implementation
enum class TaskStatus { TODO }

data class Task(
    val title: String,
    val id: String = UUID.randomUUID().toString(),
    val status: TaskStatus = TaskStatus.TODO,
    val createdAt: LocalDateTime = LocalDateTime.now()
)
```

## REFACTOR

With tests green, invoke the refactoring skills. Example: extract a factory if task creation accumulates ceremony:

```kotlin
// After refactor-for-clarity: intent-revealing factory
object TaskFactory {
    fun create(title: String): Task {
        require(title.isNotBlank()) { "Title is required" }
        return Task(title = title.trim())
    }
}
```

## The Prove-It Pattern (Bug Fix)

```kotlin
// Bug: "Completing a task doesn't update completedAt"

// Step 1: Reproduction test — must FAIL
@Test
fun `complete sets completedAt timestamp`() {
    val task = Task(title = "Test")
    val completed = task.complete()

    assertEquals(TaskStatus.DONE, completed.status)
    assertNotNull(completed.completedAt)  // Fails → bug confirmed
}

// Step 2: Fix
data class Task(
    val title: String,
    val status: TaskStatus = TaskStatus.TODO,
    val completedAt: LocalDateTime? = null,
    // ...
) {
    fun complete(): Task = copy(
        status = TaskStatus.DONE,
        completedAt = LocalDateTime.now()  // was missing
    )
}
```

## DAMP Over DRY

```kotlin
// DAMP: Each test tells its own story
@Test
fun `rejects tasks with empty titles`() {
    assertThrows<IllegalArgumentException> { TaskFactory.create("") }
}

@Test
fun `trims whitespace from titles`() {
    val task = TaskFactory.create("  Buy groceries  ")
    assertEquals("Buy groceries", task.title)
}
```

## Arrange-Act-Assert

```kotlin
@Test
fun `marks task overdue when deadline has passed`() {
    // Arrange
    val task = Task(title = "Test", deadline = LocalDate.of(2025, 1, 1))

    // Act
    val result = checkOverdue(task, currentDate = LocalDate.of(2025, 1, 2))

    // Assert
    assertTrue(result.isOverdue)
}
```

## Naming

```kotlin
// Good: Reads like a specification
class TaskCompleteTest {
    @Test fun `sets status to done and records timestamp`() { ... }
    @Test fun `throws NotFound for nonexistent task`() { ... }
    @Test fun `is idempotent when task is already done`() { ... }
}
```

## Prefer Real Implementations

```kotlin
// Fake repository — fast, no I/O, real behavior
class InMemoryTaskRepository : TaskRepository {
    private val store = mutableMapOf<String, Task>()

    override fun save(task: Task): Task = task.also { store[it.id] = it }
    override fun findById(id: String): Task? = store[id]
    override fun findAll(): List<Task> = store.values.toList()
}

// Use in tests — no mocking needed
@Test
fun `saves and retrieves task by id`() {
    val repo = InMemoryTaskRepository()
    val task = Task(title = "Test")

    repo.save(task)

    assertEquals(task, repo.findById(task.id))
}
```
