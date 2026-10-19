---
version: "1.1.0"
---
<!-- The version above is template-file metadata; it is not copied into the authored prompt. Nor is
     any comment block in this file. An authoring prompt carries no HTML comments of its own: the
     comment count across the eight measured is 0 in every one of them, so a prompt says everything
     it has to say in text a run reads.

     WHAT THIS STAMPS: one `prompts/rich.md` inside its skill's folder — the THINKING half of
     a stack, and the layer where its substance lives. Which layer may hold what is
     `<CORE>/doctrine/setup/authoring_layers.md` § The carriers, whose *The skill and its prompt*
     paragraph splits skill = orchestrator · prompt = thinking · template = section shape. This file
     carries the SHAPE that split produces, measured off the prompts that already exist; it does not
     restate the split.

     THE TEST FOR WHICH SIDE A SENTENCE FALLS ON is `<CORE>/doctrine/kaizen/lenses/locate_layer.md`,
     at `:41-46` inside § *Read the layer as it stood*: "would the fix change how the author *thinks
     about a claim*, or how the run *moves files*? Thinks-about-a-claim → the authoring prompt.
     Moves-files (a posture gate, a bucket's lifecycle, paths, cycle numbering, staging, the DONE
     signal, reporting) → the skill." Apply it before writing, not after a defect.
     CITE IT BY LINE, NOT BY SECTION. `authoring_layers.md:65` names it as
     "`kaizen/lenses/locate_layer.md` § the boundary test"; there is no section by that name — the
     test is a phrase inside § *Read the layer as it stood*. The content is genuinely there, so the
     claim holds and the anchor does not, which is the near-miss the grounding rule below is about.

     MODEL-FACING (`<CORE>/templates/README.md` § The rule — a template's format follows its
     consumer): a person or an agent reads this file and authors a fresh prompt, so everything here
     may explain itself and none of it survives. NOTE THE ASYMMETRY WITH WHAT YOU AUTHOR: this
     template is model-facing, and the prompt you write from it is READ WHOLE BY A RUN AS ITS
     INSTRUCTIONS. Nothing in the authored prompt is scaffolding a reader is expected to skip.

     TOKENS: <Role Title> the human name of the seat · <artifact> the thing authored, lowercased ·
     <DOC> the document's short name as it is written in prose · <skill-name> the carrier skill ·
     <subject> what the artifact is about — a product, or the instance.

     THE SHAPE BELOW WAS MEASURED, NOT PROPOSED. The eight `*_create_*` prompts on disk were read and
     their headings extracted with `grep -n '^#\{1,3\} '` (2026-08-19): cpo_create_prd,
     cto_create_srs, cdo_create_uxd, cdo_create_design, content_manager_create_content,
     cdo_create_visual_experience, content_manager_create_voice_experience and
     content_manager_create_writing_bar, running 176 to 574 lines
     (`ls <CORE>/prompts/ | wc -l` -> 12, `ls <CORE>/prompts/*_create_* | wc -l` -> 8). The eight
     have since moved under their skills as `prompts/rich.md` (2026-10-04), so the commands below
     record the measurement as it was taken and no longer reproduce it.

     THE HEADLINE MEASUREMENT, AND THE ONE THING TO TAKE FROM THIS FILE: THE HEADER IS AN INVARIANT
     AND THE BODY IS NOT. Every part of § THE HEADER BLOCK — the frontmatter, the H1, the
     orientation paragraph, the carrier declaration, and the `---` closing them — is eight of eight,
     in that order and with nothing between them. Below it, the eight prompts carry 72 `##` sections
     between them, of which 54 are distinct, and NO SECTION IS
     CARRIED BY MORE THAN FOUR OF THE EIGHT. Measured with
         for f in <CORE>/prompts/*_create_*; do grep -h '^## ' "$f"; done | sort | uniq -c | sort -rn
     whose top row is 4. So there is no house section list to fill in, and a template that invented
     one would be the first thing in the house to claim it. § THE RECURRING MOVES is the register
     that stands in its place: the moves that recur, each with its count and every name it goes under.

     THE GROUNDING RULE — the one check this template exists to force.
     Every sentence the authored prompt states as REQUIRED resolves one of exactly two ways, and the
     author writes which: (a) it has an owner — name the file and section, open it in the same
     session, and confirm the named section carries THE CLAIM and not merely the topic; or (b) it is
     this prompt's own — say so in the sentence. The failure worked in full, with the commands, is
     `<CORE>/templates/authoring-templates/skill_template.md`'s opening block; it is not repeated
     here, and one copy of it is the point. The near miss above — a true claim under a section name
     that does not exist — is the cheaper half of the same failure and is just as invisible to a
     reader who does not open the file. This rule is stated on THIS TEMPLATE'S OWN AUTHORITY —
     option (b) — because no doctrine file states it today.

     A PROMPT IS THE ONE LAYER THAT MAY BE LONG. Its siblings are held short because a carrier that
     teaches goes unread; this file's output is the body they point at, and the substance has to be
     somewhere. Length is not the discipline here — LAYER is. A sentence about paths, staging, cycle
     numbering, a posture halt or the done signal is the skill's however well it is written, and a
     section shape is the template's.

     WRITE ONLY THE MOVES YOUR ARTIFACT NEEDS. An empty heading asserts nothing, and the register
     below is a menu, not a floor. The header block is the floor. -->

<!-- ==== THE HEADER BLOCK — eight of eight, in this order ==== -->

---
version: "1.0.0"
---

# <skill-name> — the <Role Title>'s <artifact> authoring lens

<!-- H1 = THE SKILL'S NAME, then an em-dash, then what the file is. The file is always
     `prompts/rich.md`, so the folder it sits in is what names it, and the H1 repeats that name: a
     reader who arrives by path sees the path confirmed; a reader who arrives by search sees the
     skill, the seat and the artifact in one line. Eight of eight measured prompts carried their
     own name as the H1's first token before they moved under their skills, 2026-10-04. -->

You are the **<Role Title>** authoring <the artifact, with its path where it has a fixed one>: <what
it is the source of truth for>. <Where it sits — what it is written off, what is written off it, and
by pointer to the doctrine that fixes that order, never by restating it.> <Who reads it cold.>

<!-- FOUR THINGS, EIGHT OF EIGHT: the seat in the second person and in bold, the artifact, its place
     in the sequence, and that a downstream reader reads it COLD. "Cold" is the invariant word —
     `grep -ic 'cold'` returns between 1 and 6 for every one of the eight and 0 for none of them,
     and every hit was read in context and is the read-cold sense. Five of the eight put it in this
     paragraph; the other three state it later in the body.

     IT IS THE WHOLE JUSTIFICATION FOR THE REST. Every provenance gate, every stability rule and
     every cite-your-relation section below exists because the reader cannot ask the author
     anything. Write the cold reader down here by name and the moves stop looking like ceremony. -->

This prompt is the **thinking** — <name what it owns, as a list of its own section names, so a
reader can tell from this paragraph alone whether their question is in this file>. The <DOC>'s
**shape** is fixed by the template `<CORE>/templates/<scope>-templates/<x>_template.md`<; the
companion's shape by `<x>_open_issues_template.md` beside it>. The **posture** (the <Role
Title>-required halt), the **file loop** (<the document, its companion, the buckets, the done
signal>) and the **commit** are the `<skill-name>` skill's. Neither restates the other
(`<CORE>/doctrine/setup/authoring_layers.md` § The carriers).

<!-- THE CARRIER DECLARATION — eight of eight, and the one paragraph that may not be dropped.
     `authoring_layers.md` § The carriers requires a carrier to point at exactly one body and the
     pair to be DECLARED ON BOTH SIDES, never inferred: "a file that declares nothing has not
     adopted the rule; it has happened to be short" (`:49-51`). So this paragraph names the skill,
     and the skill's § Purpose names this prompt back. The declared pair that doctrine itself cites
     is `skills/cpo/.claude/skills/product-prd/SKILL.md:26-32` with `<CORE>/../skills/cpo/.claude/skills/product-prd/prompts/rich.md:11-18`.

     ALL THREE HALVES ARE NAMED IN ALL EIGHT: what this file owns, the template that owns the shape,
     the skill that owns posture / loop / commit. Verified per file by normalising newlines and
     matching on "prompt is the thinking", a `templates/` path, and the skill -> 8/8.

     CITING THE DOCTRINE IN THE PARAGRAPH IS 4 OF 8 (`cdo_create_visual_experience`,
     `content_manager_create_content`, `content_manager_create_voice_experience`,
     `content_manager_create_writing_bar`; the citation is newline-wrapped in the last, so a
     line-bound grep misses it). Cite it: the sentence is otherwise a house habit the next author
     cannot check.

     THE NO-RESTATEMENT CLAUSE IS 8 OF 8, UNDER FIVE WORDINGS — "Neither restates the other" (3:
     design, visual_experience, content) · "Neither file restates the other" (1: voice_experience) ·
     "neither half restates the other" (1: writing_bar) · "None of those is restated here" (2: uxd,
     srs, verbatim identical) · "Neither is restated here" (1: prd). THREE OF THE EIGHT EXTEND IT
     WITH WHAT TO DO INSTEAD, and the extension is the half worth having: uxd and srs both close
     "where this prompt names a bucket, the open-issues file, or the loop, it points at the skill,
     it does not define it", and prd says the same of a Posture or a Step. It is the sentence a
     later author meets when they are about to explain a bucket here for the reader's convenience. -->

---

<!-- ==== THE BODY — no fixed section list; pick from the register below ==== -->

## <The first move>

<The section, written as instruction to the run: what to do, the test that decides it, and what the
failure looks like when it is skipped.>

<!-- ONE `##` PER MOVE, `###` ONLY IF YOU ARE CHOOSING PRINCIPLE NUMBERING (see § THE OPEN CHOICES,
     item 1). Seven of the eight use `##` exclusively: `grep -c '^### '` returns 0 for seven and 12
     for `cpo_create_prd`, which is the only file in the set with any `###` at all.

     A `---` RULE BEFORE EACH SECTION IS FOUR OF EIGHT — `cdo_create_design` (10 of 10),
     `cdo_create_uxd` (11/11), `content_manager_create_content` (12/12), `cto_create_srs` (9/9). The
     three instance-subject prompts use exactly one rule, the one closing the header block above,
     and `cpo_create_prd` carries one before 4 of its 5. Either reads fine; the rules make a long file
     scannable
     and cost nothing.

     WRITE A HEADING THAT STATES THE MOVE, NOT THE TOPIC. Twenty-nine of the seventy-two carry an
     em-dash and a sharpening clause — "The corpus test — a rule that cannot be applied to a real
     string is theatre" — and those are the ones that survive being read out of order, because the
     clause carries the ruling and the noun only carries the topic. The bare-noun headings are the
     majority (43 of 72). -->

<!-- ============================ THE RECURRING MOVES ============================
     Every move carried by two or more of the eight, with its count and every name it goes under
     (2026-08-19). This is a menu. Nothing here is owed, and a move your artifact has no use for is
     an absence, not an omission — but a move you skip that five of eight carry is worth one
     sentence of reason in the run's own report. Delete this block from what you author.

     INPUTS — 5 of 8. `## Inputs you work from` (4: design, uxd, content, srs) ·
     `## Where the grounds come from` (1: writing_bar). Absent from cpo_create_prd and from both
     experience prompts. Where it exists it is a list, one bullet per input, and each bullet says
     what standing that input has — primary, evidence-and-background, authorized-decisions, scope
     boundary — and which of them wins where two disagree. That last clause is the load-bearing one:
     `<CORE>/../skills/cto/.claude/skills/product-srs/prompts/rich.md:39` states it as "where it and the PRD differ, **the PRD
     wins** — it was derived from this and supersedes it".

     A COMPLETENESS INSTRUMENT — 5 of 8. `## The derivation — the <X>-completeness lens` (4: design,
     uxd, content, srs) · `## The diagnostic — pass it before the PRD is done` (1: prd). Absent from
     all three instance-subject prompts. A numbered list of questions the finished artifact must
     answer, walked before the run calls itself done. It is the closest thing the set has to a
     shared instrument and it still is not a majority under one name.

     THE ONE TEST THAT DRAWS THE LINE — 5 of 8, and the sharpest move in the set.
     `## Sorting what the lens turns up — the one test that draws the line` (2: uxd, srs) ·
     `## Sorting what you write — the one test that draws the line` (1: writing_bar) ·
     `## The altitude test — the one question that decides whether something belongs here` (1:
     visual_experience) · `## The altitude test — the question that decides whether a line belongs
     to you` (1: voice_experience). One question, stated once, that partitions everything the lens
     turned up into what this artifact holds and what belongs elsewhere. Write the question, then
     the disposal of each side.

     WHERE AN ENTRY COMES FROM — 5 of 8. `## The why is the gate — creation provenance` (2: design,
     uxd) · `## The why is the gate — complete creation provenance` (1: srs) · `## An entry needs an
     origin, and an invented limit is worse than a missing one` (2: visual_experience,
     voice_experience). The PRD carries the same obligation as `## The tag contract — earned, not
     composed` plus principle 3. What it requires is a locator a cold reader can open, and what it
     bans is a claim that reads as verified because it is written confidently.

     A BOUNDARY SECTION — 5 of 8, under three names.
     `## What you own — and what you don't` (3: design, uxd, srs — verbatim, measured with
     `grep -n "^## What you own"`, which returns exactly those three) ·
     `## What belongs in this document, and what does not` (1: content, at `:255`) ·
     `## What a writing bar reaches, and what it does not` (1: writing_bar). The pairing is the
     point: a boundary written as one half is read as an invitation to the other.

     THE STABILITY RULE — 6 of 8, 5 of them as a named section, under FOUR different names.
     `## On a re-run — fold, don't re-author` (2: srs, writing_bar) · `## On a re-run or a
     re-authoring — fold, don't re-author` (1: uxd) · `## The stability rule — a re-run folds, it
     does not re-design` (1: design) · `## The stability rule — a re-run folds, it does not
     re-voice` (1: content). `cpo_create_prd` carries it as principle 7 at `:374`, "Settled content
     is stable; every delta names its authorization". Absent from both experience prompts — checked
     rather than assumed: `grep -ic '\bfold'` returns 0 for `cdo_create_visual_experience.md`, and
     `content_manager_create_voice_experience.md`'s single hit, at `:16`, is "fold them together" — a
     different sense of the word. Carry it. It is what stops the second run rewriting the owner's answers.

     HOW THE OUTPUT READS — 5 of 8. `## Tone` (4: design, uxd, content, srs) · `## How it reads`
     (1: visual_experience). Four to six lines: the register, the cold reader named, and the one
     thing worth saying twice. Three of the five point at the instance's writing bar from inside
     this section rather than restating a bar (uxd, srs, visual_experience); design and content
     state the register here and cite no bar anywhere.

     WHAT GOES TO THE OWNER INSTEAD OF BEING SETTLED — 4 of 8, verbatim in all four (content,
     visual_experience, voice_experience, writing_bar), and the same four are the only ones that say
     "you do not interview" in so many words. It names the KINDS of thing that route out, not the
     items, and it closes with the counterweight — settle it yourself where the evidence answers,
     because a question asked with the answer already on disk spends the owner's attention on
     something the run could have read. The other four route to the owner inline, inside whichever
     section raised the item.

     TRACE TO THE UPSTREAM DOCUMENT — 3 of 8. `## Every entry cites its relation to the PRD` (uxd) ·
     `## Every requirement cites its relation to the PRD` (srs) · principle 12, "Every decision cites
     its relation to your input" (prd). Carry it where the artifact derives entry-by-entry from one
     named upstream document; it is what makes the downstream template's `## Traceability` fillable.

     A MACHINE GATE — 2 of 8 have one (`## The machine gate — lint, and what "clean" actually means`
     in design; `## The machine gate` in visual_experience), and 2 of 8 state its ABSENCE as its own
     section (`## The checkability bar — there is no machine that can check this, and that is the
     whole risk` in content; `## There is no machine that can check this, and what that costs you`
     in voice_experience). The remaining 4 say nothing either way. State one or the other. An
     unstated absence reads as an oversight, and the two that name it also name what stands in the
     gate's place.

     THE ANTI-DEFAULT DISCIPLINE — 2 of 8 (design, uxd). Where the artifact's failure mode is a
     plausible generic answer rather than a wrong one.

     THE TERMINUS BOUNDS THE <X> — 2 of 8 (uxd, srs), both product-facing and both binding the
     project's Agari as a scope boundary and explicitly not as a source of requirements.

     ATTRIBUTION — 3 of 8 (design, uxd, content). Where the lens's substance is borrowed from
     outside this house, the credit goes in the shipped file with what was taken, from where, and
     the date it was read — `<CORE>/../skills/cdo/.claude/skills/product-design/prompts/rich.md:309-321` is the model. Owed only
     where something was actually borrowed.
     ========================================================================= -->

<!-- ============================ THE OPEN CHOICES ============================
     Divergences measured across the eight on 2026-08-19 that no doctrine resolves. Each is a real
     choice, not a defect to copy or avoid. Delete this block from what you author.

     1. NUMBERED PRINCIPLES OR NAMED SECTIONS — the largest structural split in the house, and it
        forks the carrier skill's wording with it. `cpo_create_prd` uses `### 1 —` … `### 12 —`
        under `## The twelve principles`, preceded by a `## Contents` index; the other seven use
        named `##` sections only and carry no index. It is the only file in the set with any `###`
        heading at all. THE CARRIER SKILLS FORK TO MATCH, in the same line of each:
        `skills/cpo/.claude/skills/product-prd/SKILL.md:28` reads "a principle referenced below by number lives
        there", while `product-srs/SKILL.md:28` and `product-uxd/SKILL.md:28` read "by name".
        Numbering makes a rule citable from a companion item, a report or a cold-read finding by
        `principle 7` and nothing else; named sections survive a reorder and are readable out of
        order. NOTHING DECIDES THIS — pick one deliberately, and note the choice in the header
        paragraph so the carrier skill's
        wording is written to match rather than guessed at.

     2. A `## Contents` INDEX — 1 of 8 (prd), and it travels with item 1: an index earns its place
        over twelve numbered principles and not over nine named sections. If you number, index.

     3. NAMING THE COMPANION'S BUCKETS — 1 of 8 names them as literal section references
        (`content_manager_create_writing_bar`, which routes each kind of item to "the companion's § 1
        *Open issues*" or "§ 2 *Choices to confirm*"; `grep -c 'Open issues'` -> 6 and
        `grep -c 'Choices to confirm'` -> 8 there, and 0 in every other prompt). Five use the
        lowercase prose form — "surface it as a *choice to confirm*" — and let the skill and the
        companion template own the names. The two experience prompts use neither. Naming them is
        precise and couples this file to a shape it does not own; the prose form is loose and
        survives a rename. Whichever you pick, do not do both in one file.

     4. HOW MUCH OF THE STACK THE HEADER RECITES — the carrier declaration is 8 of 8, but its length
        runs from two sentences to a paragraph naming the doctrine, both templates, the skill, and
        which of them are carriers at all — `<CORE>/../skills/content-manager/.claude/skills/kensaiapp-writing-bar/prompts/rich.md:21-30`
        is the longest. Longer is more checkable and goes stale faster. No measured majority.

     5. THE INSTANCE'S WRITING BAR — 4 of 8 hold their own output to `system/doctrine/writing_bar.md`
        and say so by path: `cdo_create_uxd.md:409` and `cto_create_srs.md:366` at the close of
        `## Tone`, `cdo_create_visual_experience.md:174` at the head of `## How it reads`, and
        `content_manager_create_voice_experience.md:153`. A fifth names the same path because it
        AUTHORS that file. The remaining three cite no bar at all: design and content state their
        register in their own `## Tone`, and prd has no tone section among its five `##` headings.
        BE AWARE THIS IS A FORWARD POINTER IN SOME INSTANCES:
        an instance need not hold a bar on disk, and where it does not those four cite a file that
        is not there — `ls system/doctrine/` in the instance you are authoring for settles which
        case you are in.
        `skills/content-manager/.claude/skills/kensaiapp-writing-bar/SKILL.md:73-76` reads a missing bar as "this skill has
        not landed in this instance yet", so the pointer is unlanded rather than wrong. Point at it
        if your instance holds one; state the register in `## Tone` if it does not.

     6. PRODUCT SUBJECT OR INSTANCE SUBJECT — not a divergence to resolve but the cut the others
        fall along, and worth knowing before you pick moves. Five of the eight author a document
        about ONE PRODUCT (prd, srs, uxd, design, content); three about THE INSTANCE
        (visual_experience, voice_experience, writing_bar). Every count above splits along that cut
        rather than at random. The instance-subject three carry no completeness lens at all, none of
        them has `## Inputs you work from` under that name (writing_bar's `## Where the grounds come
        from` is the nearest), and the two experience prompts carry no stability rule; all three
        carry `## What goes to the owner instead of being settled`, which no product-subject prompt
        has except content, and all three carry the one-test move — as `## The altitude test` in the
        experience pair, as `## Sorting what you write` in the writing bar. If your artifact's
        subject is the instance, read those three before the five; if it is a product, read the
        five.
     ========================================================================= -->
