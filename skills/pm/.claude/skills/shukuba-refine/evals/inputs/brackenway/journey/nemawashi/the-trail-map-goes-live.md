# 根回し Nemawashi seed — the park's trail map goes live, with closures on it

## What it is

Walkers open the map and see every trail, and every closure the rangers post, within 15 minutes of
posting. Done: the map is public, current, and shows the nearest open trail.

## Source

The SRS, FR-1 to FR-4 (`docs/SRS.md`), cut by the Principal PM.

## Stations — dynamic checklist

- [x] trails-are-drawn — every trail in the park's survey file is drawn on the map
- [x] rangers-post-a-closure — a ranger posts a closure from the ranger page
- [x] closures-are-drawn — a posted closure shows on the map within 15 minutes
- [ ] a-closure-can-be-lifted — a ranger lifts a closure and the map clears it within 15 minutes
- [ ] nearest-open-trail — a walker sees the nearest open trail from where they stand
- [ ] map-works-on-a-slow-connection — the map is usable on a 3G connection
- [ ] map-is-public — the map is reachable without a login
- [ ] closure-times-are-measured — the time from post to map is recorded for every closure
