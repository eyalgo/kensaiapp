# Change Spec — URLValidator rejects unencoded ":", "@" and "/" in the username and password

**Date:** 2026-10-10
**Category:** bug
**Behaviour:** changing
**Request:** "Fix the issue below in the product, the Django repository that the project card's
`Product path:` names. The repository stands at the commit before the issue was fixed. Make the change
the issue asks for, with tests of your own that show it, and leave the rest of Django's behaviour as
it is." The issue is `django__django-10097`, quoted in full in this folder's `change_request.md`
§ *The issue*; its constraints are that file's § *What must not be done*.

---

## Change Summary

`django.core.validators.URLValidator` accepts URLs whose username or password holds an unencoded
":", "@" or "/". It also reads an "@" in a path, query or fragment as if it ended a username, so
`http://foo/bar@example.com` is accepted, and so is almost any invalid URL once
`?m=foo@example.com` is appended. After this change such URLs are rejected. Percent-encoded forms
are still accepted, and no other verdict changes.

**Terms used below.** For a value `<scheme>://<rest>`, the **authority** is the part of `<rest>`
before the first "/", "?" or "#", or all of `<rest>` when none of the three occurs. When the authority
contains an "@", the **user information** is the text before that "@", and the host and optional port
are the text after it. The **username** is the user information up to its first ":", and the
**password** is everything after that ":". With no ":", the whole user information is the username.
"Rejected" and "accepted" mean what they mean for `URLValidator` today: rejected raises
`ValidationError`, and accepted returns without raising.

---

## Rules

### URLValidator — where user information can be

- **CP-1:** An "@" that comes after the first "/", "?" or "#" following `://` does not introduce
  user information. Such a URL gets the verdict of the same value with every "@" after that point
  removed. It is decided on the host and port written before the "/", "?" or "#". So
  `http://foo/bar@example.com` is rejected, because host `foo` is not a valid host, and
  `http://example.com/?m=foo@example.com` stays accepted.

### URLValidator — what the username and password may hold

- **CP-2:** Neither the username nor the password contains an unencoded ":", "@" or "/". A URL whose
  user information holds a second ":" is rejected (e.g. `http://foo:b:ar@example.com`), and so is one
  whose authority holds a second "@" (e.g. `http://foo@bar@example.com`, `http://foo:bar@baz@example.com`).
  A "/" never reaches the user information, because by CP-1 it ends the authority
  (`http://foo:bar/baz@example.com` is rejected).
- **CP-3:** The percent-encoded forms of those characters are accepted in the username and the
  password: `%3A`/`%3a`, `%40`, and `%2F`/`%2f`. Each of `http://foo%2Fbar@example.com`,
  `http://foo:b%3Aar@example.com` and `http://foo%40bar@example.com` is accepted.
- **CP-4:** Apart from CP-1 to CP-3, nothing changes about which user information is accepted. The
  domain is every character. The username and password reject whitespace, as today. Beyond the one
  separating ":", they also reject ":", "@", "/", "?" and "#". "?" and "#" are rejected through CP-1:
  each ends the authority. **Every other character keeps today's verdict, which is acceptance**: for
  example non-ASCII letters, `[`, `]`, `!$&'()*+,;=`, `-.~_` and `%`. The empty cases keep today's
  verdicts:
  - `http://@example.com` is rejected.
  - `http://:@example.com`, `http://:pass@example.com` and `http://user:@example.com` are accepted.

### URLValidator — how a rejection looks

- **CP-5:** A URL rejected under CP-1 or CP-2 is rejected the way `URLValidator` rejects any URL. It
  raises `ValidationError` with message `Enter a valid URL.` and code `invalid`, never another
  exception. A present defect makes this a rule. Today `URLValidator()('https://test.[com?m=foo@example.com')`
  raises `ValueError: Invalid IPv6 URL`, out of the `urlsplit` call at `django/core/validators.py`
  line 136, instead of a `ValidationError`. That value is an entry of `tests/validators/invalid_urls.txt`
  with the issue's `?m=foo@example.com` appended.
- **CP-6:** CP-1 to CP-5 hold for every scheme the validator accepts: the default four and any list
  passed as `schemes`. For example `ftp://foo/bar@example.com` is rejected, and
  `URLValidator(EXTENDED_SCHEMES)` still accepts `git+ssh://git@github.com/example/hg-git.git`.

### Proof

- **CP-7:** The change carries tests of its own that the card's `Test command:` runs. They fail on
  the unchanged tree and pass with the change. Together they cover at least:
  - the issue's URL `http://foo/bar@example.com`;
  - an unencoded ":", "@" and "/" in the username and in the password;
  - an accepted percent-encoded form (CP-3);
  - entries of `tests/validators/invalid_urls.txt` with `?m=foo@example.com` appended.
- **CP-8:** The card's `Test command:` exits 0. Its run fails only `test_URLValidator_raises_error_156`
  and `test_URLValidator_raises_error_157`, and those two names are still the trailing-newline
  values they test today: `'http://www.djangoproject.com/\n'` and `'http://[::ffff:192.9.5.5]\n'`.
  This change fixes neither of them, and no other test fails.

---

## Examples

All rows use `URLValidator()` unless a row names another validator. "Today" is the verdict at
`base_commit`, run on 2026-10-10 (see Verified Claims).

| Rule | Scenario | Today | Expected behavior |
|---|---|---|---|
| CP-1 | `http://foo/bar@example.com` (the issue's URL) | accepted | rejected |
| CP-1 | `http://foo?bar@example.com` | accepted | rejected (host `foo`) |
| CP-1 | `http://foo#bar@example.com` | accepted | rejected (host `foo`) |
| CP-1 | `http://example.com/?m=foo@example.com` | accepted | accepted |
| CP-1 | `http://example.com?m=foo@example.com` | accepted | accepted |
| CP-1 | `http://example.com#foo@bar` | accepted | accepted |
| CP-1 | `http://userid:password@example.com?m=foo@example.com` | accepted | accepted |
| CP-1 | each of the 59 entries of `tests/validators/invalid_urls.txt` with `?m=foo@example.com` appended | 41 accepted, 1 raises `ValueError`, 17 rejected | all 59 rejected |
| CP-1 | each entry of `tests/validators/valid_urls.txt` except line 51 | accepted | accepted |
| CP-2 | `http://foo:b:ar@example.com` (":" in password) | accepted | rejected |
| CP-2 | `http://f@oo:bar@example.com` ("@" in username) | accepted | rejected |
| CP-2 | `http://foo@bar@example.com` | accepted | rejected |
| CP-2 | `http://foo:bar@baz@example.com` ("@" in password) | accepted | rejected |
| CP-2 | `http://foo:bar/baz@example.com` ("/" in password) | accepted | rejected |
| CP-2 | `http://-.~_!$&'()*+,;=:%40:80%2f::::::@example.com` (`tests/validators/valid_urls.txt` line 51, password holds unencoded ":") | accepted | rejected — see Locked Answers, Gap 2 |
| CP-3 | `http://-.~_!$&'()*+,;=:%40%3A80%2f%3A%3A%3A%3A%3A%3A@example.com` (line 51 with its password's colons encoded) | accepted | accepted |
| CP-3 | `http://foo%2Fbar@example.com` | accepted | accepted |
| CP-3 | `http://foo:b%3Aar@example.com` | accepted | accepted |
| CP-3 | `http://foo%40bar@example.com` | accepted | accepted |
| CP-4 | `http://userid:password@example.com:8080/` | accepted | accepted |
| CP-4 | `http://usér:päss@example.com` | accepted | accepted |
| CP-4 | `http://[user]@example.com` | accepted | accepted |
| CP-4 | `http://us er@example.com` | rejected | rejected |
| CP-4 | `http://@example.com` | rejected | rejected |
| CP-4 | `http://:@example.com` | accepted | accepted |
| CP-4 | `http://:pass@example.com` | accepted | accepted |
| CP-4 | `http://user:@example.com` | accepted | accepted |
| CP-4 | `http://user:pa?ss@example.com` | accepted | rejected (host `user`, port `pa`) — see Locked Answers, Gap 1 |
| CP-5 | `https://test.[com?m=foo@example.com` | raises `ValueError: Invalid IPv6 URL` | raises `ValidationError`, message `Enter a valid URL.`, code `invalid` |
| CP-5 | any rejected row above | — | `ValidationError`, code `invalid` |
| CP-6 | `ftp://foo/bar@example.com` | accepted | rejected |
| CP-6 | `URLValidator(EXTENDED_SCHEMES)` on `git+ssh://git@github.com/example/hg-git.git` | accepted | accepted |
| CP-7 | the change's own tests, run on the unchanged tree | — | they fail |
| CP-7 | the change's own tests, run with the change | — | they pass |
| CP-8 | the card's `Test command:` run with the change | exit 0, 2 baseline failures | exit 0; the only failures are `test_URLValidator_raises_error_156` and `_157`, still testing the two trailing-newline values |

---

## Verified Claims

All run claims were run on 2026-10-10 in the product's change worktree for this key. That worktree
is opened from the repository the card's `Product path:` names, at `base_commit`, with no change
applied. They used the card's interpreter (`/home/kensai/issue-venv/bin/python`, Python 3.8.20) and
`settings.configure()`. Nothing outside the repository was consulted: no upstream history, no pull
request, no benchmark copy.

| Claim | Verified by | What came back |
|---|---|---|
| Today the validator accepts the issue's URL and every unencoded-character case in the Examples | ran `URLValidator()(value)` on each row's value | every row marked "accepted" under *Today* returned without raising. `http://@example.com` and `http://us er@example.com` raised `ValidationError` |
| Appending `?m=foo@example.com` makes most invalid fixtures accepted today | ran `URLValidator()` on every line of `tests/validators/invalid_urls.txt` + the suffix | 59 entries: 41 accepted, 17 rejected, 1 (`https://test.[com?m=foo@example.com`) raised `ValueError: Invalid IPv6 URL` from `django/core/validators.py` line 136 |
| The issue's three characters alone would not reject the issue's own query-string class (Locked Answers, Gap 1) | scratch probe built outside the tree. It subclassed `URLValidator` with only its user-information pattern swapped: first excluding ":", "@", "/" only, then also "?", "#" (empty user information still rejected). Same interpreter, run against the unchanged fixture files | three-characters reading: 34 of 59 invalid+suffix still accepted. This spec's reading: 0 of 59. This probe shows the rules can be met together. It is not a design |
| The rules can be met without moving any other fixture verdict | same probe, this spec's reading | all 59 `invalid_urls.txt` entries rejected, with and without the suffix. Of the 73 `valid_urls.txt` entries, only line 51 is rejected. Every row of the Examples table under *Expected behavior* matched |
| `tests/validators/valid_urls.txt` line 51 is `http://-.~_!$&'()*+,;=:%40:80%2f::::::@example.com` and is asserted valid | read the file (`grep -n '@'`), and `tests/validators/tests.py` lines 299–306, which append each `valid_urls.txt` line to `TEST_DATA` expecting `None` | confirmed. It is the only `valid_urls.txt` entry whose password holds an unencoded ":" |
| A rejection is `ValidationError` with code `invalid`, message `Enter a valid URL.` | ran `URLValidator().code` and `str(URLValidator().message)` (with `USE_I18N=False`) | `invalid`, `Enter a valid URL.` |
| `URLValidator(EXTENDED_SCHEMES)` accepts `git+ssh://git@github.com/example/hg-git.git` today | read `tests/validators/tests.py` line 218 (expects `None`); ran it | accepted |
| The card's `Test command:` passes at base with exactly two failures | ran `/home/kensai/issue-test.sh` from the product worktree root | `Ran 365 tests`, `FAILED (failures=2)`, `issue-test: only baseline failures remain (2 known at base_commit)`, exit 0. The worktree stayed clean (`git status --short` empty) |
| The two baseline failures are named by position, and are the trailing-newline values | read `tests/validators/tests.py` lines 373–376: each test name carries `test_counter`, its index in `TEST_DATA`. Printed `TEST_DATA[156]` and `[157]` | 156 = `URLValidator()`, `'http://www.djangoproject.com/\n'`. 157 = `URLValidator()`, `'http://[::ffff:192.9.5.5]\n'`. Both are inline entries at `tests/validators/tests.py` lines 222–223, both expecting `ValidationError` |
| Django's validator reference does not state which characters user information may hold | `grep -n -i 'user\|password\|authenticat' docs/ref/validators.txt` | no match |

---

## Out of Scope

- **The two baseline failures.** `test_URLValidator_raises_error_156` and `_157` (trailing newline) stay
  failing, as `change_request.md` § *What must not be done* requires. Any other test that fails today
  is not touched either.
- **Host, port, path, query, fragment and scheme validation.** Nothing changes beyond where CP-1 says
  the authority ends. This includes IPv6 and IDN handling and the 253-character host limit.
- **The validity of percent-escapes themselves.** A malformed escape such as `%zz` in user information
  keeps today's verdict.
- **`forms.URLField` and `models.URLField`.** They inherit the new verdicts through `URLValidator`.
  Their own input normalisation is not changed.
- **Other validators** in `django/core/validators.py` (e.g. `EmailValidator`).
- **Documentation and release notes.** The request asks for none. Django's validator reference
  (`docs/ref/validators.txt`) does not state the fact this change moves, as checked above. Other
  surfaces were not looked at: release notes, topic guides, and the docstrings of the form and model
  fields.
- **Anything outside the local clone.** The patch is not pushed (`project.md`, `Manages: none`), and
  nothing is published. Per the request, no record, grade or benchmark file is produced.

---

## Locked Answers (the divergence record — self-review 2026-10-10)

- **Gap 1: "?" and "#" also end where user information can be (CP-1).** The issue names only
  ":", "@" and "/". RFC 1738, which it cites, permits "?" in a username. The spec goes further
  because of what the issue itself says. It calls `?m=foo@example.com` "a query string", and says
  that appending it makes many `invalid_urls.txt` entries valid. Excluding the three characters alone
  leaves 34 of those 59 accepted, so the issue's own example would stay broken. With "?" and "#"
  ending the authority, none stay accepted (Verified Claims). The cost is a stated divergence:
  `http://user:pa?ss@example.com` goes from accepted to rejected. The issue's ask is to reject
  invalid URLs, which a stricter reading serves. The change is also reversible: it moves verdicts,
  not data.
- **Gap 2: `tests/validators/valid_urls.txt` line 51 becomes a rejected URL (CP-2).** The request
  says to leave "the rest of Django's behaviour as it is". That fixture asserts that a password of
  `%40:80%2f::::::` is valid, and the issue's quoted rule says ":" in the password must be encoded.
  The spec takes the issue's rule. The fixture is about exactly the behaviour the issue names, so it
  is not part of "the rest". The same URL with its password's colons encoded stays accepted (CP-3
  row), so what that fixture shows still has an accepted form. How the test data is brought into line
  is development-design's decision.
- **Gap 3: empty username and password keep today's verdicts (CP-4).** The issue says nothing about
  them. The conservative pick is no change: `http://@example.com` stays rejected, and
  `http://:@example.com`, `http://:pass@example.com` and `http://user:@example.com` stay accepted.
- **Gap 4: every other character keeps today's verdict (CP-4).** The issue names three characters.
  The spec closes the set by domain: whitespace stays rejected, the CP-1/CP-2 characters are newly
  rejected, and every other character stays accepted. That keeps the change to what the issue asks
  and to the request's "leave the rest".
- **Gap 5: a rejection is a `ValidationError`, never a `ValueError` (CP-5).** The request did not
  say this. One value in the issue's own example class raises `ValueError` today. A caller such as a
  form reports a `ValidationError` as an invalid field, and a `ValueError` as a crash. A rejection
  the issue asks for has to be one a caller can report.
- **Gap 6: the change's tests are ones the card's `Test command:` runs, and the baseline names hold
  (CP-7, CP-8).** The request asks for "tests of your own" and does not say where they run. The card's
  command runs only the `validators` test app, and it recognises the two baseline failures by name,
  which is their position in the test data. A test that the command does not run shows nothing at
  the change's gate. A change that renumbers the baseline turns the command red with no behaviour
  broken. Both are stated as properties of the result. Where tests go is development-design's
  decision.
