# Change Design — URLValidator rejects unencoded ":", "@" and "/" in the username and password

**Date:** 2026-10-10
**Category:** bug
**Behaviour:** changing
**Publishes text:** no

---

## 1. Change Summary

`django.core.validators.URLValidator` accepts user information that holds an unencoded ":", "@" or
"/". It also takes an "@" that comes after the authority as the end of a username. Both faults
come from one place: the user-information part of the class's `regex` pattern, `\S+(?::\S*)?@`.
That part matches any non-whitespace run, so the run can reach past the first "/", "?" or "#".
The change narrows that part and nothing else. The username and password become runs of characters
that exclude whitespace and the five delimiters ":", "@", "/", "?" and "#", joined by at most one
":". CP-1 to CP-3 and CP-6 then hold by construction, and CP-5 holds because of where the rejection
now happens. Every rejection the change adds is a failed match of `regex`. A failed match goes down
the validator's existing fallback path, and that path already turns a `ValueError` from `urlsplit`
into a `ValidationError` with code `invalid`. One product module changes: `django/core/validators.py`.
The tests live in `tests/validators/`. They are placed so that the two baseline failures keep their
`TEST_DATA` positions, 156 and 157 (CP-8).

**What crosses to the outside: nothing.** The change stores nothing on a visitor's device, collects
nothing, sends nothing to a third party, and publishes nothing. The patch stays in the local clone
(`project.md`, `Manages: none`), so there is no release step to keep.

---

## 2. Blast Radius

The product has no parts table: `docs/SDD.md` does not exist (`Definition: none`; this repository's
`docs/` is Django's own documentation). Placement therefore follows the code. The logic that is
wrong lives in `URLValidator.regex`, and so does its fix. No new piece of logic is added outside
that pattern.

| Module | Status | What changes |
|---|---|---|
| `django/core/validators.py` | Modified | `URLValidator.regex`: only the user-information part changes. Username and password become runs that exclude whitespace and ":", "@", "/", "?", "#", joined by at most one ":". The user information as a whole stays non-empty and optional. The scheme, host, port and resource-path parts, `__call__`, `schemes`, `message` and `code` do not change. |
| `django/forms/fields.py` (`URLField`) | Unchanged | Builds a `URLValidator()` by default and inherits the new verdicts, as the spec's Out of Scope states. Its code and its normalisation do not change. |
| `django/db/models/fields/__init__.py` (`URLField`) | Unchanged | Same as above. |
| `tests/validators/` | Modified | Test data and one test method. See §5. |

**Public surface.** `URLValidator`'s signature, attributes and exceptions keep their names and types.
Only the pattern string held in `regex` changes, and with it the verdicts the spec names. The class
still deconstructs to the same arguments, so migrations are unaffected. No other module in `django/`
reads `URLValidator.regex` (checked by `grep -rn URLValidator django/`: the two `URLField`s above
are the only importers). No other module is affected through an import.

---

## 3. Sub-jobs

Omitted: one product module is affected, and the change to it is one pattern with no internal seams.
There is one ordering edge between that pattern and the test data, and it is stated in §5.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `django/core/validators.py` — narrow the user-information part of `URLValidator.regex` | Build one character class for "a username or password character": not whitespace, and not ":", "@", "/", "?" or "#". The user information is then either a non-empty username, optionally followed by ":" and a possibly empty password, or a ":" followed by a possibly empty password. That form keeps CP-4's empty-case verdicts (`http://@example.com` rejected; `http://:@example.com`, `http://:pass@example.com`, `http://user:@example.com` accepted). Change no other part of the pattern and nothing in `__call__`. CP-5 needs no handler of its own (see Architect Review Notes, *CP-5 by construction*). Do not add a username/password check in Python code alongside the pattern. Two consequences of the hint: the class rules out ":", so the username/password boundary is fixed and the pattern does no extra backtracking; the existing "trailing junk does not take forever to reject" entries guard that. |

---

## 5. Test Additions

**A property the placement has to keep (CP-8):** `TEST_DATA[156]` and `TEST_DATA[157]` still hold
`(URLValidator(), 'http://www.djangoproject.com/\n', ValidationError)` and
`(URLValidator(), 'http://[::ffff:192.9.5.5]\n', ValidationError)`. So no entry is inserted into the
inline `TEST_DATA` list at or before those two. The two fixture files are appended after the inline
list, so a line added to or removed from either file does not move them.

**An ordering edge:** `valid_urls.txt` line 51 must stop asserting acceptance of
`http://-.~_!$&'()*+,;=:%40:80%2f::::::@example.com` no later than the pattern change lands. With
the pattern changed and that line still in place, the suite is red with no fault in the change.

| Sub-job | Test file | What to add / modify |
|---|---|---|
| `validators.py` | `tests/validators/valid_urls.txt` | **Modify line 51 in place** to the same URL with its password's colons percent-encoded: `http://-.~_!$&'()*+,;=:%40%3A80%2f%3A%3A%3A%3A%3A%3A@example.com` (CP-2/CP-3, Gap 2). |
| `validators.py` | `tests/validators/invalid_urls.txt` | **Append** the old line 51 value, `http://-.~_!$&'()*+,;=:%40:80%2f::::::@example.com` (CP-2, Gap 2). |
| `validators.py` | `tests/validators/invalid_urls.txt` | **Append**, each expected rejected: `http://foo/bar@example.com` (the issue's URL, CP-1), `http://foo?bar@example.com`, `http://foo#bar@example.com` (CP-1), `http://foo:b:ar@example.com` (":" in password), `http://f@oo:bar@example.com` ("@" in username), `http://foo@bar@example.com`, `http://foo:bar@baz@example.com` ("@" in password), `http://foo:bar/baz@example.com` ("/" in password) (CP-2), `http://user:pa?ss@example.com` (CP-4, Gap 1), `ftp://foo/bar@example.com` (CP-6). Each fails on the unchanged tree. |
| `validators.py` | `tests/validators/invalid_urls.txt` | **Append** as regression fences, each rejected today and after: `http://us er@example.com` (whitespace), `http://@example.com` (empty user information) (CP-4). |
| `validators.py` | `tests/validators/valid_urls.txt` | **Append**, each expected accepted: `http://example.com/?m=foo@example.com`, `http://example.com?m=foo@example.com`, `http://example.com#foo@bar`, `http://userid:password@example.com?m=foo@example.com` (CP-1); `http://foo%2Fbar@example.com`, `http://foo:b%3Aar@example.com`, `http://foo%40bar@example.com` (CP-3); `http://usér:päss@example.com`, `http://[user]@example.com`, `http://:@example.com`, `http://:pass@example.com`, `http://user:@example.com` (CP-4). These pass today and must keep passing. They fence against over-rejection. |
| `validators.py` | `tests/validators/tests.py` | **Extend the `invalid_urls.txt` loader** so that, besides each stripped line, it also appends `(URLValidator(), <line> + '?m=foo@example.com', ValidationError)` (CP-1, the issue's appended-query class). The loader runs after the inline list, so indices 156/157 hold. The suffixed entries cover every line, the ones appended above included. `https://test.[com` with the suffix is one of them: today it raises `ValueError` and the generated test errors (CP-5). |
| `validators.py` | `tests/validators/tests.py` | **Add one method to `TestSimpleValidators`** that asserts `URLValidator()` raises `ValidationError` with `code == 'invalid'` and message `Enter a valid URL.` for `http://foo/bar@example.com` (CP-1), `http://foo:b:ar@example.com` (CP-2) and `https://test.[com?m=foo@example.com` (CP-5). The generated `TEST_DATA` tests check only the exception type, so this method is what proves CP-5's code and message. It is a plain method, not a `TEST_DATA` entry, so no index moves. |

**Coverage map: every spec Example, and the rule-implied edges.**

- **CP-1:** the issue URL and the `?`/`#` variants are appended invalid rows. The four accepted
  CP-1 rows are appended valid rows. "Each of the 59 entries + suffix" is the loader extension.
  "Each entry of `valid_urls.txt` except line 51" is the existing loader, which runs over that file
  unchanged.
- **CP-2:** five appended invalid rows. Line 51 is the moved row.
- **CP-3:** the encoded line 51 (modified in place) and three appended valid rows.
- **CP-4:**
  - `http://userid:password@example.com:8080/` is covered by the existing `valid_urls.txt` line 27.
  - Non-ASCII, `[user]` and the three accepted empty cases are appended valid rows.
  - Whitespace and `http://@example.com` are appended invalid fences.
  - `http://user:pa?ss@example.com` is an appended invalid row.
  - The rule's other characters (`!$&'()*+,;=`, `-.~_`, `%`) are covered by the encoded line 51
    row, whose username holds all of them.
- **CP-5:** the new method, plus every suffixed loader entry.
- **CP-6:** `ftp://foo/bar@example.com` is appended. The `EXTENDED_SCHEMES` row is covered by the
  existing `tests.py` line 218 entry, which is unchanged and stays at its index.
- **CP-7:** the appended invalid rows, the suffixed loader entries and the new method each fail on
  the unchanged tree. The appended valid rows and the encoded line 51 pass on both trees and are
  fences, not CP-7's proof.
- **CP-8:** the placement property above. The card's `Test command:` checks it.

**What the change stops proving.** `valid_urls.txt` line 51 today asserts that the password
`%40:80%2f::::::` is accepted. That clause is gone, retired by the issue's ":" rule (Gap 2), and
the same URL now asserts rejection in `invalid_urls.txt`. The modified line 51 re-proves the rest of
what it covered: every username character it holds, and `%40`/`%2f` in the password. No other
assertion is retired.

---

## Records this change makes false

None. The product has no decision records to read: `docs/adr/`, `docs/fdr.md`, `docs/nfdr.md` and
`docs/SDD.md` are absent under the product worktree (`project.md`, `Definition: none`), so nothing in
them goes false. Django's own `docs/ref/validators.txt` does not state which characters user
information may hold (the spec's Verified Claims), so it does not go false either.

---

## Architect Review Notes

- **Where the tests go (Gap 6, delegated here):** the new URL cases go into the fixture files,
  and the appended-query class goes into the `invalid_urls.txt` loader. Both are appended after the
  inline `TEST_DATA` list, which is what keeps the baseline names `_156`/`_157` on their values. The
  one assertion `TEST_DATA` cannot make, CP-5's code and message, is a plain method. *Reason:* this
  follows the file's existing pattern, needs no new test module, and every test is one the card's
  command already runs.
- **How valid_urls.txt line 51 is brought into line (Gap 2, delegated here):** line 51 is modified
  in place to its encoded form, and the original moves to `invalid_urls.txt`. It is not simply
  deleted. *Reason:* the fixture's characters stay covered, the encoded form proves CP-3 on the
  hardest password in the suite, and the original now asserts the rejection the issue asks for.
  Nothing is deleted outside the change.
- **CP-5 by construction, not by a new handler:** the design does not wrap the regex-accepted
  path's `urlsplit` calls. Every value CP-1 or CP-2 newly rejects is rejected by a failed match of
  `regex`. A failed match goes down the existing fallback path, and that path catches `urlsplit`'s
  `ValueError` and raises `ValidationError(code='invalid')`. On that path the IDN re-check cannot
  turn a CP-1/CP-2 rejection back into an acceptance. `urlsplit` cuts the authority at "/", "?" and
  "#" first, and IDNA encoding keeps ":" and "@" as they are, so the re-checked URL fails the same
  part of the pattern. *Reason:* the spec's CP-5 is scoped to rejections under CP-1 and CP-2, and
  this realizes it without changing any other path. A scratch probe outside the tree, run on
  `https://test.[com?m=foo@example.com`, turned `ValueError` into `ValidationError: invalid` with
  only the user-information part changed. The probe was a check that the approach works, not code
  to copy.
- **No Python check alongside the pattern:** the fix stays inside the user-information part of
  `regex` and adds no parsing in `__call__`. *Reason:* one place decides the verdict. A second check
  would need to agree with the pattern on where the authority ends, and the two could drift apart.
- **Found while walking, surfaced and not designed in:** `URLValidator()('http://[user@example.com')`
  raises `ValueError: Invalid IPv6 URL` today, and it still does with this design. The pattern
  accepts the unbalanced "[" in the user information, and the IPv6 re-check at
  `django/core/validators.py` line 136 calls `urlsplit` with no guard. The spec's CP-4 calls "["
  accepted, which is true when it is balanced (`http://[user]@example.com`). For a lone "[",
  today's verdict is this `ValueError`, and CP-4 keeps it. This is a defect in the product, not in
  kensaiapp's machinery, so it is not filed in `docs/findings/`. The design does not fix it. CP-5
  scopes the never-another-exception rule to CP-1/CP-2 rejections, and the request says to "leave
  the rest of Django's behaviour as it is". Taking it into the change is the owner's call, through
  the spec. It is not the design's to make.
