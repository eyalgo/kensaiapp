# Change Design — readable starts display non-text path bytes

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the saved-data location in the console's ready message

Owns the structural delta for `tracker17 · tobiishi · 2026-10-30_ready-start-non-text-path`.
The behavioural contract is `change_spec.md` beside this file, CP-747 to CP-756.
Product paths below are relative to `products/tracker17/` unless written in full.

---

## 1. Change Summary

Keep the change in `main.py`: render the location for the readable start's ready message before
the console encodes it, while leaving the filesystem location itself intact. The composition root
owns start messages (SDD `docs/SDD.md:L226-L226`), and the existing readable branch selects
`_ready_line` before the shared announcement writes it (`main.py:L121-L141`). The resulting
message meets CP-747 to CP-751 without changing how the tracker claims, loads, binds, serves or
stops (`change_spec.md:L21-L31`).

---

## 2. Blast Radius

Placement follows `docs/SDD.md` § 3 (`docs/SDD.md:L220-L236`); import constraints follow
`docs/nfdr.md` § 1.2 (`docs/nfdr.md:L180-L211`).

| Module | Status | What changes |
|---|---|---|
| `main.py` | Modified | Owning part: `main`. Add display-only rendering of filename-decoding surrogate escapes within the readable ready-message path field. Keep `_ready_line`'s inputs and string result, and the public `start` and `main` signatures. |
| `domain/` | Unchanged | No data rule or state change. |
| `application/` | Unchanged | No action, saver or clock contract change. |
| `persistence/` | Unchanged | Preserve the original `Path` for claiming, loading and saving; no display escaping reaches filesystem operations. |
| `web/` | Unchanged | No listener, page, route or failed-action message change. |
| `errors.py` | Unchanged | No error type change. |

Test support: add `tests/unit/test_start_message.py` and
`tests/integration/test_ready_start.py`; leave existing ready-message tests untouched (CP-751).
No transitive blast radius: no product module may import `main`, and no interface crossing to
another part changes (`docs/nfdr.md:L39-L43`; `main.py:L103-L104`, `main.py:L161-L178`).

**Single delta.** One production module changes, with no independent internal contract or ordering
edge requiring sub-jobs. The ready-message rendering remains private to `main.py`.

**Boundary contract.** At `_ready_line`, render the existing location's text without changing its
absolute-path calculation at the caller. Transform only the surrogate code points Python uses
for undecodable filename bytes into the corresponding lowercase, two-digit byte escapes. Preserve
every other character, in order, including valid non-ASCII text and literal backslashes; this
implements CP-748 to CP-751 explicitly rather than depending on stdout's error policy
(`change_spec.md:L25-L31`; `main.py:L123-L139`). Python documents those surrogate escapes as
U+DC80 through U+DCFF, each representing its original byte
([Python 3.11 codecs](https://docs.python.org/3.11/library/codecs.html#error-handlers)).

Keep the existing ready-message wording, address-before-location order, one flushed write and
stop lifecycle. Apply the rendering only to the ready path field; keep the unreadable message and
page, address refusal, second-tracker refusal and failed-action output within the request's
unchanged boundary (`change_request.md` § Request; `main.py:L113-L178`).

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `main.py` — readable ready-message path | Walk the path's decoded text in order. Recognize only Python's filename-decoding surrogate-escape range, recover each represented byte, and emit its lowercase two-digit escape. Copy other characters verbatim. This is display formatting at `_ready_line`, independent of the console encoding; do not reconfigure stdout, catch a failed write as the rendering strategy, or escape the entire path as a Python literal. See [Python 3.11 codecs](https://docs.python.org/3.11/library/codecs.html#error-handlers) and CP-748 to CP-751. |

The change writes only into its own instance/product worktree; no write into another repository
is part of this design.

---

## 5. Test Additions

Rows T1 to T9 identify coverage, not implementation tasks. Example numbers below count the rows
in `change_spec.md` § Examples (`change_spec.md:L47-L56`).

| Sub-job | Test file | What to add / modify |
|---|---|---|
| T1 — `main.py`, real readable start | New `tests/integration/test_ready_start.py` | Start the existing two-argument `main.start` in a real child on a test-owned missing location decoded from bytes containing `0xe9`. Set `PYTHONIOENCODING=utf-8:strict` explicitly. Capture raw stdout/stderr, require the whole first line with the literal four-character escape, extract the actual bound address from that line, and request `GET /` there: status 200 and the empty tracker's page. Send SIGINT; require exit 0, no further stdout and empty stderr. No skip for this missing-data case. Covers Example 1 and CP-747, CP-748, CP-752, CP-755. |
| T2 — baseline proof | T1's strict missing-data case | Run this new case against the unchanged production code before implementing the rendering. Its failure must expose the child's `UnicodeEncodeError`, empty stdout and status 1, rather than merely timing out. Keep the case asserting success after the fix. Covers Example 2 and CP-752. This is a one-time red observation; commit no test that reads an old Git commit or the primary checkout. |
| T3 — valid saved data and filesystem refusal | New `tests/integration/test_ready_start.py` | Parameterize the same real-start proof for a valid `tracker.json` containing a named project. Attempt to create the byte-bearing directory in the test's temporary tree. If the filesystem refuses that name, report this parameter as skipped with the actual refusal; do not select by OS, and let unrelated setup errors fail. Otherwise require the same exact ready line, the saved project visible at the printed address, quiet exit 0 and unchanged saved bytes. Covers Examples 3 and 4, CP-747 and CP-753. |
| T4 — all represented bytes and positions | New `tests/unit/test_start_message.py` | Exercise the existing ready-line formatter with every filename-decoding surrogate marker, including both ends of U+DC80–U+DCFF, verifying the corresponding lowercase byte escape. Include consecutive and separated markers, different path components, and mixtures of markers, valid Unicode and literal backslashes. Expected output is independent fixture text, not the production renderer's output. Covers Example 5, CP-748 and CP-749. |
| T5 — console independence | New `tests/integration/test_ready_start.py` | Repeat the missing-data start for strict ASCII, the C locale and Python UTF-8 mode; also start on a path containing consecutive bytes `0xe9` and `0xff`. Explicitly remove inherited `PYTHONIOENCODING` for the non-strict variants and control the child's locale/mode variables. Assert raw bytes equal the same escaped ready line, with no raw non-text byte, surrogate spelling or replacement mark; also require HTTP 200 and quiet stop as T1 does. Covers Examples 5 and 6, CP-748, CP-750 and CP-754. |
| T6 — ordinary path continuity | Both new test files | Cover plain text, valid UTF-8 `café`, and the literal folder name `a\xe9b` as three distinct fixtures. On a strict UTF-8 console, assert the entire ready line's bytes, including real UTF-8 for `é` and the original backslash. A mixed valid-Unicode/non-text-byte fixture ensures escaping one byte does not escape valid text elsewhere. Covers Examples 7 to 9, CP-749 and CP-751. |
| T7 — existing first-output proof | Existing `tests/e2e/test_first_project.py::test_the_first_output_is_the_ready_message_address_before_location` | Run unchanged as the layer-5 QC-55 proof, alongside the new exact-first-line assertions in T1, T3, T5 and T6. Covers CP-755. |
| T8 — existing start contracts | Existing `tests/integration/test_start.py`, `tests/integration/test_start_stop.py`, `tests/unit/test_start_lifecycle.py` | Run unchanged: normal ready lines, unreadable starts, refused starts, location release and quiet SIGINT lifetime retain their existing assertions. No assertion is retired or weakened. Covers the retained contracts of CP-747 and CP-751 and the request's scope boundary. |
| T9 — product gates | Existing architecture tests and project test command | Run QC-61's no-OS-check coverage, Ruff format and lint, mypy over `main.py errors.py domain application persistence web`, and both suites through the project's locked environment. Covers Example 10 and CP-756; exact suite command remains owned by `system/projects/tracker17/project.md` § Test command, and quality commands by `docs/nfdr.md:L576-L593`. |

**Rule-implied edges.** CP-747's two readable states are T1/T3; first-and-only stdout, no stderr,
serving the printed address and quiet stop are asserted together in T1/T3/T5. CP-748/CP-749's
several bytes, lowercase hex, range endpoints and arbitrary placement are T4, with a real
multi-byte-path start also in T5. CP-750's strict/non-strict split is T1/T5. CP-751's real
backslash and valid character are T6, and existing assertions are retained by T7/T8. CP-753's
filesystem refusal is T3, not a skip of T1. CP-755/CP-756 are T7/T9. Every Example maps above;
no existing assertion is removed.

**Harness boundary.** Use temporary directories and a free loopback port, pass the original path
to the child, and enter through the unchanged `main.start`; patch no product name. Use deadlines
for line reads, HTTP, shutdown and failure cleanup, and reap every child. Derive fixture paths
from the test's temporary directory, never a literal shared `/tmp/caf` tree. The existing
real-start harness demonstrates these process boundaries
(`tests/integration/test_start.py:L74-L215`), and the session's signal fixture supplies an
interruptible parent (`tests/conftest.py:L62-L82`). New helpers may remain local to the new test
module, so no existing harness signature or assertion needs changing.

---

## Records this change makes false

None — read the decision index and the Accepted decisions in `docs/adr/`, `docs/nfdr.md` §§ 1–9,
`docs/fdr.md` §§ Starting and reaching the tracker / Saved data, and `docs/SDD.md` § 3 and OB-2.
The delta retains their module set, import direction, filesystem and lifetime contracts and
fulfills the ready message's existing location obligation (`docs/SDD.md:L220-L260`,
`docs/SDD.md:L570-L577`; `docs/fdr.md:L40-L42`, `docs/fdr.md:L101-L103`).
The package-feed review moment still owed under QC-40 is recorded in `deferred_decisions.md`
beside this file; it is an unmet obligation, not a sentence this delta makes false.

---

## Architect Review Notes

- **Placement and construction (b):** Keep the display transform inside the `main` part, at the
  readable ready-line formatter. The parts table assigns start messages there; the existing
  branch-specific formatter allows changing this message without transforming the filesystem
  path or the unreadable page (`docs/SDD.md:L226-L226`; `main.py:L121-L141`, `main.py:L161-L173`).
  The surrogate-range choice realizes CP-749 using the decoder's own markers rather than a
  hardcoded list of invalid bytes or the console's error handler
  ([Python 3.11 codecs](https://docs.python.org/3.11/library/codecs.html#error-handlers)).
- **Text verdict (b):** `yes`: the operator reads a changed path representation in the console's
  ready message, even though its surrounding wording stays fixed (CP-747/CP-748;
  `change_spec.md:L21-L27`). The text surface is only that message's location field.
- **Classification and readings:** Copy `feature` / `changing` verbatim from
  `change_spec.md:L4-L5`. No spec line is set aside. CP-750 applies to the non-text-byte form;
  the explicit exclusion for a valid character an ASCII console cannot encode remains in force
  (`change_spec.md` § Out of Scope). Do not broaden the renderer to escape all non-ASCII text.
- **QC-12 / QC-24 review — pass:** No new production part, dependency, data rule, page or file
  format is introduced; the only production responsibility is ready-message display in `main`
  (§§ 2 and 4; `docs/nfdr.md:L173-L178`, `docs/nfdr.md:L260-L263`).
- **QC-41 review — pass:** The design introduces no secret, account, credential or secret-bearing
  field (§§ 2 and 4; `docs/nfdr.md:L423-L427`).
- **QC-60 review — pass for the proposed approach:** The proposed character inspection and
  formatting, filename decoding and child-process APIs are available at the Python 3.11 floor
  ([codecs](https://docs.python.org/3.11/library/codecs.html#error-handlers),
  [os.fsdecode](https://docs.python.org/3.11/library/os.html#os.fsdecode),
  [built-ins](https://docs.python.org/3.11/library/functions.html),
  [subprocess](https://docs.python.org/3.11/library/subprocess.html)). Language resolution is
  Python, step 1 (`system/projects/tracker17/project.md` § Languages), using
  `<CORE>/doctrine/engineering/languages/python/README.md`. This review makes no claim of a
  Python 3.11 suite run.
- **Other delegated gates:** QC-5, QC-8, QC-20 to QC-23, QC-25 to QC-27, QC-36 and QC-46 have no
  touched responsibility: no refusal handling, inner-part code, saving contract, web code, page
  building or saved field changes (§ 2; delegated conditions in `docs/nfdr.md` §§ 1–4).
- **QC-40 package review — 2026-10-30:** Query every non-product package/version in the committed
  `uv.lock` against GitHub's published advisory API. Actual result: all 16 returned `[]`, so no
  matching critical advisory was returned. The checked pairs are ast-serialize 0.12.1, colorama
  0.4.6, greenlet 3.5.6, iniconfig 2.3.1, librt 0.16.0, mypy 2.4.0, mypy-extensions 1.1.0,
  packaging 26.3, pathspec 1.1.1, playwright 1.63.0, pluggy 1.6.0, pyee 13.0.1, pygments 2.21.0,
  pytest 9.1.1, ruff 0.16.10 and typing-extensions 4.16.0. Check: for each pair,
  `gh api --method GET /advisories -f ecosystem=pip -f affects=<name>@<version> -f per_page=100 --paginate`
  returned `[]`. No pin or lock-format change is proposed.
- **QC-40 browser review — exception applies:** The installed Playwright manifest names Chromium
  153.0.8010.12, revision 1243; invoking that executable with `--version` returned status 0 and
  `Google Chrome for Testing 153.0.8010.12`. Google's
  [2026-09-08 security release](https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0808145027.html)
  fixes Critical issues in 153.0.8010.36/.37, later than this build; the
  [2026-10-29 release](https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_02107719452.html)
  publishes further security fixes. Do not call this browser clean: NFDR RN-33's owner's exception
  covers this exact build through 2026-11-07, so it does not block this 2026-10-30 review
  (`docs/nfdr.md:L1103-L1116`).
- **QC-40 feed review — down; graph moment still owed:**
  `gh api repos/<owner>/<repository> --jq '{permissions: .permissions, security_and_analysis: .security_and_analysis}'`
  returned `permissions.admin: true`. The repository's Dependabot alerts request returned HTTP 403,
  `Dependabot alerts are disabled for this repository.` The read of
  `repos/<owner>/<repository>/dependency-graph/sbom/exports` returned HTTP 404, `Not Found`.
  This matches QC-40's documented down-feed case, with no new discrepancy; the graph-listing
  moment remains owed (`docs/nfdr.md:L399-L418`; `deferred_decisions.md` beside this file).

**Cold-read:** All six production modules are accounted for, the one new display responsibility
has an owner, and no cross-part contract or build-order edge changes (§ 2). T1–T9 cover every
Example and rule-implied edge (§ 5). The path form is explicit before console encoding (§ 4),
the text verdict is settled, and the record and delegated-review results are stated above.
