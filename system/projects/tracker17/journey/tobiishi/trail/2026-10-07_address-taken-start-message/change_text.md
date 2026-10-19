# Change Text — One plain message when something else holds the tracker's address

**Date:** 2026-10-07
**Category:** feature
**Behaviour:** changing

---

## Text

### The console message a start shows when something else is already using the tracker's address

**A start that can't take its address, because another program already uses it**

> The tracker didn't start, because something else is already using the address {address}. Stop that program, then start the tracker again.

`{address}` is the address the start tried to take, written as the host, a colon and the port, with no `http://` in front. Under `python3 main.py` it reads `127.0.0.1:8017`, so the whole line is:

> The tracker didn't start, because something else is already using the address 127.0.0.1:8017. Stop that program, then start the tracker again.

The string is the whole of what the terminal shows for this start, on one line. No other line comes before or after it.

When the person sees it: they typed the start command and the tracker isn't running, and they can stop the program that holds the address and type the start command again.

---

## Wording decisions

- The line is CONTENT's first Terminal messages example (`products/tracker17/docs/CONTENT.md:250`), word for word, with the address as its one variable part. The spec fixes the same line in CP-40, so no word moved. Checked against CONTENT: both sentences are under 20 words (13 and 8), the message has two sentences, the negative is contracted, the only colon sits inside the address, and the line has no exclamation mark, em dash or semicolon.
- The address is a placeholder and not the literal `127.0.0.1:8017`. The design names the address as the line's one variable part (`change_design.md` § 3, Sub-job M), and CONTENT § Localization lists an address as a value a placeholder may hold. The placeholder keeps the line true when a start tries a different address, because a line naming an address the tracker didn't try would send the reader to stop the wrong program (`change_spec.md`, Locked Answers Gap 3).
- The address has no `http://` in front. CONTENT's example writes it bare. The ready line's `http://` form is an address to open in a browser, and this line names the address the tracker failed to take.
- The line carries no second line holding the system's own error text. CONTENT gives that second line to "an action" that fails. It defines a failed start as "one paragraph" (`products/tracker17/docs/CONTENT.md:243-246`), and the spec requires exactly one message with no traceback (CP-39). The sealed unreadable-data start already prints one line and no error text (`products/tracker17/main.py:41-42`).
- No string is written for a start refused the address for any other reason. The spec leaves that start unchanged (CP-42, Out of Scope). Showing this line there would name a cause the tracker didn't establish, which CONTENT § Voice rules out ("State only what the tracker established").
- No new string is written for a start whose saved data can't be read while the address is also held. That start shows the sealed unreadable-data line alone (CP-43), and this change doesn't touch its wording.
- No new string is written for a second tracker on the same saved data. Until another unit gives that case its own message, its start finds the address held and shows this line, which is true for that start (`change_spec.md`, Out of Scope).
- Banned-word check: I searched the line for every word in CONTENT § Terminology's "Banned in anything a person sees" table and its "Rejected" column, in every inflection, and found none of them. "Address" is CONTENT's term, and "host" and "port" stay out of the line. "Program" is the word CONTENT's own example uses for whatever holds the address. The product carries no check that enforces its vocabulary, so I had no product check to run.

---

## Findings for the Content Manager

None.
