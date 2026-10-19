# kensaiapp-writing-bar eval fixtures

Read-only inputs the eval prompts (`../evals.json`) point at. A `skill-evals` run copies this tree
into `../workspace/iteration-N/<case>/<config>/inputs/` and the run works in that private copy, so the
fixtures here stay byte-identical across runs (`skills/experimental/.claude/skills/skill-evals/scripts/stage_fixtures.py`,
module docstring).

**All eval annotations live here, never inside a fixture file.** The harness feeds a fixture to the
graded model whole, comments included — a note inside `kensaiapp.md` or `michi.md` saying what the case
exercises hands the model its answer, and a run then passes on the annotation rather than on the
skill. This file is the one exception the harness never copies: `stage_fixtures.py` drops the
inputs-root `README.md` from every staged tree (`ignore_annotations`), so nothing written here reaches
an executor.

Paths in the prompts are repo-relative, and staging rewrites each one to the run's own private copy.

## What each fixture holds, and why

Each fixture is an invented instance, not a real one: a `kensaiapp.md` with its "What this is about"
section, a `system/michi.md`, and a `system/doctrine/kensaiapp_doctrine.md` — the three inputs
`kensaiapp-writing-bar` reads before it writes anything. None of them states a writing bar or hints at
what the answer should be; the grounds are there and the judgment is the skill's.

**The bar is the run's output** (`../../SKILL.md:23`). These fixtures are cut against that premise:
writing one is the outcome on every fixture whose identity and Michi are settled, and the only case
that ends without a bar is the one whose identity is still a placeholder, where the skill halts
(`tidepool`). Nothing sits underneath a bar — core states none — so a run that wrote no bar has left
the instance with nothing binding how its documents read. What separates the fixtures is what each
one gives the bar to be grounded in, and what each one puts in the run's way.

The loop files in the re-entry fixtures — every `writing_bar.md`, `writing_bar_open_issues.md` and
`trail/writing_bar/cycle-N.md` here — are written in the shape the two templates under
`<CORE>/templates/writing-bar-templates/` currently state: the bar as § 0 *Where this sits*, § 1 *The
bar*, § 2 *Deliberate absences* (omitted where there are none) and § 3 *Review notes*; the companion
as § 1 *Open issues* and § 2 *Choices to confirm*. An assertion that anchors on a section number is
anchoring on those.

### `northbay/` — cases 1 and 7

An internal instance: release tooling for five people, read by the four colleagues who have the repo
open while they read it. Its grounds are modest and that is the point — Way 1 (`one-head`) constrains
a checklist's length rather than a sentence's, and nothing anywhere in the fixture fixes what *must* /
*should* / *may* mean here. A run that writes back only what northbay handed it produces a bar with
holes in it; the skill asks for the plain general answer where the instance holds nothing particular,
so the case is graded on the parts that have no fixture sentence behind them.

Case 7 reuses the same fixture with a prompt that never puts the run in Content Manager posture. It
names the instance root anyway, so a run that fails to halt writes into its own staged copy rather
than into whatever directory it happened to start in.

### `deepwell/` — case 2

An instance whose documents leave with a published replication package. Its reader is a referee or a
stranger with no access to the lab and no way to ask a follow-up question, and the journal's
replication policy — carried in its domain doctrine — binds what a claim about a result may say. The
grounds here are unusually rich, so this is the case that measures whether the rules written are
*traced* to them rather than being general writing advice with the instance's name on top. Where the
trace is recorded is either place the stack allows: beside the rule in § 1, or as an entry in the
bar's § 3 *Review notes*, which is where a rule's *why* lands
(`prompts/rich.md` § *Sorting what you write*).

### `saltmarsh/` — case 3

An instance that wants **one rule written down and not much else**: the owner's note at
`owner_brief.md` asks that a document stating a time states its timezone, says he is not convinced
much needs writing down here, and says plainly the rule should hold everywhere rather than only here.
Two pulls in one fixture, and the skill answers both: the rule is written into saltmarsh's bar because
saltmarsh needs it, *and* it is raised in the companion as a rule every instance may want. They are
not alternatives, and neither the owner's scepticism nor the rule's portability is a reason to end the
run without a document. The bar also has to be stated whole rather than as the single addition the
owner asked for, which is why the third assertion looks for a rule that is not the owner's.

### `tidepool/` — case 4

The one fixture that ends with no document: a freshly stamped instance whose `kensaiapp.md`
§ "What this is about" is still the template's unfilled sentence, whose `system/michi.md` is still the
setup PLACEHOLDER block, and whose domain doctrine is still the STUB. A bar derived from a placeholder
would bind every document in the instance and rest on nothing, so the skill **halts** and writes
nothing — naming the file it found and saying that step 2 (`kensaiapp-michi`) has to land first
(`../../SKILL.md:117-118`).

What the case measures is that the halt is a halt and not a shrug: nothing on disk, and a report that
names the placeholder file by name and what has to land before this run can be repeated. A capable
baseline handed the same directory writes a general style guide from nothing, which is the
discriminating signal. Note that the absence cannot be checked alone — a run that did nothing and said
nothing would satisfy it — so the second assertion carries the positive half, and it is nuanced
because a halt leaves no artifact for a pattern check to read.

### `millrace/` — case 5

`northbay` mid-loop: a `writing_bar.md` an earlier round wrote (Version 1, Status Draft, written for
the colleague with the repo open), the companion carrying that bar's reader for sign-off as a § 2
*Choices to confirm* item, and a `trail/writing_bar/cycle-1.md` from the round before. The owner's
override **moves the reader** — the checklists now go to a vendor's duty engineer who cannot open the
repo and cannot ask — so the fold has to revise the bar in place rather than write a new one or leave
it alone. The existing `cycle-1.md` is what makes the next cycle `cycle-2`; a run that always writes
`cycle-1` overwrites a record. One item in the companion's § 1 *Open issues* is left unanswered on
purpose, so the round ends OPEN, the bar stays `Draft`, and the drop rule is testable on both halves
at once.

Note what a re-entry fixture cannot do: it hands the run the skill's own structure as input, so a
capable baseline continues that structure too. Take this case as a with-skill reliability guard —
cycle numbering, the whole-copy, the drop — and read discrimination off the fresh-create cases.

### `harbourgate/` — case 6

`northbay` again, plus a `system/doctrine/writing_bar.md` already on disk — and no companion and no
trail, so it is a bar written by hand before this loop existed. The prompt is the pressure: the owner
says it does not earn its place, believes core holds a bar that would bind in its stead, and asks for
it to be taken out.

The skill's answer is that it never removes a writing bar, and that the call belongs to the owner
alone — removing that file leaves every document in the instance with no bar at all, so no run makes
it on its own reasoning (`../../SKILL.md:179-181`). So the file stays — revised, reworded, extended,
whatever this run's reading calls for, but not deleted and not cut down to a stub, which is the same
removal with a file left behind. The removal request goes back to the owner in the companion, with
what it would cost said out loud. A baseline told to take a file out takes it out.

The owner's premise in the prompt is wrong on purpose: core holds no writing bar, so there is nothing
underneath to fall back on. Saying so is part of the answer the second assertion looks for.

### `fernhollow/` — case 8

`northbay` further along the same loop: a bar at Version 3 written for the vendor's duty engineer, a
trail holding `cycle-1.md` and `cycle-3.md` — `cycle-2` was removed by hand, which is the gap the
numbering rule exists for — and a companion carrying **only a § 2 "Choices to confirm"**. Two things
are loaded into that one file.

The first is the slot name. Every filled slot in it is labelled `Confirm or override:`, and the file
contains no `Answer:` slot at all, so a run that fires its consume detection on a slot literally
named "Answer" reads the companion as untouched and writes no trail cycle. What counts as an answer
slot is the companion template's, read from its current shape (`../../SKILL.md:215`), and this is the
fixture that tells the two readings apart.

The second is the residue. The owner's override on 2.1 settles one case and leaves another open —
the source-naming rule stays on a release record, comes off a checklist, and "keep it where the
number would be acted on" fixes nothing for anything else. An answer settles its item only when
nothing about what binds is left ambiguous (`prompts/rich.md`
§ *On a re-run — fold, don't re-author*), so the item still drops and the residue comes back as a
**fresh** item with an empty slot. Two failures are in scope and they point opposite ways: keeping
the answered item alive with the owner's words beside it, and deleting the companion as though the
override had settled everything. The numbering is the third thing graded — the highest on disk plus
one is `cycle-4`, where the count plus one is `cycle-2` and a naive next-after-the-first is `cycle-3`,
which would overwrite a record.

### `quarryside/` — case 9

`northbay` mid-loop with **nothing answered**: a bar at Version 2, a `cycle-1.md` in the trail, and a
companion whose two slots — the § 1 item's `Answer:`, the § 2 item's `Confirm or override:` — are both
empty. The owner re-ran the skill without having answered anything, and the prompt says nothing about
answers either way.

A companion with no slot filled is not consumed: no trail cycle, nothing to fold
(`../../SKILL.md:229`), and a re-run that folded no answer and changed no document touches no disk at
all (`../../SKILL.md:243-245`). So the whole delta is empty, and the round's only output is the
report. That makes this the one re-entry case whose positive check has to be nuanced — there is no
artifact for a pattern check to read, by design. The failure shapes are the ones a capable model
reaches for on its own: improving the bar, bumping its `Version:` with nothing folded, or rewriting
the companion to restate what is still open.

### `windlass/` — case 10

`northbay` one round from done: a bar at Version 3 / Status `Draft`, a trail holding `cycle-1.md` and
`cycle-2.md`, and a companion whose every item is answered with nothing ambiguous left in either — a
§ 1 answer that fixes the rule's reach and its check (name the role, never the person) and a § 2
`confirm`. The prompt says the owner committed the file, which is what keeps the round off the
first-closing-touch branch: the gate at `../../SKILL.md:163-166` fires on a *dirty* companion, and an
executor here has no git to check with, so the fixture's own prompt settles it rather than leaving
the run to guess.

What the case measures is the two-sided close. The companion is removed — the done signal — and
retired whole to `cycle-3.md` first, since the removal destroys the original. And the bar itself is
rewritten in the same round: the answer folded into § 1, the `Version:` bumped, and the `Status:`
line moved to `Settled`, because the Status follows the companion's absence rather than a tally of
answers (`../../SKILL.md:194`). A bar left at `Draft` beside a companion that is gone is exactly
the disagreement that staging the bar on every commit-building run exists to prevent
(`../../SKILL.md:250-252`) — and it is the failure this case catches. Note the limit: an eval executor
builds no commit, so the `--add` itself is not observable. What is observable is the state the run
leaves on disk, which is what the staging rule is for.

Note the exception the same bullet carries, and what it means for the suite: the run that halts on a
placeholder identity writes no bar, so there is nothing to stage and an `--add` on a missing path
would halt the builder. Case 4 (`tidepool`) is that run, and no assertion there asks for a staged or
written bar.

## Three things a run of these evals should know

**`<CORE>` still resolves to this repo's own `core/`.** A staged fixture is an instance whose doctrine,
prompt and templates are the ones in this repository. That is deliberate: the skill under test reads
`prompts/rich.md` and the two writing bar templates, and a fixture copy
of those would be a second copy free to drift.

**A fixture carries a `kensaiapp.md`, because the skill reads one** — its first input is
`kensaiapp.md` § "What this is about".

**Every case is staged with the whole fixture tree, so a same-named file from another fixture is not
this run's output.** `stage_fixtures.py:99` copies all of `inputs/` into each case's staged root, so
`harbourgate/system/doctrine/writing_bar.md` sits in the tree for case 1 as well, and
`millrace`'s companion sits in the tree for case 7. An assertion that reads "no such file
exists anywhere" means *not produced by this run* — check `run_delta.json` and `outputs/`, never a
walk of the staged inputs. That is how it has already been graded: the posture-halt case (then case 5)
passed with-skill at 1.0 in iteration-1 with `millrace`'s `writing_bar_open_issues.md` in its
staged tree, on the evidence "run_delta.json shows empty created[], modified[], deleted[] arrays".
