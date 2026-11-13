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

Every `R-n`, `PD-n`, `OOS-n` and `RN-n` below is an entry of `products/tracker17/docs/fdr.md`, version 7.
Every `PRD`, `SRS` and `SDD` reference is to `products/tracker17/docs/PRD.md`,
`products/tracker17/docs/SRS.md` and `products/tracker17/docs/SDD.md`.

---

## 1. Open issues — behavioural questions with no answer yet

None.

## 2. Choices to confirm — the Principal PM drafted a best-effort answer; confirm or override

### 2.1 The inputs moved after FDR version 6 read them, and the FDR now follows them
- **Drafted into the FDR:**
  - **R-129 (new):** the summary shows the due-today count, the project's tasks due today under R-69 that are neither `done` nor `cancelled`, a zero shown.
  - **R-130 (new):** a task due today is in the due-today count and not in the overdue count.
  - **R-131 (new):** one summary works out both counts against the same "today", even when the date changes while the summary is produced.
  - **OOS-17 (new):** no due-today marking on a list's tasks, and no filter for tasks due today.
  - **R-128 (changed):** the refusal of a filter or sort value no control can hold applies while the tracker serves its saved data. While the saved data is unreadable, that address shows R-25's page, and nothing is refused.
  - **Examples** gain four rows: the due-today side of the overdue boundary, an empty project's 0, the date changing during one summary, and a bad filter value on unreadable data.
  - **RN-11** gains drop-lines for SDD § 3's four layers, § 4 TS-6, RT-4's Behave scenario folder, § 9 TO-10, the due-today count's place on the page, and AC-13's due-today side. Its line on PRD § Assumptions now reads the PRD version 8 sentence, "tracker17 is public". **RN-16** and **RN-17** record the new and changed entries.
  - **The *Inputs read* line** reads PRD version 9, SRS version 8, SDD version 23 and UXD version 12.
  - **Unchanged:** R-69, R-96, R-99, PD-15 and OOS-1, each read against the changes and still true as written.
- **Rationale:** the FDR's only permitted deltas are an owner's answer and an upstream change, and this item reports the upstream changes so you can see the foundation moved. PRD version 9 § Core Features, Project summary adds the count on your answer (`products/tracker17/docs/trail/prd/cycle-7.md` § 1.1), and SRS version 8 FR-38, AC-13 and RN-26 carry it down, the one "today" for both counts included. SRS RN-26 says "FR-26 adds no due-today marking and FR-32 no due-today filter", and UXD version 12 UX-F6 says the same, so OOS-17 writes the exclusion down where a builder reads it. SDD version 19 § 4 RT-8 says that while the saved data cannot be read, a filter form's "values are not read, no refusal arises", which made R-128 as written false on unreadable data. RN-14 scoped R-20 and R-105 the same way. The rest of the SDD's change from version 18 to version 23 is structure, test mechanism and the cut, and moves no rule. The product does not show the count today: `products/tracker17/docs/what_left.md` lists it as missing. Confirming these rules does not build it. One thing this run found and cannot fix: `system/projects/tracker17/finish_line.md` § What this finish line does not require still quotes PRD § Assumptions as saying tracker17 "stays that way until the owner decides to publish it", a sentence PRD version 8 removed. The finish line's own first sentence there, that done "does not require tracker17 to be published or tried by an outside reader", still holds, so OOS-1 stands. Correcting the quote is the finish line's owner's, the CPO.
- **If overridden:** with "drop OOS-17", nothing here excludes a due-today marking or filter, and a builder may add one that the PRD and SRS never asked for. With "drop R-131", the one-"today" rule rests on SRS FR-38 alone, and its Examples row goes. With "keep R-128 as version 6 wrote it", R-128 contradicts SDD RT-8 and R-25 on unreadable data, RN-17 and the unreadable Examples row go, and the FDR states a refusal the tracker does not give. A different definition of the count is a change to the PRD (the CPO's) and the SRS (the CTO's) first.
- **Confirm or override:** confirm, with one addition. R-129, R-130, R-131, OOS-17, the changed R-128, the four Examples rows, RN-11, RN-16, RN-17 and the *Inputs read* line stand as drafted, and each matches PRD version 9, SRS version 8 FR-38, AC-13 and RN-26, UXD version 12 UX-F6 and UX-S5, and SDD version 23 § 4 RT-8. The addition is about the finish line, not the FDR. The rationale says the finish line misquotes PRD § Assumptions and that fixing it is the CPO's, but it sends that fix nowhere. The finish line also has the same removed wording in a second place: its third bar says the owner runs it alone "because the PRD makes them the only reader until they publish". Both now go to the CPO as item § 2.1 of `system/projects/tracker17/finish_line_open_issues.md`, opened for this answer. OOS-1 stands, because its conclusion does not rest on the removed wording. Reasoning: `products/tracker17/docs/trail/fdr/self_answer-5.md`.

## 3. Raised from downstream — an item raised against the FDR after it settled

None.
