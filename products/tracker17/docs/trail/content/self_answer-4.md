# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-07
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Every claim it leans on was re-read in `CONTENT.md`, `web/pages.py`, `web/routes.py`, `main.py` and git history on 2026-10-07.

## Items worked

### 2.1 — RN-16 says tracker17 has no code yet, and the product now has pages with strings in them

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed with addition
- **Why:** The change is taken: RN-16 stops saying the product has no strings and no code. One addition is made. The proposal names `web/pages.py` as where the strings are, and that is narrower than the facts. The slot says so, for the next `product-content` run to fold.

  *Seat.* The item is `CONTENT.md`'s. The edit lands in one Review Note of this document, binds no person and no outside party, and I could name no ground the owner holds that I cannot see. It is one question, so it does not split. It is a correction, not a widening: it fixes a statement that is false now.

  *The draft is sound, and I re-measured it.* `CONTENT.md:493` says "tracker17 has no strings of its own, because it has no code yet", word for word as the item quotes it. `web/pages.py:63` returns "A project needs a name. Type one." and is committed (`5f1f13d81`, 2026-10-07). `CONTENT.md` was settled in `f60f6a6de` on 2026-10-06, so the strings were written after the rules. The item rests on a fact that is false, which is the prompt's strongest ground in § The items are not the whole of what a document is owed. It also matters beyond the note: the product-content prompt makes the product's own strings the evidence that binds where it exists (`product-content/prompts/rich.md` § The corpus test), so a document that tells its reader no corpus exists points that reader away from it.

  *The addition: the strings are in three places, not one.* `web/pages.py` writes the pages. `web/routes.py:210` writes the terminal line printed when an action fails ("The tracker couldn't create '{name}', and nothing was changed."). `main.py:41` and `main.py:50` write the terminal's failed-start line and its ready line. All three were committed on 2026-10-07 (`5f1f13d81`, `0a015872b`, `63b4da736`). `CONTENT.md` § Scope puts the terminal text in the language (`CONTENT.md:25-27`), so a RN-16 that named only `web/pages.py` would tell the next reader the terminal has no corpus. That is the same kind of false statement the item corrects.

  *Failure paths.* Stale: code moves faster than documents, so RN-16 says where the strings are as of this revision and does not promise a file stays put. Absent: the written setup instructions are not covered. I did not read them, so RN-16 should claim no more than the three files measured. Empty, refused and concurrent: not reached, since the note records evidence and no action.

  *Two other lines that say "no corpus", and why they stand.* `CONTENT.md:434` (RN-2) and `CONTENT.md:491` (RN-15) give "no corpus" as the reason a call was made. Those calls were made on 2026-10-06 when none existed, and the owner confirmed them then (`trail/content/cycle-1.md` § 2.1). RN-15 says "has" in the present tense, so a cold reader could take it as current. The fix is one sentence in RN-16 that says those two notes record the position when the calls were made. That keeps the edit in one note and does not rewrite two others.

  *Not claimed.* RN-16 must not say whether the strings meet the rules. That is a Content Editor run on a change that publishes text, or an audit. This was already the item's own limit and I kept it.

  *Close call.* I considered plain confirm. What tipped it to an addition is the terminal text: the item's grounds name one file, and the proposed note would then be false about the other two.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
