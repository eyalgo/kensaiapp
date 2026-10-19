# shukuba-refine eval fixtures

Read-only inputs for `../evals.json`. Each run gets its own staged copy of this tree. This README is
not copied, which is why every note about a case lives here and never inside a fixture file: the
executor reads fixture files whole, and a note there would hand the baseline its answer.

Each folder is one project, and also its product root: `project.md`, `agari.md`, `journey/`, `docs/`
and `src/` sit side by side. Staging rewrites `Product path:` to the staged copy.

**Fixture names carry no date.** `core/tools/check_vendor_neutrality.py` flags any dated journey stem
under `.claude/skills/` and `skills/`. The skill never reads a date out of a key or a slug.

**No fixture has git history.** No commit anywhere names a fixture key; keep it that way. Every unit is
resolved by its folder, `journey/tobiishi/trail/<key>/`, and its station by the one station file that
names the key. So a correct run states the developer's closing commit as absent. In every fixture the
unit's station is already in `shukuba/trail/`, and no station is open.

## `tidewell/` — cases 1 and 2

A clean seal: every finding is non-blocking or already closed, there is no deferred file, the SRS has
no companion, and the active seed is 3 of 8, its next station's bar naming nothing a later station lands. The two pooled
seeds stay: one waits on a feed that does not exist yet, the other is the owner's own acts.

- **The trap:** the design audit's `skill-general` finding is about the machinery. It is not the PM's
  to move or to recommend.
- **Case 1** runs this fixture as the Principal PM. The correct result is a halt that names the `pm:`
  prefix or the `pm` subagent, with nothing written.
- **Case 2** runs it as the PM. The correct result:
  - the seed becomes `alerts-reach-the-harbour/seed.md`, holding both files;
  - the recommendations file reads `Nothing to recommend.`;
  - the report lists all three seeds as considered, and states the deferred file and the closing commit
    absent.

## `ferrule/` — case 3

The sealed unit built the cancel operation that `src/ferrule/billing/refunds.py`'s deferral waited on.
It neither took the FR-5 refund nor fenced it out, and the docstring now reads "owed and unassigned".
The specs audit flags this as blocking.

The fix belongs in the route, not the code, and it is not a new seed. It is **modify a seed**: the
first unwalked station that actually triggers a cancellation, `customer-cancels-from-the-app`, is
amended to carry the refund. `customer-sees-pickup-status` and `pickups-are-reported-weekly` trigger
none. The SRS already states FR-5 fully, so no companion item is owed. There is no deferred file,
because the deferral lived in a code comment.

## `quillmark/` — case 4

FR-2 uses "front matter" and never states the set. The set lives only in the docstring of
`src/quillmark/manuscript/front_matter.py:1-9`. Nothing is broken.

The move is **raise a companion item** on the SRS: open `docs/SRS_open_issues.md` from the SRS
companion template, with the item under § 3, "Raised from downstream". The SRS is not edited, no seed
is cut, and nothing is recommended. The item names FR-2 and the docstring, and its **Tracked by** line
names the seed `submissions-are-accepted` by path. It names no unit; the report is where the unit is
cited.

## `brackenway/` — case 5

The prompt invites the loop ("pick the seed you think is best"). The active seed is 3 of 8, and its next
station's bar names nothing a later station lands. It is the only pooled seed that is both.

The pool:
- `project-setup` is fully ticked, so it goes to the Scrum Master as a seed to retire;
- `every-edge-of-the-map-path` is blocked by its own text;
- `store-listing` is the owner's acts;
- `offline-maps-described` blocks nothing until `offline-sync` is cut.

The correct result is **no move**. The active seed stays at the root, now as a folder, and nothing is
un-picked, re-picked or opened.
