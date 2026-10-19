# Tech Lead instruction — django-10097: URLValidator rejects unencoded ":", "@" and "/" in the username and password

**Product root:** <the issue's clone>/.worktrees/2026-10-10_django-10097 — every path below is relative to it.
**Scope:** narrow the user-information part of `URLValidator.regex` in `django/core/validators.py`, and bring `tests/validators/` into line. Nothing else in Django changes.

---

## Project layout

```
<product-root>/
  django/core/validators.py            ← modified (URLValidator.regex, user-information part only)
  tests/validators/
    valid_urls.txt                     ← modified (line 51 in place; lines appended)
    invalid_urls.txt                   ← modified (lines appended)
    tests.py                           ← modified (invalid_urls.txt loader; one new method on TestSimpleValidators)
```

No file or directory is created. No parts table — placement follows change_design.md §2.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **One task, not several:** design §3 is omitted (one module, one pattern). The pattern and the test data are one task, not a code task and a tests task. A tests-only task would leave the suite red with no green point of its own, and the design's ordering edge (§5) joins `valid_urls.txt` line 51 to the pattern change. The task states the edge as a property below.
- **Baseline checked, not copied:** the card's `Test command:` was run once in this change's product worktree. It ran 365 tests, failed two, printed `only baseline failures remain (2 known at base_commit)` and left the tree clean. It runs `tests/validators`, so every test this task adds is one the gate runs. The gate in the task is the card's command as it stands.
- **Hint carried unchanged:** design §4's hint is an approach (one character class, the shape of the user information, no Python check beside the pattern). It is carried as written. It contains no pattern text, so nothing was cut.
- **Behaviour held by review, not by a test:** the design deliberately leaves `http://[user@example.com` raising `ValueError` (CP-4, "leave the rest"). A test of it would fix a defect as the expected verdict, so the task carries it under `Held by review`.
- **No edge case added:** every Example in the spec has a row in design §5's coverage map, and the empty-user-information cases and the whitespace fence are already in it. Nothing was removed.

## Corrections owed while there

- Owed outside this change's reach: `django/core/validators.py` line 136, `URLValidator.__call__` — `urlsplit` on the IPv6 re-check has no `ValueError` guard, so `URLValidator()('http://[user@example.com')` raises `ValueError: Invalid IPv6 URL` instead of `ValidationError`; the design surfaced it and did not take it in (design § Architect Review Notes). Not a record this change makes false; it is a defect found while walking, and widening CP-5 to cover it is the owner's call through the spec.

No record is made false by this change (`change_design.md` § *Records this change makes false* reads None), so no other entry is owed.

---

### Task 1: URLValidator user information and its test data (`django/core/validators.py`, `tests/validators/valid_urls.txt`, `tests/validators/invalid_urls.txt`, `tests/validators/tests.py`)

**Dependencies:** None

**What to build:** `URLValidator.regex` rejects an unencoded ":", "@" or "/" in the username or password, and no longer lets a "?", "#" or "/" end up inside user information, while percent-encoded forms and every other verdict stay as they are. The tests are the two fixture files, the `invalid_urls.txt` loader and one method in `tests/validators/`.

**Imports and storage this task may bring in:** none. It adds no module, no third-party origin and no device storage.

**Property to keep (CP-8):** `TEST_DATA[156]` and `TEST_DATA[157]` stay `(URLValidator(), 'http://www.djangoproject.com/\n', ValidationError)` and `(URLValidator(), 'http://[::ffff:192.9.5.5]\n', ValidationError)`. Nothing is inserted into the inline `TEST_DATA` list at or before them. Everything the task adds to the test data goes after the inline list: the two fixture files and the loader are read after it.

**Property to keep (ordering edge):** `valid_urls.txt` line 51 never asserts acceptance of `http://-.~_!$&'()*+,;=:%40:80%2f::::::@example.com` while the changed pattern is in the tree.

#### Behaviours to verify (developer adds the data and method listed here, in `tests/validators/`)

Data edits:

- `valid_urls.txt` line 51 is modified in place to `http://-.~_!$&'()*+,;=:%40%3A80%2f%3A%3A%3A%3A%3A%3A@example.com`. It is accepted before and after the change (CP-2/CP-3).
- `invalid_urls.txt` gets the old line 51 value, `http://-.~_!$&'()*+,;=:%40:80%2f::::::@example.com`, appended. It is rejected after the change (CP-2).
- `invalid_urls.txt` gets these appended, each expected rejected and each accepted on the unchanged tree (CP-7 proof):
  - `http://foo/bar@example.com` (the issue's URL, CP-1)
  - `http://foo?bar@example.com`, `http://foo#bar@example.com` (CP-1)
  - `http://foo:b:ar@example.com` (":" in the password)
  - `http://f@oo:bar@example.com` ("@" in the username)
  - `http://foo@bar@example.com`
  - `http://foo:bar@baz@example.com` ("@" in the password)
  - `http://foo:bar/baz@example.com` ("/" in the password)
  - `http://user:pa?ss@example.com` (CP-4, spec Gap 1)
  - `ftp://foo/bar@example.com` (CP-6)
- `invalid_urls.txt` gets these appended as regression fences, rejected before and after: `http://us er@example.com` (whitespace), `http://@example.com` (empty user information).
- `valid_urls.txt` gets these appended, each expected accepted and accepted before and after (fences against over-rejection):
  - `http://example.com/?m=foo@example.com`
  - `http://example.com?m=foo@example.com`
  - `http://example.com#foo@bar`
  - `http://userid:password@example.com?m=foo@example.com`
  - `http://foo%2Fbar@example.com`
  - `http://foo:b%3Aar@example.com`
  - `http://foo%40bar@example.com`
  - `http://usér:päss@example.com`
  - `http://[user]@example.com`
  - `http://:@example.com`
  - `http://:pass@example.com`
  - `http://user:@example.com`

Loader and method:

- `test_invalid_urls_with_appended_query_are_rejected` (behaviour, not a literal name) — the `invalid_urls.txt` loader in `tests/validators/tests.py` also appends `(URLValidator(), <line> + '?m=foo@example.com', ValidationError)` for each stripped line, so all lines, the ones appended above included, are tried with the suffix (CP-1). On the unchanged tree 42 of the 59 original lines' suffixed forms fail to raise `ValidationError`: 41 are accepted, and `https://test.[com?m=foo@example.com` errors with `ValueError`.
- `test_url_validator_rejection_has_code_and_message` — a new plain method on `TestSimpleValidators`, not a `TEST_DATA` entry. For each of `http://foo/bar@example.com`, `http://foo:b:ar@example.com` and `https://test.[com?m=foo@example.com`, `URLValidator()` raises `ValidationError` with `code == 'invalid'` and message `Enter a valid URL.` (CP-1, CP-2, CP-5). Its failing run on the unchanged tree is the `ValueError` for the third value and a missing raise for the first two.

Other rules this task must keep, each covered by data already in the suite or above:

- `URLValidator(EXTENDED_SCHEMES)` still accepts `git+ssh://git@github.com/example/hg-git.git` (the existing entry at `tests/validators/tests.py` line 218, unchanged and at its index) (CP-6).
- `http://userid:password@example.com:8080/` stays accepted (existing `valid_urls.txt` line 27) (CP-4).
- The "trailing junk does not take forever to reject" entries still finish (the pattern must not backtrack catastrophically).

#### Held by review

- `http://[user@example.com` keeps raising `ValueError: Invalid IPv6 URL` — covered by no test, because a test would pin a defect as the expected verdict (CP-4, design § Architect Review Notes). Held by reading the diff: `__call__` is not touched, and the character class still allows "[" and "]".
- The diff changes only the user-information part of `URLValidator.regex` and adds no check in Python beside it. Nothing in `__call__`, `schemes`, `message` or `code` changes (design §4). Held by reading the diff.
- Every string a visitor could read is absent from this change: the only text added is URL data in test files and one test method's names and asserted message, which comes from `design §5` verbatim. Any further string, such as a comment or a docstring beyond a short one, is an unapproved addition.

#### Implement

Infer from failing tests.

# Hint: build one character class for "a username or password character": not whitespace, and not ":", "@", "/", "?" or "#". The user information is then either a non-empty username, optionally followed by ":" and a possibly empty password, or a ":" followed by a possibly empty password. That form keeps the empty cases' verdicts (`http://@example.com` rejected; `http://:@example.com`, `http://:pass@example.com`, `http://user:@example.com` accepted). Change no other part of the pattern and nothing in `__call__`. A rejection needs no handler of its own: every value newly rejected is a failed match of `regex`, which takes the existing fallback path that turns `urlsplit`'s `ValueError` into `ValidationError`. Do not add a username/password check in Python beside the pattern.

#### Verification gate

Run `/home/kensai/issue-test.sh` from the product root, in this worktree and nowhere else.

Pass criteria: exit 0; the run's only failures are `test_URLValidator_raises_error_156` and `test_URLValidator_raises_error_157`, which still test the two trailing-newline values; every test listed above fails on the tree before the pattern change and passes after it, apart from the fences, which pass on both. Nothing else fails. The built behaviour is checked on the validator itself: `http://foo/bar@example.com` and `https://test.[com?m=foo@example.com` raise `ValidationError`, and `http://foo%2Fbar@example.com` and `http://example.com/?m=foo@example.com` return without raising.
