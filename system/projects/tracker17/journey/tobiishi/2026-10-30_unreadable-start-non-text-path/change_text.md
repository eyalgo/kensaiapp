# Change Text — show non-text path bytes on an unreadable start

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing

---

## Text

These are the exact words of the two places this change touches. Every word outside `{location}` is what the tracker writes today, so the one thing that moves is how `{location}` is written.

`{location}` in both places is the saved data's location, shown as one absolute path. Each byte of the path that is not text is written as a backslash, an x and the byte's two lowercase hex digits, in the place the byte sits. Several such bytes are each written on their own. Every other character of the path is written as it is, a valid `é` and a real backslash included. No mark that stands for a character replaces a byte. The same form is written whatever encoding the terminal has.

| The machine's path | What the person reads as `{location}` |
|---|---|
| The bytes `/tmp/caf`, `e9`, `/data` | `/tmp/caf\xe9/data`, where `\xe9` is four characters |
| The bytes `/tmp/a`, `e9`, `ff`, `/data` | `/tmp/a\xe9\xff/data` |
| `/tmp/café/data`, valid text | `/tmp/café/data` |
| A folder really named `a\xe9b`, seven plain characters | `a\xe9b` |
| `/Users/sam/tracker17/data`, plain characters | `/Users/sam/tracker17/data` |

### The unreadable-data line in the terminal

**The tracker started on saved data it couldn't read, at any location**

> The tracker couldn't read its saved data at {location}, and nothing in it was changed. Open http://{address} in your browser to read this on a page. To start fresh on purpose, follow Setting saved data aside in the setup instructions.

`{address}` is the address the start is serving on, such as `127.0.0.1:8017`.

When the person sees it: the start has just printed this as its first and only line in place of the ready line, and they can open the address or follow the named section of the setup instructions.

### The unreadable-data page

**Any address opened while the tracker serves on saved data it couldn't read, at any location**

The page title:

> The saved data can't be read - tracker17

The heading:

> The saved data can't be read

The sentences under the heading:

> The tracker couldn't read its saved data, which is kept at {location}. Nothing in it was changed or overwritten. To start fresh on purpose, follow Setting saved data aside in the setup instructions.

On this page, a `<`, a `&` or a `"` in the path is shown as that character.

When the person sees it: the page replaces every page of the tracker and offers no control, so they can read where the saved data is and follow the named section of the setup instructions.

---

## Wording decisions

- The page and the line each keep one string for a path with such a byte and for a path without one — `change_spec.md` rule CP-763 holds a plain path to today's bytes, and `products/tracker17/docs/CONTENT.md` § Grammar and mechanics, "It is one form in every place a path is written", gives the byte no message of its own.
- No sentence explains what `\xe9` means — the request says "with no new wording", and the terminal line and the page each already carry the three sentences that are the limit in `products/tracker17/docs/CONTENT.md` § Grammar and mechanics, "A message has at most three sentences".
- The first place is named as a line in the terminal, where the design's `Publishes text:` line says console — `products/tracker17/docs/CONTENT.md` § Terminology picks "terminal" for that window.
- The hex digits are lowercase and each byte is written on its own — `change_spec.md` § Locked Answers, Gaps 3 and 4, settled both, and the standard's only example is lowercase. The missing rule on case is raised below.
- The address is one placeholder, `{address}` — `products/tracker17/docs/CONTENT.md` § Localization names an address as what one placeholder holds. What the person reads is unchanged.
- The page title and the heading are written out although they carry no path — a Developer reading this file cold can then see that the whole page holds these words and no others.
- Ctrl-C at this start has no string — `change_spec.md` rule CP-757 has it stop with nothing more written, so no message is owed.
- A folder name that really holds a backslash, an x and two hex digits reads the same as an escaped byte, and no words tell the two apart — `products/tracker17/docs/CONTENT.md` RN-33 records that case as not covered, and `change_spec.md` § Out of Scope leaves it out.

---

## Findings for the Content Manager

- "The tracker couldn't read its saved data, which is kept at {location}." — the standard does not say how to name a location that holds no saved data. A start at a location beneath a regular file reaches this page (`change_spec.md` rule CP-767), and nothing is kept at that location. — written as `products/tracker17/docs/CONTENT.md` § Error, "Saved data that can't be read", sets it, because the request allows no other text to change.
- `/tmp/a\xe9\xff/data` — `products/tracker17/docs/CONTENT.md` § Grammar and mechanics, "A path the tracker prints", says "two hex digits" and does not state their case. — written lowercase, as that rule's example and the tracker's ready line write them.
