# 上がり Agari — tracker17's "done"

*The **project**-level declaration: this project's **Agari** — the terminus that defines when the
product is done, set by the CPO. A **declaration**, not a queue. A project has **no Michi** (it serves
the instance's Way — `system/michi.md`). `project-stamp` stamps this into
`system/projects/tracker17/agari.md`. Upkeep that outlives done, such as a re-check on a cadence or a
correction when the world changes, does not keep the project open. It moves to the instance's upkeep
register, `system/upkeep.md` (`<CORE>/doctrine/setup/kensaiapp_structure.md` § App-level).*

---

tracker17 is done when **the owner can use it locally, easily, by themselves** — the owner's answer,
2026-10-05 (`system/projects/tracker17/trail/agari/cycle-1.md` § 1.1, "I can use it locally easily by
myself"). The owner shows that by passing, on one run-through, the three bars that
`products/tracker17/docs/PRD.md` § Success Metrics says are "checked before the product is called
done". All three bars, the third included, were confirmed in
`system/projects/tracker17/trail/agari/cycle-2.md` § 2.1, with the reasoning in
`system/projects/tracker17/trail/agari/self_answer-1.md`.

**Reached when** all three bars pass:

1. **Works.** The owner runs through Key Use Cases 3, 4 and 5 in the browser with no error and no
   wrong result, and the full automated suite passes with its unit, integration and end-to-end layers
   all present (`products/tracker17/docs/PRD.md` § Success Metrics, **Works**).
2. **Simple to set up.** Starting from a fresh copy, on a machine with only the stated prerequisites,
   the owner follows only the written setup instructions. They reach the tracker open in their browser
   in no more than three commands and within ten minutes, and nothing asks for an account, a key or a
   sign-up (`products/tracker17/docs/PRD.md` § Success Metrics, **Simple to set up**).
3. **Simple to read.** The owner reads the code cold and judges it simple. They also trace one Core
   Feature, picked at the time of the check, from the product definition to its code and its tests,
   by following what the documents and the code point to. Both are the owner's pass/fail calls
   (`products/tracker17/docs/PRD.md` § Success Metrics, **Simple to read**).

   This bar is part of the owner's own use, not a check for some other reader. In the project-setup
   interview the owner said there is "no SIMPLE example of a kensaiapp product", and that what they will
   do with it is "Look at the code, see if it works, and see if it's simple to set up on a machine"
   (`products/tracker17/docs/trail/prd/cycle-1.md` § 1.3 and § 1.4). The owner also runs this bar alone,
   on their own machine, because the PRD makes them the only reader until they publish
   (`products/tracker17/docs/PRD.md` § Assumptions). That fits "by myself". The trace half came into the
   PRD through a later round (`products/tracker17/docs/trail/prd/cycle-4.md` § 2.1). It is part of the
   settled PRD, so dropping it would mean revising the PRD, not this Agari.

**What this Agari does not require.** It does not require tracker17 to be published or tried by an
outside reader. On this reading the owner's answer says "by myself", and
`products/tracker17/docs/PRD.md` § Assumptions says tracker17 "stays that way until the owner decides
to publish it" and that "until then the owner is the only reader". Publishing is the owner's later
decision, and it does not hold this project open. The PRD's re-check of the bars "again on every later
release" (`products/tracker17/docs/PRD.md` § Success Metrics) is upkeep after done, not a condition of
it.
