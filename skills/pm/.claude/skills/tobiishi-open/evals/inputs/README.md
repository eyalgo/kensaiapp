# tobiishi-open eval fixtures

Read-only inputs for `../evals.json`. Each run gets its own staged copy of this tree. This README is
not copied, which is why every note about a case lives here and never inside a fixture file: the
executor reads fixture files whole, and a note there would hand the baseline its answer.

Each folder is one project and also its product root. Staging rewrites `Product path:` to the copy.

**Fixture names carry no date.** `core/tools/check_vendor_neutrality.py` flags any dated journey stem
under `.claude/skills/` and `skills/`. The skill describes a station and a seed by their dated form
(`<YYYY-MM-DD>_<slug>.md`); these fixtures are undated. A with-skill run that fails to see an open
station for that reason is a finding about the skill, not about the fixture.

**No fixture has git history, and the staged copy sits in a gitignored workspace.** The skill's
Step 6 commits on the current checkout; here that commit is expected to fail or be skipped. No
assertion reads a commit — every one reads `run_delta.json` or a written file.

## `lanternfold/` — cases 1 and 5

The motivating failure. The station's *What it is* says **move** the header set into the renderer,
which reads like a refactor. Its *Reached when* says `render_welcome` and `render_goodbye` stop
returning a bare `str` and return the body with the header set — a changed signature on two public
names, so the change is `changing` and cannot be a `refactor`. The change is driven by NFDR QC-4, so
`nfdr` is the truthful category; `feature` also passes, `refactor` never does.

- **Case 1** runs it as the PM.
- **Case 5** runs it as the Principal PM: the correct result is a halt that names the `pm:` prefix or
  the `pm` subagent, with nothing written.

## `quarrystone/` — case 2

A true refactor: three private helpers move to a private module, and every public name and signature
stays. `refactor` + `preserving` is correct here, so the case guards against the teaching tipping a
run into calling everything `changing`.

## `bellhaven/` — case 3

New behaviour: `export_csv` and a new route. `feature` + `changing`.

## `emptyfield/` — case 4

No seed, no station, no product documents. Step 4's last row: the next move is `seeds-from-idea`,
the Principal PM's, and nothing is written. `seeds-from-product-docs` is wrong — there are no documents.
