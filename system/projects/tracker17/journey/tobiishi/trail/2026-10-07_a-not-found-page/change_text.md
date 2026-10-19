# Change Text — A not-found page for an address with no project

**Date:** 2026-10-07
**Category:** feature
**Behaviour:** changing

---

## Text

The not-found page is the same for every address it answers, so each place below has one state:
the person opened an address the tracker has nothing at. The page shows no part of that address,
so no string carries a variable part.

### The not-found page's message

**The person opened an address the tracker has nothing at**

> There's no project at this address

When the person sees it: they followed or typed an address and got this instead of a project's page. They know only that nothing is there, and the line under it gives them the way back.

This string is the page's heading. It ends with no full stop.

### The not-found page's link to Projects

**The person opened an address the tracker has nothing at**

> Open Projects.

When the person sees it: right under the message, as the one thing to do next. Opening the link takes them to the Projects page.

This is one string. Only the word `Projects` is the link's text. `Open`, the space before `Projects` and the full stop after it are not part of the link. The link's accessible name is its visible text, `Projects`, with nothing added.

### The not-found page's title

**The person opened an address the tracker has nothing at**

> Not found - tracker17

When the person sees it: in the browser tab and in a screen reader's page announcement, before the message is read.

The separator is a space, a hyphen-minus and a space, as in every other page title the tracker shows.

---

## Wording decisions

- The message says "There's no project at this address" for every address the page answers, a wrong address such as `/nowhere` included. The request said the page "says the project does not exist". — The tracker can't tell whether a project was deleted or the address was mistyped. CONTENT RN-11 and its banned-words row ("deleted or gone, to explain a missing page") call for the smaller true thing, and "no project at this address" is true at every address the spec's CP-30 and CP-31 cover. One string serves both cases because the page is identical for all of them (CP-33).
- The message has no full stop. CONTENT's example, "There's no project at this address.", has one. — The design puts the message in the page's heading (DESIGN § Typography, "the UX-S9 and UX-S10 messages"). CONTENT § Grammar and mechanics, *Sentence endings*, gives headings no end punctuation, and the standard's own UX-S9 heading, "The saved data can't be read", is a whole sentence written without one.
- The line after the message reads "Open Projects." and not "Open Projects or All tasks.", which is CONTENT's example. — All tasks doesn't exist yet. The spec's CP-33 and CP-34 drop it from the page, and offering a link to an area that doesn't exist would point the reader at nothing. A finding below records that the formula has no one-place form.
- Only "Projects" is the link's text. — CONTENT § Accessibility of text says link text "names the destination and nothing else", and "Projects" is the name the header link and the Projects page's own heading already use for that place. The verb "Open" is CONTENT's verb for a link (§ Grammar and mechanics, *Verbs for pressing*).
- The message's link gets no longer accessible name, even though the header's link also reads "Projects". — Both links go to the same page, so nothing needs to tell them apart. CONTENT's rule for a repeated label has the accessible name add "the thing the control acts on". A link acts on nothing, and both links lead to the same place. A finding below asks the Content Manager to settle the case.
- The title is CONTENT's own example, "Not found - tracker17", word for word. — CONTENT § Accessibility of text, *Every page has a title that names its subject*, lists it among its examples, and the spec's CP-33 names it as the title.
- Each string was checked against CONTENT's banned words and banned punctuation in every inflection, and against the page tests' forbidden words ("all tasks", "people", "rename", "delete"). None is used. The design's test that the page's main area holds no "task" also holds, because neither on-page string contains the word.

---

## Findings for the Content Manager

- "Open Projects." — The pattern for an address with nothing at it ("then the two places to go as links") has no form for a product whose All tasks area doesn't exist yet. Its examples all end "Open Projects or All tasks." — Written meanwhile as the pattern's second sentence without its second place, as the spec's CP-33 requires. When All tasks ships, this string needs another look.
- "Open Projects." with the header's "Projects" link on the same page — § Accessibility of text says that where the same visible label appears more than once, "the accessible name adds the thing the control acts on". It doesn't say whether two links with the same text and the same destination count as a repeat. — Written meanwhile with no added accessible name, because the two links aren't different things for a reader to tell apart.
