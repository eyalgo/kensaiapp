# Tech Lead instruction — what-the-start-prints: explain all three start announcements

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — product paths below are relative to it; command blocks explicitly run from the instance change worktree root.
**Scope:** Place the approved text in README.md's “What the start prints” section, covering CP-736–CP-746.

---

## Project layout

```text
products/tracker17/
  README.md                 ← modified: What the start prints only
```

No directory or package file is created. Placement follows `change_design.md:20-38`, § 2.
The parts table is `docs/SDD.md:216-238`, § 3; startup logic stays with `main`.
The module set and both permitted and forbidden imports remain `docs/nfdr.md:180-211`, § 1.2, QC-13–QC-19.
This task introduces no executable logic or import.

## TL Review Notes

- **Task source:** The design has no numbered § 3. Its single README delta is explicit in § 2 and § 4 (`change_design.md:26-46`), with checks V1–V13 in § 5. Task 1 uses that delta directly; no missing interface or build-order decision needs inventing.
- **Review lane:** Task 1 uses the review-verified shape. The acceptance target is a passage's meaning, and the spec excludes test edits (`change_spec.md:43-45,98-102`). The presence command supplements the reading; it does not assert the passage's meaning. No automated test is added for the copy or for a condition that holds only during this change.
- **Comparison strengthened:** V10–V11 compare against the pre-edit commit (`change_design.md:66-67`). The gate instead compares against the branch's own merge base with `main`, including uncommitted edits. This catches changes anywhere in the arc and avoids a fixed historical SHA. The byte comparison covers every README byte outside the section, including CP-744's protected passage.
- **Language resolution:** Python, resolution step 1, the project card's `Languages:`; opened `<CORE>/doctrine/engineering/languages/python/README.md`. This plan changes no Python source and proposes no language-level construct.
- **Baseline checked, 2026-10-30:** The exact card command in Task 1 ran before any product edit. Inside the Codex sandbox its first suite ended `138 failed, 2655 passed, 20 errors in 312.68s`; the second suite did not run because the command uses `&&`. A focused `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_listener.py -xq` exposed `PermissionError: [Errno 1] Operation not permitted` at `socket.bind`. With command approval, that same focused invocation returned `35 passed in 12.17s`. The approved full card command then exited 0: `2813 passed in 367.64s` and `122 passed in 55.50s`. These are environment-specific baseline results, not failing product behaviours to put in a red-at-baseline task.
- **Gate inputs checked:** `<CORE>/tools/gate_suite.py check`, using this section's JSON and freshly read path, tracked-file and main-branch decision context, exited 0 with `resolves — owners-mac: the product has no CI, so its gates run on the owner's Mac`. This was a check only; it issued no suite and supplies no `Environment:` declaration.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "From the instance change worktree root, git ls-files enumerated 6146 tracked files. Inspected that inventory and its configuration/build/workflow entries: no CI configuration or runner declaration. The .claude/workflows entries are local skill-evaluation workflows. git ls-files '*.yml' '*.yaml' '*Jenkinsfile*' '*Makefile*' '*justfile*' '*Dockerfile*' '*.toml' '*.json' '*.star' '*.bzl' '*.nix' '*.gradle*' '*.xml' '*.properties' .github .circleci .buildkite .gitlab returned local settings, package/tool manifests, fixtures and eval data; no CI configuration."
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

No container tag is supplied: the inventory found no CI version or product toolchain-version file.
The worktree's `docs/nfdr.md` § 8 and accepted ADRs name no environment override or amd64 requirement.

### Task 1: Explain the three start outcomes (`README.md`)

**Dependencies:** None

**What to build:** Place `change_text.md`'s approved passage verbatim between `### What the start prints` and the next `### ` heading. `change_text.md` is the text artifact beside this instruction in `tracker17 · tobiishi · 2026-10-30_what-the-start-prints`; this plan fixes no new published sentence. The task's review criteria come from `change_spec.md:26-45` and `change_design.md:57-95`.

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- **V1–V3 / CP-736–CP-737:** The section-only command below prints `0` before editing and at least `1` afterward. A sentence identifies `The tracker couldn't read`, with a straight apostrophe, as the announcement for saved data that can't be read. Any quotation beyond the prefix matches `main.py:168-173`, `_unreadable_line`, word for word, substituting only the example location.
- **V4 / CP-738–CP-739:** The section says the tracker is still running on that line and continues until stopped. It gives `Setting saved data aside` as the next step for starting fresh on purpose. It claims no loss, deletion, corruption or damage to the saved data.
- **V5 / CP-740:** The ready example remains, with the explanation of the reader's own location replacing the example location. The ready line means running; opening the address shows Projects in that ready case only.
- **V6–V7 / CP-741:** The description of `The tracker didn't start` still says the line gives the reason and next action. It says this start stopped and covers both a refused second tracker and an address already held. It never claims the earlier tracker stopped, and adds no separate explanation for each refusal reason.
- **V4–V8 / CP-742:** Read only this section. Both ready and unreadable-data announcements mean running; the failed-start announcement means this start stopped. The keep-running statement and Ctrl-C instruction explicitly apply to the two running cases, without asking the reader to stop a refused start.
- **V9 / CP-743:** No statement says that nothing else can appear in the terminal. Any count concerns the three start-announcement kinds, treating both failed-start reasons as one kind. No discussion of tracebacks or unexpected serving failures is added.
- **V10–V11 / CP-744–CP-745:** The only changed product file is `README.md`, and its only changed section is the target. Everything before the section body and from the next heading onward is byte-identical to the branch's merge base. This includes the passage from “If it can't read the data, the tracker starts anyway.” through “even if you repair the saved data.” under “Starting the tracker again”. The boundary and product-diff commands below verify this change's scope; they remain review commands, never suite tests.
- **V12 / CP-745:** Both existing suites exit 0. No runtime source, unreadable-data page, lock, test, dependency, product record or other README section changes.
- **V13 / CP-746:** Each sentence authored by this change has at most 20 words; a verbatim program quotation is exempt. Review the text against `docs/CONTENT.md` § Grammar and mechanics and § Terminology, including “terminal”, “saved data”, exact heading names, straight apostrophes and contracted negatives.
- **Approved text:** The placed passage agrees byte for byte with the passage assigned to this section by `change_text.md`. Any text that cannot be placed verbatim is recorded rather than rewritten.

#### Implement

Verified by review — no test.

#### Verification gate

Run every command below from the **instance change worktree root**.

The section-only check, before and after the edit:

```sh
awk '/^### What the start prints/{f=1;next} /^### /{f=0} f' products/tracker17/README.md | grep -cF "The tracker couldn't read"
```

Before: `0`, grep exit 1. After: a positive integer, grep exit 0. A match in another section is insufficient.

Review the complete README diff and check that no other product file differs:

```sh
git diff "$(git merge-base main HEAD)" -- products/tracker17/README.md
git diff --exit-code "$(git merge-base main HEAD)" -- products/tracker17/ ':!products/tracker17/README.md'
git diff --check "$(git merge-base main HEAD)" -- products/tracker17/README.md
```

Pass: all V1–V13 criteria hold on reading the first diff; the second and third commands print nothing and exit 0.

Compare the untouched README bytes with the same merge base, without adding a test or file:

```sh
python3 - <<'PY'
from pathlib import Path
import subprocess

path = 'products/tracker17/README.md'
base = subprocess.check_output(['git', 'merge-base', 'main', 'HEAD'], text=True).strip()
before = subprocess.check_output(['git', 'show', f'{base}:{path}'])
after = Path(path).read_bytes()
heading = b'### What the start prints\n'

def outside_section(text):
    assert text.count(heading) == 1, 'Expected exactly one target heading'
    start = text.index(heading) + len(heading)
    end = text.index(b'\n### ', start) + 1
    return text[:start], text[end:]

assert outside_section(before) == outside_section(after), 'README changed outside target section'
print('README bytes outside the target section are unchanged')
PY
```

Pass: prints `README bytes outside the target section are unchanged`, exit 0. This one-change check ends with the change.

Run the exact project-card test command:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/
```

Pass: both suites run, both exit 0, and there are no new failures. The copy and scope criteria above are also required; passing the suites alone does not verify them.
