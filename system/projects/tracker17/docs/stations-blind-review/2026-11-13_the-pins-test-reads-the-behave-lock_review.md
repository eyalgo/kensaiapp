# Blind review: the route of 2026-11-13_the-pins-test-reads-the-behave-lock

Read at `e37272532b8d01629847135ac08c7cc7e6398966`, by a fresh run that did not cut the route. Line
numbers (L…) refer to the seed unless another file is named. S1 = `pins-over-behave` (L15).

## 0. Coverage map

**Rulings.** None recorded. The seed has no rulings heading, and `## Source` (L11) quotes only the
NFDR's own words, "QC-39 starts unmet in its test". That records where the idea came from. It is not
an owner's dated call.

**`## What it is`, sentence by sentence:**

- L5, "Serves the Way `product-downstream` … Moves the Agari toward **Works** and **Simple to set
  up** (a lock that cannot drift from its manifest)". This is purpose, not work. Its Works half sits
  on S1's "the suite stays green", and its drift half on S1's "on a declared dependency its lock does
  not fix at that version".
- L7, "`tests/architecture/test_pins.py:L18` reads only the root manifest and `uv.lock`". This states
  the current state, so it is not mapped. It holds: `test_pins.py:L17-L18` reads only
  `PRODUCT_ROOT / "pyproject.toml"`, `test_pins.py:L46` reads only `PRODUCT_ROOT / "uv.lock"`, and
  `grep -n -i behave tests/architecture/*.py` printed nothing (exit 1).
- L7, "both manifests pin `playwright==1.65.1`, and `uv lock --check --project .behave` resolves
  clean". This is current state, so it is not mapped. It holds: `pyproject.toml:L17` and
  `.behave/pyproject.toml:L8` both read `playwright==1.65.1`, and in a disposable clone at the review
  commit `uv lock --check --offline --project .behave` exited 0.
- L7, "the pins test reads the second manifest … the same way". S1 carries it: "`test_pins.py`
  fails on a `.behave/` dependency not pinned with `==`". What "the same way" covers is § 6.2.
- L7, "… and lock the same way". S1 carries it only in part: "and on a declared dependency its lock
  does not fix at that version". The clause has no `.behave/` qualifier (§ 3.1).
- L7, "fails when the folder holds no manifest". S1 carries it: "on a `.behave/` holding no
  manifest".
- L7, "… or no lock". S1 carries it: "or no `uv.lock`".
- L7, "reads nothing when the folder is absent". S1 carries it: "reads nothing when `.behave/` is
  absent".
- L7, "QC-40's lock clause rides on it". **Unmapped** (§ 1.1, § 6.1).

**`## Out` (L25)**, "`uv lock --check --project .behave` is a `development-design` review bar … this
seed does not move it into the suite". No bar names `uv lock --check`, so the route obeys the fence.

## 1. Not carried

1. L7, "QC-40's lock clause rides on it". No word in S1's bar (L15) names QC-40, an advisory or a
   browser build. Whether the sentence asks for any work is § 6.1.

## 2. Contradicted or added

None found. S1 contradicts no sentence of L7, and it obeys the Out fence at L25. The bar adds two
terms that L7 does not contain, "a mutation moving one pin fails it" and "the suite stays green".
Both say how the bar is checked and widen no scope, so neither is raised here.

## 3. Not checkable

1. L15, "and on a declared dependency its lock does not fix at that version". The two clauses before
   it both say `.behave/`. This one does not, though L7 is about "the second manifest and lock".
   Read over the root, the clause already holds today. `test_pins.py:L44-L57`
   (`test_uv_lock_fixes_every_declared_dependency_at_its_declared_version`) fails today on a root
   dependency that `uv.lock` does not fix at its declared version, ending in
   `assert [pair for pair in wanted if pair not in locked] == []` (L57). Only the `.behave/` reading
   fails before the work and passes after it.
2. L15, "a mutation moving one pin fails it". The clause does not say which manifest the pin is in. A
   pin moved in the root `pyproject.toml` already fails the test today (`test_pins.py:L57`), so on that
   reading the mutation is a guard that passes before the work. Only a pin moved in
   `.behave/pyproject.toml` fails after the work and not before.
3. L15, the four "fails on" cases and the mutation. These are checked only by changing the tree:
   removing `.behave/pyproject.toml`, removing `.behave/uv.lock`, loosening a pin, or moving one. The
   bar does not say whether the suite itself holds these cases, the way
   `test_the_exact_pattern_refuses_a_range_and_accepts_a_pin` holds the pattern's
   (`test_pins.py:L65-L70`). If it does not, they are checked by a run in a copy, and that copy's
   result is removed with it. A fresh session can repeat the run, so the bar can be checked. Without
   that, though, nothing the station leaves shows the cases were ever run.

Whether each case fails today was checked by reading. Today the test reads nothing under `.behave/`
(`test_pins.py:L17-L18`, L46), so the unpinned, missing-manifest and missing-lock cases pass today and
fail after the work: each is a real failing case. "reads nothing when `.behave/` is absent" passes
both before and after, so it is a guard, and it stands beside the failing cases.

## 4. Cannot be met where it stands

None found. S1 is the only station. What its bar needs is on disk or is S1's own work:

- `.behave/pyproject.toml:L5-L9` declares `behave==1.3.3`, `httpx==0.28.1` and `playwright==1.65.1`.
  `.behave/uv.lock` fixes `behave 1.3.3`, `httpx 0.28.1` and `playwright 1.65.1`, read with `tomllib`.
  So the new checks pass on the tree as it stands, and "the suite stays green" can hold after them.
- Both `.behave/pyproject.toml` and `.behave/uv.lock` are tracked (`git ls-files .behave`).
- `declared_dependencies` (`test_pins.py:L21-L29`) already reads `[project] dependencies`, where the
  folder declares its three.
- The suite is green at the review commit. In a disposable clone, the card's `Test command:` gave
  "3276 passed, 2 skipped" for `tests/` and "122 passed" for `tests/e2e/`, both exit 0.

## 5. Divergence lines

None found. L17 claims "one test file, one capability, one merge", and S1's line (L15) names only
`test_pins.py`. L17 also claims "the bar now names the missing-manifest and absent-folder cases", and
L15 does name them: "on a `.behave/` holding no manifest" and "reads nothing when `.behave/` is
absent".

## 6. Readings left open

1. L7, "QC-40's lock clause rides on it".
   - **Reading A.** This is a note about dependency, not work. QC-40's lock clause, "A critical
     advisory against a test dependency either lock file of QC-39 fixes" (`docs/nfdr.md:L455`), names
     the folder's set only once QC-39 holds it, so there is nothing more to build.
   - **Reading B.** The station must also show QC-40 being met for the folder's lock. QC-40 is a
     review gate with no test row ("QC-12, QC-25, QC-26, QC-27, QC-40, QC-41 and QC-60 are review
     gates and have no row", `docs/nfdr.md:L815`), so no test bar could carry it.
   - S1 follows A, because it says nothing about QC-40.
2. L7, "reads the second manifest and lock the same way".
   - **Reading A.** "The same way" means the three checks QC-39 names: "fails on a test dependency
     not pinned with `==`, on a missing lock file, or on a declared dependency its lock file does not
     fix at its declared version" (`docs/nfdr.md:L424-L425`).
   - **Reading B.** It means every assertion the root's tests make, which also include "the manifest
     declares no dependency, so there is nothing to pin" (`test_pins.py:L35`) and "uv.lock holds no
     package record" (`test_pins.py:L49`).
   - S1 follows A. It carries neither of B's two extra cases.

## What this review could not read

None.
