# Self-answer report — agari.md

## Header

- **Companion:** system/projects/tracker17/agari_open_issues.md
- **Document:** system/projects/tracker17/agari.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-05
- **Sources re-read:** None. The answer rests only on files in this repository: the PRD, its trail, and
  the Agari's own trail.

## Items worked

### 2.1 — Done also needs the Simple to read bar, not only your own use of the tracker

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft's conclusion holds: tracker17 is done when all three bars in
  `products/tracker17/docs/PRD.md` § Success Metrics pass. Its argument does not fully hold, so the
  real reason is added.

  *Check 1 — whose call.* Answering it binds only the Agari's agreement with the settled PRD. No person,
  money or outside party is bound by it. I could name no ground I cannot see. The owner's intent behind
  "by myself" is readable, and § Check 2 reads it. On this reading the call is the owner's seat, and the
  run sits in it. I was close to *left for the owner*, because the draft says "Whether 'done' stretches
  past your own answer is your call". A recorded owner statement that "done" means using the tracker
  and not reading its code would have tipped it there. None exists.

  *Check 2 — is the draft sound.* The draft says the third bar checks "something else", namely the outside
  reader, and that the owner "did not write that sentence yourself". That understates the owner's own
  record. In the project-setup interview the owner answered "There's no SIMPLE example of a kensaiapp
  product" (`products/tracker17/docs/trail/prd/cycle-1.md` § 1.3) and "Look at the code, see if it
  works, and see if it's simple to set up on a machine" (same file, § 1.4). So reading the code for
  simplicity is the owner's own use case. Also, the read bar is run by the owner alone, on the owner's
  machine. The PRD says "Until then the owner is the only reader" (`products/tracker17/docs/PRD.md`
  § Assumptions), and the bar is "a pass/fail call by the owner" (§ Success Metrics, **Simple to
  read**). Condition 3 therefore fits "I can use it locally easily by myself"
  (`system/projects/tracker17/trail/agari/cycle-1.md` § 1.1). It does not widen that answer to an
  outside reader. The Agari already excludes outside readers under "What this Agari does not require".
  The draft's reasoning holds for one part. The trace half of the bar was added by self-answer runs and
  not by the owner: `products/tracker17/docs/trail/prd/cycle-2.md` § 2.10 kept the trace in Key Use
  Case 2, and `products/tracker17/docs/trail/prd/cycle-4.md` § 2.1 put it into the bar.

  *Check 3 — the settled record.* An override would leave the Agari contradicting the settled PRD
  (`**Status:** Settled`, `products/tracker17/docs/PRD.md`). § Success Metrics says "All three bars are
  checked before the product is called done". The draft's own "If overridden" field says this too.
  An answer that needs a settled document to move is a change to that document, so dropping the trace
  half would be a `product-prd` item, not an Agari item. Confirming agrees with the PRD and with the
  Agari's own text.

  *Check 4 — failure paths.* **Refused:** the owner reads the code and judges it not simple. The Agari is
  then not reached and the work continues. That is the PRD's named risk, "A browser app may be less
  simple than the terminal tool it follows" (§ Risks), and the bar is what catches it. **Absent:** a
  definition document on the trace path is missing. The trace then fails, because it must be followed
  "never by searching" (§ Success Metrics). The project's definition is `full`
  (`system/projects/tracker17/project.md`, `**Definition:** full`), so those documents are expected to
  exist by the time of the check. **Stale:** the bars are re-checked "again on every later release"
  (§ Success Metrics). The Agari already treats that re-check as upkeep after done. **Empty** and
  **concurrent** do not apply. The check happens once on a built product, by one person.

  *The addition.* When `project-agari` folds this answer, the Agari should give the owner's interview
  answers as the reason for condition 3, citing `products/tracker17/docs/trail/prd/cycle-1.md` § 1.3
  and § 1.4. It should not describe the bar as one only a self-answer run put there. The fold also
  drops the line "The inclusion of the third bar is awaiting the owner's confirmation"
  (`system/projects/tracker17/agari.md`), because this answer settles that question.

  *Reported, not corrected.* The item's rationale says "You did not write that sentence yourself". That
  is true of the PRD's exact sentence. It is incomplete as a claim about where the read bar came from,
  for the reason given under check 2. Correcting the item's text is `project-agari`'s job, not this
  run's.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **system/projects/tracker17/agari.md** — `<CORE>/launchers/skill/launcher.sh project-agari tracker17`
