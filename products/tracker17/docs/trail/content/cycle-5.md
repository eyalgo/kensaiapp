# CONTENT open issues — tracker17

> Companion to `CONTENT.md`. The Content Manager authored the verbal language non-interactively;
> this file holds the calls it made and wants your sign-off on — each with the reason behind it,
> and what moves underneath it if you override — plus the few things it genuinely could not
> settle.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**,
> then re-run `product-content`. It folds your answers into `CONTENT.md` and drops the resolved
> items. When nothing is left open, `product-content` **deletes this file**: no file = the verbal
> language is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git refuses
> to remove a file with uncommitted edits in it — so an uncommitted answer stops that run before
> it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the Content Manager folds them in, it first copies
> this file whole to `docs/trail/content/` — so what you decided, and why, stays readable and
> citable for good.
>
> **§ 3 comes from outside this run.** The verbal language is read by everyone who writes a string,
> and a seat downstream can find a pattern it has no rule for. It is recorded there, answered here,
> and folded by the same run.

> **No `product-content` run wrote this file.** The PM opened it on 2026-10-07, reading the product's
> not-found page against the settled verbal language, with the two items in § 3.

---

## 1. Open issues

None.

## 2. Choices to confirm

None.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 "An address with nothing at it" has no form for a product with one place to go
- **Raised by:** PM — 2026-10-07
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_first-project`
- **What it blocks:** the not-found page has no pattern behind its second sentence. `CONTENT.md:225-230` gives the formula "one sentence that says there is no project or no task at this address, then the two places to go as links", with both examples ending "Open Projects or All tasks.". SDD § 4 EX-12 keeps All tasks off every page until its slice, so the page ships one place: `web/pages.py:209-210` reads "There's no project at this address" then "Open Projects.".
- **Where it shows:** `CONTENT.md` § Message patterns, "An address with nothing at it". Proposed: the formula names the places that exist, one or two, with "Open Projects." as the one-place form.
- **If a document has to be written:** none.
- **Answer:** Take the change, worded so that it names no build order. The formula's second part becomes: then a link to each place the tracker has to send the reader, named by its label, Projects first and All tasks after it. With two places the sentence is "Open Projects or All tasks." With one place it is "Open Projects." The two existing examples stand as the two-place form, and one example is added for the one-place form. The addition to the proposal is the ground and the wording. The Review Note rests on the rule this language already holds, "State only what the tracker established" (`CONTENT.md` § Voice): a sentence that tells the reader to open a place the tracker doesn't have is a claim it can't keep. That ground holds in every build and states no delivery order, which a definition document may not state (`<CORE>/doctrine/setup/setting_up_a_project.md` § The definition set never names the journey). So the formula carries no count and no "one or two". It follows the places the tracker has. The occurrence is `web/pages.py` line 210, `<p>Open <a href="{PROJECTS_ADDRESS}">Projects</a>.</p>`, which is the one-place form in the product now. Reasoning: `products/tracker17/docs/trail/content/self_answer-5.md`.

### 3.2 Whether two links with the same label and the same destination count as a repeated label
- **Raised by:** PM — 2026-10-07
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_first-project`
- **What it blocks:** a ruling on the not-found page's accessible names. `CONTENT.md:323-325` says "Where the same visible label appears more than once on a page, the accessible name adds the thing the control acts on". The not-found page holds two links labelled "Projects", both to `/`: the header's at `web/pages.py:53` and the message's at `web/pages.py:210`. Neither adds anything to its name.
- **Where it shows:** `CONTENT.md` § Accessibility, the rule on a control's accessible name. Proposed: the rule says whether two links with the same label and the same destination are a repeat; if they are not, it says so, and the page stands as built.
- **If a document has to be written:** none.
- **Answer:** Not a repeat. Add one sentence to the accessible-name rule in § Accessibility of text: links that share a label and open the same address share one name, and the added thing applies where controls act on different things. A link acts on its destination, so two links with the same label and the same address have nothing to tell apart. The not-found page stands as built. Both links read "Projects" and both open `/`, since `web/pages.py` sets `PROJECTS_ADDRESS = "/"` (line 23) and uses it at line 53, the header, and line 210, the message. Two links with the same label and different addresses stay barred by the rule already in that section, "Two links to different places never share their text." The ground is the rule's own purpose and the W3C's stated direction: "It is a best practice for links with the same destination to have consistent text" (https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context.html, re-read 2026-10-07). A rule that forced different names onto the same destination would pull against that sentence. Reasoning: `products/tracker17/docs/trail/content/self_answer-5.md`.
