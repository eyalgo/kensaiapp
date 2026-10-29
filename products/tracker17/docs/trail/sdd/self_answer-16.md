# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-29
- **Sources re-read:** https://docs.astral.sh/uv/getting-started/installation/, "Standalone
  installer", read 2026-10-29: the macOS and Linux install is `curl -LsSf
  https://astral.sh/uv/install.sh | sh`, and the page names no Python as a prerequisite of that
  installer. It is the page RT-4 cites for the suite's section saying how to install uv, and the
  answer keeps that pointer in the suite's section. Read in this repository at `f86543f50`: the
  companion whole; `SDD.md` whole; `README.md` whole; ADR-0013 whole; `adr/README.md`; `nfdr.md`'s
  header; SRS FR-4, FR-41, C-7, C-8, AC-3 and RN-23; UXD UX-F1 and UX-S1; `trail/sdd/cycle-12.md`
  § 5.1 and `self_answer-15.md`; the seed and station the item names, and the sealed unit's
  `deferred_decisions.md` and `change_spec.md` § Out of Scope.

## Items worked

### 5.1 — § 6 S-1 and § 4 RT-4 disagree on whether the prerequisites section names uv

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** answered
- **Why:** S-1 holds: the prerequisites section names uv, for the test suite only, beside the
  one-time network line; RT-4 is reworded to say that "the tracker's own setup" is the tracker's
  prerequisites and RT-2's two commands, so the two sentences agree. Check 1: the edit lands in
  § 4 and in S-1's *Artifact*, both the CTO's columns in § *Who decides what*; it binds the
  document's consistency and no person, money or risk; the owner's call of 2026-10-29 chose uv
  and said nothing about where the README names it, so no reserved ground is in play. Check 2:
  the item carries no draft, and it is one question — which sentence holds — because RT-4's
  "names it nowhere" is false only if the prerequisites section counts as the tracker's own setup.
  The document already answers that for the network connection: RT-1 says the one-time
  connection "that SRS FR-4 and UXD UX-S1 list among the prerequisites is needed only to set up
  the test suite", and `README.md:29` carries it in `### What you need` as the tests' alone. A
  suite-only prerequisite marked as such is already a thing the prerequisites section holds, so
  "the tracker's own setup" cannot mean that section without also forbidding RT-1's line. Check 3:
  SRS FR-4's first bullet puts the suite's one network need under prerequisites by name ("to fetch
  the declared dependencies", which RT-4 says only the tests have); UXD UX-S1 lists "prerequisites
  (including the one-time network connection setup needs)"; RN-62 reads uv as joining that list
  ("so uv joins the list without a word of the UXD moving") and says `first-project`'s bar "has
  the prerequisites name uv for the suite" — so the authoring round meant S-1's reading and RT-4's
  sentence was aimed at the tracker's commands. SRS C-7 and AC-3 stay true: the tracker's setup is
  two commands on Python alone, and a prerequisite stated as the suite's does not enter C-7's
  "stated prerequisites" for the tracker any more than the network line does. UXD UX-F1 keeps
  "Decision points: none": a sentence saying what the tests need asks the reader to choose
  nothing. ADR-0013 § Decision's "the tracker's own setup names it nowhere" stays true under the
  reworded RT-4 and is not owed a change. Check 4: absent uv — the tracker runs and the suite is
  a missing prerequisite the instructions explain (UX-F1's first failure line); refused — a
  machine where uv cannot be installed is the same case as the Linux browser libraries, and the
  tracker is unaffected; stale — uv's installer page moves: the pointer sits in the suite's
  section only, where RT-4 already keeps it. The close call was the opposite reading, uv named in
  the suite's section alone, which keeps `### What you need` shorter; it lost because it would
  leave the network line as the one suite prerequisite stated up front and send a reader who
  checked their prerequisites to a tool they meet seventy lines later, and because it would move
  S-1's settled artifact bar and RN-62's reading instead of one ambiguous clause in RT-4. The
  README's `### What you need` is then owed one sentence; the station that holds the opposite
  reading in its reached-when item 4 is sealed and reached, and which unit carries the sentence is
  the PM's, as the item itself says.

## Left for the owner

None this run.

## Skipped

None this run.

## Raised on this document

### 2.1 — The header, § 12 and § 4 RT-4 still read the records at ADR-0012 and NFDR version 18

- **What the document is owed:** the header's *Inputs read* and § 12 read the records as they
  stand — ADR-0013 Accepted, ADR-0002 superseded by it, NFDR version 19, the architecture
  companion live again — and RT-4 names ADR-0013 as the record of the suite's environment.
- **Why it is worth a cycle:** a fact in it is now false. `SDD.md:6` says the records run to
  ADR-0012, the NFDR is at version 18 and `architecture_open_issues.md` "no longer exists";
  `SDD.md:1636-1637` counts twelve records. `adr/README.md` lists ADR-0013, Accepted 2026-10-29,
  and ADR-0002 "Superseded by ADR-0013"; `nfdr.md`'s header reads version 19 and traces six
  obligations to ADR-0013; both landed at `909fc536c`; the companion was reopened at `f86543f50`.
  The cost is nil beyond this round: the fold is owed for § 5.1 anyway, and cycle 11's § 2.1
  (RN-60) shows the fold's own catch-up reaching these lines.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
