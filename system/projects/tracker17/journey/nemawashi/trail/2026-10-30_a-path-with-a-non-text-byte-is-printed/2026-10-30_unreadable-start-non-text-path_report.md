# 宿場 Shukuba refine — `2026-10-30_unreadable-start-non-text-path`

*Unit `2026-10-30_unreadable-start-non-text-path`, sealed Tobiishi, reviewed 2026-10-30.
Station `2026-10-30_unreadable-start` (root). Seed `2026-10-30_a-path-with-a-non-text-byte-is-printed`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-30_unreadable-start` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | the companion item raised |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1, 3 | Moves row 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking, 4 change-local, 1 skill-general (`specs-states-test-shape`, the machinery's, not this route's); the proof-rule gaps were closed by the tests (Considered row 3) |
| flow findings | `flow_findings/development-design.md` | 0 blocking, 2 change-local; the page's missing `\udce9` check was added and mutation-tested, 154 cases fail on that break (Considered row 3) |
| flow findings | `flow_findings/development-content.md` | 0 blocking, 1 change-local: a sentence in `change_text.md`, which is not published (Considered row 3) |
| flow findings | `flow_findings/development-plan.md` | 0 blocking, 2 change-local; the real-start route checks exist (Considered row 3) |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking, 3 change-local; the undelivered cases were repaired by code-integrity, and the `__version__` one is Considered row 6 |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`; no product bug, tests strengthened; nothing left unfixed; its one call (a `PUT` gets the page) is the spec's reading and needs nothing |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM (line 9): dependency audit did not run, the NFDR names none. QC-40 already says so, no companion owed (Considered row 5) |
| developer's closing commit | `<a commit not in the public history>` | page cases merged, harness takes a working directory; the byte-named directory case skips on this machine and passed in code-integrity's Linux run |
| deferred decisions | `deferred_decisions.md` | entry 1, failed-action path form, `Owner: none`: carried by the seed's `failed-action-path` since the last refine; entry 2, QC-40 graph-listing moment, `Owner: none`: owned by QC-40's own review (Considered row 4) |
| the closing commit's `Deferred:` lines | absent — `<a commit not in the public history>` holds none | none to route |
| corrections owed | absent — `tl_instruction.md` has no such section | none |
| work handed on | `change_spec.md` § Out of Scope | failed-action message → the seed's `failed-action-path`; the rest only fences (Considered row 7) |

## Upstream

`git log --since=2026-10-30T15:47:01+01:00 --name-status -- products/tracker17/docs/` printed nothing before this run's companion commit. `find products/tracker17/docs -name '*_open_issues.md' -not -path '*/trail/*'` printed nothing: no live companion until this run raised one.

## Held

None. `chain-tracker17-state.json` has `ended: settled`, `pending` null; `journey/tobiishi/` holds only `trail/`, so no open unit. `chain-change-tracker17-state.json` is live on this key only for this refine step.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a seed | `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed` | The next station's bar rests on one of two clauses that disagree, so the seed logs the wait, says the line is re-cut if the other clause stands, and its Out no longer rules the fold out. The bar is unchanged, so this is not a re-aim | `products/tracker17/docs/CONTENT.md:135-139`; `products/tracker17/docs/CONTENT.md:266-267`; `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed` (line 23) | `188677651` |
| raise a companion item | `products/tracker17/docs/CONTENT_open_issues.md` § 3 | Two clauses of a settled document disagree at a site that exists: one form in every place a path is written, against error text exactly as the system reported it. The last refine read only the first clause | `Site._report_failure('Could not save.', OSError(92, 'Illegal byte sequence', os.fsdecode(b'/tmp/caf\xe9')))` at `products/tracker17/web/routes.py:1327-1332` prints `OSError: [Errno 92] Illegal byte sequence: '/tmp/caf\udce9'` | `9ad88f3ac` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-30_unreadable-start` | All six reached-when lines hold, so the close is owed to the Scrum Master, and this run does not make it | Bars 1–3: `products/tracker17/tests/unit/test_unreadable_message.py`, `products/tracker17/tests/integration/test_unreadable_path.py`, `products/tracker17/tests/integration/test_unreadable_start.py`; live, `main._unreadable_line` prints `/tmp/caf\xe9/data` and `web.UnreadableSite` builds. Bar 4: `code-integrity-report.md` § Test evidence (293 failed, 12 passed on the merge base's production files). Bar 5: `git diff --name-status ce9e51683 6591e5482 -- products/tracker17/tests products/tracker17/docs` shows three added test modules only. Bar 6: the card's two commands in a disposable clone at `6591e5482`: 3272 passed, 2 skipped; 122 passed |
| `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed`, line `failed-action-path` | Reachable where it stands once the companion item is answered with the lean: the site exists and writes `\udce9` today, no test holds it, and the work is that station's own. It is not reordered, because the wait is on a document and not on a later station | Clauses: `products/tracker17/docs/CONTENT.md:135-139`, `:266-267`. Site: `products/tracker17/web/routes.py:1327-1332`. `git grep -n 'report_failure' -- products/tracker17/tests` prints nothing |
| the unit's change-local flow findings | Each ended with the unit: real-start route checks exist, the page holds no `\udce9`, and the terminal-encoding sentence sits in a record no reader of the product sees | `products/tracker17/tests/integration/test_unreadable_start.py:249-256`; `code-integrity-report.md` § Test evidence; `flow_findings/development-content.md` |
| `products/tracker17/docs/nfdr.md` QC-40, graph-listing moment | Entry 2's `Owner: none` is wrong in effect: QC-40 says this reading records the feed as down and the moment as still owed, and raises no discrepancy | `products/tracker17/docs/nfdr.md:399-418`; `deferred_decisions.md` entry 2 |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already states that no audit command exists, as earlier refines found, so the line asks for nothing it does not say | `security-report.md` (line 9); `products/tracker17/docs/nfdr.md:399-418` |
| `__version__` on the product's modules | No move, and no basis for a call on this evidence: no product module carries it, the change added no module, and the clause's own evidence is all core's tools | `git grep -c '__version__' -- 'products/tracker17/*.py'` prints nothing; `<CORE>/doctrine/engineering/languages/python/conventions.md:148-154` |
| `products/tracker17/docs/CONTENT.md` RN-33, a surrogate outside U+DC80–U+DCFF | The form does not occur: the machine's decoding yields only that range, so no carrier | `os.fsdecode(bytes(range(128, 256)))` → min `0xdc80`, max `0xdcff`, as the last refine measured; `change_spec.md` § Out of Scope |

## Absent

The closing commit's `Deferred:` lines and `tl_instruction.md` § *Corrections owed while there*: the unit produced neither. No other input was unreadable.
