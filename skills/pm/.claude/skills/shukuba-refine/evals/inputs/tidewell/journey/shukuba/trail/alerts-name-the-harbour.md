# 宿場 Shukuba — every alert names its harbour and its tide

*Item 2 on the active 根回し Nemawashi `alerts-reach-the-harbour`. Slug: `alerts-name-the-harbour`.*

## What it is

An alert says which harbour and whether the tide is high or low, in FR-3's words.

## Reached when

- `pytest tests/` exits 0.
- `tests/test_alert_text.py::test_names_harbour_and_tide` asserts the exact FR-3 text for one high and
  one low tide.

## Guardrail

- The time stays in UTC here; local time is the next station's.
- **Not here:** `alerts-carry-the-local-time`.
