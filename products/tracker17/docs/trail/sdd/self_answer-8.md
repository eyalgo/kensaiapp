# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-12
- **Sources re-read:** None — no answer this run gave rests on a source outside this repository.
  Read in-repo besides `SDD.md` whole and the companion: `application/tracker.py` whole;
  `domain/tasks.py:85-120, 185-235`; `web/routes.py:405-445`;
  `tests/integration/test_task_tracker.py:305-335`; `tests/unit/test_tasks.py` (the `changed is
  False` cases, lines 428-490); `application/contracts.py:1-20`; `SRS.md` FR-9, FR-12, FR-16,
  FR-18, NFR-3, NFR-8; `UXD.md` UX-I4, UX-S6; `fdr.md` R-65, R-116, R-117, R-48, RN-12; `nfdr.md`
  QC-21; `architecture_open_issues.md` whole; the station record
  `system/projects/tracker17/journey/shukuba/trail/2026-10-11_edit-task-fields.md` and the unit's
  review `journey/nemawashi/2026-10-07_tasks-in-a-project/2026-10-11_edit-task-fields_report.md`;
  `trail/sdd/self_answer-7.md` and `trail/sdd/cycle-5.md`, the previous round. No suite was run: the
  item is about what the code says, which was read on disk at `main` `8315df674`, and the round
  changes no code.

The companion held one open item, § 5.1, `Seat: cto`, and the invocation listed none, so this run
worked it. It cites an occurrence, `application/tracker.py:L105-L114` on `main`, and asks for a
statement found false to be corrected, not for the document to state a case it does not state, so
§ *A widening item waits until it occurs* does not send it back.

## Items worked

### 5.1 — § 3's `application` row says every action saves; an edit that changes no field saves nothing

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** confirmed with addition
- **Why:** The item hands a concrete change ("qualify the save-then-publish sequence as applying to
  an action whose `domain` outcome reports a change, and say that an action reporting none returns
  the current state without saving or publishing"), so I treated that sentence as the draft, as the
  prompt says to do with a lean in a bucket that nominally carries none, and weighed it rather than
  answering from scratch. The draft holds and is taken; two things are added. One question, one
  seat; it did not split.

  *Seat (check 1).* The edit lands in § 3's `application` row, a CTO row in § *Who decides what*.
  The answer binds this document's consistency with the product and nothing outside it — no person,
  no party, no risk the owner carries — and I can name no ground I cannot see. Mine, in the owner's
  seat. The same sentence in NFDR QC-21 and ADR-0001 is the Principal Architect's and already
  carries its own item, `architecture_open_issues.md` § 3.1 (commit `cc3956f5a`), still at its
  placeholder; my finding is the same qualification, so I neither appended a near-duplicate nor
  revised it.

  *The draft holds (check 2), and the answer.* Every citation in the item is as stated: the row is
  `SDD.md:201` and reads "Each action is one call: it applies a `domain` rule to the current state,
  saves the new state, and only then makes it current"; `application/tracker.py:105-114` reads `if
  outcome.changed: self._save_then_publish(new_state)` and its docstring says "one that reports none
  saves and publishes nothing"; `domain/tasks.py:214-215` returns `state, TaskEditOutcome(task=current,
  changed=False)` when no field differs; `tests/integration/test_task_tracker.py:311-322` asserts
  `saver.saved == []` on that path. The draft's own reason also holds: the decision is `domain`'s
  (`_changed_value`, `tasks.py:189-193`), `application` reads a field of the outcome, so the row's
  *Must not own* — "Any rule of its own: it never decides whether a change is allowed" — stays true.
  I put the answer in the SDD's words ("makes it current", "the current state stays as it was")
  rather than the code's "publishes", because the row never used that word and the fold should not
  import it. **Addition one** is a bound the draft did not state and a reader would get wrong from
  "reports a change" alone: the report is a comparison of submitted against shown (§ 4 RT-7), not of
  the new state against the current one. `TaskEditOutcome`'s own docstring says `changed` "is true
  even when the submitted value is what the task already holds" (`tasks.py:107-108`). So the stale
  case where the operator changes a field to exactly what another tab already saved does save, and
  saves a state equal to the current one. Naming it keeps a later reader from "fixing" the row with a
  state comparison that would hand `application` a rule. **Addition two** says what does not move,
  because the item's heading, "every action saves", invites a reader to look for the sentence
  elsewhere: § 4 SD-2 and SRS FR-9 bind the done report to the disk, and an action reporting no
  change reports nothing done — `web/routes.py:438` adds `"saved"` to the address only when
  `outcome.changed`, which is FDR R-116 and UXD UX-I4 ("A result is shown only once it is saved: no
  page shows an action as done before that"); § 9 TO-3 already says "on every change"; NFR-3's
  "for that field" is exactly an unchanged field not being written. The answer also places the two
  neighbouring cases so the qualified row is read as general and not as edit-only: a move to the
  status a task already has is a refusal under SRS FR-18, not a no-change outcome, and FDR R-65's
  label already carried will be the second action to report none, which the row covers without
  enumerating actions — which actions can report none is `domain`'s per action, and the row says the
  mechanism only.

  *Nothing settled moves (check 3).* No requirement changes: FR-9, NFR-3, NFR-8 and FR-39 are each
  checked above and hold. No § 4 condition changes; SD-2 is not false on an unchanged edit, because
  nothing is reported done. UX-I4 and UX-S6 ("After an action, UX-I4's confirmation") are consistent
  with no line on a save that saved nothing, on UX-I4's own sentence. The FDR already states the
  behaviour (R-116, an owner directive per its RN-12), so the product's no-line page has an owner.
  No earlier answer of this run bears on it; there was one item. The `tasks-in-a-project` slice's
  *Reached when* and § 7's edges do not move: this is a correction of a part's description, the kind
  RN-34 and RN-41 record, not a re-cut under § 10.

  *Failure paths (check 4).* *Empty*: a submission with no shown values at all is unchanged by
  `_changed_value`'s rule (`tests/integration/test_task_tracker.py:318`, `TaskFields()` as shown) —
  `domain`'s rule, which the row does not restate. *Absent*: the task is gone — `TaskNotFound` is
  raised before any outcome, and `web` reopens the page (`routes.py:426-427`); no save. *Stale*: the
  two halves are in the answer — an unchanged field from a stale page is not written, and a field
  changed to the other tab's value is. *Concurrent*: § 4 RT-6 applies one request at a time, so no
  second actor arrives between the report and the save. *Refused*: every refusal is raised by
  `domain` before an outcome exists, and no save happens (FDR R-117). *Failed*: an unchanged edit
  makes no save, so SD-2's failure branch cannot arise on it; on a changed edit it stands as written.
  I was close to leaving "publishes" in the answer as the code's word for making the state current,
  and did not: the row is the SDD's and the fold should carry the SDD's vocabulary.

  *What I considered raising and did not.* The UXD says nothing about a save that changed nothing
  (`grep -n -i "unchanged\|no change\|nothing changed" UXD.md` printed nothing on 2026-10-12). That
  is an omission, not a false fact, not an upstream move and not a contradiction — UX-I4's sentence
  already covers it — and the FDR states the behaviour, so it does not meet the bar for a cycle.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
