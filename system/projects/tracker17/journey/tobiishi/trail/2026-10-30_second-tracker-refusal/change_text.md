# Change Text — a second tracker on the same saved data is refused

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing

---

## Text

### The terminal's second-start refusal

**A start on saved data another running tracker is using**

> The tracker didn't start, because another tracker is already running on the same saved data. Stop that one first, then start this one.

When the person sees it: they typed the start command and it ended with this one line. They know the first tracker is still running, and they can stop it and start again.

### The setup instructions

**A second start while another tracker is running, at the end of the section "Starting the tracker again"**

> If another tracker is already running on the same saved data, a second start is refused. It shows this one line in its terminal and exits.
>
> ```
> The tracker didn't start, because another tracker is already running on the same saved data. Stop that one first, then start this one.
> ```
>
> The first tracker carries on, and the refused start changes nothing in the saved data. To stop the first tracker, press Ctrl-C in its terminal.

When the person sees it: they saw the refusal, or want to know what a second start does. They learn that the first tracker is unharmed and how to stop it.

**A start after a tracker was killed, directly after the passage above in the same section**

> A tracker that was killed doesn't prevent the next start. There's nothing to do first. Type the same commands, and the tracker reads its saved data as the killed tracker left it.

When the person sees it: a tracker ended without Ctrl-C and they are unsure whether anything must be undone. They learn that nothing must be, and they start the tracker the usual way.

**An empty saved-data directory set aside, in the section "Setting saved data aside", directly after the sentence that begins "If `mv` says"**

> If the new directory is empty, there was no saved data to set aside.

When the person sees it: they set aside saved data from a tracker that saved nothing, `mv` reported no problem, and the new directory holds no file. They learn that nothing went missing.

---

## Wording decisions

- The terminal line is `CONTENT.md` § Message patterns, Terminal messages, word for word — `change_spec.md` CP-693 pins it, so the request's "using that location" is not used.
- "Saved data" replaces the request's "location" in the setup instructions passage — `CONTENT.md` § Terminology fixes "saved data", and the refusal line in the same passage already says it.
- Added the "new directory is empty" sentence, a state nobody wrote a message for — CP-703 lets an empty saved-data directory remain after a tracker that saved nothing stops, so `mv` now succeeds where it used to report no such file. The existing "Your saved data is in a new directory" would then leave the reader looking for a file that never existed.
- Added "To stop the first tracker, press Ctrl-C in its terminal." — the refusal says to stop the other tracker and the passage is where the reader looks for how. The words repeat the setup instructions' own stopping step in "What the start prints".
- Wrote no "only one tracker can run" sentence — CP-702 lets a start proceed where the check can't be made, such as a file system that offers no lock, so the tracker doesn't make that guarantee.
- "The refused start changes nothing in the saved data" replaces "the saved data's bytes stay as they were" — the first tracker carries on and may save, so the smaller true claim is about the refused start.
- "Doesn't prevent the next start" replaces the request's "a start after a kill succeeds" — a later start can still stop for unreadable saved data or a taken address, under CP-700 and CP-701.
- "There's nothing to do first" replaces the design's "without clearing a lock" — the lock is a mechanism the reader never handles, and `CONTENT.md` § Terminology rejects "clear" for saved data.
- The refusal line is kept for the moment when the other start holds the saved data and hasn't reached its ready line — CP-698 gives that start the same line, and `CONTENT.md` fixes one line for the case. If the other start then fails, starting again succeeds, so the action in the line still leads somewhere.
- Wrote no string for a start after a kill or Ctrl-C, or for a start where the check can't be made — CP-699 and CP-702 keep today's ready, unreadable and address lines, and CP-699 forbids a message about the earlier tracker.
- The banned-word scan hit "left" and "no" and neither was rewritten — `CONTENT.md` § Terminology bans "left" as a position and "No" as a control label, and here they mean "as it left it" and "no saved data". The product carries no vocabulary check to run.

---

## Findings for the Content Manager

- "A tracker that was killed doesn't prevent the next start." — `CONTENT.md` § Terminology has no term for a tracker ended by a kill it can't handle — written with "killed", the word `change_spec.md` CP-708 uses.
