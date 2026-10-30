# 根回し Nemawashi refine — `2026-10-29_the-suite-runs-on-uv`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-10-29_the-suite-runs-on-uv` at `6720fc607`,
and the pool re-read behind it, 2026-10-30. The slug came from the caller: "answering the retired seed 2026-10-29_the-suite-runs-on-uv".*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | route across projects | Principal PM | none — a `principal-pm:` session, on `2026-10-29_project-card-commands #2` | — | `2026-10-29_project-card-commands #2` |
| 2 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh nemawashi-pick tracker17` | — | the pool (`2026-10-11_protect-saved-data`) |
| 3 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 2 | row 2 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 3 | row 3 |

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-10-29_uv-lock-and-pins-test` — Nothing to recommend. | read | none | The file carries no item. | `trail/2026-10-29_the-suite-runs-on-uv/2026-10-29_uv-lock-and-pins-test_recommendations.md:L8` |
| `2026-10-29_readme-on-uv` — Nothing to recommend. | read | none | The file carries no item. | `trail/2026-10-29_the-suite-runs-on-uv/2026-10-29_readme-on-uv_recommendations.md:L8` |
| `2026-10-29_project-card-commands #1` — retire this seed once its last station closes | ignored | none | Answered by the retire that already happened. | `6720fc607` (`retire: nemawashi/2026-10-29_the-suite-runs-on-uv → trail/`); seed checklist all ticked, `trail/2026-10-29_the-suite-runs-on-uv/seed.md:L17-L19` |
| `2026-10-29_project-card-commands #2` — settle where a change worktree runs the card's `Setup command:` | route across projects | named as next move 1 | The fix is in kensaiapp's core tooling, which tracker17 does not own, and no live seed in any project carries it. | `core/templates/project_template.md:L11` ("in the directory Test command: runs in"); `core/tools/create_change_worktree.py:L15-L16`, `:L472-L476` ("once, in the product directory"); `grep -rlnE 'create_change_worktree\|Setup command'` over live seedbeds → two hits, neither on this ask |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-10-11_protect-saved-data` | kept | — | Still owed and still advances **Works**; the uv walk touched none of it, and its pointers still hold. | `products/tracker17/main.py:L104-L113` still prints and exits on unreadable data; `grep -rln 'fcntl\|flock' products/tracker17` → only `docs/trail/sdd/self_answer-2.md`; no `UnreadableData` in `web/` or `application/`; SDD § 6 S-8 at `products/tracker17/docs/SDD.md:L1140` |

## The docs cut

Not owed: S-1 to S-7 are walked, S-8 is carried by `2026-10-11_protect-saved-data`, and the uv move the last refine named is now met (`products/tracker17/docs/nfdr.md:L352-L360`, QC-39 "The entry is met"; `products/tracker17/docs/SDD.md:L808-L1140` holds eight slices).

## Found while reading

None. The journey-link check found no dead pointer; its one malformed triple is the satellite triple `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md` already records. `products/tracker17/docs/what_left.md` reads "Nothing is left to build." while S-8 is unbuilt; that is not a defect, since the PRD's want for unreadable data (`products/tracker17/docs/PRD.md:L185-L187`) is met by the current refusal, and S-8's every-page view and second-tracker lock are design-level.

## Held and refused

None. The definition chain ended `settled` (`system/logs/chain-tracker17-state.json`), and the product has no live companion.
