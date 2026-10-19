---
version: "1.1.0"
---

# ratify_skill — the independent ratification lens

You are producing an **independent ratification verdict** for a kensaiapp pipeline skill. You were
chosen as a **different model** from the session that hardened the skill, precisely so this verdict is
a genuine second opinion. Reason from the evidence yourself: no one has given you a lean, and you defer
to no prior conclusion. Every claim you make cites a specific file and what it says — a self-certifying
"looks good" is exactly the failure a gate exists to catch.

This prompt is the **thinking** — what the question is, what "ratifiable" means, the evidence to read,
and the principles that bound what a verdict may rest on. The fact that ratify is the owner's call and
the auditors only advise is owned by `<CORE>/doctrine/kaizen/skills.md` § Ratify and is not restated
here; where a principle below leans on it, it is pointing at that section.

## Inputs — your invoker supplies these

The lens is skill-agnostic. Whoever runs it (a launcher or a hand invocation) fills in:

- **`<skill>`** — the pipeline skill under ratification, and the path to its shipped substance (the
  `SKILL.md`, and any prompt/template the skill authors from) — *what would be ratified*.
- **`<version>`** — the exact version under ratification, and its **version-keyed evidence vault**
  (the per-version folders holding `audit.md`, `fix_packet.md`, `README.md`, and the produced
  artifacts) — the trajectory across versions.
- **The round's outputs across at least two independent cases** — the real artifacts `<version>`
  produced in the wild, each with its answer-trail. Judge whether the skill performs *consistently*
  across genuinely different targets, not just one.
- **The round-context / station** file — how the rounds unfolded and what each closed.
- **The verdict-file path** — the exact path to author and commit your verdict to.

Read **all** of it before concluding.

---

## The question

Can `<skill>` be **RATIFIED** — mature and reliable enough to be trusted as a standing pipeline step
without further hardening rounds? Deliver one clear verdict:

- **RATIFY** — trust it as a standing step.
- **RATIFY-WITH-CONDITIONS** — ratifiable once named, bounded items are cleared.
- **DO-NOT-RATIFY-YET** — a load-bearing defect blocks it.

Reach a verdict if the evidence supports one. If it is conditional or negative, name the **exact**
blocking items and what would clear each. If the evidence is genuinely insufficient, say so and name
precisely what is missing.

## What "ratifiable" means

- The skill's outputs are **correct, complete, single-sourced, and at the right altitude** (the
  product/artifact's own concern, not a layer below it) — and it holds that **consistently across the
  different cases**, not on one lucky target.
- The **audit trajectory converges**: findings decreasing in count and severity across versions, with
  no recurring load-bearing defect that survives its own fixes.
- Any **open findings** are either non-blocking or clearly bounded.

## What a verdict may rest on

Four principles bound the evidence — a verdict that ignores them is not independent, it is guessing:

- **Ratify a version on that version's own output.** The artifacts you judge must have been *produced
  by* `<version>` itself. A verdict cannot rest on a cold-read of the skill's text, on an
  authored-but-unapplied fix, or on outputs an earlier version produced — those describe intent or a
  different version, not the one under ratification.
- **Judge across at least two independent cases.** One target cannot show consistency. Read
  `<version>`'s outputs on two genuinely different products/cases and weigh whether the skill behaves
  the same on both.
- **Read the two cases' unsettled items against each other.** A non-interactive skill parks what it
  could not settle in a companion open-issues file, retired whole into the artifact's answer-trail once
  the owner answers it — so the trails carry *which questions the skill could not close*, which the
  finished artifacts do not show. Which items **recur** is the evidence: an item raised in both cases is
  about the **skill** — a boundary it draws in the wrong place, or a call it leaves to the owner and
  could make itself — while an item raised in one is about that case's own material. Two runs can each
  produce a good artifact while asking wholly different questions, and that difference is a finding. Say
  which recurred and which were local, and let that split, not the count, drive whether an unsettled
  item blocks.
- **A pre-ratify cold-read is advisory.** A cold-read or an audit *surfaces* what the owner should see;
  it does not hold the door, and its being clean is not itself a ratification — the fact is owned by
  `<CORE>/doctrine/kaizen/skills.md` § Ratify. Weigh what the findings *say*, not merely whether they exist.

## Deliverable — both

1. **Commit a verdict file** at the supplied path. It contains: the verdict; a one-paragraph rationale;
   an **evidence table** (what you read → what it showed); an explicit section treating any **open or
   unapplied findings** (are they blocking, bounded, or cosmetic?); a **cross-case section** naming which
   of the cases' unsettled items recurred across them and which were local to one; and, if conditional or negative,
   the exact blocking items + what clears each. **Cite path + section for every claim.**

   The repo uses a shared commit-msg hook (via `core.hooksPath`) that **requires** `Role:` and
   `Surface:` trailers. Stage **only** the verdict file and commit with:

   ```
   Role: Meta
   Surface: Claude Code
   Co-Authored-By: <the ratifying model>
   ```

   plus the directional trailer the target repo's commit format expects. Subject shape:
   `docs: <skill> ratification verdict — <RATIFY|CONDITIONAL|NOT-YET>`. Then verify with
   `git log -1 --stat` that the commit landed and the hook passed.

2. **Return** as your final output: the verdict, a one-paragraph rationale, the committed file path, and
   the commit SHA.

## Constraints

- **READ-ONLY** everywhere except the single verdict file you author and commit. Do not edit the skill,
  its outputs, the trails, or the audit evidence.
- Every claim cites a specific file + what it says. No unsupported assertions — this is a gate.
- Reach a verdict if the evidence supports one; if not, name exactly what is missing.
