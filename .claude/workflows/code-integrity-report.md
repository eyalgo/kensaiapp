# Code integrity report — eval staging wiring

**Reviewed:** 2026-07-25 · commits `458b20d..39276c2` (12 commits, `ab27f2c` first)
**Skill:** `development-code-integrity`, interactive mode, on `main`

## What was reviewed

| File | Role in the change |
|---|---|
| `.claude/workflows/run-skill-evals.js` | the workflow — plan tasks 1–5 |
| `.claude/workflows/tests/run-skill-evals.test.js` | its source-regex test file — plan tasks 1–5 |
| `.claude/skills/skill-evals/SKILL.md` | the caller-facing doc — plan task 6 |

The three scripts the wiring calls into — `stage_fixtures.py`, `harvest_run.py`, and the viewer's
`generate_review.py` — were **read but not modified**, and `git diff 458b20d..HEAD` confirms the change
touched no file under `scripts/`. The plan fenced them as done and tested; they were read only to verify
the workflow's calls against their real CLIs.

## The intent it was checked against

The `ad-hoc-implementation` plan package `eval-staging-wiring`, at
`…/scratchpad/eval-staging-wiring-plan.md`. Its six tasks each carry a stated intent and a
`#### Behaviours to verify` list; those behaviour lists are the reference, in the same position a
`tl_instruction.md` would occupy.

**No test in this report was derived from the implementation.** Each new test names the plan behaviour it
covers. Where a behaviour is a regression guard against the *pre-change* state (task 5's "run_manifest.json
keeps every field it already has"), the field list was taken from the manifest literal at `458b20d` — the
baseline the behaviour names — not from the current source.

## Coverage walk — 26 stated behaviours

Every behaviour in tasks 1–5 was walked against the test file. Twenty-six behaviours; eighteen already had
a test that would fail if the behaviour broke. Eight did not, and are the tests added below.

| Task | Behaviour | Before | Now |
|---|---|---|---|
| 1 | `Stage` in `meta.phases`; `meta` stays a pure literal | covered | — |
| 1 | `phase('Stage')` after Setup, before Execute | marker order only | **strengthened** |
| 1 | Stage `agent()` invokes `stage_fixtures.py` with `--skill-dir` + `--workspace` | flag names anywhere in file | **strengthened** |
| 1 | requests structured output through a schema whose properties include `cases` | schema declared | **added** — schema reaches the agent |
| 1 | staged result bound to a module-level const the executor reads | covered | — |
| 1 | Stage prompt says return stdout JSON verbatim | covered | — |
| 2 | executor composes its prompt from the staged prompt for `(item.name, item.config)` | old form gone + lookup exists | **added** — template interpolates it |
| 2 | prompt states skill-resolved files are not redirected | covered | — |
| 2 | `Input files: none` gone | covered | — |
| 2 | a `Save all output files to:` instruction still exists | covered | — |
| 2 | `phase: 'Execute', ...EXECUTOR_OPTS` exactly once | covered | — |
| 2 | arm difference remains the ternary | covered | — |
| 3 | harvest invoked with `--config-dir` at `<workspace>/<case>/<config>` | flag name only | **added** — target pinned |
| 3 | after the executor completes, before grading | not covered | **added** — ordering |
| 3 | harvest phase name ≠ `'Grade'`, declared in `meta.phases` | covered | — |
| 3 | both grading prompts name `run_delta.json`, `product/`, `reference/` | covered | — |
| 3 | harvest runs for every run item, not only with-skill | **not covered** | **added** |
| 4 | throws when a staged prompt still names the fixture root | `throw` exists | — |
| 4 | in either its absolute or its repo-relative spelling | not covered | **added** |
| 4 | keys on the resolved fixture root, not bare `evals/inputs` | covered | — |
| 4 | error names the offending case and configuration | covered | — |
| 4 | a no-fixture skill passes without throwing | covered | — |
| 5 | `eval_metadata.json` carries the **staged** prompt under `prompt` | only `authored_prompt` checked | **added** |
| 5 | authored prompt under a distinct key | covered | — |
| 5 | `run_manifest.json` keeps every field it already has | 3 of 9 fields | **strengthened** to all 9 |
| 6 | prose only — verification gate is a grep | n/a | gate run, below |

## Tests added or fixed

Ten tests added; **no existing test was changed or removed**. All ten derive from the plan, not from owner
expectations and not from the code.

1. **the Stage agent requests structured output through its schema, in the Stage phase** — task 1. The old
   test proved a schema containing `cases` exists in the file; it did not prove the schema reaches the
   agent. A declared-but-unpassed schema returns free prose, every `STAGED.cases` lookup goes `undefined`,
   and the executor silently falls back to the unstaged prompt — the exact failure staging exists to close,
   reappearing with the whole suite green.
2. **`stage_fixtures.py` is invoked with the run's own skill dir and workspace** — task 1. The old test
   matched `--skill-dir` and `--workspace` anywhere in the file, which a half-wired call also satisfies.
   Now pinned as one invocation carrying `${skillDir}` and `${workspace}`.
3. **staging runs after Setup's work, not merely after the `phase()` marker** — task 1's "after the Setup
   phase's work". Staging's real dependency is Setup's *output*: `workspace` is derived from
   `setup.next_iteration`, so a `phase('Stage')` placed before the setup agent returns would stage into
   `iteration-undefined` while the old marker-order test stayed green.
4. **the executor prompt template interpolates the staged prompt** — task 2. The old tests proved the old
   interpolation is gone and that a lookup exists *somewhere*. Neither proves the template handed to the
   executor uses the staged value; a dead lookup plus any other spelling of the authored prompt passed both.
5. **harvest is pointed at the run's own `<case>/<config>` directory** — task 3. `harvest_run.py` resolves
   `inputs/`, `outputs/` and `staged_manifest.json` relative to `--config-dir`; pointed at `outputs/`
   instead it exits 0 as a silent no-op (verified: `harvest_run.py:88-94`). Only the flag *name* was tested.
6. **harvest runs after the executor and before any grading agent** — task 3's ordering clause, untested.
   Harvesting too early records an empty delta; too late and the grader cannot read it.
7. **harvest runs for every run item, not only the with-skill arm** — task 3, wholly untested. The baseline
   arm's delta is what makes a where-did-it-land assertion a comparison rather than a claim about one run.
8. **the guard checks both the absolute and the repo-relative spelling of the fixture root** — task 4,
   untested. `stage_fixtures.py:143` rewrites exactly those two spellings, so a guard checking one leaves
   the other able to reach an executor un-rewritten.
9. **the per-config `eval_metadata.json` records the STAGED prompt under `prompt`** — task 5's headline
   behaviour, untested. The old test proved `authored_prompt` exists and the path is right, but not that
   the key the viewer actually displays holds the staged value.
10. **`run_manifest.json` keeps every field it had before staging was wired** — task 5. The old guard
    checked three tokens out of nine fields; five could vanish with it green. Now enumerates all nine.

Each new assertion was checked for **discriminating power**, not just for passing: every one was re-run
against a deliberately mutated copy of the workflow source and confirmed to fail. A test that stays green
under the broken behaviour is worth nothing, and three of the eight gaps above were exactly that shape —
an assertion satisfied by a token's mere presence.

## Task 6 — the verification gate

Task 6 is prose with no spec tests; its gate is a grep, and that is all it can be. All four points pass:

- no assertion that both arms share one fixture tree survives — Step 2b now states the opposite and
  correctly re-aims the guard at the *tracked* tree as the remaining hazard;
- `stage_fixtures.py` and `harvest_run.py` both appear in the supporting-tools list (`SKILL.md:71-72`);
- the File Structure tree names `inputs/`, `staged_manifest.json`, `run_delta.json`, `product/`,
  `reference/`, per configuration;
- both suites still green (no-regression check).

## Cold-read verification

The closing commit marks `handoff-cold-read` done, noting the pass ran "inline" rather than through the
skill. Treated as a claim to verify, not a fact. A sample of the named resources, checked against the real
files this session:

| Claim | Verified against | Result |
|---|---|---|
| `stage_fixtures.py --skill-dir --workspace` | `stage_fixtures.py:153-154` | correct |
| its stdout carries `repo_root` / `fixture_root` / `cases`, matching `STAGE_SCHEMA` | `stage_fixtures.py:212-217` | correct |
| a no-fixture skill prints `fixture_root: null`, `cases: {}` and exits 0 | `stage_fixtures.py:188-195` | correct — and the guard's `if (STAGED.fixture_root)` gate is what makes that payload safe, since it carries no `repo_root` |
| the guard's two spellings are the two `rewrite_prompt` replaces | `stage_fixtures.py:143` | correct — absolute and `relative_to(repo)`, exactly |
| `harvest_run.py --config-dir` is the `<case>/<config>` dir | `harvest_run.py:27, 80, 84-86` | correct |
| `staged_manifest.json` sits beside `inputs/`, where harvest looks | `stage_fixtures.py:130` writes `dest_inputs.parent`; `harvest_run.py:103` reads `config_dir` | correct |
| harvest finds the pristine tree via `stage_manifest.json` at the workspace root | `stage_fixtures.py:219` writes it; `harvest_run.py:62-72` walks parents | correct |
| the viewer prefers a config-level `eval_metadata.json` over its eval-level parent | `generate_review.py:92` | correct — `run_dir` first, then `run_dir.parent` |
| `commit_builder` flags (`--add`/`--actor`/`--skill`/`--directional`) | `commit_builder.py commit --help` | correct |
| `developer` maps to `Role: Developer` | `commit_builder.py:87-99` (`AGENT_ROLE`) | correct |

Ten claims checked, ten hold. The inline pass did not miss anything in this sample — but "inline" is not
the skill, and this report verifies the sample, not the pass.

## Commit count

The closing commit reports "13 commits" while listing 12. **Twelve landed, and nothing is missing.** The
structure accounts for all six tasks exactly: tasks 1–5 each contributed a `— red` / `— green` pair (ten
commits), task 6 contributed one commit and correctly no pair because the plan states "No spec tests" for
it, and the closing empty marker is the twelfth. The miscount is in the prose of a report, not in the work.

## Finding

**No bugs found in the code.** All 26 stated behaviours in tasks 1–5 hold in the implementation, and task
6's grep gate passes. The eight gaps above were **missing or non-discriminating tests, not defects** — the
behaviours they now pin were already correct, and the tests were added so a future regression cannot pass
silently.

Two items are recorded below rather than resolved, neither of them a code defect:

- an **open intent question** on the unconditional staged-prompt fallback — not a proven defect, and
  resolving it requires a decision the plan does not make;
- an **owner-raised layer-placement finding** on task 6's documentation — a real defect, but in the plan's
  instruction rather than in the developer's execution of it, and outside this pass's remit to fix.

### Open question — the unconditional staged-prompt fallback

Task 2's behaviour reads: *"The executor `agent()` composes its prompt from the staged prompt for that
`(item.name, item.config)`, and the raw `item.prompt` no longer reaches any executor."*

The implementation composes `STAGED.cases?.[item.name]?.[item.config]?.prompt ?? item.prompt` — so the raw
authored prompt *can* still reach an executor, whenever the staged lookup misses. The same fallback shape
appears in the task-5 metadata write.

Two readings of the behaviour, both defensible:

- **The fallback is required.** Task 4's fourth behaviour says a skill with no fixture tree at all must pass
  the guard cleanly. For such a skill `STAGED.cases` is `{}`, nothing is staged, and without a fallback the
  executor would receive `undefined`. Under this reading "the raw `item.prompt` no longer reaches any
  executor" describes the removal of the *old direct interpolation* — which is done, and already tested.
- **The fallback is too wide.** It is not scoped to the no-fixture case. For a skill that *does* have a
  fixture tree, a single case missing from `STAGED.cases` silently sends the authored, un-rewritten prompt
  to that executor — and the task-4 guard cannot catch it, because the guard iterates `STAGED.cases` and
  inspects the *staged* prompts, which are correctly rewritten. That is precisely the "silently produce a
  graded result" outcome task 4 exists to prevent, arriving through a path the guard does not watch.

Reachability is narrow but real: `stage_fixtures.py:199` keys cases by the `name` it reads from
`evals.json` directly, while the workflow keys by the `name` the Setup **agent** reported for the same
field. Both read the same field, but one reads it through a model — so the keys diverge on a transcription
slip, not on a code path.

**Not acted on.** Removing the fallback breaks task 4's no-fixture behaviour; scoping it to
`!STAGED.fixture_root`, or raising when a fixture-having skill has an unstaged case, is a behaviour change
the plan does not ask for. Under this skill's own rule — STOP when it cannot be told from the intent
whether the test or the code is wrong — no test was authored for it and no fix was invented. There is
therefore **no red commit**: the stop is on an intent question, not on a failing test.

### Finding (owner-raised) — the new artifact shapes landed in the wrong layer

Raised by the owner during this review, verified independently here, and **recorded rather than fixed**.

Task 6 had the developer expand the `## File Structure` tree in `SKILL.md` with the staged `inputs/`,
`staged_manifest.json`, `run_delta.json`, `product/`, and `reference/`. This skill already has a layer that
owns artifact shapes and locations: `references/schemas.md`, whose every section is one artifact —
`## evals.json`, `## grading.json`, `## metrics.json`, `## timing.json`, `## benchmark.json`
(`references/schemas.md:7, 52, 132, 166, 188`). Its own header states the job: *"This document defines the
JSON schemas used by skill-evals."*

So the two newest artifacts are documented in the layer that should only point, and are **absent from the
layer that should own them** — `grep` for `run_delta` / `staged_manifest` in `references/schemas.md` returns
nothing. Two consequences:

- the shapes now live away from the scripts that write them (`stage_fixtures.py:123-132` writes
  `staged_manifest.json`; `harvest_run.py:146-160` writes `run_delta.json`), so they will drift;
- a reader looking in the obvious place will not find the two newest artifacts at all.

**Attribution: not the developer.** The plan's task 6 instructed exactly this — *"Update the File Structure
tree to show, per configuration, the staged `inputs/`, the sibling `staged_manifest.json`, and inside
`outputs/` the `run_delta.json` plus `product/` and `reference/`."* The developer implemented the
instruction faithfully. The instruction named the wrong layer.

Corroboration from inside the change under review: the workflow's own comment and the existing test both
already treat `references/schemas.md` as the documenting layer — `run-skill-evals.js:89` ("README.md and
references/schemas.md have always documented") and `run-skill-evals.test.js:64` (citing
`references/schemas.md:48`). The layer convention is not an outside opinion; the reviewed code appeals to it.

**One extra fact for whoever performs the relocation:** there is today **no pointer at all** from `SKILL.md`
to `references/schemas.md` — `grep` finds no reference to `schemas.md` anywhere inside the skill directory;
the only two mentions in the tree are the workflow comment and the test comment above. So "leave `SKILL.md`
pointing at it" means *creating* a pointer that does not currently exist, not editing one. `README.md`
mentions neither artifact either.

**Why this pass records it instead of fixing it.** I agree with the owner's scope call, and would have held
the same line unprompted: this skill's remit is proving the code does what its intent says by making the
tests match that intent. A documentation-layer relocation is neither a test nor a code-correctness matter,
and this skill's contract explicitly excludes redesigning things and authoring specs. Relocating prose
between two documentation layers — and creating a cross-layer pointer that has never existed — is a change
to how this skill's docs are organised, which is a decision above this pass. Recorded, not performed.

**Where it does touch this review, and it is worth naming.** Task 6's verification gate is a `grep` for five
tokens in `SKILL.md`, and it passes — I reported that above, and it remains true. But this finding is the one
place in the whole review where *the gate passing* and *the outcome being right* come apart: a token-presence
grep confirms the content is **present** and is structurally blind to whether it is present in the **right
layer**. The gate could not have caught this, by construction. That is a limit of the gate the plan chose,
not a failure to run it — and it is the reason a human layer-check found what the grep could not.

## Verification

| Command | Result |
|---|---|
| `python3 -m pytest .claude/skills/skill-evals/scripts/ -q` | 35 passed |
| `node --test '.claude/workflows/tests/*.test.js'` | 56 tests, 56 pass, 0 fail (was 46) |
| `node --check .claude/workflows/run-skill-evals.js` | exit 0 |

## The honest limit of this check

Tasks 1–5 are behaviours in a workflow whose tests are **regexes over its own source text**. That is the
established technique in this file, and for a stated reason: the script has top-level `await` and injected
globals so it is not importable, and the Workflow runtime has no filesystem and no shell, so there is
nothing to execute in a test harness.

Every one of the ten tests added here is therefore a **source-text assertion**. Each proves a line is
present, correctly valued, and correctly positioned relative to its neighbours; **none proves the wiring
runs.** Concretely: nothing here demonstrates that `stage_fixtures.py` was ever executed by the workflow,
that a staged prompt reached a real executor, or that `run_delta.json` was ever produced or read. The
strongest claim these tests support is that the wiring cannot be *deleted or reordered* without a test
going red. Proof that it *runs* needs one real eval iteration, and that is outside this review.

Task 6 has no test at all, by the plan's own instruction. Its gate is a grep over prose, and a grep is the
whole of the assurance available for it.
