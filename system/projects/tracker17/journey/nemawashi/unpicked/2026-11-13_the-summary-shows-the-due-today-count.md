# 根回し Nemawashi seed — the summary shows the due-today count

## What it is

Serves the Way `product-downstream`: tracker17 is the product the crew is proven on, and the owner asked for this count (my reasoning, not a lookup). Moves the finish line's **Works** bar, whose run-through is the PRD's use cases (`system/projects/tracker17/finish_line.md`).

PRD version 9, SRS version 8, UXD version 12, CONTENT version 22 and SDD version 23 all say a project's summary shows the count of open tasks due today directly after the overdue count, as a plain number, 0 included, under one "today" for both counts. The product does not: `grep -rniE 'due.today|due_today' domain application web --include='*.py' --include='*.html'` prints nothing (run from `products/tracker17`, 2026-11-13, at `edd4235e1`), `domain/summary.py`'s `ProjectSummary` has `overdue` and no due-today field, and `products/tracker17/docs/what_left.md` lists the count as missing. S-6's bar is unmet by the product, and SDD § 10 RC-7 hands the build to this seat. After this, the summary shows the count with the label "Due on {date}" (`products/tracker17/docs/CONTENT.md` § Terminology), and the tests of SRS AC-13's due-today side pass.

## Source

Cut from `products/tracker17/docs/SDD.md` § 6 S-6 *Reached when* → *Behaviour* ("directly after it the due-today count") and *Command* ("AC-13's due-today side"), with § 10 RC-7 *Still unresolved* ("the Principal PM cuts the build from S-6's unmet share"). Label from `products/tracker17/docs/CONTENT.md` § Terminology, row "Due on {date}". Not-built claim from `products/tracker17/docs/what_left.md` ("Missing at: `7ffd5c365`").

## Stations — dynamic checklist

- [ ] summary-shows-due-today — a project's summary shows the due-today count, an open task due on the summary's one date, directly after "Overdue", as a plain number, 0 on an empty project, labelled "Due on {date}"; a task due that day is never also overdue; one done or cancelled is in neither count; both commands of the card's test command pass

## Relation to existing work

Waits on the FDR, which is this seat's: `products/tracker17/docs/fdr.md` version 6 R-96 lists the summary's counts and omits this one, and it read PRD version 7, SRS version 6 and SDD version 18. A change that moves scope past the FDR is returned `fdr-update-needed` to this seat, so `product-fdr` runs before this seed is walked (a gate, not a preference; `<CORE>/roles/CROSS_ROLE.md` § 9 *FDR gate*). The documents themselves are settled. The four seeds that fold the count into the SRS, UXD, SDD and CONTENT have their work on disk and sit in the pool; this seed does not wait for them to be picked: `tracker17 · nemawashi · 2026-11-13_the-srs-carries-the-due-today-count`, `tracker17 · nemawashi · 2026-11-13_the-uxd-carries-the-due-today-count`, `tracker17 · nemawashi · 2026-11-13_the-sdd-carries-the-due-today-count`, `tracker17 · nemawashi · 2026-11-13_the-content-carries-the-due-today-count`. Independent of `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract`.

## Out (later / elsewhere)

No "Due on" marker on list rows and no due-today filter: the PRD places the count in the summary only (SDD § 6 S-6 *Not in this slice*). No summary across projects. The count's link behaviour stays a plain number.
