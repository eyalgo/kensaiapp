---
version: "1.2.3"
---
<!-- The version above is template-file metadata; it is not copied into the template you author from
     this one. Nor is any comment block in this file.

     WHAT THIS STAMPS: a stack's DOCUMENT TEMPLATE — the third artifact of a stack, the one
     `<CORE>/doctrine/setup/authoring_layers.md` § The skill and its prompt calls the section shape,
     beside the skill (orchestrator) and the prompt (thinking). Its own output is a real document in
     a product, a project or the instance. The doubled word in this file's name is deliberate: it is
     a template for a template, and every shape in this layer is named `<what it stamps>_template.md`.

     IT ALSO STAMPS THE COMPANION beside it. Every stack measured carries a pair — the document and
     its `*_open_issues_template.md` — and the pair is what makes the loop's done signal work. § THE
     COMPANION at the foot is that half.

     MODEL-FACING, AND SO IS WHAT YOU AUTHOR FROM IT (`<CORE>/templates/README.md` § The rule — a
     template's format follows its consumer). A skill's prose tells a model to author the document,
     so the template it reads may carry frontmatter, HTML-comment guidance and prose about itself, and
     none of it survives into the result. IF A SCRIPT WILL STAMP YOUR TEMPLATE INSTEAD, STOP AND USE
     THE OTHER FORMAT: that README's § Adding a script-facing template governs, the file is the bytes
     you want to land, and it must carry NO frontmatter and NO `version:` at all
     (`<CORE>/doctrine/governance/versioning.md` § The test — who reads the file, not what kind of
     thing it is). The two are not stylistic variants; getting it wrong costs a stripper function in
     the stamper, forever.

     TOKENS: <DOC> the document's short name in caps as its filename carries it · <doc> the same
     lowercased, for the trail folder · <subject> what the document is about — a product name, an
     instance name · <Role Title> the seat that owns it.

     THE SHAPE BELOW WAS MEASURED, NOT PROPOSED. Six document templates and their six companions
     were read whole and their headings extracted with `grep -n '^#\{1,3\} '` (2026-08-19):
     prd_template, srs_template, uxd_template, design_template, content_template and
     writing_bar_template, with the `*_open_issues_template` beside each. Where all six agree the
     element is stated flat below. Where they diverge, § THE OPEN CHOICES names the divergence, the
     count and who does what — a template that picks one quietly turns an open question into a house
     fact the next author inherits without knowing it was ever a question.

     THE GROUNDING RULE — the one check this template exists to force.
     Every element the authored template calls REQUIRED resolves one of exactly two ways, and the
     author writes which: (a) it has an owner — name the file and section, open it in the same
     session, and confirm the named section carries THE CLAIM and not merely the topic; or (b) it is
     this template's own — say so in the sentence. The failure worked in full, with the commands, is
     `<CORE>/templates/authoring-templates/skill_template.md`'s opening block; it is not repeated
     here, and one copy of it is the point. This rule is stated on THIS TEMPLATE'S OWN AUTHORITY —
     option (b) — because no doctrine file states it today.

     WHAT A TEMPLATE OWNS, AND WHAT IT MUST NOT: the sections and their order, and nothing else. What
     each section must ANSWER, and the bar an entry is written to, are the PROMPT's. Restating them
     here makes a second copy that is accurate the day it is written and false the day the prompt
     moves, with nothing watching (`<CORE>/doctrine/governance/single_source.md` § Why a copy is
     worse than it looks). The comments you write say what a section is FOR, never how to decide it.
     Four of the six say exactly this in their own opening block; model it on
     `<CORE>/templates/product-templates/content_template.md:17-20`.

     DELETE ANY SECTION THE DOCUMENT GENUINELY HAS NO CONTENT FOR — but the six-of-six elements below
     are the floor, and an author who drops one owes a reason rather than an omission.

     THE METADATA NOTE UNDER THE FRONTMATTER says the version is "not copied into the instantiated
     document" — that exact word, in all eight document templates on disk. Not "stamped": most of
     these are read by a model that authors a fresh file, with no script to stamp anything, so the
     word would name a mechanism the template does not have. -->

<!-- ==== THE OPENING BLOCK OF THE TEMPLATE YOU ARE AUTHORING — write it like this ==== -->

<!-- The single source of the <DOC> shape. Lands at `<where the stamped document goes>`.

     MODEL-FACING: the `<skill-name>` skill reads this file and authors a fresh document, so
     everything here may explain itself and none of it survives into the result.

     WHAT THIS FILE OWNS: the sections of the document and their order, and nothing else. <What the
     document covers, and the bar each entry is written to, are the skill's own `prompts/rich.md`'s — the
     authoring body this shape is stamped under, declared on both sides
     (`<CORE>/doctrine/setup/authoring_layers.md` § The carriers).>

     PROVENANCE — <where the format came from, if it came from anywhere. If the format is an outside
     vendor's, say so, name the exact command and version the schema was read from, and say the
     vendor is the authority rather than this file — `<CORE>/templates/product-templates/design_template.md:9-19` is the model. If
     the format is ours, say THAT explicitly and say what stands where a vendor's linter would have
     stood — `<CORE>/templates/product-templates/content_template.md:9-15` is the model. An unstated provenance reads as ours by
     default, and a later author will not know which it was.>

     <Anything empirically verified about the format — a probe run, an exit code observed, a section
     that turned out to be safe — goes here with its date, so the next author does not re-run it or,
     worse, assume it.> -->

<!-- ==== THE HEADER BLOCK — six of six, verbatim in shape ==== -->

# <DOC> — <subject>

**Status:** Draft | Settled | Locked
<!-- Draft = the companion is on disk, so something awaits the owner.
     Settled = the companion is gone. Nothing awaits the owner — the done signal.
     Locked = ratified as the source of truth. The owner's act, never the run's. -->
**Owner:** <Role Title>
**Version:** <n> — <one-line note on what this revision changed **about the subject** — not the
authoring cycle; no "folded in the answer / retired the companion">

<!-- ALL FOUR LINES ARE SIX OF SIX: the `Status:` line with a comment defining all three values, the
     `Owner:`, and the `Version:`. Measured with `grep -c '^\*\*Status:\*\*'` and its siblings across
     the six templates, each returning 1.

     THE `Status:` COMMENT IS NOT DECORATION. The skill sets this line from the DONE condition — the
     companion's absence — never from a tally of answers, and the three values have to be defined
     where the author of the document can see them, or the line degrades into a mood.

     THE `Version:` IS THE DOCUMENT'S OWN, in the body, not frontmatter — a product's artifacts
     version by the product's rules (`<CORE>/doctrine/governance/versioning.md` § Out of scope). The
     template file's `version:` at the top is a different marker for a different reader; do not merge
     them.

     WRITE THE `Version:` HINT AGAINST THE SUBJECT, NOT THE CYCLE. Only prd_template does this today
     (`<CORE>/templates/product-templates/prd_template.md:15`) and it is the right instinct: without it, revision notes fill up with
     "folded in the owner's answers", which records the machinery and nothing a reader wants. -->

> <The orientation paragraph: what this document is the source of truth for, who reads it cold, that
> it is updated in place with versioning, and — as load-bearing as the rest — what belongs OUT of it
> and which document downstream holds that instead. Close with the omission rule: omit a section
> only when it genuinely does not apply; do not pad one to fill it.>

<!-- FIVE OF SIX carry this blockquote; writing_bar_template has none (§ THE OPEN CHOICES). Where it
     exists it is the one place a cold reader learns the document's altitude, so a template without
     one is asking every author to re-derive it.

     KEEP TASTE OUT OF IT. `<CORE>/doctrine/governance/where_taste_appears.md` § What a document
     upstream may say: a document that does not own the aesthetic call carries the requirement, never
     the preference — "every destructive action is undoable for 10s or confirmed" belongs upstream,
     "the product should feel forgiving" does not. -->

---

<!-- ==== THE SECTIONS ==== -->

## <Section>

<!-- One comment per section saying what it HOLDS. Not how to decide it — that is the prompt's. -->

<A placeholder in angle brackets showing the shape of an entry, not an example of one. Where entries
need stable IDs so downstream documents can cite them, give them a typed prefix here and say so in
the orientation paragraph.>

## <DOC> Review Notes

<!-- FIVE OF SIX carry a review-notes section: srs, uxd, design_md, content_md and writing_bar.
     prd_template does not (§ THE OPEN CHOICES).

     WHAT IT IS FOR: the run's own divergences and the reasons for them, recorded in the document
     rather than in a chat nobody keeps. Three loaders and three authoring prompts state an
     improvement-logging obligation against a section like this one — `<CORE>/roles/loaders/content_manager_global.md:30`,
     `<CORE>/roles/loaders/developer_global.md:54`, `<CORE>/roles/loaders/principal_pm_global.md:20-21`, and the "not a passive translator"
     clause in `<CORE>/../skills/cdo/.claude/skills/product-uxd/prompts/rich.md`, `<CORE>/../skills/cdo/.claude/skills/product-design/prompts/rich.md` and `<CORE>/../skills/cto/.claude/skills/product-srs/prompts/rich.md` (measured
     2026-08-19). If your stack's role carries that clause, this section is where it discharges, and
     omitting it leaves the clause with nowhere to land.

     BE CAREFUL WHAT YOU CALL IT, THOUGH. Whether that obligation is DOCTRINALLY required is exactly
     the open question the grounding rule above was written from: the file usually cited for it does
     not carry it. State the obligation as your role's, cited to the loader or prompt that actually
     states it — those six are named above and each was opened — and not to a doctrine file that
     merely bans the opposite. -->

<!-- ============================ THE COMPANION ============================
     Every stack measured carries a second template, `<x>_open_issues_template.md`, and the pair is
     what makes the done signal work: the document's `Status:` is set from whether this file exists.
     Author it beside the document template, in the same commit. Its measured shape, six of six:

       version: frontmatter, and the same metadata-not-copied note
       # <DOC> open issues — <subject>
       > a blockquote addressed to THE OWNER: answer inline, fill each slot, COMMIT THIS FILE, then
         re-run <skill-name>; when nothing is left the skill deletes this file, and no file = done.
         It also promises the trail — each fold copies this file whole to `trail/<doc>/` first, so
         what the owner decided and why stays readable and citable for good. Six of six make that
         promise, and it is the sentence that earns the owner's trust in answering inline at all.
       ---
       ## 1. Open issues — <the kind of question>, with no answer yet
       ### 1.1 <the question, in one line>
       - **Why it matters:** <what in the document depends on this>
       - **Answer:** <the owner fills this in>
       <!- - add 1.2, 1.3, … as needed - ->
       ## 2. Choices to confirm — the <Role Title> drafted a best-effort answer; confirm or override
       ### 2.1 <the decision, in one line>
       - **Drafted into the <DOC>:** <the choice made, and where it was written>
       - **Rationale:** <why this was the best-effort call, and the source it derives from>
       - **If overridden:** <the blast radius — what moves, and how>
       - **Confirm or override:** <"confirm", or "override: <what to do instead>">

     THE TWO SLOT LABELS ARE SIX OF SIX AND EXACT — `**Answer:**` and `**Confirm or override:**`,
     measured with `grep -o` across all six companions. The skill detects a consumed companion by a
     FILLED SLOT, so renaming a label silently breaks the loop's re-entry: a filled answer reads as
     unfilled and the owner's words are dropped. If you must rename one, the skills read the label
     from the template's current shape rather than from memory — check that yours does before you do.

     A THIRD BUCKET IS THE EXCEPTION, NOT THE RULE. Only prd_open_issues carries one
     (`## 3. Directives`, for an external action the owner confirms as a gate). Add a third bucket
     only where a genuinely different KIND of item exists — not to sort items you already have.

     A SUB-ITEM FOR A DECLARED ABSENCE. Three companions (design, content, writing_bar) carry an
     item shape under bucket 2 for "a category/section declared absent", so an omission reaches the
     owner as a choice to confirm rather than as a silent hole. Where your document template permits
     omitting a section, carry it; where it does not, do not.
     ======================================================================= -->

<!-- ============================ THE OPEN CHOICES ============================
     Divergences measured across the six document templates on 2026-08-19 that no doctrine resolves.
     Each is a real choice, not a defect to copy or avoid. Delete this block from what you author.

     1. A REVIEW-NOTES SECTION — 5 of 6 carry one; prd_template does not. Nothing on disk says a
        document template must. The question is whether the owning role carries an
        improvement-logging clause: where it does, the section is where that clause discharges.

     2. AN ORIENTATION BLOCKQUOTE — 5 of 6; writing_bar_template has none, and also has no `---`
        rule under its header block. Its § 0 "Where this sits" does the orientation job as a numbered
        section instead. Both work; the blockquote is the majority and is easier to read cold.

     3. AN OWNER-DECLARATION COMMENT BLOCK after the frontmatter — 4 of 6 (uxd, design_md,
        content_md, writing_bar) open with a block headed "The single source of the <X> shape",
        naming what the file owns and what it does not; prd_template and srs_template carry only the
        one-line metadata note. `<CORE>/doctrine/governance/single_source.md` § The rule calls that
        declaration load-bearing rather than decorative — "without the declaration there is no way to
        ask whether a sentence belongs where it sits". Write it.

     4. NUMBERED SECTIONS OR NOT — 3 of 6 number them (srs 1-8, uxd 1-11, writing_bar 0-3); prd,
        design_md and content_md do not. Numbering makes a section citable from another document by
        `§ n`; not numbering survives a reorder. Pick by whether anything downstream will cite the
        sections, and say which in the opening block.

     5. `## Open Questions` — 3 of 6 (prd, srs, uxd). Whether to carry it is the choice; what it
        means is no longer one. All three now draw the line explicitly, because a document that
        routes an item to the companion AND lists it here gives it two homes while only the
        companion's absence reports done. prd moves a confirmed gate out to
        `## Gates & External Dependencies`; srs and uxd keep only what resolves downstream rather
        than by an owner's answer. If you carry the section, say in its comment what makes an item
        belong here rather than in the companion; if you cannot, that is the answer.

     6. `## Traceability` — 3 of 6 (uxd, design_md, content_md), each tracing to its own upstream
        document. Carry it where your document derives entry-by-entry from a named upstream; not
        where it does not.
     ========================================================================= -->
