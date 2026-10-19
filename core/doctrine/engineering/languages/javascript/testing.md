---
version: "1.1.3"
---

# JavaScript — testing

This language's implementation of `testing_doctrine.md` — the tool, the file location and the run
command for each layer. What counts as a passing suite is `quality_gates.md` § The two gates; this
file does not set a bar.

## The tool

`node:test` with `node:assert/strict`, both from Node's standard library, both imported with the
`node:` prefix. `node:test` is "Stability: 2 - Stable" and has been since v20.0.0
(`https://nodejs.org/api/test.html`). No test framework is installed and none is needed —
`toolchain.md` § Dependencies.

## Layers 1–5

| Layer | Tool | Location | Run command |
|---|---|---|---|
| 1 — Unit | `node:test` | `tests/<module>.test.js` | `node --test 'tests/*.test.js'` |
| 2 — Integration | `node:test` + the real adapter | `tests/<module>.test.js` | `node --test 'tests/*.test.js'` |
| 3 — Application | `node:test` | `tests/<module>.test.js` | `node --test 'tests/*.test.js'` |
| 4 — UI | none standing — see below | — | — |
| 5 — End-to-End | `node:test` | `tests/e2e/<flow>.test.js` | `node --test 'tests/e2e/*.test.js'` |

The glob is quoted so the shell hands it to Node unexpanded
(`https://nodejs.org/api/test.html`). Layers 1–3 share one invocation; layer 5 runs separately, per
`testing_doctrine.md` § Layers 1–5 ("Layer 5 runs separately").

In this instance those paths resolve to `.claude/workflows/tests/` (`layout.md` § The tree), and the
suite command is `node --test '.claude/workflows/tests/*.test.js'`, which reported
`tests 140 · pass 140 · fail 0` on 2026-08-21 under Node `v26.0.0`.

**Layer 4 has no standing JavaScript tool here, because component testing needs a DOM and Node does
not provide one.** Every tool that supplies one is an installed package, which makes the choice a
product decision under `toolchain.md` § Adding one — so a JavaScript product with a UI records its
component-test tool in its own `docs/nfdr.md` § 9, and a product without a UI omits the layer with
rationale there, per `testing_doctrine.md`.

Coverage is available in the runtime through `--experimental-test-coverage` (`node --help`,
2026-08-21). No threshold is set — `quality_gates.md` § The two gates.

## Layers 6–7

QA-role-owned, per `testing_doctrine.md` § Layers 6–7 — a division this file leaves as it found it.

No layer-6 or layer-7 JavaScript file exists in the repo, so the tool below is reasoning rather than
observation: **both layers are written as `node:test` cases too**, because an ArchUnit-style rule is
an assertion over module structure and a layer-7 scenario is an assertion over behaviour, and neither
needs anything `node:assert/strict` lacks. The reason to name a tool at all rather than leave the
entry open is that the alternative — an installed BDD framework — is a dependency, and
`toolchain.md` § Adding one makes that a product's decision, not this packet's.

**That reasoning is the family's answer for layer 6, settled 2026-08-30.** All four packets now name a
layer-6 tool, and each names the one its other layers already install — this one, `pytest` for Python,
Vitest for TypeScript, and for shell a pytest walking every file on disk. TypeScript held the opposite
position until that date, on the grounds that a rule's boundaries are the product's design rather than
the language's; the grounds are true and the conclusion was not, because what the rule *says* is the
product's and what *runs* it is the language's.

**Where the rule itself lives.** The *content* of a layer-6 rule — which module may import which — is
the product's, in `docs/nfdr.md` § 1.2, and the entry there names this layer in its `verified by:`
tail. This packet says only what runs it.

## Writing a test

- **A test name is a sentence stating the behaviour**, not a label for the function under test:
  `test('the surfaced check runs only after entries is known, not before', …)`
  (`.claude/workflows/tests/eval-fix.test.js:30`).
- **A test file opens with a `//` header block** saying what it covers, which failure modes it guards,
  and the command that runs it — `// Run: node --test .claude/workflows/tests/eval-fix.test.js`
  closes both (`conventions.md` § Comments, form 3).
- **Assertions come from `node:assert/strict`**, so `assert.equal` is `===` without the caller having
  to remember to reach for `strictEqual`.

## Testing a file that is not an importable module

A Claude Code Workflow script cannot be imported: it has top-level `return` and it reads `agent`,
`log`, `phase` and `args` as globals its runner injects. Two techniques exist here, and one is
better.

**Preferred — compile the real bytes and run them.** Read the file, strip the one `export` keyword,
and compile the remainder as an `AsyncFunction` body with the injected globals supplied as stubs.
No file shows this technique today: the one test that used it retired with the workflow it tested.
The reason to prefer it still holds: executing the real driver loop proves its paths against the
actual code that ships, rather than against a regex's idea of it.

**Fallback — pin the real source text** with `indexOf` and regex over the file's own bytes, used by
both test files that remain (`.claude/workflows/tests/run-skill-evals.test.js:282`, `:298` regex-match
`export const meta` and do not execute it). Its limit is stated in its own header, verbatim: "a
source-text test pins a line against deletion and reordering; it cannot prove the wiring runs"
(`.claude/workflows/tests/ad-hoc-flow.test.js:8-9` at `a01eb180`, retired 2026-09-18).

Reach for the fallback only where the file cannot be compiled at all.

**Neither technique may test a copy of the logic.** Both read the real on-disk file, and
`ad-hoc-flow.test.js:7-8` at `a01eb180` states why: "a standalone copy of the predicates would be a copy the
workflow never executes."
