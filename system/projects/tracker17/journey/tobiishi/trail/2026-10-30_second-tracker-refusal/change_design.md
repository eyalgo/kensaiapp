# Change Design — a second tracker on the same saved data is refused

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the terminal's second-start refusal and the README's setup instructions

---

## 1. Change Summary

This blueprint owns the lock's placement, its lifetime across startup and serving, and the tests for
`tracker17 · tobiishi · 2026-10-30_second-tracker-refusal`.
It implements `change_spec.md:21-46`, § Rules, CP-693–CP-709: persistence claims the saved-data
directory before loading it, and the start command turns proven contention into the fixed refusal.
The claim lasts through listener closure, independently of saves.

The design adds `persistence/location_use.py` and wires its lifetime into `main.py`.
The README passage belongs under “Starting the tracker again”.
The location may be an empty directory before the first save, as CP-703 permits
(`change_spec.md:37`, § What stays as it is).
The saved-file format, action flow, page building and command arguments stay unchanged.

**Language resolution:** Python — step 1, `system/projects/tracker17/project.md`, `Languages:`;
packet: `<CORE>/doctrine/engineering/languages/python/README.md`, § The seven concerns and where each
is answered.
The artifact belongs beside the spec under the change's folder, per
`<CORE>/doctrine/setup/kensaiapp_structure.md:2201-2207`, § 2, `journey/tobiishi/<key>/`.

Product paths below are relative to `products/tracker17/`.
`change_spec.md`, `change_request.md` and `deferred_decisions.md` name files beside this design.

---

## 2. Blast Radius

Placement follows `docs/SDD.md:212-218`, § 3, The parts: persistence owns the location lock and main
owns wiring and start messages.
The module set and permitted edges come from `docs/nfdr.md:166-196`, § 1.2, QC-13–QC-19.

| Module | Status | What changes |
|---|---|---|
| `persistence/` | Modified | Owning part: persistence. Add `location_use.py` for acquisition, directory identity, contention classification, ownership lifetime and startup rollback. Add public re-exports in `__init__.py`. Leave `SavedData.load`, `SavedData.save` and their format alone. |
| `main.py` | Modified | Owning part: main. Enter the location claim before loading, handle its typed contention signal, mark successful listener creation, and retain the claim until listener closure. Keep `start(address, location)`, `main(argv)`, `serve_until_stopped` and the SIGINT policy's public contracts. |
| `domain/` | Unchanged | No data rule, entity, refusal for an operator action, or saved field changes. |
| `application/` | Unchanged | No saving protocol or action changes. The saver remains `SavedData`. |
| `web/` | Unchanged | No listener interface, address, route or page changes. |
| `errors.py` | Unchanged | The new persistence signal derives from its existing `AppError`. |

Supporting files: add `tests/integration/test_location_use.py` and
`tests/integration/test_single_tracker.py`; extend `tests/integration/test_start.py` where needed;
replace only CP-703's named assertion in `tests/e2e/test_first_project.py`; add the README passage.

The only production consumer affected by the added persistence exports is main on this design.
No existing export or signature changes, and no new cross-part import is needed: main already imports
persistence, while application is forbidden to import it (`docs/nfdr.md:175-191`, QC-14–QC-17).

---

## 3. Sub-jobs

### Sub-job A — `persistence/`: claim the directory for one running tracker

**Scope:** put the lock adapter and its resource lifetime in `persistence/location_use.py`, with
real-file/process adapter tests in `tests/integration/test_location_use.py`.

**Exposes through `persistence/__init__.py`:**

| Surface | Contract |
|---|---|
| `LocationInUse` | A distinct `AppError` subclass. It means a nonblocking lock attempt found a conflicting owner. It contains no published wording and is never raised merely because a pathname or marker exists. |
| `LocationUse(location)` | A context manager. Construction stores the path; entering attempts the exclusive location claim and returns the lifetime object. A successful claim is held until context exit. Proven contention raises `LocationInUse` before the body runs. Other acquisition `OSError`s enter without a claim, quietly, preserving CP-702's existing startup path. An interruption or unrelated exception during entry unwinds acquired resources and propagates unchanged. |
| `LocationUse.mark_started()` | Records that listener creation succeeded. It performs no file save. Once marked, an empty location created for the claim may remain after stopping. |
| Context exit | Releases every descriptor the attempt owns on normal return or exception, without suppressing the body's exception. Before `mark_started`, restores an initially absent location to absent when this attempt created it and it is still the same empty directory. Existing directories and every saved file are left intact. |

These additions realize `SM-5`'s existing outward signal, whose owner is persistence
(`docs/SDD.md:233-241`, § The seams, SM-5).
The three existing persistence exports stay available with identical signatures
(`persistence/__init__.py:3-5`, public re-exports).

**Ownership properties:**

- The exclusive claim is on the directory object, not `tracker.json`, a PID, a text path, or a
  newly created lock file. No marker is written. All saves retain the same claim, including a save
  that replaces `tracker.json`.
- Relative, absolute and symbolic-link paths to the same directory meet the same claim.
  A contender never waits for the first tracker to stop.
- After acquiring, the open directory and the directory currently named by the path must still be
  the same object. If startup rollback removed the opened directory in the meantime, discard that
  claim and acquire against the current path. An unlinked directory descriptor cannot authorize
  serving a newly created directory at the same path.
- Rollback removes only an empty directory created by this attempt, with its identity checked.
  It never recursively deletes, removes a pre-existing directory, removes a contender's directory,
  or deletes saved data. A losing contender never removes the winner's location.
- Only the lock operation's contention result becomes `LocationInUse`. A permission, descriptor,
  unsupported-lock, resource, or directory-creation failure is CP-702's indeterminate outcome.
  Partial acquisition is unwound before following the existing load-and-bind path.

The last outcome is deliberately quieter than a new error: CP-702 requires today's behavior for
every cause other than an actual running tracker (`change_spec.md:36`, § What stays as it is).
The existing load and save methods remain usable without acquiring this lifetime, preserving their
direct adapter callers (`persistence/saved_data.py:83-130`, `SavedData`).

**Depends on:** none.

### Sub-job B — `main.py`: own the claim for the start's entire lifetime

**Scope:** wire A into the existing two-argument `start`, with the real-start proofs and the one
released end-to-end assertion.

**Exposes:** unchanged entry signatures and ready, unreadable and address-taken outputs, plus the
CP-693 refusal on genuine contention.

The startup order is explicit: enter `LocationUse`, load saved data, build the tracker, bind the
listener, mark the location started, then call the existing `serve_until_stopped`.
Context exit comes after that call's listener closure.
An acquired claim also spans all early returns and unrelated exceptions after acquisition.
The existing serving coordinator closes its listener even when arming, announcing or serving fails
(`main.py:77-92`, `serve_until_stopped`), so its signature and cleanup responsibility stay intact.

Catch `LocationInUse` by type at the start boundary and emit only CP-693's line to standard error,
returning 1. Neither load nor bind runs for that refusal.
No lock descriptor, filesystem operation, primitive error test or lock wording reaches domain,
application or web.
Unsuccessful acquisition other than contention leaves the original unreadable-before-address
order intact (`main.py:102-124`, `start`; `change_spec.md:24-36`, CP-696, CP-700–CP-702).
An unrelated bind error still propagates after location cleanup.

**Depends on:** A's `LocationUse`, `mark_started` and `LocationInUse` contract.

### Sub-job C — `README.md`: explain the second start and restart after a kill

**Scope:** add the CP-708 passage to “Starting the tracker again”. It says a second start is refused
with a message while the first carries on, and starting after a kill succeeds without clearing a
lock. The passage includes “another tracker”.

**Exposes:** the setup passage required by `change_spec.md:45`, CP-708.
Keep the README's fixed headings, its Status section and its unreadable-data description intact.

**Depends on:** none; the passage's behavior is fixed by CP-708.

**Build sequence:** A and C are independent. B follows A because B consumes A's new exports.
On this design there is no atomic-landing edge: A is an additive adapter until B wires it in, and
CP-703's saved-file assertion can hold before and after the wiring.
The single merge still carries the whole capability and proof (`change_request.md:7`, Sizing).

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — directory claim | Open the directory read-only and use `fcntl.flock` with exclusive, nonblocking flags. Keep that descriptor for the lifetime. The directory is stable across the existing save's file replacement; CP-694 and CP-700 leave no room for a new lock-file entry. Use the native contention errno from the lock call, not every `OSError`. Check directory identity under the acquired claim so startup rollback cannot strand a successful claim on an unlinked directory. |
| A — rollback | Track creation by this attempt and successful listener startup separately. Remove only the attempt's still-identical empty directory on failed startup, while excluding another successful owner. Leave a directory after a successful start, including one stopped before its first save. |
| B — lifetime wiring | None |
| B — process proofs | Use readiness or an explicit child-process barrier, with deadlines on readiness, exit, HTTP requests and cleanup. Fail on a second ready line instead of waiting forever for exit. Run rare acquisition-error cases in isolated children with a Python audit hook that raises a chosen `OSError` at the OS call and records that it fired; replace no name inside a product module. |
| C — README passage | None |

The primitive is in Python 3.11's Unix standard library
(https://docs.python.org/3.11/library/fcntl.html, `flock`).
Linux documents exclusive nonblocking acquisition, contention as `EWOULDBLOCK`, and release when
the last descriptor closes (https://man7.org/linux/man-pages/man2/flock.2.html, DESCRIPTION and ERRORS).
Apple documents the same exclusive/nonblocking contention contract
(https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/flock.2.html,
DESCRIPTION and ERRORS).
No operating-system branch or external dependency is added.

---

## 5. Test Additions

Rows T1–T19 cover the spec's Examples in order where practical. Layers follow `docs/nfdr.md:588-612`,
§ 9: AC-16's real-process persistence proofs are layer 2; the existing browser case remains layer 5.
Each new module's docstring names SRS NFR-3 / AC-16 and the other requirements it checks (CP-707).
Test paths in the table are relative to the product root.

| Row / sub-job | Test file | What to add / modify |
|---|---|---|
| T1 / B | `tests/integration/test_single_tracker.py` | First required proof, `test_second_tracker_is_refused_without_changing_the_first`: real first and second processes, same populated location, distinct ports. Assert empty stdout, exact CP-693 stderr with one newline, exit 1, no ready line or serving on the second port, unchanged bytes and directory listing, then an HTTP request answered by the first. CP-693, CP-694, CP-704. |
| T2 / B | `tests/integration/test_single_tracker.py` | Second required proof, `test_tracker_starts_after_the_owner_is_killed`: establish a refused second process before killing the first with SIGKILL; reap it; start again and assert ready, HTTP response and saved contents as left. Parameterize saved data and no save. Both this proof and T1 use only entry points present before the change, so each independently fails at the base because refusal is absent. CP-699, CP-703, CP-705. |
| T3 / B | `tests/integration/test_single_tracker.py` | Parameterize contention before any save, after the first actual save and after repeated actual saves. In every case refuse without altering the listing or saved bytes; first process still answers. This checks that file replacement never drops the claim. CP-694, CP-695. |
| T4 / B | `tests/integration/test_single_tracker.py` | Same location and same port gives the tracker-in-use line, never the address line. Exercise the real no-argument `main.py` command in a disposable product copy for the fixed-address example. Also damage the first process's saved file after readiness, then assert another start gives the contention line and preserves the damaged bytes. CP-696. |
| T5 / B | `tests/integration/test_single_tracker.py` | Relative versus absolute paths and symbolic-link aliases refuse on the same directory. A distinct directory starts on a distinct port; on the first tracker's port it gives only the existing address line. CP-697, CP-701. |
| T6 / B | `tests/integration/test_single_tracker.py` | Release two children from one barrier on the same location, distinct ports; assert exactly one ready process and one complete CP-693 refusal. Repeat for a pre-existing directory and an initially absent leaf. Keep the winner running until the loser has exited and verify its HTTP response. CP-698. |
| T7 / B | `tests/integration/test_single_tracker.py` | SIGINT stop, wait for exit 0, restart on the same location and assert ready/HTTP success; retain saved bytes. T2 covers the unhandleable kill and empty recovery. CP-699. |
| T8 / B | `tests/integration/test_start.py` | Keep the existing unreadable-data cases and precedence test unchanged. Add location-is-a-file and directory-without-read-permission cases: today's exact unreadable line, exit 1 and unchanged file/listing. Permission cases use a normal user, with the packet's root exception only. CP-700. |
| T9 / B | `tests/integration/test_start.py` | Keep held-address, existing-saved-data and unrelated-bind-failure tests unchanged, including their initially-absent-location assertions. Add retry after each failed startup on a free address to prove claim release. CP-701; CP-700's failed load also releases its claim. |
| T10 / A, B | `tests/integration/test_location_use.py`; `tests/integration/test_single_tracker.py` | Real absent location under a read-only parent follows today's ready/serving path and never claims another tracker. Isolated child audit-hook cases inject non-contention failures in directory opening/creation and locking, including unsupported locking and exhausted lock resources; verify the hook fired, the CP-693 line never appears, and existing load/bind behavior and rollback remain. Do not turn an open permission error into contention. CP-702. |
| T11 / B | `tests/e2e/test_first_project.py` | In `test_not_found_requests_write_nothing`, replace only `assert not tracker.location.exists()` with an assertion that `tracker.saved_file` does not exist. Retain the same not-found requests, subsequent create, byte snapshot and unchanged-byte assertion. CP-703. |
| T12 / A | `tests/integration/test_location_use.py` | With real files and independent processes: entry holds the claim before loading/saving; aliases contend; another directory does not; successful exit and exception exit release it. An interruption during entry closes partially acquired resources and propagates unchanged. Existing directory contents are unchanged. Constructor alone acquires nothing. Verify the exported error derives from `AppError`. |
| T13 / A | `tests/integration/test_location_use.py` | Failed startup restores an initially absent empty leaf; it leaves a pre-existing empty directory and any populated directory intact. After `mark_started`, an empty leaf remains and a new claim succeeds after exit. No recursive removal and no saved-file deletion. |
| T14 / A | `tests/integration/test_location_use.py` | Coordinate a contender that opens the directory before an owner's failed-start rollback removes it, then continues acquisition. It cannot return a claim on the removed directory; its eventual live-path claim excludes a third process. A loser cannot remove a winning process's directory. This checks the identity/rollback boundary used by CP-697–CP-698. |
| T15 / B | `tests/unit/test_start_lifecycle.py`; `tests/integration/test_start_stop.py` | Existing coordinator, real SIGINT and before-return tests stay unchanged. Their contracts fence quiet shutdown and exception propagation while the outer location context is added. |
| T16 / A, B | `tests/architecture/test_imports.py`; `test_reach.py`; `test_shapes.py`; `test_trace.py` in the same directory | Existing walks discover the new module automatically. Require the standard-library-only imports, persistence-only filesystem work, main-only refusal wording, one base error, no OS checks and requirement-bearing new test docstrings. CP-706, CP-707. No hardcoded module exemption. |
| T17 / C | `tests/integration/test_start.py` | Add a README passage check for the CP-708 meanings under the unchanged restart heading. Require `grep -c -i -F "another tracker" products/tracker17/README.md` to print at least 1, and read the passage for refusal, first tracker continuing and restart after a kill. |
| T18 / all | Existing full suites | Both CP-709 commands exit 0: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`. No exclusions, selected-only replacement, or browser-suite narrowing. |
| T19 / A, B | Product quality gates | From the product root, `uv run --locked ruff format --check .`, `uv run --locked ruff check .` and `uv run --locked mypy main.py errors.py domain application persistence web` exit 0. CP-707 and NFDR QC-62. |

**Retired assertion:** T11 retires only directory nonexistence at
`tests/e2e/test_first_project.py:223-238`, `test_not_found_requests_write_nothing`.
Its “no saved data is created” clause is re-proved by saved-file absence in T11, while T3 and T13
prove the permitted empty-directory state. No other assertion is retired.

**Rule pass:** CP-693/CP-694 → T1 and T3; CP-695 → T3 and T12;
CP-696 → T4 and the unchanged precedence case in T8; CP-697 → T5, T12 and T14;
CP-698 → T6 and T14; CP-699 → T2, T7 and T15; CP-700 → T8–T10;
CP-701 → T5, T9 and T13; CP-702 → T10; CP-703 → T2, T3, T11 and T13;
CP-704 → T1; CP-705 → T2; CP-706 → T12 and T16; CP-707 → T16 and T19;
CP-708 → T17; CP-709 → T18.
T1 and T2's old-tree runs are one-time development evidence, never committed tests that read Git
history or another checkout.

---

## Records this change makes false

None — reviewed `docs/adr/README.md` and the Accepted decisions it indexes, `docs/nfdr.md` §§ 1–10,
`docs/fdr.md` and `docs/SDD.md` § 3, with § 4's SD/OB/TS contracts.
The design fills the lock side of SM-5 without a new part, import edge, saved field or format.
The unreadable-data page remains the record gap already handed on in `deferred_decisions.md`,
§ The unreadable-data page; it is not made false by this change.

---

## Architect Review Notes

All design decisions below are the architect's, 2026-10-30.

- **Directory identity and lifetime — kind (b):** use the directory descriptor rather than the saved
  file or a persistent marker. This realizes before-first-save ownership, alias equality and
  unchanged listings by construction (CP-694–CP-698). The saved file is replaced on each save
  (`persistence/saved_data.py:124-130`, `SavedData.save`), so a claim on that file would not be the
  chosen stable identity. A standard-library scratch probe on this machine returned
  `directory held: busy 35`, `directory released: acquired`, `entries: []` for two interpreters
  applying nonblocking `fcntl.flock` to the same read-only directory descriptor path.
- **Startup rollback — kind (b):** `mark_started` distinguishes failed bind cleanup from stopping a
  tracker that served. CP-701 requires an absent location after failed bind, while CP-703 permits
  the empty location after a successful start (`change_spec.md:35-37`, § What stays as it is).
  Identity validation excludes a stale descriptor after rollback. It adds no operator-visible
  outcome beyond those rules.
- **Indeterminate acquisition — kind (b):** contain only acquisition `OSError`s that are not proven
  contention; continue the original load/bind behavior. Keep cleanup outside the message policy.
  This realizes CP-702 for all non-contention causes, rather than keeping a short allowlist that
  would accidentally turn a new filesystem error into a new refusal.
- **NFDR delegated reviews — pass:** QC-12's simplicity review accepts one adapter file for the
  one-tracker requirement. QC-22's no-rule review places only OS ownership and location cleanup in
  persistence. QC-24's no-rule review keeps main to composition, ordering and typed-message mapping.
  QC-25's replaceability review passes because the format and Saver contract remain untouched
  (`docs/nfdr.md:159-164,234-260`, QC-12, QC-22, QC-24–QC-26). QC-5's action-refusal review does not
  move this OS signal into domain: the startup signal is explicitly persistence's SM-5 signal
  (`docs/SDD.md:239`, SM-5), and neither application nor web is changed.
  QC-8, QC-20, QC-21, QC-23, QC-26, QC-27, QC-37 and QC-46 have no touched trigger: no page,
  domain rule, application flow, save protocol or saved field is added.
- **QC-41 and QC-60 — pass:** add no secret, account or credential. The new primitive uses Python
  3.11's `fcntl`/`os` facilities, not a later language feature
  (https://docs.python.org/3.11/library/fcntl.html#fcntl.flock;
  https://docs.python.org/3.11/library/os.html#os.open).
  ADR-0009's one Unix path is retained without a platform check; there is no Windows fallback
  (`docs/adr/0009-one-unix-lock-no-windows.md:14-18`, Decision).
- **QC-40, package advisories — pass for the published critical feed checked:** on 2026-10-30,
  `gh api --method GET /advisories -f ecosystem=pip -f severity=critical -f per_page=100 --paginate`
  filtered against all 16 external names in `uv.lock` returned eight pages of
  `{"matches":[],"page_count":100}` and one of `{"matches":[],"page_count":33}`.
  No matching critical advisory was returned; this is not a claim about unreported advisories.
  No pin, lock format or test dependency changes.
- **QC-40, browser — pass under the dated exception:** invoking the installed Playwright Chromium
  executable with `--version` returned exit 0 and `Google Chrome for Testing 153.0.8010.12`.
  Google's 2026-10-29 release names 156.0.8078.79/.80 and a critical MediaStream fix
  (https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_02107719452.html?amp=1).
  The older installed build remains covered through 2026-11-07 by
  `docs/nfdr.md:1085-1101`, RN-33; this design neither renews that exception nor moves the pin.
- **QC-40, repository feed — down; graph observation still owed:** an authenticated
  `gh api repos/kensaiapp/<the instance KensaiApp is developed in> --jq '{admin: .permissions.admin, dependency_graph: .security_and_analysis.dependency_graph.status}'`
  returned `{"admin":true,"dependency_graph":null}`. The alerts call returned HTTP 403,
  `Dependabot alerts are disabled for this repository.`
  The asynchronous `dependency-graph/sbom/generate-report` call returned HTTP 404, `Not Found`.
  The failed export is not proof of the graph's contents. The existing observation obligation
  remains open under `docs/nfdr.md:389-398`, QC-40, and is handed on in `deferred_decisions.md`.
- **Spec reading — no lines set aside:** the ordering, indeterminate path, directory existence and
  one released assertion are already explicit in CP-696 and CP-700–CP-703. The design carries
  those rules without changing the request's scope. The text locations are the terminal and
  README only; no unreadable-data page or console revision is included.

Cold-read result: module placement, contracts, dependency order, every Example, rule-implied failure
paths, retired coverage, record effects and the text verdict are accounted for above.
No write into a third repository is part of this design.
