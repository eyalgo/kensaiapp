# 根回し Nemawashi seed — CONTENT carries the due-today count

## What it is

Serves the Way `product-downstream`: tracker17 is the product the crew is proven on, and the owner asked for this summary count (my reasoning, not a lookup). Moves the finish line's **Works** bar, whose run-through is the PRD's use cases (`system/projects/tracker17/finish_line.md`).

UXD version 12 labels the due-today count "in words" and shows it as a plain number directly after the overdue count (`products/tracker17/docs/UXD.md` § 5.6 UX-F6). `CONTENT.md` fixes "Overdue" as the term for the overdue state and the accessible name of a summary count ("3 overdue tasks") and has no term for tasks due today: `grep -ciE 'due.today' products/tracker17/docs/CONTENT.md` → 0 (run from `products/tracker17`, 2026-11-13). The build would write a string with no standard behind it, and the Content Editor may not invent one. After this, `CONTENT.md` states the label, the term against its rejected words, and the accessible name where one is owed.

`DESIGN.md` is not raised: the count is a plain number in the summary's existing type, and the UXD names no new mark (`grep -ciE 'due.today' DESIGN.md` → 0 is not a gap by itself; my reasoning, not a lookup). The CDO's re-run decides otherwise if it reads it differently.

The item is on `products/tracker17/docs/CONTENT_open_issues.md` § 3.1, raised by this seat.

## Source

Cut from `products/tracker17/docs/UXD.md` § 5.6 UX-F6 ("labelled in words and never shown by colour alone"), read against `products/tracker17/docs/CONTENT.md` (the "Overdue" term row; "3 overdue tasks"). The owner's answer is in `products/tracker17/docs/trail/prd/cycle-7.md` § 1.1 (2026-11-13).

## Stations — dynamic checklist

- [ ] content-folds-the-count — `CONTENT_open_issues.md` § 3.1 is answered and `product-content` has folded it: the label, the term with its rejected words and the accessible name are in `CONTENT.md`, and the companion is gone

## Relation to existing work

Beside `tracker17 · nemawashi · 2026-11-13_the-sdd-carries-the-due-today-count`: both read the UXD and neither reads the other. `tracker17 · nemawashi · 2026-11-13_the-uxd-carries-the-due-today-count` has its work on disk (UXD version 12) and wants a pick and a close.

## Out (later / elsewhere)

Built: the seed that builds the count in the product, `tracker17 · nemawashi · 2026-11-13_the-summary-shows-the-due-today-count`, was cut and walked without waiting, and the count is built (`e4209621a`).

Divergence, 2026-11-13 (`shukuba-refine`, review of `tracker17 · tobiishi · 2026-11-13_ignored-sigint-timing`): the work this seed asks for is on disk — CONTENT version 22 (`f3749d5bf`), § Terminology row "Due on {date}", Settled, carries the count and its companion is gone — so the seed wants a pick and a close, not a second fold; the grep in § What it is records the state when the seed was cut.

Divergence, 2026-11-13 (`shukuba-refine`, review of `tracker17 · tobiishi · 2026-11-13_summary-shows-due-today`): § Out no longer says the build seed waits for this one — the count is built on `main` (`e4209621a`) and `products/tracker17/docs/what_left.md` reads "Nothing is left to build."
