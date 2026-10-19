# Change Design — Point.distance pads the shorter point with zeros

**Date:** 2026-10-10
**Category:** bug
**Behaviour:** changing
**Publishes text:** no

---

## 1. Change Summary

`Point.distance` in `sympy/geometry/point.py` pairs coordinates with `zip`, and `zip` stops at the
shorter of the two coordinate lists. When one point has fewer coordinates than the other, the extra
coordinates are dropped, and `Point(2,0).distance(Point(1,0,2))` returns `1` instead of `sqrt(5)`.
After the change, `distance` treats each coordinate the shorter list lacks as zero before it sums the
squared differences (CP-9, CP-10). Every same-length result stays exactly as it is, including a
`Float` result from a plain sequence of floats (CP-11). A non-sequence argument still raises
`TypeError` (CP-12). The change touches one method in one module, and adds tests to the one file the
card's `Test command:` runs. `Point2D` and `Point3D` do not override `distance`, so they take the fix
through inheritance with no change of their own.

**What crosses the outward boundary: nothing.** The change stores nothing on any device, collects
nothing and sends nothing to a third party. It is a local patch to a local clone. The card reads
`Manages: none`, so the patch is never pushed, and no other surface of the presence says anything
this change moves.

---

## 2. Blast Radius

The product has no `docs/`, so it has no `nfdr.md` § 1.2 module set and no `SDD.md` § 3 parts
table. Step 2 therefore has no placement to make, and the module set below is drawn from the spec
and from reading the callers of `distance` under `sympy/`. The new logic is the padding of the
shorter coordinate list. It stays inside `Point.distance`, the method the spec's rules are about.

| Module | Status | What changes |
|---|---|---|
| `sympy/geometry/point.py` | Modified | `Point.distance`: the argument's coordinates are read once, the shorter of the two coordinate lists is padded with zeros to the longer one's length, and the existing sum of squared differences runs over the padded pair. The signature, the return type and the docstring stay as they are. `taxicab_distance`, `midpoint` and `dot` are not touched (spec, Out of Scope). |
| `sympy/geometry/tests/test_point.py` | Modified | New test functions for CP-9 to CP-12 (§5). |
| `sympy/geometry/line.py`, `line3d.py`, `polygon.py`, `ellipse.py`, `plane.py` | Unchanged | They call `Point.distance` / `Point3D.distance` on points of one dimension: a segment's endpoints, a polygon's vertices, a center and a vertex. CP-11 keeps every same-length result exactly as it is, so none of their results moves. Their own `distance` methods, which take a `Line`, a `Segment` and so on, are out of scope by the spec and are not touched. |

**Transitive radius.** The public interface of `Point.distance` does not change: it keeps its name and
signature, the argument types it accepts and the exception it raises. Only the value for arguments of
different length changes. No importing module needs a change.

---

## 3. Sub-jobs

Omitted. One module is affected (`sympy/geometry/point.py`), and the change inside it is one method
with no internal seams, so there is no ordering edge to cut on. The tests ride with it as a single
delta.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `point.py` — `Point.distance` pads the shorter coordinate list | Read the argument's coordinates **once, before measuring anything**: a `Point`'s `args`, and otherwise the argument materialized into a tuple. Materializing first keeps two of today's behaviours that a length check would break. A non-iterable (`5`, a `Line`) still raises `TypeError` at that read, and a one-shot iterator argument, which has no `len()`, still works. Pad the shorter list with SymPy's zero, `S.Zero`, which is already imported, so that the padded list matches what a padded `Point`'s coordinates would be. Then run the existing sum of squared differences over the two equal-length lists. Do **not** turn a plain-sequence argument into a `Point`. `Point` construction rationalizes floats, which would turn `Point(2,0).distance((1.5,0))` into `1/2` (breaking CP-11), and it would give the integer `5` a meaning (breaking CP-12). |

---

## 5. Test Additions

All the rows go in `sympy/geometry/tests/test_point.py`, the only file the card's `Test command:`
runs (spec Gap 5). They form two new test functions. They do not extend the existing ones, so that
the tests that prove the fix fail cleanly on the unchanged tree and do not take the existing
assertions down with them.

**Function 1 — the fix (CP-9, CP-10). Every assertion fails on the unchanged tree and passes with
the change (CP-13).**

| Rule | Test file | What to add |
|---|---|---|
| CP-9 | `tests/test_point.py` | `Point(2,0).distance(Point(1,0,2)) == sqrt(5)`, the issue's call |
| CP-9 | `tests/test_point.py` | `Point(1,0,2).distance(Point(2,0)) == sqrt(5)`, the other order |
| CP-9 | `tests/test_point.py` | `Point(0,0).distance(Point(1,1,1,1)) == 2`, lengths 2 and 4 |
| CP-9 | `tests/test_point.py` | `Point(1,1,1,1).distance(Point(0,0)) == 2`, lengths 4 and 2 |
| CP-9 | `tests/test_point.py` | `Point(x,y).distance(Point(0,0,z)) == sqrt(x**2 + y**2 + z**2)`, symbolic |
| CP-10 | `tests/test_point.py` | `Point(2,0).distance((1,0,2)) == sqrt(5)` and `Point(2,0).distance([1,0,2]) == sqrt(5)`, a longer tuple and list |
| CP-10 | `tests/test_point.py` | `Point(1,0,2).distance((2,0)) == sqrt(5)`, a shorter sequence |
| CP-10 | `tests/test_point.py` | `Point(2,0).distance((1.5,0,2))` is a `Float` and equals the `Float` square root of `4.25`. Compare against a `Float` built the same way, not against the 15-digit decimal printed in the spec |
| CP-10 (rule-implied edge) | `tests/test_point.py` | `Point(2,0).distance(()) == 2`. The empty sequence pads to the origin. Today it returns `0` |

**Function 2 — what does not change (CP-11, CP-12). These assertions pin today's behaviour. They pass
on both trees, which is what a guard should do.**

| Rule | Test file | What to add |
|---|---|---|
| CP-9 (zero-distance edge) | `tests/test_point.py` | `Point(1,0).distance(Point(1,0,0)) == 0`. It passes on the unchanged tree too (the dropped coordinate is `0`), so it sits here and not in Function 1 |
| CP-11 | `tests/test_point.py` | `Point(1,1).distance(Point(4,5)) == 5`, `Point(x,y).distance(Point(0,0)) == sqrt(x**2 + y**2)`, `Point3D(1,1,1).distance(Point3D(0,0,0)) == sqrt(3)`, `Point(1,2,3,4).distance(Point(0,0,0,0)) == sqrt(30)` |
| CP-11 | `tests/test_point.py` | `Point(2,0).distance((1.5,0))` is a `Float` equal to `Float(0.5)`, not `Rational(1, 2)` |
| CP-11 (rule-implied edge) | `tests/test_point.py` | `Point(2,0).distance(iter((1.5,0)))` is a `Float` equal to `Float(0.5)`: a one-shot iterator argument keeps working |
| CP-11 | — | `Point2D(4, 2.5).distance((6, 3)) == sqrt(17)/2` is already asserted at `test_point.py` line 236. Covered by that line, so no new row |
| CP-12 | `tests/test_point.py` | `raises(TypeError, lambda: Point(2,0).distance(5))` and `raises(TypeError, lambda: Point(2,0).distance(Line((0,0),(1,1))))` |

**CP-13 and CP-14** are not test rows. They are run outcomes. Function 1 fails on the unchanged tree
and passes with the change. The card's `Test command:` exits 0 with no failing test.

**Assertions this change retires: none.** Every existing `distance` assertion in the file compares
points of the same length (spec, Verified Claims), and CP-11 keeps those results exactly as they are.

---

## Records this change makes false

None. The product has no `docs/`, so there is no `adr/`, `nfdr.md`, `fdr.md` or `SDD.md` to read and
none of them can go false. The `distance` docstring says nothing about points of different length
(spec, Verified Claims), so nothing in it goes false either.

---

## Architect Review Notes

- **(b) The argument is read once, before anything measures it.** The spec says a plain sequence is
  accepted and that a non-sequence raises `TypeError`. It does not say how the length is found.
  Calling `len()` on the raw argument would break a one-shot iterator argument, which works today.
  That argument has no `len()`, so the call raises where today it returns a value. That is a
  same-length behaviour change, and CP-11 forbids it. Materializing first keeps the iterator working,
  and it keeps `TypeError` for `5` and a `Line`, because they fail at the read (probed on the
  unchanged tree: `tuple(5)` and `tuple(Line(...))` both raise `TypeError`). The iterator assertion in
  §5 pins this.
- **(b) The padding is SymPy's zero, so the result is the padded result by construction.** CP-9 and
  CP-10 define the expected value as "what today's `distance` returns for the padded pair". A padded
  `Point`'s extra coordinates are `S.Zero`, so the design pads with `S.Zero` and matches that
  definition exactly. A Python `0` would match it only by coincidence, through arithmetic that happens
  to agree.
- **(b) The empty-sequence edge is derived from CP-10 and was not stated.** CP-10's rule pads a
  shorter sequence. The empty tuple is its shortest case, and it pads to the origin, so
  `Point(2,0).distance(())` becomes `2` where today it is `0`. That follows from the rule as written.
  It is pinned in Function 1 so the rule's boundary is proved and not left implicit.
- **(b) CP-13's "they fail on the unchanged tree" applies to the fix tests only.** The guard tests for
  CP-11 and CP-12 pin today's behaviour, so they cannot fail on the unchanged tree. The design keeps
  the fix tests and the guard tests in two separate functions. Function 1 then fails as a unit at
  `base_commit` and passes with the change, and Function 2 passes throughout. CP-13's list of what
  the failing tests cover sits wholly in Function 1. The `Point(1,0)` / `Point(1,0,0)` example is in
  Function 2 because it already returns `0` today.
- **(b) Where the tests live (spec Gap 5, left to this stage).** They go in
  `sympy/geometry/tests/test_point.py`, the only file the card's `Test command:` runs, so the change's
  gate sees them.
- **(b) No docstring change, so `Publishes text: no`.** The request asks for no documentation, and the
  spec's Out of Scope keeps the docstring as it is. Adding a docstring example would put new words in
  front of a reader and would need the content step. Nothing asked for it.
- **(e) No parts table to place by.** The product has no `docs/SDD.md`, so no part's `Owns` column can
  be read. The padding stays inside `Point.distance` because every rule in the spec is a rule about
  that method, and a helper elsewhere would invent a seam that nothing else uses.
