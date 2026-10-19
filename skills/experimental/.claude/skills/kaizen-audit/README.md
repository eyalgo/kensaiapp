# kaizen-audit

Auditing a skill through its output is not one reader's job — it is a fan-out of
independent ones, some of whom must **not** see the skill and some of whom must see
the whole stack, run in that order and never mixed. A single reader given
everything cannot fresh-read the artifact, and a fresh reader given nothing cannot
say which layer to fix. This skill runs that shape: it spawns the blind lens
auditors, then the non-blind synthesis passes, and gathers what they find into one
`audit.md` beside the artifact. It orchestrates and collects; the lens files
(`<CORE>/doctrine/kaizen/lenses/`) own how each auditor looks.

It is written to be **agnostic to any procedure that calls it**. It takes an
artifact, its producing stack, and an optional prior version as inputs, and hands
back findings — it does not produce the evidence it reads, and does not act on the
findings it emits. A kaizen skill-hardening round is the caller it was built for,
but the skill encodes none of that round's steps.

## What It Does

- Reads the lens set from `<CORE>/doctrine/kaizen/lenses/README.md` — the authority
  for which lenses are blind (fan-out) and which are not (synthesis).
- **Blind fan-out** — spawns one `kensaiapp-auditor` per blind lens, each given the
  artifact and its inputs and *nothing about the skill*, running concurrently. A
  blind auditor classifies its findings but does not name a layer.
- **Non-blind synthesis** — runs the version comparison, the surfaced-set
  comparison, and one layer-location pass per skill-general finding, each given what
  a fresh read is not allowed (both versions, or the whole stack).
- **Gathers** every finding into an `audit.md` beside the artifact — a stack
  manifest, the round shape, who ran, the findings in the contract's ledger grammar,
  and any disagreement surfaced rather than resolved away. It gathers; it does not
  re-judge a verdict.

## File Structure

```
kaizen-audit/
├── SKILL.md    # the orchestration: what to read, the fan-out, the synthesis, the gather
└── README.md   # this file
```

The lenses, the contract, and the auditor agent live outside this skill by design —
the lenses and contract in `<CORE>/doctrine/kaizen/lenses/` (so a lens versions on
its own and an auditor loads only its own), and the `kensaiapp-auditor` agent in its own group, `<CORE>/../skills/kensaiapp-auditor/.claude/agents/kensaiapp-auditor.md`. This skill names them; it does not carry them.

## Depends On

- **`kensaiapp-auditor`** — the agent this skill spawns, once per lens. It carries no
  lens of its own; the task prompt this skill writes names the lens, and the agent
  loads that lens and the contract itself.

## When to Use

Reach for this when there is a settled, snapshotted artifact to audit — the produced
document sitting with its inputs as evidence — and you want the skill that made it
judged through it. Phrases that fit: "audit this evidence", "fan out the auditors",
"audit the product-prd output", "run the audit over v3.4.0". It expects the snapshot
to exist already; if the artifact is still live and unsnapshotted, it stops rather
than audit in place. It is not the fixer — it emits findings and leaves acting on
them to the caller.
