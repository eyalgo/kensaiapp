# Code integrity report — 2026-10-10_django-10097

Integrity: pass

**Date:** 2026-10-10 · **Mode:** workflow · **Seat:** Senior Engineer (`development-code-integrity`)
**Outcome:** clean pass. The code already did what its intent says, and no bug was found. I added the
tests the intent implied that the suite did not yet carry. Each is red against the base pattern and
green against the developer's. They are committed in the product repository as `b7539b2`.

---

## Deferrals

**None.** The closing marker (`226fb12`, `developer: 2026-10-10_django-10097 — implementation complete`,
the only marker on the branch) carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

The product is in its own repository: `code_worktree` =
`<the issue's clone>/.worktrees/2026-10-10_django-10097`,
diffed from `b9cf764` (base_commit) to `2996ee6` (the developer's green commit):

- `django/core/validators.py`: the one changed line, the user-information part of `URLValidator.regex`,
  which went from `(?:\S+(?::\S*)?@)?` to `(?:(?:[^\s:@/?#]+(?::[^\s:@/?#]*)?|:[^\s:@/?#]*)@)?`. I also
  read the whole of `URLValidator.__call__`, because the design's CP-5 argument rests on its fallback path.
- `tests/validators/tests.py`, `valid_urls.txt` and `invalid_urls.txt`: the developer's red commit
  `2cf0763` and green commit `2996ee6`.

## The intent it was checked against

- `tl_instruction.md`: Task 1, its *Behaviours to verify*, the two *Properties to keep* (CP-8 indices,
  the line-51 ordering edge) and *Held by review*.
- `change_spec.md`: CP-1 to CP-8, the Examples table and Locked Answers Gaps 1–6.
- `change_design.md`: §4 hint, §5 test placement and coverage map, Architect Review Notes (in particular
  *CP-5 by construction*).
- `docs/fdr.md`: absent (`Definition: none`). It is optional context, and its absence is the normal case.

## Placement (Step 0)

**No parts table.** `docs/SDD.md` does not exist under the product worktree (checked 2026-10-10; neither
do `docs/fdr.md` or `docs/nfdr.md`). Project card `Definition: none`. There was nothing to place
against, so the step did not run and no `… — placement` commit was made. For the record, the change
added no logic outside `URLValidator.regex`, which is where the faulty logic already lived.

## Language resolution

- **Python**, answered at chain step 1 (`project.md` `Languages: Python`).
- Packet opened: `languages/python/README.md` → `conventions.md`, `quality_gates.md`, and
  `testing_python.md` for Testing. I also read `toolchain.md`, `layout.md` and `errors_logging.md`
  through the developer's marker record, and checked its citations against the router. The floor still
  applies beneath the packet.
- **Quality gates.** Compile: `/home/kensai/issue-venv/bin/python -m compileall -q -f tests/validators/tests.py`
  exited 0, run with the product's interpreter, as the card names. Suite: the card's `Test command:`,
  below. No formatter or linter ran, because none is installed in the product's virtualenv (the
  packet's § *What is not installed* holds for it too).
- **Conventions.** Every line I added is within 100 columns (the longest is 97). The lines over 100 in
  `tests.py` (251–254, 269, 369) were there before the change. **Single-quoted strings, against the
  packet's double-quote rule:** a recorded call, *Calls made* 1.
- **Testing.** `testing_python.md`'s pytest layout does not apply here. The product's own runner
  (`tests/runtests.py`) and its `tests/<app>/` layout govern, the same call (*Calls made* 1). Its
  hand-written-fake rule had nothing to act on, because `URLValidator` has no collaborator to fake.

## Tests added or fixed

**None fixed.** Every existing test, the developer's included, asserts what the intent says. I checked
each against its source sentence:

- The appended invalid rows → CP-1, CP-2, CP-4 Gap 1, CP-6.
- The suffixed loader → CP-1 (the issue's own class) and CP-5.
- `test_url_validator_rejection_has_code_and_message` → CP-5's code and message.
- The valid fences → CP-1, CP-3 and CP-4.
- The modified line 51 → CP-3.

None of them would still pass with the old pattern in place, except the fences, which are meant to
pass on both trees.

**Added**, in product commit `b7539b2`:

| Test | Intent it proves | Why it was missing | Base pattern | Changed pattern |
|---|---|---|---|---|
| `test_url_validator_rejects_user_information_for_every_scheme`, a new method on `TestSimpleValidators` with 4 subtests: `ftps://foo/bar@example.com` (default validator); `git+ssh://foo/bar@…`, `git+ssh://git:pa:ss@…` and `git+ssh://git@git@…` (`URLValidator(EXTENDED_SCHEMES)`) | CP-6: CP-1 to CP-5 hold for "the default four and **any list passed as `schemes`**" | The only custom-schemes assertion was an acceptance (`tests.py`, the `git+ssh://git@github.com/…` entry). An acceptance cannot show that the rejections hold under a custom list. `ftps` was the one default scheme no row used. | all 4 red | all 4 green, code `invalid` |
| `invalid_urls.txt` + `http://foo:b:ar@例子.测试`, `http://foo@bar@例子.测试`, `http://foo/bar@例子.测试` (each also tried with the loader's `?m=foo@example.com` suffix) | CP-1/CP-2 through the IDN fallback. The design (*CP-5 by construction*) says the fallback's IDNA re-encode "cannot turn a CP-1/CP-2 rejection back into an acceptance" | Every rejected row had an ASCII host, so the re-encode was always the identity and the claim had no test. With an IDN host the netloc really is re-encoded (`xn--…`) before the second match. | 6 red (`_451`–`_456`) | 6 green |
| `valid_urls.txt` + `http://user:pass@例子.测试` | CP-4 fence: user information with an IDN host keeps today's acceptance | Pairs with the three rows above. Without it, code that rejected every IDN URL carrying user information would pass them. | green | green |
| `valid_urls.txt` + `http://foo:b%3aar@example.com` | CP-3 names `%3a` (lowercase) as accepted | Every encoded-colon row used `%3A`. | green | green |

The rows are appended to the fixture files and the method sits outside `TEST_DATA`, so
`TEST_DATA[156]` and `[157]` still hold the two trailing-newline values (CP-8).

The red/green columns were measured by running the full validators suite twice: once in a disposable
copy holding the new tests with `django/core/validators.py` reverted to `b9cf764`, and once in the
change's worktree.

## The finding

**No issues.** No bug was found, nothing was misplaced, and no test asserted the wrong thing. The code
matches its intent on every row of the spec's Examples, and on the further cases above.

- **Gate:** the card's `Test command:` (`/home/kensai/issue-test.sh`), run from the product worktree
  root, exited 0. 472 tests ran. The only failures are `test_URLValidator_raises_error_156` and `_157`
  (`issue-test: only baseline failures remain`). The worktree was clean afterwards.
- **Held by review**, which I verified by reading the code and running it:
  - The diff changes only the user-information part of `regex`. `__call__`, `schemes`, `message` and
    `code` are unchanged.
  - `http://[user@example.com` still raises `ValueError: Invalid IPv6 URL`, as the plan holds.
  - The only text added is URL data and test names. My additions add only URL data and one method name.
- **No catastrophic backtracking** (the plan's "trailing junk" rule). It is covered by the existing
  entries, which pass. I also measured adversarial inputs (`http://` + `a`×50000, `a:`×50000 + `@x`,
  `a@`×50000):
  - the changed pattern rejected all three in 0.004 s;
  - the base pattern took 20.5 s.

  The change therefore also removes the old pattern's quadratic backtracking. I added no timing test,
  because a wall-clock assertion is flaky across machines and the plan does not ask for one.
- **Already surfaced upstream, unchanged here:** the unguarded `urlsplit` on the IPv6 re-check in
  `URLValidator.__call__` (`django/core/validators.py`). Its effect is that `http://[user@example.com`
  raises `ValueError` instead of `ValidationError`. The design's Architect Review Notes and the plan's
  *Corrections owed while there* both record it. Taking it into a change is the owner's call, through
  the spec.
- **Domain overlay (this instance's doctrine):** it does not bear on this change. The change stores
  nothing, collects nothing, loads no third-party resource and publishes no text (design §1,
  *Publishes text: no*). No test reaches LinkedIn, and no fixture states a claim about KensaiApp or
  about Eyal.

## Calls made

1. **Quote style and test layout: the product's own coding-style record outranks the language packet.**
   - *Question:* the Python packet says double-quoted strings (`conventions.md` § Surface style) and
     tests beside their subject (`layout.md`). Django's
     `docs/internals/contributing/writing-code/coding-style.txt` says "Use single quotes for strings",
     and its tests live under `tests/<app>/`.
   - *Readings weighed:* (a) The packet wins, because `languages/README.md` § Precedence says a packet
     outranks "the surrounding code's own habits". (b) The product's written style guide wins, because
     the same section says "A packet never overrides the product's own records".
   - *Taken:* (b). Django's style guide is a written, standing record of the product, not a habit left
     by the last hand. The precedence chain lists ADR / NFDR / FDR by name, and Django has none of
     those. Its style guide is the record that does the same job. The developer made the same call for
     the strings it added (marker, *Language resolution*). Mine follow it.
   - *Whose to confirm:* the owner, as keeper of the packet doctrine and its precedence.
   - *If reversed:* the strings in `tests/validators/tests.py` that this change added would become
     double-quoted. No verdict and no test result would change.
2. **The CP-6 cases go in a plain method, not in `TEST_DATA` or a fixture file.**
   - *Question:* where a custom-schemes rejection belongs.
   - *Readings weighed:* (a) A new `TEST_DATA` entry at the end of the inline list, which is allowed
     because it sits after index 157. (b) A plain method, as the design used for CP-5.
   - *Taken:* (b). The fixture loaders only build `URLValidator()`, so a fixture row cannot carry a
     custom scheme list. A method moves no index at all, which keeps CP-8 true by construction.
   - *Whose to confirm:* the Architect, since design §5 owns test placement.
   - *If reversed:* the four cases would move into `TEST_DATA` with the same assertions. Coverage would
     be the same.

## Commits

- Product repository (`code_worktree`), branch `2026-10-10_django-10097`: `b7539b2` — the tests above.
- Instance repository (`pipeline_worktree`), branch `2026-10-10_django-10097`: this report, committed on
  its own.
