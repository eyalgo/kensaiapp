# Code integrity report — 2026-10-11_requests-1142

Integrity: pass

**Change:** a GET or HEAD request with no body is sent without a Content-Length header (psf__requests-1142).
**Reviewed by:** Senior Engineer, development-code-integrity, workflow mode, 2026-10-11.
**Product:** in its own repo. Code and tests are committed in the product worktree
`<the issue's clone>/.worktrees/2026-10-11_requests-1142`.
This report is committed in the instance worktree.

---

## Deferrals

**None.** The closing marker is `a035434` (`developer: 2026-10-11_requests-1142 — implementation complete`),
the newest and only one on the branch. It carries no `Deferred:` line and no `Failing:` line, and it
says "Every deferred or halted task: none". There was nothing to check.

## What was reviewed

The product diff from `base_commit` `22623bd` to the developer's last commit `f355892`:

- `requests/models.py`: `PreparedRequest.prepare_content_length`, 8 added lines (the CP-9 predicate
  and the delete-until-absent loop).
- `test_requests.py`: the `RecordingAdapter` fake, `_NoOpRaw`, `recording_session`, the
  `assertNoContentLength` helper, and 14 tests in `RequestsTestCase`.
- Read alongside, to judge the predicate: `Request.prepare` (the preparer order, `models.py:216-229`),
  `prepare_body`, `prepare_auth`, and `Session.resolve_redirects` (`sessions.py:85-135`).

## The intent it was checked against

- `tl_instruction.md`: Task 1 and Task 2, their `#### Behaviours to verify`, the *Held by review*
  items, and the TL Review Notes.
- `change_spec.md`: CP-9 to CP-15, the Examples table, the Out of Scope list and Locked Answers Gaps 1 to 5.
- `change_design.md`: §4's hint, the §5 rows, and the Architect Review Notes (including the redirect drift note).
- `change_request.md`: the issue text and the 21 baseline failures.
- `docs/fdr.md`: absent. This product's card reads `Definition: none`, so that is the normal case.

Every Example row in the spec was walked against the suite. Each CP-9 to CP-13 row has a test that
asserts it. CP-14 and CP-15 hold at the gate (below).

## Tests added or fixed

No existing test was wrong. Two additions, both in the commit `67dbb94` (`— tests`):

1. **`test_head_without_body_has_no_content_length`**: this test now also prepares `Request('head', u)`
   and asserts method `HEAD` and no Content-Length. *Why:* `tl_instruction.md`, TL Review Notes,
   third bullet, says Task 1 adds "a lower-case `'get'` and `'head'` method through
   `Request(...).prepare()`". The suite covered `'get'` only. The case fails on the unchanged tree,
   like the rest of the CP-9 tests (checked in a disposable copy).
2. **`test_bodiless_get_and_head_gain_no_transfer_encoding`** (new). It asserts that no
   `Transfer-Encoding` is present on a bodiless Session `get`, `head` and `get` with tuple auth, on
   `Request('GET', u).prepare()`, or on either request of a `POST data='hello'` → `302` → `GET`
   redirect. *Why:* CP-13 says "Nothing about `Transfer-Encoding` changes", and no test proved that
   sentence. The design's §5 says row 11 covers it, but row 11 asserts Content-Length only, and on
   the stream branch, where the change does not act. *Evidence that it means something:* it passes
   on the unchanged tree, because it fences today's behaviour. In a disposable copy, a mutant that
   sets `Transfer-Encoding: chunked` in place of the dropped header left all 14 earlier tests green.
   This test caught it.

## The finding

**No bug.** The code does what its intent says. Every new test was green on first run against the
change's code, so there is no red commit and no green fix.

What was verified directly, not assumed:

- **Gate (CP-14, CP-15):** `/home/kensai/issue-test.sh` from the product root gives
  `21 failed, 20 passed`, then `issue-test: only baseline failures remain (21 known at base_commit)`,
  exit 0. The 20 passes are the 5 original tests, the developer's 14 and the 1 added here.
- **Preparer order:** `prepare_method` (line 220) runs before `prepare_body` (224) and
  `prepare_auth` (227). So the predicate sees the upper-cased method, and `'get'`/`'head'` count.
- **Held by review, probed:** a hand-built `PreparedRequest` with `method None` still gets
  `Content-Length: '0'` and does not raise. A generator `data` still gets `Content-Length: 'None'`.
  Both keep today's behaviour, as Task 1's *Held by review* requires. Neither is pinned by a test, on purpose.
- **The developer's mutation claims** (`not body` for `body is None`, the predicate widened, HEAD
  dropped, a single delete) are consistent with the suite as read: each named test asserts exactly
  the case that mutant breaks.

**One code change, no behaviour change:** the commit `11017e3` (`— conventions`) requotes the
strings on the lines this change added from single to double quotes, in both files. The reason is
the language resolution below, and it is recorded under *Calls made*. All 40 cases gave the same
result by name before and after the requote, and `compileall -q` exits 0.

**Domain (the instance overlay):** none of the site rules apply. The product is the requests
library in a local clone that is never pushed. The change stores nothing on a device, embeds and
collects nothing, and publishes no text. No test reaches LinkedIn or opens any connection: the
`RecordingAdapter` answers every request in process. Merging this change is not a publication.

**Carried, not mine to reconcile:** the Architect Review Notes flag that the spec's redirect
Verified Claim names the wrong mechanism. That is the **Product Owner's** document. The tests cover
both the default-`'0'` path and the caller-supplied path, so the rule is proved under either reading.

## Calls made

1. **Does the Python packet's double-quote convention bind on an upstream third-party repository?**
   - *Readings:* (a) yes: the skill says a packet's answer binds over the surrounding file's own
     style, and the packet resolved through this project's card (`Languages: Python`, chain step 1);
     (b) no: `conventions.md` measured the house's own Python, and a benchmark patch reads better in
     its file's single-quote style. The developer took (b) and recorded it as a divergence.
   - *Taken:* (a). The rule in `development-code-integrity` § Step 2, *Language packets*, is explicit
     ("the packet wins, the code changes"), and its history note says the owner made it binding on
     purpose. No product decision file outranks it: the product has no ADR, NFDR or FDR.
   - *Whose:* the owner's, as keeper of `core/doctrine/engineering/languages/python/conventions.md`
     and of the skill.
   - *If reversed:* revert `11017e3`. It changes only quote characters, and the suite gives the
     same result either way.
2. **Where does a behaviour-preserving convention fix go, given the skill's commit table has no row for it?**
   - *Readings:* fold it into the clean-pass tests commit, or give it its own commit ahead of the tests.
   - *Taken:* its own commit, `11017e3` (`— conventions`), run under the same discipline as a Step 0
     placement move: the suite was run by name before and after, with identical results. The
     tests commit after it then shows only tests, which keeps the log legible.
   - *Whose:* the owner, as keeper of `development-code-integrity` § *Commit*.
   - *If reversed:* the two commits squash into one. Nothing else changes.
3. **Lower-case `'head'`: the Behaviours list names only `'get'`, but the TL Review Notes name both.**
   - *Taken:* the TL Review Notes are the plan's own statement of what Task 1 adds, so `'head'` is
     part of Task 1's intent. Added (test 1 above).
   - *Whose:* the **Tech Lead** (`tl_instruction.md`).
   - *If reversed:* drop the two added lines. The code is unaffected.
4. **Is CP-13's "Nothing about `Transfer-Encoding` changes" already covered by design row 11?**
   - *Taken:* not covered. Row 11 asserts Content-Length on bodies that go through the stream
     branch, so it cannot fail when the CP-9 branch adds an encoding. Added (test 2 above).
   - *Whose:* the **Architect** (`change_design.md` §5, "Rule-implied edges").
   - *If reversed:* the test is a fence of today's behaviour and can be removed without touching code.

## Placement

**No parts table.** The product has no `docs/SDD.md`, so there is nothing to place against. Step 0
did not run, and no `— placement` commit exists. For the record, the new logic sits where
`change_design.md` §2 puts it: the predicate is in `PreparedRequest.prepare_content_length`, and the
test fake is in `test_requests.py`.

## Language resolution

- **Language:** Python, answered at chain step 1 by `project.md` `Languages: Python`.
- **Packet:** `core/doctrine/engineering/languages/python/README.md`, all six concerns. Toolchain is
  `toolchain.md`, Layout `layout.md`, Quality gates `quality_gates.md`, Conventions `conventions.md`,
  Errors and logging `errors_logging.md`, and Testing `core/doctrine/engineering/testing_python.md`.
- **Applied as the bar:**
  - *Quality gates.* Compile: `python -m compileall -q requests/models.py test_requests.py` with
    the card's interpreter exits 0. Its one `SyntaxWarning`, at `models.py:568`, is in code this
    change did not write. Suite: the card's Test command exits 0 against the baseline.
  - *Conventions, followed:* lines stay within 100 columns (none added go past it), snake_case
    names, no annotations on test functions, and no new dependency (`tempfile` is in the standard library).
  - *Conventions, enforced here:* double-quoted strings. The change's lines did not follow it. They
    were fixed in `11017e3`, and they now read differently from the single-quoted strings the
    upstream file already had (Calls made, 1).
  - *Conventions, bearing on nothing:* `from __future__ import annotations` (this change writes no
    annotation) and `__version__` (no module was created).
  - *Errors and logging:* bears on nothing. The change has no exception handling and no logging.
- **Divergences accepted, each forced by the product or the card:**
  - *Test location.* `testing_python.md`'s `tests/test_<domain>.py` gives way to the root
    `test_requests.py`, because the card's Test command runs only that file and `change_design.md`
    §5 fixes the location.
  - *The test seam.* A hand-written recording fake is handed in through `Session.mount`, the seam
    `Session` exposes, rather than a constructor argument. Nothing is monkeypatched, which is the
    point of the rule.
  - *Interpreter.* The interpreter is the card's (`/home/kensai/issue-venv/bin/python`, 3.9), not
    a bare `python3`.
