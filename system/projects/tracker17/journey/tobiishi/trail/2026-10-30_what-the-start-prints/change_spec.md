# Change Spec — the setup instructions name the third line a start can print

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing
**Request:** Make the README section "What the start prints" (`products/tracker17/README.md`, under `### What the start prints`) name all three lines a start can print. Today it describes the ready line and says a line starting `The tracker didn't start` is the other outcome. Add the third line, the one starting `The tracker couldn't read`, printed when the saved data cannot be read, beside those two, with a sentence that names the line and says the tracker is still running when it shows, and that tells the operator what to do next (follow "Setting saved data aside"). A reader of only this section must be able to say which of the three lines means the tracker is up and which means it stopped. The wording quoted is the program's own: the sentence beginning `The tracker couldn't read` matches the start of the text `_unreadable_line` builds in `main.py`, and the README quotes it rather than rewording it. The check is `awk '/^### What the start prints/{f=1;next} /^### /{f=0} f' products/tracker17/README.md | grep -cF "The tracker couldn't read"` printing 1 or more, where it prints 0 now. Both suites pass. What must not be weakened: the section still describes the ready line and the `The tracker didn't start` line; the README passage on the unreadable start under the starting instructions (the block quoted near lines 70 to 76) stays true and is not rewritten to fit, only pointed at if useful; `main.py`, the unreadable-data page, the lock and every test stay as they are, apart from any README test that already reads this text.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `languages/python/README.md` opened
**Inputs read:** fdr.md Settled · nfdr.md Settled · SDD.md Settled · SRS.md Settled · UXD.md Settled · CONTENT.md Settled · ADR-0016 Accepted

---

## Change Summary

The section "What the start prints" tells a reader about two of the outcomes a start has, and leaves out the one where the tracker runs on saved data it couldn't read. This change adds that line and makes the section say which lines mean the tracker is running and which means this start stopped.

**Sizing decision:** one change. The acceptance boundary is one reader capability, the section telling an operator what each line means (`pm_right_size.md` § Right-size to one honest merge; source: SDD § 6 `protect-saved-data`, *Artifact*, and the request). Every rule below is an obligation of that one passage, and it fits one flow.

---

## Rules

"The section" means the text of `products/tracker17/README.md` from the heading `### What the start prints` up to the next `### ` heading. The wording is the Content Editor's, except the fixed strings the rules name. No rule fixes where in the section a sentence stands.

### The third line

- **CP-736:** The section contains the string `The tracker couldn't read`, with a straight apostrophe. `awk '/^### What the start prints/{f=1;next} /^### /{f=0} f' products/tracker17/README.md | grep -cF "The tracker couldn't read"` prints 1 or more.
- **CP-737:** A sentence in the section names that line by those starting words and says it is what the start prints when the saved data can't be read. Any longer quotation of the line reads word for word as the terminal prints it: `The tracker couldn't read its saved data at <location>, and nothing in it was changed. Open http://127.0.0.1:8017 in your browser to read this on a page. To start fresh on purpose, follow Setting saved data aside in the setup instructions.`
- **CP-738:** The section says the tracker is still running when that line shows, and that it keeps running until it is stopped.
- **CP-739:** The section tells the operator what to do next when that line shows: follow `Setting saved data aside`, that heading spelled exactly (`CONTENT.md` § Terminology). It keeps the program's condition, starting fresh on purpose. It doesn't say the saved data is lost, deleted, corrupted or damaged.

### The other two lines

- **CP-740:** The section still shows the ready line, says the reader's own location appears in place of the example location, and says opening the address shows the Projects page. It says the ready line means the tracker is running. The Projects page is said of the ready line only, because with the third line every address shows one other page.
- **CP-741:** The section still says a line starting with `The tracker didn't start` says why and what to do next. It now also says this start has stopped. It doesn't say that no tracker is running at all, because a refused second start leaves the first tracker running.

### Telling them apart

- **CP-742:** A reader of only the section can sort the three lines: the ready line and the `The tracker couldn't read` line mean the tracker is running, and the `The tracker didn't start` line means this start stopped. "The tracker keeps running" and "press Ctrl-C" read as applying to the two running lines and not to the `The tracker didn't start` line. Today they follow that line's sentence directly, with nothing limiting them (`products/tracker17/README.md:50-52`).
- **CP-743:** The section may not say that nothing else can ever appear in the terminal. Other text can: a bind failure other than a held address, and an unexpected failure while serving. The word "three" counts the lines the start itself announces, and the two reasons sharing the start `The tracker didn't start` are one line.

### What stays as it is

- **CP-744:** The passage under `### Starting the tracker again`, from "If it can't read the data, the tracker starts anyway." through "even if you repair the saved data.", stays byte for byte. The section may point at it, and needn't.
- **CP-745:** `products/tracker17/README.md` is the only product file that changes, and only the section changes within it. Both suites pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`.
- **CP-746:** Every sentence the change writes in the section is at most 20 words and uses the words `CONTENT.md` § Grammar and mechanics and § Terminology fix: "terminal", "saved data", and contracted negatives. A quotation of a program line is exempt from the word limit, because it is the program's text.

---

## Examples

| Scenario | Expected behavior | Rules |
|---|---|---|
| Run the request's `awk` and `grep` check before the change | Prints `0` | CP-736 |
| Run the same check after the change | Prints `1` or more | CP-736 |
| The section quotes more of the third line than its start | The quoted part matches the terminal's text word for word, with the location shown as the section's example | CP-737 |
| A reader has only the section and sees `The tracker couldn't read…` | They can say the tracker is still running until stopped, and that following `Setting saved data aside` is the next step for starting fresh | CP-738, CP-739, CP-742 |
| A reader sees `The tracker is running…` | They can say the tracker is running, and that the address opens the Projects page | CP-740, CP-742 |
| A reader sees `The tracker didn't start, because another tracker is already running…` | They can say this start stopped and the line says why and what to do. Nothing they read says the other tracker stopped | CP-741, CP-742 |
| A reader sees `The tracker didn't start, because something else is already using the address…` | Same reading: this start stopped, and the same sentence in the section covers it | CP-741, CP-743 |
| A reader looks for Ctrl-C after a `The tracker didn't start` line | The section doesn't tell them to stop anything for that line | CP-742 |
| A bind failure prints a traceback | The section makes no claim that excludes it, and says nothing about it | CP-743 |
| Diff the passage under `### Starting the tracker again` after the change | Empty | CP-744 |
| `git diff --stat` against the base, over `products/tracker17` | Lists `README.md` only | CP-745 |
| Both suites after the change | Exit 0 | CP-745 |
| Count the words of each new sentence | At most 20, apart from a quoted program line | CP-746 |

---

## Verified Claims

No rule renders a language-level fact: all three lines are text the product chose, so no packet line bears on them and this table has no rendering row. Rows marked base ran at `5e46e3a1a`. Tests ran by their ids, together, in the change worktree.

**Records above the change:** no test or check on the section is required of this change. `nfdr.md`, `SDD.md` and `adr/` were searched for the README, the setup instructions and the start's lines, and read where they hit, not read whole. `nfdr.md` RN-12 holds the setup instructions' content as behaviour, and SDD § 4 TS-1's test-first rule covers the code parts it names.

| Claim | Verified by | What came back |
|---|---|---|
| The request's check prints 0 at the base (CP-736) | The `awk` and `grep` command, on the base README | `5e46e3a1a`: `0` |
| The check prints 1 or more on a tree with the third line (CP-736) | The same command on a disposable clone at `5e46e3a1a` with a trial section. The trial text decides nothing here | `1` |
| The third line starts with the fixed string, and reads as CP-737 quotes it (CP-736, CP-737) | `main._unreadable_line("127.0.0.1", 8017, Path("/x"))`, called directly; `products/tracker17/main.py:168-173`, read | `startswith("The tracker couldn't read")` is `True`; the text agrees with CP-737 |
| The third line stays what the start prints on unreadable data, once, with the tracker serving (CP-737, CP-738 unchanged) | `tests/integration/test_start.py::test_an_unreadable_start_serves_one_page_and_announces_once` | `5e46e3a1a`: passed |
| A running tracker on that line stops when asked, and not before (CP-738) | `tests/integration/test_start_stop.py::test_unreadable_start_stops_quietly_and_releases_its_location` | `5e46e3a1a`: passed |
| The section the line points to is a README heading (CP-739) | `tests/integration/test_start.py::test_the_announcement_quotes_a_heading_the_readme_has` | `5e46e3a1a`: passed |
| Setting data aside as the README says keeps the earlier work (CP-739) | `tests/integration/test_start.py::test_set_aside_then_restart_preserves_the_earlier_work` | `5e46e3a1a`: passed |
| The ready line stays what a ready start prints (CP-740 unchanged) | `tests/integration/test_start_stop.py::test_real_start_stops_at_the_completed_ready_write` | `5e46e3a1a`: passed |
| A refused second start exits 1 with one line and the first tracker still answers (CP-741) | `tests/integration/test_single_tracker.py::test_second_tracker_is_refused_without_changing_the_first` | `5e46e3a1a`: passed |
| A held address gives one line and a failing status (CP-741, CP-743) | `tests/integration/test_start.py::test_a_start_with_a_held_address_prints_the_one_line_and_changes_nothing` | `5e46e3a1a`: passed |
| The keep-running sentence follows the didn't-start sentence with nothing limiting it (CP-742) | `products/tracker17/README.md:50-52`, read | `5e46e3a1a`: as CP-742 says |
| Another bind failure propagates without one of the three lines (CP-743) | `tests/integration/test_start.py::test_an_unrelated_bind_error_on_unreadable_data_propagates_without_a_line` | `5e46e3a1a`: passed |
| An unexpected failure while serving writes to the terminal (CP-743) | `products/tracker17/web/routes.py:1327-1332`, read; `docs/nfdr.md` QC-56 | Two lines on standard error |
| The passage CP-744 holds stands at lines 71 to 77, one line from where the request places it | `products/tracker17/README.md:71-77`, read | `5e46e3a1a`: as named |
| CP-744's passage can stay and the third line still be added (CP-744) | `git diff --unified=0` on the disposable clone's trial section | Hunks at lines 50 and 52 only |
| Both suites pass with the section changed, and no test reads it (CP-745) | The two commands of CP-745 from the clone's root, on the trial section, with a real tracker and Chromium; `git grep "What the start prints" -- products/tracker17/tests` | First: 2813 passed, exit 0. Second: 122 passed, exit 0. Grep: no hit |

---

## Out of Scope

- `main.py`, the unreadable-data page, the lock and every test. No test reads the section, so none changes.
- Any README section other than "What the start prints": `### Starting the tracker again` and `### Setting saved data aside` stay as they are, and so does `## Status`.
- A description of a traceback or an unexpected failure's terminal lines, in this section or any other.
- A separate sentence for each reason a start can be refused. The line itself says why.
- Any control inside the tracker that sets data aside or repairs it (SDD § 6 `protect-saved-data`, *Not in this slice*).
- An edit to any document under `products/tracker17/docs/`.

---

## Locked Answers (the divergence record — self-review 2026-10-30)

- **Gap 1 — what "up" and "stopped" mean across three lines (b):** two lines mean running and one means this start stopped. The request asks which line means which, and the third line's own sentence says the tracker is running.
- **Gap 2 — "stopped" says this start, not every tracker (b):** CP-741 limits it. A refused second start leaves the first tracker answering, so an unlimited "the tracker stopped" would be false of that case.
- **Gap 3 — "three lines" is the start's own announcements (b):** the program prints two texts sharing the start `The tracker didn't start`, and other text can reach the terminal on a failure the start doesn't announce. CP-743 counts them as one line and bars a claim that nothing else appears, because such a claim would be false.
- **Gap 4 — the keep-running sentence (b):** CP-742 requires it to read as applying to the running lines only. The request's "which means it stopped" can't be met if the section's next sentence reads as saying that line's tracker keeps running.
- **Gap 5 — the Projects page (b):** CP-740 ties it to the ready line. The third line's reader finds one other page at every address, so the sentence would otherwise mislead.
- **Gap 6 — the next step keeps the program's condition (b):** CP-739 keeps "start fresh on purpose". Setting data aside is what a reader does to start fresh, and the line they just read says so. The section doesn't present it as the only thing they may do.
- **Gap 7 — "not rewritten to fit" read as byte for byte (b):** the conservative reading of the request's guardrail. The request's "near lines 70 to 76" stands at 71 to 77 at the base, so CP-744 names the passage by its words and not its lines.
- **Gap 8 — no sentence wording fixed (b):** the rules fix what the section must say and leave the words to the run that owns them. Only the program's strings and the heading are fixed.
- **Gap 9 — the content rules on the new sentences (b):** CP-746 states the limits `CONTENT.md` already places on the setup instructions. The request says nothing on them, and they hold for this text.
