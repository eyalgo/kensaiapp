# 宿場 Shukuba — a posted closure is drawn on the map

*Item 3 on the active 根回し Nemawashi `the-trail-map-goes-live`. Slug: `closures-are-drawn`.*

## What it is

A closure a ranger posts shows on the map within 15 minutes (FR-2, FR-3). Lifting one is the next
station's. Walked as the change unit `closures-on-the-map`.

## Reached when

- `pytest tests/` exits 0.
- `tests/test_closures.py::test_posted_closure_is_drawn` and `::test_drawn_within_15_minutes` pass.

## Guardrail

- No lifting here; that is `a-closure-can-be-lifted`.
- **Not here:** `nearest-open-trail`.
