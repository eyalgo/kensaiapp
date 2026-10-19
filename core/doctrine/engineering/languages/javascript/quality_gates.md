---
version: "1.1.3"
---

# JavaScript — quality gates

The checks a tool can fail the build on, and the exact command for each. A rule only a reader can
apply is not here — it is in `conventions.md`, per `languages/README.md` § The seven concerns.

## The two gates

| Gate | Command | Passes when |
|---|---|---|
| Parse | `node --check <file>` | exit status 0 |
| Suite | `node --test '.claude/workflows/tests/*.test.js'` | every test passes and the run exits 0 |

Both ship with Node and need no installed dependency, which is why these two are the gates and the
usual third — a linter — is not (§ What is not installed).

**Parse.** `node --check` compiles a file without running it, and on an ambiguous `.js` file it parses
under the CommonJS goal, not the ES-module goal a workflow script actually loads under
(`toolchain.md` § Module system): its own error trace names `wrapSafe (node:internal/modules/cjs/loader:1762:18)`
when a check fails (run on a deliberately broken file, 2026-08-21). That goal gap means Parse and the
runtime can disagree — `node --check .claude/workflows/run-skill-evals.js` exits `0` while `node
.claude/workflows/run-skill-evals.js` exits `1` with `SyntaxError: Illegal return statement`, because
`export const meta` forces ES-module loading and a top-level `return` is illegal there (`:510`; run
2026-09-18). So this gate catches what both goals agree is broken — an unmatched paren, a broken brace — and it
does not catch a file that parses cleanly under CommonJS but cannot load as the module it actually is;
Parse passing is not evidence a workflow script runs. `.claude/workflows/code-integrity-report.md:247`
records it in that run's verification table: `node --check .claude/workflows/run-skill-evals.js` →
`exit 0`.

**Suite.** The layer model behind the suite, what a test file looks like, and why the glob is quoted
are `testing.md`'s. Its bar is here, and it is total: **a red test is a failed gate, and a suite that
does not run is a failed gate.** On 2026-08-21 the command reported `tests 140 · pass 140 · fail 0`.

Coverage thresholds are available in the runtime (`--test-coverage-lines`, `--test-coverage-branches`
and `--test-coverage-functions`, from `node --help` on 2026-08-21) and **no threshold is set**. A
product that sets one records the number in its own `docs/nfdr.md`, which is where a per-product
quality bar belongs.

## What is not installed

No formatter, no linter and no type checker runs over JavaScript here. On 2026-08-21 `git ls-files`
matched no `eslint`, `prettier`, `biome`, `tsconfig`, `jsconfig` or `.editorconfig` path, and Node
itself ships neither: `node --help | grep -cE '^\s+--(lint|format)'` returned `0` on 2026-08-21.

That is a consequence of the dependency position in `toolchain.md`, not an oversight: every one of
these tools is an installed package, and this house has no `package.json` to install it into.

**So every style rule in `conventions.md` is reader-applied.** None of them is a gate, and a change
that breaks one fails no command. That is the cut `languages/README.md` draws, landing here at its
sharpest: with two gates this narrow, almost all of this packet's practice is convention.

A product that decides otherwise records the tool in its own `docs/adr/` and adds it as a
dependency per `toolchain.md` § Adding one. Three the ecosystem offers, with the vendor's own page
for each:

- **ESLint** — `https://eslint.org`. It reads one of six flat-config filenames — "eslint.config.js
  eslint.config.mjs eslint.config.cjs eslint.config.ts eslint.config.mts eslint.config.cts"
  (`https://eslint.org/docs/latest/use/configure/configuration-files`) — and none of the old
  `.eslintrc.*` names: that system was removed in v10.0.0, released 2026-02-06
  (`https://eslint.org/blog/2026/02/eslint-v10.0.0-released/`). A config written under the old name
  is not read at all.
- **Prettier** — `https://prettier.io`.
- **Biome** — `https://biomejs.dev`.
