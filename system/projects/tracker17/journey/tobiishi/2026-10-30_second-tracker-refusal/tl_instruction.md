# Tech Lead instruction — second-tracker-refusal: one running tracker per saved-data location

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every product path below is relative to it; command blocks explicitly state their working directory.
**Scope:** CP-693–CP-709: the Unix location claim, startup refusal and recovery, their process proofs, and the restart passage in the README.

This plan owns the implementation tasks for `tracker17 · tobiishi · 2026-10-30_second-tracker-refusal`.
Its inputs are the sibling `change_spec.md` §§ Rules and Examples and `change_design.md` §§ 1–5.
The plan's home follows `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2,
`journey/tobiishi/<key>/`.

## Project layout

```text
products/tracker17/
  persistence/
    __init__.py                         ← modified: public re-exports only
    location_use.py                     ← new: location claim and its lifetime
  main.py                               ← modified: composition and typed start message
  README.md                             ← modified: restart passage
  tests/
    integration/
      test_location_use.py               ← new: real adapter and independent-process proofs
      test_single_tracker.py             ← new: real start, refusal and recovery proofs
      test_start.py                      ← modified: additional startup failure/retry cases
    e2e/
      test_first_project.py              ← modified: CP-703's one assertion
```

Create the three new files inside the existing directories; no package or `__init__.py` is added.
Placement follows `docs/SDD.md:212-249`, § 3: persistence owns the lock and its signal across
SM-5; main owns wiring and terminal wording. The existing module set is `domain`, `application`,
`persistence`, `web`, `main` and the shared `errors` (`docs/nfdr.md:34-39,166-196`).
The layout shows only the paths added or modified, per `change_design.md:35-52`, § 2.

The import graph stays `web → application → domain`, `persistence → domain`, with main able to
import all four and every part able to import errors. Persistence must not import application,
web, main or tests; application must not import persistence or web; no part imports main or a
third-party runtime dependency (`docs/nfdr.md:166-196`, QC-13–QC-19).

Language resolution: Python — step 1, `system/projects/tracker17/project.md` `Languages:`; packet
`<CORE>/doctrine/engineering/languages/python/README.md`. The product's Python 3.11 floor,
standard-library runtime, one error base, test trace and quality gates remain binding
(`docs/nfdr.md:50-54,145-157,193-196,545-575`, QC-4, QC-11, QC-19, QC-59–QC-62).

## TL Review Notes

The Tech Lead makes the following planning decisions, 2026-10-30.

- **README verification:** design § 5 T17 recommends another README assertion in
  `tests/integration/test_start.py`. Task 3 instead verifies the passage by review and the exact
  CP-708 grep command. A string match cannot prove the three meanings, and the shared planning
  body's review-verified shape explicitly covers copy changes. The existing fixed-heading tests
  remain unchanged; no README test is removed.
- **Lifetime coverage added:** Task 2 adds a process observation during listener closure, because
  design § 3 B requires ownership through closure but § 5 T15 only retains the coordinator's
  existing tests. Those tests call `serve_until_stopped` with handed collaborators
  (`tests/unit/test_start_lifecycle.py:107-124`); they do not prove that `start` retains its outer
  location claim. The additional observation checks that composition boundary without patching it.
- **Rollback coverage sharpened:** Task 1 explicitly tests a directory populated after claim
  entry but before failed-start cleanup. Design § 3 A forbids removing populated directories;
  this case prevents creation ownership alone from authorizing deletion (T13).
- **Task dependency:** Task 3 has no dependency on Task 2; its wording is fixed by CP-708.
  Its position after the runtime tasks keeps the code and its explanation together in the reading
  order, without asserting that the passage consumes a runtime interface (design § 3 C).
- **Change-only evidence:** the two base-tree failures and the one-assertion boundary are review
  evidence in Task 2, never tests that inspect a historical checkout. This carries design § 5's
  old-tree requirement using the shared planning body's merge-base rule.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git ls-files products/tracker17 inventoried the product's tracked files: source, tests, README, docs, .gitignore, pyproject.toml and uv.lock, with no CI configuration or build runner. git ls-files .github .gitlab-ci.yml Jenkinsfile azure-pipelines.yml .circleci .buildkite returned no paths. The repository-wide git ls-files CI/build-path inspection returned only core/launchers/build-idea/launcher.sh, its test, core/tools/build_idea.py and pipeline documentation; none configures tracker17 CI."
  },
  "decisions": {"override": null, "amd64": null},
  "candidates": [
    {
      "language": "python",
      "image": "docker.io/library/python",
      "image_source": {
        "root": "core",
        "file": "doctrine/engineering/languages/python/environment.md",
        "anchor": "Start a container from the official Python image, `docker.io/library/python`, tagged with CI's"
      }
    }
  ],
  "guest": null
}
```

No CI version supplies a candidate tag; `pyproject.toml:4` supplies a minimum, not a pinned CI
version. The decision search over `docs/nfdr.md`, `docs/SDD.md` and `docs/adr/` found no environment
entry or amd64 requirement. The JSON records evidence only, following `<CORE>/prompts/gate_suite.md`
Steps 1, 3 and 4, without an owner's ask or a guest.

### Task 1: Claim one saved-data directory (`persistence/location_use.py`, `persistence/__init__.py`)

**Dependencies:** None

**What to build:** persistence's exclusive location lifetime from design § 3 A, with
`LocationUse(location)`, `mark_started()` and the distinct `LocationInUse(AppError)` exported from
the package. Construction acquires nothing; entry returns the lifetime, proven contention raises
before entering the body, and other acquisition `OSError`s enter without a claim. The lifetime
owns all descriptor cleanup and failed-start rollback, and suppresses no exception from the body.
Only a native contention result from the lock operation means another owner; an error from opening,
creating or checking the directory must not be classified by errno as lock contention. No marker,
PID file, saved field or lock-file entry is added (design § 3 A; CP-694–CP-698, CP-702, CP-706).

#### Behaviours to verify (developer adds tests to `tests/integration/test_location_use.py`)

- `test_constructing_location_use_claims_and_creates_nothing` — constructing the adapter neither
  creates an absent location nor prevents an independent process from claiming an existing one.
- `test_location_in_use_is_the_shared_typed_error` — its public export derives from `AppError`;
  existing `DEFAULT_LOCATION`, `SavedData` and `UnreadableData` exports keep their signatures.
- `test_entered_location_excludes_another_process_before_any_save` — entry holds an exclusive,
  nonblocking claim without a saved file; a contender fails promptly before its body runs.
- `test_aliases_contend_but_another_directory_does_not` — relative, absolute and symlink aliases
  meet the same directory claim; a distinct directory remains independently claimable.
- `test_context_exit_releases_the_claim` — normal and exceptional exits permit a new process to
  acquire; the body's sentinel exception propagates unchanged. Populated directory bytes and
  listings stay identical throughout.
- `test_interruption_during_entry_releases_partial_resources` — a child audit/profile observer
  interrupts entry after opening or acquiring; the original exception propagates, no owned
  descriptor survives, and a fresh process can claim the location.
- `test_non_contention_acquisition_failure_enters_without_a_claim` — isolated children exercise
  directory creation, opening and locking errors, including unsupported locking and exhausted
  lock resources. Verify the injection fired, body entry succeeds, no `LocationInUse` is raised,
  and any acquired resources and attempt-created empty leaf are unwound. An open permission error
  must not masquerade as contention, even if its errno also occurs at the lock operation.
- `test_failed_start_restores_only_its_own_empty_leaf` — before `mark_started`, an initially absent
  empty leaf is removed; a pre-existing empty directory, a populated directory, and a directory
  populated after entry all remain, with every saved byte intact.
- `test_successful_start_keeps_its_empty_location` — `mark_started` saves no file; after normal or
  exceptional exit, the created empty location remains and a new process can claim it.
- `test_contender_reacquires_the_live_directory_after_owner_rollback` — coordinate an owner that
  fails startup and a contender that already opened its directory. The contender cannot authorize
  serving through the now-unlinked descriptor; its eventual live-path claim excludes a third
  process. A losing contender never removes the successful owner's directory.

#### Held by review

- CP-706 / design § 3 A — no lock wording, data rule, platform branch or third-party dependency;
  cleanup removes only the owned, still-identical empty directory, excludes another successful
  owner, and never deletes recursively. Architecture walks cover the imports, error hierarchy and
  console boundary; read the cleanup and identity protocol for the filesystem guarantees.
- Existing `persistence/saved_data.py:83-130` load/save behavior and its public signatures stay
  intact; this adapter does not require direct `SavedData` callers to acquire a lifetime.

#### Implement

Infer from failing tests.

# Hint:
Open the directory read-only and use `fcntl.flock` with exclusive, nonblocking flags. Keep that
descriptor for the lifetime. The directory is stable across the existing save's file replacement;
CP-694 and CP-700 leave no room for a new lock-file entry. Use the native contention errno from the
lock call, not every `OSError`. Check directory identity under the acquired claim so startup
rollback cannot strand a successful claim on an unlinked directory.

Track creation by this attempt and successful listener startup separately. Remove only the
attempt's still-identical empty directory on failed startup, while excluding another successful
owner. Leave a directory after a successful start, including one stopped before its first save.

#### Verification gate

From the change worktree root, run the project card's complete command:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/
```

From the product root, run:

```sh
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy main.py errors.py domain application persistence web
```

Pass: the new adapter tests and both complete suites pass, as do all three quality commands.
Existing architecture walks discover the new file without an exemption (design § 5 T16, T18–T19).
Each new test module's opening docstring names SRS NFR-3 / AC-16 and its other checked requirements
(CP-707). Permission-denied tests use real filesystem permissions and skip only when running as
root, by `<CORE>/doctrine/engineering/testing_python.md` § Rules.

### Task 2: Own the claim across startup and serving (`main.py`, `tests/integration/test_single_tracker.py`, `tests/integration/test_start.py`, `tests/e2e/test_first_project.py`)

**Dependencies:** Task 1 — consumes persistence's `LocationUse`, `mark_started` and `LocationInUse`.

**What to build:** compose the lifetime around the unchanged `start(address, location)` contract:
claim, load, build tracker, bind, mark started, serve, close listener, release claim. Map only
`LocationInUse` to CP-693's one stderr line and return 1 before load or bind. All early returns and
unrelated exceptions after acquisition release the claim; non-contention acquisition failures
retain the original unreadable-before-address behavior (design § 3 B; CP-693, CP-696, CP-700–CP-702).
Published wording comes verbatim from the sibling `change_text.md`; CP-693 fixes the terminal
line and adds exactly one trailing newline. Keep `main(argv)`, `serve_until_stopped` and the
SIGINT adapter's public contracts. Change CP-703's named end-to-end assertion with this wiring,
because this is where an empty location becomes visible before the first save.

#### Behaviours to verify (developer adds tests to `tests/integration/test_single_tracker.py` and `tests/integration/test_start.py`)

- `test_second_tracker_is_refused_without_changing_the_first` — real processes on the same
  populated location and distinct ports: the second has empty stdout, exactly CP-693 plus newline
  on stderr, exit 1, no ready line and no listener. Compare saved bytes and the listing immediately
  around refusal; then assert an HTTP response from the still-running first process (T1).
- `test_tracker_starts_after_the_owner_is_killed` — show a second real process refused, then
  SIGKILL and reap the first; a fresh process prints ready and answers HTTP with the saved contents
  as left. Parameterize populated and never-saved locations. Keep the shown refusal in this test
  so the test independently fails before the lock is wired (T2; CP-705).
- `test_refusal_keeps_the_claim_before_and_after_saves` — before any save, after one real save and
  after repeated real saves, the contender is refused, bytes/listing stay unchanged, and the first
  still answers. No saved file exists before the first save (T3; CP-694–CP-695, CP-703).
- `test_location_in_use_wins_over_other_start_refusals` — same location/same port gives only
  CP-693, including the real no-argument `main.py` command in a disposable product copy. Damage
  the file after the first becomes ready: the next start still gives CP-693, preserves the damaged
  bytes/listing, and leaves the first serving (T4; CP-696).
- `test_real_starts_resolve_directory_aliases_and_separate_locations` — relative/absolute and
  symlink aliases contend; a distinct directory on a free port serves, and on the held port gets
  only today's address line with its listing unchanged (T5).
- `test_simultaneous_starts_have_one_ready_owner` — release two children from one barrier onto
  distinct ports and one location. For both an existing directory and an initially absent leaf,
  exactly one becomes ready and the other completes the exact refusal; keep the winner alive
  until the loser exits and then assert its HTTP response (T6; CP-698).
- `test_tracker_restarts_after_ctrl_c` — SIGINT ends the owner quietly with exit 0; restart on the
  same location is ready and answers HTTP, preserving saved bytes (T7).
- `test_invalid_location_keeps_the_unreadable_start_contract` — location-is-a-file and directory
  without read permission retain today's exact unreadable stderr line, exit 1 and unchanged
  bytes/listing. Restore permissions in cleanup; the normal-user/root rule from Task 1 applies
  (T8; CP-700).
- `test_failed_start_releases_its_location_for_retry` — retry after unreadable data is repaired,
  after a held address is released and after an unrelated bind error, on a usable address. The
  retries become ready and answer HTTP. Failed startup keeps a pre-existing listing unchanged
  and returns an initially absent leaf to absent; an unrelated bind error propagates unchanged,
  without either refusal message (T9).
- `test_indeterminate_acquisition_keeps_existing_start_behavior` — an absent leaf under a real
  read-only parent still serves, as CP-702 requires. Isolated audit-hook cases for create/open/lock
  errors must prove injection occurred, never print CP-693, preserve load-before-bind precedence
  and failed-start rollback, and permit the existing ready path when load and bind succeed (T10).
- `test_location_claim_remains_held_during_listener_close` — pause the real child at listener
  closure using an interpreter observer; an independent contender still refuses there. Release
  the child, wait for exit, and show a fresh start serves. Replace no product name or code object.
- Keep the existing coordinator, SIGINT and before-return assertions in
  `tests/unit/test_start_lifecycle.py` and `tests/integration/test_start_stop.py` unchanged (T15).
- In `tests/e2e/test_first_project.py::test_not_found_requests_write_nothing`, replace only
  `assert not tracker.location.exists()` with `assert not tracker.saved_file.exists()`. Retain
  the same not-found requests, subsequent creation, byte snapshot and unchanged-byte assertion
  (T11; CP-703).

#### Held by review

- CP-704–CP-705's two required tests import only entry points available at the branch's merge
  base. Each must fail there for a missing refusal, without hanging, and pass on this branch.
  A missing new import or fixture is not that proof. This is one-time execution evidence, never
  a committed test of repository history (design § 5, after T19).
- CP-703 permits only the one assertion replacement above. All other existing assertions,
  suite collection, fixed addresses, published messages and signatures retain their contracts
  (spec §§ What stays as it is and Out of Scope; design § 2).
- Claim mechanics, error-number handling and filesystem cleanup belong only to persistence;
  main's new responsibility is composition and typed-message mapping. Read that boundary in
  addition to the existing architecture walks (SDD § 3 SM-5; NFDR QC-22, QC-24, QC-42, QC-45).

#### Implement

Infer from failing tests.

# Hint:
Use readiness or an explicit child-process barrier, with deadlines on readiness, exit, HTTP
requests and cleanup. Fail on a second ready line instead of waiting forever for exit. Run rare
acquisition-error cases in isolated children with a Python audit hook that raises a chosen
`OSError` at the OS call and records that it fired; replace no name inside a product module.

#### Verification gate

From the change worktree root, run the complete card command:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/
```

From the product root, run:

```sh
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy main.py errors.py domain application persistence web
```

Pass: both complete suites and all quality commands exit 0, including every new process proof,
the single amended end-to-end assertion and unchanged startup/lifecycle tests. All children are
reaped and all test sockets closed on success or failure; no permission or timeout failure counts
as evidence of contention. New module docstrings meet CP-707.

For the one-time base-tree proof, from the change worktree root:

```sh
TRACKER_PROOF_BASE=$(git merge-base main HEAD)
TRACKER_PROOF_COPY=$(mktemp -d)
git clone --quiet --no-hardlinks . "$TRACKER_PROOF_COPY"
git -C "$TRACKER_PROOF_COPY" checkout --quiet "$TRACKER_PROOF_BASE"
cp products/tracker17/tests/integration/test_single_tracker.py "$TRACKER_PROOF_COPY/products/tracker17/tests/integration/test_single_tracker.py"
(
  cd "$TRACKER_PROOF_COPY"
  uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_single_tracker.py::test_second_tracker_is_refused_without_changing_the_first products/tracker17/tests/integration/test_single_tracker.py::test_tracker_starts_after_the_owner_is_killed
)
```

Pass for this before-check: both named tests fail because the second starts serving, and their
deadlines/cleanup prevent a hang. Read the output before removing the scratch copy, from outside it:

```sh
rm -rf "$TRACKER_PROOF_COPY"
```

The same selected test command in the change worktree must pass. Record both outcomes as
development evidence. Review the change-only boundaries from the change worktree root:

```sh
git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/e2e/test_first_project.py
git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/unit/test_start_lifecycle.py products/tracker17/tests/integration/test_start_stop.py products/tracker17/tests/conftest.py products/tracker17/domain products/tracker17/application products/tracker17/web products/tracker17/errors.py products/tracker17/persistence/saved_data.py products/tracker17/pyproject.toml products/tracker17/uv.lock products/tracker17/docs
```

Pass: the first diff contains only CP-703's named assertion replacement; the second is empty.
These comparisons end with the change and are never added to the suite.

### Task 3: Explain refusal and restart (`README.md`)

**Dependencies:** None

**What to build:** place the sibling `change_text.md`'s README passage verbatim under
“Starting the tracker again”, as design § 3 C specifies, satisfying CP-708.

#### Deliverables verified by review

- The passage says that another tracker using the location makes a second start refuse with a
  message, that the first carries on, and that starting after a kill succeeds without clearing a
  lock. It contains the words “another tracker” (CP-708; design § 3 C).
- All existing headings, the entire Status section, and the unreadable-data description keep
  their text; only the requested restart passage is added (spec § Out of Scope; design § 3 C).
- The published passage matches `change_text.md` verbatim; this task authors no replacement copy
  (cross-role contract § 2).

#### Implement

Verified by review — no test.

#### Verification gate

From the change worktree root:

```sh
grep -c -i -F "another tracker" products/tracker17/README.md
git diff "$(git merge-base main HEAD)" -- products/tracker17/README.md
uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/
```

Pass: grep prints at least 1; reading the passage proves all three CP-708 meanings and its exact
placement/copy; the diff preserves every existing heading, Status and unreadable-data wording;
both full suites exit 0 with no exclusions. Each review criterion receives its own verdict.
