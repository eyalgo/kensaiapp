# Change Text — Linux test setup and the suite's Git prerequisite

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing

---

## Text

Each string below is a whole paragraph of the setup instructions, written in the instructions' own
markdown. The backticks are part of the string: each pair marks a code span, and the characters
inside it are typed exactly as shown. Nothing in either string is a variable.

### The setup instructions' Running the tests section

**A reader on Linux, after the section's opening paragraph and before the seven commands**

> On Linux, where the commands say `python -m playwright install chromium`, type `python -m playwright install --with-deps chromium` instead. That command also installs the system libraries the browser needs, using the operating system's package manager. It asks for administrator rights. The tracker and `pytest tests/` need none of what it installs. On Linux, the end-to-end tests need Debian 12 or 13, or Ubuntu 22.04, 24.04 or 26.04, on x86-64 or arm64.

When the person sees it: they are about to type the seven commands on Linux, and they learn which one
to type differently, what that command asks of their machine, that the tracker and `pytest tests/`
don't depend on it, and whether their Linux is one the end-to-end tests run on.

**A reader who reaches the end of the section, as its last paragraph**

> For every test to pass, your copy needs to be a Git repository, with `git` on the path. If either is missing, as in a copy unpacked from a download, 1 test doesn't pass. That test checks that Git ignores the saved data. The tracker itself needs neither a Git repository nor `git`.

When the person sees it: they have the commands and may have seen 1 test not pass, and they learn the
two conditions that test needs, what it checks, and that starting the tracker needs neither.

---

## Wording decisions

- The replacement is worded "where the commands say `python -m playwright install chromium`, type
  `python -m playwright install --with-deps chromium` instead", not as a command of its own. — The
  design places the note before the unchanged block and requires that it can't read as an extra step
  before the virtual environment is made (`change_design.md` § 1 Change Summary, edit site 1). Naming
  the step the reader swaps keeps the Linux command at that step, after the dependencies install.
- "That command" and "It" in the Linux paragraph each follow a sentence whose last-named command is the
  `--with-deps` one. — The first sentence names two commands, so each later reference has to land on
  the one just named for the reader to type.
- CP-70 and CP-71 are three sentences, not one. — `docs/CONTENT.md` § Accessibility of text, "The
  reading bar", has each sentence carry one claim, and the package manager, the administrator rights
  and what needs none of it are three claims.
- "the system's package manager" (`change_spec.md` CP-70) became "the operating system's package
  manager". — `docs/CONTENT.md` § Terminology rejects "system" as a word for the tracker. Saying
  "operating system" leaves no reading in which the tracker runs the package manager. "System
  libraries" stays, because the library's own kind has no plainer name and the sentence ties it to
  the browser.
- The sentence on the libraries says the command installs "the system libraries the browser needs".
  — It is the reason the command asks for administrator rights, and `docs/SDD.md` § 4 RT-4 grounds it:
  "On Linux that browser needs system libraries the operating system does not ship by default, and
  the same one-time step fetches them". It claims no more than that sentence does.
- The Linux systems are framed as what the end-to-end tests "need" on Linux, and the sentence opens
  "On Linux". — `docs/SDD.md` § 4 RT-4 calls `pytest tests/e2e/` on another Linux "a missing
  prerequisite", so "need" is the claim the source makes. Opening with "On Linux" keeps a macOS reader
  from reading the list as the only places the tests run. The README's "It has been checked on macOS
  only" stays true, because "need" states a requirement, not a check.
- The vendor's "Debian 12 / 13, Ubuntu 22.04 / 24.04 / 26.04 (x86-64 or arm64)" (`docs/SDD.md` § 4
  RT-4) became "Debian 12 or 13, or Ubuntu 22.04, 24.04 or 26.04, on x86-64 or arm64". — `docs/CONTENT.md`
  § Grammar and mechanics allows parentheses only in "(unassigned)", and the slashes would read as
  dates or paths. "Or" is the honest join, since a machine runs one of them. The sentence is 20 words,
  the bar's limit, and holds the literal `Debian 12` CP-72 and CP-79 require.
- "x86-64" and "arm64" stay as written. — They are the architectures' own names, as the vendor writes
  them, not abbreviations the tracker made. `docs/CONTENT.md` § Grammar and mechanics, Abbreviations,
  writes tool names as their owners do, and CP-72 requires both to appear.
- "Running the full suite needs" (`change_spec.md` CP-73) became "For every test to pass, your copy
  needs to be a Git repository". — The setup instructions never name a "full suite". They call the
  set "the tests" and say what each command runs, so "every test" is the instructions' own term for
  the same thing. "Your copy" is the instructions' word for the reader's checkout throughout.
- "one test doesn't pass" (the replaced paragraph's wording) became "1 test doesn't pass". —
  `docs/CONTENT.md` § Grammar and mechanics, Numbers: "Counts are numerals ... never words". The
  replaced paragraph predates this check.
- "as in a copy unpacked from a download" is kept from the replaced paragraph, inside a new sentence.
  — It names the case a reader is most likely to be in. CP-76 forbids the two old sentences as
  written, not this phrase, and `change_spec.md` § Verified Claims shows the same single test not
  passing in a copy extracted with `git archive`.
- The test's failure is worded "doesn't pass", never "fails". — `docs/CONTENT.md` § Terminology,
  "Banned in anything a person sees", lists "failed, failure", and the replaced paragraph already wrote
  "doesn't pass".
- CP-74 closes the paragraph, after the test's explanation. — A reader who has just read what the
  test needs next asks whether the tracker needs it too, and the last sentence answers that.
- Checks run over both strings: each sentence counted at 20 words or fewer, command spans included
  (longest 20). Every banned word in `docs/CONTENT.md` § Terminology and every banned punctuation mark
  in § Grammar and mechanics searched for, and none found. The six relative words of CP-77 searched for
  with `grep -w -i`, and none found. The product carries no check over its prose, so none was run.

---

## Findings for the Content Manager

- "On Linux, the end-to-end tests need Debian 12 or 13, or Ubuntu 22.04, 24.04 or 26.04, on x86-64 or
  arm64." — `docs/CONTENT.md` § Grammar and mechanics, Numbers, says counts are numerals, but sets no
  rule for a version number or for naming a hardware architecture in the setup instructions. —
  Written as the vendor writes them, under the Abbreviations rule that tool names follow their owners.
