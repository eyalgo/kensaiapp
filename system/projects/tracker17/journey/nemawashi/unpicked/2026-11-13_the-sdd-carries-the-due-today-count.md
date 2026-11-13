# 根回し Nemawashi seed — the SDD carries the due-today count

## What it is

Serves the Way `product-downstream`: tracker17 is the product the crew is proven on, and the owner asked for this summary count (my reasoning, not a lookup). Moves the finish line's **Works** bar, whose run-through is the PRD's use cases (`system/projects/tracker17/finish_line.md`).

UXD version 12 shows the due-today count on the project summary, directly after the overdue count (`products/tracker17/docs/UXD.md` § 5.6 UX-F6, § 4 UX-S5). The SDD's summary slice stops short of it: § 6 S-6 `project-summary` lists the counts it delivers without it and traces to FR-25, FR-38 and UX-F6, UX-S4, UX-S5 only. `grep -ciE 'due.today' products/tracker17/docs/SDD.md` → 0 (run from `products/tracker17`, 2026-11-13). The code shows none either, and `products/tracker17/docs/what_left.md` names the count as not built. The build seed cannot be cut until the SDD names the slice that carries it. After this, the SDD does, with its place in § 7.

The item is on `products/tracker17/docs/SDD_open_issues.md` § 5.1, raised by this seat.

## Source

Cut from `products/tracker17/docs/UXD.md` § 5.6 UX-F6 ("the due-today count ... sits directly after the overdue count"), read against `products/tracker17/docs/SDD.md` § 6 S-6 *Reached when* → *Behaviour* ("the overdue count, the count with no due date"); `products/tracker17/docs/what_left.md` ("Missing at: `7ffd5c365`"). The owner's answer is in `products/tracker17/docs/trail/prd/cycle-7.md` § 1.1 (2026-11-13).

## Stations — dynamic checklist

- [ ] sdd-folds-the-count — `SDD_open_issues.md` § 5.1 is answered and `product-sdd` has folded it: a slice or a re-cut of S-6 carries the count, with its § 7 edge and its § 8 fields, and the companion is gone

## Relation to existing work

`tracker17 · nemawashi · 2026-11-13_the-srs-carries-the-due-today-count` and `tracker17 · nemawashi · 2026-11-13_the-uxd-carries-the-due-today-count` sit in the pool with their work already on disk (SRS version 8, UXD version 12, both companions gone); each wants a pick and a close, not a second fold. Beside `tracker17 · nemawashi · 2026-11-13_the-content-carries-the-due-today-count`, which reads the UXD and not the SDD. Independent of `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract`.

## Out (later / elsewhere)

The FDR and NFDR re-runs waited for the SDD to carry it; the seed that builds the count in the product, `tracker17 · nemawashi · 2026-11-13_the-summary-shows-the-due-today-count`, was cut and walked without waiting, and the count is built (`e4209621a`). Each is cut or swept after this seed retires, not inside it. The FDR is this seat's own, through `product-fdr`.

Divergence, 2026-11-13 (`shukuba-refine`, review of `tracker17 · tobiishi · 2026-11-13_ignored-sigint-timing`): the work this seed asks for is on disk — SDD version 23 (`edd4235e1`), Settled, carries the count and its companion is gone — so the seed wants a pick and a close, not a second fold; the grep in § What it is records the state when the seed was cut.

Divergence, 2026-11-13 (`shukuba-refine`, review of `tracker17 · tobiishi · 2026-11-13_summary-shows-due-today`): § Out no longer says the build seed waits for this one — the count is built on `main` (`e4209621a`) and `products/tracker17/docs/what_left.md` reads "Nothing is left to build."
