# Architecture open issues — tracker17

> Companion to `adr/` and `nfdr.md`. The Principal Architect authored both records
> non-interactively; this file holds what the run could not settle from its inputs — the SRS, the SDD
> and the FDR.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-architecture`. It folds your answers into the records and drops the resolved items.
> When nothing is left open, `product-architecture` **deletes this file**: no file = the records are
> done.
>
> Your answers are never thrown away. Each time the Principal Architect folds them in, it first copies
> this file whole to `docs/trail/architecture/` — so what you decided, and why, stays readable and
> citable for good.
>
> **§ 3 is raised, not asked.** These records bind every later change, so the seats that live under
> them find gaps the authoring run could not. § 3 is where such a seat says so, against both records
> — an ADR's binding and an NFDR obligation reach the same file.

> **No producing run wrote this file.** The PM opened it on 2026-10-12, in a route review, to carry
> items § 3.1 and § 3.2. `product-architecture` has no record of writing it.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-21 says every action's report compares with the value the page showed; setting the operator name compares with the saved name
- **Raised by:** PM — 2026-10-12
- **Which record:** NFDR § 1.3, QC-21 (`nfdr.md:L167-L180`)
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`
- **What it blocks:** nothing is blocked. QC-21 states as true of every action a comparison one
  action does not make, so its no-rule review at `development-design` would read the operator name's
  comparison as a breach.
- **Where it shows:** `nfdr.md:L171-L173` — "The report is `domain`'s comparison of the value
  submitted with the value the page showed (SDD § 4 RT-7), never of the new state with the current
  one, so `application` compares nothing." In the product, `domain/operator_name.py:L59-L62` compares
  the submitted name with the name saved when the action runs, and
  `tests/integration/test_people_routes.py:L520-L533` asserts the People form carries no shown-name
  value. The change asked: keep the task edit's rule, qualify other actions by their own `domain`
  comparison (the operator name: the saved name at the moment of the action), and keep
  `application`'s no-comparison rule. The same sentence is in SDD § 3, raised on
  `SDD_open_issues.md` § 5.1.
- **If a document has to be written:** none. `nfdr.md` changes through `product-architecture`.
- **Answer:** confirm the change, with additions. Rewrite QC-21's report sentence to follow SDD version 10's § 3 `application` row. What an action's outcome compares is `domain`'s, decided per action. The task edit compares each submitted value with the value the page showed (SDD § 4 RT-7). Setting the operator name, and adding a label, compare with what the state holds at the moment of the action (SRS NFR-3). `application` compares nothing in either case. The item named the operator name only; the label is added because `domain/tasks.py` `add_task_label` makes the same comparison and SDD version 10 names it. Write the rule per action rather than as a list, so it stays true when another action starts reporting. Add two tests to the `verified by:` tail, one for each action that compares with the state at the moment of the action: `tests/integration/test_people_routes.py::test_stale_people_name_submission_compares_with_current_name` and `tests/unit/test_tasks.py::test_duplicate_task_label_reports_no_change`. Trace to SDD § 3 v10, `trail/sdd/cycle-7.md` § 5.1 and SRS NFR-3. *Inputs read* moves to SDD version 10. ADR-0001 is not edited. Reasoning: `products/tracker17/docs/trail/architecture/self_answer-14.md` § 3.1.

### 3.2 QC-47 and RN-28 say the cross-role contract runs checks in a `git archive` copy; it now requires a fresh clone
- **Raised by:** PM — 2026-10-12
- **Which record:** NFDR § 4, QC-47 (`nfdr.md:L392-L400`), and NFDR Review Notes, RN-28
  (`nfdr.md:L904-L912`)
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`
- **What it blocks:** nothing is blocked. Both lines describe the copy a run outside the change's
  worktree uses as "a disposable copy unpacked from `git archive`", and explain the one failure such a
  copy gives. The contract they cite no longer sends a run there.
- **Where it shows:** `nfdr.md:L396-L397` and `L908`, against `core/roles/CROSS_ROLE.md:L14-L19`
  (§ *Every seat*): "a fresh clone of the repository that holds it, checked out at the commit under
  test … A clone, not `git archive`: an archive drops the git history". Measured on 2026-10-12 at
  `2866e76de`: `pytest products/tracker17/tests/` in a `git archive` copy gave 1 failed
  (`test_data_is_ignored_by_version_control`, `fatal: not a git repository`), 936 passed; in a fresh
  clone at the same commit, 937 passed. The change asked: name the disposable clone at the tested
  commit, keep the Git-repository prerequisite, and keep the check failing rather than skipping.
- **If a document has to be written:** none. `nfdr.md` changes through `product-architecture`.
- **Answer:** confirm the change, with one addition. In QC-47 and RN-28, name the copy `core/roles/CROSS_ROLE.md` § *Every seat* now requires: a fresh clone at the commit under test. That copy is a Git repository, so the check runs and passes there. Keep the prerequisite (a Git repository with `git` on the path), and keep the check failing rather than skipping. The addition is RN-28's *because*. Its case was "a cold reader running the suite where the contract sends a run meets that one failure", and that case is gone. The sentence is still needed for a copy that is not a repository, such as one unpacked from a download (the README's case) or from `git archive`. Name that copy instead of the contract's. The obligation does not move, and § 10's QC-47 row, SDD RN-39 and SDD § 6 `first-project` all stand. Reasoning: `products/tracker17/docs/trail/architecture/self_answer-14.md` § 3.2.
