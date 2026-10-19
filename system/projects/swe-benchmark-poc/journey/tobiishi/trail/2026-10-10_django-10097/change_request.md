# Change request — 2026-10-10_django-10097

**Request:** Fix the issue below in the product, the Django repository that the project card's
`Product path:` names. The repository stands at the commit before the issue was fixed. Make the change
the issue asks for, with tests of your own that show it, and leave the rest of Django's behaviour as
it is.

This is the second attempt. The first halted at
the developer step, `red-suite`, because the test command it was given was already red before any
change; the command now knows those failures, and this request is otherwise unchanged. The change is done when it is sealed. Nothing
else is asked of it: no record, no grade and no benchmark file. Bookkeeping is done
outside KensaiApp.

## The issue

*Not reproduced in this example.* The run was given the issue's title and body verbatim, as the benchmark SWE-bench Verified publishes them. That text is its author's, and the benchmark declares no licence for it, so this example links the issue and summarises it instead.

**The issue:** https://code.djangoproject.com/ticket/29528

**In short:** Django's `URLValidator` accepts URLs whose username or password holds a `:`, `@` or `/` that is not %-encoded, though RFC 1738 requires those characters to be encoded there. So some invalid URLs, such as `http://foo/bar@example.com`, pass validation. The issue asks the validator to reject them.

## What must not be done

- **Do not look for the fix.** Work from this request and the repository you are given. Do not read
  Django's history after this commit, its pull requests, its issue tracker, its later releases, or any
  copy of the SWE-bench benchmark (`system/projects/swe-benchmark-poc/doctrine/ai_responsibility.md`
  § 1.1). A patch made with any of them in view is not graded.
- **Do not delete anything outside the change** (same file, § 1.2).
- **Do not fix Django's other failing tests.** Two tests fail before any change, in the environment
  the card's `Test command:` runs: `validators.tests.TestSimpleValidators.test_URLValidator_raises_error_156`
  and `test_URLValidator_raises_error_157` (365 run, 2 failed, at `base_commit`, 2026-10-10). Leave them
  failing. Only the behaviour the issue names is this change's. The card's `Test command:` knows these
  two: it passes while they are the only failures, and fails on any other.

**Category:** bug
**Behaviour:** changing
**Classified because:** the issue says URLValidator accepts URLs it should reject. Making it reject them
changes what it does, so Behaviour is `changing`, and the cause is a defect in existing behaviour, so
Category is `bug` (`<CORE>/doctrine/flow/change_classification.md`, the two axes).

**Sealed:** 2026-10-10 — accepted; merged to `main` via `--no-ff`.
