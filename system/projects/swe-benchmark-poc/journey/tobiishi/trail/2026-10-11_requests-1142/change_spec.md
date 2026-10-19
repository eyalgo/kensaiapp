# Change Spec — a GET or HEAD request with no body is sent without a Content-Length header

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Request:** "Fix the issue below in the product, the repository that the project card's
`Product path:` names (`psf/requests`). The repository stands at the commit before the issue was
fixed. Make the change the issue asks for, with tests of your own that show it, and leave the rest of
the product's behaviour as it is." The issue is `psf__requests-1142`, "requests.get is ALWAYS sending
content length", quoted in full in this folder's `change_request.md` § *The issue*. Its constraints
are in that file's § *What must not be done*.

---

## Change Summary

Today requests prepares every request that has no body with `Content-Length: 0`, whatever its method.
That includes the plain `requests.get(url)` the issue reports, which some servers answer with 503.
After this change, a GET or HEAD request with no body carries no `Content-Length` header. This holds
when auth is given, when the caller passed the header, and when the request comes from following a
redirect. Every other request keeps the `Content-Length` it gets today.

**Terms used below.**

- The **prepared request** is the `requests.PreparedRequest` that requests builds for a call:
  `Request(...).prepare()` returns it. For a call made through `requests.get`, `requests.head`,
  `requests.request` or a `Session`, it is the object handed to the session's transport adapter
  (`adapter.send(request, ...)`), and the response's `.request` attribute holds it.
- **No body** means the prepared request's public `body` attribute is `None`. With no `files`, that
  is the case today for `data` omitted, `''` or `{}`, and for `data=None` passed to `requests.get`,
  `requests.head`, `requests.request` or a `Session`. It is **not** the case for `data=[]` or
  `data=()`, or for `data=None` passed to `Request(...)` directly. Their body is an empty list or
  tuple (Verified Claims), and CP-13 covers them.
- A request's **method** is the prepared request's `method` attribute, which requests upper-cases.
  So `'get'` passed by the caller counts as `GET`.
- **Carries no `Content-Length` header** means `'Content-Length' in prepared.headers` is `False`. The
  header mapping is case-insensitive, so no spelling of the name is present.

---

## Rules

### Content-Length — a GET or HEAD request with no body

- **CP-9:** A prepared request whose method is `GET` or `HEAD` and which has no body carries no
  `Content-Length` header. This holds for `Request(...).prepare()`, and for every request
  `requests.get`, `requests.head`, `requests.request` and a `Session` hand to the transport adapter.
  It is a rule because of a present defect: `PreparedRequest.prepare_content_length` sets
  `Content-Length` to `'0'` before looking at the body (`requests/models.py` line 389, called from
  `prepare_body` at line 380). Today `Request('GET', url).prepare().headers['Content-Length']` is
  `'0'`.
- **CP-10:** CP-9 holds whatever headers the caller passed. A `Content-Length` the caller supplies, in
  any spelling (`Content-Length`, `content-length`), is not present on such a request, and preparing
  it does not raise. Today the caller's value is replaced by `'0'`.
- **CP-11:** CP-9 holds when the call gives `auth`, as a `(user, pass)` tuple or an auth object. It is
  a rule because of a second present defect: `prepare_auth` recomputes the header after auth runs
  (`requests/models.py` line 411). Today `requests.get(url, auth=('u', 'p'))` is prepared with
  `Content-Length: 0`.
- **CP-12:** CP-9 holds for a request requests makes by following a redirect. A followed request
  whose method is `GET` or `HEAD` and which has no body carries no `Content-Length`. This includes
  the case where the request that was redirected carried one. Example: a `POST` with `data='hello'`
  (`Content-Length: 5`) is answered `302`, and requests follows it with a `GET` with no body. That
  `GET` carries no `Content-Length`: neither `5` nor `0`.

### Content-Length — what does not change

- **CP-13:** Every request outside CP-9 keeps the `Content-Length` it gets today. The predicate has
  two axes, and this rule decides every side of both:
  - **Method.** Any method other than `GET` and `HEAD`, whether it is standard (`POST`, `PUT`,
    `PATCH`, `DELETE`, `OPTIONS`) or not, keeps today's header. With no body, that header is
    `Content-Length: 0`.
  - **Body.** A `GET` or `HEAD` whose body is not `None` keeps today's header. That covers form
    `data`, string `data`, `files` and a file object passed as `data`. An empty file object still
    gets `Content-Length: 0`, because its body is the file object and not `None`. An empty list or
    tuple body also keeps `Content-Length: 0`: `data=[]`, `data=()` and `Request(..., data=None)`.
    A generator body keeps what it gets today as well (see Out of Scope).

  Nothing about `Transfer-Encoding` changes.

### Proof

- **CP-14:** The change carries tests of its own that the card's `Test command:` runs. They fail on
  the unchanged tree and pass with the change. Together they cover at least:
  - a `GET` with no body, which is the issue (CP-9);
  - a `HEAD` with no body (CP-9);
  - a `GET` with no body given `auth` (CP-11);
  - a `GET` with a body, which keeps its `Content-Length` (CP-13);
  - a `POST` with no body, which keeps `Content-Length: 0` (CP-13).

  These tests must pass in the environment the card's `Test command:` runs. In that environment the
  bundled transport cannot open a connection: on the card's interpreter, sending raises
  `TypeError: __init__() got an unexpected keyword argument 'strict'` from
  `requests/packages/urllib3/connectionpool.py` line 196, and that is why the network tests in the
  baseline fail. How the tests avoid it is development-design's decision.
- **CP-15:** The card's `Test command:` exits 0. Its run fails only the 21 tests listed in
  `change_request.md` § *What must not be done*, under the same names. This change fixes none of
  them, and no other test fails.

---

## Examples

"Today" is the behaviour at `base_commit`, run on 2026-10-11 (see Verified Claims). "CL" is the
prepared request's `Content-Length` value, and "—" means the header is absent. `u` is any `http://`
URL.

| Rule | Scenario | Today | Expected behavior |
|---|---|---|---|
| CP-9 | `requests.get(u)` (the issue) | CL `0` | CL — |
| CP-9 | `Request('GET', u).prepare()` | CL `0` | CL — |
| CP-9 | `Request('get', u).prepare()` (lower-case method) | CL `0` | CL — |
| CP-9 | `requests.head(u)` | CL `0` | CL — |
| CP-9 | `requests.get(u, data='')` / `data={}` / `data=None` | CL `0` | CL — |
| CP-10 | `requests.get(u, headers={'Content-Length': '7'})` | CL `0` | CL —, no exception |
| CP-10 | `Request('GET', u, headers={'content-length': '7'}).prepare()` | CL `0` | CL —, no exception |
| CP-11 | `requests.get(u, auth=('u', 'p'))` | CL `0` | CL —; `Authorization` still set |
| CP-11 | `requests.head(u, auth=('u', 'p'))` | CL `0` | CL — |
| CP-12 | `POST data='hello'` answered `302`, followed as a `GET` | first CL `5`, followed `GET` CL `0` | first CL `5`, followed `GET` CL — |
| CP-12 | `GET` answered `301`, followed as a `GET` | CL `0`, then CL `0` | CL —, then CL — |
| CP-12 | `HEAD` answered `302`, followed as a `HEAD` | CL `0`, then CL `0` | CL —, then CL — |
| CP-13 | `requests.get(u, data='x')` | CL `1` | CL `1` |
| CP-13 | `requests.get(u, data={'a': 'b'})` | CL `3`, form content type | CL `3`, form content type |
| CP-13 | `requests.get(u, files={'f': <2 bytes>})` | CL = multipart length | unchanged |
| CP-13 | `requests.get(u, data=<empty temp file>)` | CL `0` | CL `0` |
| CP-13 | `requests.get(u, data=<3-byte temp file>)` | CL `3` | CL `3` |
| CP-13 | `requests.get(u, data=[])` / `data=()` (body `[]` / `()`) | CL `0` | CL `0` — see Locked Answers, Gap 2 |
| CP-13 | `Request('GET', u, data=None).prepare()` (body `[]`) | CL `0` | CL `0` — see Locked Answers, Gap 2 |
| CP-13 | `requests.post(u)` / `put` / `patch` with no body | CL `0` | CL `0` |
| CP-13 | `requests.delete(u)` / `requests.options(u)` | CL `0` | CL `0` |
| CP-14 | the change's own tests, run on the unchanged tree | — | they fail |
| CP-14 | the change's own tests, run with the change | — | they pass |
| CP-15 | the card's `Test command:` run with the change | exit 0, 21 baseline failures, 5 passed | exit 0, the same 21 failures and no other |

---

## Verified Claims

All runs were made on 2026-10-11 in a scratch copy, `git archive` of the product worktree for this
key at `base_commit` `22623bd8c265b78b161542663ee980738441c307`, extracted under `/tmp`. They used
the card's interpreter, `/home/kensai/issue-venv/bin/python` (Python 3.9.25). The product worktree
itself was left clean (`git status --short` empty). Nothing outside the repository was consulted: no
upstream history after `base_commit`, no pull request, no issue tracker and no benchmark copy.

| Claim | Verified by | What came back |
|---|---|---|
| Today every bodiless request is prepared with `Content-Length: 0`, whatever its method | `Request(m, u).prepare()` for `GET`, `get`, `HEAD`, `POST`, `DELETE`, `OPTIONS` | `body=None`, CL `'0'` for each. `get` is prepared with method `GET` |
| The *Today* column of the Examples | each call made through a `Session` with a recording adapter mounted on `http://`, which captured the prepared request handed to `adapter.send` | every *Today* cell matched |
| Which `data` values give a body of `None` (Terms, CP-13) | `Request('GET', u, data=d).prepare()` for `d` in `None`, `[]`, `''`, `{}`; `Session().get(u, data=d)` through the recording adapter for `d` omitted, `None`, `[]`, `()`, `''` | `Request`: `None`→body `[]`, `[]`→`[]`, `''`→`None`, `{}`→`None`. `Session`: omitted, `None` and `''`→`None`, `[]`→`[]`, `()`→`()`. CL `'0'` in every case. `Request.__init__` turns `data=None` into `[]` (`requests/models.py`, `Request.__init__`), and `Session.request` passes `data` through as given |
| The redirect case today (CP-12) | same recording adapter, answering `302`/`301` with `Location: /next` | `POST data='hello'` sent CL `5`, then a `GET` with `body=None`, CL `0`. The followed request is rebuilt from the original's headers (`requests/sessions.py`, `resolve_redirects`, passes `headers=req.headers`), so the original's CL reaches the followed request's input |
| Auth recomputes the header (CP-11) | read `requests/models.py` lines 397–411; ran `requests.get(u, auth=('u', 'p'))` through the recording adapter | `prepare_auth` calls `prepare_content_length(self.body)` at line 411. Prepared CL `0` |
| Sending over a connection fails in the card's environment (CP-14) | ran `requests.get` against a local socket server on the card's interpreter | `TypeError: __init__() got an unexpected keyword argument 'strict'` from `requests/packages/urllib3/connectionpool.py` line 196. No request reached the server |
| The interpreter's own transport adds no `Content-Length` to a bodiless `GET` or `HEAD`, so the prepared headers are what would reach the wire | `http.client.HTTPConnection.request(m, '/', body=None, headers={})` against a local socket server, on the card's interpreter | `GET`, `HEAD`, `DELETE`, `OPTIONS`: no `Content-Length` line. `POST`: `Content-Length: 0` |
| The card's `Test command:` passes at base with exactly 21 failures | ran `/home/kensai/issue-test.sh` from the scratch copy's root | `21 failed, 5 passed`, `issue-test: only baseline failures remain (21 known at base_commit)`, exit 0 |
| The rules can be met together without a new failure | scratch probe, not a design: the scratch copy's `prepare_content_length` patched to leave the header absent for a bodiless `GET`/`HEAD` and remove any present one, then the recording-adapter probe and the `Test command:` rerun | every *Expected behavior* cell from CP-9 to CP-13 matched. `Test command:` exit 0, the same 21 failures, 5 passed. A first version of the patch that removed the header with `headers.pop('Content-Length', None)` raised `KeyError` on the CP-10 row, which is why CP-10 says "does not raise" |
| No existing test asserts a request's `Content-Length` | `grep -n -i content-length test_requests.py` | no match |

---

## Out of Scope

- **Bodiless requests of other methods.** `DELETE`, `OPTIONS` and any non-standard method keep
  `Content-Length: 0` (CP-13), although RFC 7230 § 3.3.2 says a user agent should not send the header
  when there is no body and the method does not anticipate one. See Locked Answers, Gap 1.
- **A way for the caller to choose.** The issue's alternative, "add the possibility to not send it",
  is not built. A caller cannot force or suppress `Content-Length` on any method, and CP-10 does not
  make a caller-supplied value stick on a `GET` or `HEAD`.
- **The 21 baseline failures,** and the transport's incompatibility with the card's interpreter
  behind them. They stay as they are, as `change_request.md` requires.
- **Defects found while probing that the issue does not name.** Each is left as it is:
  - A generator passed as `data` is prepared with `Content-Length: None`, the string `'None'`.
  - An `io.BytesIO` passed as `data` raises `io.UnsupportedOperation: fileno` while being prepared.
  - A `303` answer is not always followed as a `GET`, because `requests/sessions.py` line 108 compares
    the status code with `is`. A `PUT` answered `303` was followed as a bodiless `PUT` with
    `Content-Length: 0`, and keeps that.
- **Documentation and release notes.** The request asks for none. Neither `docs/`, `README.rst` nor
  `HISTORY.rst` says which requests carry a `Content-Length`. The only mentions are response headers
  in `docs/user/advanced.rst` lines 64 and 126, and a response-body fix at `HISTORY.rst` line 219.
  Docstrings in `requests/` were not looked at.
- **Anything outside the local clone.** Nothing is pushed (`project.md`, `Manages: none`), and
  nothing is published. Per the request, no record, grade or benchmark file is produced.

---

## Locked Answers (the divergence record — self-review 2026-10-11)

- **Gap 1 — which methods (CP-9, CP-13):** `GET` and `HEAD` only. The issue names `GET`. `HEAD` is
  added because it is the same request as `GET` with no response body, and a server that rejects the
  header on one has the same reason to reject it on the other. Other bodiless methods keep
  `Content-Length: 0`. The request says to leave the rest of the product's behaviour as it is, and
  the issue gives no case for them. The choice is reversible: it changes a header, not data. A wider
  set (every method whose meaning does not anticipate a body) remains open to a later change.
- **Gap 2 — "no body" is `body is None` (CP-9, CP-13):** the issue says "GET requests" without
  saying what counts as empty. The spec keys the rule to the prepared request's public `body`
  attribute. That covers the issue's own call, `requests.get(u)`, and every path that leaves `body`
  as `None`. Two kinds of empty input are left as they are:
  - An empty file object is a body the caller passed, so it keeps today's `Content-Length: 0`.
  - An empty list or tuple (`data=[]`, `data=()`, and `Request(..., data=None)`, which requests turns
    into `[]`) is prepared today with a body object, not with `None`. It keeps `Content-Length: 0`.

  Whether an empty sequence should count as "no body" is a question about how requests reads
  `data`, not about the header. The prepared request reports a body for it, and a rule that dropped
  the header while a body is still reported would leave the two disagreeing. This is the
  conservative pick: it changes only requests where requests already reports nothing to send. It is
  reversible, and a later change can widen it.
- **Gap 3 — a caller-supplied `Content-Length` on such a request is dropped (CP-10):** the request is
  silent on this. Today requests never sends the caller's value on a bodiless request: it always
  replaces it with `'0'`. Dropping it keeps that, with the computed value now "absent". Keeping the
  caller's value would be a new capability the issue offers only as an alternative. It would also
  let a stale value through, such as the `5` in CP-12's redirect example. Reversible.
- **Gap 4 — redirects (CP-12):** the request does not mention redirects. A `GET` that requests sends
  after a redirect is still a `GET` requests sends, which is what the issue reports. It is the case
  most likely to go wrong, because the followed request starts from the original request's headers.
  A change that only stops adding the header would send `POST`'s `Content-Length: 5` on a bodiless
  `GET`, which is worse than today.
- **Gap 5 — the tests run where the card's command runs, and the baseline holds by name (CP-14,
  CP-15):** the request asks for "tests of your own" and does not say where they run. A test the
  command does not run shows nothing at the change's gate. A test that needs a working connection
  fails in that environment, and it would show up as a new failure. Both are stated as properties of
  the result. Where the tests go and how they observe a request are development-design's decisions.
