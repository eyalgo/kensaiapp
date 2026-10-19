---
version: "1.0.1"
---

# AI responsibility — kensaiapp-core (base)

*The boundary between **AI-driven decisions** and **mechanical / system rules**, layered
kensaiapp-core → instance → project (precedence in §0: **core dominates**). This is the **base**
(kensaiapp-core) body — the shipped default every instance inherits. Two parts: general doctrine (§1)
+ per-role doctrine (§2). The meta-principle is set by the instance's `AGENTS.md` § Doctrine;
this is the concrete base body. This file and the instance / project layers all stamp from
`templates/ai_responsibility_template.md`.*

---

## 0. Precedence — the guardrail (core dominates)

ai_responsibility layers like an instruction file: core (this file) sets the **base** AI-boundary for every
role; an instance and a project layer their own on top. **But precedence is inverted.** Unlike
an instruction file, where the most-local one wins, here **core is authoritative.** A lower layer may **add**
a role boundary or **tighten** an existing one — it may **not relax, remove, or override** a boundary
set in core. Where a lower-layer rule conflicts with core, **the core rule wins**, and the conflict is
**surfaced**, not silently resolved in the instance's favor. A deployment can be *stricter* than the
kensaiapp default, never *looser*. This is the same shape as §1's mechanical-rule-wins, raised to the
layer axis: the base boundaries are a guardrail.

**The layers, base → most-local:**

1. **kensaiapp-core** — `<CORE>/doctrine/governance/ai_responsibility.md` (this file). The shipped
   default every instance inherits. **Authoritative on conflict.**
2. **kensaiapp instance** — `system/doctrine/ai_responsibility.md`. This deployment's cross-project
   additions. Adds / tightens; never relaxes core.
3. **project** — `system/projects/<name>/doctrine/ai_responsibility.md`. Product-specific additions
   for one project. Adds / tightens; never relaxes core or the instance.

## 1. General AI doctrine

AI roles drive reasoning and decisions **within their own scope**. Mechanical / system rules — the
skills, the pipeline gates, the flow's halt-don't-ask, and the commit/seal bookkeeping — **constrain**
those decisions and are **not the AI's to override**. Where an AI decision and a mechanical rule
conflict, the **mechanical rule wins**, and the AI **surfaces the conflict** rather than working around
it. The AI's autonomy is *inside* its lane; the rails between lanes are mechanical.

## 2. AI doctrine per role

Each role decides autonomously within its lane and must not cross into another role's locked artifacts:

- **PM** — picks autonomously what to work on next; **must not** modify the FDR. The FDR is the product
  contract, owned upstream; the PM *derives* the next change from it, it never *edits* it.

*(More role boundaries are added here as they emerge.)*
