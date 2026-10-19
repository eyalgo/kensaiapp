<!-- Template-file metadata is stamped by the merge, never on a change branch; this file carries none. -->

# Change Text — <title>

**Date:** YYYY-MM-DD
**Category:** <copied from change_spec.md>
**Behaviour:** <copied from change_spec.md>

<!-- The three header lines are copied, never re-derived: this skill classifies nothing. -->

---

## Text

<!-- One block per place the design's `Publishes text:` line names, in the order the line names them.
Under each place, one string per state a person can meet there. Each string is written verbatim, in
the exact characters the person reads, so the Developer places it without choosing a word. Name the
place as the person knows it (the page, the dialog, the message), never as an identifier or a file.
Write a string that needs a variable part with the variable marked in braces and described in the line
under it; never as a fragment that a runtime joins to another. -->

### <place, as the person knows it>

**<state this string is shown in>**

> <the string, verbatim>

When the person sees it: <one line — what they know at this moment and what they can do next>

**<next state>**

> <the string, verbatim>

When the person sees it: <one line>

---

## Wording decisions

<!-- Each improvement over the request's own phrasing, with its reason: a state the change creates
that nobody wrote a message for, two strings for one concept collapsed into one, a message that
claimed a cause the system cannot establish replaced by the smaller true thing, a sentence assembled
from fragments taken apart, a banned word replaced with the standard's own. Also each place where the standard left a choice and the run made it, and
why it was safe to make. Write `None` when the strings follow the request unchanged. -->

- <the decision> — <the reason>

---

## Findings for the Content Manager

<!-- Each rule the standard does not state that a string here needed. Name the string, name the rule
that is missing, and say how the string was written in the meantime. Write `None` when the standard
answered every string. A finding is never written into CONTENT.md or the writing bar from here. -->

- <the string> — <the rule the standard does not state> — <how it was written meanwhile>
