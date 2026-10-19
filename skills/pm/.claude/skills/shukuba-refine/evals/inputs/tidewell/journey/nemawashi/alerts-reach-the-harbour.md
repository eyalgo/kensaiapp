# 根回し Nemawashi seed — every subscribed harbour user gets the day's tide alerts on time

## What it is

A harbour user follows one harbour and gets a message before each high and low tide. Done: alerts
leave on time, in the harbour's local time, and a user can pause and stop them.

## Source

The SRS, FR-1 to FR-6 (`docs/SRS.md`), cut by the Principal PM.

## Stations — dynamic checklist

- [x] tides-are-computed-per-harbour — the tide table for a harbour is computed for the next 7 days
- [x] alerts-name-the-harbour — each alert names the harbour and the tide
- [x] alerts-carry-the-local-time — times in the harbour's own zone, across a daylight-saving change
- [ ] alerts-leave-on-time — an alert leaves 30 minutes before its tide, within one minute
- [ ] quiet-hours — a user's quiet hours hold an alert until they end
- [ ] pause-and-resume — a user pauses alerts and resumes them
- [ ] unsubscribe — a user stops alerts with one message
- [ ] delivery-is-measured — the share of alerts sent on time is recorded daily

## Out (later / elsewhere)

- A second tide source — `unpicked/tide-data-from-a-second-source.md`.
