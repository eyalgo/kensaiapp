# Tech Lead instruction — project-card-commands: set up and run both locked suites

**Category:** nfdr
**Behaviour:** changing
**Product root:** products/tracker17 — product-relative paths are resolved here; paths beginning `system/` or `core/` are relative to the instance change worktree.
**Scope:** Replace only the Setup and Test command values on the project card.
**Inputs read:** change_spec.md no Status line · change_design.md no Status line · project.md no Status line · ADR index no Status line, current records Accepted · NFDR Settled (version 21) · FDR Settled (version 4) · SDD Settled (version 16).

This instruction owns the implementation task and its verification for `tracker17 · tobiishi · 2026-10-29_project-card-commands`. The change's `change_spec.md` § Rules owns CP-685–CP-692; its `change_design.md` §§ 2, 4 and 5 own placement, command strategy and acceptance checks.

## Project layout

```text
<instance change worktree>/
  system/projects/tracker17/project.md    ← modified: two command values only
```

No directory, product module, helper or persistent test is created. The card owns the execution context under `products/tracker17/docs/nfdr.md:541-544`, § 8 Operational constraints. The five product parts remain those of `products/tracker17/docs/SDD.md:208-218`, § 3 The parts, and their allowed and forbidden imports remain `products/tracker17/docs/nfdr.md:166-197`, § 1.2 Forbidden imports. Placement follows the design's § 2 decision to keep this tooling in the card.

## TL Review Notes

Tech Lead decisions, 2026-10-29:

1. **Task cut:** the design has no § 3 Sub-jobs heading, but §§ 1, 4 and 5 explicitly describe a single card delta. Task 1 takes that cohesive responsibility from those sections. Splitting Setup from Test would separate the environment made from the environment used, against the spec's Request.
2. **Review-verified lane:** Task 1 uses the review-verified shape. The spec's § Out of Scope preserves every product test, and the design's § 5 explicitly makes T1–T8 temporary command checks. The value-only diff and preservation against the branch's base are checks of this change, not permanent suite assertions. Every T1–T8 criterion remains required below; this lane does not waive execution evidence.
3. **Hint placement:** the design's § 4 hint is expressed as command properties in Task 1's deliverable. There is no `# Hint:` block under Implement because the review-verified shape requires that body to be exactly `Verified by review — no test.` The Git-root project selection, quoting, locked runs, separate processes and `&&` approach are all retained.
4. **Gate correction:** use the edited card's actual Test value in Task 1's gate. The pre-edit `pytest products/tracker17/tests/` differs from the spec's Verified Claims invocation through uv and omits the second suite by `products/tracker17/tests/conftest.py:44-59`, `_command_line_names_end_to_end` and `pytest_ignore_collect`. The required two-process meaning is also explicit in `products/tracker17/docs/SDD.md:803-806`, § 6 preamble. Do not treat a green first process as the full gate.
5. **Baseline limits:** the pre-edit `pytest products/tracker17/tests/` was invoked once from the change-worktree root and collected 2,698 tests under Python 3.15.0. It was interrupted after the permission failures were diagnosed, exiting 2 with `38 failed, 1948 passed, 31 errors in 236.20s`; this is an incomplete run. A focused diagnostic, `pytest -q products/tracker17/tests/integration/test_label_listener.py -x`, exited 1 with `1 error in 0.05s`: `socket.bind` raised `PermissionError: [Errno 1] Operation not permitted`. This is evidence of that invocation's inability to bind the loopback listener, not evidence of a green baseline or of a regression introduced by the card edit. Task 1 stays review-verified; these failures are not deferred product tests that qualify for the red-at-baseline lane.
6. **Second-process lock edge:** T7 additionally exercises a lock becoming stale between the two actual test processes. The spec's CP-690 requires every invocation to refuse drift, and checking only the first process leaves the second process's refusal unobserved. The temporary first-suite mutation for this check changes the scratch manifest after its tests pass, with the second suite otherwise intact.
7. **Coordinate clarification:** the template's product-relative default does not reach the instance-owned card. The header and commands explicitly distinguish the instance change-worktree root from `products/tracker17`, so the developer edits the card in this branch rather than a path beneath the product.

## Corrections owed while there

- Owed outside this change's reach: `products/tracker17/docs/nfdr.md:633-634`, § 10 Verification map, preamble — the statement identifying the card's Test value as `pytest tests/` with a separate end-to-end command becomes false. Replace the copied command with a pointer to the card's Test value and state that the suite gate runs both suites through that value from the change-worktree root. This carries the design's § Records this change makes false entry; the NFDR is an input and is not edited by this task.

## Gate environment inputs

The inventory below records the change-worktree repository, not another product's tree. No product decision supplies an environment override or an amd64 requirement: the search `rg -n 'environment:|amd64|owners.mac|CI|runner' products/tracker17/docs/adr/*.md products/tracker17/docs/nfdr.md products/tracker17/docs/SDD.md` found no such decision. NFDR § 8 contains no environment entry. The Python image comes from the packet's § Provisioning; no CI version is supplied as a tag.

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git ls-files at the instance change-worktree root returned 6064 tracked paths. Top-level entries: .claude, .env.example, .gitignore, .providers.toml.example, .python-version, .telemetry.env, AGENTS.md, Brewfile, CLAUDE.md, Containerfile, README.md, about, core, docs, kensaiapp.md, products, pyproject.toml, skills, system, uv.lock. No tracked CI configuration was found. Reviewed the non-trail YAML/TOML/JSON inventory, Containerfile and .claude/workflows: the Containerfile is a local execution image; the two workflow scripts are skill-eval and eval-fix workflows, not CI jobs. products/tracker17/pyproject.toml configures the product's local tools. No CI runner or version matrix is configured."
  },
  "decisions": {"override": null, "amd64": null},
  "candidates": [
    {
      "language": "python",
      "image": "docker.io/library/python",
      "image_source": {
        "root": "core",
        "file": "doctrine/engineering/languages/python/environment.md",
        "anchor": "Start a container from the official Python image, `docker.io/library/python`, tagged with CI's"
      }
    }
  ],
  "guest": null
}
```

### Task 1: Replace the paired Setup and Test values (`system/projects/tracker17/project.md`)

**Dependencies:** None

**What to build:** Make the card create the product's locked environment and run both complete suites in that environment, within CP-685–CP-692.

- Setup uses `uv sync --locked`. Its quoted project argument is derived from Git's top-level directory plus `products/tracker17`, so either permitted working directory selects the same product without a fallback warning. Do not use a fixed checkout path.
- Test runs from the instance change-worktree root. Select `products/tracker17` explicitly on each locked `uv run` invocation. Run `products/tracker17/tests/` and `products/tracker17/tests/e2e/` in separate pytest processes joined by shell `&&`, as the design's § 4 hint requires.
- Retain the design's absent-browser boundary: Setup fetches no browser. The prerequisites remain `products/tracker17/README.md:89-109`, § Running the tests. No command hides a missing browser or a failing layer.
- Replace only each command value before its existing trailing HTML comment. Preserve all other bytes of the card and every product file, including the README, tests, manifest and lock, as the design's § 2 and the spec's CP-691–CP-692 require.

#### Deliverables verified by review

Each row is a required verdict with command output or a diff reading. T1–T8 are the design's § 5 identifiers. All mutations below are in independent disposable Git clones and never in the change worktree or the product's primary checkout.

| Check | Deliverable and pass criterion |
|---|---|
| T1 — fresh Setup | Extract the actual card value. Execute it through `/bin/sh` from a fresh clone root and independently from `products/tracker17` in another fresh clone. Begin each with neither root nor product `.venv`. Each exits 0, creates only the product `.venv`, creates no root `.venv` or `products/tracker17/products/`, and emits no stderr line beginning `warning:`. Include a clone path containing spaces. CP-685–CP-686. |
| T2 — stale Setup | In independent clones, change only scratch `requires-python` from `>=3.11` to `>=3.12`, leaving the lock alone. Execute Setup separately from each permitted directory. Each exits non-zero, and the lock's bytes before and after match. CP-687. |
| T3 — actual values | Read both extracted values: Setup is not `none` and uses locked uv synchronization; Test uses uv and does not begin with `pytest`. Both test invocations independently select the product and include `--locked`. No `--frozen`, selection flag, retry, skip, ignore, success fallback or output suppression appears. CP-685, CP-688–CP-690. |
| T4 — clean full run | After fresh Setup, execute the actual Test value from the clone root. Both complete suites exit 0 and produce their own summaries, covering unit, integration, architecture and end-to-end tests. No command-driven deselection or skipped layer is accepted. Compare lock bytes and require empty `git status --short -- products/tracker17` afterwards. The example's 2,698 and 121 counts are measurements, not fixed count assertions. CP-689–CP-690. |
| T5 — failing tests | In separate scratch clones, make one otherwise collected unit test fail, and one otherwise collected end-to-end test fail. Execute the entire Test value in each clone. Both exit non-zero. The end-to-end case has a green first suite and reaches the second process. The unit-failure case need not run the second suite. CP-689. |
| T6 — collection refusal | Independently introduce a collection error in the first suite and in the second suite; each full Test value exits non-zero. Independently make the first suite and the second suite collect no tests, retaining the collection/import fixtures and keeping the other suite healthy; each full Test value exits non-zero. Never add a success fallback for pytest's empty-suite status. CP-689. |
| T7 — locked Test | With a scratch-stale manifest, run the full Test value and require non-zero before test collection or execution, with byte-identical lock. Also let a temporary first-suite test make the scratch manifest stale after the first suite passes: the second locked process must refuse before collecting its suite and leave the lock byte-identical. T3 separately checks both flag occurrences. CP-690. |
| T8 — edit boundary | Compare against the branch's own merge base with `main`. Only the two command-value spans may differ on the card; both trailing comments and all other bytes match. The change diff contains only this card and the change's own records, with no diff under `products/tracker17/`. CP-691–CP-692. |

#### Implement

Verified by review — no test.

#### Verification gate

Run commands from the instance change-worktree root unless a different directory is specified. `$WORKTREE` denotes that root. First inspect the edit boundary:

```sh
git diff "$(git merge-base main HEAD)" -- system/projects/tracker17/project.md
git diff "$(git merge-base main HEAD)" -- products/tracker17
git diff --name-only "$(git merge-base main HEAD)" -- . ':!system/projects/tracker17/project.md' ':!system/projects/tracker17/journey/tobiishi/2026-10-29_project-card-commands/**'
git diff --check
```

Pass: the first diff has exactly the two value-only changes; the next two diffs and `git diff --check` print nothing. For T8, additionally compare the before/after card bytes with only the two command-value spans masked; a line diff alone does not prove byte preservation.

For the disposable acceptance checks, make a fresh clone at the implementation commit using this recipe. Repeat the recipe for independent scenarios rather than repairing a deliberately mutated copy into the clean-run evidence.

```sh
WORKTREE="$(git rev-parse --show-toplevel)"
CHECK_SHA="$(git rev-parse HEAD)"
CHECK_ROOT="$(mktemp -d)"
git clone --quiet "$WORKTREE" "$CHECK_ROOT/checkout with spaces"
git -C "$CHECK_ROOT/checkout with spaces" checkout --quiet "$CHECK_SHA"
```

In each clone-root subshell, extract the actual values without their trailing comments:

```sh
SETUP_COMMAND="$(sed -n 's/^\*\*Setup command:\*\*[[:space:]]*//p' system/projects/tracker17/project.md | sed 's/[[:space:]]*<!--.*$//')"
TEST_COMMAND="$(sed -n 's/^\*\*Test command:\*\*[[:space:]]*//p' system/projects/tracker17/project.md | sed 's/[[:space:]]*<!--.*$//')"
```

Use `/bin/sh -c "$SETUP_COMMAND"` for each Setup check, with output and status retained. For the product-directory case, extract at the clone root first and execute `( cd products/tracker17 && /bin/sh -c "$SETUP_COMMAND" )`. Run the clean full-suite check and each negative Test check through `/bin/sh -c "$TEST_COMMAND"` from the clone root. Run `shasum -a 256 products/tracker17/uv.lock` before and after each lock-sensitive check, and `git status --short -- products/tracker17` after the clean run. Scratch failure and collection mutations must be shown to affect a collected test in the intended suite.

Keep every clone execution inside a subshell, so the controlling shell remains outside it. Once its outputs are read, remove that run's disposable directory from outside with `rm -rf "$CHECK_ROOT"` in its own command, per `<CORE>/roles/CROSS_ROLE.md` § Every seat.

Pass: all T1–T8 criteria have recorded verdicts; the clean actual card command runs both suites successfully; negative cases retain non-zero exits; the product's tracked bytes and lock remain unchanged in the clean run. No green result is inferred from a permission refusal or an interrupted run.

The developer's closing suite uses `<CORE>/prompts/gate_suite.md` with this plan's sourced inputs and the edited card. Retain the tool's actual result; this task's disposable command checks supply the separate fresh-Setup, mutation and diff evidence.
