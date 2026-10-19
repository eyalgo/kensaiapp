# 宿場 Shukuba — every alert states the harbour's local time

*Item 3 on the active 根回し Nemawashi `alerts-reach-the-harbour`. Slug: `alerts-carry-the-local-time`.*

## What it is

Alerts print tide times in UTC. This leg states each time in the harbour's own zone, with its
abbreviation, including on the day a daylight-saving change falls between two tides. Walked as the
change unit `local-time-in-alerts`.

## Reached when

- `pytest tests/` exits 0.
- `tests/test_alert_text.py::test_dst_day` asserts both tides on a change day in local time with the
  zone's abbreviation.

## Guardrail

- The alert's wording stays as FR-3 states it; only the time changes.
- **Not here:** `alerts-leave-on-time`, `quiet-hours`.
