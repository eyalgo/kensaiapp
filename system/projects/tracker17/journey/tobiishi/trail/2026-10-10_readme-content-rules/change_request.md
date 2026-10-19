# Change request — 2026-10-10_readme-content-rules

---

**Request:** Bring the README's setup text inside the content rules the last unit left it breaking. Two sentences in `products/tracker17/README.md`, between `## Status` and `## How it's built`, break `docs/CONTENT.md` § Grammar and mechanics. The first is the prerequisites sentence that ends with the Python download address, 21 words against the 20-word limit (`docs/CONTENT.md:120`); split it into sentences of 20 words or fewer that say the same thing, keeping the address https://www.python.org/downloads/ and the instruction to type the command again. The second is the line under "Setting saved data aside" that says the saved data is "now" in a new directory; reword it without "now" or any other of today, yesterday, tomorrow, ago, recently (`docs/CONTENT.md:126-127`), keeping what it tells the reader: the directory name, the date-and-time naming with its example, and the `ls ~/tracker17-set-aside` command. After the change, from `## Status` up to `## How it's built`, no sentence runs longer than 20 words and `grep -n -w -i -e today -e yesterday -e tomorrow -e now -e ago -e recently products/tracker17/README.md` matches nothing in that span. Any other sentence in the span found over 20 words or carrying one of those words is fixed the same way.

What must not be weakened: the README's meaning and every command in it stay as they are; every heading stays, with "Starting the tracker again" and "Setting saved data aside" spelled exactly; `main.py`, the tests and the product's behaviour do not change; the `docs/` definition documents are not edited; "How it's built" and "The documents" stay as they stand; the tests that read the README's headings keep passing, and `pytest tests/` and `pytest tests/e2e/` still exit 0 from `products/tracker17/`.

**Sizing:** the acceptance boundary is the station's reached-when 8, one capability: the README's setup text keeps the content rules the product states. Both sentences are one obligation of that contract, checked by the one grep and the one length rule, so they are one honest merge and one flow. Reached-when 1 to 7 were checked by the last unit's refine and are guarded here, not redone.
**Category:** bug
**Behaviour:** preserving
**Classified because:** the station's reached-when 8 says the README keeps `docs/CONTENT.md:120` and `:126-127`, and `README.md:23` and `:81` break them (21 words; "now"); the text is reworded with its meaning unchanged, so it adds nothing to the contract.

**Sealed:** 2026-10-11 — accepted; merged to `main` via `--no-ff`.
