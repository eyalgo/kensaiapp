# FDR open issues — tracker17

> Companion to `fdr.md`. The Principal PM authored the FDR non-interactively; this file holds what the
> run could not settle from its inputs — the PRD, the SRS and the SDD.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-fdr`. It folds your answers into the FDR and drops the resolved items. When nothing is
> left open, `product-fdr` **deletes this file**: no file = the FDR is done.
>
> Your answers are never thrown away. Each time the Principal PM folds them in, it first copies this
> file whole to `docs/trail/fdr/` — so what you decided, and why, stays readable and citable for good.
>
> **§ 3 is the odd one, and worth reading twice.** The Principal PM writes the FDR *and* is the seat
> most likely to raise an item against it later, cutting the same product's documents into seeds. The
> two are different acts at different times, and § 3 keeps the later one visible instead of letting
> it be quietly folded back into § 1 as though the authoring run had asked it.

Every `R-n`, `PD-n`, `OOS-n` and `RN-n` below is an entry of `products/tracker17/docs/fdr.md`, version 3.
Every `PRD`, `SRS` and `SDD` reference is to `products/tracker17/docs/PRD.md`,
`products/tracker17/docs/SRS.md` and `products/tracker17/docs/SDD.md`.

Both items below report an upstream document that changed after FDR version 2 settled on 2026-10-06
(commit `42a4a0ebb`). Each says what the change moved in the FDR. The FDR now follows each change, and
each item asks you to confirm that it does.

---

## 1. Open issues — behavioural questions with no answer yet

None.

## 2. Choices to confirm — the Principal PM drafted a best-effort answer; confirm or override

### 2.1 PRD v5 and SRS v5 add a fourth priority, `critical`, and the FDR now follows them
- **Drafted into the FDR:** R-51 refuses a priority other than `low`, `medium`, `high` or
  `critical`. R-90 has priority ascending run `low`, `medium`, `high`, `critical`, and descending run
  `critical`, `high`, `medium`, `low`. R-96 counts each of the four priorities. PD-5 names the four
  priorities as the one exception to taking over tracker16-X's rules. RN-6 says C-5 takes over
  tracker16-X's refusal of an unknown priority and not its three-value set. No other rule, decision,
  exclusion or example names the priority set: R-21's "unknown status or priority" reads against
  R-51, and R-42 keeps `medium` as the default.
- **Rationale:** the upstream documents settle every part of this, so nothing here is the Principal
  PM's own call. PRD § Core Features, Priorities reads "A task is `low`, `medium`, `high` or
  `critical`, and `medium` is the default", and its preamble makes Priorities "The one exception" to
  behaving as the predecessor does (the owner's answer, `products/tracker17/docs/trail/prd/cycle-5.md`
  § 1.1). SRS FR-15 names the four, FR-36 sorts `critical` after `high`, FR-38 counts four, and C-5
  carries the exception. The order is the owner's answer in
  `products/tracker17/docs/trail/srs/cycle-4.md` § 3.1, with the reasoning in SRS RN-24. This item
  replaces the one a `companion-self-answer` run wrote here on 2026-10-11 while answering
  `SRS_open_issues.md` § 3.1. That item proposed the same change to R-51, R-90 and R-96, and its
  reasoning is `products/tracker17/docs/trail/srs/self_answer-4.md`. It is listed because a
  foundation the FDR settled on moved, and you should see that it moved.
- **If overridden:** the FDR would contradict SRS v5 FR-15, FR-36 and FR-38. A different priority set
  or order is a change to the PRD (the CPO's) and the SRS (the CTO's) first, and the FDR follows them.
  R-51, R-90, R-96, PD-5 and RN-6 would move with it. A different place for `critical` in the order
  moves R-90 only.
- **Confirm or override:** confirm. PRD § Core Features, Priorities and SRS v5 FR-15, FR-36, FR-38 and C-5 say what R-51, R-90, R-96, PD-5 and RN-6 now say. No other FDR entry, and none of the UXD, SDD, DESIGN or NFDR, lists the priority values. Reasoning in `products/tracker17/docs/trail/fdr/self_answer-2.md`.

### 2.2 SDD versions 4 to 7 changed what the setup instructions say for Linux, and the FDR now follows them
- **Drafted into the FDR:**
  - **R-119 (new):** for Linux, the instructions on running the test suite give the one-time step
    that installs the browser together with its system libraries. They say the step uses the
    system's package manager and asks for administrator rights, and that the tracker and the tests
    that do not drive the browser need none of it.
  - **R-120 (new):** the instructions name the Linux systems the end-to-end tests run on, which are
    the systems the pinned browser-driving test dependency supports. The rule names no list, because
    the SDD says the list moves when the pin moves.
  - **PD-8 (extended):** the tracker runs on any Linux with Python 3.11 or later. The end-to-end tests
    run only on the systems R-120 names, and on any other Linux the tracker and the tests that do not
    drive the browser still run.
  - **R-48 and R-115** also trace to SDD § 4 RT-7, which states the same edit-form save they do.
  - **RN-11 and RN-12** say what is true now: the NFDR exists, the SDD's port and line-break questions
    are closed, the UXD states where a field's maximum is shown, and the UX-F9 collision RN-12 named
    is closed.
- **Rationale:** each change traces to SDD § 4, which is one of the four SDD sections the FDR reads.
  SDD § 4 RT-3 now says the end-to-end suite runs on fewer Linux systems than the tracker. RT-4 has
  the instructions give the Linux install step, say it asks for administrator rights, and carry the
  pinned library's list of Linux systems (SDD version 7, commit `4156e81b2`; why, SDD RN-38). R-9 to
  R-11 and PD-8 already take the instructions' prerequisites from RT-1, RT-3 and RT-4, so leaving the
  new content out would leave RT-3 and RT-4 only half carried. RT-7 gained the edit-form save in SDD
  version 5 (why, SDD RN-32), and R-115 and R-48 already state it. Four SDD changes land as no rule:
  - RT-5's address, `127.0.0.1:8017`. R-4 and PD-10 say the address is fixed, and the value is the
    SDD's.
  - SEC-2's sharper refusals and SEC-3's no-framing policy. Both are mechanisms that serve R-110.
  - TS-4's two-way pointer check. It is a mechanism that serves PD-13.
  - SDD § 6 S-1's statement that the full suite needs the copy to be a Git repository. It sits in a
    slice, which the FDR does not read, and no § 4 condition states it.
  RN-11 records each of these four.
- **If overridden:** with "drop the Linux rules", R-119 and R-120 go, and PD-8 loses its last two
  sentences. The instructions' Linux content then rests on the SDD alone, and the FDR names none of it
  as behaviour. With "state the port", R-4 or PD-10 names `127.0.0.1:8017`. A later change of port is
  then a change to the FDR as well as to the SDD. With "carry the Git prerequisite", a rule beside
  R-8 says the instructions state it. That rule would trace to no section the FDR reads, so SDD § 4
  would first have to state it.
- **Confirm or override:** confirm. SDD v7 § 4 RT-3 and RT-4 say what R-119, R-120 and PD-8 now carry, and Playwright's own page confirms that `--with-deps` installs the system dependencies through the package manager and tries to become root. The Git prerequisite stays out, because it sits in SDD § 6, which the FDR does not read. Reasoning in `products/tracker17/docs/trail/fdr/self_answer-2.md`.

## 3. Raised from downstream — an item raised against the FDR after it settled

None.
