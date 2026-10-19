# 根回し Nemawashi seed — from a fresh copy to a first project that stays

## What it is

Serves the Way `fit-to-publish`: `products/tracker17/README.md:L3-L5` says tracker17 exists so a reader can "read a whole product it built, run it, and judge how simple it was to set up", and this seed delivers that setup and the first code to read. It is the first thing worth having on the product: after it, a reader follows the written setup instructions from a fresh copy to the tracker open in their browser, creates a first project, and finds it still there after stopping and starting. It carries one action from a page through the rules into the saved data and back after a restart, so it uses all five parts and all seven seams of the SDD (`docs/SDD.md` § 3) under the real start command. Moves the Agari toward its **Simple to set up** bar in full, and the first step of **Works** and **Simple to read** (`system/projects/tracker17/agari.md`).

Rests on SDD §§ 2, 3 and 4 in full; no earlier slice. Its bar is SDD § 6 S-1 *Reached when*, in three halves: the behaviour (first-run Projects page, create form, refusals that keep the typed text, not-found page, one plain message when the address is taken), the command (`python3 main.py`; both suites pass with at least one unit, one integration and one end-to-end test, including SRS AC-9, AC-10, AC-18, AC-6 for a project, and AC-20's description half) and the artifact (`products/tracker17/README.md` with every UX-S1 section; `domain/projects.py`, `application/`, `persistence/`, `web/`).

**Why it goes first.** The SDD calls it the smallest reversible slice that proves the shape (§ 6 S-1, *Why here in the order*), and it is where §11 R-2 (focus on a form control) and § 4 RT-10 (a line break counted in a multi-line field) are first tested. Finding either wrong here costs one slice.

## Source

Cut from `products/tracker17/docs/SDD.md` § 6 S-1, slug `first-project` ("After this, a reader can follow the written setup instructions from a fresh copy to the tracker open in their browser"). Behaviour traced from `docs/fdr.md`, `docs/nfdr.md` and ADR-0001 to ADR-0009 through the slice's *Traces to* line, which is not copied here. Product checked on 2026-10-07: `ls products/tracker17` lists `errors.py main.py pyproject.toml README.md tests`; `main.py:main` is empty and `README.md` says "no code exists". The slice's work is still owed.

Route re-cut at the pick, 2026-10-07: the proposal's `domain-and-saved-data` and `web-and-start` are merged into `a-project-that-stays`, because the first is a layer whose only value is that the second needs it and leaves nothing a reader can run, while one path through all five parts under the real start command is where § 11 R-2 and § 4 RT-10 are tested. The `git status --short` check moves from `setup-instructions` to `a-project-that-stays`, because the data path lands it and the README does not. The station may take several change units.

Route amended by `shukuba-refine`, 2026-10-07: `setup-instructions` now also carries `README.md` § Status, because `README.md:9-11` still says "no code exists, so there's nothing to run" while `main.py` serves the tracker, UX-S1's sections do not include § Status, and no companion template names `README.md`, so only this station can carry the fix.

Route amended by `shukuba-refine`, 2026-10-07 (after `2026-10-07_a-not-found-page`): `a-project-that-stays` also carries the pointer test's reverse direction, because SDD v6 § 4 TS-4 (RN-34) and NFDR QC-11 now state it, `tests/architecture/test_trace.py:87-90` checks only the forward one, and no station on the route lands it before `tasks-in-a-project` adds the next feature module.

Route amended by `shukuba-refine`, 2026-10-07 (after `2026-10-07_address-taken-start-message`): `setup-instructions` also carries the unreadable-data start message's pointer to "Setting saved data aside", because UXD UX-S2 asks each start failure to say what to do, `main.py:43-44` says only what is wrong, `docs/CONTENT.md:252` ends that message with the pointer, and the section it points to first exists on that station.

## Stations — dynamic checklist

- [x] a-project-that-stays — under `python3 main.py` a project is created (refusals keep the typed text), listed and still listed after a restart, an unknown address shows the not-found page, `git status --short` lists nothing under `data/`, and `pytest tests/` and `pytest tests/e2e/` exit 0 with the S-1 tests named in the seed's bar, and the pointer test fails both ways SDD § 4 TS-4 states
- [x] setup-instructions — `README.md` holds every UX-S1 section, its § Status says what runs now rather than that no code exists, a start that cannot read its saved data ends its message by pointing to the README's "Setting saved data aside" section by that heading, and a reader following only it from a fresh copy reaches the Projects page in no more than three commands

## Relation to existing work

Opens the product: `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`, `tracker17 · nemawashi · 2026-10-07_comment-on-a-task` and `tracker17 · nemawashi · 2026-10-07_status-moves` all rest on it (SDD § 7). Not-yet-cut slices that rest on it: `protect-saved-data`.

## Out (later / elsewhere)

Tasks and the add-task form (`tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`). Renaming or deleting a project (slice `delete-and-rename`, not yet cut). The unreadable-data page and the refusal of a second tracker (slice `protect-saved-data`, not yet cut); until then a start that cannot read the data stops with one plain message and writes nothing (§ 4 SD-4). The People and All tasks header links. A package, installer or hosted demo, which the PRD places out of scope.
