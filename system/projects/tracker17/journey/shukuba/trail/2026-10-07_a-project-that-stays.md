# 宿場 Shukuba — a first project that stays across a restart

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-07_first-project`. Slug: `a-project-that-stays`.*

## What it is

One path through all five parts and all seven seams of the SDD (`products/tracker17/docs/SDD.md` § 3), under the real start command `python3 main.py`: the first-run Projects page, the create-project form, refusals that keep the typed text, the project's page, the not-found page, and saved data under `data/` that survives a stop and a start. It is one station because a domain layer alone leaves nothing a reader can run, and this path is where § 11 R-2 (focus on a form control) and § 4 RT-10 (a line break counted in a multi-line field) are first tested. It is the behaviour and command halves of SDD § 6 S-1; the README is the next station. It may take several change units.

## Reached when

Each is checked from `products/tracker17/` in a fresh checkout.

1. `python3 main.py` prints the address and the saved-data location, nothing before them, and serves until stopped.
2. In a browser: the first-run Projects page shows the create form with a note beside the description field that it cannot be changed later and the most characters it holds. Creating a project lands on its page, which shows its name and description and says it has no tasks yet, with no add-task form. A blank name and a name already in use (case ignored) are each refused beside the name field, typed text kept, page opened at the name field. Projects lists every project by name. After stopping and starting, the project is still listed. An address for a project that does not exist shows the not-found page, which speaks of a project only and links to Projects only.
3. Starting while something else holds the address prints one plain message.
4. After a project is created, `git status --short` run in the copy lists nothing under `data/`.
5. `pytest tests/` and `pytest tests/e2e/` each exit 0, and between them they hold at least one unit, one integration and one end-to-end test, including the tests SRS AC-9, AC-10, AC-18 and (for a project) AC-6 describe.
6. Named tests exist and pass: an end-to-end test that a refused name opens the page with keyboard focus in the name field and the reason as its accessible description (§ 4 EX-4, EX-14, RT-9); an end-to-end test filling the description to its maximum with line breaks and finding it saved whole (AC-20, description half); a test sending a `main`-started tracker a name over the maximum, finding the answering page gives the reason, holds none of the sent text, and the saved data unchanged (AC-12, § 4 RT-8, RT-10, § 11 R-10); an integration test that the number the form's sentence states equals the description field's `maxlength` (§ 4 RT-10).
7. `domain/projects.py` and the directories `application/`, `persistence/` and `web/` exist under `products/tracker17/` (`ls` lists them; before this station `ls products/tracker17` lists `errors.py main.py pyproject.toml README.md tests`).
8. The pointer test fails both ways SDD § 4 TS-4 and NFDR QC-11 state: `tests/architecture/test_trace.py` holds a test that fails when a feature word in TS-3's table has its `domain/<word>.py` and is not in `LANDED_FEATURE_WORDS`, beside the existing one for a landed word with no module, and `pytest tests/` passes.

## Guardrail

- Do not weaken the SDD's seams to land this faster: all five parts are used, not a shortcut through one.
- Do not add tasks, the add-task form, People or All tasks links, rename or delete. Do not add the unreadable-data page or the second-tracker refusal; a start that cannot read the data stops with one plain message and writes nothing (§ 4 SD-4).
- Do not touch the setup README beyond what the tests need; its sections are the next station's.
- `data/` stays out of version control.
- **Not here:** `tracker17 · nemawashi · 2026-10-07_first-project` item 2 (`setup-instructions`); `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`.

*Amended by `shukuba-refine`, 2026-10-07: reached-when 8 added. SDD v6 § 4 TS-4 (RN-34) and NFDR QC-11 now state the reverse pointer check, the test file holds only the forward one, and no station on the route lands it.*
