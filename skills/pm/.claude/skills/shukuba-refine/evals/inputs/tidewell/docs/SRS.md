# SRS — tidewell

**Status:** Settled · **Version:** 4

## Functional requirements

### FR-1 — Tide table
The service computes each followed harbour's high and low tides for the next 7 days, from the harbour
authority's published feed.

### FR-2 — Subscription
A user follows exactly one harbour.

### FR-3 — Alert
30 minutes before each tide the user gets one message: the harbour's name, "high" or "low", and the
tide's time.

### FR-4 — Local time
Every time in an alert is in the harbour's own time zone, with the zone's abbreviation.

### FR-5 — Quiet hours
A user may set quiet hours; an alert due inside them is held until they end.

### FR-6 — Stop and pause
"PAUSE", "RESUME" and "STOP" each take effect on the next alert.
