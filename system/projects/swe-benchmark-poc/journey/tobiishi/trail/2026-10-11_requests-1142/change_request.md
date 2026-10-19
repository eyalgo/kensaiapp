# Change request — 2026-10-11_requests-1142

**Request:** Fix the issue below in the product, the repository that the project card's
`Product path:` names (`psf/requests`). The repository stands at the commit before the issue was
fixed. Make the change the issue asks for, with tests of your own that show it, and leave the rest of
the product's behaviour as it is.

It is done when it is sealed. Nothing else is
asked of it: no record, no grade and no benchmark file. Bookkeeping is done outside
KensaiApp.

## The issue

*Not reproduced in this example.* The run was given the issue's title and body verbatim, as the benchmark SWE-bench Verified publishes them. That text is its author's, and the benchmark declares no licence for it, so this example links the issue and summarises it instead.

**The issue:** https://github.com/psf/requests/issues/1051

**In short:** Requests always adds a `Content-Length` header, even to a GET request with no body. Some servers reject such a request, and the issue asks that the header not be sent then.

## What must not be done

- **Do not look for the fix.** Work from this request and the repository you are given. Do not read
  the repository's history after this commit, its pull requests, its issue tracker, its later
  releases, or any copy of the SWE-bench benchmark
  (`system/projects/swe-benchmark-poc/doctrine/ai_responsibility.md` § 1.1). A patch made with any of
  them in view is not graded.
- **Do not delete anything outside the change** (same file, § 1.2).
- **Do not fix the product's other failing tests.** 21 tests fail before any change, in the environment the card's `Test command:` runs (================== 21 failed, 5 passed, 21 warnings in 1.03s ===================, at `base_commit`):

  - `test_requests.py::RequestsTestCase::test_BASICAUTH_TUPLE_HTTP_200_OK_GET`
  - `test_requests.py::RequestsTestCase::test_DIGESTAUTH_WRONG_HTTP_401_GET`
  - `test_requests.py::RequestsTestCase::test_DIGEST_HTTP_200_OK_GET`
  - `test_requests.py::RequestsTestCase::test_HTTP_200_OK_GET_ALTERNATIVE`
  - `test_requests.py::RequestsTestCase::test_HTTP_200_OK_GET_WITH_MIXED_PARAMS`
  - `test_requests.py::RequestsTestCase::test_HTTP_200_OK_GET_WITH_PARAMS`
  - `test_requests.py::RequestsTestCase::test_HTTP_200_OK_HEAD`
  - `test_requests.py::RequestsTestCase::test_HTTP_200_OK_PUT`
  - `test_requests.py::RequestsTestCase::test_HTTP_302_ALLOW_REDIRECT_GET`
  - `test_requests.py::RequestsTestCase::test_POSTBIN_GET_POST_FILES`
  - `test_requests.py::RequestsTestCase::test_POSTBIN_GET_POST_FILES_WITH_DATA`
  - `test_requests.py::RequestsTestCase::test_custom_content_type`
  - `test_requests.py::RequestsTestCase::test_decompress_gzip`
  - `test_requests.py::RequestsTestCase::test_different_encodings_dont_break_post`
  - `test_requests.py::RequestsTestCase::test_links`
  - `test_requests.py::RequestsTestCase::test_prepared_request_hook`
  - `test_requests.py::RequestsTestCase::test_request_ok_set`
  - `test_requests.py::RequestsTestCase::test_status_raising`
  - `test_requests.py::RequestsTestCase::test_unicode_get`
  - `test_requests.py::RequestsTestCase::test_urlencoded_get_query_multivalued_param`
  - `test_requests.py::RequestsTestCase::test_user_agent_transfers`

  Leave them failing. The card's `Test command:` knows them: it passes while they are the only failures, and fails on any other.

**Category:** bug
**Behaviour:** changing
**Classified because:** the issue reports behaviour the product gets wrong. Correcting it changes what
the product does, so Behaviour is `changing`, and the cause is a defect in existing behaviour, so
Category is `bug` (`<CORE>/doctrine/flow/change_classification.md`, the two axes). Where the issue
asks for a capability the product lacks rather than a defect, the specs step reclassifies it.

**Sealed:** 2026-10-11 — accepted; merged to `main` via `--no-ff`.
