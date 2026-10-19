# Tech Lead instruction — sympy-11618: Point.distance pads the shorter point with zeros

**Product root:** <the issue's clone>/.worktrees/2026-10-10_sympy-11618 — every path below is relative to it.
**Scope:** `Point.distance` in `sympy/geometry/point.py` counts a coordinate the shorter point lacks as `0` (CP-9, CP-10); every same-length result and the `TypeError` for a non-sequence stay as they are (CP-11, CP-12); the tests go in `sympy/geometry/tests/test_point.py`, the only file the card's `Test command:` runs (CP-13, CP-14). The change stores nothing on a device, calls no third party and publishes no text. It brings in no import and no dependency: `S` is already imported in `point.py`.

---

## Project layout

```
sympy/
  geometry/
    point.py                 ← modified (Point.distance only)
    tests/
      test_point.py          ← modified (two new test functions)
```

No parts table — placement follows change_design.md §2. The product has no `docs/`. No file or directory is created.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):
- **Task split, guards first:** design §3 is omitted and §5 holds two test functions. The plan makes them two tasks. Task 1 is the guard function (CP-11, CP-12, and the zero-distance edge), Task 2 is the fix function with the production change. The guards already pass at `base_commit`, so they cannot be written test-first. Putting them in a task of their own, ahead of the fix, gives the developer a pinned baseline before `distance` is touched, and keeps Task 2's red clean: every assertion in Function 1 fails on the unchanged tree.
- **Already-green shape for Task 1:** each guard asserts behaviour that `Point.distance` already has. The plan routes the task by the already-green marker with a `Reason:` line. I read `distance` (lines 237–270) and confirmed the same-length, `Float`, iterator and `TypeError` paths hold today; the spec's Verified Claims ran the same calls. The behaviours are carried in full and none is dropped.
- **Dependencies: None on both tasks.** Task 2 uses nothing Task 1 makes. Their order is for the reasons above and the task numbers carry it.
- **Hint carried, tightened to the approach:** design §4's hint goes into Task 2 as a `# Hint:` block, with no code. It keeps the three constraints the architect wrote (read the argument once before measuring it, pad with `S.Zero`, never turn a plain sequence into a `Point`).
- **Behaviour locked, comparison of the `Float` results:** the design says to compare against a `Float` built the same way, not the 15-digit decimal in the spec. Both `Float` assertions (Task 1 and Task 2) carry that line, so a test cannot pass or fail on how the decimal prints.
- **Gate command:** the card's `Test command:` (`/home/kensai/issue-test.sh`) runs `sympy/geometry/tests/test_point.py` only, and the spec ran it at base (`6 passed`, exit 0, empty baseline). The gate below uses it unchanged.

### Task 1: Guards — what does not change (`sympy/geometry/tests/test_point.py`)

**Dependencies:** None

**What to build:** one new test function, `test_distance_unchanged_cases`, placed after the existing `test_Point2D`. It pins today's `distance` results for the cases CP-11 and CP-12 say stay as they are, plus the zero-distance edge of CP-9. It does not extend an existing test function.

#### Behaviours to verify (developer adds tests to `sympy/geometry/tests/test_point.py`)

- `test_distance_unchanged_cases` asserts all of the following, using the file's existing imports (add `Float` and `x`, `y` only if the file lacks them, from SymPy as the file already imports from it):
  - `Point(1,0).distance(Point(1,0,0)) == 0` — CP-9's zero-distance edge. It already returns `0`, because the dropped coordinate is `0`.
  - `Point(1,1).distance(Point(4,5)) == 5`.
  - `Point(x,y).distance(Point(0,0)) == sqrt(x**2 + y**2)`, symbolic.
  - `Point3D(1,1,1).distance(Point3D(0,0,0)) == sqrt(3)`.
  - `Point(1,2,3,4).distance(Point(0,0,0,0)) == sqrt(30)`.
  - `Point(2,0).distance((1.5,0))` is a `Float` that equals `Float(0.5)`, and does not equal `Rational(1, 2)`. A plain sequence of floats keeps a `Float` result.
  - `Point(2,0).distance(iter((1.5,0)))` is a `Float` that equals `Float(0.5)`. A one-shot iterator argument keeps working.
  - `raises(TypeError, lambda: Point(2,0).distance(5))`.
  - `raises(TypeError, lambda: Point(2,0).distance(Line((0,0),(1,1))))`.
- The existing assertion `Point2D(4, 2.5).distance((6, 3)) == sqrt(17)/2` (`test_point.py` line 236) already covers its CP-11 row. Add nothing for it.

#### Implement

Tests cannot go red.

Reason: `Point.distance` already returns each of these values at `base_commit`. The guards pin behaviour that exists, and the change must keep it. The fix lands in Task 2.

#### Verification gate

Run `/home/kensai/issue-test.sh`.

Pass criteria: exit 0, the new function is among the tests that ran and passed, and no test fails. Nothing in `sympy/geometry/point.py` has been touched yet.

### Task 2: Pad the shorter point in `Point.distance` (`sympy/geometry/point.py`, `sympy/geometry/tests/test_point.py`)

**Dependencies:** None

**What to build:** `Point.distance` treats every coordinate the shorter of the two coordinate lists lacks as zero before it sums the squared differences, for a `Point` argument and for a plain-sequence argument, whichever of the two is shorter and for any pair of lengths (CP-9, CP-10). The signature, the return type and the docstring stay as they are. `Point2D` and `Point3D` do not override `distance` and take the fix through inheritance. `taxicab_distance`, `midpoint` and `dot` are not touched (spec, Out of Scope). The tests are one new function, `test_distance_pads_shorter_point`, in `sympy/geometry/tests/test_point.py`, placed after Task 1's function.

#### Behaviours to verify (developer adds tests to `sympy/geometry/tests/test_point.py`)

Every assertion below fails on the unchanged tree and passes with the change (CP-13):

- `test_distance_pads_shorter_point` asserts all of the following:
  - `Point(2,0).distance(Point(1,0,2)) == sqrt(5)` — the issue's call.
  - `Point(1,0,2).distance(Point(2,0)) == sqrt(5)` — the other order.
  - `Point(0,0).distance(Point(1,1,1,1)) == 2` — lengths 2 and 4.
  - `Point(1,1,1,1).distance(Point(0,0)) == 2` — lengths 4 and 2.
  - `Point(x,y).distance(Point(0,0,z)) == sqrt(x**2 + y**2 + z**2)` — symbolic (add `z` to the file's symbols if it lacks it).
  - `Point(2,0).distance((1,0,2)) == sqrt(5)` and `Point(2,0).distance([1,0,2]) == sqrt(5)` — a longer tuple and a longer list.
  - `Point(1,0,2).distance((2,0)) == sqrt(5)` — a shorter sequence.
  - `Point(2,0).distance((1.5,0,2))` is a `Float` and equals `sqrt(Float(4.25))`. Compare against a `Float` built the same way, not against the 15-digit decimal in the spec.
  - `Point(2,0).distance(()) == 2` — the empty sequence pads to the origin. Today it returns `0`.

#### Implement

Infer from failing tests.

# Hint: Read the argument's coordinates once, before anything measures it. For a `Point` that is its `args`, and for anything else it is the argument materialized into a tuple. Reading first keeps two behaviours of today's code that a length check on the raw argument would break: a non-iterable (`5`, a `Line`) still raises `TypeError` at that read, and a one-shot iterator, which has no `len()`, still works. Pad the shorter of the two lists with SymPy's zero (`S.Zero`, already imported in `point.py`), so the padded list matches what a padded `Point`'s coordinates would be, and then run the existing sum of squared differences over the two equal-length lists. Do not turn a plain-sequence argument into a `Point`: construction rationalizes floats, which would turn `Point(2,0).distance((1.5,0))` into `1/2`, and it would give the integer `5` a meaning.

#### Verification gate

Run `/home/kensai/issue-test.sh`.

Pass criteria: exit 0 with no failing test; `test_distance_pads_shorter_point` and Task 1's `test_distance_unchanged_cases` both ran and passed; no existing test changed. On the unchanged tree `test_distance_pads_shorter_point` fails.
