# Change Spec — README setup prose meets the content rules

**Date:** 2026-10-10
**Category:** bug
**Behaviour:** preserving
**Request:** Bring the README's setup text inside the content rules the last unit left it breaking. Two sentences in `products/tracker17/README.md`, between `## Status` and `## How it's built`, break `docs/CONTENT.md` § Grammar and mechanics. The first is the prerequisites sentence that ends with the Python download address, 21 words against the 20-word limit (`docs/CONTENT.md:120`); split it into sentences of 20 words or fewer that say the same thing, keeping the address https://www.python.org/downloads/ and the instruction to type the command again. The second is the line under "Setting saved data aside" that says the saved data is "now" in a new directory; reword it without "now" or any other of today, yesterday, tomorrow, ago, recently (`docs/CONTENT.md:126-127`), keeping what it tells the reader: the directory name, the date-and-time naming with its example, and the `ls ~/tracker17-set-aside` command. After the change, from `## Status` up to `## How it's built`, no sentence runs longer than 20 words and `grep -n -w -i -e today -e yesterday -e tomorrow -e now -e ago -e recently products/tracker17/README.md` matches nothing in that span. Any other sentence in the span found over 20 words or carrying one of those words is fixed the same way.

What must not be weakened: the README's meaning and every command in it stay as they are; every heading stays, with "Starting the tracker again" and "Setting saved data aside" spelled exactly; `main.py`, the tests and the product's behaviour do not change; the `docs/` definition documents are not edited; "How it's built" and "The documents" stay as they stand; the tests that read the README's headings keep passing, and `pytest tests/` and `pytest tests/e2e/` still exit 0 from `products/tracker17/`.

---

## Change Summary

Reword the README's setup prose without changing its meaning, to meet the existing constraints in `products/tracker17/docs/CONTENT.md:L120-L129`, § Grammar and mechanics, “Sentence length” and “Dates and times”.
This specification owns the characterization contract and the repair's acceptance boundary.

The product binding is `system/projects/tracker17/project.md:L3`, **Product path:**.
The source request is `tracker17 · tobiishi · 2026-10-10_readme-content-rules`, `change_request.md:L5-L12`, **Request** and classification.

## Sizing Decision

Product Owner decision, 2026-10-10: keep one capability repair.
The acceptance boundary is setup prose that meets its content constraints with its meaning intact, from `change_request.md:L5-L9`, **Request** of `tracker17 · tobiishi · 2026-10-10_readme-content-rules`.
On this reading, both sentences and any further violation belong to the same repair (`change_request.md:L5`, **Request**).
On this reading, the preservation checks support the acceptance boundary (`change_request.md:L7`, **Request**).
On this reading, the bounded prose repair fits one development flow (`change_request.md:L5-L9`, **Request** and **Sizing**).
This applies `core/prompts/pm_right_size.md`, § Right-size to one honest merge.

## Invariants (characterization contract)

- **Test continuity:** the existing test suite must pass unchanged after the repair.
  From the product directory, `pytest tests/` and `pytest tests/e2e/` must both exit 0, as the source request requires.
  The README-heading tests must remain intact and passing.
  The baseline end-to-end failure and its observed environmental condition are recorded under Verified Claims; no green baseline is claimed.
- **Public interface:** every public importable symbol and signature remains identical.
  The export declarations are `products/tracker17/domain/__init__.py:L18-L34`, `products/tracker17/application/__init__.py:L20-L33`, `products/tracker17/persistence/__init__.py:L5` and `products/tracker17/web/__init__.py:L9`, each at `__all__`.
- **README meaning and commands:** every instruction, factual meaning, command and command order stays intact throughout `products/tracker17/README.md`.
  Splitting or rewording a sentence must preserve its conditions, consequences and next action.
  This includes the Python prerequisite, both alternatives requiring installation, https://www.python.org/downloads/ and the instruction to type the version command again.
  It also includes the set-aside directory's name and home-directory location, the date-and-time naming, `2026-10-08-143205` and `ls ~/tracker17-set-aside`.
  The before-text is `products/tracker17/README.md:L17-L23`, § What you need, and `:L69-L85`, § Setting saved data aside.
- **Headings and retained sections:** every README heading keeps its spelling, level and order.
  In particular, “Starting the tracker again” and “Setting saved data aside” remain exactly those headings.
  The README's § How it's built and § The documents remain unchanged.
  The before-text is `products/tracker17/README.md:L58-L69` and `:L109-L139`, under those four headings.
- **Product continuity:** `products/tracker17/main.py`, the tests, all other product code and the product's behaviour remain unchanged.
  Every definition document under `products/tracker17/docs/` remains unchanged.
  These preservation boundaries come from `change_request.md:L7`, **Request**.

## Structural Goal

The repair changes prose only in the span beginning at `## Status` and ending immediately before `## How it's built`.
Every sentence in that span must contain at most 20 words.
No whole word in that span may be “today”, “yesterday”, “tomorrow”, “now”, “ago” or “recently”, regardless of case.
These are the existing constraints being repaired, from `products/tracker17/docs/CONTENT.md:L120-L129`, § Grammar and mechanics.

The prerequisite sentence has 21 whitespace-separated words at `products/tracker17/README.md:L23`, § What you need.
Split that sentence into shorter sentences with the same meaning.
The saved-data description contains “now” at `products/tracker17/README.md:L81`, § Setting saved data aside.
Reword that description without any banned word and preserve the information the Invariants protect.
Any other violation of either constraint within the bounded span must receive the same meaning-preserving repair.
The final wording is not fixed by this specification.

The source request's grep command must produce no matching line in the bounded span:

```sh
grep -n -w -i -e today -e yesterday -e tomorrow -e now -e ago -e recently products/tracker17/README.md
```

The command runs from the instance worktree root.
The sentence-length check reads sentences as prose, retaining addresses, paths, versions and inline commands as whole whitespace-separated tokens.
A dot within a version, address or path is not a sentence ending.
Headings and fenced shell commands are not prose sentences; their text is protected by the Invariants.

## Verified Claims

Baseline tree: `5dfc3343efecbc67362aea8d91b516c18a8a9809`, read and checked inside this change's isolated worktree.
Checks below ran on 2026-10-10 without editing the README, code, tests or definition documents.

| Claim | Verified by | What came back |
|---|---|---|
| The prerequisite sentence exceeds the existing limit. | Read `products/tracker17/README.md:L23`, § What you need, against `products/tracker17/docs/CONTENT.md:L120-L121`, “Sentence length”; counted with `len(sentence.split())`. | 21 words. |
| The bounded prose has no additional sentence over the limit. | Read the full bounded span; a `python3` check split prose at sentence-ending punctuation followed by whitespace, skipped headings and fenced blocks, and counted whitespace-separated words. | 67 prose sentences checked; only line 23 exceeded 20 words. |
| The saved-data description carries a banned word. | Ran the grep command above from the instance worktree root against the unchanged README. | Exit 0; its sole match was line 81, “Your saved data is now in a new directory…”. |
| Both installation conditions, the download address and the repeat instruction exist. | Read `products/tracker17/README.md:L17-L23`, § What you need. | Lower than 3.11 or missing `python3`; install 3.11 or later from the named address; type the command again. |
| The saved-data description contains the information protected by the request. | Read `products/tracker17/README.md:L69-L85`, § Setting saved data aside. | Home-directory location, date-and-time directory naming, `2026-10-08-143205` and `ls ~/tracker17-set-aside` are present. |
| The unchanged regular suite passes. | Ran `pytest tests/` from the product directory, first with the host pytest and then after `source .venv/bin/activate`, using the dependencies installed from `tests/requirements.txt`. | Both runs exited 0 with 224 passed; the locked environment used pytest 9.1.1 and Python 3.14.7. |
| The end-to-end baseline is not green in the observed environment. | Ran `pytest tests/e2e/` from the product directory after `source .venv/bin/activate`, using real tracker processes and installed Chromium. | Exit 1: 11 passed, 1 failed. `test_the_real_start_command_with_the_address_held` failed before starting the tracker because it could not bind `127.0.0.1:8017`: `[Errno 48] Address already in use`. |
| The fixed-address failure also occurs in isolation. | Ran `pytest tests/e2e/test_start_command.py` under the same conditions; inspected `tests/e2e/test_start_command.py:L40-L46`; ran `lsof -nP -iTCP:8017 -sTCP:LISTEN`. | Isolated test exited 1 with the same bind failure. `lsof` reported Python PID 86069 listening on `127.0.0.1:8017`. The listener was left running; neither the test nor the address was replaced. |
| The two fixed headings have existing test coverage. | Read `products/tracker17/tests/integration/test_start.py:L94-L167`, `_headings`, `_readme_headings`, `test_the_message_closing_sentence_quotes_a_heading_the_readme_has` and `test_the_readme_has_both_fixed_headings`; ran `pytest tests/` from the product directory. | Both tests passed in the 224-test baseline run, exit 0. |
| The public export surface has explicit declarations. | Read each of the four `__init__.py` files named under Public interface, at `__all__`. | All four declare the symbols they re-export; no export change is part of this repair. |
| The repair preserves the locked setup contract. | Read all of `products/tracker17/docs/fdr.md`, especially § The written setup instructions, R-8 to R-14, and § Saved data, R-28. | On this reading, rewording without changing instructions contradicts no locked FDR decision. |

## Out of Scope

- Changes to README text before `## Status` or from `## How it's built` onward.
- Changes to setup steps, commands, supported platforms, prerequisites, printed terminal messages or saved-data behaviour.
- Changes to product code, tests, definition documents or content rules.
- A general README rewrite or any new product capability.
