# 宿場 Shukuba — a booked pickup can be cancelled

*Item 3 on the active 根回し Nemawashi `pickups-end-to-end`. Slug: `pickups-can-be-cancelled`.*

## What it is

The cancel operation: a booked pickup becomes cancelled and the courier is told (FR-4). No shop page
calls it yet. Walked as the change unit `cancel-endpoint-lands`.

## Reached when

- `pytest tests/` exits 0.
- `tests/test_cancel.py::test_cancel_tells_courier` and `::test_collected_is_refused` pass.

## Guardrail

- No shop-facing page here; that is `customer-cancels-from-the-app`.
- **Not here:** `customer-sees-pickup-status`.
