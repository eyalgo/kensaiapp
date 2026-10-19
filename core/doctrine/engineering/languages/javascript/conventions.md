---
version: "1.0.4"
---

# JavaScript — conventions

How JavaScript is named and shaped here. Nothing in this file is enforced by a tool — `quality_gates.md`
§ What is not installed says why, and that is what makes these conventions rather than gates. What the
code does at a failure or an event is `errors_logging.md`.

Every rule below was read off the eight tracked `.js` files (`git ls-files '*.js'`, 2026-08-21) unless
it says otherwise.

## Surface style

- **No statement-terminating semicolons.** Zero across all eight files: `grep -h ';$' … | grep -v
  '^\s*//' | wc -l` returned `0` on 2026-08-21.
- **Two-space indent** (`.claude/workflows/eval-fix.js:4-8`).
- **Single-quoted strings.** A double-quoted string appears only where the content itself carries an
  apostrophe or a single quote — `test("the fixer's prompt does not mention surfaced calls", …)`
  (`.claude/workflows/tests/eval-fix.test.js:108`) and `src.indexOf("phase('apply')")` (`:49`). An
  escape is the thing being avoided, so the outer quote changes rather than the inner one.
- **A value reaches a string through a template literal**, never through `+`. `+` joins string
  *literals* across lines, including a conditional fragment. No staying file shows that join today —
  `grep -n '+$' .claude/workflows/*.js .claude/workflows/tests/*.test.js` returns nothing
  (2026-09-18) — and no `+` in the repo has a variable on either side of it inside a message
  (`grep -nE "' \+ [a-z]" .claude/workflows/*.js` returned nothing, 2026-08-21).

## Bindings and declarations

- **`const` by default, `let` only where the binding is reassigned, `var` never.** `grep -cw var`
  returned `0` for every file on 2026-08-21.
- **A named `function` declaration for a top-level helper.** Eighteen of them across the eight files
  (`grep -nE "^(export )?(async )?function " $(git ls-files '*.js')`, 2026-08-21),
  for example `function authorPrompt(skill, root, workspace, previous)`
  (`.claude/workflows/eval-fix.js:93`). An arrow function is for an inline callback and for a stub
  passed into another function.
- **`SCREAMING_SNAKE_CASE` for a module-level constant that is a registry, a schema or a fixed
  table** — `DECISION` and `APPLY` at `.claude/workflows/eval-fix.js:35` and `:77`, and
  `SETUP_SCHEMA` at `.claude/workflows/run-skill-evals.js:48`.
  **The same casing also lands on four more module-level constants that are none of those three** —
  `EXECUTOR_OPTS`, `RUN_ITEMS` and `STAGED` in `.claude/workflows/run-skill-evals.js:143`, `:189` and
  `:214`, and `WORKFLOW` in each of the test files, a path derived from `import.meta.url`
  (`grep -nH '^const [A-Z_][A-Z0-9_]* *=' $(git ls-files '*.js')`, 2026-08-21). The corpus draws no
  single line between those four and the camelCase constants below, so read this as the observed
  exception rather than a rule that explains it. **`camelCase` for a module-level constant that is
  none of the above**, including one derived at load time: `suppliedKey` and `startIdx` at `:132-133`.

Intent-revealing names, no abbreviations and no generic labels are already required by
`<CORE>/doctrine/engineering/languages/developer_standards.md` § Clean code; this file adds the casing, not the
naming standard.

## Imports and exports

- **Named exports only, and one per module.** Each workflow script exports exactly one binding,
  `export const meta` (`grep -c '^export ' .claude/workflows/*.js` returns `1` for each of the two,
  2026-09-18). No test in the staying suite asserts that count holds — the one assertion that did was
  deleted with the file it tested. **No default export exists anywhere
  in the repo**, and none is written: a default export has no name at the import site, so two callers
  can spell the same module's export differently.
- **Every standard-library import carries the `node:` prefix** — `import { test } from 'node:test'`,
  `import assert from 'node:assert/strict'`, and the same for `node:fs/promises`, `node:url` and
  `node:path`. The prefix makes a builtin unmistakable at a glance and cannot be shadowed by an
  installed package.
- **A relative import specifier carries its `.js` extension.** ES modules do not resolve an
  extensionless specifier: `node main.js` importing `'./dep'` failed with
  `Error [ERR_MODULE_NOT_FOUND]: Cannot find module '…/dep'`, and the same import written `'./dep.js'`
  resolved (run on 2026-08-21). No relative import exists in the repo today, so this rule is the
  runtime's requirement rather than an observed house practice.
- **`await` directly, never a `.then()` chain.** `grep -h '\.then(' …` returned `0` matches on
  2026-08-21. Top-level `await` is used where the module needs a value before it can define anything
  else — `const src = await readFile(WORKFLOW, 'utf8')`
  (`.claude/workflows/tests/eval-fix.test.js:26`).
- **A module locates a sibling file through `import.meta.url`**, resolved with `fileURLToPath`,
  `dirname` and `join` — `.claude/workflows/tests/eval-fix.test.js:25`. Never a path built against
  the process working directory, which is whatever the caller happened to be standing in.

## Comments

`<CORE>/doctrine/engineering/languages/developer_standards.md` § Clean code states the rule and hands this file one
question: "A comment that says *what* the code does is the smell… The one exception is a comment
recording *why* the code is shaped this way and not the obvious other way, with a citation… Which
doc-comment form carries that exception in a given language is that language's `conventions.md` to
state."

In JavaScript it is three forms, and they are not interchangeable:

1. **A single-line `/** … */` block above a function** states that function's contract in one
   sentence. No file under `.claude/workflows/` shows one today (`grep -n '/\*\*'
   .claude/workflows/*.js .claude/workflows/tests/*.js` prints nothing, 2026-09-18).
2. **A `//` block immediately above a construct** carries the floor's exception — why this shape and
   not the obvious other one — and names the alternative that was rejected.
   `.claude/workflows/run-skill-evals.js:16-25` is the model: it records why `skillDir` and
   `skillEvalsDir` are never derived from each other's parent, because "that derivation … is exactly
   what broke the moment they diverge", and cites the station that decided it.
3. **A `//` header block at the top of the file, above the imports**, where the reasoning for the
   file's whole approach is not recoverable from its code. Every test file opens with one;
   `.claude/workflows/tests/ad-hoc-flow.test.js:11-27` at `a01eb180` (retired 2026-09-18) listed each
   failure mode its assertions guard and the commit that produced it.

**Section banners are `// ── <what the section is> ──`** in a workflow script
(`.claude/workflows/eval-fix.js:12`, `:31`, `:75`, `:219`) and a dashed rule
carrying the same label in a test file (e.g. `.claude/workflows/tests/eval-fix.test.js:28`). They
divide a long file into named parts; they are not a substitute for any of the three forms above.
