---
version: "2.0.2"
---

# TypeScript — testing

TypeScript's implementation of the layer model in `testing_doctrine.md`: the tool, the file location
and the run command for each layer. The three gates a change must pass are `quality_gates.md`, and
none of the layers below is one of them.

Read `testing_doctrine.md` first. It owns what each layer is, who writes it, and which layers are
optional; this file only says what each one is made of in TypeScript.

## Layers 1–5 — code-time

| Layer | Tool | Location | Run command |
|---|---|---|---|
| 1 — Unit | Vitest | `tests/unit/<module>.test.ts` | `pnpm exec vitest run` |
| 2 — Integration | Vitest | `tests/integration/<module>.test.ts` | `pnpm exec vitest run` |
| 3 — Application | Vitest | `tests/application/<use-case>.test.ts` | `pnpm exec vitest run` |
| 4 — UI | Vitest Browser Mode | `tests/ui/<component>.test.ts` | `pnpm exec vitest run` |
| 5 — End-to-end | Playwright | `tests/e2e/<flow>.spec.ts` | `pnpm exec playwright test` |

Layers 1–4 share one `vitest run`. Layer 5 runs separately, which is `testing_doctrine.md`'s own
rule rather than a TypeScript one.

**Vitest for layers 1–4, Playwright for layer 5 — the packet author's call, 2026-08-21.** No
TypeScript test file exists in the galaxy to read the choice off, so it rests on two vendor facts
rather than an observation: Vitest is "a next generation testing framework powered by Vite"
(https://vitest.dev/guide/) and reads the product's own `vite.config.ts` with no second build
configuration (below), and Playwright is the provider Vitest Browser Mode itself names for layer 4
(https://vitest.dev/guide/browser/), so layer 5 reuses that same browser stack rather than installing
a second one.

## The rules that make that table work

- **A Vitest file is named `<subject>.test.ts`.** Vitest's default is that "tests must contain
  `.test.` or `.spec.` in their file name" (https://vitest.dev/guide/), and this packet uses
  `.test.` for layers 1–4 so that `.spec.ts` is unambiguously a Playwright file. The two runners
  then never collect each other's tests, without either one needing a custom glob.
- **A test file mirrors the production module it covers**, which is `testing_doctrine.md`'s rule;
  `src/file-tree.ts` is covered by `tests/unit/file-tree.test.ts`, keeping `layout.md`'s
  `kebab-case` filenames.
- **Vitest reads the product's own `vite.config.ts`.** Vitest is "a next generation testing
  framework powered by Vite" and reads that config by default (https://vitest.dev/guide/), so the
  aliases, plugins and transforms under test are the ones the build uses. A separate `vitest.config.ts`
  is added only for settings that are genuinely about the test run — including `test.projects`, which
  is what lets layers 1–3 run in Node while layer 4 runs in the browser, since "if you need to run
  some tests using Node-based runner, you can define a `projects` option with separate configurations
  for different testing strategies" (https://vitest.dev/guide/browser/).
- **Layer 4 runs in a real browser, not a simulated DOM.** Vitest Browser Mode runs "tests in the
  browser natively, providing access to browser globals like window and document", and its Playwright
  provider is the one to use because "it supports parallel execution"
  (https://vitest.dev/guide/browser/). "Vitest always requires a provider to be defined"
  (https://vitest.dev/guide/browser/), and that provider is `@vitest/browser-playwright`, a dev
  dependency of every TypeScript product here. The reason this packet requires it rather than jsdom: the
  products render with Lit or direct DOM (a product's `docs/product_request.md` § 6), so a component test
  is a test of custom elements, shadow roots and layout — the parts a simulated DOM reimplements
  approximately, which makes a pass on jsdom evidence about jsdom.
- **Layer 4 follows `testing_doctrine.md`'s own exemption rule** — "A product with a UI does not get
  the exemption." Whether a given TypeScript product has a UI is that product's own fact, not this
  packet's to settle; a product without one records the exemption in its own `docs/nfdr.md` § 9, per
  `languages/README.md` § Precedence.
- **Layer 5 is Playwright, and it drives the built output rather than the dev server.** Playwright
  is already in the product as the Browser Mode provider layer 4 uses
  (https://vitest.dev/guide/browser/), so layers 4 and 5 share one browser stack and one set of
  browser downloads instead of two. Pointing it at the dev server would undo that: the dev server
  transforms on demand and serves modules the build would have bundled differently, so a pass
  against it is not a statement about what ships.
- **What is mocked is decided by `testing_doctrine.md`'s table**, not by what is convenient to stub
  in TypeScript. The subject stays real.

## Layers 6–7 — acceptance-time

Owned by the QA role and written from the design and the specs before code, per
`testing_doctrine.md`, which also says where a project with no active QA role records that.

**Layer 7 runs through the layer-5 tooling in the table above.** A specification-level scenario
enters the product through its real entry point, which is what Playwright already drives, so the
layer needs no second runner.

**Layer 6 runs on Vitest**, the same runner layers 1–4 already use:

| Layer | Tool | Location | Run command |
|---|---|---|---|
| 6 — Architecture | Vitest | `tests/architecture/<property>.test.ts` | `pnpm exec vitest run` |

**Reversed on 2026-08-30, and the reason the earlier position was wrong is worth keeping.** This
packet said until then that there was no standing TypeScript tool because *"the boundaries it enforces
are drawn by a product's own design rather than by the language — so there is no single TypeScript
answer to pick."* Both halves of that are true and the conclusion does not follow: **what the rule
says** is the product's and varies, **what runs the rule** is the language's and does not. A layer-6
rule is an assertion over module structure — it reads the tree and fails with the site it found — and
Vitest runs an assertion. The JavaScript packet reached the right answer from the same premise, so the
family disagreed with itself on a question only one of them had finished.

No second dependency: layers 1–4 already install Vitest, and naming a dedicated architecture library
here would push a toolchain decision into every TypeScript product, which `toolchain.md` § *Adding one*
makes the product's call. A product that wants one anyway — dependency-cruiser and ts-arch are the
standing options — records it in `docs/nfdr.md` § 9.

**Where the rule itself lives.** The *content* of a layer-6 rule is the product's, in
`docs/nfdr.md` § 1.2, and the entry there names this layer in its `verified by:` tail. This table says
only what runs it.
