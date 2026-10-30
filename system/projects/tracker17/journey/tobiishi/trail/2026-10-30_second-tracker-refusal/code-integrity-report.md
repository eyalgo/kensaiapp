# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

This report records the review of `tracker17 · tobiishi · 2026-10-30_second-tracker-refusal`, the change that refuses a second tracker on saved data already in use. The review found one race in the code and fixed it. Five calls wait for their owners to confirm.

## Deferrals

None. The closing marker `726104505` carries no `Deferred:` line.

## What was reviewed

The code commits on the branch under `products/tracker17/`:

- `persistence/location_use.py` and `persistence/__init__.py`
- `main.py`
- `README.md`
- `tests/integration/test_location_use.py`, `tests/integration/test_single_tracker.py` and `tests/integration/test_start.py`
- `tests/e2e/test_first_project.py`

## The intent it was checked against

- `tl_instruction.md`, the primary intent, in the change's folder
- `change_spec.md`, rules CP-693 to CP-709, in the same folder
- `change_design.md` §§ 3 and 5, and `change_text.md`, for the plan's references
- `products/tracker17/docs/fdr.md`, read as context only

## The finding

**One bug was found and fixed: a start could serve with no claim on the location.**

The race needs a start, called the contender here, that has found the directory present and has not yet opened it. A failed start's rollback then removes the directory. The contender's open fails with "no such file", and the code treated that as an undeterminable claim. So the contender served unclaimed, and a third start also served on the same location. That breaks CP-693 and CP-698, and design § 3 A, which says to "acquire against the current path". The existing tests covered only a contender that had already opened the directory.

The fix adds `LocationUse._open_leaf`. A directory that is gone at the open now goes round the existing bounded retry, so the contender makes the directory again and claims it. The module docstring also claimed rollback runs "only while the claim is held", which was false for a failed lock or open, so the docstring now says what the code does.

Red commit: `4aeece743`, whose one failing case read `'entered False' == 'entered True'`. The fix rides with this report.

Nothing was misplaced. The other tests added passed against the code as written.

## The tests added or fixed

Added in `tests/integration/test_location_use.py`:

- `test_contender_about_to_open_reacquires_the_live_directory_after_owner_rollback` is the red test for the bug above.
- `test_losing_contender_that_made_the_directory_leaves_it_to_the_owner` covers the plan's "a losing contender never removes the successful owner's directory". Before it, only a loser that had not made the directory was tested. Removing the code's `self._created = False` line makes this test fail.
- `test_interruption_during_entry_removes_the_leaf_it_made` extends the plan's interruption case to an absent location, so a location that did not exist stays absent (CP-701).
- `test_dangling_symbolic_link_enters_without_a_claim_and_stays_dangling` holds CP-702 and shows the new retry ends on a path that never opens.

Added and fixed in `tests/integration/test_single_tracker.py`:

- `test_start_after_a_kill_serves_what_the_killed_tracker_saved` is added for CP-699. The existing kill test saved an empty state and checked the file and a 200, so it stayed green when a restart ignored the saved data. The new test fails under that same break, and it also checks that the restart says nothing about the earlier tracker.
- `test_the_real_second_start_command_gets_the_refusal_and_not_the_address_line` is fixed. It ran `main.main()` through `python3 -c`, while CP-696 names the real `python3 main.py`. It now runs that file, and checks that the first tracker still answers.
- `test_indeterminate_acquisition_keeps_existing_start_behavior` gains the scenario `unreadable-and-address-held`, because the plan asks it to preserve load-before-bind precedence and no case had both refusals apply.

## Test evidence

- An earlier run of the test command exited 0 and printed `Environment: owners-mac — no CI`.
- An earlier run of the test command exited 1 and printed `Environment: owners-mac — no CI`.
- The last run of the test command exited 0: 2768 passed in the first suite and 121 in the end-to-end suite.
- Ruff's format check, Ruff's lint and mypy exit clean, and `python3 -m compileall -q` exits 0 on `main.py` and `persistence`.
- **CP-704 and CP-705, checked independently:** in a disposable clone at the merge base `00e82c6ba`, with the new test file copied in, both named tests fail (three cases) in 30.59 seconds. Each fails with "the process kept running: it served instead of ending", and neither hangs.
- **CP-708:** `grep -c -i -F "another tracker"` on the README prints 2. All three meanings are in the passage, under "Starting the tracker again". Every line of `change_text.md`'s README passages is in the README verbatim, and the CP-693 line is in `main.py` verbatim.
- **CP-703 and the plan's boundary:** the diff of `test_first_project.py` is the one named assertion. The diff of the lifecycle tests, `domain`, `application`, `web`, `errors.py`, `saved_data.py`, the lock files and `docs` is empty.
- **Headings and Status:** the README diff adds no heading and does not touch the Status section.

## Placement

The parts table is `products/tracker17/docs/SDD.md` § 3.

| Logic | Owning part | Result |
|---|---|---|
| The claim, its identity check and its rollback | `persistence` (owns "the lock that lets one running tracker use a location") | Already there, `persistence/location_use.py` |
| The order of claim, load, bind and mark, and the typed mapping to the message | `main` (composition and start messages) | Already there, `main.py` |
| The CP-693 wording | `main` | Already there |

No move was made, so no placement commit exists.

## Calls made

1. **Should `location_use.py` and `persistence/__init__.py` carry `__version__`?**
   - *Readings:* `languages/python/conventions.md:148` says every non-test module does. `<CORE>/doctrine/governance/versioning.md:177` says "A product's artifacts version by the product's rules".
   - *Taken:* leave it out. No tracker17 module carries one, and the product's records state no such rule. The rule describes itself as `versioning.md`'s marker for a script.
   - *Owner:* the owner, through the Python packet.
   - *If reversed:* the marker goes in once per package, across the whole product, in one change.
2. **May the README sentence "If the new directory is empty, there was no saved data to set aside." stay?**
   - *Readings:* `tl_instruction.md` Task 3 and `change_design.md` § 3 C name only "Starting the tracker again", and the spec's Out of Scope names the set-aside restart. `change_text.md` places this sentence in "Setting saved data aside".
   - *Taken:* keep it. `change_text.md` is the source of published strings, and CP-703 makes an empty directory reachable there. The sentence does not touch the restart steps or the unreadable-data description.
   - *Owner:* the Tech Lead.
   - *If reversed:* one sentence comes out, and the reader of an empty set-aside directory has no explanation.
3. **Should a location whose parent is missing be claimed?**
   - *Readings:* CP-695 says a location is in use from the start. CP-702 lets a start go on unclaimed when the location cannot be created. The code makes only the last directory, so a missing parent enters unclaimed, and two such starts would both serve.
   - *Taken:* leave it. `DEFAULT_LOCATION` is `data` beside the code, whose parent always exists, and `main` takes no location. So no operator command reaches the case, only a direct call to `start`. Creating parents would also add directories outside the location, which QC-42 and the rollback rule do not allow for.
   - *Owner:* the Architect.
   - *If reversed:* `LocationUse` creates parents and its rollback removes them.
4. **May rollback remove the leaf with no claim after a failed open or lock?**
   - *Readings:* the plan's `test_non_contention_acquisition_failure_enters_without_a_claim` requires the attempt-created leaf to be unwound. Its Held by review says cleanup "excludes another successful owner", and with no descriptor or lock nothing can exclude one.
   - *Taken:* keep the removal, as the tested behaviour. Harm needs two things in the instant between `mkdir` and the open: a failure on this start's open, such as running out of descriptors, and another start claiming the directory it just made. That owner would then hold an unlinked directory.
   - *Owner:* the Architect.
   - *If reversed:* a failed open leaves an empty directory behind, and the plan's case and CP-701's wording for that path change.
5. **Are behaviours split across several tests acceptable where the plan names one test?**
   - *Readings:* the plan names `test_location_in_use_wins_over_other_start_refusals`, `test_invalid_location_keeps_the_unreadable_start_contract`, `test_failed_start_releases_its_location_for_retry` and `test_indeterminate_acquisition_keeps_existing_start_behavior` as single tests. The developer split them by cause, partly into `tests/integration/test_start.py`.
   - *Taken:* accept. Each listed behaviour has its own assertion, and the plan's list places these in both files.
   - *Owner:* the Tech Lead.
   - *If reversed:* tests are renamed or merged, with no change in what they assert.

## Language resolution

Python, answered by step 1 of the chain, `project.md` `Languages:`. The packet read is `<CORE>/doctrine/engineering/languages/python/README.md`, with its `conventions.md` and `quality_gates.md`, and `testing_python.md` for Testing. `quality_gates.md`'s bar is met, and the product's own Ruff and mypy gates pass. `testing_python.md`'s seam rule holds, because no new test patches a name inside a product module. The one departure from `conventions.md` is Call 1.
