---
version: "1.1.4"
---

# JavaScript — layout

The source tree, where a new file of each kind goes, and how files and modules are named. How the
things *inside* a file are named is `conventions.md`; where a test file goes per test layer is
`testing.md`.

## The tree

JavaScript in this instance is Claude Code Workflow scripts, and they live where Claude Code loads
them from:

```
.claude/workflows/<meta.name>.js      one file per workflow, flat
.claude/workflows/tests/              every test file
```

`core/doctrine/setup/kensaiapp_structure.md` § *Workflows* enumerates the two scripts. The `tests/`
subdirectory holds two files on disk (`ls .claude/workflows/tests/`, 2026-09-18, after
`ad-hoc-flow.test.js` and the `/development` orchestrator's test both retired with their workflows)
and is the tree `testing.md` runs its suite over.

**The scripts import nothing from each other** — `grep -n "from '\./\|from '\.\./" .claude/workflows/*.js`
returned nothing on 2026-08-21. There is no barrel file and no `index.js`.

## Where a new file goes

| Kind | Path |
|---|---|
| Workflow script | `.claude/workflows/<meta.name>.js` |
| Its test | `.claude/workflows/tests/<same-basename>.test.js` |
| A helper two scripts share | `.claude/workflows/lib/<name>.js` |

The helper row is this authoring run's call, 2026-08-21: nothing shares code today, and putting the
first shared module in a named subdirectory keeps a helper from reading as a fifth loadable
workflow. Every `.js` file directly under `.claude/workflows/` is a candidate for the
`Workflow(<name>)` permission that launches one by name (`kensaiapp_structure.md` § *Workflows — saved Workflow scripts*);
`.claude/workflows/tests/` and `code-integrity-report.md` are already the two direct children that
are not one, so the row does not claim the directory is workflow-only, only that a `.js` helper
should not sit where a workflow name is looked up.

Where a test file goes, for this tree or for a product with its own source tree, is `testing.md`'s
to state — file location is the Testing concern's, per `languages/README.md` § The seven concerns.

## Naming

- **kebab-case for a filename**, all lowercase: `run-skill-evals.js`, `eval-fix.js`.
- **A workflow script's basename is its `meta.name`**, exactly. `run-skill-evals.js:2` declares
  `name: 'run-skill-evals'`, and `kensaiapp_structure.md` § *Workflows* says what rests on the two
  agreeing — the skill "launches by name (`meta.name: 'run-skill-evals'`)". Both pairs match
  (`grep -n "name: '" .claude/workflows/*.js`, 2026-09-18).
- **A test file is its subject's basename plus `.test.js`.** The two on disk pair 1:1 with the two
  scripts.
- **`.js`, and only `.js`.** No `.mjs` or `.cjs` is tracked (`git ls-files '*.mjs' '*.cjs'` returned
  nothing, 2026-08-21). The module system comes from the source text, not from the extension —
  `toolchain.md` § Module system.
