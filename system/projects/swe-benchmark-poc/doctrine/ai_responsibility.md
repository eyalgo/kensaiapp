# AI responsibility — swe-benchmark-poc

*The boundary between **AI-driven decisions** and **mechanical / system rules** for this `swe-benchmark-poc`. Two
parts: the **general** doctrine (§1, what AI may and may not decide) and the **per-role** doctrine (§2,
each role's specific decision boundary). Layered kensaiapp-core → instance → project; **precedence is
fixed by core (see §0).** Authored at the lower two levels — the instance (cross-project) and each
project (product-specific) — both stamped from this template. The instance's `AGENTS.md` § doctrine stub
points here; stamped **verbatim**, substituting only `swe-benchmark-poc`.*

---

## 0. Precedence — set by core

Precedence is fixed by kensaiapp-core's `ai_responsibility.md` §0: **core dominates.** This `swe-benchmark-poc`
layer may **add** a role boundary or **tighten** an existing one; it may **not relax, remove, or
override** a boundary set in core. On conflict, the core rule wins and the conflict is surfaced.

## 1. General AI doctrine

> **The standing shape, which governs `swe-benchmark-poc` until this section adds to it.** AI reasoning drives
> decisions **within a role's scope**; mechanical rules — skills, pipeline gates, the flow's
> halt-don't-ask, commit and seal bookkeeping — **constrain** that reasoning and are not the AI's to
> override. Where the two conflict, the mechanical rule wins and the AI surfaces the conflict rather than
> working around it.
>
> **Add a `swe-benchmark-poc`-specific rule here only where the layers above this one do not already give it** —
> what the AI decides for `swe-benchmark-poc`, what it must not decide, and the principle that settles a case none
> of them names. Each addition **adds or tightens**; none relaxes core (§0).

**1.1 A run that works an issue does not look for its fix.** No run inside an issue's change reads
the benchmark or its fix from anywhere: not the SWE-bench dataset or any local copy of it, not the
grading harness's logs, and not the upstream repository's history after the issue's base commit, its
pull requests, its issue tracker or its later releases. It works from the change request and the clone
it is handed. A patch made with any of these in view shows nothing about KensaiApp.

**1.2 No headless run deletes anything outside its own change.** Cleaning up the benchmark's files, a
clone or the harness's output is the owner's act, or an interactive session's, never a step on a
headless run's path.

## 2. AI doctrine per role

> **One entry per role, and only where `swe-benchmark-poc` needs a boundary the layers above it do not give.** An
> entry records what that role decides **autonomously** and what it **must not** touch — the shape being
> that a role may choose its own next work but may not edit an artifact owned upstream. The **base**
> per-role rules are kensaiapp-core's; the instance body (`system/doctrine/ai_responsibility.md`) adds
> the cross-project boundaries, and a project's file adds only what is product-specific. Each layer
> **adds or tightens**, never relaxes core (§0). Where this section names no role, the layers above
> govern it.
