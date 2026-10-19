# 根回し Nemawashi seed — a shop books, tracks and cancels a pickup

## What it is

A shop books a courier pickup, watches its status and can cancel it. Done: all three work from the
shop's own page, and a cancellation costs what FR-5 says.

## Source

The SRS, FR-1 to FR-6 (`docs/SRS.md`), cut by the Principal PM.

## Stations — dynamic checklist

- [x] booking-takes-an-address — a shop books with an address and a window, and pays the fee
- [x] courier-is-notified — the courier gets each new booking
- [x] pickups-can-be-cancelled — the cancel operation exists and tells the courier
- [ ] customer-sees-pickup-status — the shop's page shows each pickup's status
- [ ] customer-cancels-from-the-app — a shop cancels a pickup from its page
- [ ] pickups-are-reported-weekly — each Monday the shop gets last week's pickups
