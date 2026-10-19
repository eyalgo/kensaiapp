# SRS — ferrule

**Status:** Settled · **Version:** 6

## Functional requirements

### FR-1 — Booking
A shop books a pickup with an address and a two-hour window. A booking fee is charged.

### FR-2 — Courier notice
The courier is sent each new booking.

### FR-3 — Status
The shop sees the pickup's status: booked, collected, delivered or cancelled.

### FR-4 — Cancellation
A shop may cancel a pickup until it is collected. The courier is told.

### FR-5 — Refund on cancellation
A pickup cancelled more than two hours before its window starts refunds the booking fee in full. A
later cancellation refunds nothing.

### FR-6 — Weekly report
Each Monday the shop gets a report of last week's pickups.
