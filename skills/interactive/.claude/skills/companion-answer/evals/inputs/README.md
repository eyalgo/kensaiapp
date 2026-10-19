# Eval fixtures — companion-answer

Five independent trees, each staged privately per run. Notes about what a fixture is *for* live here and
never inside a fixture file: `skill-evals` feeds the fixture tree to the grader whole, so an annotation
in an ingested file is an instruction the baseline arm reads too, and a case then passes on the note
rather than on the skill.

**Every producing skill named in these fixtures is invented** — `berth-charter`, `mooring-standard`,
`ledger-standard`, `quay-rules`, `tide-tables`, `crossing-rules`, `river-survey`. None exists, none has a
launcher, and that is the point:
the skill under test must derive what it needs from the file in front of it, and a fixture naming a real
skill would let a run answer from what it already knows about that skill instead. It also means the
launcher lookup always lands on its third branch (no launcher exists), so the cases test the honest
"here is the skill and the posture it needs" rather than the easy folder match.

## The trees

| Tree | Shape | What it is for |
|---|---|---|
| `harbourlight/` | one live companion at `system/standards/`, one copy of it under a project's `docs/imported_charters/`, and a § 3 whose slot belongs to the producing role | The main path: answers into owner slots only, the copy left alone, the document itself untouched |
| `northgate/` | a settled document with **no** companion beside it; one companion-shaped file under `archive/rounds/` whose header points back at `system/standards/` | The absence path: nothing is open, and a run has to say what it searched rather than only that it found nothing |
| `ledgerworks/` | a live companion whose header is a two-role baton and **backticks no skill to re-run**; header names the document by bare filename, not by path | The degradation path: derive what can be derived, ask about what cannot, invent nothing |
| `twinfields/` | two live companions, both in the same directory, each with its own document and producing skill | The ambiguity path: list both and ask, rather than picking |
| `stonebridge/` | a live companion on `crossing_rules.md` whose item 1.1 belongs to `river_survey.md`; the survey settled with **no** companion beside it; and `core/templates/crossing-templates/` holding the survey's template **and** the crossing's own | The routing path: ask, open the other document's companion from *its* template, commit it and check it before answering the item that sent you there |

## Liveness, and why the copies are here

Two of the four trees carry a file that is companion-shaped and is not a live companion, and each is
excluded by both of the skill's filters, deliberately — so a case fails visibly whichever one a run
skips.

- **Not in a document home, one level deep.** `harbourlight`'s copy is three levels below a project card
  (`system/projects/quayside/docs/imported_charters/`); `northgate`'s is under `archive/rounds/`. Neither
  is reached by the globs.
- **Not where its own header says its document is.** Both name `system/standards/<doc>.md` from
  somewhere else.

An answer written into either is lost: no run will ever fold it in.

`northgate/archive/rounds/mooring_standard_open_issues.md` is deliberately **already answered** — both
slots carry real answers rather than placeholders. A run that treats it as live has two ways to fail
visibly: it either walks a question the owner already closed, or it overwrites their words.

## The second template in `stonebridge`

`core/templates/crossing-templates/` holds two templates, and only one of them is the survey's. The other
is the crossing rules' own — the document being walked, which already has its companion and needs no
second one. It is there so that resolving a template is a real choice: a run that takes the first file the
glob returns, or the only one it happens to notice, writes the survey a companion carrying the crossing's
header, and the case fails on the header rather than on the file count.

