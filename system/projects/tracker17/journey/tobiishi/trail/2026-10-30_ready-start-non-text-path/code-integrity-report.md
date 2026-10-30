# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

## The deferrals

None. The closing marker carries no `Deferred:` line.

## What was reviewed

`products/tracker17/main.py` (`_shown_location`, its three constants and `_ready_line`),
`products/tracker17/tests/unit/test_start_message.py` and
`products/tracker17/tests/integration/test_ready_start.py`.

## The intent it was checked against

`tl_instruction.md`, `change_spec.md` (CP-747 to CP-756) and `change_text.md` beside this file, with
`change_design.md` § 2 and § 5. `docs/fdr.md` was not needed for any call.

## The tests added or fixed

All in `tests/integration/test_ready_start.py`.

- **Added `test_readable_start_keeps_the_original_path_for_the_file_system`.** The plan requires the
  original path in every file-system operation, and only the valid-file case proved it. That case
  skips on a file system that refuses the byte, so the suite here had no test of it. The start makes
  its directory when it claims the location, so a leaked display form leaves a folder really named
  `caf\xe9`, and the test holds that none exists. CP-747, CP-748; design § 2.
- **Added `test_readable_start_on_a_valid_file_at_an_ordinary_path`.** The skipped case's saved-data
  fixture had never been read by a tracker. This runs that fixture on every file system: the named
  project shows and the file's bytes stay. CP-747, CP-751.
- **Fixed one assertion in `test_readable_start_path_is_independent_of_console_policy`.** It looked
  for `udc` anywhere in the line, the temporary directory included, so a machine whose temporary path
  holds those letters would fail on sound code. It now looks for `\udc`, the form CP-748 names.

## The finding

**No bugs and nothing misplaced.** The code does what its intent says. The review's findings were in
the tests: one gap, one unproved fixture and one assertion too wide, all above.

The developer's handoff named the valid-file case as most likely to bite, because it had run nowhere.
It has now run and passed once, outside the gate: Python 3.11.17 in the official Linux container, with
the two new modules read-only, gave 156 passed and none skipped. The suite the verdict rests on still
skips that case here, as CP-753 says it must. See *Calls made*, item 1.

## Calls made

1. **Can a pass rest on a suite that skips the valid file at a byte-bearing path?** The readings were
   to hold the verdict until a gate reaches a file system that accepts the directory, or to accept the
   skip. **Took: accept it.** CP-753 and Locked Answers Gap 5 state that skip, and the case passed in
   the container run above. **Owner:** the Product Owner (`change_spec.md`). Ruled the other way, the
   product needs a gate environment that can hold the directory, which `docs/nfdr.md` § 8 would record.
2. **Is a refusal only `EILSEQ` or `EINVAL`?** The developer chose those two where the plan names no
   errno. The readings were any `OSError` or that short list. **Took: the short list.** The plan says
   unrelated setup failures must not become skips, and a refusal outside the list fails loudly, which
   is the easier mistake to find. **Owner:** the Tech Lead (`tl_instruction.md`). Ruled the other way,
   only the test's tuple changes.
3. **Does `main.py` owe `__version__`?** The developer recorded leaving it out as a divergence from
   `conventions.md:148`. **Took: none owed, and no divergence.** That line calls it `versioning.md`'s
   marker, and `versioning.md` § *Whose artifacts — kensaiapp's, never a product's* makes a product's
   version string product content. Nothing in this intent sets one. **Owner:** the product's Architect
   (`docs/nfdr.md`). Ruled the other way, a later change adds markers across the product.

## Placement

The parts table is `docs/SDD.md` § 3. Nothing was moved, so there is no placement commit.

| Logic | Owning part | Result |
|---|---|---|
| `_shown_location` and `SURROGATE_ESCAPE_BASE`, `FIRST_SURROGATE_ESCAPE`, `LAST_SURROGATE_ESCAPE` | `main`, which writes the start messages | Already there |
| `_ready_line`'s use of it | `main` | Already there |

## The language resolution

Python, chain step 1, `project.md` `Languages:`. Packet read:
`<CORE>/doctrine/engineering/languages/python/README.md`, with `conventions.md`, `quality_gates.md`,
`environment.md` and `testing_python.md`. No packet rule required a code change; `__version__` is
*Calls made*, item 3. The product's Ruff, mypy and `tests/unit/`, `tests/integration/` layout are its
own records, which outrank the packet.

## Test evidence

No test went red against the code, so there is no red commit.

- **The card's command through the gate tool:** exit 0, 2968 passed and 1 skipped, then 122 passed.
  The skip is the valid-file case, on the file system's refusal: errno 92, `Illegal byte sequence`.
- **Quality gates, product root:** compile exit 0, `ruff format --check .` exit 0, `ruff check .`
  passed, `mypy main.py errors.py domain application persistence web` no issues.
- **CP-752 on the code before the change:** a disposable clone at `a7d507b23` with the new test module
  failed the strict missing-data case with status 1, empty stdout and `UnicodeEncodeError` on
  `'\udce9'`.

**Would a test notice wrong code?** Each mutation of `main.py` ran in a scratch copy over the two new
modules, on this machine, and none was committed.

| Mutation | Failed | Includes |
|---|---|---|
| Uppercase hex | 125 | every test holding an escape |
| Escape all non-ASCII | 8 | `keeps_ordinary_paths_verbatim` |
| Surrogate spelling `\udce9` | 148 | every test holding an escape |
| Replacement mark | 148 | every test holding an escape |
| No escape at all | 145 | every test holding an escape |
| Range one short at the top | 8 | `escapes_each_filename_byte` for `0xff` |
| Backslashes doubled | 3 | `keeps_ordinary_paths_verbatim` |
| Display form used as the location | 1 | `keeps_the_original_path_for_the_file_system` |

The last mutation is the gap the added test closes: it failed nothing else here. In the Linux container
the same mutation also fails the valid-file case.
