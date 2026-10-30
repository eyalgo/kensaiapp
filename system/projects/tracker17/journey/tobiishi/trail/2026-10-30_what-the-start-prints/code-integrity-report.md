# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

## Deferrals

None. The closing marker `<a commit not in the public history>` carries no `Deferred:` line.

## What was reviewed

`products/tracker17/README.md`, section `### What the start prints`, the only product file the change touched. The diff from merge base `5e46e3a1a` to `<a commit not in the public history>` holds no code and no test.

## The intent it was checked against

`tl_instruction.md`, then `change_spec.md` (CP-736 to CP-746), with `change_design.md` § 5 (V1 to V13) for the checks and `change_text.md` for the approved strings. `products/tracker17/docs/fdr.md` was not needed: nothing was left open that it would settle.

## The tests added or fixed

None. `change_spec.md` § Out of Scope excludes every test, so each rule was proved by the plan's commands or by reading (see Calls made).

## Test evidence

The card's test command, through the gate tool, on `<a commit not in the public history>`: exit 0, 2813 passed and 122 passed. This is the only full run this step made.

| Rule | Check | Result |
|---|---|---|
| CP-736 (V1, V2) | The section-only `awk` and `grep` count | Base `0`, branch `2` |
| CP-737 (V3) | Section read; `products/tracker17/main.py:168-173`, `_unreadable_line`, read | Names the line by its starting words with a straight apostrophe, for a start on saved data it can't read. No longer quotation |
| CP-738, CP-739 (V4) | Section read; grep for `lost`, `delet`, `corrupt`, `damag` | Still running, keeps running until stopped, follows `Setting saved data aside` to start fresh on purpose. Grep: no hit. The heading exists in the README |
| CP-740 (V5) | Section read | Ready example kept, own location explained, running stated, Projects page tied to that line |
| CP-741 (V6, V7) | Section read; both refusal strings read, `products/tracker17/main.py:33,154` | "this start has stopped", and one sentence covers both refusals. Each string gives its reason and next action. Nothing says the earlier tracker stopped |
| CP-742 (V8) | Section read | The keep-running and Ctrl-C sentences name the two running lines. The failed-start paragraph comes last |
| CP-743 (V9) | Section read; grep for `three`, `traceback` | No claim that nothing else appears. Grep: no hit |
| CP-744 (V10) | The named passage compared with the merge base | Identical |
| CP-745 (V11, V12) | Product diff excluding the README; `git diff --check`; README bytes outside the section compared with the merge base; both suites | Empty, clean, identical, green |
| CP-746 (V13) | Each sentence in the section counted; `products/tracker17/docs/CONTENT.md` § Grammar and mechanics and § Terminology read | Longest sentence is 19 words. Uses "terminal", "saved data" and contracted negatives |
| Approved text | Every `change_text.md` string searched for in the section, in order | All six present in order, nothing else in the section but the example's fence |

## The finding

No issues. Nothing was moved, the intent excludes new tests, every rule above holds, and both suites passed.

Carried, not acted on: `change_text.md` § Findings for the Content Manager, on "stopped" having no `CONTENT.md` term for a start that ended by itself after a refusal. It stays with that seat.

## Calls made

- **Does this step add a test for the section?** Step 1 asks for a test per behaviour; `change_spec.md` § Out of Scope excludes every test, and `tl_instruction.md` makes Task 1 review-verified. Took the spec's reading: no test added, each rule proved by command or reading instead. An added test would have broken CP-745 and asserted the meaning of prose by string match. The document is the Product Owner's, with the Tech Lead's plan under it. If they rule the other way, a later change adds a test that reads the section, and this change's product text doesn't move.

## Placement

No new logic. `products/tracker17/docs/SDD.md` § 3 was read, and the change adds prose only, so no piece of logic had a part to be walked against. No `… — placement` commit.

## Language resolution

Python, chain step 1, `system/projects/tracker17/project.md` `Languages:`. Packet read: `languages/python/README.md`, with `conventions.md`, `quality_gates.md`, `testing_python.md` and `environment.md`. The suite gate was run. No Python changed, so the conventions and the compile gate bore on nothing, and the compile gate was not run.
