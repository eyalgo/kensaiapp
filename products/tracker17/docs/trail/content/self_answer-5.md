# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-07
- **Sources re-read:** Two W3C pages, both read on 2026-10-07. `https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context.html` says "It is a best practice for links with the same destination to have consistent text (and this is a requirement per Success Criterion 3.2.4 Consistent Identification for pages in a set)", and SC 2.4.4 is Level A. `https://www.w3.org/WAI/WCAG22/Understanding/consistent-identification.html` says SC 3.2.4 is Level AA and requires that "Components that have the same functionality within a set of web pages are identified consistently". Only the first sentence quoted from the first page is relied on, for item 3.2. Everything else this run leans on was read in this repository on 2026-10-07.

## Items worked

### 3.1 — "An address with nothing at it" has no form for a product with one place to go

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** confirmed with addition
- **Why:** The change is taken, with a different ground and different wording from the proposal. The formula follows the places the tracker has to send the reader, with "Open Projects." as the one-place sentence. It carries no count and no "one or two".

  *Seat.* The item is `CONTENT.md`'s. The edit lands in one message pattern of this document, binds no person and no outside party, and I could name no ground the owner holds that I can't see. It is one question, so it does not split.

  *The widening bar.* The item widens the document, because the formula states two places and the item asks it to state a case with one. The prompt answers such an item "not until it occurs" unless it cites an occurrence (`prompts/rich.md` § A widening item waits until it occurs). This one cites one: `web/pages.py` line 210, which I re-read, reads `<p>Open <a href="{PROJECTS_ADDRESS}">Projects</a>.</p>`. That is a site in the product as it stands now, so the form is taken.

  *Where the proposal needed an addition.* The proposal names the places "that exist, one or two". The reason the item gives for there being one is SDD § 4 EX-12, a delivery rule about which areas a page shows before the slice that delivers them. A definition document does not state when a thing is built (`<CORE>/doctrine/setup/setting_up_a_project.md` § The definition set never names the journey), and the upstream documents describe the finished product with all three areas (`UXD.md` § 4, "Three top-level areas"; `DESIGN.md` § Layout, Header, "the three nav links"). A rule written as "one or two" would encode a build order in a standing document, and the one-place form would then sit unused once every area is there. The ground that holds in every build is already in this document: a string states "only what the tracker established" (§ Voice, the third row of the first table). A sentence that sends the reader to a place the tracker doesn't have claims what it can't keep. Worded as "each place the tracker has", the formula needs no edit when All tasks arrives.

  *Failure paths.* Empty: no build has zero places, because Projects is the home page (`UXD.md` § 4) and the page for unreadable saved data replaces every page, not-found included (`UXD.md` § 4, "One page replaces all of them"). Absent and stale: an area the tracker gains later is covered by the same wording, which is the point of dropping the count. Concurrent and refused: not reached, since the pattern words a page and takes no action. Not covered: People is not a place this sentence offers, because UX-S10 names Projects and All tasks only (`UXD.md` UX-S10, "links to Projects and All tasks"). That holds until the UXD says otherwise.

  *Seen and not raised.* The page's own heading says "There's no project at this address" for every address, and `not_found_page` takes no argument so it can't say "task" (`web/pages.py` docstring, "the same for every address, showing none"). The formula already reads "no project or no task", so the standard is met by the page saying the smaller of the two. Nothing in the document is false, so nothing is raised.

  *Close call.* I considered plain confirm of "one or two". What tipped it to an addition is that the proposal's ground is a delivery rule the document may not state.

### 3.2 — Whether two links with the same label and the same destination count as a repeated label

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** answered
- **Why:** Not a repeat. Links that share a label and open the same address share one name, and the rule adds "the thing the control acts on" only where controls act on different things. The not-found page stands as built.

  *Seat.* The item is `CONTENT.md`'s: stating the accessibility bar for text is this seat's job (`<CORE>/roles/loaders/content_manager_global.md` § Responsibilities, item 5). It binds no person and no outside party, and I could name no ground I can't see. The proposal states a question and a conditional, with no answer drafted, so the item is answered from scratch.

  *The widening bar.* The item asks the rule to state a case it doesn't state, and it cites occurrences: `web/pages.py` line 53, `<a href="{PROJECTS_ADDRESS}">Projects</a>` in the header, and line 210, the same in the message. I re-read both, and line 23 sets `PROJECTS_ADDRESS = "/"`, so both open `/`. Two links with one label and one destination are on the page today, so the case is taken.

  *Why it is not a repeat.* The rule at `CONTENT.md` § Accessibility of text ("Where the same visible label appears more than once on a page, the accessible name adds the thing the control acts on") exists so a reader can tell two controls apart by what they act on. A link acts on its destination. Two links to one address have nothing to tell apart, and adding a word to either would give the same place two names. The link rule in the same section already bars the opposite case, "Two links to different places never share their text." Together the two read as one rule: one label per place, and one place per label.

  *The source, re-read.* The W3C Understanding page for SC 2.4.4 says "It is a best practice for links with the same destination to have consistent text" (https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context.html, 2026-10-07). A rule forcing different names onto the same destination would run against that direction. I relied on that one sentence only. I did not rely on a reading of SC 3.2.4 as requiring identical text, because its own Understanding page says "consistent identification does not require identical labels", so the answer doesn't depend on it.

  *Failure paths.* Empty: a page with one link to an address has no repeat. Stale: the header's links and the message's links change as areas arrive, and the rule is stated on label and address together, so it needs no edit. Concurrent: not reached. Refused: not reached. Not covered: a button and a link with one label are different controls and the rule's "thing it acts on" still separates them. Same label with the same path but a different filter in the address is a different address, so it is not covered by the exemption.

  *Decided together with 3.1.* After 3.1 the not-found page's message link and the header's link are the same pair in every build, with one place or two, so the two answers had to agree. They do: 3.1 words the sentence by what the tracker has, and this one says the pair needs no extra name.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
