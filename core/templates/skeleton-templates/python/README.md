# Python skeleton tree

What `core/launchers/product-skeleton/launcher.sh` copies wholesale into a new Python product
before any product-specific code exists. It is the frame every Python product needs and never
varies — no modules, no entities, no routes, no product name. This file checks every choice below
against the doctrine that fixed it, so a reader can verify the tree rather than trust it.

**Consumer, and why the tree carries no `version:`.** A launcher script copies these bytes
verbatim into a product; per `core/templates/README.md` § The rule, that makes this a
**script-facing** template — content only, no frontmatter, nothing that must not survive the copy.
`core/doctrine/governance/versioning.md` § Where the test lands states the same split for the
marker specifically: *"Templates a script stamps | none — must not carry one"* — so no file here
carries a `version:` or a Python `__version__`.

**The placeholder this tree carries.** `pyproject.toml`'s `[project] name` carries the literal
token `__PROJECT__`, which `core/launchers/product-skeleton/launcher.sh` replaces with the project
card's `Package slug:` when it copies this tree — in file contents and in path names alike. It
substitutes nothing else, and that this tree invents no second token is held by
`core/tools/test_skeleton_trees.py` rather than by the launcher: the trees are ours, so the check
belongs where they are authored rather than on the owner's machine at copy time.

**Which token set applies is the consuming script's** —
`core/templates/README.md` § *Adding a script-facing template*, step 2 names all three sets and
states that they never meet. The one not to reach for here is the project stamper's `<project>` /
`<name>` / `<scope>`, which stamps a project's management folder and knows nothing about a
product's code.

`[project] version` carries **no token at all** — it reads `version = "0.0.0"`. PEP 621 makes the
field mandatory unless it is declared dynamic, and nothing on the project card supplies a package
version (Open questions), so a real starting value stands there for a product to raise rather than
a placeholder nothing would substitute. This README described a `<product-version>` token here
until 2026-09-02; `pyproject.toml` never carried one.

## Where each concern was routed from

`core/doctrine/engineering/languages/README.md` fixes seven concerns, and the Python router,
`core/doctrine/engineering/languages/python/README.md`, gives each exactly one destination. The
table below holds the six that fixed this tree's files. The seventh, Gate environment, routes to
`environment.md` and fixed none, because it decides where a product's gates run rather than what the
copy ships:

| Concern | Destination | What it fixed for this tree |
|---|---|---|
| Toolchain | `toolchain.md` | interpreter, version floor, dependency-adding procedure |
| Layout | `layout.md` → routes a **managed product** to `arch_defaults.md` § Package Structure and to `testing_python.md` for its test tree | the flat-file shape (§ What is deliberately not here, below) |
| Quality gates | `quality_gates.md` | Ruff + mypy, and where their config lives |
| Conventions | `conventions.md` | line length, quote style, `from __future__ import annotations`, DI/composition pattern |
| Errors and logging | `errors_logging.md` | the `main(argv) -> int` entry-point shape, exit/message conventions |
| Testing | `testing_python.md` (outside the packet folder — the router says so explicitly) | `tests/` root, `tests/e2e/`, `tests/architecture/`, the pytest run commands |

Two files outside the packet were also load-bearing, both named by `layout.md` itself:
`core/doctrine/engineering/arch_defaults.md` § Package Structure and § Composition Root (the
package shape and the composition-root rule are language-agnostic, so `layout.md` sends a managed
product there rather than answering them itself — `layout.md:15-16`, *"A managed product gets its
package shape from `arch_defaults.md` § Package Structure — which is language-agnostic, so it is
the body and not the Python overlay"*) and `arch_defaults_python.md` § Exception hierarchy (the
Python spelling of the single-named-base rule).

**This instance's own Python layout was not used as a source.** `layout.md` states explicitly that
its own directory conventions (`core/tools/<module>.py`, tests beside their subject, etc.) describe
"a set of standalone executables," not a product (`layout.md:19`, *"This instance's own Python is
not a product"*) — the same § Two trees split (`:13-17`) that routes a product's package shape
above. Every layout decision in this tree traces to `arch_defaults.md` and `testing_python.md`
instead.

## What is in the tree, and its citation

| File | What it is | Fixed by |
|---|---|---|
| `pyproject.toml` | requires-python floor, Ruff config, mypy config, pytest `testpaths` | see rows below |
| `.gitignore` | Python-standard ignores for the tools this frame names | GitHub's own `github/gitignore/Python.gitignore`, retrieved 2026-09-02 |
| `main.py` | the composition root | `arch_defaults.md` § Composition Root + `errors_logging.md`'s `main()` shape |
| `errors.py` | the single named base error, `AppError(Exception)` | `arch_defaults.md` § Exception shape + `arch_defaults_python.md` § Exception hierarchy |
| `tests/conftest.py` | puts the project root on `sys.path` | `toolchain.md` § Build system (see below) |
| `tests/`, `tests/e2e/`, `tests/architecture/` | the fixed test-tree locations | `testing_python.md` |

### `pyproject.toml`

- `requires-python = ">=3.13"` — `toolchain.md:17`, *"The supported floor is Python 3.13"*. Syntax
  (`requires-python`, quoted comparator string) verified against
  `https://packaging.python.org/en/latest/guides/writing-pyproject-toml/`, retrieved 2026-09-02:
  that page's own minimal example reads `requires-python = ">= 3.8"`.
- `name` under `[project]` is the one placeholder token this tree carries (above); `version` is a
  real starting value, `0.0.0`. PEP 621 makes `name` mandatory and `version` mandatory unless
  marked `dynamic` — confirmed on the same packaging.python.org page, retrieved 2026-09-02 — and
  this frame fixes no build backend (see Open questions), so neither can be computed. The launcher
  supplies `name` from the project card; nothing supplies `version`, which is why only one of them
  is a token.
- `[tool.ruff]` `line-length = 100` — `conventions.md:16`, *"Lines stay within 100 columns"*, and
  `quality_gates.md:74`, *"Set `line-length` from `conventions.md`"* (Ruff's own default is 88,
  which `quality_gates.md:75` says explicitly is not this house's number). `indent-width = 4` —
  `conventions.md:37`, *"Four-space indent."* `target-version = "py313"` carries the same floor as
  `requires-python`. Table/key syntax (`[tool.ruff]`, `line-length`, `indent-width`,
  `target-version`) verified against `https://docs.astral.sh/ruff/configuration/`, retrieved
  2026-09-02 — the same URL `quality_gates.md:74` already cites for the precedence between
  `pyproject.toml`, `ruff.toml` and `.ruff.toml`.
- `[tool.ruff.format]` `quote-style = "double"` — `conventions.md:20`, *"Double-quoted strings,
  and triple-double-quoted docstrings"*, counted at 10,924 double-quoted tokens against 128
  single-quoted. Section name verified against the same Ruff configuration page.
- `[tool.mypy]` `python_version = "3.13"` — `quality_gates.md:76-79` fixes mypy as the type checker
  and names `pyproject.toml`'s `[tool.mypy]` section as its destination over `mypy.ini`; the value
  carries the same floor as `requires-python`, above. Section-name syntax
  (`[tool.mypy]`, not `[mypy]`) verified against
  `https://mypy.readthedocs.io/en/stable/config_file.html`, retrieved 2026-09-02 — the same URL
  `quality_gates.md:78` cites.
- `[tool.pytest.ini_options]` `testpaths = ["tests"]` — reflects `testing_python.md`'s fixed
  `pytest tests/` invocation for layers 1–4. Syntax verified against
  `https://docs.pytest.org/en/stable/reference/customize.html`, retrieved 2026-09-02 (`[tool.pytest.ini_options]`
  table name, `testpaths` as a list).
- **No `[project.dependencies]`, no `[project.optional-dependencies]`, no lockfile.** See Open
  questions — `toolchain.md` § Adding one (`:60-75`, product-facing) fixes the shape a dependency
  takes but explicitly leaves the manager unfixed, so nothing here can name one.
- **No `[build-system]`.** No destination in the Python router, and no clause of `arch_defaults.md`,
  names a build backend for a product — genuine silence, not an instance fact being misread as one.
  See Open questions.

### `.gitignore`

Six stanzas — byte-compiled files, distribution/packaging, unit-test/coverage reports,
environments, mypy, Ruff — copied from the sections of the same name in GitHub's own
`github/gitignore` `Python.gitignore` (`https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore`,
retrieved 2026-09-02), trimmed to the entries this frame's own tools produce (pytest, mypy, Ruff,
coverage, a virtualenv) rather than the framework-specific stanzas (Django, Flask, Scrapy, …) that
file also carries and this frame does not name.

### `main.py` — the composition root

`arch_defaults.md:51-55` fixes the rule: *"The composition root (`main()` or an equivalent
bootstrap module) is the only place that wires concrete implementations to abstractions. It owns
wiring, not flow."* `conventions.md`'s § Constructs names the same pattern for this house's own
code and calls it "the composition root: the only place a concrete implementation is constructed" —
cited here as the worked shape, not as the source of the rule (the rule is `arch_defaults.md`'s;
`conventions.md` is where the house already applies it). The `def main(argv: list[str] | None =
None) -> int` signature and `sys.exit(main())` wiring are `errors_logging.md:55`, *"A `main()` that
returns a status is spelled `def main(argv: list[str] | None = None) -> int` and wired as
`sys.exit(main())`."* `main()` returns `0` and wires nothing because the frame has no modules to
wire — the launcher adds those per the product's SDD § 3 parts table, which is explicitly out of
this run's scope.

### `errors.py` — the single named base error

`arch_defaults.md:63-65` § Exception shape: *"A single named base. One product-level base error
type; every typed error derives from it, and none derives directly from the language's root error
type."* `arch_defaults_python.md:41-45` § Exception hierarchy spells it for Python: *"A single named
base inheriting `Exception` — `TaskTrackerError(Exception)` in a product called task-tracker."*
`AppError` is a placeholder for that product-specific name — this tree carries no product name
(constraint), so it cannot spell `<Product>Error` literally; the README says so rather than
inventing one. `errors_logging.md:27-33` confirms this is the product rule and not the house's own
narrower-base habit: *"A managed product does not get that choice: `arch_defaults.md` § Exception
shape states the single-named-base rule … forbidding exactly what two of these three [house
exceptions] do — a typed exception inheriting directly from bare `Exception`."*

### `tests/conftest.py`

**This file is this run's own supplied answer, not a packet spelling — flagged as such.**
`toolchain.md` § Build system (`:33-44`) reads *"Nothing here is installed … Because nothing is
installed, a test cannot import its subject by package name. It gets there through a
directory-scoped `conftest.py`"* — but that whole section is measured over this **instance's own**
scripts (`git ls-files` counts, and `core/tools/conftest.py` / `.claude/conftest.py` named by path),
not a rule stated for a product; it does not bind this tree. Neither `arch_defaults.md` nor any
other Python-router destination says whether a product ships an installable package or runs flat
like this house does, and this tree fixes no `[build-system]` (Open questions), so nothing makes
`main.py` / `errors.py` importable by name from `tests/`. `conftest.py`'s `sys.path.insert` shim is
the obvious, minimal fix for that gap — the same mechanical shape the instance's own two files use,
reused here as a pattern rather than cited as their rule — and it is harmless if a product later adds
a proper package and drops it.

### `tests/`, `tests/e2e/`, `tests/architecture/`

`testing_python.md`'s layer table fixes three locations unconditionally (layers 1–3 flat under
`tests/`, `testing_python.md:17-19`; layer 5 at `tests/e2e/`, `:21` and `:29`; layer 6 at
`tests/architecture/`, `:40`). `tests/ui/` (layer 4) is **not** created: `testing_python.md:30`
states it is opt-in, *"Most Python products in this system are CLIs and omit the layer entirely
with rationale in `docs/nfdr.md`"* — creating it here would invent a UI for a product that may not
have one, which the job's own guardrail forbids. `tests/e2e/` and `tests/architecture/` hold only a
`.gitkeep` — git does not track an empty directory, and no test file belongs here yet because there
is nothing to test.

## What is deliberately not here

- **No formatter/linter/type-checker installed, no lockfile, no `[build-system]`, no
  `[project.dependencies]`.** See Open questions.
- **No modules, no entities, no routes, no package directory.** `arch_defaults.md:30-32` § Package
  Structure: *"Multi-module products: when the system has 2+ layers with their own internal files,
  each module is a package directory … Flat files suit single-file additions or a small touch
  inside one module."* The frame starts at zero modules, so flat files (`main.py`, `errors.py` at
  the root) are what that rule itself yields for this case — not a decision this tree adds on top of
  it. The SDD § 3 parts table is what turns this into package directories, per-product, and that is
  the launcher's job.
- **No `__init__.py`.** Nothing here is a package yet (no second module to group); adding one now
  would be inventing structure the flat-file case does not call for.
- **No `docs/adr/`, `docs/nfdr.md`.** Those are a managed project's own definition documents
  (`setting_up_a_project.md`), not part of the language frame.

## Open questions — surfaced, not settled

1. **The dependency manager and lock policy are unfixed, so nothing here declares a dependency.**
   `toolchain.md:60-75` § Adding one describes the shape a first dependency takes — `pyproject.toml`
   plus a generated lockfile plus an exact pin — as three things landing together in a product's own
   ADR, and closes with *"The manager is unfixed for the same reason — the first product to need one
   names it in the same ADR."* Since pytest, Ruff and mypy are all installed packages
   (`quality_gates.md:45`, *"No formatter, no linter and no type checker runs over Python
   here"*), and no manager is fixed to lock any of them, this tree ships their **config** (where the
   packet does fix it) but not their **declaration** as a dependency. This is a genuine fork I did
   not resolve: `toolchain.md`'s own "Adding one" procedure reads as gating the *existence* of
   `pyproject.toml` on a product's first dependency-adding ADR, while `quality_gates.md:71` calls
   `pyproject.toml` "the file the product adds anyway" when naming it as Ruff's config destination —
   which assumes it exists. I resolved toward inclusion (this file exists, carrying only the
   floor + gate config) because `quality_gates.md`'s own words name it as a destination outright;
   the alternative — omitting `pyproject.toml` entirely until a product's first ADR — is equally
   defensible from `toolchain.md` alone, and the owner may prefer it.
2. **No build backend is named**, so `[build-system]` is absent and `version` in `[project]` cannot
   be computed or validated — it is a placeholder token rather than a real value. Neither
   `toolchain.md` nor any other destination in the Python router names a build backend (setuptools,
   hatchling, flit, …); this is a packet silence, not an omission on this tree's part.
3. **`AppError`'s name is a placeholder, not the pattern's real spelling — and not the `__PROJECT__`
   token either.** `arch_defaults_python.md` names the base error after the product
   (`TaskTrackerError` for "a product called task-tracker"), a `<Product>Error` shape that the
   launcher's plain-string `__PROJECT__` substitution cannot produce on its own (it would need to
   also carry a class-name casing rule this frame is not asked to add). `AppError` stands as
   a literal, generic class name rather than a token. Whether the launcher should later rewrite it to
   a cased form of the product's name, or leave the product to rename it by hand, is undecided;
   this run's scope is the tree, not the launcher.
4. **`tests/conftest.py`'s `sys.path` shim is this run's own supplied mechanism, not a packet
   spelling.** No destination fixes whether a product built from this frame installs itself as a
   package or runs flat; `toolchain.md` § Build system, which describes that exact shim, is measured
   over this instance's own scripts and does not bind a product (`toolchain.md:35-44` names
   `core/tools/conftest.py` and `.claude/conftest.py` by path). I supplied the same mechanical shape
   because the frame is unimportable without it and no build backend is named to make it unnecessary
   (Open question 2) — flagged here rather than presented as doctrine.
