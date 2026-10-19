---
version: "1.0.3"
---

# Python — quality gates

The checks a tool can fail the build on, and the exact command for each. A rule only a reader can
apply is not here — it is in `conventions.md`, per `languages/README.md` § The seven concerns.

## The two gates

| Gate | Command | Passes when |
|---|---|---|
| Compile | `python3 -m compileall -q <path>` | exit status 0 |
| Suite | the run command in `testing_python.md`, per layer | exit status 0 |

Both ship with the interpreter and need no installed package — which is why these two are the
gates and a formatter, a linter and a type checker are not (§ What is not installed).

**Compile.** The `compileall` module's own documentation says its functions "compile Python source
files in a directory tree" (`https://docs.python.org/3/library/compileall.html`); the check reports
a syntax error without running anything. Run against a file containing `def f(:` on 2026-08-21 it printed
`*** Error compiling './broken.py'...` with the `SyntaxError` and exited `1`; against a valid file
it exited `0`. `-q` suppresses the list of files compiled and keeps the error messages, which is
what makes the output readable as a finding list. The gate writes `__pycache__` beside the sources;
`.gitignore:2` already ignores it.

This gate catches a file that cannot be parsed. It does not catch a name that does not exist, an
argument of the wrong type, or an import that fails — nothing here type-checks, so Compile passing
is not evidence a module runs.

**Suite.** The layer model, the tool and the per-layer run command are `testing_python.md`'s; the
bar is here, and it is total: **a red test is a failed gate, and a suite that does not run is a
failed gate.** The second half is not rhetorical — pytest exits `5` for "No tests were collected"
and `1` for "Tests were collected and run but some of the tests failed"
(`https://docs.pytest.org/en/stable/reference/exit-codes.html`), and a gate that treats only `1` as
a failure passes a run that tested nothing. Measured here on 2026-08-21: `python3 -m pytest -q` at
the repository root collected 1448 tests.

No coverage threshold is set. A product that sets one records the number in its own `docs/nfdr.md`,
which is where a per-product quality bar belongs.

## What is not installed

No formatter, no linter and no type checker runs over Python here, and none is configured anywhere.
On 2026-08-21 `grep -rn -iE "\b(ruff|black|flake8|mypy|pylint|isort|pyright)\b"` across `*.md`,
`*.py`, `*.toml`, `*.json` and `*.sh` returned seven lines and **not one of them is a
configuration**: two stanza headings in `core/templates/gitignore_template.md:75` and `:86`, two
colour words in prose, one query string inside an eval fixture, and two lines in an archived
proposal recording this same grep. No `ruff.toml`, `mypy.ini`, `setup.cfg`, `.flake8`,
`pyrightconfig.json` or `.editorconfig` is tracked.

That follows from the dependency position in `toolchain.md`, not from an oversight: every one of
these tools is an installed package, and this house installs none.

**So every rule in `conventions.md` is reader-applied.** None of them is a gate, and a change that
breaks one fails no command. That is the cut `languages/README.md` draws, at its sharpest: with two
gates this narrow, almost all of this packet's practice is convention.

## What a product installs, when it installs one

These are house defaults. A product's own decision files outrank them — `languages/README.md`
§ Precedence — so a product that names something else in its `docs/adr/` is not departing from
doctrine, it is doing what the chain says it may.

- **Formatter and linter: Ruff, one package for both.** `ruff format` is "an extremely fast Python
  code formatter designed as a drop-in replacement for Black, available as part of the `ruff` CLI"
  (`https://docs.astral.sh/ruff/formatter/`), and `ruff format --check <path>` "will avoid writing
  any formatted files back, and instead exit with a non-zero status code upon detecting any
  unformatted files" — which is the gate form. `ruff check <path>` is the lint half. Configuration
  goes in `pyproject.toml`, the file the product adds anyway per `toolchain.md` § Adding one; Ruff
  also reads `ruff.toml` and `.ruff.toml`, and "the `.ruff.toml` file will take precedence over the
  `ruff.toml` file, and the `ruff.toml` file will take precedence over the `pyproject.toml` file"
  (`https://docs.astral.sh/ruff/configuration/`). **Set `line-length` from `conventions.md`** —
  Ruff's default is 88, which is not this house's number.
- **Type checker: mypy.** Ruff does not type-check, so this is a second package or none. mypy reads
  `mypy.ini`, then `.mypy.ini`, then a `[tool.mypy]` section of `pyproject.toml`, then a `[mypy]`
  section of `setup.cfg` (`https://mypy.readthedocs.io/en/stable/config_file.html`); use the
  `pyproject.toml` section, for the same reason as above.

Both choices are this authoring run's, 2026-08-21, and nothing on disk settled either: the criterion
was fewest new packages for the coverage gained, which follows from `toolchain.md`'s zero-dependency
position. The named alternative for the second is Pyright, recorded by a product in its `docs/adr/`.
Astral's `ty` was not chosen because its vendor announced "the Beta release of ty" on 2025-12-16 and
said "we're working towards a Stable release next year" (`https://astral.sh/blog/ty`, read
2026-08-21).
