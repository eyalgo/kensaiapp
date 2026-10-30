# Change Design — show non-text path bytes on an unreadable start

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the unreadable-data console line and the unreadable-data page

---

## 1. Change Summary

This blueprint places the display changes and their proof for `tracker17 · tobiishi · 2026-10-30_unreadable-start-non-text-path`. The requirements are `change_spec.md` § Rules, CP-757–CP-772.

Use the existing console path formatter in the unreadable announcement. Give the unreadable page its own path-field formatter before HTML escaping and UTF-8 encoding. Keep the original location at the claim, load and listener boundaries. Change no surrounding wording, route policy, shutdown behaviour or persistence operation, as CP-763–CP-764 require.

**Language resolution:** Python — step 1, `system/projects/tracker17/project.md` `Languages:`; packet `core/doctrine/engineering/languages/python/README.md`, with its layout, conventions, errors/logging and testing destinations read for this design.

Paths below beginning `main.py`, `web/`, `tests/` or `docs/` are relative to `products/tracker17/`.

---

## 2. Blast Radius

Placement follows `docs/SDD.md` § 3, *The parts, and the seams between them*, rows `main` and `web` (lines 220–248). Console field rendering belongs to the start-message owner. Page field rendering belongs to the whole-page owner. No new top-level part, shared formatting service or import edge is needed.

| Module | Status | What changes |
|---|---|---|
| `domain/` | Unchanged | No entity, refusal or data rule changes. |
| `application/` | Unchanged | No action, clock or saving-contract changes. |
| `persistence/` | Unchanged | Original location, load, save and lock paths stay untouched. |
| `web/` | Modified | Owning part: `web`. In `pages.py`, format only the unreadable page's location field, then pass it through the existing `_escape`. The unchanged `UnreadableSite` constructor receives the decoded location and can encode the resulting page. |
| `main.py` | Modified | Owning part: `main`. Make `_unreadable_line` use the existing `_shown_location` for its location field. Leave `_ready_line`, the conversion algorithm and start wiring as they are. |
| `errors.py` | Unchanged | No exception or error-base change. |
| `tests/` | Modified — supporting proof | Add focused console, page/site and real-start cases in § 5; retain existing regression assertions. |

The import check permits `main` to import `web` and forbids the reverse (`docs/nfdr.md` § 1.2, QC-16–QC-17, lines 196–204). The design needs neither a new public formatter nor a cross-part call. `web/__init__.py` exports stay unchanged.

The affected page call chain is `main._serve_claimed` → `listen_unreadable` → `UnreadableSite` → `pages.unreadable_data_page` (`main.py:129-144`, `_serve_claimed`; `web/listener.py:104-111`, `listen_unreadable`; `web/routes.py:1344-1346`, `UnreadableSite`). Its signatures and callers stay unchanged. No transitive caller modification is required under `docs/nfdr.md` § 1.2. The failed-action reporting site remains outside this delta, per `change_spec.md` § Out of Scope.

---

## 3. Sub-jobs

### Sub-job A — `main.py`: unreadable console location

**Scope:** Render the location field in `_unreadable_line` through `_shown_location`, without changing the other text or any start/lifetime operation. Include the console assertions and the start-side proof in § 5.

**Exposes:** Keep `_unreadable_line(host: str, port: int, location: Path) -> str` and `start(address: tuple[str, int], location: Path) -> int`. The line replaces each filename-decoding marker U+DC80–U+DCFF with its corresponding four-character lowercase byte escape, preserving every other character. `start` still supplies one absolute location for display, while the original `Path` reaches persistence.

**Depends on:** none. The formatter already belongs to `main.py` (`main.py`:164–183, `_shown_location` and `_ready_line`).

### Sub-job B — `web/`: unreadable page location

**Scope:** Format the location inside `pages.unreadable_data_page`, before `_escape`, using a private page-local helper if needed. Include the page/site assertions in § 5. Do not change the general `_escape` function or the routing and listener implementations.

**Exposes:** Keep `unreadable_data_page(location: str) -> str`, `UnreadableSite(location: str, own_host: str)` and `listen_unreadable(address: tuple[str, int], location: str) -> Listener`. A caller passes the original decoded location. Page construction itself replaces filename-decoding markers with the CP-760 escape form, then HTML-escapes that text through `_escape`. For supported decoded paths, `UnreadableSite` construction and its existing UTF-8 encoding succeed without caller preprocessing.

**Depends on:** none. B consumes no contract added by A. A consumes no contract added by B.

**Build sequence:** A and B have no ordering dependency and may proceed independently. The complete real-start capability requires both. No atomic-landing edge is imposed: neither public interface changes, and the existing ordinary-path assertions remain valid with either isolated delta. This is a structural judgement, not a suite result.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — unreadable console field | None |
| B — unreadable page field | Apply a field-local mapping of U+DC80–U+DCFF to lowercase byte escapes before the existing HTML escape. The existing `main._shown_location` is the shape reference, not an import target. Broad Unicode backslash replacement would spell a surrogate rather than the required byte; changing `_escape` would reach unrelated fields. |

The real-start proof uses the existing child-process pattern of `tests/integration/test_ready_start.py` (`START_PROGRAM`, `_Start`, `child_environment`). Pass path bytes losslessly to the child and decode them there. Each child calls real `main.start` with an ephemeral loopback port. Give every wait and request a deadline and clean up children on assertion failure. Set console encoding in the child's environment, without patching any product module. These are test-boundary constraints; no production seam is added.

---

## 5. Test Additions

Example numbers below mean the seventeen rows of `change_spec.md` § Examples, in their existing order. Expected text must come from CP-757–CP-763, not from either product formatter. Compare full ordinary-path representations to their pre-change expectations. No existing assertion is retired or weakened.

| Row | Sub-job | Test file | What to add / modify |
|---|---|---|---|
| T1 | A | `tests/unit/test_unreadable_message.py` — new | Build `_unreadable_line` with `Path(os.fsdecode(b'/tmp/caf\xe9/data'))`; assert the complete line, four literal escape characters, no replacement mark, no U+DC80–U+DCFF, no surrogate spelling, and successful strict UTF-8 encoding. CP-760, CP-765; Example 1. |
| T2 | B | `tests/integration/test_unreadable_path.py` — new | Construct `web.UnreadableSite` directly from the decoded original string and request `/` with valid host/request headers. Assert 503, the path in the decoded body, no replacement mark or filename marker, and strict UTF-8 page bytes. Also call the page builder directly to pin its field rendering. CP-759–CP-760, CP-766; Example 2. |
| T3 | A, B | `tests/integration/test_unreadable_start.py` — new | Real child start under strict UTF-8, using a location with the byte beneath a regular file. This case never skips. Assert its first stdout bytes are the full CP-757 line, read the port from that line, fetch the 503 page, send SIGINT, and assert status 0, no further stdout and empty stderr. Snapshot the regular file's bytes and its containing directory before/after. CP-757, CP-760, CP-764, CP-767, CP-771; Example 3. |
| T4 | A, B | T1–T3 files; failing-run evidence in the unit's implementation report | Record each of the three required proofs failing against the starting tree, and passing against the implementation. The real-start baseline fails before output with encoding failure/status 1. Keep this as run evidence, not a permanent test reading Git history. CP-762, CP-769; Example 4. |
| T5 | A, B | `tests/integration/test_unreadable_start.py` | Parameterize T3 for strict ASCII, C locale with coercion disabled, and Python UTF-8 mode, with inherited console variables removed. Use an ASCII fixture prefix plus decoded byte markers. Check identical ASCII escape bytes, empty stderr and clean shutdown. CP-762; Example 5. |
| T6 | B, with A's real start | `tests/integration/test_unreadable_path.py`; `tests/integration/test_unreadable_start.py` | On the decoded-byte location check `/people`, `/nothing?x=1`, root with a query and same-origin `POST /projects`: identical 503 page bodies for reads, `no-store` and the existing policy headers; stylesheet GET is 200; POST is 303 through the existing address builder. Assert no navigation or data controls. CP-758, CP-764; Example 6. Existing request-refusal tests remain untouched. |
| T7 | A, B | `tests/integration/test_unreadable_start.py` | Attempt a real byte-named directory in test-created storage, with unreadable `tracker.json`; prove the line/page, unchanged saved-file bytes and directory listing, and no directory with the literal escape spelling. Skip only this case on the actual filesystem refusal, reporting that refusal as the reason. Other setup failures fail the test. No OS-name condition and no skip of T3. CP-764, CP-768; Examples 7–8. |
| T8 | A, B | T1 and T2 files | Cover every filename-decoding marker including both endpoints, plus consecutive, separated, repeated and cross-component markers. Include the decoded `b'/tmp/a\xe9\xff/data'` example. Expected escapes are independently specified; preserve position and all surrounding text. CP-760–CP-761; Example 9 and the rules' byte-domain edges. |
| T9 | B | `tests/integration/test_unreadable_path.py` | Mix a marker with `<`, `&`, `"` and valid non-ASCII text. Parse the page and assert literal text, no injected element, and raw HTML escaping through `_escape`. CP-761; Example 10. |
| T10 | A, B | T1 and T2 files | Valid `/tmp/café/data`, plain ASCII and a literal-backslash name `a\xe9b` keep their complete line/page representations. Check non-filename surrogates just below/above the range and a high surrogate: the line keeps them and the site's UTF-8 encoding still raises, as the scope fence requires. CP-761, CP-763; Examples 11–12, 14 and § Out of Scope. |
| T11 | A, B | `tests/integration/test_unreadable_start.py` | A real relative unreadable location containing the byte is shown as one absolute path in the line and page. Verify no directory with the escaped spelling is created. Direct field formatters do not resolve or rewrite paths. CP-761, CP-764; Example 13. |
| T12 | A, B | Existing `tests/integration/test_start.py`, `test_unreadable_pages.py`, `test_unreadable_routes.py`, `test_single_tracker.py`, `test_location_use.py`, `test_saved_data.py`; `tests/unit/test_address.py`, `test_start_message.py`; `tests/integration/test_ready_start.py`; `tests/e2e/test_unreadable_data.py` | Run unchanged: ordinary-path wording and page bytes, controls, claim/load/save location, second-start refusal, lock and saved-data preservation, ready start, and the browser's first-output contract. In particular retain `test_the_browser_opens_the_unreadable_page_without_controls`. CP-763–CP-764, CP-771; Examples 14–15. |
| T13 | A, B | Existing `tests/architecture/test_imports.py`, `test_reach.py`, `test_trace.py`; every new test module | Preserve the existing architecture checks. New modules name their SRS/CP/QC coverage and patch no product module. No new import of `main` in production, console writer or production OS check. CP-770, CP-772; Example 16. |
| T14 | A, B | Full existing suite and quality gates | Ruff format, Ruff lint and mypy at NFDR QC-62's commands, through the locked product environment; both invocations of the project card's `Test command:`. CP-772; Example 17. |

**Rule-edge pass:** CP-757/CP-767/CP-771 → T3, T5, T11; CP-758 → T2, T6, T12; CP-759/CP-766 → T2; CP-760–CP-761 → T1–T2, T8–T11; CP-762 → T4–T5; CP-763 → T10, T12; CP-764 → T3, T6–T7, T11–T12; CP-765 → T1; CP-768 → T7; CP-769 → T4; CP-770 → T13; CP-772 → T13–T14. The valid character an ASCII console cannot encode and the failed-action message remain outside the change, per `change_spec.md` § Out of Scope.

---

## Records this change makes false

None — reviewed `docs/adr/README.md` and the records' statuses, Accepted ADR-0001, ADR-0013, ADR-0014 and ADR-0016 for the touched boundaries; `docs/nfdr.md` §§ 1–3, QC-40–QC-45, QC-51, QC-55, QC-60–QC-62 and RN-33; `docs/fdr.md` R-2, R-16, R-24–R-27; and `docs/SDD.md` § 3. The design adds no part or forbidden import and implements the existing location-display contract. No product record is edited.

---

## Architect Review Notes

All design decisions below are the architect's, 2026-10-30.

- **Field-local conversion, kind (b):** Realize CP-759–CP-761 at each display owner, rather than preprocessing the location in `_serve_claimed`. This makes direct `UnreadableSite` construction work by construction and keeps the original persistence location intact. The page maps markers before `_escape`, and before the encoding at `web/routes.py`:1346. Only the new page-local conversion parallels the console helper. This bounded duplication avoids exporting presentation machinery across owners or adding a sixth part for two fields. The placement is covered by the `main` and `web` rows of `docs/SDD.md` § 3; no kind-(e) ownership exception is needed.
- **Absolute-path boundary, kind (b):** Keep absolute-path construction in the real start, where `main.py:124-130`, `_serve_claimed`, already computes it. The field formatters preserve their arguments apart from the CP-760 markers. This preserves the direct page builder's plain-string contract and proves the relative-path requirement at T11's start boundary.
- **Spec reading:** No spec line is set aside. The regular-file proof and filesystem-refusal-only skip follow `change_spec.md` § Locked Answers, Gaps 1–2, without adding a product test hook.
- **QC-5 gate — not triggered:** No refusal type or refusal-handling path is changed. The target functions are `_unreadable_line` and `unreadable_data_page` (`main.py`:187–192; `web/pages.py`:2647–2661), rather than the action-refusal handlers named by `docs/nfdr.md` QC-5.
- **QC-8, QC-12, QC-23, QC-24, QC-27 — pass for this design:** Conversion is a pure field rendering operation. No new retained state, data rule, filesystem/clock reach, part or dependency is introduced. Page code remains replaceable with `web` and its composition wiring, per `docs/nfdr.md` §§ 1.1, 1.3–1.4. Gates conditional on changing `domain`, `application`, persistence, the saving contract or saved fields are not triggered.
- **QC-36 — pass for this design:** The formatted location still enters the page through the one existing `_escape` function (`web/pages.py`:452–454, 2656). No separate HTML builder or global escape change is permitted by § 3 B. T9 covers markup beside a byte marker.
- **QC-41 — pass for this design:** Only the already-required saved-data location is displayed. No credential, account or secret is introduced; the review boundary is `docs/nfdr.md` QC-41.
- **QC-60 — pass by review, not an interpreter run:** The design adds no language or library feature beyond the existing character mapping in `main.py` `_shown_location` and the existing page escaping/encoding calls. It adds no dependency or OS branch. This satisfies the feature-review gate in `docs/nfdr.md` QC-60 without claiming a Python 3.11 suite run.
- **QC-40, locked packages — reviewed:** The reviewed third-party pairs are the sixteen entries in `uv.lock:10-486` excluding the local `tracker17` package. The exact query below exited 0 with empty output, meaning no matching advisory rows. GitHub defines the feed and parameters at https://docs.github.com/en/rest/security-advisories/global-advisories?apiVersion=2022-11-28, *List global security advisories*. No pin or lock-format selection is part of this design.

  ```sh
  gh api --method GET advisories -f ecosystem=pip -f severity=critical -f 'affects=ast-serialize@0.12.1,colorama@0.4.6,greenlet@3.5.6,iniconfig@2.3.1,librt@0.16.0,mypy@2.4.0,mypy-extensions@1.1.0,packaging@26.3,pathspec@1.1.1,playwright@1.63.0,pluggy@1.6.0,pyee@13.0.1,pygments@2.21.0,pytest@9.1.1,ruff@0.16.10,typing-extensions@4.16.0' -f per_page=100 --paginate --jq '.[] | {ghsa_id,severity,published_at,withdrawn_at,html_url,vulnerabilities}'
  ```

- **QC-40, browser — pass under the existing exception:** `'<home>/Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing' --version` returned `Google Chrome for Testing 153.0.8010.12`. Google's October security releases name later desktop builds and critical fixes (https://chromereleases.googleblog.com/2026/10/, *Stable Channel Update for Desktop*, 2026-10-29). The applicable authority is `docs/nfdr.md:1104-1112`, RN-33, the owner's dated exception for this exact build through 2026-11-07. Verdict: the browser does not block this review on 2026-10-30. No pin change or renewed exception is made.
- **QC-40, repository feed — down, return check remains owed:** The admin permission query returned `{"admin":true}`. The Dependabot alerts query returned HTTP 403, `Dependabot alerts are disabled for this repository.` The asynchronous dependency-report request returned HTTP 404, `Not Found`. These are the outcomes `docs/nfdr.md` QC-40 (lines 404–415) explicitly treats as a down feed with its return check still owed. The matching entry is appended to `deferred_decisions.md`; no discrepancy in the record is raised.
- **Cold read:** All seventeen Examples map to T1–T14, and the separate rule-edge pass accounts for CP-757–CP-772. Public signatures, allowed imports, record corrections, text places and writes are settled in §§ 2–5. There is no write into another repository. This review runs no product acceptance suite, per `core/roles/loaders/architect_global.md` § *Verification is not yours to call*.
