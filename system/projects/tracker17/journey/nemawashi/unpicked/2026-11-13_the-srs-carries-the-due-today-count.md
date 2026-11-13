# 根回し Nemawashi seed — the SRS carries the due-today count

## What it is

Serves the Way `product-downstream`: tracker17 is the product the crew is proven on, and its summary is one the owner just asked for (my reasoning, not a lookup). Moves the finish line's **Works** bar, whose run-through is the PRD's use cases (`system/projects/tracker17/finish_line.md`).

PRD version 9 says the project summary shows the count of open tasks due today beside the overdue count (`products/tracker17/docs/PRD.md` § Core Features, **Project summary**). The SRS stops at version 7 and FR-38 lists no such count (`products/tracker17/docs/SRS.md` § 3.11). The UXD, SDD and NFDR do not mention it, the FDR only repeats that a task due today is not overdue, and the code does not show it (`grep -ci 'due today'` over each document; `grep -rniE 'due.today'` over `*.py` and `*.html`, run from `products/tracker17`, 2026-11-13). `products/tracker17/docs/what_left.md` names it as not built. The PRD's change reaches the product only through the documents derived from it, so the work cannot be cut until they carry it. After this, the SRS states the count, and the later documents can follow.

The item is on `products/tracker17/docs/SRS_open_issues.md` § 3.1, raised by this seat.

## Source

Cut from `products/tracker17/docs/PRD.md` § Core Features, **Project summary** ("Beside the overdue count, it shows the count of tasks due today"), read against `products/tracker17/docs/SRS.md` § 3.11 FR-38 ("the overdue count, under FR-25"); `products/tracker17/docs/what_left.md` ("Missing at: `7ffd5c365`"). The owner's answer is in `products/tracker17/docs/trail/prd/cycle-7.md` § 1.1 ("Summary: due-today count", 2026-11-13).

## Stations — dynamic checklist

- [ ] srs-folds-the-count — `SRS_open_issues.md` § 3.1 is answered and `product-srs` has folded it: FR-38 and its acceptance criterion carry the due-today count, and the companion is gone

## Relation to existing work

Independent of `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` and `tracker17 · nemawashi · 2026-11-13_the-ignored-sigint-test-holds-in-a-full-run`.

## Out (later / elsewhere)

The UXD, SDD, FDR and NFDR re-runs, and the seed that builds the count in the product, wait for the SRS to carry it. Each is cut or swept after this seed retires, not inside it.
