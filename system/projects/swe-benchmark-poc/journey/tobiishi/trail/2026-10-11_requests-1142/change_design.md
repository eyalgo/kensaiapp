# Change Design — a GET or HEAD request with no body is sent without a Content-Length header

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Publishes text:** no

---

## 1. Change Summary

Today `PreparedRequest.prepare_content_length` writes `Content-Length: 0` before it looks at the body.
It is the one place where requests sets that header on a body that is not a stream. Two call sites
reach it: `prepare_body` on the non-stream branch, and `prepare_auth`, which recomputes the header
after auth runs. The change puts the CP-9 predicate (the prepared method is `GET` or `HEAD`, and the
body is `None`) inside `prepare_content_length`. When the predicate holds, the method leaves the
request with **no** `Content-Length`: it removes any header already present and adds none. When it
does not hold, the method behaves exactly as today. Because both call sites, and every request path
(`Request.prepare`, `requests.get`/`head`/`request`, a `Session`, a followed redirect), prepare
through this method, the one change covers CP-9 to CP-12. CP-13 is kept by leaving every other branch
untouched.

Only one product module changes, `requests/models.py`. The product's one test file,
`test_requests.py`, gets the change's own tests.

**What crosses to the outside** (the instance overlay's boundary): nothing. The change stores nothing
on any device, collects nothing and sends nothing to a third party. It touches no presence surface
and publishes nothing. The product manages nothing and is never pushed (`project.md`, `Manages:
none`). The only outward effect is one header that the patched library no longer sends.

---

## 2. Blast Radius

The product has no parts table (`docs/SDD.md` § 3) and no module set (`docs/nfdr.md` § 1.2). Its
`docs/` holds only Sphinx documentation. So the module set below is the `requests/` package's files
that touch request preparation, and placement follows the code's own ownership: `PreparedRequest`
owns everything that is computed onto a prepared request's headers.

| Module | Status | What changes |
|---|---|---|
| `requests/models.py` | Modified | `PreparedRequest.prepare_content_length`: new logic. For a prepared method of `GET`/`HEAD` with `body is None`, the request ends up with no `Content-Length`, and one that is already present is removed. Otherwise, today's behaviour. `prepare_body` and `prepare_auth` keep their calls, and both inherit the rule. The stream branch of `prepare_body` and `Request.__init__` are untouched. |
| `requests/sessions.py` | Unchanged | `resolve_redirects` rebuilds each followed request through `Session.request` → `Request.prepare`, so the rule reaches it without a change here (CP-12). |
| `requests/auth.py` | Unchanged | Auth objects run inside `prepare_auth`, before the recompute that now applies the rule (CP-11). `HTTPDigestAuth.handle_401` re-sends the already-prepared request, which already lacks the header. |
| `requests/api.py` | Unchanged | `requests.get`/`head`/`request` are `Session().request(...)`, with no preparation logic of their own. |
| `requests/structures.py` | Unchanged | `CaseInsensitiveDict` already gives a case-insensitive `in` and `del`, which the change uses as they are. |
| `requests/adapters.py` | Unchanged | Sends whatever headers the prepared request carries. |
| `test_requests.py` | Modified | The change's own tests (§5). |

The public interface does not change: `prepare_content_length(self, body)` keeps its signature, and no
symbol is added or removed. So there is no transitive radius. An importer of `models` sees the same
names, and only the header value differs. The change crosses no other surface or project. It is one
benchmark issue's patch in a local clone.

---

## 3. Sub-jobs

Omitted: one product module is affected. Inside `models.py` there is one seam,
`prepare_content_length`, and both callers inherit the change from it. No two parts of the change
have an ordering edge between them, so there is nothing to cut below module level.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `requests/models.py` — `prepare_content_length` applies CP-9 | Key the rule on `self.method`, which `prepare_method` has already upper-cased, and on `body is None`. When the rule applies, *remove* the header. Skipping the `'0'` default is not enough, because the header can already be present from the caller's `headers` (CP-10) or from headers a followed redirect carries over (CP-12). Remove it through the header mapping's own case-insensitive delete, and repeat while the membership test still finds the header. `CaseInsensitiveDict.__setitem__` does not fold case, so the mapping can hold more than one spelling, and each delete removes only one of them. Do not use `pop`. `CaseInsensitiveDict` does not override it, so the plain-dict `pop` bypasses the lower-keys cache. That is what raised the `KeyError` the spec's probe recorded under CP-10. A request prepared by hand with no method set (`self.method is None`) falls outside the rule and keeps today's behaviour. |
| `test_requests.py` — the change's tests | The tests observe the prepared request in one of two ways, without a connection. The first is `Request(...).prepare()`. The second is a `Session` with a test-local adapter (a `requests.adapters.BaseAdapter` subclass) mounted on `http://`, which records every prepared request handed to `send` and answers from a script. For a redirect, the scripted response needs `status_code`, a `location` header, `url`, `_content` set (so `resp.content` does not read a socket), and a `raw` whose `release_conn` does nothing, because `resolve_redirects` closes the response. |

---

## 5. Test Additions

All tests go in `test_requests.py`, in `RequestsTestCase`, because that is the file the card's `Test
command:` runs (`pytest test_requests.py`). None of them opens a connection (CP-14). They use the
observation points in the §4 row. "Session" below means a `requests.Session` with the recording
adapter mounted, and `u` is any `http://` URL.

| # | Rule / Example | Test file | What to add | Unchanged tree |
|---|---|---|---|---|
| 1 | CP-9: `Request('GET', u).prepare()`; `Request('get', u).prepare()` | `test_requests.py` | New test: CL absent on both; method prepared as `GET` | fails |
| 2 | CP-9: `requests.get(u)`, the issue, observed as Session `get(u)` (Review Notes, *observation point*) | `test_requests.py` | New test: the recorded prepared request has `body is None` and no CL | fails |
| 3 | CP-9: `requests.head(u)`, as Session `head(u)`; `Request('HEAD', u).prepare()` | `test_requests.py` | New test: CL absent on both | fails |
| 4 | CP-9: Session `get(u, data='')`, `data={}`, `data=None` | `test_requests.py` | New test: CL absent for each of the three | fails |
| 5 | CP-10: Session `get(u, headers={'Content-Length': '7'})`; `Request('GET', u, headers={'content-length': '7'}).prepare()`; `Request('GET', u, headers={'Content-Length': '7', 'content-length': '8'}).prepare()` (two spellings at once) | `test_requests.py` | New test: no exception, and CL absent in any spelling, on each | fails |
| 6 | CP-11: Session `get(u, auth=('u', 'p'))`; Session `head(u, auth=('u', 'p'))`; Session `get(u, auth=HTTPDigestAuth('u', 'p'))` (an auth object) | `test_requests.py` | New test: CL absent on each; `Authorization` still set on the tuple `GET` | fails |
| 7 | CP-12: `POST data='hello'` scripted `302 → /next` | `test_requests.py` | New test: two recorded requests. The first is a `POST` with CL `'5'`. The second is a `GET` with `body is None` and no CL | fails |
| 8 | CP-12: `GET` scripted `301`; `HEAD` scripted `302` | `test_requests.py` | New test: both recorded requests have no CL, for each method | fails |
| 9 | CP-13 body axis: Session `get(u, data='x')` → CL `'1'`; `data={'a': 'b'}` → CL `'3'` plus form `Content-Type`; `files={'f': <2 bytes>}` → CL equals `len(body)` | `test_requests.py` | New test (regression fence) | passes |
| 10 | CP-13 body axis: `data=<empty temp file>` → CL `'0'`; `data=<3-byte temp file>` → CL `'3'` | `test_requests.py` | New test (regression fence) | passes |
| 11 | CP-13 body axis: Session `get(u, data=[])` and `data=()` → CL `'0'`; `Request('GET', u, data=None).prepare()` (body `[]`) → CL `'0'` | `test_requests.py` | New test (regression fence) | passes |
| 12 | CP-13 method axis: Session `post`/`put`/`patch`/`delete`/`options` with no body → CL `'0'`; `Request('PURGE', u).prepare()` (non-standard) → CL `'0'` | `test_requests.py` | New test (regression fence). The `POST` case is CP-14's named minimum | passes |
| 13 | CP-14 / CP-15: the card's `Test command:` | — | No new test. With the change, it exits 0, and the only failures are the 21 named in `change_request.md` § *What must not be done* | — |

**Rule-implied edges with no row of their own:**

- *A generator body keeps what it gets today, and nothing about `Transfer-Encoding` changes*
  (CP-13). Covered by row 11. `data=[]` and `data=()` go through the same stream branch of
  `prepare_body`, which the change leaves untouched, and their body is not `None`, so the predicate
  excludes them. Pinning the generator's present value (`Content-Length: 'None'`) in a test would lock
  in a defect the spec puts out of scope.
- *A bodiless `POST` given auth keeps `Content-Length: 0`.* Covered by rows 6 and 12 together. The
  recompute in `prepare_auth` is the same method the predicate guards, and row 12 fences the
  non-`GET`/`HEAD` side of it.
- *A request prepared by hand with no method.* It is outside every spec Example. It keeps today's
  behaviour by construction (§4), and no row pins it.

**What the change stops proving:** nothing. No existing test asserts a request's `Content-Length`
(the spec's Verified Claims, `grep -i content-length test_requests.py`), so no assertion is retired.

---

## Records this change makes false

None. I read `$PROJECT_DOCS` (the product worktree's `docs/`). It holds Sphinx user documentation and
no `adr/`, `nfdr.md`, `fdr.md` or `SDD.md`, so there is no record to go false. The spec's Out of
Scope already records that no file in `docs/`, `README.rst` or `HISTORY.rst` says which requests carry
a `Content-Length`.

---

## Architect Review Notes

- **(a) CP-14's "they fail on the unchanged tree" and its CP-13 minimums.** CP-14 says the change's
  tests fail on the unchanged tree. It also requires them to cover a `GET` with a body and a bodiless
  `POST` that keep today's `Content-Length`, and those can only pass on the unchanged tree. Resolved:
  the *set* fails on the unchanged tree, because rows 1–8 (CP-9 to CP-12) each fail there. Rows 9–12
  are regression fences that pass both before and after, as §5's last column states. Reason: a
  preservation test that failed today would be asserting a change CP-13 forbids.
- **(b) CP-9 to CP-12 are realized by construction at one seam.** The rule lives in
  `prepare_content_length`, keyed on the prepared method and `body is None`, and it *removes* the
  header instead of declining to add it. It is not placed in `prepare_body` alone, because
  `prepare_auth`'s recompute would put the header back (CP-11). It is not placed in
  `resolve_redirects` either, because the followed request is prepared through the same method
  anyway (CP-12). Removal, not omission, is what makes CP-10 and CP-12 hold whatever headers the
  request's input carried.
- **(b) "In any spelling" (CP-10) is realized by removing until absent.** A probe at `base_commit`
  shows that `CaseInsensitiveDict` stores each spelling as its own key. Its `__setitem__` does not
  fold case, so a caller's `content-length` and a computed `Content-Length` sit side by side, and its
  `__delitem__` removes one key per call. A single delete would leave a second spelling the caller
  passed. So §4 repeats the delete while membership holds, and row 5 adds the two-spelling case.
  Reason: the spec's "any spelling" is a contract, and one delete would meet it only when the caller
  happened to pass a single spelling.
- **(b) The observation point for `requests.get`/`requests.head`.** Rows 2, 3 and 6 observe the
  issue's call through a `Session` with a mounted recording adapter, not through `requests.get`
  itself. Reason: `requests.get` builds a throwaway `Session` inside `api.request` and adds no
  preparation logic of its own. Observing it directly would mean patching a class attribute
  process-wide, and a `Session` reaches the same `prepare` path without that. CP-14 leaves the "how"
  to this stage.
- **(d) No parts table, no module set.** Placement and blast radius are taken from the package's own
  structure (`PreparedRequest` owns computed request headers), because the product carries neither
  `docs/SDD.md` § 3 nor `docs/nfdr.md` § 1.2. No record names a review at this stage, so there was no
  delegated gate to perform.
- **Drift in the spec's Verified Claims (flagged; the rules stand).** The redirect row says the
  followed request "is rebuilt from the original's headers … so the original's CL reaches the
  followed request's input". A probe on a scratch copy at `base_commit`, using the card's interpreter
  and a recording adapter, does not bear this out. `prepare_headers` copies the headers into a new
  `CaseInsensitiveDict`, so the computed `Content-Length: 5` never enters `Request.headers`. The
  followed `GET` is prepared with CL `'0'` from the default in `prepare_content_length`, not with a
  carried `5`. A `Content-Length` the *caller* passed in `headers` on the original request does
  reach the followed request's input. CP-12 and its Examples are unaffected, and the removal in §4
  covers both cases. The spec's reason for Gap 4 ("would send `POST`'s `Content-Length: 5`") holds
  only for that caller-supplied case.
