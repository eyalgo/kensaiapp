# Change request — local-time-in-alerts

*The PM-minted intake for one 飛び石 Tobiishi — the single change `/development tidewell` carries
through the pipeline.*

---

**Request:** Every time in an alert is stated in the harbour's own time zone with the zone's
abbreviation (SRS FR-4), including on the day a daylight-saving change falls between two tides. Today
alerts print UTC.

In scope: the alert's time and its zone abbreviation. Out of scope: the alert's wording (FR-3), quiet
hours (FR-5).

**Category:** feature
**Behaviour:** changing

---

**Sealed:** 2026-09-09 — accepted; merged to `main` via `--no-ff`.
