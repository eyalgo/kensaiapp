# Change Text — the Your name messages show a name holding a curly brace as typed

**Date:** 2026-10-29
**Category:** bug
**Behaviour:** changing

---

## Text

### The saved, failed and refusal messages in Your name on the People page

Every string below is today's wording, unchanged (`change_spec.md` § Rules, CP-624, "The three
lines' wording"). What this change alters is only that `{name}` now always shows the name exactly as
the person typed it. A name holding `{` or `}` is shown with every brace in place, none added,
dropped, doubled or halved (CP-619, CP-621). `{name}` is the one variable part. The single quotes
around it belong to the string, not to the name (`CONTENT.md` § Localization, "The quotes around a
typed value belong to the string").

**Saved — the name was set**

> You set your name to '{name}'.

`{name}`: the name the person just saved, exactly as typed, such as `Sam`, `{x}`, `}` or `{{x}}`.

When the person sees it: they pressed Save with a name the tracker accepted and kept. Nothing more
is needed, and they can comment under that name.

**Failed — the tracker couldn't save the name, for a reason that is not a refusal**

> The tracker couldn't set your name to '{name}', and nothing was changed. What you typed is still in the form. Try again.

`{name}`: the name the person typed and tried to save, exactly as typed, braces included. The same
name is still in the field.

When the person sees it: they pressed Save and the save didn't happen. Their saved name, if any, is
as it was, and pressing Save again retries with what they typed.

**Refused — the name was blank**

> Your name can't be blank. Type a name.

No variable part.

When the person sees it: they pressed Save with nothing, or only spaces, in the field. Their saved
name is unchanged, including one holding a brace such as `{x}`, and they can type a name and press
Save.

**Refused — the name was longer than the limit**

> Your name can't be longer than 200 characters. Type a shorter one.

No variable part. The count is the product's fixed limit, so the string has one form.

When the person sees it: they pressed Save with more than 200 characters. Their saved name is
unchanged, including one holding a brace such as `{x}`, and the field shows that saved name again.

---

## Wording decisions

- All four strings are kept word for word as the product shows them today — CP-624 locks "the three
  lines' wording", and the design's Architect Review Notes say the `yes` verdict "authorizes no
  rewording". Each string was checked against `CONTENT.md` and already meets it. The saved line
  follows § Completed ("You set your name to 'Sam'."). The failed line follows § Error, failure ("The
  tracker couldn't…", nothing was changed, the form still holds the input, one action). The two
  refusals follow § Error, refusal (the reason, then one action, two sentences).
- The variable part is described as the name "exactly as typed, braces included" rather than left
  as a bare slot — the defect this change fixes is a name whose braces were read as part of the
  message. The description states the requirement the string has to keep (CP-619, CP-621) without
  naming how the name reaches the page.
- The two refusal strings are written out although they carry no name — the design's `Publishes
  text:` line names "refusal messages", and CP-623 requires them shown unchanged with a brace name
  already saved. Writing them here lets the Developer place all four lines from one source.
- No block is written for the no-name line ("No name is set. You need a name to comment.") or any
  other text in the section — the design's line names only the saved, failed and refusal messages,
  and the no-name line is unchanged (CP-624).
- Banned-word check, run by hand over the four strings against `CONTENT.md` § Terminology, "Banned
  in anything a person sees", and § Grammar and mechanics: no hit. No string uses error, failed,
  invalid, sorry, please, successfully, click, we or our, an exclamation mark, an em dash, a
  semicolon or an ellipsis. Every negative is contracted and every sentence is under 20 words. The
  product carries no vocabulary check of its own: its two tests matching "banned"
  (`tests/architecture/test_imports.py`, `BANNED_EVERYWHERE`, and `tests/architecture/test_reach.py`)
  check imports, not words.

---

## Findings for the Content Manager

- "You set your name to '{name}'." with a name such as `{value}` — `CONTENT.md` § Voice, "Limits the
  product holds", bans "an unsubstituted template slot (`<name>`, `{value}`, `%s`)" in any delivered
  string. Unlike § Grammar and mechanics, "Banned punctuation" ("These bans govern the tracker's own
  words. They don't reach a value the reader typed"), it does not say whether the ban reaches a value
  the reader typed. A saved name that is itself `{value}` is shown as typed and reads exactly like the
  banned slot. The standard does not state whether a typed value that looks like a slot is exempt —
  meanwhile the name is shown exactly as typed, following § Voice ("write the reader's typed words
  back exactly") and § Grammar and mechanics, "Quotes".
