# Blind review: the route of 2026-11-13_the-summary-shows-the-due-today-count

Read at `ece780885918f0b36555d1f1d4051ea6af9fb654`, by a fresh run that did not cut the route. Line
numbers (L…) refer to the seed unless another file is named. Product files are cited from
`products/tracker17/`. S1 = `summary-shows-due-today` (L15).

The seed records **no ruling**. Nothing in it is a call attributed to the owner with a date. L5's
"the owner asked for this count" carries no date and calls itself "my reasoning, not a lookup".
§ Source (L11) quotes the SDD, CONTENT and `what_left.md`, which says where the work came from, not
what an owner decided. The map below covers the sentences of `## What it is` (L5, L7) and the parts
L7 lists.

## 0. Coverage map

- **L5: "Moves the finish line's Works bar".** S1: "both commands of the card's test command pass".
  This is the Works bar's suite half (`system/projects/tracker17/finish_line.md:L22-L24`, "the full
  automated suite passes"). The seed says the work moves the bar, not that it reaches it, so the
  browser run-through half is not owed here.
- **L7, the count of open tasks due today.** S1: "a project's summary shows the due-today count, an
  open task due on the summary's one date".
- **L7, "directly after the overdue count".** S1: "directly after \"Overdue\"". The summary's overdue
  row is labelled "Overdue" today (`web/pages.py:L1821-L1824`, `_SummaryRow("Overdue", summary.overdue,
  _OVERDUE_COUNT_LINK)`), so the label the bar names exists.
- **L7, "as a plain number".** S1: "as a plain number (not a link)".
- **L7, "0 included".** S1: "0 on an empty project", and "the summary test's count row on an empty
  project and a built one".
- **L7, "under one \"today\" for both counts".** S1: "an open task due on the summary's one date", and
  "a task due that day is in the due-today count and not overdue". The summary already reads the
  clock once (`application/tracker.py:L298-L305`, "One clock read gives the date"), so a fresh
  session checks this half by reading. None of the bar's tests changes the date between the two
  counts, the case FDR R-131's example shows (`docs/fdr.md:L485`).
- **L7, the label "Due on {date}".** S1: "labelled \"Due on {date}\"". CONTENT fixes the date's form,
  "with the date written `YYYY-MM-DD`" (`docs/CONTENT.md:L166`).
- **L7, "the tests of SRS AC-13's due-today side pass".** S1: "new tests fail on `main` and pass
  after: AC-13's due-today side (a task due that day is in the due-today count and not overdue; one
  done or cancelled is in neither)". This matches AC-13's wording (`docs/SRS.md:L517-L519`, "an open
  task due today is in the summary's due-today count and not overdue, and a task due today in `done`
  or `cancelled` is in neither count").
- **L7, "S-6's bar is unmet by the product".** S1 carries S-6's due-today shares: the Behaviour line
  (`docs/SDD.md:L1160-L1171`) through the clauses above, and the Command line (`docs/SDD.md:L1172-L1176`)
  through "AC-13's due-today side", "the summary test's count row … a built one" and
  "`python3 tests/timed_run.py` exits 0". S-6's *Artifact*, "`domain/summary.py` exists", is true
  today (`domain/summary.py:L1`).

## 1. Not carried

None found.

## 2. Contradicted or added

None found. The bar adds nothing L7 lacks. Its "(not a link)" restates "plain number", and its
"Overdue" is the label already on the page. It builds nothing the `## Out` fence (L23) excludes: no
list-row marker, no filter and no summary across projects.

## 3. Not checkable

None found. Each named case fails on `main` because `ProjectSummary` has no due-today field
(`domain/summary.py:L68-L83`: `overdue`, `no_due_date` and no other date row). The cases' "not
overdue" halves pass today, as guards: `tests/unit/test_due_dates.py:L75`, "assert is_overdue(today,
status, TODAY) is False", and `tests/unit/test_summary.py:L281-L292`, a task due `TODAY` left out of
`overdue == 1`. Each case also asserts the due-today count, so no case is made of guards alone.
`python3 tests/timed_run.py` does not name the directory it runs from. The script's own header does:
"Run it from the product root" (`tests/timed_run.py:L9`).

## 4. Cannot be met where it stands

None found. S1 is the only station. Everything its bar needs is either its own work (the field, the
row, the label and the tests) or already exists: the "Overdue" row (`web/pages.py:L1822`), the single
clock read (`application/tracker.py:L304`), the CONTENT term (`docs/CONTENT.md:L166`) and the settled
FDR rules (`docs/fdr.md:L332-L337`, R-129 to R-131, version 8 Settled).

## 5. Divergence lines

1. L27 claims the bar "adds S-6's `timed_run.py` check, which S-6's *Command* requires". S-6's check
   is "`python3 tests/timed_run.py` exits 0 and covers opening a summary" (`docs/SDD.md:L1176`).
   S1 carries "`python3 tests/timed_run.py` exits 0" only, without "covers opening a summary". That
   half is true today (`tests/timed_run.py:L5`, "opening a project's Summary"), so the gap changes
   nothing a check would find. But the line does not say what the divergence says it adds.
2. L27 supports its claim with "`grep -rniE 'due.today|due_today' tests` finds no due-today test".
   Run from `products/tracker17` at the commit read, that command prints 8 lines. The pattern
   matches `due=TODAY` in overdue-boundary fixtures (`tests/unit/test_summary.py:L285`,
   `make_task(2, status=TaskStatus.IN_PROGRESS, due=TODAY)`). The conclusion holds when the code is
   read, since no test asserts a due-today count. But a fresh session that runs the command as
   evidence gets output, not the empty result the line implies.

## 6. Readings left open

None found.

## What this review could not read

None.
