# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-12
- **Sources re-read:** None — no answer this run gave rests on a source outside this repository.
  Read in-repo besides `SDD.md` (the header, § *Who decides what*, § 3, § 4, § 6 S-3, § 10, RN-45,
  RN-46 and § Open Questions) and the companion: `domain/operator_name.py:40-62`;
  `application/tracker.py:60-160`; `domain/tasks.py:246-290`; `web/routes.py:586-615`;
  `tests/integration/test_people_routes.py:495-533`; `tests/unit/test_tasks.py:727-740`;
  `SRS.md` FR-9, FR-27, NFR-3, DR-5; `UXD.md` UX-F8, UX-F9; `fdr.md` R-62, R-65; `nfdr.md` QC-21,
  RN-37, RN-38; `architecture_open_issues.md` whole; `trail/sdd/cycle-6.md` and
  `trail/sdd/self_answer-8.md`, the previous round; the open station
  `system/projects/tracker17/journey/shukuba/2026-10-12_operator-name.md` and its refine report
  `journey/nemawashi/2026-10-07_comment-on-a-task/2026-10-12_operator-name_report.md`. No suite was
  run: the item is about what the code says, which was read on disk at `main` `22660036e`, and the
  round changes no code.

The companion held one open item, § 5.1, `Seat: cto`, and the invocation listed none, so this run
worked it. It cites an occurrence, `domain/operator_name.py:L59-L62` on `main`, and asks for a
statement found false to be corrected, not for the document to state a case it does not state, so
§ *A widening item waits until it occurs* does not send it back.

## Items worked

### 5.1 — § 3's `application` row says every action's report compares with the value the page showed; setting the operator name compares with the saved name

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** confirmed with addition
- **Why:** The item hands a concrete change ("qualify the comparison sentence as the task edit's
  rule (§ 4 RT-7), and say that setting the one operator name reports no change when the submitted
  name equals the saved name at the moment of the action; the comparison stays `domain`'s, and
  `application` still compares nothing"), so I treated that sentence as the draft, as the prompt says
  to do with a lean in a bucket that nominally carries none, and weighed it. The draft holds and is
  taken; two things are added. One question, one seat; it did not split.

  *Seat (check 1).* The edit lands in § 3's `application` row, a CTO row in § *Who decides what*.
  The answer binds this document's agreement with the product and nothing outside it — no person,
  no party, no risk the owner carries — and I can name no ground I cannot see. Mine, in the owner's
  seat. The same sentence in NFDR QC-21 is the Principal Architect's and already carries its own
  item, `architecture_open_issues.md` § 3.1 (commit `15b201d62`), still at its placeholder.

  *The draft holds (check 2), and the answer.* Every citation in the item is as stated: the row is
  `SDD.md:202`; `domain/operator_name.py:60-62` returns `state, OperatorNameOutcome(..., changed=False)`
  when `checked == state.operator_name`; `tests/integration/test_people_routes.py:520-533` asserts
  the form's inputs are `["name"]` and that a stale page's repeat of the saved name saves nothing.
  The draft's reason holds too: § 4 RT-7 already says "The task's edit form is that form", so the
  shown-value comparison was the task edit's in § 4 before § 3's row generalised it in cycle 6, and
  SRS NFR-3 states the other rule as the default — "Every action is checked against the saved data
  at the moment it is applied, not against what the page showed". The sentence the row needs is
  therefore the general one: what the report compares is `domain`'s, per action, with the task edit
  as the one action that compares with what the page showed. **Addition one** is a second occurrence
  the item did not name: `domain/tasks.py:253-258`, `add_task_label`, checks the label "against the
  labels it carries now" and reports `changed=False` for one already carried
  (`tests/unit/test_tasks.py:727-735`). That is the same shape as the name — a comparison with the
  state at the moment of the action — and it falsifies the row's "never of the new state with the
  current one" a second time. Labels landed at `25fff47d2` and the name at `cb48338e3`, both after
  version 9 (`33ad1a2a7`), which is why RN-45 could say "the edit is the one action that reports"
  and name the label as a future second; both lines are a dated record and stay. Naming the per-action
  rule rather than two exceptions keeps the row true when a fourth action reports. **Addition two**
  says what does not move, because the item's heading invites a reader to look for the sentence
  elsewhere: RT-7 is not changed; § 4 SD-2 and SRS FR-9 bind the done report to the disk, and
  `web/routes.py:605-606` redirects to plain People with no `operator_saved` when `outcome.changed`
  is false (`test_people_routes.py:502-518` asserts no completion line and no focus), which is UXD
  UX-I4; FDR R-62 and R-65, SRS DR-5, UXD UX-F8 and S-3's behaviour line stand as written. I put the
  answer in the SDD's words ("makes it current", "at the moment of the action") and kept NFR-3's
  citation, so the fold can trace the saved-state rule to a requirement rather than to the code.

  *Nothing settled moves (check 3).* No requirement changes: NFR-3, FR-9, FR-27 and DR-5 hold, and
  NFR-3 is strengthened, not contradicted — the task edit is its stated exception ("replaces whatever
  the other tab saved for that field"). No § 4 condition changes. No slice's *Reached when*, fence or
  place moves and no edge in § 7 changes, so this is a correction of a part's description, as RN-45
  was, not a re-cut under § 10. The answer agrees with the architecture companion's § 3.1 ask
  ("qualify other actions by their own `domain` comparison"), which covers the label without naming
  it; I did not revise that item, because its ask already carries the general rule and the
  Principal Architect's run reads § 3's row as its source. No earlier answer of this run bears on it;
  there was one item.

  *Failure paths (check 4).* *Empty*: no name saved yet — `state.operator_name` is `None`, any valid
  name differs, so the first set reports a change. *Absent*: nothing to find — the name is one
  field of the state, so the task edit's `TaskNotFound` path has no counterpart. *Stale*: both
  halves are in the answer, and they differ by action — a task field changed to the other tab's value
  saves; a name or a label equal to the other tab's value does not. *Concurrent*: § 4 RT-6 applies
  one request at a time, so "at the moment of the action" is read under the lock. *Refused*: a blank
  or too-long name is raised by `domain` before any outcome (`operator_name.py:47-49`), `web` keeps the
  typed text for a blank and nothing for too long (RT-8's exception), and nothing is saved. *Failed*:
  a no-change name never reaches the saver, so SD-2's failure branch cannot arise on it; on a
  changed name it stands as written. I was close to a plain *confirmed*, and the label occurrence
  tipped it: a row that said "the operator name is the exception" would be false again for labels
  on the day it was folded.

  *What I considered raising and did not.* The SDD header says "`products/tracker17/docs/SDD_open_issues.md`
  does not exist, and its absence is the done signal", and its *Inputs read* names NFDR version 10
  where `nfdr.md` is now version 11. Both are facts the fold rewrites on every round as part of
  consuming this companion, so neither is owed a cycle of its own.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
