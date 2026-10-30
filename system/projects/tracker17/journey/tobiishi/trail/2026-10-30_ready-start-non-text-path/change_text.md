# Change Text — a readable start prints a path with a non-text byte

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing

---

## Text

This file holds the exact words `tracker17 · tobiishi · 2026-10-30_ready-start-non-text-path` publishes, for the Developer to place as written. The ready line's wording does not change. Only the way `{location}` is written does.

### The saved-data location in the terminal's ready line

**The tracker started on readable saved data, none yet or a valid file, whatever the path holds**

> The tracker is running. Open {address} in your browser. Saved data is kept at {location}.

When the person sees it: they have started the tracker, and they know it is running, which address to open and where their saved data is. The tracker keeps serving until they press Ctrl-C.

`{address}` is `http://<host>:<port>` with the host and port the tracker actually bound.

`{location}` is the saved data's absolute path, written as follows:

- Each byte of the path that the machine's file-name decoding could not turn into text is written as four characters: a backslash, an x and the byte's two lowercase hex digits. Byte `0xe9` is written `\xe9`.
- Several such bytes are each written on their own, in place.
- Every other character of the path is written as it is, in order.
- The form is the same on every terminal encoding.
- The raw byte, the form `\udce9` and a replacement mark never appear.

The whole line at each kind of path, with the address as an example:

| The path | The line |
|---|---|
| Holds one non-text byte, from `b'/tmp/caf\xe9/data'` | `The tracker is running. Open http://127.0.0.1:8017 in your browser. Saved data is kept at /tmp/caf\xe9/data.` |
| Holds two non-text bytes, from `b'/tmp/a\xe9\xff/data'` | `The tracker is running. Open http://127.0.0.1:8017 in your browser. Saved data is kept at /tmp/a\xe9\xff/data.` |
| Holds a valid non-ASCII character, `/tmp/café/data` | `The tracker is running. Open http://127.0.0.1:8017 in your browser. Saved data is kept at /tmp/café/data.` |
| Holds a folder really named `a\xe9b`, seven plain characters | `The tracker is running. Open http://127.0.0.1:8017 in your browser. Saved data is kept at /tmp/a\xe9b/data.` |
| Holds plain characters only, `/Users/sam/tracker17/data` | `The tracker is running. Open http://127.0.0.1:8017 in your browser. Saved data is kept at /Users/sam/tracker17/data.` |

---

## Wording decisions

- **All readable paths share one string.** A path with a non-text byte and a path with none are one concept, the ready line, and only `{location}` differs. Two strings would invite two wordings, and CP-751 holds the plain path's line byte for byte.
- **The line adds no sentence explaining `\xe9`.** `docs/CONTENT.md` § Loading fixes the ready line's parts as "the tracker is running, the address to open, where the saved data is kept", and the design's `Publishes text:` line names only the location. The reader is a developer on their own machine (`docs/CONTENT.md` § Voice), so on this reading the form needs no gloss.
- **The hex digits are lowercase.** CP-748 sets this, following the only examples in `docs/CONTENT.md` § Grammar and mechanics, "A path the tracker prints". The finding below records that the rule itself leaves the case open.
- **A path that really holds a backslash reads the same as an escaped byte.** No string tells the two apart, because `docs/CONTENT.md` RN-33 leaves that case "Not covered" and CP-751 keeps the real backslash as it is.
- **This file says "terminal" where the spec and the design say "console".** `docs/CONTENT.md` § Terminology fixes the term and rejects "console". The published line uses neither word.
- **These states have no new words.** Ctrl-C writes nothing (CP-747). The unreadable start, its page and the failed-action line stay as they are (`change_spec.md` § Out of Scope). A valid character that an ASCII terminal can't write also stays as it is (the same section).
- **The banned-word check found nothing to replace.** The string and the table's lines were searched against the banned table in `docs/CONTENT.md` § Terminology and the banned punctuation in § Grammar and mechanics. The colon sits only inside an address, and § Grammar and mechanics allows that. The product carries no check that enforces its vocabulary: `git grep` over `products/tracker17/tests` and `products/tracker17/pyproject.toml` for the banned words "whoops", "uh-oh" and "unfortunately" returned nothing.

---

## Findings for the Content Manager

- `\xe9` in the ready line — `docs/CONTENT.md` § Grammar and mechanics, "A path the tracker prints", says "two hex digits" and does not state their case, while its only examples are lowercase — The string was written with lowercase digits, as CP-748 sets.
