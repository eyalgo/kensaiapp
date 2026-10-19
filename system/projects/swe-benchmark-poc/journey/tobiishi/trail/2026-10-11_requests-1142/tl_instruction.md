# Tech Lead instruction — requests-1142: a GET or HEAD request with no body is sent without a Content-Length header

**Product root:** <the issue's clone>/.worktrees/2026-10-11_requests-1142 — every path below is relative to it.
**Scope:** `PreparedRequest.prepare_content_length` in `requests/models.py` leaves a bodiless `GET`/`HEAD` with no `Content-Length` (CP-9 to CP-12); the change's own tests go in `test_requests.py` (CP-13, CP-14). The card's `Test command:` ends exit 0 with the same 21 baseline failures and no other (CP-15).
**Classification:** Category `bug` · Behaviour `changing` (copied from `change_design.md`).

**What this change may bring in:** no third-party origin, no device storage, no new dependency, no new module, no new public symbol. The tests open no connection (CP-14).

---

## Project layout

```
requests/
  models.py          ← modified (PreparedRequest.prepare_content_length only)
test_requests.py     ← modified (new tests in RequestsTestCase, plus one test-local adapter class)
```

No parts table — placement follows change_design.md §2. No `docs/adr/`, `docs/nfdr.md` or `docs/SDD.md` exist for this product, so the module set is `change_design.md §2`'s. Nothing is created or renamed.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Task split:** the design's §5 rows 1–8 (CP-9 to CP-12, red on the unchanged tree) and rows 9–12 (CP-13 fences, green on the unchanged tree) are two tasks here, not one. Reason: they have different lanes. Rows 1–8 are test-first. Rows 9–12 cannot go red on the tree as it stands, and a test-first marker on them would send the developer to manufacture a red that is not there. Task 2 uses the already-green shape.
- **Ordering:** Task 2 comes after Task 1 and lists it under `Dependencies:`. Reason: the fences use the recording adapter Task 1 creates in `test_requests.py`, so it uses what Task 1 makes. The fences are also only a fence once the rule exists, since their point is that the change leaves them green.
- **Behaviour added (edge cases the design's rows imply):** Task 1 adds `Authorization` still set on a bodiless tuple-auth `GET`, taken from the spec's CP-11 row, and a lower-case `'get'` and `'head'` method through `Request(...).prepare()`. Reason: the spec's Examples state both and §5 pins them only in passing.
- **Behaviour added:** Task 1 asserts the followed request in a redirect is prepared from a request whose caller passed `Content-Length` (`headers={'Content-Length': '7'}` on a bodiless `GET` answered `302`), in addition to §5 row 7's `POST data='hello'`. Reason: the architect's drift note (Architect Review Notes, last bullet) shows the carried-over header reaches the followed request's input only when the *caller* passed it, so that is the case where a change that merely stops adding the header would go wrong, and row 7 alone does not exercise it.
- **Spec drift carried, not reconciled:** the design flags that the spec's Verified Claims row on redirects is wrong about the mechanism (a followed `GET` is prepared with `0` from the default, not a carried `5`). The rules and examples stand, and Task 1's hint covers both cases. Nothing in the plan depends on the spec's explanation.
- **Hint kept, tightened:** the design's §4 hint for `prepare_content_length` is carried into Task 1 as the approach only. The hint for the tests is carried too, and the plan does not give the adapter's code.
- **Gate command checked:** `project.md` `Test command:` was run once in this change's product worktree (`/home/kensai/issue-test.sh`). It runs and returns `21 failed, 5 passed`, then `issue-test: only baseline failures remain (21 known at base_commit)`, exit 0. It is a valid gate and every `#### Verification gate` below uses it. The tool reports baseline failures; it does not by itself prove the new tests ran, so Task 1 and Task 2 name tests that must be among the passes.

## Corrections owed while there

- Owed outside this change's reach: none. `change_design.md` § *Records this change makes false* is the zero form: the product's `docs/` holds Sphinx user documentation and no record that says which requests carry a `Content-Length`.
- Held by reading, not by a task: a `PreparedRequest` prepared by hand with `self.method is None` falls outside the rule and keeps today's behaviour. No Example covers it and no test pins it. See Task 1, *Held by review*.

---

### Task 1: Drop Content-Length on a bodiless GET/HEAD (`requests/models.py`, `test_requests.py`)

**Dependencies:** None

**What to build:** `PreparedRequest.prepare_content_length(self, body)` applies CP-9. When the prepared method is `GET` or `HEAD` and `body is None`, the prepared request ends with no `Content-Length` header in any spelling, and a header already present is removed. In every other case the method behaves as it does today. The signature is unchanged, and `prepare_body` and `prepare_auth` keep their calls to it. The tests in this task add the recording adapter that every later test uses: a `requests.adapters.BaseAdapter` subclass local to `test_requests.py`, mounted on `http://` of a `Session`, that records each prepared request handed to `send` and answers from a script.

#### Behaviours to verify (developer adds tests to `test_requests.py`, in `RequestsTestCase`)

All of these run without a connection. "Session" is a `requests.Session` with the recording adapter mounted, and `u` is any `http://` URL. "No CL" means `'Content-Length' in prepared.headers` is `False`.

- `test_get_without_body_has_no_content_length` — `Request('GET', u).prepare()` and `Request('get', u).prepare()` have no CL, and both have method `GET`.
- `test_session_get_without_body_has_no_content_length` — the issue's call, observed as Session `get(u)`: the recorded prepared request has `body is None` and no CL.
- `test_head_without_body_has_no_content_length` — Session `head(u)` and `Request('HEAD', u).prepare()` have no CL.
- `test_get_with_empty_data_has_no_content_length` — Session `get(u, data='')`, `data={}` and `data=None` each have no CL.
- `test_caller_supplied_content_length_is_dropped_on_bodiless_get` — Session `get(u, headers={'Content-Length': '7'})`, `Request('GET', u, headers={'content-length': '7'}).prepare()` and `Request('GET', u, headers={'Content-Length': '7', 'content-length': '8'}).prepare()` do not raise, and each has no CL in any spelling. The two-spelling case is the one a single delete would miss.
- `test_bodiless_get_with_auth_has_no_content_length` — Session `get(u, auth=('u', 'p'))` has no CL and still has an `Authorization` header; Session `head(u, auth=('u', 'p'))` and Session `get(u, auth=HTTPDigestAuth('u', 'p'))` have no CL.
- `test_followed_get_after_post_redirect_has_no_content_length` — Session `post(u, data='hello')` scripted `302` with `Location: /next`: two recorded requests. The first is a `POST` with CL `'5'`. The second is a `GET` with `body is None` and no CL (neither `'5'` nor `'0'`).
- `test_followed_request_after_redirect_has_no_content_length` — Session `get(u)` scripted `301`, and Session `head(u)` scripted `302`: each followed request has no CL.
- `test_followed_get_drops_caller_supplied_content_length` — Session `get(u, headers={'Content-Length': '7'})` scripted `302`: the first and the followed request both have no CL.

Rows 1 to 8 of the design's §5 are the first eight tests. The ninth is this plan's addition (TL Review Notes). All nine fail on the unchanged tree.

For the redirect tests, the scripted response needs `status_code`, a `location` header, `url`, `_content` set so `resp.content` does not read a socket, and a `raw` whose `release_conn` does nothing, because `resolve_redirects` closes the response.

#### Held by review

- A request prepared by hand with `self.method is None` keeps today's behaviour. The design makes it so by construction (§4), and no Example or test pins it. It is held by reading the diff: the predicate must not raise on a `None` method, and must not treat it as `GET`.
- A generator `data` keeps what it gets today (`Content-Length: 'None'`) and `Transfer-Encoding` does not change (CP-13). It is covered by no test, on purpose: pinning `'None'` would lock in a defect the spec puts out of scope. It is held by reading the diff: the stream branch of `prepare_body` is untouched.

#### Implement

Infer from failing tests.

# Hint: key the rule on `self.method`, which `prepare_method` has already upper-cased, and on `body is None`. When it applies, *remove* the header; skipping the `'0'` default is not enough, because the header can already be present from the caller's `headers` or from headers a followed redirect carries over. Remove it through the header mapping's case-insensitive delete, and repeat while the membership test still finds the header, since `CaseInsensitiveDict.__setitem__` does not fold case and the mapping can hold more than one spelling. Do not use `pop`: `CaseInsensitiveDict` does not override it, so the plain-dict `pop` bypasses the lower-keys cache and raised the `KeyError` the spec's probe recorded under CP-10. Everything else in the method keeps today's behaviour.

#### Verification gate

Run `/home/kensai/issue-test.sh` from the product root.

Pass criteria: this task's nine tests pass and appear among the passes; the 21 baseline failures are the only failures, under the same names (CP-15); exit 0. The nine tests fail before the change to `requests/models.py`.

---

### Task 2: Fence what must not change — CP-13 (`test_requests.py`)

**Dependencies:** Task 1 (uses the recording adapter Task 1 adds)

**What to build:** regression tests that pin the `Content-Length` every request outside CP-9 gets today, on both axes of the CP-13 predicate: method and body. They add no production code.

#### Behaviours to verify (developer adds tests to `test_requests.py`, in `RequestsTestCase`)

- `test_get_with_body_keeps_content_length` — Session `get(u, data='x')` has CL `'1'`; `data={'a': 'b'}` has CL `'3'` and the form `Content-Type`; `files={'f': <2 bytes>}` has CL equal to `len(body)`.
- `test_get_with_file_object_keeps_content_length` — `data=<empty temp file>` has CL `'0'`, and `data=<3-byte temp file>` has CL `'3'`.
- `test_get_with_empty_sequence_body_keeps_content_length_zero` — Session `get(u, data=[])` and `data=()` have CL `'0'`, and `Request('GET', u, data=None).prepare()` (body `[]`) has CL `'0'`.
- `test_bodiless_non_get_head_keeps_content_length_zero` — Session `post`, `put`, `patch`, `delete` and `options` with no body each have CL `'0'`, and `Request('PURGE', u).prepare()` (a non-standard method) has CL `'0'`. The `POST` case is CP-14's named minimum.
- `test_bodiless_post_with_auth_keeps_content_length_zero` — Session `post(u, auth=('u', 'p'))` has CL `'0'`. This fences the non-`GET`/`HEAD` side of the recompute in `prepare_auth`, which the design covers only by combining rows 6 and 12.

#### Implement

Tests cannot go red.

Reason: the subject is today's `prepare_content_length`, which already gives each of these requests the header these tests assert, and Task 1's change leaves every branch outside the `GET`/`HEAD` and `body is None` predicate as it was. These tests pass on the unchanged tree, so nobody claims to have watched them fail. They are real and must be asserted. Their job is to fail if Task 1's predicate is written too wide.

#### Verification gate

Run `/home/kensai/issue-test.sh` from the product root.

Pass criteria: this task's five tests pass and appear among the passes; the 21 baseline failures are the only failures, under the same names; exit 0. Run once more with Task 1's change to `requests/models.py` reverted: these five tests must still pass there (they are fences of today's behaviour), and Task 1's nine must fail.
