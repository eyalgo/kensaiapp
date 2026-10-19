# Self-answer report — PRD.md

## Header

- **Companion:** products/tracker17/docs/PRD_open_issues.md
- **Document:** products/tracker17/docs/PRD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-05
- **Sources re-read:** None. The one answer this run gave rests on statements inside
  `products/tracker17/docs/PRD.md` and its trail, and on no source outside this repository. § Why This
  rests its claim that tracker16-X "can't show that trace" on tracker16-X's `docs/fdr.md`. The answer
  below does not lean on that claim: Key Use Case 2 contains the trace whether or not tracker16-X can
  show one, so the bar is owed either way.

## Items worked

### 2.1 — Key Use Case 2's trace — following one feature from the PRD to its code and tests — has no success bar

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft is confirmed: **Simple to read** gains one sentence that checks the trace. Two
  additions close cases the draft leaves open.

  **Check 1 — this item is this run's to answer.** The edit lands in `products/tracker17/docs/PRD.md`
  § Success Metrics, the document being answered. The answer commits the owner to one more check when
  they run the bar. It commits nobody outside, no money and no risk anyone carries. The owner reserved
  one call in this bar: the code is judged simple by them, "a pass/fail call by the owner, and no line
  count stands in for it" (`products/tracker17/docs/PRD.md` § Success Metrics, "Simple to read"). The
  answer does not move that call. It adds a check on whether the trace exists, not on how simple it
  reads. I can name no ground I cannot see. The trace entered Key Use Case 2 as the CPO's addition, and
  the owner's own answers do not mention it (`products/tracker17/docs/trail/prd/cycle-1.md` § 1.2,
  "Someone who is interested in seeing how kensaiapp builds apps", and § 1.4, "Look at the code, see if
  it works, and see if it's simple to set up on a machine"). Keeping the trace in Key Use Case 2 is
  settled by `products/tracker17/docs/trail/prd/cycle-2.md` § 2.10. That answer, "Keep Key Use Case 2,
  because 'how kensaiapp builds apps' (answer 1.2) is that trace", is a prior self-answer, and it binds
  this run. Given that settled trace, a bar for it is a question of the document's own consistency.

  **Check 2 — the draft holds for the reason it gives.** § Success Metrics says "Each bar names the Key
  Use Cases it checks, and together they cover all five". **Simple to read** names Key Use Case 2 and
  checks only "the owner reads the code cold and judges it simple". Key Use Case 2 also says the reader
  "follows one feature from the product definition to where it is built and where it is tested", and no
  bar checks that part. § Why This names the trace as "What tracker17 adds". So the cover-all-five
  sentence is false for half of Key Use Case 2, and the half left out is the product's stated edge. The
  lean of one sentence in the existing bar rather than a fourth bar also holds. **Simple to read**
  already names Key Use Case 2, and following a feature from its definition to its code is part of the
  reading that use case describes. A fourth bar would also make "All three bars are checked" in the same
  section false and need a second edit. I was close to preferring a fourth bar, so that the label
  "Simple to read" would not have to carry a check on whether the trace exists. What kept me on one
  sentence is that each bar is named for the use cases it checks, and Key Use Case 2 is one use case.

  **One supporting-text error, reported and not corrected.** The item's draft line says "The bar is one
  you confirmed (`trail/prd/cycle-2.md` § 2.4)". That slot ends "Reasoning in
  `docs/trail/prd/self_answer-1.md`", so the confirm was a self-answer run's, given in the owner's seat,
  and not the owner's own. The answer here does not depend on who confirmed it. The CPO may correct the
  wording on its fold.

  **Check 3 — no contradiction.** The addition keeps the bar a pass/fail call by the owner, as § Success
  Metrics requires. It keeps "All three bars" and "they cover all five" true, and it makes the second one
  true for the first time. It agrees with § Core Features, "Tested throughout": the tests are "part of
  what the reader comes to read", and the trace ends in them. The bullet in § Open Questions, "whether
  the **Simple to read** bar also checks Key Use Case 2's trace", is answered by this item and drops on
  the fold. `system/projects/tracker17/agari.md` is still a placeholder and states nothing to agree
  with. Item 2.1 is the only item in this companion, so no earlier answer of this run bears on it.

  **Check 4 — the two additions.**
  1. **Who picks the feature, and when.** The draft says "the owner picks one Core Feature" and does not
     say when. If the feature can be chosen in advance, the product can pass by making one feature trace
     cleanly while the rest do not. That would be a bar rewarding a showcase over a followable product.
     Key Use Case 2 has a reader follow "one feature", and the reader chooses which. So the owner picks
     at check time, and any Core Feature the operator uses can be picked. That excludes
     **Tested throughout**, which is a property of every feature, not a feature the operator uses.
  2. **What "without searching the whole codebase" means.** As drafted, searching part of the codebase
     would pass. On this reading the intended test is that the trace is followable. The owner reaches
     the code and its tests by following what the definition documents and the code point to, not by
     searching for them.

  The other failure paths are covered by the draft and the bar as they stand. **Absent:** if a
  definition document, the code or the tests for the chosen feature are missing, the trace breaks and
  the bar fails. That is the signal the bar exists to give. **Stale:** if a document points at code
  that has since moved, the trace breaks on the next release. § Success Metrics already re-checks every
  bar "again on every later release", so the break is caught there. **Refused:** a trace the owner
  cannot follow fails the bar, and the product is not called done, the same as for the other bars.
  **Empty and concurrent** do not arise for a check one person runs once on a built product.

## Left for the owner

None this run.

## Skipped

- **§ 1, § 3, § 4** — each says "None." and holds no item.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/PRD.md** — `<CORE>/launchers/skill/launcher.sh product-prd tracker17`
