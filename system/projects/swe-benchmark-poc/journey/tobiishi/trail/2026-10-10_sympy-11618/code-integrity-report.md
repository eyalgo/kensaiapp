# Code integrity report — 2026-10-10_sympy-11618

Integrity: pass

**Change:** `Point.distance` pads the shorter point with zeros (`sympy__sympy-11618`).
**Reviewed by:** Senior Engineer, `development-code-integrity`, workflow mode, 2026-10-10.
**Outcome:** a clean pass. The code does what its intent says. One assertion was missing from the
suite and has been added; it passed on the code as it stands. No code was changed.

## Deferrals

**None.** The newest closing marker, `e475037` (`developer: 2026-10-10_sympy-11618 — implementation
complete`), has no `Deferred:` line and no `Failing:` line. There is nothing to check.

## What was reviewed

The product is in its own repository, so the code and this report sit in different places:

- code worktree: `<the issue's clone>/.worktrees/2026-10-10_sympy-11618`
- pipeline worktree: the instance worktree for the key, which holds this report

The code reviewed is `360290c4c..3301a41fc`. These are the developer's three commits:

- `d09e203de`: Task 1 guards
- `6ee8fe74e`: Task 2 red
- `3301a41fc`: Task 2 green

The diff touches two files:

- `sympy/geometry/point.py`: the body of `Point.distance`, lines 269–278
- `sympy/geometry/tests/test_point.py`: imports at lines 3–4, `test_distance_unchanged_cases`, and
  `test_distance_pads_shorter_point`

## The intent it was checked against

- `tl_instruction.md`: Task 1 (guards) and Task 2 (padding), with their *Behaviours to verify*.
- `change_spec.md`: CP-9 to CP-14, the Examples table, Locked Answers, and Out of Scope.
- `change_design.md`: §2 (placement), §4 (the hint) and §5 (the test rows).
- `change_request.md` § *What must not be done*.
- `docs/fdr.md`: absent. The product has no `docs/`, and the card reads `Definition: none`. This is
  optional context and its absence is not a gap.

## How it was run

The card's `Test command:` is `/home/kensai/issue-test.sh`. It was run from the code worktree root.

- **On the branch:** exit 0, `8 passed`, both before and after this review's commit.
- **Red proof:** a disposable `git archive` of `360290c4c` was made, the branch's `test_point.py` was
  copied over it, and the suite ran there with the issue's interpreter, outside every checkout.
  - Result: `1 failed, 7 passed`.
  - The failure is `test_distance_pads_shorter_point`, on the issue's own call: `1 == sqrt(5)`.
  - `test_distance_unchanged_cases` passes at base, which is what a guard should do (design §5).
  - CP-13 holds.
- **Compile gate:** `compileall -q` on `test_point.py` exits 0.
- **Line length:** no added line is over 100 columns.

## Tests added or fixed

**Added: one assertion** in `test_distance_pads_shorter_point`, in commit `3856ebaa0` in the code
worktree:

```python
padded_float = Point(1, 0, 2).distance((2.5, 0))
assert isinstance(padded_float, Float)
assert padded_float == sqrt(Float(6.25))
```

**Why it was added.** CP-10 says that CP-9 holds for a plain sequence "in either order", and that "a
`Float` in the sequence still gives a `Float` result". The suite proved the `Float` result in only one
order: `(1.5, 0, 2)`, where the sequence is the longer side and `self` is padded. The case where the
**sequence** is the shorter side had no `Float` check. In that case the sequence itself is the side
that gets padded.

That gap mattered. A fix that padded a short sequence by building a `Point` from it would rationalize
the float, which design §4 forbids. The suite as handed over stayed green against that fix, because
`Point(1,0,2).distance((2,0))` uses integers.

**Checks on the new assertion:**

- At `base_commit` it fails: the call returns `1.50000000000000`.
- Against that mutant it fails on the `isinstance` line.
- On the branch it passes and returns `2.50000000000000`, a `Float`.
- The expected value is the one CP-10 defines: `Point(1,0,2).distance((2.5,0,0))` at base, which was
  probed as `Float` 2.5. It is compared against a `Float` built the same way, as design §5 directs.

**Fixed: none.** Every other assertion matches its row in `tl_instruction.md` and design §5. The one
row not delivered is the developer's dropped `!= Rational(1, 2)` (see *Calls made*, 1).

**Checked and left alone:**

- Every other CP-9 to CP-12 row is in the suite, and the CP-11 row at `test_point.py:236` was already
  there.
- Either point can be the shorter one: tested for 2 and 3 points, 3 and 2, 2 and 4, and 4 and 2.
- The padding value is checked by `Point(1,0).distance(Point(1,0,0)) == 0`, so padding with anything
  other than zero goes red.
- `Point2D` and `Point3D` do not override `distance`. This was probed with `'distance' in
  Point2D.__dict__` and the same for `Point3D`, and both are False. The `Point(2,0)` and
  `Point(1,0,2)` pairs build exactly those two classes, so the tests cover the inheritance path.

## The finding

**No bug. Nothing misplaced.** Here is how the code reads against the intent:

- `Point.distance` reads the argument once: `p.args` for a `Point`, and `tuple(p)` for anything else.
- It pads the shorter side with `S.Zero`, then runs the original sum of squared differences.
- **Same length:** the `missing` count is 0, and the pairs are the same as `zip(self.args, p)` gave
  before. CP-11 holds by construction.
- **Not a sequence:** `5` or a `Line` raises `TypeError` at `tuple(p)`, so CP-12 holds.
- **Plain sequence:** it is never turned into a `Point`, so a `Float` stays a `Float` in both orders.

The one gap was in the suite, not the code (*Tests added*).

**Domain overlay (`system/loaders/senior_engineer.md`):**

- The change stores nothing on a device.
- It loads no embed, form or third-party script.
- It publishes no text (`Publishes text: no`).
- It has no LinkedIn-facing test.

So the instance doctrine's §§ 3, 4 and 6 have nothing here to bear on.

## Calls made

1. **The dropped Task 1 assertion `Point(2,0).distance((1.5,0)) != Rational(1, 2)`.**
   - **The question:** should the suite assert this inequality, as `tl_instruction.md` Task 1 and
     design §5 ("not `Rational(1, 2)`") state it?
   - **The readings weighed:**
     - (a) Assert the inequality as written.
     - (b) Assert the intent behind it, "a `Float`, not `1/2`" (CP-11), through the result's type.
   - **What decided it:** `Float(0.5) == Rational(1, 2)` is `True` in this SymPy. This was probed at
     `base_commit`. So (a) fails on correct, unchanged code and cannot be the intent.
   - **Taken:** (b). The developer made this call and the reviewer confirms it. The isinstance check
     plus `== Float(0.5)` already tell a `Float` from a rationalized result.
   - **Whose document:** the Tech Lead's (`tl_instruction.md` Task 1), from the Architect's
     `change_design.md` §5.
   - **If they rule the other way:** an inequality can't be written with SymPy `==` here. Any other
     form, such as `not result.is_Rational`, says the same thing as the type check, so the suite
     would not change in substance.

2. **An infinite iterator as the argument.**
   - **The question:** `tuple(p)` now reads the whole argument. Today's `zip` stopped at `self`'s
     length, so `Point(2,0).distance(itertools.count())` returned a value before. Now it never
     returns.
   - **The readings weighed:**
     - (a) CP-11's "returns exactly what it returns today" covers every iterable.
     - (b) The rules are about a point's coordinates. The spec's terms define the argument as "a
       `Point` or a plain sequence of coordinates", and design §4 names a one-shot **finite**
       iterator as the edge to keep.
   - **Taken:** (b). An unbounded iterable is not a point's coordinates. The design's own hint, read
     once by materializing, is what produces this, and the design chose it on purpose. No test was
     added and no code was changed.
   - **Whose document:** the Product Owner's (`change_spec.md` CP-11 and its Terms).
   - **If they rule the other way:** `distance` would need to read the argument lazily against
     `self`'s length. The length of a longer iterator would then be unknowable, so CP-10 could not
     hold for iterators. That is a redesign and would go back to the Architect.

3. **Python packet rules that apply to a whole module.**
   - **The question:** `conventions.md` asks for `from __future__ import annotations` as the first
     statement and a `__version__` in every non-test module. Should they be added to SymPy's
     `point.py` and `test_point.py`?
   - **The readings weighed:**
     - (a) The packet outranks the file's style, so add them.
     - (b) The request's "leave the rest of the product's behaviour as it is" and the spec's Out of
       Scope keep the change to the one method and its tests. A module-wide marker is outside that
       change.
   - **Taken:** (b). This is the smaller, reversible answer, and it keeps the request meaning what it
     says. The change wrote no annotation and created no module. Every rule that bears on the lines it
     did write is met (below).
   - **Whose document:** the owner's. This is the request's scope set against the shared packet.
   - **If they rule the other way:** both files gain module-level lines that the issue did not ask for.

## Placement

**No parts table.** The product has no `docs/`, so there is no `docs/SDD.md` § 3 and Step 0 has
nothing to place against. For the record, the only new logic is the padding of the shorter coordinate
list. It sits in `Point.distance` (`sympy/geometry/point.py`), where `change_design.md` §2 keeps it.
Nothing was moved and there is no `… — placement` commit.

## Language resolution

- **Language:** Python. It is declared in `project.md` (`Languages: Python`) and was answered at step
  1 of the chain.
- **Packet opened:** `core/doctrine/engineering/languages/python/README.md`. The concerns read were:
  - Conventions: `conventions.md`
  - Quality gates: `quality_gates.md`
  - Testing: `core/doctrine/engineering/testing_python.md`, routed outside the packet folder
  - Toolchain, Layout and Errors and logging were taken as the developer's marker records them. This
    review changed no import, file or raise.
- **Followed:**
  - Lines within 100 columns.
  - Test functions are not annotated.
  - snake_case locals (`padded_float`).
  - A `#` block above the construct that says why. The new assertion's comment names the rejected
    alternative, building a `Point`.
  - Both gates: compile exits 0, and the suite exits 0 and ran.
- **Diverged:**
  - The test location and run command differ from `testing_python.md` § Layers 1–5. The tests sit in
    SymPy's `sympy/geometry/tests/test_point.py` and run under the card's command. That file is the
    only one the gate runs (spec Gap 5, design §5).
  - The interpreter is `/home/kensai/issue-venv/bin/python` (3.9.25), not a bare `python3`. The
    card's command fixes it.
  - The module-wide markers were not added (*Calls made*, 3).
