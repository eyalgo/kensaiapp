# Change Spec — Point.distance ignores the coordinates one point has and the other lacks

**Date:** 2026-10-10
**Category:** bug
**Behaviour:** changing
**Request:** "Fix the issue below in the product, the repository that the project card's
`Product path:` names (`sympy/sympy`). The repository stands at the commit before the issue was
fixed. Make the change the issue asks for, with tests of your own that show it, and leave the rest of
the product's behaviour as it is." The issue is `sympy__sympy-11618`, quoted in full in this folder's
`change_request.md` § *The issue*. That file's § *What must not be done* sets the change's constraints.

---

## Change Summary

`Point.distance` returns the wrong value when the two points have different numbers of coordinates.
It uses only as many coordinates as the shorter point has, so `Point(2,0).distance(Point(1,0,2))`
returns `1` instead of `sqrt(5)`. After this change, a coordinate the shorter point lacks counts as
`0`, so that call returns `sqrt(5)`. Every distance between two points with the same number of
coordinates stays as it is today.

**Terms used below.** A point's **length** is its number of coordinates (`len(p)`, which is also
`p.ambient_dimension`). The **argument** is `p` in `self.distance(p)`. It is either a `Point` or a
plain sequence of coordinates, such as a tuple or list; `distance` accepts both today. To **pad** a
point or sequence to length `n` is to append `0` as many times as it takes to reach `n` coordinates.
"Equals" means SymPy `==` on the returned expression.

---

## Rules

### Point.distance — points of different length

- **CP-9:** When `self` and a `Point` argument have different lengths, `self.distance(p)` equals what
  `distance` returns today once the shorter of the two is padded to the longer one's length. This
  holds whichever of the two is the shorter, and for any pair of lengths. For example,
  `Point(2,0).distance(Point(1,0,2))` equals `Point(2,0,0).distance(Point(1,0,2))`, which is
  `sqrt(5)`.
- **CP-10:** CP-9 holds the same way when the argument is a plain sequence rather than a `Point`, in
  either order: `Point(2,0).distance((1,0,2))` and `Point(1,0,2).distance((2,0))` each equal
  `sqrt(5)`. The result is the one today's `distance` gives for the padded sequence, so a `Float` in
  the sequence still gives a `Float` result: `Point(2,0).distance((1.5,0,2))` is
  `2.06155281280883`.

### Point.distance — what does not change

- **CP-11:** When `self` and the argument have the same length, `self.distance(p)` returns exactly
  what it returns today, both for a `Point` and for a plain-sequence argument. For example,
  `Point(1,1).distance(Point(4,5))` is `5`, `Point(2,0).distance((1.5,0))` is `0.500000000000000`
  (a `Float`, not `1/2`), and `Point(1,2,3,4).distance(Point(0,0,0,0))` is `sqrt(30)`.
- **CP-12:** An argument that is neither a `Point` nor a sequence of coordinates keeps today's
  outcome, which is `TypeError`. Examples are the integer `5` and a `Line`.

### Proof

- **CP-13:** The change includes its own tests, and the card's `Test command:` runs them. They fail on
  the unchanged tree and pass with the change. Together they cover at least:
  - the issue's call `Point(2,0).distance(Point(1,0,2))`, which equals `sqrt(5)`;
  - the same pair in the other order;
  - a plain-sequence argument of a different length (CP-10);
  - a pair whose lengths differ by more than one, such as 2 and 4.
- **CP-14:** The card's `Test command:` exits 0, and no test in its run fails. At `base_commit` no
  test fails (`change_request.md` § *What must not be done*), and the card's baseline list is empty.

---

## Examples

"Today" is the value at `base_commit`, run on 2026-10-10 (see Verified Claims).

| Rule | Scenario | Today | Expected behavior |
|---|---|---|---|
| CP-9 | `Point(2,0).distance(Point(1,0,2))` (the issue's call) | `1` | `sqrt(5)` |
| CP-9 | `Point(1,0,2).distance(Point(2,0))` | `1` | `sqrt(5)` |
| CP-9 | `Point(0,0).distance(Point(1,1,1,1))` | `sqrt(2)` | `2` |
| CP-9 | `Point(1,1,1,1).distance(Point(0,0))` | `sqrt(2)` | `2` |
| CP-9 | `Point(1,0).distance(Point(1,0,0))` | `0` | `0` |
| CP-9 | `Point(x,y).distance(Point(0,0,z))` (symbols) | `sqrt(x**2 + y**2)` | `sqrt(x**2 + y**2 + z**2)` |
| CP-10 | `Point(2,0).distance((1,0,2))` | `1` | `sqrt(5)` |
| CP-10 | `Point(2,0).distance([1,0,2])` | `1` | `sqrt(5)` |
| CP-10 | `Point(1,0,2).distance((2,0))` | `1` | `sqrt(5)` |
| CP-10 | `Point(2,0).distance((1.5,0,2))` | `0.500000000000000` | `2.06155281280883` (a `Float`) |
| CP-11 | `Point(1,1).distance(Point(4,5))` | `5` | `5` |
| CP-11 | `Point(x,y).distance(Point(0,0))` | `sqrt(x**2 + y**2)` | `sqrt(x**2 + y**2)` |
| CP-11 | `Point3D(1,1,1).distance(Point3D(0,0,0))` | `sqrt(3)` | `sqrt(3)` |
| CP-11 | `Point(1,2,3,4).distance(Point(0,0,0,0))` | `sqrt(30)` | `sqrt(30)` |
| CP-11 | `Point(2,0).distance((1.5,0))` | `0.500000000000000` | `0.500000000000000` |
| CP-11 | `Point2D(4, 2.5).distance((6, 3))` (`sympy/geometry/tests/test_point.py` line 236) | `sqrt(17)/2` | `sqrt(17)/2` |
| CP-12 | `Point(2,0).distance(5)` | `TypeError` | `TypeError` |
| CP-12 | `Point(2,0).distance(Line((0,0),(1,1)))` | `TypeError` | `TypeError` |
| CP-13 | the change's own tests, run on the unchanged tree | — | they fail |
| CP-13 | the change's own tests, run with the change | — | they pass |
| CP-14 | the card's `Test command:` run with the change | exit 0, `6 passed` | exit 0, no test fails |

---

## Verified Claims

Every claim below was checked on 2026-10-10 in the product's change worktree for this key, which is
opened from the repository the card's `Product path:` names, at `base_commit` `360290c4c`, with no
change applied. The runs used the interpreter the card's command uses (`/home/kensai/issue-venv/bin/python`,
Python 3.9.25) with `PYTHONDONTWRITEBYTECODE=1`, and `git status --short` was still empty afterwards.
Nothing outside the repository was consulted: no upstream history, no pull request, and no copy of
the benchmark.

| Claim | Verified by | What came back |
|---|---|---|
| Every *Today* value in the Examples | ran each row's call | each returned the value in its *Today* column. `5` and a `Line` raised `TypeError: '<type>' object is not iterable` |
| Today's same-length `distance` gives the CP-9/CP-10 expected values for the padded pairs | ran `Point(2,0,0).distance(Point(1,0,2))`, `Point(1,0,2).distance(Point(2,0,0))`, `Point(2,0,0).distance((1,0,2))`, `Point(1,0,2).distance((2,0,0))`, `Point(0,0,0,0).distance(Point(1,1,1,1))`, `Point(1,0,0).distance(Point(1,0,0))`, `Point(x,y,0).distance(Point(0,0,z))`, `Point(2,0,0).distance((1.5,0,2))` | `sqrt(5)` ×4, `2`, `0`, `sqrt(x**2 + y**2 + z**2)`, `2.06155281280883` |
| The defect is present at `sympy/geometry/point.py` lines 269–270 | read `Point.distance` (lines 237–270) | it sums over `zip(self.args, p.args if isinstance(p, Point) else p)`, and `zip` stops at the shorter of the two |
| The rules can be met together | a scratch probe built outside the tree replaced `Point.distance` in memory, padding the shorter coordinate list with `0` before calling the original method. It ran on the unchanged tree. It shows that the rules can all be met; it is not a design | every CP-9 and CP-10 row gave its expected value, five same-length calls gave a `repr` identical to the original's, and `5` and a `Line` still raised `TypeError` |
| `distance` accepts a plain sequence today, and the suite already relies on that | read `sympy/geometry/tests/test_point.py` lines 230–236 | `p2.distance(p3)` with `p3 = (6, 3)` is asserted to equal `sqrt(17)/2` |
| Every `distance` assertion in the suite compares points of the same length | read every `distance` line of `sympy/geometry/tests/test_point.py` (41–43, 141–143, 235–236) | all same-length, so CP-11 keeps them as they are |
| The card's `Test command:` runs only `sympy/geometry/tests/test_point.py` | read `/home/kensai/issue-suite.sh` | `python -m pytest -rfE -p no:cacheprovider sympy/geometry/tests/test_point.py` |
| The card's `Test command:` passes at base with no failures | ran `/home/kensai/issue-test.sh` from the product worktree root | `6 passed, 103 warnings`, exit 0. `/home/kensai/issue-baseline.txt` is empty (0 bytes) |
| The `distance` docstring says nothing about points of different length | read lines 238–267 | its examples are two 2-D pairs, and nothing in it mentions dimension or length |

---

## Out of Scope

- **Other `Point` methods that pair up coordinates the same way.** `taxicab_distance`, `midpoint` and
  `dot` also use only as many coordinates as the shorter point has. Today
  `Point(2,0).taxicab_distance(Point(1,0,2))` is `1`, `Point(2,0).midpoint(Point(1,0,2))` is
  `Point2D(3/2, 0)`, and `Point(2,0).dot(Point(1,0,2))` is `2`. The issue names only `distance`, and
  the request says to leave the rest as it is, so these keep today's behaviour. Whether they get a
  change of their own is the PM's call.
- **Point arithmetic and construction.** `Point(2,0) + Point(1,0,2)` raises `ValueError` today and
  still does. Nothing changes in how points are built or how floats in them are converted.
- **Distances between a point and other entities** (`Line`, `Segment`, `Circle`, …), and
  `Segment.length`. These are not touched, and CP-12 keeps `Point.distance`'s `TypeError` for a
  non-sequence argument.
- **Documentation.** The request asks for none. The `distance` docstring does not state the fact this
  change moves, as checked above. The geometry module's `.rst` pages were searched for "dimension"
  and say nothing about distance between points of different length. No other surface was checked.
- **Anything outside the local clone.** The patch is not pushed (`project.md`, `Manages: none`), and
  nothing is published. As the request asks, the change produces no record, grade or benchmark file.

---

## Locked Answers (the divergence record — self-review 2026-10-10)

- **Gap 1: a missing coordinate counts as `0`, and the call does not raise (CP-9).** A mismatch in
  length could be handled either way. The issue settles it: it gives `sqrt(5)` as the right answer
  for its own call, and `sqrt(5)` is the padded distance. Raising an error would give the issue's
  call no value at all.
- **Gap 2: both orders, any pair of lengths, and plain-sequence arguments (CP-9, CP-10).** The issue
  shows one call: a 2-D `self` and a 3-D `Point` argument. The spec states the rule for any pair of
  lengths, so the rule is not limited to the 2-D and 3-D cases the issue happens to show. Distance is
  symmetric, so the reversed call must give the same value. `distance` already accepts a plain
  sequence, and the suite relies on that (Verified Claims). A fix that covers `Point` arguments only
  would leave `Point(2,0).distance((1,0,2))` returning the issue's wrong `1`.
- **Gap 3: same-length results stay exactly as they are, including `Float` results (CP-10, CP-11).**
  The request says to leave the rest of the product's behaviour as it is. Today a plain sequence of
  floats gives a `Float` distance, while the same coordinates passed as a `Point` give a rational. CP-11
  keeps that difference, and CP-10 extends it to the padded case. Turning the argument into a `Point`
  first would change `Point(2,0).distance((1.5,0))` from `0.500000000000000` to `1/2`, a change the
  issue does not ask for.
- **Gap 4: a non-sequence argument still raises `TypeError` (CP-12).** The issue says nothing about
  it. The conservative pick is no change. It is stated as a rule because a fix that wraps the argument
  in `Point` would give `5` a meaning as a one-coordinate point and return a number. That would be a
  new behaviour, and nothing asked for it.
- **Gap 5: the change's tests are ones the card's `Test command:` runs (CP-13).** The request asks for
  "tests of your own" and does not say where they run. The card's command runs
  `sympy/geometry/tests/test_point.py` only, so a test the command does not run shows nothing at the
  change's gate. Where the tests go is development-design's decision.
- **Gap 6: the other methods that use only the shorter point's coordinates are left alone (Out of
  Scope).** `taxicab_distance`, `midpoint` and `dot` have the same blind spot. The unit of acceptance
  is the operation the issue reports, `distance`, and the request says to leave the rest as it is.
  They are named under Out of Scope so the PM can carry them.
