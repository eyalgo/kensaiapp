# Change Spec — Create a first project that stays after a restart

**Date:** 2026-10-07
**Category:** feature
**Behaviour:** changing
**Request:** the **Request** of `change_request.md` in this folder, verbatim:

> Make `python3 main.py` start a working tracker in which a person can create a first project, see it, and still find it after stopping and starting. Run it from `products/tracker17/`. It prints the address and the saved-data location, nothing before them, and serves until stopped. The browser shows the first-run Projects page with the create form. Beside the description field a note says the description cannot be changed later and gives the most characters it holds, and that number equals the field's `maxlength`. Creating a project lands on its own page, which shows its name and description and says it has no tasks yet, with no add-task form. A blank name and a name already in use (case ignored) are each refused beside the name field, the typed text is kept, and the page opens with keyboard focus in the name field and the reason as its accessible description. A name over the maximum, sent in a request no page can send, gets the page that gives the reason, holds none of the sent text, and leaves the saved data unchanged. Projects lists every project by name, and a project is still listed after a stop and a start. The data is saved under `data/`, which stays out of version control, so `git status --short` lists nothing there after a project is created. This is one path through all five parts and all seven seams of SDD § 3 (`domain/projects.py`, `application/`, `persistence/`, `web/`, `main.py`), not a shortcut through one. A start that cannot read the saved data stops with one plain message and writes nothing (SDD § 4 SD-4).
>
> Tests ship with it: `pytest tests/` and `pytest tests/e2e/` each exit 0, between them holding at least one unit, one integration and one end-to-end test. They include the tests SRS AC-6 (for a project) describes, an end-to-end test of focus and accessible description on a refused name (SDD § 4 EX-4, EX-14, RT-9), an end-to-end test filling the description to its maximum with line breaks and finding it saved whole (AC-20, description half), the over-long name test (AC-12, § 4 RT-8, RT-10, § 11 R-10), and the integration test that the sentence's number equals `maxlength`. SRS AC-9 (interrupted save) and AC-18 (visible failures) are covered here as far as saving a project and starting the tracker reach them.
>
> **Must not be weakened or added:** the SDD's seams are used as written; no tasks, add-task form, People or All tasks links, rename or delete; no unreadable-data page and no second-tracker refusal; the setup README is not touched beyond what the tests need.

---

## Change Summary

tracker17's start command today runs an empty `main` and exits, so the product has no behaviour yet. This change makes `python3 main.py` start the tracker in the browser, where the operator creates a project, sees it listed, and finds it again after stopping and starting the tracker, with its refusals, its saving and its tests.

The paths below are relative to the product root, which is the directory `system/projects/tracker17/project.md` names in `Product path:`. The FDR rules cited as `R-n` and `PD-n` are `docs/fdr.md`'s. The SDD, SRS, UXD and CONTENT sections cited are `docs/SDD.md`, `docs/SRS.md`, `docs/UXD.md` and `docs/CONTENT.md` under that root. Every word a page or the console shows is `docs/CONTENT.md`'s (SDD § 4 EX-11), so the rules below state what a message must say and leave its wording to the content step.

**Sizing.** The acceptance boundary is one operator action, creating a project and finding it again after a restart, from SDD § 6 S-1 *Reached when*, *Behaviour* and *Command*. Its refusals, its saving, its start and its tests are that one capability's acceptance obligations, so they stay together under `<CORE>/prompts/pm_right_size.md` § *Right-size to one honest merge*. The not-found page and the address-taken message are separate responsibilities with their own boundaries, and the request already leaves them to later change units.

---

## Rules

### Starting and stopping the tracker

- **CP-1:** `python3 main.py`, typed from the product root, takes no argument and starts the tracker. Once the tracker answers requests, the console shows one ready message that states the address to open and then the saved data's location, in that order. The console shows nothing before the ready message. *(R-1, R-2; CONTENT § Message patterns, Loading)*
- **CP-2:** The address is an `http://` address on the loopback interface, fixed by SDD § 4 RT-5, and it is the same address on every start (R-4, PD-10). Which port it uses is development-design's choice (SDD § Open Questions, "Which port the fixed address uses").
- **CP-3:** The tracker serves until it is stopped. An interrupt typed in its console (Ctrl-C) stops it. That stop shows no Python traceback in the console. Every project the tracker reported as created before the stop is in the saved data afterwards.
- **CP-4:** The saved data is kept under `data/` at the product root. The location the ready message states is an absolute path that starts with the absolute path of that `data/` directory. The location is the same whatever directory `main.py` is started from (R-16).
- **CP-5:** Version control ignores `data/`, so after a project is created, `git status --short` run in the copy lists nothing under `data/` (R-16; SDD § 4 SD-6). Today nothing ignores it: `git check-ignore -v data/projects.json`, run from the product root, prints nothing and exits 1.
- **CP-6:** When no saved data exists, the tracker starts empty, with no projects and no sample data (R-17).
- **CP-7:** A start whose saved data cannot be read does not serve. It shows one plain console message that says the tracker didn't start because it couldn't read its saved data and names the saved data's location. It shows no ready message, exits with a non-zero status, and leaves every byte of the saved data unchanged. *(R-24, R-27; SDD § 4 SD-4, OB-2; CONTENT § Message patterns, Error, "Terminal messages")*
- **CP-8:** Saved data counts as unreadable under CP-7 when the tracker cannot read all of it, or when it holds a project that breaks a rule this change sets: a name with no non-whitespace character (CP-14), a name another project also has, compared exactly (CP-15), or a name or description over its maximum (CP-16). *(R-21, R-22, R-23; SDD § 4 SD-5)* The members of R-21 and R-22 that concern tasks, assignees, labels, comments and the operator's name are not fixed here, because each arrives with the change that adds its data. The tracker never loads part of the saved data and drops the rest (R-23).

### The Projects page

- **CP-9:** Opening the address shows the Projects page. Every page this change serves carries the header, and the header links to Projects and to no other area (SDD § 4 EX-12). No page this change serves shows, links to or points in words to tasks, People, All tasks, renaming or deleting.
- **CP-10:** When no project exists, the Projects page says there are no projects yet and invites a first project, with the create form in view (R-95; UXD UX-S3, first-run state).
- **CP-11:** The create form has a name field, a multi-line description field and a Create button. The name field's `maxlength` is 200 and the description field's `maxlength` is 4,000 (R-76; SDD § 4 RT-10). Beside the description field, in view before Create is pressed, a note says the description can't be changed after the project is created and states the most characters the description can hold. The number that note states, read as a number, equals the description field's `maxlength`. The name field states no maximum (UXD UX-F2).
- **CP-12:** The Projects page lists every project. Each entry shows the project's name, as a link to that project's page, and its description when it has one (UXD UX-S3). Entries are in ascending order of name with letter case ignored. Two names that are equal with letter case ignored appear in ascending order of their exact text. Letter case here spans Unicode letters, not ASCII alone. The exact case mapping is development-design's choice, and `A` to `Z` and `a` to `z` must compare equal under it.

### Creating a project

- **CP-13:** Pressing Create with a name that holds at least one non-whitespace character, and an optional description, creates the project. The name and the description are saved exactly as typed, surrounding spaces included, except that each line break is saved as one character (R-30, R-77, R-80). The browser then shows the new project's page.
- **CP-14:** A name with no non-whitespace character, such as an empty name or a name of spaces, tabs or line breaks only, is refused (R-31). Whitespace here spans every character Unicode classes as whitespace, not ASCII alone, so a name of no-break spaces only is refused too.
- **CP-15:** A name already used by another project is refused. Names are compared exactly, so with `Alpha` saved, `Alpha` is refused, while `alpha` and `Alpha ` with a trailing space are each accepted as different names (R-32, R-80).
- **CP-16:** A name over 200 characters, or a description over 4,000 characters, is refused, and the tracker never shortens a value to make it fit. One character is one Unicode code point, counted on the value as it would be saved, and a line break counts as one character (R-76, R-77, R-78). A name of exactly 200 characters and a description of exactly 4,000 characters are accepted (R-79).
- **CP-17:** A project's page shows the project's name and its description, and says that the project has no tasks yet. It carries no add-task form, no words inviting a first task, and no rename or delete control (SDD § 6 S-1, *Behaviour*; UXD UX-S4).
- **CP-18:** The page that answers a successful Create shows one completion line that names the created project (UXD UX-I4; CONTENT § Message patterns, Completed, verb "created"). Reloading that page, or going back and then forward to it, creates no second project and shows the same line (R-106, PD-11).
- **CP-19:** A refusal under CP-14 or CP-15 is answered by the Projects page, which shows the reason in plain words beside the name field (R-100; CONTENT § Message patterns, Error, "A refusal"). The name and description fields hold exactly what was typed. When the page opens, the name field is in view and has keyboard focus, and the reason is the name field's accessible description. The reason itself never takes focus. *(UXD UX-I3; SDD § 4 EX-4, EX-14, RT-9)*
- **CP-20:** A submission holding a value over its maximum under CP-16 cannot come from the tracker's own form, so the request that sends one is built by hand. It is answered by the page that gives the reason beside the field whose value was too long, and that field has keyboard focus when the page opens. The name field is the one when both values were too long. That page holds none of the sent text, in any field or anywhere else on the page. A submission that is over-long and also breaks CP-14 or CP-15 gets this answer, and the reason given is the over-long one. *(PD-11; SDD § 4 RT-8, RT-10; § 11 R-10)*
- **CP-21:** A refused Create leaves the saved data unchanged, and the Projects page lists no new project, before or after a restart (R-100). Reloading the page that answers a refusal shows the same reason and creates nothing (R-106, PD-11).
- **CP-22:** A Create submission that does not come from the tracker's own pages is refused and changes nothing (R-110). Which submissions count as coming from the tracker's own pages is fixed by SDD § 4 SEC-2: a submission is accepted only when it names the tracker's own address as its host and the browser marks it `Sec-Fetch-Site: same-origin`. Every other mark (`cross-site`, `same-site`, `none`) and a submission with no mark are refused.
- **CP-23:** Every page this change serves shows a typed value as text, so a name such as `<b>A&B</b>` displays as typed (R-112). No page loads anything from outside the machine (R-111), runs a script (SDD § 4 EX-2), or shows error text produced by Python (R-108).

### Saving

- **CP-24:** The tracker reports a project as created only after the project is in the saved data (R-18). After the tracker is stopped and started again, the Projects page lists every project that was created, with its name and description unchanged (R-15; SRS AC-6, the project part).
- **CP-25:** When saving a new project fails for a reason that is not a refusal, the console shows a message naming the action and the error (R-107). The browser shows a page saying the tracker couldn't create the project and that nothing was changed, with what was typed still in the form (UXD UX-I5; CONTENT § Message patterns, Error, "A failure that is not a refusal"). The saved data is unchanged, and the Projects page does not list the project, before or after a restart (R-18).
- **CP-26:** When the tracker is stopped part-way through saving a new project, by a crash or a killed process, the next start reads the saved data as the state either before that Create or after it, never as a mix of the two and never as unreadable (R-19; SRS AC-9).

### Where the code lives, and its tests

- **CP-27:** The tracker's code sits in the five parts SDD § 3 names, at the product root: `domain/`, with the project rules in `domain/projects.py`, then `application/`, `persistence/`, `web/` and `main.py`. Creating a project crosses each of the seven seams SDD § 3 names (`SM-1` to `SM-7`), under the contracts and the direction of dependence that section states. These parts and seams are fixed by SDD § 3 and § 6 S-1 *Artifact*, and by `docs/adr/0001-rule-core-behind-server-rendered-pages.md`. The tracker imports nothing outside Python's standard library (PD-6; `docs/adr/0002-standard-library-only-no-web-framework.md`).
- **CP-28:** Every dependency `pyproject.toml` declares is fixed to an exact version, and the test dependencies are locked, with every dependency they pull in, in one committed file (PD-7; SDD § 4 RT-4). Today `pyproject.toml` `[dependency-groups]` `dev` declares floors, not exact versions: `"mypy>=2.3"`, `"pytest>=9.0"` and `"ruff>=0.16"`.
- **CP-29:** `pytest tests/` and `pytest tests/e2e/`, each typed from the product root inside the virtual environment that holds the test dependencies, each exit 0 (SDD § 6, "Both suites pass"). Between them they hold at least one unit test, one integration test and one end-to-end test, and the end-to-end tests drive Chromium against a tracker started by `main` (PD-12; SDD § 4 TS-1). They include:
  - a test that a created project is listed with its name and description after a stop and a start (CP-24; SRS AC-6, the project part);
  - an end-to-end test that a refused name opens the page with keyboard focus in the name field and the reason as that field's accessible description (CP-19);
  - an end-to-end test that fills the description field to its maximum, with line breaks in the text, and finds the project created with the description saved whole (CP-16; SRS AC-20, the description half);
  - a test that sends a tracker started by `main` a name over its maximum, in a request no page of the tracker can send, and finds the reason given, none of the sent text on the page, and the saved data unchanged (CP-20; SRS AC-12);
  - a test that sends a description over its maximum and finds it refused (CP-16; SDD § 4 RT-10, "adds a test that a longer value is refused");
  - an integration test that builds the create form and finds the number its note states equal to the description field's `maxlength` (CP-11);
  - a test per refusal under CP-14 and CP-15 that finds the reason given and the saved data unchanged (CP-21; SRS AC-12);
  - a test that a Create submission not from the tracker's own pages is refused with the saved data unchanged (CP-22);
  - a test that saved data breaking each rule CP-8 names is reported as unreadable, with its bytes unchanged (CP-7, CP-8; SDD § 4 SD-5);
  - a test that interrupts a save and finds the next start reading the state from before or after (CP-26; SRS AC-9);
  - a test that induces a save failure and finds the console message, the browser's failure page and the saved data unchanged (CP-25; SRS AC-18);
  - a test that `data/` is ignored by version control after a project is created (CP-5).

---

## Examples

| Rule | Scenario | Expected behaviour |
|---|---|---|
| CP-1 | `python3 main.py` from the product root | Nothing shows until the tracker answers. Then one message states the address, then the saved-data location. |
| CP-2 | The tracker is started twice, one start after the other has stopped | The ready message states the same `http://` loopback address both times. |
| CP-3 | Ctrl-C in the tracker's console after creating `Alpha` | The tracker stops with no traceback. The next start lists `Alpha`. |
| CP-4 | `python3 /path/to/product/main.py` typed from the home directory | The ready message states the same location as a start typed from the product root, under the product's `data/`. |
| CP-5 | `Alpha` created, then `git status --short` in the copy | No line names a path under `data/`. |
| CP-6 | First start, no saved data | The Projects page lists no project and shows no sample data. |
| CP-7 | Saved data that is not readable in full, for example a truncated file | One console message says the tracker didn't start and names the location. No ready message, a non-zero exit status, and the saved data's bytes are unchanged. |
| CP-8 | Saved data holding two projects both named `Alpha` | Reported as unreadable under CP-7. |
| CP-8 | Saved data holding one project whose name is 201 characters | Reported as unreadable under CP-7. |
| CP-9 | Any page this change serves | The header links to Projects only. No People or All tasks link. |
| CP-10 | First run, the Projects page | The page says there are no projects yet and invites a first one, with the create form in view. |
| CP-11 | The create form | The name field's `maxlength` is 200, the description field's is 4,000, and the note beside the description field states 4,000 as the maximum and says the description can't be changed later. |
| CP-12 | Projects `beta`, `Alpha` and `alpha` created in that order | Listed as `Alpha`, `alpha`, `beta`. `Alpha` comes before `alpha` by exact text. |
| CP-13 | Create with name `  Alpha  ` and a two-line description | Created. The project's page shows the name with its surrounding spaces kept and the description with its line break. |
| CP-14 | Create with a name of three spaces | Refused beside the name field. No project is created. |
| CP-14 | Create with a name of two no-break spaces (U+00A0) | Refused beside the name field. No project is created. |
| CP-15 | `Alpha` exists, Create `Alpha` | Refused beside the name field. |
| CP-15 | `Alpha` exists, Create `alpha` | Created. Names are compared exactly. |
| CP-16 | Create with a description of exactly 4,000 characters, line breaks included, typed in the field | Created, with the description saved whole and not shortened. |
| CP-17 | The page of the newly created `Alpha` | Shows `Alpha` and its description, says the project has no tasks yet, and has no add-task form and no rename or delete control. |
| CP-18 | Reload the page that answered the Create of `Alpha` | Still one project named `Alpha`, and the same completion line. |
| CP-19 | `Alpha` exists, Create `Alpha` with description `notes` | The Projects page opens with focus in the name field, the reason as its accessible description, `Alpha` still in the name field and `notes` still in the description field. |
| CP-20 | A hand-built submission with a 201-character name | The page gives the reason beside the name field, contains none of the 201 characters, and the saved data is unchanged. |
| CP-20 | A hand-built submission with a blank name and a 4,001-character description | The reason given is the over-long description's, and the page holds none of the sent text. |
| CP-21 | Reload the page that answered a refused Create | The same reason shows. Nothing is created. |
| CP-22 | A Create submission marked `Sec-Fetch-Site: cross-site` | Refused. The saved data is unchanged. |
| CP-22 | A Create submission carrying no `Sec-Fetch-Site` mark | Refused. The saved data is unchanged. |
| CP-22 | A Create submission marked `Sec-Fetch-Site: none`, as one typed into the address bar would be | Refused. The saved data is unchanged. |
| CP-23 | Create a project named `<b>A&B</b>` | The list and the project's page show `<b>A&B</b>` as text. Nothing renders bold. |
| CP-24 | Create `Alpha` with description `x`, stop, start | The Projects page lists `Alpha` with description `x`. |
| CP-25 | Saving fails while `Alpha` is created | The console names the action and the error. The browser says the tracker couldn't create `Alpha` and nothing was changed, with `Alpha` still in the form. `Alpha` is not listed, before or after a restart. |
| CP-26 | The process is killed part-way through saving `Beta`, with `Alpha` already saved | The next start lists `Alpha`, and lists `Beta` or not, and never reports the saved data as unreadable. |
| CP-27 | Reading the product root after the change | `domain/projects.py`, `application/`, `persistence/`, `web/` and `main.py` exist, and nothing outside `tests/` imports a package outside the standard library. |
| CP-28 | Reading `pyproject.toml` after the change | No declared dependency carries a range such as `>=`. A committed lock file pins the test dependencies. |
| CP-29 | `pytest tests/`, then `pytest tests/e2e/`, from the product root | Both exit 0, and the tests listed in CP-29 are among those run. |

---

## Verified Claims

All commands ran on 2026-10-07 against the main checkout at commit `311cd4b6b`, from the product root, which holds the same tree this change's branch was created from.

| Claim | Verified by | What came back |
|---|---|---|
| `main.py` today starts nothing and prints nothing (Change Summary) | `python3 main.py; echo $?` under Python 3.14.7 | No output, exit status 0. |
| Nothing ignores `data/` today (CP-5) | `git check-ignore -v data/projects.json` | No output, exit status 1. |
| `pyproject.toml` declares floors, not exact versions (CP-28) | Reading `pyproject.toml` `[dependency-groups]` | `dev = ["mypy>=2.3", "pytest>=9.0", "ruff>=0.16"]`. |
| The five parts do not exist yet (CP-27) | `ls domain application persistence web data` | "No such file or directory" for each of the five. |
| `pytest tests/` passes today and `tests/e2e/` holds no test (CP-29) | `python3 -m pytest tests/ -q`, then `python3 -m pytest tests/e2e/ -q` | `1 passed`, exit 0. Then `no tests ran`, exit 5. `tests/e2e/` holds only `.gitkeep`. |
| tracker16-X refuses a blank project name by Python's `str.strip()`, which treats a no-break space as whitespace (Gap 13) | Reading `task-tracker-X/tasktracker16x/domain/project.py`, then `python3 -c "print(repr('\u00a0'.isspace()), repr('\u00a0Alpha'.strip()))"` | The check reads `if not name.strip():`. The command printed `True 'Alpha'`. |
| No `CP-<n>` identifier is in use in the project's record, so this series starts at CP-1 | `grep -rn "CP-[0-9]"` over `system/projects/tracker17/` and the product root | No match. `system/projects/tracker17/journey/tobiishi/trail/` is empty. |

---

## Out of Scope

- Tasks, the add-task form, the People and All tasks links, renaming a project and deleting one. The request excludes each, and SDD § 6 S-1 *Not in this slice* places them in later slices.
- The page for saved data that cannot be read (UXD UX-S9; R-25, R-26) and the refusal of a second tracker (R-5). The request excludes both, and R-6 waits with the second tracker.
- What an address naming no project shows (R-105; UXD UX-S10). A later change unit of this station delivers the not-found page. Until then, CP-23's ban on Python error text is the only rule on such an address.
- The console message when something else holds the address (R-4, second sentence). A later change unit of this station delivers that message.
- The setup instructions in `README.md`, beyond what the tests need. The next station delivers them.
- Editing a project's description after creation, which never exists (R-36; OOS-15).
- Whether `tests/timed_run.py` gains the create action in this change (SDD § 4 TS-5). The request does not name the timed run, so this spec sets no rule for it, and development-design applies TS-5 as it reads it.
- The docstring trace and its pointer test (SDD § 4 TS-3, TS-4), and every other SDD § 4 condition this spec does not name. Those conditions bind every slice in their own words, and this spec does not restate them.

---

## Locked Answers (the divergence record — self-review 2026-10-07)

- **Gap 1 — "a name already in use (case ignored)":** the duplicate check compares names exactly (CP-15), and letter case is ignored only in the order of the Projects list (CP-12). The request's words read as a case-blind duplicate check, which contradicts `docs/fdr.md` R-32 ("Names are compared exactly, so `Alpha` and `alpha` are different names") and the FDR's Examples row "Project `Alpha` exists, the operator creates `alpha` | Accepted". The sentence the request condenses, SDD § 6 S-1 *Behaviour*, puts "ignoring case" on the list ("Projects lists every project by name, ignoring case"), and UXD UX-S3 does the same ("sorted by name, ignoring case"). On this reading the parenthesis moved one clause in condensing. A product-owner spec cannot change R-32, and a request meaning to change it would have come as `fdr-update-needed` rather than in scope. If the PM did mean a case-blind check, the route is `fdr-update-needed` to the Principal PM, and this spec is re-run after R-32 changes.
- **Gap 2 — what the Projects list shows for each project:** each entry shows its description too, and its name links to the project's page (CP-12). The request says only "by name". UXD UX-S3 lists "every project by name, with its description", and without a link the project's page could be reached only by typing its address.
- **Gap 3 — two names equal with letter case ignored:** they are listed in ascending order of their exact text (CP-12). Exact comparison lets `Alpha` and `alpha` both exist, so the case-blind order alone leaves their order open. A tie broken by the printed text can be checked from the page alone.
- **Gap 4 — the completion line after Create:** the new project's page shows one line naming the created project (CP-18). The request does not mention it. UXD UX-I4 confirms every completed action in one line, and CONTENT § Message patterns, Completed fixes the verb "created".
- **Gap 5 — how a start that cannot read the saved data ends:** with no ready message and a non-zero exit status (CP-7). The request says only "stops with one plain message and writes nothing". A ready message would invite the operator to open an address nothing serves. A non-zero status is the reversible choice that lets a test and a shell tell the failed start from a stop.
- **Gap 6 — stopping the tracker:** an interrupt typed in its console stops it with no traceback (CP-3). The request says "serves until stopped" and names no way to stop. The interrupt is the stop the console offers with nothing written for it. A traceback would put Python's error text in front of the operator on an ordinary stop, against CONTENT § Message patterns, Error, which keeps that text to failures.
- **Gap 7 — the printed location and a start from another directory:** the location is an absolute path under the product's `data/`, and the same from any working directory (CP-4). The request says "Run it from `products/tracker17/`" and does not say what a start from elsewhere does. R-16 already fixes that the location "does not depend on the directory the start command was run from".
- **Gap 8 — an over-long description:** it is refused and tested as the over-long name is (CP-16, CP-29). The request names only the name. R-78 refuses every over-long value, and SDD § 4 RT-10 says "A slice that adds a text field writes the field's `maxlength` and adds a test that a longer value is refused". The description field is added here.
- **Gap 9 — which reason an over-long submission gets when it breaks more than one rule:** the over-long reason, beside the over-long field, and the name field when both are over-long (CP-20). The request does not cover the combination. The request already requires that the answer to an over-long name holds none of the sent text, and an answer that holds none of it can be given whatever else the submission breaks. Giving the blank or duplicate reason instead would leave that answer open to showing the over-long text.
- **Gap 10 — a Create submission from another origin:** refused, with a test (CP-22). The request does not name SRS AC-10. FDR R-110 binds every action, and Create is the first action that changes the saved data. A Create built without the check would ship a form any web page could submit.
- **Gap 11 — exact versions for every declared dependency:** the three existing floors become exact versions along with the new test dependencies (CP-28). The request does not name `pyproject.toml`. The tests this change ships need their dependencies declared, and PD-7 fixes "Every declared dependency" to an exact version. Pinning only the new ones would leave PD-7 broken in the same file this change edits.
- **Gap 12 — the header:** every page this change serves carries the header with Projects as its only link (CP-9). The request excludes the People and All tasks links. SDD § 4 EX-12 puts the header on every page and shows only the areas that exist so far.
- **Gap 13 — what counts as whitespace in a blank name:** every character Unicode classes as whitespace, a no-break space included (CP-14). The request says only "a blank name", and R-31 says "no non-whitespace character" without naming the set. PD-5 makes tracker16-X's rule tracker17's, and tracker16-X refuses with `if not name.strip():` in `task-tracker-X/tasktracker16x/domain/project.py`, under the docstring "Reject a name that has no non-whitespace character". Python's `str.strip()` removes Unicode whitespace: `python3 -c "print('\u00a0'.isspace())"` prints `True`.
