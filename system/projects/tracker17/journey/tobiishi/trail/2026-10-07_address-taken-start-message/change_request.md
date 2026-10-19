# Change request — 2026-10-07_address-taken-start-message

*Opened from station `2026-10-07_a-project-that-stays` (item 1 of `tracker17 · nemawashi · 2026-10-07_first-project`). Third change unit of that station; the station may take more.*

---

**Request:** Make a start while something else holds the tracker's address print one plain message and stop. Run from `products/tracker17/` under `python3 main.py`. Today the bind error propagates out of the listener (`web/listener.py:5`, "A bind error propagates: the signal that the address is taken is the next change unit's"), so the console shows the standard library's traceback. After this change the console shows a single plain, one-paragraph message that says something else is already using the address and what to do next (SRS FR-3; UXD UX-S2 error), with its words taken from the product's content record (`docs/CONTENT.md:250`), and no string invented in code. The start exits with a failing status, serves nothing, and writes nothing to the saved data: no `data/` folder or file is created or changed by the failed start. A start that cannot read its saved data keeps stopping with its own one plain message as sealed.

Tests ship with it: an integration test that a start against an address already held prints the message, returns a failing status and leaves the saved-data location untouched, and an end-to-end or process-level test under the real start command, `python3 main.py`, with another listener holding the address. `pytest tests/` and `pytest tests/e2e/` each exit 0.

**Must not be weakened or added:** the SDD's seams are used as written, with the composition root still the only place that wires concrete parts (`main.py`); the console shows nothing before the ready line on a good start (UX-S2); no tasks, add-task form, People or All tasks links, rename or delete; no unreadable-data page and no second-tracker refusal (another tracker on the same saved data is `protect-saved-data`'s, not this unit's); the setup README is not touched beyond what the tests need; project creation, its refusals, the not-found page and saved data keep behaving as sealed.

**Left to later change units of this station:** the pointer test's reverse direction (station reached-when 8) and the check that the station's whole reached-when holds. The README is the next station.

**Sizing:** the acceptance boundary is one operator action, starting the tracker while its address is held and being told so in plain words (SDD § 6 S-1, *Behaviour*, last sentence; UXD UX-S2; station reached-when 3). The message, the exit, the no-write guarantee and their tests stay together (`pm_right_size.md` § *Right-size to one honest merge*). The reverse pointer test is a different responsibility, keeping the trace between documents and code honest, with its own acceptance boundary (SDD § 4 TS-4), so it is a later unit.

**Category:** feature
**Behaviour:** changing
**Classified because:** the station's reached-when 3 reads "Starting while something else holds the address prints one plain message", and the product shows the standard library's traceback today, so a console message the operator acts on is added to the contract.

**Sealed:** 2026-10-07 — accepted; merged to `main` via `--no-ff`.
