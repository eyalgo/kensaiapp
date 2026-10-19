# Change Spec — README § Running the tests gives the Linux browser step and the suite's Git prerequisite

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Request:** Bring the README's "Running the tests" section up to what SDD v7 gives it (`docs/SDD.md:677-686`, § 6 S-1 *Artifact*, § 4 RT-4). For Linux, the section names `python -m playwright install --with-deps chromium` in place of `python -m playwright install chromium`, says that this command runs the package manager and asks for administrator rights, says the tracker and `pytest tests/` need none of it, and names the Linux systems the pinned library's documentation lists (including Debian 12). The section also says the full suite needs the copy to be a Git repository with `git` on the path, and says what the one test that otherwise fails checks: that Git ignores the saved data. It replaces the current closing paragraph about a copy that isn't a Git repository, which says the test fails but not that `git` is needed. This is reached-when 9 of station `2026-10-08_setup-instructions`; reached-when 1 to 8 stay true. The README text must keep `docs/CONTENT.md` § Grammar and mechanics (no sentence over 20 words, none saying "today", "yesterday", "tomorrow", "now", "ago" or "recently"), so reached-when 8's grep still matches nothing. Sizing: one section of one file, one honest merge. Must not be weakened: no change to `main.py`, tests, other headings, commands or `docs/`; "How it's built" and "The documents" stay as they are, and the start prints and serves what it does today.

---

## Change Summary

The README's § Running the tests gains, for Linux, the browser install command that also fetches the system libraries, what that command asks of the machine, and the Linux systems the end-to-end tests run on. Its closing paragraph is replaced by one that says the full suite needs a Git repository and `git` on the path, and what the one test that fails otherwise checks. This closes FDR R-119 and R-120 and SDD § 6 S-1 *Artifact* (`docs/SDD.md:677-686`), which the README does not carry today.

All paths below are relative to the product root, the directory `project.md` `Product path:` names.

---

## Rules

### Linux — the browser step in § Running the tests

- **CP-69:** § Running the tests gives, for Linux, the command `python -m playwright install --with-deps chromium`, written exactly so in a code span or code block. It says a Linux reader types it in place of `python -m playwright install chromium`. (Closes FDR R-119's "one-time step"; SDD § 4 RT-4, `docs/SDD.md:285-288`.)
- **CP-70:** The section says that the Linux command runs the system's package manager and asks for administrator rights. (FDR R-119.)
- **CP-71:** The section says that the tracker and `pytest tests/` need none of what the Linux command installs. (FDR R-119; SDD § 4 RT-4, `docs/SDD.md:289-290`.)
- **CP-72:** The section names the Linux systems the end-to-end tests run on. They are the systems the documentation of the pinned `playwright==1.63.0` lists, as SDD § 4 RT-4 carries them (`docs/SDD.md:291-293`): Debian 12 and 13, and Ubuntu 22.04, 24.04 and 26.04, on x86-64 or arm64. Every one of the five systems and both architectures appear. The literal text `Debian 12` appears. The section names no other Linux system as one the end-to-end tests run on. (FDR R-120, PD-8.)

### Git — the suite's prerequisite in § Running the tests

- **CP-73:** The section says that running the full suite needs the copy to be a Git repository, and needs `git` on the path. (SDD § 6 S-1 *Artifact*, `docs/SDD.md:681-682`.)
- **CP-74:** The section says that the tracker itself needs neither a Git repository nor `git`. (SDD `docs/SDD.md:682`, "which the tracker's own setup does not"; see Locked Answers, Gap 1.)
- **CP-75:** The section says that when either condition in CP-73 is missing, one test doesn't pass, and that this test checks that Git ignores the saved data. (SDD § 6 S-1 *Artifact*, `docs/SDD.md:682-683`; FDR R-12 is the behaviour that test guards.)
- **CP-76:** The CP-73 to CP-75 text closes the section, in place of the paragraph that closes it now (`README.md:107`: "In a copy that isn't a Git repository, such as one unpacked from a download, one test doesn't pass. That test checks that Git ignores the saved data."). Neither of those two sentences remains as written, and the section states the Git condition once. A defect is being removed here: `README.md:107` names the non-Git copy but not a missing `git`, and the second condition fails the same test (see Verified Claims).

### Wording and boundaries

- **CP-77:** Every sentence this change adds or rewrites keeps `docs/CONTENT.md` § Grammar and mechanics. No sentence is longer than 20 words (`docs/CONTENT.md:120`), and none says "today", "yesterday", "tomorrow", "now", "ago" or "recently" (`:126-127`). Negatives are contracted (`:118-119`), no Latin abbreviation appears, and commands and tools are written as their owners write them (`:131-132`). After the change, `grep -n -w -i -e today -e yesterday -e tomorrow -e now -e ago -e recently products/tracker17/README.md` exits 1 with no output.
- **CP-78:** Nothing in `README.md` outside § Running the tests changes, and no heading is added, removed or renamed anywhere in the file. Inside the section, the code block of seven commands (`README.md:91-99`) keeps every command, exactly as written and in the same order. The paragraphs at `README.md:89`, `:101`, `:103` and `:105` stay as written. No file other than `README.md` changes.
- **CP-79:** After the change, `grep -n -F -e '--with-deps' -e 'Debian 12' products/tracker17/README.md` matches at least one line for each pattern, and every match lies inside § Running the tests. (Station `2026-10-08_setup-instructions` reached-when 9's check.)

---

## Examples

| Scenario | Expected behavior |
|---|---|
| CP-69: a Linux reader reads § Running the tests | They find `python -m playwright install --with-deps chromium` written exactly, told to type it in place of `python -m playwright install chromium` |
| CP-69, CP-78: a macOS reader follows the seven-command block | The block is unchanged, and `python -m playwright install chromium` is still its fifth command |
| CP-70: a Linux reader about to type the Linux command | The section has told them it runs the system's package manager and asks for administrator rights |
| CP-71: a Linux reader who wants only the tracker, or only `pytest tests/` | The section tells them neither needs what the Linux command installs |
| CP-72: a reader on Debian 12, Debian 13, Ubuntu 22.04, 24.04 or 26.04, on x86-64 or arm64 | The section names their system among those the end-to-end tests run on |
| CP-72: a reader on a Linux not in the list, such as Fedora | The section names no system beyond the five as one the end-to-end tests run on |
| CP-73, CP-75: a reader runs the suite in a copy unpacked from a download, with no `.git` | The section has told them a Git repository is needed, and that one test, which checks that Git ignores the saved data, doesn't pass otherwise |
| CP-73, CP-75: a reader runs the suite in a Git repository on a machine with no `git` on the path | The section has told them `git` on the path is needed, and that the same one test doesn't pass otherwise |
| CP-74: a reader with no `git` who only wants to run the tracker | The section tells them the tracker needs neither a Git repository nor `git` |
| CP-76: a reader reads to the end of § Running the tests | The last paragraph is the Git text, and the two sentences at `README.md:107` today no longer appear |
| CP-77: the README's whole text is grepped for the six relative words | `grep -n -w -i -e today -e yesterday -e tomorrow -e now -e ago -e recently products/tracker17/README.md` exits 1 |
| CP-77: a sentence the change adds is counted | It has 20 words or fewer |
| CP-78: `git diff` of the change | Touches only `products/tracker17/README.md`, and only lines inside § Running the tests; no line starting with `#` changes |
| CP-79: the station's reached-when 9 grep runs | It matches a line holding `--with-deps` and a line holding `Debian 12`, both inside § Running the tests |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| The README carries neither `--with-deps` nor `Debian 12` today (CP-69, CP-72, CP-79) | `grep -n -F -e '--with-deps' -e 'Debian 12' products/tracker17/README.md`, in the change worktree at branch point | No output, exit 1 |
| Reached-when 8's grep matches nothing today, so CP-77 keeps an exit-1 result rather than creating one | `grep -n -w -i -e today -e yesterday -e tomorrow -e now -e ago -e recently products/tracker17/README.md`, same tree | No output, exit 1 |
| § Running the tests is `README.md:87-107`; its command block is `:91-99` with `python -m playwright install chromium` at `:96`; its closing paragraph is `:107` (CP-76, CP-78) | Read `products/tracker17/README.md` in the change worktree | As stated; `:107` reads as quoted in CP-76 |
| In a copy that is not a Git repository, `pytest tests/` fails exactly one test, and that test checks Git ignores the saved data (CP-75) | `git archive HEAD products/tracker17` extracted to `/private/tmp`, outside any repository (`git rev-parse` → "not a git repository"); `python3 -m pytest tests/ -q` from `products/tracker17`, real `git` on the path | `1 failed, 223 passed`; the failure is `tests/integration/test_start.py::test_data_is_ignored_by_version_control`, `git check-ignore` returning 128 |
| In a Git repository with `git` not on the path, the same one test fails and no other does (CP-73, CP-75, CP-76's defect) | Same archive, `git init` and one commit made in the copy; `pytest tests/` run with `PATH` holding only `python3` and `/bin`, which has no `git` | `1 failed, 223 passed`; the failure is the same test, with `FileNotFoundError: ... 'git'` |
| With both conditions met, `pytest tests/` passes (the baseline for the two rows above) | The same Git copy with `git` on the path | `224 passed` |
| `pytest tests/` needs neither the browser nor the browser-driving library (CP-71) | The three runs above used a Python with no `playwright` module installed (`import playwright` → `ModuleNotFoundError`); `tests/conftest.py:7` states that `pytest tests/` does not collect `tests/e2e/` | All three runs collected 224 tests and none needed `playwright` |
| The tracker needs neither a Git repository nor `git` (CP-74) | `grep -rnw git products/tracker17 --include='*.py'`, with lines under `tests/` filtered out | No match, exit 1; the only `git` call in the product is the test at `tests/integration/test_start.py:168` |
| The one Git test is `test_data_is_ignored_by_version_control` in `tests/integration/test_start.py`, and it runs `git check-ignore` (CP-75) | Read `tests/integration/test_start.py:165-170` | `subprocess.run(["git", "check-ignore", "-q", "data/tracker.json"], ...)`, asserting return code 0 |
| The pin is `playwright==1.63.0` (CP-72) | Read `tests/requirements.txt` | `playwright==1.63.0` |

---

## Out of Scope

- `main.py`, every file under `tests/`, `pyproject.toml`, `tests/requirements.txt` and every file under `docs/`. The start prints and serves what it does today.
- Every README section other than § Running the tests, including § Status, "How it's built" and "The documents" (CP-78).
- The seven commands in the section's command block, and the order they're typed in (CP-78).
- Checking the setup on Linux, or running `pytest tests/e2e/` on any Linux. SDD § 11 R-9 owns that, and the README's "checked on macOS only" stands.
- Saying what to do on a Linux outside the CP-72 list, beyond naming the list. No sentence about other distributions is required.
- Re-reading the Playwright documentation. The list is the one SDD § 4 RT-4 carries for the pin, and it moves only when the pin does (`docs/SDD.md:295-296`).
- Naming the failing test's function or file in the README. The README says what the test checks (CP-75), not where it lives.
- Windows. The README's "Windows isn't supported" stands.

---

## Locked Answers (the divergence record — self-review 2026-10-11)

- **Gap 1 — whether the README says the tracker needs no Git:** CP-74 requires it. The request asks only for the suite's prerequisite. SDD § 6 S-1 *Artifact* states the prerequisite together with "which the tracker's own setup does not" (`docs/SDD.md:682`). Without that sentence, a reader with a downloaded copy could take `git` for a prerequisite of the tracker. The prerequisites section names Python alone, and `README.md:38` says starting the tracker installs nothing. The claim is verified in Verified Claims. Saying it adds one sentence and takes nothing away, so it can be undone.
- **Gap 2 — where the Linux command goes:** CP-69 asks for the command and the "in place of" instruction, and leaves where they sit inside the section to design and content. The seven-command block stays exactly as written (CP-78). The request says "no change to … commands", and the macOS reader's path must stay intact. That rules out changing the block's fifth command in place.
- **Gap 3 — no new heading:** CP-78 adds no heading anywhere, including no "Linux" sub-heading inside the section. The request says "no change to … other headings" and sizes the change to "one section of one file". Station reached-when 1 checks heading lines, and a new heading is a structural change the request didn't ask for.
- **Gap 4 — § Status is unchanged:** § Status lists setup-instruction items with the commit that brought each in (`README.md:7`). The request sizes the change to § Running the tests alone, so § Status gains no line here. If § Status should carry this item, that's a route question for the PM, not a rule in this spec.
- **Gap 5 — the Linux list's source:** CP-72 takes the five systems and two architectures as SDD § 4 RT-4 carries them for `playwright==1.63.0` (`docs/SDD.md:291-293`), and does not re-read the vendor page. The SDD owns that fact, and the request points to the SDD.
- **Gap 6 — the "otherwise" covers both conditions:** CP-75 says the one test fails when *either* condition is missing, not only in a non-Git copy. Verified Claims shows the same single failure in both cases. The request's "the one test that otherwise fails" follows "a Git repository with `git` on the path", so it covers both. `README.md:107` covers only the first case.
- **Gap 7 — "full suite":** CP-73 keeps the SDD's term "the full suite" and doesn't name which command holds the Git test. The test sits under `pytest tests/`, but "full suite" in the SDD and in FDR R-8 means both commands together. Saying where the test sits would add a detail the request does not ask for.
