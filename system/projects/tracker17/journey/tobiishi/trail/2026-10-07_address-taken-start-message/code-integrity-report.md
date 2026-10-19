# Code integrity report — 2026-10-07_address-taken-start-message

Integrity: pass

## Deferrals

None. The newest closing marker, `af3439893` (it supersedes `6c778da38`), carries no `Deferred:` line.

## What was reviewed

The change's code commits `2235ac548`..`b3344945a` under `products/tracker17/`: `web/listener.py`,
`web/__init__.py`, `main.py`, `tests/integration/test_listener.py`, `tests/integration/test_start.py`,
`tests/e2e/test_start_command.py`.

## The intent it was checked against

`tl_instruction.md` (Tasks 1 and 2), `change_spec.md` (CP-39 to CP-46, Locked Answers Gaps 1–8),
`change_design.md`, and `change_text.md` for the line's words. `docs/fdr.md` R-4 was the context.

## Placement

The parts table is `docs/SDD.md` § 3.

- `AddressTaken`, and telling "address in use" apart from other bind failures, sit in `web/listener.py`.
  That is `web`, which owns "listening on the loopback address" (`SDD.md:194`) and the outward signal
  of SM-6 (`SDD.md:217`). Already in place.
- The console line and the failing status sit in `main.py`. That is `main`, which "writes the start
  messages to the console" (`SDD.md:195`). Already in place.

Nothing was moved, so there is no placement commit.

## Tests added or fixed

All are in `tests/integration/test_start.py`.

- **Added: `test_a_start_refused_the_address_for_another_reason_is_not_told_it_is_taken`**
  (CP-42, Gap 5). Before this test, no case checked `start` against a bind failure that is not "in
  use". A `main` that caught `OSError` along with `AddressTaken` would print the address message for
  a cause the tracker never established, and every test would still pass. Proved: with
  `except (AddressTaken, OSError)` patched into a scratch copy, this test went red. The rest of
  `test_start.py` stayed green, apart from `test_data_is_ignored_by_version_control`, which fails
  only because the copy is not a git repository.
- **Fixed (tightened): `test_a_held_address_leaves_existing_saved_data_untouched`** (CP-39, CP-41).
  The test dropped blank lines before comparing standard error and never looked at standard output.
  CP-39 requires exactly one message on standard error and nothing on standard output. It now
  asserts `out == ""` and an exact `err`.
- **Fixed (tightened): `test_unreadable_saved_data_wins_over_a_held_address`** (CP-43). It also
  dropped blank lines, and it did not check the directory's listing, which CP-43 inherits from CP-7.
  It now requires exactly one line on standard error and an unchanged listing. The address-message
  check now covers all of standard error, not only the first line.

## The finding

No bug. The code already did what its intent says. The suite missed one case (CP-42 at the start
level), and two tests were looser than their rules, so a wrong `main` could have passed them. All
three are now covered. `pytest products/tracker17/tests/` → 209 passed; `pytest
products/tracker17/tests/e2e/` → 12 passed (venv `/private/tmp/t17venv`, outside the repo).

## Calls made

- **Which reading of "behaves as today" CP-42 asks of `start` for another bind failure.** Option 1:
  the `OSError` keeps propagating out of `start`, as it does today. Option 2: `start` turns it into
  some message of its own. I took option 1. The spec says the behaviour "is unchanged here" (Out of
  Scope; Gap 5). The design says every other bind failure "propagates as it does today" (§ 1).
  `change_text.md` writes no string for that case. The new test therefore asserts that an `OSError`
  propagates and is not an `AddressTaken`. Owner: the Product Owner (`change_spec.md`). If they rule
  for option 2, that start needs words from the content step, and this test changes.

## Language resolution

- Python, from `project.md` `Languages:` (chain step 1).
- Packet read: `languages/python/README.md`, with `conventions.md` and `testing_python.md`.
- The bar held for the added lines:
  - lines within 100 columns (checked with awk);
  - `from __future__ import annotations` is already the file's first statement;
  - no `monkeypatch`: the address is held with a real socket and the bind failure comes from a real
    documentation address;
  - layer-2 tests go under `pytest tests/`.
- I agree with the developer's two recorded packet divergences, in its marker at `af3439893`: no
  `__version__` marker, and no `error: ` prefix on the CONTENT line.
