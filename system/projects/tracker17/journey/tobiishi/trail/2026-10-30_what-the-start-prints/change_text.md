# Change Text — the setup instructions name the third line a start can print

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing

---

## Text

### The setup instructions' "What the start prints" section

These strings are the whole text of the section, in reading order, from its heading to the next heading. The heading stays as it is. Each quoted string below is one paragraph, except the ready line's example, which keeps its place as a block of its own. Backticks are part of the text, because the setup instructions set a program's words in them. Every string is literal: the address and the example location are written as shown, and no part is filled in when the section is read.

**The tracker is ready: the sentence that introduces the line (unchanged)**

> When the tracker is ready, the terminal shows one line like this one.

When the person sees it: they have just typed the start command and want to know what the terminal should show. They can compare their own terminal with the example that follows.

**The tracker is ready: the example line (unchanged)**

> The tracker is running. Open http://127.0.0.1:8017 in your browser. Saved data is kept at /Users/sam/copy/products/tracker17/data.

When the person sees it: they are reading the program's own ready line with an example location. They can match it against what their terminal shows.

**The tracker is ready: what the line means**

> That line means the tracker is running. With that line, open http://127.0.0.1:8017 in your browser to see the Projects page. Your own copy's location appears in place of `/Users/sam/copy/products/tracker17/data`.

When the person sees it: their terminal shows the ready line. They know the tracker is up and can open the address to reach Projects.

**The tracker started on saved data it can't read**

> When the tracker starts on saved data it can't read, the line starts with `The tracker couldn't read` instead. The tracker is still running when that line shows. To start fresh on purpose, follow Setting saved data aside in these setup instructions.

When the person sees it: their terminal shows the line that starts with those words and no ready line. They know the tracker is up, and they know where to go if they want to start fresh. If they do nothing, the tracker keeps running.

**Either running line: how long the tracker runs and how to stop it**

> After either `The tracker is running` or `The tracker couldn't read`, the tracker keeps running until you stop it. To stop it, press Ctrl-C in its terminal.

When the person sees it: their terminal shows one of the two running lines and the prompt hasn't come back. They know that is expected and how to end it.

**This start didn't go ahead**

> A line that starts with `The tracker didn't start` means this start has stopped. The line says why and what to do next.

When the person sees it: their terminal shows the line that starts with those words. They know this start ended and that the line itself gives the reason and the action. Nothing here tells them to stop anything, and nothing says another tracker has stopped.

---

## Wording decisions

- The sentence that names the third line says "When the tracker starts on saved data it can't read", where the request says the line is printed "when the saved data cannot be read". — Saved data that can't be read doesn't always produce that line: a start refused because the address is held or another tracker is running prints `The tracker didn't start` whatever the data holds (`products/tracker17/main.py`, `_serve_claimed`). The smaller true thing is that the line belongs to a start that went ahead on that data. It still tells the reader what CP-737 asks for.
- The keep-running sentence names both running lines by their starting words, and the sentence that says Ctrl-C follows it directly. — CP-742 and the design's Architect Review Notes, "Explicit running-case scope", rule out relying on nearness to set the scope. Saying "either line" alone would have left the reader to work out which two of the lines were meant.
- The `The tracker didn't start` sentence moves to the end of the section, after the keep-running and Ctrl-C sentences. — Today those two sentences follow it directly and read as applying to it. Placing it last removes that reading. The spec fixes no order, so the order is set here, and the Developer places the strings in this order.
- "With that line, open http://127.0.0.1:8017" replaces the bare "Open http://127.0.0.1:8017". — CP-740 ties the Projects page to the ready line only, because with the third line every address shows one other page. The bare imperative read as true of any line.
- The section says nothing about what the browser shows after the third line. — CP-740 needs only that Projects isn't claimed for it, and the third line tells the reader itself to open the address and read the page. "Starting the tracker again" already describes that page, so a sentence here would be a second telling.
- The section doesn't use the word "three", and the request's "all three lines" is met by naming each line. — CP-743 allows the count only with its limits explained. Leaving it out avoids any reading that nothing else can appear in the terminal.
- "this start has stopped" limits the stop to the one start. — CP-741 requires it, because a refused second start leaves the first tracker running. The section adds no separate sentence about the first tracker, because "Starting the tracker again" already says it carries on, and the spec's Out of Scope rules out a sentence for each refusal reason.
- The next step keeps the program's condition, "To start fresh on purpose". — CP-739 requires it, and a bare "follow Setting saved data aside" would present setting data aside as the only thing to do about a tracker that is still running and has changed nothing.
- The heading is written bare and capitalised as a heading, with no quote marks: "follow Setting saved data aside". — `products/tracker17/docs/CONTENT.md` § Terminology says a string that points to a section "quotes its heading exactly", and § Grammar and mechanics keeps straight single quotes for a value the reader typed. Both examples of this pointer in § Message patterns, Error are bare, and so is the program's line, so the bare form is the standard as applied.
- "in these setup instructions" replaces the program's "in the setup instructions". — The reader is already inside the document, as its opening sentence says "These are tracker17's setup instructions". The program's line stays quoted as the program prints it wherever it is quoted, and this sentence is the section's own.
- "That line means the tracker is running" comes before the location sentence, which moves to the end of its paragraph. — The meaning is what the reader is sorting the lines by, so it comes first, and "That line" then has its referent directly before it.
- No longer quotation of the third line is written. — CP-737 makes it optional, and the whole line already stands under "Starting the tracker again". The starting words are enough to recognise it.
- The banned lexicon in `products/tracker17/docs/CONTENT.md` § Terminology and § Grammar and mechanics was searched in every string, and nothing needed replacing. — The product carries no vocabulary check that reads the setup instructions (`git grep "What the start prints" -- products/tracker17/tests` has no hit), so this search is the check.

---

## Findings for the Content Manager

- "A line that starts with `The tracker didn't start` means this start has stopped." — `products/tracker17/docs/CONTENT.md` § Terminology, the "killed" row, records "Stopped" as the setup instructions' word for Ctrl-C and gives no term for a start that ended by itself after a refusal. — Written with "stopped", because CP-741 and the request both use the word for this case and the phrase "this start" keeps it apart from a tracker the reader stopped with Ctrl-C.
