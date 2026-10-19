# Change request — 2026-10-11_pytest-10051

**Request:** Fix the issue below in the product, the repository that the project card's
`Product path:` names (`pytest-dev/pytest`). The repository stands at the commit before the issue was
fixed. Make the change the issue asks for, with tests of your own that show it, and leave the rest of
the product's behaviour as it is.

It is done when it is sealed. Nothing else is
asked of it: no record, no grade and no benchmark file. Bookkeeping is done outside
KensaiApp.

## The issue

*Not reproduced in this example.* The run was given the issue's title and body verbatim, as the benchmark SWE-bench Verified publishes them. That text is its author's, and the benchmark declares no licence for it, so this example links the issue and summarises it instead.

**The issue:** https://github.com/pytest-dev/pytest/issues/9877

**In short:** In pytest, `caplog.get_records()` stops following `caplog.records` once `caplog.clear()` is called: `clear()` replaces the records list rather than emptying it, so `get_records()` keeps the old list, neither cleared nor receiving new records.

## What must not be done

- **Do not look for the fix.** Work from this request and the repository you are given. Do not read
  the repository's history after this commit, its pull requests, its issue tracker, its later
  releases, or any copy of the SWE-bench benchmark
  (`system/projects/swe-benchmark-poc/doctrine/ai_responsibility.md` § 1.1). A patch made with any of
  them in view is not graded.
- **Do not delete anything outside the change** (same file, § 1.2).
- **Do not fix the product's other failing tests.** None fail before any change (============================== 15 passed in 0.27s ==============================, at `base_commit`). The card's `Test command:` passes only when none fails.

**Category:** bug
**Behaviour:** changing
**Classified because:** the issue reports behaviour the product gets wrong. Correcting it changes what
the product does, so Behaviour is `changing`, and the cause is a defect in existing behaviour, so
Category is `bug` (`<CORE>/doctrine/flow/change_classification.md`, the two axes). Where the issue
asks for a capability the product lacks rather than a defect, the specs step reclassifies it.

**Sealed:** 2026-10-11 — accepted; merged to `main` via `--no-ff`.
