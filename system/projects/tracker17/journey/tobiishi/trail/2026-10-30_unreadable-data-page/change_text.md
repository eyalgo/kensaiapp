# Change Text — a start on unreadable saved data serves one plain page

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing

---

## Text

This file holds the exact words `tracker17 · tobiishi · 2026-10-30_unreadable-data-page` publishes, for the Developer to place as written. `{location}` is the saved data's absolute path, the same path in every string. `{address}` is `http://<host>:<port>` with the host and port the tracker actually bound.

### The unreadable-data page

**The browser tab's title, at every address that shows the page**

> The saved data can't be read - tracker17

When the person sees it: they have opened any address of a tracker that couldn't read its saved data, and the title tells this page apart from every other.

**The product name at the top of the page, as plain text with no link**

> tracker17

When the person sees it: they know which product is speaking, and nothing here takes them anywhere.

**The page's one heading**

> The saved data can't be read

When the person sees it: they learn the fact first, before where the data is or what to do.

**The page's body**

> The tracker couldn't read its saved data, which is kept at {location}. Nothing in it was changed or overwritten. To start fresh on purpose, follow Setting saved data aside in the setup instructions.

When the person sees it: they know where the data is and that it is unchanged, and their way forward is a section of the setup instructions, because the page offers no control.

### The console line on an unreadable start

**The tracker couldn't read its saved data and now answers requests, written once as one line**

> The tracker couldn't read its saved data at {location}, and nothing in it was changed. Open {address} in your browser to read this on a page. To start fresh on purpose, follow Setting saved data aside in the setup instructions.

When the person sees it: they have just started the tracker, and they know why they won't get the Projects page, where the data is, and where the way forward is written.

### The setup instructions, section "Starting the tracker again"

**The paragraph on what a start reads, in place of "The tracker reads its saved data as it starts, so every project you created before it stopped is still listed."**

> The tracker reads its saved data as it starts. If it can read the data, every project you created before it stopped is still listed.

When the person sees it: they are about to start the tracker again and want to know what they will find.

**A new paragraph directly after that one, ending in a command block**

> If it can't read the data, the tracker starts anyway. It shows this one line in its terminal.

When the person sees it: they learn the second outcome of a start before they meet it.

**The new command block's one line, set as the refusal line in the same section is set**

> The tracker couldn't read its saved data at /Users/sam/copy/products/tracker17/data, and nothing in it was changed. Open http://127.0.0.1:8017 in your browser to read this on a page. To start fresh on purpose, follow Setting saved data aside in the setup instructions.

When the person sees it: they can match what their terminal prints against this line, with `/Users/sam/copy/products/tracker17/data` and the address written as literal examples.

**A new paragraph directly after that command block**

> Your own copy's location appears in place of `/Users/sam/copy/products/tracker17/data`. In your browser, every address shows one page that says the same thing. The page has no links and no controls. The start and the page change nothing in the saved data. The tracker keeps showing the page until you stop it, even if you repair the saved data.

When the person sees it: they know the page is expected, that it can't act on the data, and that only a new start reads the data again.

**The killed-tracker paragraph, in place of "A tracker that was killed doesn't prevent the next start. There's nothing to do first. Type the same commands, and the tracker reads its saved data as the killed tracker left it."**

> A tracker that was killed doesn't prevent the next start. There's nothing to do first. In a terminal at the top of your copy, type the same commands, `cd products/tracker17` and `python3 main.py`. The tracker reads its saved data as the killed tracker left it.

When the person sees it: their earlier tracker ended by force, and the commands they need stand in the sentence that asks for them.

### The setup instructions, section "Setting saved data aside"

**The section's opening paragraph, in place of "Setting saved data aside moves it out of the tracker's reach and deletes nothing, so the next start is empty. Do it to start fresh, or when the tracker didn't start because it couldn't read its saved data."**

> Setting saved data aside moves it out of the tracker's reach and deletes nothing, so the next start is empty. Do it to start fresh, or when the tracker couldn't read its saved data.

When the person sees it: they have followed the pointer from the page or the terminal, or they want to start fresh, and they learn what the step does.

**The no-saved-data sentence, in place of "If `mv` says there's no such file or directory instead, there was no saved data to set aside. If the new directory is empty, there was no saved data to set aside."**

> If `mv` says there's no such file or directory, or the new directory is empty, there was no saved data.

When the person sees it: they have run the commands and either result needs explaining, with one conclusion for both.

---

## Wording decisions

- **The console line carries its four required parts in three sentences.** CP-711 requires the unreadable fact with its location, the unchanged data, the address and the section. `docs/CONTENT.md` § Grammar and mechanics, "A message has at most three sentences", sets the limit. The first sentence joins two parts the way § Message patterns, Error, already does in "The tracker couldn't add 'Set up CI', and nothing was changed."
- **The address sentence says why to open the address, in "to read this on a page".** A bare "Open {address} in your browser" repeats the ready line, and CP-711 says this line is not the ready line. The added words also tell the reader not to expect the Projects page.
- **The console's pointer uses the page's sentence word for word.** The earlier terminal wording was "See Setting saved data aside in the setup instructions." Two wordings for one pointer read as two things.
- **The console says "changed" and the page says "changed or overwritten".** CP-716 pins the page's words. CP-711 asks the line to say nothing was changed, and the terminal example in `docs/CONTENT.md` § Terminal messages reads "Nothing in it was changed." Both claims hold under CP-725, so neither was moved to match the other.
- **The section's heading is written without quote marks in the page, the console line and the README.** `docs/CONTENT.md` § Terminology says a pointer "quotes its heading exactly", and its own page example carries no marks. CP-716 pins that form, so the console line follows it.
- **The published strings say "terminal" and "setup instructions" where the request says "console" and "README".** `docs/CONTENT.md` § Terminology fixes both terms and rejects the request's words.
- **The strings say "every address", and `GET /style.css` remains the one exception.** CP-719 keeps the stylesheet, which is not a page. On this reading the README's sentence holds for every page a reader meets, so it does not name the exception.
- **The README gains one sentence nobody asked for, "The tracker keeps showing the page until you stop it, even if you repair the saved data."** CP-724 creates that state, and a reader who repairs the file and reloads would otherwise think the repair did nothing.
- **"the same commands" gets its commands in its own sentence, and that sentence is split.** With the commands added, the earlier sentence ran to 22 words against the 20-word limit in `docs/CONTENT.md` § Grammar and mechanics. "In a terminal at the top of your copy" is added because `cd products/tracker17` works only from there.
- **The duplicated conclusion becomes one sentence, dropping "instead" and "to set aside".** Keeping both phrases gives 24 words against the same limit. The new sentence keeps both of CP-734's conditions and is exactly 20 words.
- **Two README passages stay as they are because they remain true.** "Stop the tracker first if it's running" covers a tracker showing the page. The second-tracker paragraph and its line hold under CP-713.
- **"What the start prints" stays unchanged, and it does not describe the new line.** The design's `Publishes text:` line names only the two sections above, and CP-734 limits the change to them. Its sentences stay true, but a reader of that section alone meets no mention of the new line, so a later change should add one.
- **These states have no new words.** The empty 403 and the empty 303 carry none, under CP-720 and CP-721. Ctrl-C writes nothing, under CP-712. A second start keeps the CP-693 line. A held address keeps today's address-taken line, under CP-714.
- **The banned-word check found nothing to replace.** Every string was searched against the banned table in `docs/CONTENT.md` § Terminology and against the banned punctuation in § Grammar and mechanics. The one hit is "left" in the README's existing "as the killed tracker left it", a verb and not the position word the table bans. The product carries no check that enforces its vocabulary: its tests' only "banned" and "vocabulary" matches concern imports and closed sets of page modes, under `tests/architecture/` and `tests/integration/`.

---

## Findings for the Content Manager

- The console line in this file — `docs/CONTENT.md` § Terminal messages has no pattern for a start that serves on saved data it can't read, because its formula covers only "A start that fails". Its third example, "The tracker didn't start, because it couldn't read its saved data at …", goes false with this change — The line was written from § Tone, the row "Saved data that can't be read", and from CP-711. `tracker17 · tobiishi · 2026-10-30_unreadable-data-page` already parks the same gap in its `deferred_decisions.md`.
- "follow Setting saved data aside in the setup instructions" — `docs/CONTENT.md` § Terminology says a string "quotes its heading exactly" and does not say whether that means quote marks, while its examples carry none — The string was written without marks, following the page example CP-716 pins.
