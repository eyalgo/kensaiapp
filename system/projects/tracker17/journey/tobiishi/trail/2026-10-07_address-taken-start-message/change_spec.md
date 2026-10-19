# Change Spec — One plain message when something else holds the tracker's address

**Date:** 2026-10-07
**Category:** feature
**Behaviour:** changing
**Request:** the **Request** of `change_request.md` in this folder, verbatim:

> Make a start while something else holds the tracker's address print one plain message and stop. Run from `products/tracker17/` under `python3 main.py`. Today the bind error propagates out of the listener (`web/listener.py:5`, "A bind error propagates: the signal that the address is taken is the next change unit's"), so the console shows the standard library's traceback. After this change the console shows a single plain, one-paragraph message that says something else is already using the address and what to do next (SRS FR-3; UXD UX-S2 error), with its words taken from the product's content record (`docs/CONTENT.md:250`), and no string invented in code. The start exits with a failing status, serves nothing, and writes nothing to the saved data: no `data/` folder or file is created or changed by the failed start. A start that cannot read its saved data keeps stopping with its own one plain message as sealed.
>
> Tests ship with it: an integration test that a start against an address already held prints the message, returns a failing status and leaves the saved-data location untouched, and an end-to-end or process-level test under the real start command, `python3 main.py`, with another listener holding the address. `pytest tests/` and `pytest tests/e2e/` each exit 0.
>
> **Must not be weakened or added:** the SDD's seams are used as written, with the composition root still the only place that wires concrete parts (`main.py`); the console shows nothing before the ready line on a good start (UX-S2); no tasks, add-task form, People or All tasks links, rename or delete; no unreadable-data page and no second-tracker refusal (another tracker on the same saved data is `protect-saved-data`'s, not this unit's); the setup README is not touched beyond what the tests need; project creation, its refusals, the not-found page and saved data keep behaving as sealed.

---

## Change Summary

Today, when another program already holds the tracker's address, `python3 main.py` ends with a Python traceback whose last line is `OSError: [Errno 48] Address already in use`. After this change the start prints one plain message instead. The message says something else is using the address and tells the operator what to do. The start then ends with a failing status and writes nothing to the saved data.

The paths below are relative to the product root, which is the directory `system/projects/tracker17/project.md` names in `Product path:`. The FDR rules cited as `R-n` and `PD-n` are `docs/fdr.md`'s. The SDD, UXD and CONTENT sections cited are `docs/SDD.md`, `docs/UXD.md` and `docs/CONTENT.md` under that root. `CP-1` to `CP-29` are the rules of the sealed change spec `system/projects/tracker17/journey/tobiishi/trail/2026-10-07_create-a-project-that-stays/change_spec.md`, and `CP-30` to `CP-38` are those of `system/projects/tracker17/journey/tobiishi/trail/2026-10-07_a-not-found-page/change_spec.md`. This change realizes R-4's second sentence, which the FDR already states. It adds no rule the FDR does not hold.

**Sizing.** The acceptance boundary is one operator action: starting the tracker while its address is held, and being told so in plain words (SDD § 6 S-1, *Behaviour*, "Starting while something else holds the address shows one plain message"; UXD UX-S2, Error; R-4). The message, the failing exit, the guarantee that nothing is written and their tests are that one capability's acceptance obligations, so they stay together under `<CORE>/prompts/pm_right_size.md` § *Right-size to one honest merge*. The pointer test's reverse direction keeps the trace between documents and code honest. It is a different system responsibility, with its own boundary (SDD § 4 TS-4), and the request leaves it to a later unit.

---

## Rules

### A start that cannot take its address

- **CP-39:** When `python3 main.py`, typed from the product root, cannot take the tracker's address because another program already uses it, the start fails. The address is `127.0.0.1:8017`, fixed by SDD § 4 RT-5. A failed start:
  - shows exactly one message in the console, on standard error, and writes nothing to standard output;
  - shows no ready message and no Python traceback;
  - ends by itself, without the operator stopping it, with a non-zero exit status;
  - leaves the other program holding the address, so a connection to `127.0.0.1:8017` still reaches that program afterwards.

  Today such a start writes a traceback to standard error that ends `OSError: [Errno 48] Address already in use`, and exits 1. The cause is the bind error that `web/listener.py:5` says it lets propagate. *(R-4; SRS FR-3; SDD § 4 OB-2; UXD UX-S2)*
- **CP-40:** The message is one paragraph on one line. It says the tracker didn't start because something else is already using the address. It names the address as `127.0.0.1:8017`, and it tells the operator to stop that program and then start the tracker again. Its words are CONTENT's first example under § Message patterns, Error, "Terminal messages" (`docs/CONTENT.md:250`). The only change is that the tracker's own address replaces the example's `127.0.0.1:8000`. The console line is therefore:

  `The tracker didn't start, because something else is already using the address 127.0.0.1:8017. Stop that program, then start the tracker again.`

  No word in the message is one CONTENT does not hold. *(UXD UX-S2; CONTENT § Message patterns, Error, "Terminal messages"; SDD § 4 EX-11)*
- **CP-41:** A start that fails under CP-39 writes nothing to the saved data. When no saved data exists, no `data/` directory or file exists afterwards. When saved data exists, every byte of every file in its directory, and the directory's listing, are the same afterwards as before. *(R-4; SRS FR-3; SDD § 4 OB-2)*

### Which starts CP-39 covers

- **CP-42:** CP-39 covers every start in which another program's use of the address stops the tracker from taking `127.0.0.1:8017`, whatever address form that program listens on. A start that can still take `127.0.0.1:8017` is not in CP-39, and starts and serves as it does today. One such case: on macOS, a program listening on `0.0.0.0` at port 8017 leaves the start able to take `127.0.0.1:8017`. A start that cannot take the address for some other reason is not in CP-39 either, for example when the machine refuses the address to the tracker. Out of Scope names it. Which message a start shows when the program holding the address is another tracker on the same saved data is R-5's, and this change does not fix it.
- **CP-43:** When the saved data cannot be read, the start shows the unreadable-data message alone, as CP-7 sealed it, whether or not something else holds the address. The console never shows both failure messages for one start. Standard output stays empty, the exit status is non-zero, and every byte of the saved data is unchanged (CP-7). *(R-24, R-27; SRS FR-3, FR-8)*

### What stays as it is

- **CP-44:** A start that takes its address behaves as CP-1 sealed it. The console shows nothing until the ready message, and the ready message is the first thing it shows (R-2; UXD UX-S2).
- **CP-45:** The change is built behind the parts and seams SDD § 3 names, as written. `main.py` stays the only module that wires a concrete part to an abstraction (SDD § 3; the module docstring of `main.py`). The change adds no part, no seam and no dependency outside Python's standard library (PD-6; `docs/adr/0001-rule-core-behind-server-rendered-pages.md`; `docs/adr/0002-standard-library-only-no-web-framework.md`). The message's words come from `docs/CONTENT.md` through the content step (SDD § 4 EX-11).

### Its tests

- **CP-46:** `pytest tests/` and `pytest tests/e2e/`, each typed from the product root inside the virtual environment that holds the test dependencies, each exit 0 (SDD § 6, "Both suites pass"). They include:
  - an integration test of a start against an address that another listener already holds. It finds the CP-40 line as the only console output, on standard error, with nothing on standard output and a non-zero status. It finds the saved-data location unchanged under CP-41, both where no saved data exists and where saved data does exist;
  - a process-level or end-to-end test that runs the real start command, `python3 main.py`, from the product root while another listener holds `127.0.0.1:8017`. It finds that the process ends by itself with a non-zero status, that standard error is the CP-40 line, that standard output is empty, and that `data/` at the product root is as it was before the start (CP-39, CP-40, CP-41). Afterwards a connection to `127.0.0.1:8017` still reaches the holding listener (CP-39);
  - a test that a start with unreadable saved data and a held address shows the unreadable-data message alone (CP-43).

  The tests in `tests/integration/test_start.py` that check an unreadable start (CP-7, CP-8) stay, and pass unchanged.

---

## Examples

| Rule | Scenario | Expected behaviour |
|---|---|---|
| CP-39 | Another program listens on `127.0.0.1:8017`. No `data/` exists. The operator types `python3 main.py` from the product root | The process ends by itself with a non-zero status. Standard output is empty. Standard error holds the CP-40 line and no traceback. |
| CP-39 | After that failed start, a connection is made to `127.0.0.1:8017` | The holding program answers it, as before the start. |
| CP-40 | Any start CP-39 covers | Standard error is exactly: `The tracker didn't start, because something else is already using the address 127.0.0.1:8017. Stop that program, then start the tracker again.` |
| CP-41 | Address held, no saved data | No `data/` directory exists afterwards. |
| CP-41 | Address held. `data/tracker.json` holds project `Alpha` | The file's bytes and the directory's listing are unchanged afterwards. |
| CP-42 | On macOS, a program listens on `0.0.0.0` at port 8017 | The start takes `127.0.0.1:8017` and shows the ready message, as today. |
| CP-42 | Another program listens on `127.0.0.1:8017` with address reuse switched on | The start cannot take the address. CP-39 applies. |
| CP-43 | Address held, and `data/tracker.json` cannot be read | Only the unreadable-data message, naming the location. No address message. Standard output empty, non-zero status, file bytes unchanged. |
| CP-44 | Nothing holds the address. `python3 main.py` | The first console output is the ready message, as today. |
| CP-45 | Reading the change's diff | No new part, seam or outside dependency. Only `main.py` wires concrete parts. The message's words are ones `docs/CONTENT.md` holds. |
| CP-46 | `pytest tests/`, then `pytest tests/e2e/`, from the product root | Both exit 0, and the tests CP-46 lists are among those run. |

---

## Verified Claims

The commands ran on 2026-10-07 against commit `e21a54119`, in a disposable copy of the product made with `git archive HEAD products/tracker17` (`<CORE>/roles/CROSS_ROLE.md` § *Every seat*), on macOS under Python 3.14.7. `git diff --stat e21a54119 0bbb53c5d -- products/tracker17` is empty, so the same holds at this branch's base, `0bbb53c5d`. A holder in the rows below is a separate Python process that binds a TCP socket and listens.

| Claim | Verified by | What came back |
|---|---|---|
| Today a start whose address is held prints a traceback and exits 1, with nothing on standard output (CP-39) | A holder on `127.0.0.1:8017`, then `python3 main.py` from the copy's product root, which had no `data/` | Exit `1`. Standard output empty. Standard error a traceback through `web/listener.py` line 62 `listen`, ending `OSError: [Errno 48] Address already in use`. |
| Today that start writes nothing to the saved data, with or without saved data present (CP-41) | The row above, then `ls -d data`. Then the same start with `data/tracker.json` holding project `Alpha`, comparing `shasum` before and after | `ls`: "No such file or directory". With `Alpha` saved: exit `1`, the same traceback, `shasum` unchanged, and `data/` listing only `tracker.json`. |
| With unreadable saved data and a held address, the start shows the unreadable-data message alone (CP-43) | A holder on `127.0.0.1:8017`, `data/tracker.json` holding `{"next_project_id": 3, "projects": [ truncated`, then `python3 main.py` | Exit `1`. Standard output empty. Standard error one line: "The tracker didn't start, because it couldn't read its saved data at /private/tmp/…/products/tracker17/data. Nothing in it was changed." `shasum` unchanged. |
| Which holders stop the start, on macOS (CP-42) | `main.start(("127.0.0.1", P), <fresh temp>/data)` with a holder on port P, four ways, with a 3-second timer | Holder on `127.0.0.1` without address reuse, and with it: `OSError` errno 48 "Address already in use" each time. Holder on `0.0.0.0` without address reuse, and with it: the start took the address and was still serving at 3 seconds each time. |
| The address is `127.0.0.1:8017` (CP-39, CP-40) | Reading `docs/SDD.md:285-288` (RT-5) and `main.py:20` | RT-5: "The address is `127.0.0.1:8017`, fixed in one constant, `ADDRESS` in `main.py`." `main.py:20`: `ADDRESS = ("127.0.0.1", 8017)`. |
| CONTENT holds the message's words (CP-40) | Reading `docs/CONTENT.md:243-250` | The formula says "one paragraph that begins "The tracker didn't start", gives the reason, and gives one action". Line 250 reads "The tracker didn't start, because something else is already using the address 127.0.0.1:8000. Stop that program, then start the tracker again." |
| `web/listener.py:5` says the bind error propagates (CP-39) | Reading `web/listener.py:1-6` | "A bind error propagates: the signal that the address is taken is the next change unit's." |
| `main.py` is the only module that wires concrete parts (CP-45) | Reading `main.py:1-2` | "The composition root — the only place this product wires a concrete implementation to an abstraction." |
| The unreadable-start tests CP-46 keeps pass today | `python3 -m pytest -p no:cacheprovider -q tests/integration/test_start.py tests/integration/test_listener.py` in the copy | `19 passed, 1 failed`. The failure is `test_data_is_ignored_by_version_control`: `git check-ignore` exited 128 because the `git archive` copy is not a repository. The test does not concern this change. Each unreadable-start test passed. |
| Today the holding program still answers on the address after the failed start (CP-39) | A holder on `127.0.0.1:8017` that answers one connection with `holder-here`, then `python3 main.py`, then a client connection to `127.0.0.1:8017` | Start exit `1`. The client received `b'holder-here'`. No `data/` afterwards. |
| The highest `CP-<n>` in the project's record is CP-38, so this series starts at CP-39 | `grep -rhoE 'CP-[0-9]+' system/projects/tracker17/journey/tobiishi/trail/ products/tracker17`, numbers sorted | Highest is `38`. |

---

## Out of Scope

- A start that cannot take the address for a reason other than another program using it, for example when the machine refuses the address to the tracker. Its behaviour is unchanged here (CP-42). Locked Answers Gap 5 says why.
- The refusal of a second tracker on the same saved data (R-5), and the message it shows. It is `protect-saved-data`'s, as the request says. Until that unit lands, a second tracker started from the same copy finds its address held, and CP-39 gives it the CP-40 message, which is true of it. Nothing here fixes which message R-5's case shows once that unit lands (CP-42).
- The wording of the unreadable-data message, which stays as CP-7 sealed it. CONTENT's third Terminal messages example adds a sentence about Setting saved data aside, and this change does not add it.
- The unreadable-data page (UXD UX-S9; R-25, R-26).
- Choosing another address, or an option to the start command. The address is fixed (PD-10; SDD § 4 RT-5, § 9 TO-6).
- Anything about the program that holds the address beyond its keeping the address.
- Tasks, the add-task form, the People and All tasks links, renaming a project and deleting one. The request excludes each.
- The setup instructions in `README.md`, beyond what the tests need. The next station delivers them.
- The pointer test's reverse direction (station reached-when 8), and the check that the station's whole reached-when holds. Later units of this station deliver them.
- Project creation, its refusals, the not-found page and the saved data's behaviour, which stay as `CP-1` to `CP-38` sealed them.
- Windows (PD-8).

---

## Locked Answers (the divergence record — self-review 2026-10-07)

- **Gap 1 — which console stream:** the message goes to standard error, and standard output stays empty (CP-39). The request says only "the console". Standard output carries the ready message, so keeping it empty on a failed start means nothing that reads standard output for the ready message can take a failure for it. The unreadable-data failure behaves the same way today (Verified Claims, CP-43 row). The choice is reversible.
- **Gap 2 — the exit status:** non-zero, with no particular value fixed (CP-39). The request says "a failing status", and CP-7 fixes the unreadable-data failure to the same extent. Today the status is 1.
- **Gap 3 — the address the message names:** `127.0.0.1:8017`, not the `127.0.0.1:8000` of CONTENT's example (CP-40). The example illustrates the formula, and CONTENT's ready-message example uses the same 8000. SDD § 4 RT-5 records the tracker's address as `127.0.0.1:8017`. A message naming an address the tracker did not try would send the operator to stop a program that is not in the way.
- **Gap 4 — which starts count as "something else holds the address":** the ones where another program's use of the address stops the start from taking `127.0.0.1:8017` (CP-42). The request names the case but not its edge. On macOS a program on `0.0.0.0` at the same port does not stop the start (Verified Claims). The tracker then takes its address and works, so a message saying it didn't start would be false. Keying the rule to whether the start can take the address keeps the message true on each supported system. It makes no claim about how each system decides.
- **Gap 5 — a start refused the address for another reason:** not covered, and its behaviour is unchanged (CP-42; Out of Scope). The request, R-4, SRS FR-3 and UXD UX-S2 each name only an address something else is using. Showing this message for another cause would state a cause the tracker has not established, which CONTENT § Voice rules out ("State only what the tracker established"). No upstream document gives this case its own words.
- **Gap 6 — both failures at once:** the unreadable-data message alone (CP-43). The request says a start that cannot read its saved data "keeps stopping with its own one plain message as sealed". UXD UX-S2 and R-4 each speak of one plain message, so a start shows one message, never two. That is today's behaviour (Verified Claims).
- **Gap 7 — the holding program keeps the address:** a connection to `127.0.0.1:8017` still reaches it after the failed start (CP-39). The request does not say. Without this rule, a start that shared the address with its holder could pass every other check. A start that disturbed another program would also act beyond the tracker's own data. R-5 sets the same expectation for a running tracker under a second start.
- **Gap 8 — "serves nothing" made observable:** the process ends by itself and shows no ready message (CP-39). Today the start also ends by itself, but it ends in a traceback.
