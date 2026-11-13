# 根回し Nemawashi seed — the UXD carries the due-today count

## What it is

Serves the Way `product-downstream`: tracker17 is the product the crew is proven on, and the owner asked for this summary count (my reasoning, not a lookup). Moves the finish line's **Works** bar, whose run-through is the PRD's use cases (`system/projects/tracker17/finish_line.md`).

PRD version 9 and SRS version 8 say the project summary shows the count of open tasks due today beside the overdue count (`products/tracker17/docs/SRS.md` § 3.11 FR-38). The UXD stops at the old list: UX-F6 names the total, status, priority, overdue, no-due-date and per-assignee counts, and UX-S5 follows it (`products/tracker17/docs/UXD.md` § 5.6, § 4 UX-S5). `grep -ci 'due today'` over the UXD finds none; the SDD, NFDR, `DESIGN.md` and `CONTENT.md` find none either, and the code does not show it (run from `products/tracker17`, 2026-11-13). `products/tracker17/docs/what_left.md` names it as not built. The next document in the chain cannot state the count until the UXD says where it sits and whether it is a link. After this, the UXD states it.

The item is on `products/tracker17/docs/UXD_open_issues.md` § 3.1, raised by this seat.

## Source

Cut from `products/tracker17/docs/SRS.md` § 3.11 FR-38 ("beside the overdue count, the due-today count"), read against `products/tracker17/docs/UXD.md` § 5.6 UX-F6 ("the total, the count per status, the count per priority, the overdue count, the count with no due date"); `products/tracker17/docs/what_left.md` ("Missing at: `7ffd5c365`"). The owner's answer is in `products/tracker17/docs/trail/prd/cycle-7.md` § 1.1 (2026-11-13).

## Stations — dynamic checklist

- [ ] uxd-folds-the-count — `UXD_open_issues.md` § 3.1 is answered and `product-uxd` has folded it: UX-F6, UX-S5 and its data line carry the due-today count, with its place, link or plain number, and zero state, and the companion is gone

## Relation to existing work

`tracker17 · nemawashi · 2026-11-13_the-srs-carries-the-due-today-count` sits in the pool with its work already on disk (SRS version 8, `a3b3d39cd`, companion gone); it wants a pick and a close rather than a second fold. Independent of `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` and `tracker17 · nemawashi · 2026-11-13_the-ignored-sigint-test-holds-in-a-full-run`.

## Out (later / elsewhere)

The SDD, FDR, NFDR, `DESIGN.md` and `CONTENT.md` re-runs waited for the UXD to carry it; the seed that builds the count in the product, `tracker17 · nemawashi · 2026-11-13_the-summary-shows-the-due-today-count`, was cut and walked without waiting, and the count is built (`e4209621a`). Each is swept or cut after this seed retires, not inside it.

Divergence, 2026-11-13 (`nemawashi-refine`, answer to `tracker17 · nemawashi · 2026-11-13_the-ignored-sigint-test-holds-in-a-full-run`): the work this seed asks for is on disk — UXD version 12 (`59b5394da`), Settled, carries the count at UX-F6 and UX-S5 and its companion is gone — so the seed wants a pick and a close, not a second fold; § What it is records the state when the seed was cut.

Divergence, 2026-11-13 (`shukuba-refine`, review of `tracker17 · tobiishi · 2026-11-13_summary-shows-due-today`): § Out no longer says the build seed waits for this one — the count is built on `main` (`e4209621a`) and `products/tracker17/docs/what_left.md` reads "Nothing is left to build."
