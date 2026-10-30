# Change Design — explain the third start announcement

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the setup instructions’ “What the start prints” section

---

## 1. Change Summary

This blueprint scopes one README passage and maps its acceptance checks for `tracker17 · tobiishi · 2026-10-30_what-the-start-prints`.
Add the unreadable-data announcement to `products/tracker17/README.md` under “What the start prints”, following `change_spec.md:24-45`, “Rules”.
Keep wording ownership with `change_text.md`; this design fixes no new published sentence.

The program already selects the ready or unreadable-data announcement before serving (`products/tracker17/main.py:121-141`, `_serve_claimed`).
Its third announcement is `_unreadable_line` (`products/tracker17/main.py:168-173`).
The document changes what the reader learns; no runtime logic, signature, schema or import changes are needed (`change_spec.md:43-45`, “What stays as it is”).

## 2. Blast Radius

The parts table assigns startup messages to `main`, not setup prose (`products/tracker17/docs/SDD.md:211-238`, “The parts, and the seams between them”).
There is no new executable logic to place in a part.
The single delta is the README section; the table also accounts for every module in `products/tracker17/docs/nfdr.md:180-211`, “Forbidden imports”.

| Module or artifact | Status | What changes |
|---|---|---|
| `products/tracker17/README.md` | Modified | Only “What the start prints”; obligations are `change_spec.md:24-45`, CP-736–CP-746. |
| `domain/` | Unchanged | No rule changes; `change_spec.md:43-44`, CP-744–CP-745. |
| `application/` | Unchanged | No action changes; `change_spec.md:44`, CP-745. |
| `persistence/` | Unchanged | No saved-data or lock changes; `change_spec.md:44`, CP-745. |
| `web/` | Unchanged | No page or listener changes; `change_spec.md:44`, CP-745. |
| `main.py` | Unchanged | Announcement builders and startup stay as written; `change_spec.md:98`, “Out of Scope”. |
| `errors.py` | Unchanged | No error changes; `change_spec.md:44`, CP-745. |
| `tests/`, `pyproject.toml`, `uv.lock`, product `docs/` | Unchanged | No product-file edit beyond the README; `change_spec.md:44,98-102`, CP-745 and “Out of Scope”. |

No transitive blast radius: no public interface changes, and no import edge changes (`change_spec.md:44`, CP-745).
No write outside the instance/product worktree is required.

## 4. Code Strategy

The product delta changes one document, with no internal dependency edge requiring sub-jobs.

| Sub-job / change | Hint |
|---|---|
| README — “What the start prints” | None |

## 5. Test Additions

No test additions or modifications: `change_spec.md:98-102`, “Out of Scope”, excludes them.
Use the following review and command checks for the prose delta.
Each row maps one Example, in order, from `change_spec.md:49-65`, “Examples”.
“Test file” names the reviewed artifact where no test is written.

| Check / single delta | Test file or review target | What to verify |
|---|---|---|
| V1 — Example 1 | README section; command below | Before editing, the CP-736 check prints `0`; grep exits 1 for no match. This run observed that output. |
| V2 — Example 2 | README section; same command | After editing, CP-736 prints at least `1`; grep exits 0. |
| V3 — Example 3 | README section; `main.py`, `_unreadable_line` | CP-737: check the straight apostrophe and exact prefix. If more is quoted, compare it word for word with the builder, substituting only the example location. |
| V4 — Example 4 | README section alone | CP-737–CP-739, CP-742: the named line means saved data couldn't be read and the tracker keeps running until stopped. The next step names `Setting saved data aside` exactly, conditional on starting fresh on purpose. |
| V5 — Example 5 | README section alone | CP-740, CP-742: the ready example remains, the example location is explained, and opening the address shows Projects only for this case. The ready line means running. |
| V6 — Example 6 | README section alone | CP-741–CP-742: a refused second start has stopped; the line gives its reason and next action. The passage never says the earlier tracker stopped. |
| V7 — Example 7 | README section alone | CP-741, CP-743: the same failed-start description covers a held address without adding a separate explanation for each refusal reason. |
| V8 — Example 8 | README section alone | CP-742: the keep-running statement and Ctrl-C apply explicitly to the ready and unreadable-data cases. They must not instruct the reader to stop a refused start. |
| V9 — Example 9 | README section alone | CP-743: no claim excludes other terminal output. Add no discussion of tracebacks or unexpected serving failures. |
| V10 — Example 10 | README, “Starting the tracker again” | CP-744: compare the named passage byte for byte with the pre-edit version; no difference. |
| V11 — Example 11 | Product diff against the pre-edit commit | CP-745: only `products/tracker17/README.md` differs. Its prefix through the target heading and its suffix beginning at the next `### ` heading remain byte-identical. |
| V12 — Example 12 | Existing `tests/` and `tests/e2e/` | CP-745: both commands below exit 0, without altering tests, dependencies or the lock. |
| V13 — Example 13 | Every new sentence in the section | CP-746: at most 20 words per authored sentence; verbatim program quotations are exempt. Check “terminal”, “saved data” and contracted negatives against `products/tracker17/docs/CONTENT.md`, “Grammar and mechanics” and “Terminology”. |

The section-only presence check, run from the instance worktree root:

```sh
awk '/^### What the start prints/{f=1;next} /^### /{f=0} f' products/tracker17/README.md | grep -cF "The tracker couldn't read"
```

The unchanged regression commands required by `change_spec.md:44`, CP-745:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/
uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/
```

Rule pass beyond the Examples:

- CP-736’s section boundary and fixed-string case are covered by V1–V2; a match elsewhere in the README does not satisfy V2.
- CP-737’s minimum prefix and optional longer quote are covered by V3; no full-line quotation is required.
- CP-738’s until-stopped condition is covered by V4 and V8.
- CP-739’s conditional next action and exact heading are covered by V4. Also check that the new prose claims no loss, deletion, corruption or damage.
- CP-740’s location substitution and Projects-only-for-ready restriction are covered by V5.
- CP-741’s two refusal reasons and preservation of an earlier running tracker are covered by V6–V7.
- CP-742’s isolated reading and the scope of Ctrl-C are covered by V4–V8.
- CP-743’s other output, including unexpected serving failure, is covered by V9. If a count is used, it counts announcement kinds and treats both failed-start reasons as one kind.
- CP-744’s protected passage and CP-745’s other sections and files are covered by V10–V12.
- CP-746’s quotation exception, terminology and contractions are covered by V3 and V13.

No existing assertion is retired.
The current tests pin the unreadable announcement and serving lifetime (`products/tracker17/tests/integration/test_start.py:242-262`, `test_an_unreadable_start_serves_one_page_and_announces_once`).
They also pin the earlier tracker’s survival after refusal (`products/tracker17/tests/integration/test_single_tracker.py:300-312`, `test_second_tracker_is_refused_without_changing_the_first`).
Retain these tests unchanged alongside the ready and unreadable stop checks (`products/tracker17/tests/integration/test_start_stop.py:396-410,630-665`, `test_real_start_stops_at_the_completed_ready_write` and `test_unreadable_start_stops_quietly_and_releases_its_location`).

## Records this change makes false

None — read `products/tracker17/docs/fdr.md`, “Starting and reaching the tracker”, “The written setup instructions” and “Saved data”; `products/tracker17/docs/nfdr.md`, §§ 1–9 and the applicable Review Notes; `products/tracker17/docs/SDD.md` § 3; and `products/tracker17/docs/adr/`, its index and applicable accepted decisions.
The README delta changes no statement in those records.
QC-40’s unmet package-feed obligation is carried in `deferred_decisions.md`; the change does not make it false.

## Architect Review Notes

Decisions and reviews below are the architect’s, 2026-10-30.

- **Explicit running-case scope (b):** Realize CP-742 through wording that identifies both running cases in the keep-running and stop instruction’s scope. Do not rely on sentence proximity to imply that scope. The reason is the reader-only distinction required by `change_spec.md:38`, CP-742. Placement and exact wording remain unfixed.
- **Document checks in § 5 (d):** Use review targets and command checks rather than new automated tests. `change_spec.md:98-102`, “Out of Scope”, excludes test changes. No spec line is set aside and no existing assertion is removed.
- **Parts placement:** The SDD has a parts table, but this change adds prose rather than executable logic. Keep all startup logic in `main.py` as assigned by `products/tracker17/docs/SDD.md:211-238`, § 3. No extra part or import is justified.
- **Delegated structural reviews:** Pass QC-12 and QC-41: the scoped delta adds no code part, account, credential or secret (`change_spec.md:43-45`, CP-744–CP-746). QC-5, QC-8, QC-20–QC-27, QC-36, QC-46 and QC-60 have no affected executable seam, field, page-building or language feature. These triggers are in `products/tracker17/docs/nfdr.md:55-65,96-100,217-280,346-352,480-486,567-576`. The sweep `rg -n development-design products/tracker17/docs/adr/` returned no matches.
- **Language resolution:** Python, step 1, `system/projects/tracker17/project.md`, `Languages:`; opened `<CORE>/doctrine/engineering/languages/python/README.md`. No language-level change is designed.
- **QC-40 packages:** On 2026-10-30, query GitHub’s public advisory API once for each registry package/version in `products/tracker17/uv.lock`: `gh api --method GET /advisories -f ecosystem=pip -f severity=critical -f affects=<name>@<version> -f per_page=100`. All 16 queries returned empty lists. This is a point-in-time critical-advisory reading, not a claim that packages have no vulnerabilities; endpoint: https://api.github.com/advisories.
- **QC-40 browser:** The worktree’s installed Playwright Chromium executable reported `Google Chrome for Testing 153.0.8010.12` via `--version`. Microsoft’s pinned browser manifest agrees: https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/packages/playwright-core/browsers.json. Google’s 2026-10-20 and 2026-10-27 desktop security releases list newer critical fixes: https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_02018666648.html and https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_0562499947.html. Treat the installed build as behind those releases, not as cleared of advisories. It does not block this review under the owner’s build-specific exception through 2026-11-07 (`products/tracker17/docs/nfdr.md:1104-1116`, RN-33). No pin moves.
- **QC-40 feed:** `gh api repos/kensaiapp/<the instance KensaiApp is developed in> --jq '{full_name,permissions,security_and_analysis}'` returned `permissions.admin: true`. The alerts read returned HTTP 403 with `Dependabot alerts are disabled for this repository`; `gh api repos/kensaiapp/<the instance KensaiApp is developed in>/dependency-graph/sbom/generate-report` returned HTTP 404. Verdict: feed down, graph-listing moment still owed, no discrepancy, per `products/tracker17/docs/nfdr.md:403-415`, QC-40. `deferred_decisions.md` carries that obligation without expanding this README change.
