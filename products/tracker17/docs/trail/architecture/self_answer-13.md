# Self-answer report — `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-12
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository.
  Besides the companion, the run read these in the repo: `nfdr.md`'s header, § 1.3 (QC-20 to QC-23)
  and § 6 (QC-49 to QC-54); `adr/README.md`; `adr/0001-…` whole; `adr/0004-…` § Context and
  § Decision; `SDD.md`'s header, § 3 `application` row, § 4 SD-2, RN-45 and RN-46;
  `trail/sdd/self_answer-8.md` whole; `trail/architecture/self_answer-12.md`, the previous round;
  `fdr.md` R-116 and R-117; and in the product, `application/tracker.py` whole,
  `domain/tasks.py:94-112, 189-230`, `web/routes.py:168-173, 438`, and
  `tests/integration/test_task_tracker.py:311-322`. The code was read at `main` `33ad1a2a7`.
  `git diff --stat 8315df674 HEAD -- products/tracker17 ':!products/tracker17/docs'` lists only
  `products/tracker17/README.md`, so the code the SDD round verified has not moved. No suite was run.
  The item is about what the records say, and this round changes no code.

The companion held one open item, § 3.1, and the invocation listed none, so this run worked it. The
item cites an occurrence, `application/tracker.py:L105-L114`. It asks for a statement found false to
be corrected, not for the records to state a case they do not state. So § *A widening item waits
until it occurs* does not send it back.

## Items worked

### 3.1 — QC-21 and ADR-0001 say every action saves; an edit that changes no field saves nothing

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** The item hands over a concrete change: qualify QC-21's save-before-current sequence to
  an action whose `domain` outcome reports a change, give `application` no comparison rule of its
  own, and record the qualification beside QC-21 instead of editing ADR-0001. That is a lean, so I
  weighed it as a draft. The draft holds, and I took it. I added three things: the bound on what the
  report compares, an enforcement surface for the new half, and how the Accepted ADR is handled.

  *Seat (check 1).* The edit lands in `nfdr.md` QC-21 and, if anywhere, in `adr/`. Both are this
  companion's documents and the Principal Architect's. The answer binds only the records' agreement
  with the SDD and the product. It commits no person, outside party, money or risk, and I can name no
  ground I cannot see. So it is mine, in the owner's seat. The item has two parts, the QC-21 wording
  and the ADR-0001 handling. Both have the same seat, so the item stays whole, with both parts
  answered in one slot.

  *The draft holds (check 2).* I checked every citation on disk. `nfdr.md:167-168` reads "Each
  action is one call: apply a `domain` rule, save, then make the new state current." `adr/0001-…:26-28`
  reads "Each applies a `domain` rule to the current state, saves the result, and only then makes it
  current." `application/tracker.py:111-113` saves only `if outcome.changed`. `domain/tasks.py:215`
  returns `state, TaskEditOutcome(task=current, changed=False)` when no field differs. The test
  `test_tracker_unchanged_edit_never_saves` asserts `saver.saved == []`. The draft also keeps QC-21's
  no-rule half true, because the decision is `domain`'s `_changed_value` (`tasks.py:189-190`) and
  `application` only reads a field of the outcome. The item's own claim of harm also holds. As
  written, QC-21's review at `development-design` would read the product's intended behaviour as a
  breach.

  *Addition one, the bound.* "Reports a change" alone invites a later reader to make `application`
  compare states, which is a rule QC-21 forbids it. So the qualification says what the report
  compares: the submitted value with the value the page showed (SDD § 4 RT-7), never the new state
  with the current one. `TaskEditOutcome`'s docstring says `changed` is "true even when the submitted
  value is what the task already holds" (`tasks.py:107-108`). These are the words SDD v9's § 3 row now
  carries (`SDD.md:202`). QC-21 traces to that row, so QC-21 should match it, not paraphrase it.

  *Addition two, enforcement.* QC-21's *verified by:* names layer 6 and a design review, and neither
  of them fails when an unchanged edit saves. The test above does, so it should be named in the
  entry's tail. The entry's trace should also name SDD § 3's `application` row at its cycle-6 fold
  (`trail/sdd/cycle-6.md` § 5.1). The NFDR's *Inputs read:* says "SDD Settled (version 8)" (`nfdr.md:5`).
  The SDD is now version 9 (`SDD.md:5`), and this round's fold should move that line.

  *Addition three, ADR-0001.* ADR-0001 gets no superseding record and no edit. The record is
  Accepted, and `product-architecture` changes only its Status line, and only to record a
  supersession. The previous round of this companion rested on the same rule
  (`trail/architecture/self_answer-12.md`, § 3.1). A superseding record would also fail the
  significance test. The decision is five parts behind server-rendered pages, with one direction of
  dependence. No part, edge or trade-off of it moves. The save sequence has its own record,
  ADR-0004, whose Decision says "on every change" (`adr/0004-…:18`) and stays true. So the
  qualification goes in an NFDR Review Note: ADR-0001's `application` bullet is the 2026-10-06
  statement, and QC-21, which ADR-0001 lists under *Binds*, is the current one. I came close to
  recommending a superseding record, because a reader of ADR-0001 alone still meets the unqualified
  sentence. Two things would have tipped me: the sequence being what the decision chose, or a part or
  edge moving. Neither is true.

  *Nothing settled moves (check 3).* QC-49 still holds, because an action that reports no change
  reports nothing done. `web/routes.py:438` adds `saved` to the address only on `outcome.changed`,
  which matches FDR R-116 ("changes nothing and is not refused"). QC-53 says the lock is "held from
  the start of a request's check until its result is saved". `web/routes.py:171-173` holds it for
  the whole request, so on a no-save action that sentence is a minimum the code meets, and it is not
  false. QC-54's "the saver received only saves" is untouched. The answer agrees with SDD v9 § 3 and
  RN-45, which already decided the same qualification upstream. This run gave no earlier answer that
  bears on it, since there was one item.

  *Failure paths (check 4).* **Empty:** a submission with no shown values reports no change
  (`test_task_tracker.py:318`). That is `domain`'s rule, and QC-21 should not restate it. **Absent:**
  the task is gone, and `TaskNotFound` is raised before any outcome, so nothing is saved.
  **Stale:** an unchanged field on a stale page is not written. A field changed to the value another
  tab already saved reports a change and saves a state equal to the current one. That is one whole
  write under QC-50, and nothing is lost. **Concurrent:** QC-53 applies one action at a time, so no
  second actor arrives between the report and the save. **Refused:** every refusal comes from
  `domain` before an outcome exists, and nothing is saved (FDR R-117). **Failed save:** this can
  arise only on the changed path, where QC-49 stands as written.

  *What I considered raising and did not.* The stale *Inputs read:* line is a false fact in
  `nfdr.md`. This item's fold already carries it, so it is named in addition two rather than raised
  as a second item.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
