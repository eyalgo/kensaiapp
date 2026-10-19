---
version: "2.5.0"
---

# Skill intelligence — the work sets the model and the effort, not the worker

This file owns how much intelligence a chain run gets and where that is declared. Intelligence is the
pair **model + effort**, and it is set by the **work** — the skill and the prompt it runs — never by the
role or agent that carries the work out. The owner's call, 2026-09-29.

> **Owns:** what intelligence is, where a skill declares it, how a launch reads it, and what happens
> when it is missing. **Does not own:** the values themselves (each skill's own
> `intelligence/<provider>.md`), the model of a run with no skill behind it
> (`model_assignment.md` § *Runs with no standing slot*), eval runs (`model_assignment.md`
> § *Eval runs*), or the frame this rule instantiates (`system_anatomy.md` § *Intelligence follows the
> work, not the worker*).

---

## The rule

**A role is context. A skill and its prompt are the work. The work sets the intelligence.** A role's
agent definition carries posture, trusted documents, tools and authority. It carries no `model:`. A
skill carries the model and the effort its work needs, because two skills run by one role can need very
different intelligence: `tobiishi-seal` and `shukuba-refine` both run as `pm`, and one is procedural
closure where the other decides what a station becomes.

**Intelligence is the pair, not the model alone.** The same model at a low and at a high effort are two
different execution profiles, so a skill always states both halves together.

## Where a skill declares it

**One file per vendor, in the skill's own folder:** `<skill dir>/intelligence/<provider>.md` — today
`claude.md`, and `codex.md`, `gemini.md`, `hf.md` or `ollama.md` when that vendor is given one. Each file holds
three things:

- **`**Model:**`** — the vendor's exact model ID, as that vendor's CLI takes it (`claude-opus-5-5`). An
  alias that floats with the vendor's releases (`opus`) is not accepted, because it changes what a skill
  runs on without any file here changing.
- **`**Effort:**`** — the vendor's effort level for that model. Optional: where the field is absent, no
  effort is passed, which is right for a model that takes none.
- **A Why paragraph** — why this work earns this intelligence, read against the task's length,
  ambiguity, risk and what downstream consumes as-authored.

**Each vendor's file is written in that vendor's own terms.** There is no cross-vendor tier and no
table that translates one vendor's choice into another's. `Opus` names one vendor's model, and a
skill's intelligence on another vendor is a separate decision about that vendor's catalogue, made in
that vendor's file.

**A skill's `launcher.md` carries neither `**Model:**` nor `**Effort:**`.** The intelligence file is
their one home.

## How a launch reads it

**The launcher reads the file for the provider the run goes to, and passes both halves to the
provider's adapter unchanged.** Whether a model and an effort are a valid pair is the adapter's check,
per provider — a skill file never encodes one vendor's constraints for another.

**No file for the running provider → the launch is refused, and the refusal names the missing path.**
Nothing falls back — not to the agent file, not to `model_assignment.py`'s tier table, and not to the
provider's default model. A fallback is deliberately not built. The owner's call, 2026-09-29.

**A skill with no `intelligence/` folder at all is outside the rule**: it launches with no model and
no effort, on the provider's default. The refusal fires only where the folder exists without the
running provider's file. A chain skill cannot slip out by losing its folder, because a test derives
the chain-launched set from the engines' own tables and requires each member's file.

**One chain skill reads its intelligence differently**, by the owner's call, 2026-09-29:

- **`companion-self-answer`** has no intelligence file of its own. It runs on the **producing
  skill's** model — the skill whose document it is answering — and always at effort `high`, whatever
  effort the producer declares. Where it cannot resolve the producer, it runs on the provider's default
  model, still at `high`.

`product-sdd` is not an exception: it is a CTO skill with one run, so its `intelligence/` folder
declares one `**Model:**` and `**Effort:**` per provider, like every other producer's.

## Scope

**Every skill a chain launches carries an intelligence file** — the product chain's document
producers, the development and change chains' steps, and `build-idea`'s journey moves — except
`companion-self-answer`, which runs on its producer's (above). Which skills those are is the chains' own to state: `<CORE>/tools/chain.py`
`DOCUMENT_REGISTRY`, `<CORE>/tools/chain_development.py` `DEVELOPMENT_STEPS` and `CHANGE_STEPS`, and
`<CORE>/tools/build_idea.py`. **Which provider a chain's run goes to is stated in one file per instance, `.providers.toml` at the instance root** — one entry per document, step and `build-idea` skill row, and a walk may be forced onto a provider over it. Its only reader, and the rule between the two, is
`<CORE>/tools/providers.py`; an entry the file lacks is refused, never defaulted. This file's part is
unchanged by it: the intelligence file read is the one for the provider the run goes to, and its
absence is refused.

**A skill outside the chains may carry an `intelligence/` folder where a launcher reads it.** That
is the skill launcher, `<CORE>/launchers/skill/launcher.sh`, for a skill that holds a `launcher.md`,
or the skill's own `<CORE>/launchers/<skill>/launcher.sh` where it has one. Once the folder exists,
the rule above holds for that skill unchanged: the file read is the one for the provider the run goes
to, and its absence is refused. `kensaiapp-writing-bar` is the first, and `experience-visual` and
`experience-voice` follow it — the owner's calls, 2026-09-30.
A folder that no launcher reads declares nothing, so a test names each such skill and requires one
of the two.

**Every other run outside the chains is untouched by this file.** An interactive session, an
Agent-tool spawn, a run started through `agent-invoke`, and a launcher that starts an agent without a
skill's intelligence file run on whatever model their caller passes, or on the provider's default
where none is passed.
`model_assignment.md` § *Runs with no standing slot* still governs how a caller with no skill behind the
run chooses.
