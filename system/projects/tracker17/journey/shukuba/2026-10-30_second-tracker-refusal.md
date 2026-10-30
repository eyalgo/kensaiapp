# 宿場 Shukuba — a second tracker on the same saved data is refused

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-11_protect-saved-data`. Slug: `second-tracker-refusal`.*

## What it is

Before this station nothing but a taken address stopped a second tracker from starting on the
saved-data location a running tracker uses. This station adds the one lock (ADR-0009, SDD `SM-5`) so a second start on that
location prints one plain message and exits while the first tracker carries on untouched, and a start
after the first tracker was killed succeeds. Both halves of SRS AC-16 land as tests, and the README
says what a start does in both cases. It is one station, apart from the unreadable-data page, because
the lock was the unproven part (no lock in the code, no kill-recovery shown) and the page needs none of it.

## Reached when

All hold, checked from the repository root on `main`:

1. **Refusal.** A test under `products/tracker17/tests/` starts a tracker, starts a second on the same
   saved-data location, and asserts: the second start prints one plain message naming that it is
   refused because another tracker is using the location, and exits without serving; the first
   tracker still answers a request afterwards; the saved data's bytes are unchanged.
2. **Recovery.** A test under the same tree kills the first tracker (a kill the tracker cannot handle),
   then starts a tracker on the same location and asserts it serves.
3. **The tests are real.** Run against the tree as it was before this station (the commit it was
   opened at), the two tests fail; run after, they pass.
4. **Suites.** `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and
   `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/` both exit 0.
5. **README.** `grep -c -i -F "another tracker" products/tracker17/README.md` prints at least 1 (it
   prints 0 before this station), and the passage it finds says a second start on a location in use is
   refused with a message while the first carries on, and that a start after a kill succeeds.

## Guardrail

- The lock is the one in ADR-0009: Unix only, no Windows path, no operating-system check, no message for one.
- A start on unreadable saved data keeps today's exit-1 stop; changing it is the next station's.
- Saved data is never written, replaced or deleted by the refusal (SDD SD-4).
- No change to the address-taken behaviour, the screens, or the data model.
- **Not here:** the unreadable-data page, its console message, the set-aside restart, the one-test-per-DR-6-break
  work and the README's unreadable-data description are `tracker17 · nemawashi · 2026-10-11_protect-saved-data`'s
  item 2, `unreadable-data-page`.
