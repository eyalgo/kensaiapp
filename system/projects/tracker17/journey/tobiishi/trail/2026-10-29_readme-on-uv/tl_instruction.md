# Tech Lead instruction — readme-on-uv: set up the suite with uv

**Category:** nfdr
**Behaviour:** changing
**Product root:** products/tracker17 — every path below is relative to it unless a command states another working directory.
**Scope:** Update the README's suite instructions and the two supporting descriptions. Keep the tracker's setup, headings and every other product file unchanged.

This instruction owns the task cut and verification gates for `tracker17 · tobiishi · 2026-10-29_readme-on-uv`. Read the companion `change_spec.md` § Rules, CP-668–CP-684, and `change_design.md` §§ 1–5 for the acceptance contract and placement.

## Project layout

```text
products/tracker17/
  README.md                 ← modified
```

No directory or package creation is required. The parts table is `docs/SDD.md:204-234`, § 3, *The parts, and the seams between them*. The import boundary remains `docs/nfdr.md:166-197`, § 1.2, *Forbidden imports*. Task 1 adds no executable logic to any part, per companion `change_design.md` § 2, *Blast Radius*.

The binding environment decision is `docs/adr/0013-standard-library-only-no-web-framework-suite-environment-made-by-uv.md:22-37`, § Decision, with the commands in `docs/SDD.md:299-333`, § 4 RT-4. Preserve FDR R-8–R-14 and R-119–R-120 (`docs/fdr.md:57-82`, *The written setup instructions*) and PD-7 (`docs/fdr.md:375-376`, exact dependency versions).

## TL Review Notes

- **Task shape — Tech Lead, 2026-10-29:** Use the review-verified lane. Companion `change_design.md` § 5 prescribes document checks, and `change_spec.md` CP-682 excludes test edits. Keep the checks that compare this branch with its base in this task, rather than adding permanent tests tied to a historical README.
- **Task source — Tech Lead, 2026-10-29:** The design's § 2, *Blast Radius*, states one cohesive documentation delta and no sub-job split. It has no separate § 3. Task 1 uses that explicit single-file cut; no interface or ordering decision is needed.
- **Gate command — Tech Lead, 2026-10-29:** The instance project card's `Test command:` is `pytest products/tracker17/tests/`, from the instance worktree root. Companion `change_spec.md` § Verified Claims measured `uv run pytest tests/ -q` and `uv run pytest tests/e2e/ -q` from the product root. Task 1 uses the specified uv commands so its verification exercises the environment the README teaches. The card stays unchanged under CP-682; this plan does not substitute a new card command for a closing gate run by `<CORE>/prompts/gate_suite.md`.
- **Scope comparisons — Tech Lead, 2026-10-29:** Replace the spec Examples' comparisons against the moving tip of `main` with the branch's own merge base, while comparing against the working file so uncommitted edits are included. The reason is `<CORE>/prompts/tech_lead_create_tl_instruction.md` Step 3, *A check that holds only for this change is never a suite test*. Exact byte and heading comparisons strengthen the design's V7/V10 checks without changing their contracts.
- **Baseline run — Tech Lead, 2026-10-29:** `pytest products/tracker17/tests/` from the instance worktree root collected 2,698 tests and exited 1: `38 failed, 2629 passed, 31 errors in 271.47s`. Tracebacks include `PermissionError: [Errno 1] Operation not permitted` at `socket.bind` while setting up loopback listeners (`tests/integration/test_label_listener.py:49`, `web/listener.py:96`) and in `tests/integration/test_start_stop.py:527`. This run establishes no green baseline. Do not classify these results as the red-at-baseline task lane: Task 1 changes prose and has no new test. A valid suite verdict requires an execution environment that permits the listeners; no code or test workaround belongs in this README task.

## Gate environment inputs

Language evidence is the instance project card's `Languages: Python` line. The CI inventory was `git ls-files` at the instance worktree root: 6,041 tracked files, with no CI configuration candidate. A search for runner/workflow declarations in tracked configuration and shell-script areas returned no matches. The root `Containerfile` builds the local execution image and declares no CI runner. `docs/nfdr.md:538-566`, § 8, *Operational constraints*, records no environment entry or amd64 requirement. The Python image source is `<CORE>/doctrine/engineering/languages/python/environment.md` § Provisioning. No product toolchain file or CI configuration supplies an exact container tag; no tag is inferred from the instance's interpreter files.

Checked this JSON with `<CORE>/tools/gate_suite.py record` and `check`, using fresh path, tracked-file and decision-record inputs: `record exit: 0`; `resolves — owners-mac: the product has no CI, so its gates run on the owner's Mac`; `check exit: 0`. The check starts no suite, per `<CORE>/prompts/gate_suite.md` § *The check — whether the evidence resolves, with nothing run*.

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git ls-files at the instance worktree root: 6041 tracked files; top-level entries .claude, .env.example, .gitignore, .providers.toml.example, .python-version, .telemetry.env, AGENTS.md, Brewfile, CLAUDE.md, Containerfile, README.md, about, core, docs, kensaiapp.md, products, pyproject.toml, skills, system, uv.lock. No build-service or CI runner configuration found; runner/workflow declaration search in configuration and shell-script areas returned no matches. Product-local git ls-files: 282 files; no CI configuration."
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

### Task 1: Update the suite instructions and supporting descriptions (`README.md`)

**Dependencies:** None

**What to build:** Place the README copy that satisfies CP-668–CP-682 in the three locations identified by companion `change_design.md` § 2. Where companion `change_text.md` supplies the published text, place it verbatim, per `<CORE>/roles/CROSS_ROLE.md` § 2, *Implementation contract*. Use the no-count decision-log wording chosen in `change_design.md` § 5, V9. Do not edit the protected setup slice, Status paragraph, source, tests, manifests, lock, product records or project card.

#### Deliverables verified by review

- **V1 / CP-668:** Read the suite section for uv installed before the commands, the exact official installation-page URL in the spec, and lowercase tool spelling. No installer recipe or uv version is added.
- **V2 / CP-669:** Compare the suite section's command block with the spec's five-line block, including order and absence of extra lines. Keep the lead-in that starts the reader at the top of the copy.
- **V3 / CP-670, CP-672:** Read the explanation of sync and run against both rules. Check the distinct non-end-to-end and Chromium end-to-end commands in prose as well as the block. The bare-pytest check below prints nothing and exits 1.
- **V4 / CP-671:** Read the Linux replacement against every clause of CP-671: exact `--with-deps` spelling, package manager, administrator rights, tracker/non-end-to-end exemption, all five named distributions/versions and both architectures. This is a reading; no Linux execution is required.
- **V5 / CP-673:** Read the environment paragraph for sync creating product-local `.venv`, keeping it there, the dot-directory exclusion and the failure when the environment is elsewhere inside the product. The source-walk exclusion is `tests/conftest.py:135-147`, `SourceWalk._all`.
- **V6 / CP-674:** Read the new-terminal path separately: rerun the uv test commands inside the product, with no preliminary step.
- **V7 / CP-675:** Retain the test-setup network requirement. Compare the Git-repository paragraph byte for byte with the branch's base using the command below, including the one failing test, its purpose and the tracker's exemption.
- **V8 / CP-676–CP-677:** Read the test bullet against CP-676, including exact-version dependencies, all three layers, Chromium and the RT-4/TS-1 citation. The How-it's-built grep below must find uv. The first bullet links the exact ADR-0013 path CP-677 names; no ADR-0002 link remains.
- **V9 / CP-678:** Read The documents entry for no numerical decision count and the retained `docs/adr/README.md` index pointer.
- **V10 / CP-679, CP-681:** The byte comparison below proves the protected setup slice is identical. Compare all heading texts, levels and order without line numbers. The setup no-uv grep below prints nothing and exits 1. Preserve the two-command start by leaving that slice identical.
- **V11 / CP-680:** Run the whole-README fixed-string grep below unchanged. Pass means no output and exit 1, including forbidden substrings hidden in otherwise reasonable prose.
- **V12 / CP-682:** The product/card scope checks below show only the README differs under the product and the card is identical. No permanent test or helper is added for any of these checks.
- **V13 / CP-683:** In a fresh Git clone of the branch commit on macOS, run the five specified lines in order. Each exits 0, `.venv` exists and is Git-ignored, and `uv.lock` remains byte-identical to its committed blob after both suites.
- **V14 / CP-684:** Read the companion design's *Architect Review Notes*, QC-12 and QC-41/FDR R-14 verdicts. The README diff introduces no additional part or setup requirement beyond the reviewed uv prerequisite. The two existing items in companion `deferred_decisions.md` remain outside the product edit; preserve the protected slice and the committed dependencies.

#### Implement

Verified by review — no test.

#### Verification gate

From the product root, run these checks individually. The three negative checks pass only on **no output, exit 1**; an exit above 1 is an error. The How-it's-built check passes on at least one line, exit 0.

```sh
sed -n '/^### Running the tests/,/^## /p' README.md | grep -o '.\{0,7\}pytest' | grep -vxF 'uv run pytest'
sed -n "/^## How it's built/,/^## The documents/p" README.md | grep -nw uv
sed -n '/^## Setup instructions/,/^### Running the tests/p' README.md | grep -nw uv
grep -nF -e 'python3 -m venv' -e 'pip install' -e 'requirements.txt' -e 'activate' -e 'python -m playwright' -e '`venv`' README.md
```

From the product root, run this change-only comparison as a terminal check, without adding it to the suite. Pass: `protected setup, Git paragraph and headings unchanged`, exit 0.

```sh
python3 - <<'PY'
import re
import subprocess
from pathlib import Path

base = subprocess.check_output(['git', 'merge-base', 'main', 'HEAD'], text=True).strip()
before = subprocess.check_output(['git', 'show', f'{base}:products/tracker17/README.md'])
after = Path('README.md').read_bytes()

def setup(data):
    start = data.index(b'## Setup instructions\n')
    end = data.index(b'### Running the tests\n', start)
    return data[start:end]

def git_paragraph(data):
    start = data.index(b'For every test to pass, your copy needs to be a Git repository,')
    return data[start:data.index(b'\n\n', start)]

assert setup(after) == setup(before), 'protected setup changed'
assert git_paragraph(after) == git_paragraph(before), 'Git paragraph changed'
assert re.findall(rb'^#{1,6} .+$', after, re.M) == re.findall(rb'^#{1,6} .+$', before, re.M), 'headings changed'
print('protected setup, Git paragraph and headings unchanged')
PY
```

From the **instance worktree root**, check scope against the branch's merge base. The first command prints only `products/tracker17/README.md`. The second prints nothing. The status command shows only the README before its edit is committed, or nothing after it is committed; it must expose no added product/card file.

```sh
git diff --name-only "$(git merge-base main HEAD)" -- products/tracker17 system/projects/tracker17/project.md
git diff "$(git merge-base main HEAD)" -- products/tracker17 ':!products/tracker17/README.md' system/projects/tracker17/project.md
git status --short --untracked-files=all -- products/tracker17 system/projects/tracker17/project.md
```

From the product root after the specified setup, the per-task regression commands are `uv run pytest tests/` and `uv run pytest tests/e2e/`. Pass: both exit 0 with no new failure. Keep the final gate's environment handling with `<CORE>/prompts/gate_suite.md`; the JSON above supplies its evidence.

For CP-683, from the **instance worktree root**, create a disposable clone at the commit being verified. Run this only once the README edit is in that commit. The five lines inside the subshell are CP-669 verbatim. The subshell stops on any nonzero exit.

```sh
verification_commit=$(git rev-parse HEAD)
verification_copy=$(mktemp -d)
git clone --quiet . "$verification_copy"
git -C "$verification_copy" checkout --quiet "$verification_commit"
(
  cd "$verification_copy" || exit
  set -e
  cd products/tracker17
  uv sync --locked
  uv run playwright install chromium
  uv run pytest tests/
  uv run pytest tests/e2e/
  test -d .venv
  git check-ignore .venv/
  git show HEAD:products/tracker17/uv.lock | cmp - uv.lock
  git status --short
)
```

Pass: all five specified commands exit 0; the directory check and `cmp` exit 0; `git check-ignore` prints `.venv/`, exit 0; status prints nothing. Record each command's result and each V1–V14 verdict in Developer Review Notes. Read the results before removing the disposable clone, from outside it, as a separate command:

```sh
rm -rf "$verification_copy"
```
