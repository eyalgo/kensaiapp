---
version: "1.7.1"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->
<!-- Nor is this block. What this stamps: the instance overlay for one prefix-invoked role — the thin
     layer over that role's posture body at `<CORE>/roles/loaders/<role>_global.md`, naming only what
     is true of the instance it lives in. Lands at `system/loaders/<role>.md`, one file per role.

     For the thirteen roles that read no context: architect · cdo · content_editor ·
     content_manager · cpo · cto · developer · principal_architect · principal_pm ·
     product_owner · scrum_master · senior_engineer · tech_lead.
     **pm has its own template** (`pm_overlay_template.md`) — it is the only role in a kensaiapp
     that reads a context, and that difference is structural, not a substitution.

     **§ On invocation has two forms, and the role decides which.** The body below is the
     **delivery tier's** — architect · content_editor · developer · product_owner · scrum_master ·
     senior_engineer · tech_lead, and
     principal_pm, which cuts 根回し Nemawashi seeds from the settled SDD and so writes the
     journey rather than standing outside it. The **definition tier** — cpo · cto · cdo ·
     content_manager · principal_architect, whose records name no change unit — authors its
     documents before any change unit exists and takes the alternative carried in the comment
     directly above that section. Same split, same reason, as
     `<CORE>/roles/CROSS_ROLE.md`'s definition-tier carve-out.

     Replace `<role>`, `<Role Title>` and `<instance>` throughout. The stamped file starts its own
     `version` at 1.0.0 and carries no comment blocks.

     NO CHANGE-RECORD SECTION, AND THAT IS DELIBERATE. An overlay records nothing about its own
     history: no Review Notes, no changelog, no what-changed-and-why. Nothing here has been left
     out. The practice is consistent across the whole role layer — measured 2026-08-31, none of the
     14 global bodies and none of the 12 overlays carries one, and the two places the word "Review
     Notes" appears in that layer both name the section of an artifact the ROLE produces (an SRS, an
     SDD, a closing commit body), never a section of the loader.

     WHY, because an instance's writing bar will ask. A definition-chain document is derived from:
     the SRS reads the PRD, the SDD reads both, and a reader deciding whether a downstream document
     is still true has to know what authorized the change without leaving the file — so those
     documents carry the record inside them. A loader is not derived from. It is read whole at
     session open, by a session that had no prior state, and nothing downstream cites it as a source
     (that is the rule at `<CORE>/doctrine/setup/setting_up_a_project.md` § *The definition set never
     names the journey*, read from the other side). Its history has a real home already: the commit
     that made the change carries the reason, the Role that made it, and the version this file
     bumped to. A second copy inside the file would be the copy `single_source.md` deletes.

     SO A BAR THAT REQUIRES A CHANGE RECORD IN "a document authored here" DOES NOT REACH AN OVERLAY,
     and this paragraph is the statement that says so rather than leaving the silence to be read as
     an omission. An instance that wants one anyway may add it — a lower layer may tighten — but it
     is adding something, not filling a gap. -->

# <Role Title> loader — <instance> overlay

Extends `<CORE>/roles/loaders/<role>_global.md` (role posture, skills, hand-off triggers). This overlay
adds only what is true of *this* instance — everything else is the global loader's; read it there
rather than trusting a summary here.

## On invocation

<!-- DEFINITION TIER (cpo · cto · cdo · content_manager · principal_architect) — use this paragraph
     instead of the one below, naming this seat's own upstream document where it says "the settled document":

     No on-invocation context read. Posture comes from the two-layer stack (the global core loader
     above + this instance overlay); live state is the settled document above this seat in the
     definition chain. Its `journey/` is read **deliberately** when a station has opened this run —
     that station's guardrail binds you — never reflexively, and it is an **input**, never live
     state and never a source a document may cite
     (`<CORE>/doctrine/setup/setting_up_a_project.md` § *The definition set never names the
     journey*). -->

No on-invocation context read. Posture comes from the two-layer stack (the global core loader
above + this instance overlay); live state comes from the directed project's `journey/`, consulted
**deliberately** — not read reflexively here.

## Key files

- `system/projects/<name>/project.md` — the project card and product binding (`Product path:`).

## The domain

**Not declared yet.** This instance's domain section is deliberately empty — it is authored per
instance, and leaving it blank is a stated state, not an oversight. Until it is written, the global
loader's posture governs alone. Do not copy another instance's domain here.

## Project-specific rules / overrides

None yet — the global <Role Title> posture governs.
