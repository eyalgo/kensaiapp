---
version: "1.3.0"
---

# Python — conventions

How Python is named and shaped here, and, where a bullet says so, what the language itself does with
a construct. Nothing in this file is enforced by a tool —
`quality_gates.md` § What is not installed says why, and that is what makes these conventions
rather than gates. What the code does at a failure or an event is `errors_logging.md`.

Every measurement below was taken on 2026-08-21 over the house-authored Python — `core/tools/`,
`core/launchers/` and `.claude/hooks/` — unless it names a wider set.

## Surface style

- **Lines stay within 100 columns.** 292 of 28,881 lines exceed it (1.0%). 88 columns is not this
  house's number: 2,682 lines exceed that, so adopting a formatter's 88-column default would
  reflow most of the tree. `quality_gates.md` § What a product installs points a formatter's
  `line-length` back here.
- **Double-quoted strings, and triple-double-quoted docstrings.** 10,924 double-quoted string
  tokens against 128 single-quoted, and 728 `"""` docstrings against zero `'''` (counted with
  `tokenize`, so a quote inside a string is not miscounted). Of the 128 single-quoted tokens, 55
  carry a double quote in their own content and 65 sit inside an f-string's expression —
  `f"...{entry['name']}..."` — and the remaining 8 are neither: two `assert '$SCRIPT_DIR/…' in text`
  / `not in text` lines apiece in four launcher test files —
  `core/launchers/experience-visual/test_experience_visual.py:516-517`,
  `core/launchers/experience-voice/test_experience_voice.py:523-524` (both retired 2026-09-30, with
  their launchers),
  `core/launchers/kensaiapp-writing-bar/test_kensaiapp_writing_bar.py:512-513` (that suite retired
  2026-09-30, with its launcher) and
  `core/launchers/product-content/test_product_content.py:585-586` (that suite retired 2026-09-17,
  with its launcher) — where the single quote wraps a
  shell path inside the assertion, not a Python string carrying a double quote.
- **Interpolation is an f-string.** No `%`-formatting exists (`git grep -nE '" % \(|" % [a-z]'`
  returned nothing across all 95 tracked files). `.format()` is used 31 times and never on a
  literal — always on a template held elsewhere, a module constant such as `PROMPT` or `PLAN`, or
  a string read from a template file (`skills/interactive-product/.claude/skills/project-stamp/scripts/stamp_project.py:287`).
  That is the split: an f-string interpolates at the point of use, `.format()` fills a template
  defined away from it.
- **Four-space indent.** Every indent step in the measured set is exactly four columns — zero
  files show a step of any other width when the tokenizer's `INDENT` tokens are compared.

## Typing

- **`from __future__ import annotations` is the first statement.** 56 of the 95 tracked files
  carry it, and it is near-total where the house authors most: 14 of 14 under `core/launchers/`
  and 31 of 35 under `core/tools/`.
- **Builtin generics and PEP 604 unions, never their `typing` spellings.** Over all 95 tracked `.py`
  files — a wider set than this file's own default, named because that is the scope the count
  holds over — 221 uses of `list[`, `dict[`, `tuple[` and `set[` (counted by AST: a `Subscript` node
  whose value is one of those four names) against zero of `List[`, `Dict[`, `Tuple[` or `Set[`; 118
  uses of `X | None` against zero `Optional[`. `typing` is imported by three files in the whole
  tree, and only for a construct with no builtin spelling — `Literal` in
  `core/tools/commit_builder.py:109` and `core/tools/verify_commit_msg.py:32`, `Callable` in
  `core/tools/spawn_satellite.py:95`.
- **A production function is annotated on its parameters and its return.** Across the 15
  production modules under `core/tools/`, 156 of 184 functions carry a return annotation and 246 of
  290 parameters are annotated. **A test function is not** —
  1,264 of the 1,350 `def test_*` functions in the measured set carry no annotation at all (94%),
  because a test's parameters are pytest fixtures whose names already say what they are.
- **A `None` default makes `None` the value when no argument is passed; the annotation does not say
  so.** `x: T = None` called without `x` holds `None`, whatever `T` reads, and "The Python runtime does
  not enforce function and variable type annotations" (https://docs.python.org/3/library/typing.html).
  PEP 484 once let a type checker read such an annotation as optional and now recommends against it:
  "Type checkers should move towards requiring the optional type to be made explicit"
  (https://peps.python.org/pep-0484/, § Union types). From 3.11, `typing.get_type_hints` no longer adds
  `Optional` for a `None` default: "Changed in version 3.11: Previously, `Optional[t]` was added for function
  and method annotations if a default value equal to `None` was set. Now the annotation is returned
  unchanged" (https://docs.python.org/3/library/typing.html, `get_type_hints`). Neither source above
  fixes how such a parameter's type is spelled when shown, and this bullet fixes no rendering. This bullet states what the language does, not a house habit, so no count
  stands behind it.

## Constructs

- **`@dataclass(frozen=True)` is the house's own default for a value read after it is built** — 21
  of the 23 `@dataclass` uses in this corpus, which is not a product's entity layer (`layout.md`
  § Two trees). `arch_defaults_python.md` § *Entity immutability* names `@dataclass(frozen=True)` for a
  product's entities specifically; what this corpus adds, outside that scope, is the shape of its
  own exception. Both non-frozen uses are a class named `Report` that a run accumulates into
  (`core/tools/link_satellite.py:114`, `core/tools/spawn_satellite.py:140`).
- **`Enum` for a closed value set**, which `<CORE>/doctrine/engineering/languages/developer_standards.md`
  § Engineering judgment already requires. The house form is a bare `Enum` when the member is only
  compared (`class Verdict(Enum)`, `core/tools/experience_gate.py:39`) and `(str, Enum)` when the
  member's value is also written out or read back (`class Outcome(str, Enum)`,
  `.claude/scripts/run_eval.py:36`).
- **`pathlib.Path` over `os.path`.** 72 of the 95 tracked files import `pathlib`; 18 use
  `os.path`. The rule the corpus supports without exception is the second one: **a module picks one
  and does not mix them** — of the 31 production files using either, 29 use exactly one.
  `Path` as the default for new code is this authoring run's call, 2026-08-21, on the ground that a
  path then travels as a typed value rather than as a `str` that happens to hold one.
- **A module is given its collaborators; it constructs none.** Everything a unit reaches the world
  through — the filesystem, a subprocess, the environment, another tool's output, a notification
  channel — arrives as a constructor parameter, and the only place a concrete implementation is
  built is one wiring function at the bottom of the module. `core/tools/chain.py` is the worked
  shape: four ports (`Files` `:237`, `Processes` `:278`, `Reports` `:293`, `Notifier` `:327`), an
  engine that states the rule in its own docstring (`:1008`, *"Everything it uses is handed to it; it
  constructs nothing"*), and `build_chain()` at `:1512` under the heading at `:1499` — *"The
  composition root: the only place a concrete implementation is constructed"* — which `main()` at
  `:1528` calls at `:1564` and `:1596`. **Do not reach a collaborator from a unit's body.** A module
  that opens its own file or starts its own subprocess can only be driven by monkeypatching itself,
  and a suite that patches its own subject proves the patch: `core/tools/test_chain.py:4-6` records
  the predecessor that was green over 161 functions while the engine ignored the spine it was handed.
- **This rule is stated against one worked module, not read off a majority**, which is what makes it
  the one bullet here a reader will find the surrounding code disagreeing with. Measured 2026-09-01,
  10 of the 17 non-test modules under `core/tools/` reach a collaborator directly:

  ```sh
  grep -lE 'subprocess\.(run|check_output|check_call|Popen)|(^|[^a-zA-Z_.])open\(|os\.environ|urllib|shutil\.' core/tools/*.py | grep -vc '/test_'
  ```

  `languages/README.md` § Precedence settles that case and is the reason this bullet is written
  anyway: the packet outranks the surrounding code's habits, the packet wins, and the run records
  that it diverged from the file. The probe counts sites rather than violations — `chain.py`'s own
  four are its port bodies and its wiring function (`:254`, `:260`, `:284`, `:1328`).
- **Several collaborators arrive keyword-only, and none carries a default.**
  `core/tools/chain.py:880-882` is the form — a `*`, then seven required parameters (`store`,
  `files`, `processes`, `reports`, `notifier`, `environ`, `engine_path`), each annotated and none
  defaulted. Measured 2026-09-01 with
  `grep -rn 'def __init__(self' core/tools/ core/launchers/ .claude/hooks/ | grep -v '/test_'`, the
  corpus holds four non-test constructors and all four are in this one file: the three taking one or
  two collaborators take them positionally (`:295`, `:323`, `:816`), and only the seven-parameter
  engine is keyword-only. Keyword-only past two is this authoring run's call, 2026-09-01, on the
  ground that a positional list of seven collaborators cannot be read at the call site and silently
  tolerates a reordering. The one defaulted parameter beside them,
  `cycle_cap: int = DEFAULT_CYCLE_CAP` (`:882`), is a plain value and not a collaborator; **a default
  on a collaborator is what this rule forbids**, because it lets a caller omit the seam and get the
  real implementation without saying so.
- **A port is a plain class, never `typing.Protocol`.** `Files`, `Processes`, `Reports` and
  `Notifier` are ordinary classes whose real behaviour is their bodies, and a test's fake satisfies
  one by having its methods — `core/tools/test_chain.py:24`, *"the fakes: one per port the engine
  is given"*, with `FakeFiles` at `:27` inheriting nothing. Measured 2026-09-01,
  `grep -rn Protocol core/tools/ core/launchers/ .claude/hooks/ | grep -v '/test_'` returns nothing.
  Nothing type-checks here, so a `Protocol` buys no verification and only adds a class to keep in
  step — `quality_gates.md` § What is not installed, *"No formatter, no linter and no type checker
  runs over Python here, and none is configured anywhere."* `arch_defaults_python.md`
  § *Repository typing* names `typing.Protocol` for a **product's** repository layer, where that
  product's own gates may check it; what this corpus states, outside that scope, is the spelling for
  code no gate runs over. One rule at two type-checking positions, not two answers to one question.

## Naming

- **snake_case for a function, a parameter and a local; PascalCase for a class.**
- **A leading underscore marks module-internal.** In those same 15 modules, 97 of 175 top-level
  functions carry it, so the un-prefixed set is readable as the module's public surface. The same
  applies to a constant: 36 module constants there are `SCREAMING_SNAKE_CASE` and 27 more are the
  same with a leading underscore.
- **Every non-test module carries `__version__ = "X.Y.Z"`**, placed after the imports and before
  the first definition — 13 of the 15 under `core/tools/` and all 7 under `.claude/hooks/`.
  `core/tools/written_forward.py:70` and `core/tools/commit_builder.py:111` are two. The two
  apparent exceptions are not: `auditrun/rounds.py` and `coldread/manifest.py` are package members,
  and **a package carries the marker once, in its `__init__.py`**
  (`core/tools/auditrun/__init__.py:9`). This is `versioning.md`'s marker for a script, in the
  spelling Python already has for it.

Intent-revealing names, no abbreviations and no generic labels are already required by
`<CORE>/doctrine/engineering/languages/developer_standards.md` § Clean code; this file adds the casing, not the
naming standard.

## Comments and docstrings

`<CORE>/doctrine/engineering/languages/developer_standards.md` § Clean code states the rule — a comment saying
*what* the code does is the smell — and hands this file one question: which form carries the one
exception, a comment recording why the code is shaped this way and not the obvious other way.

In Python it is two forms, and they differ by scope.

1. **The module docstring, for reasoning about the whole file.** 37 of the 40 production files in
   the tree open with one. Six files — four of them production — structure that docstring under a
   literal `WHY THIS EXISTS` heading. `core/tools/written_forward.py:4-20` is the model: it records
   that the rule it enforces "kept coming back" and cites the two commits that had stripped the same
   defect by hand. The floor names `commit_builder.py` as carrying a header of exactly this kind;
   that docstring is `core/tools/commit_builder.py:2-100`, and what makes it this kind is the
   parenthetical at `:12-13` — "(this module is its executable source, not a second definition)" —
   which names the reading the file exists to prevent.
2. **A `#` block immediately above one construct**, naming the alternative that was rejected.
   `.claude/scripts/utils.py:27-29` is the shape: "Drop CLAUDECODE so `claude -p` can run nested
   inside a Claude Code session. The guard exists for interactive-terminal conflicts; a subprocess
   is safe."

A function docstring is a third thing and not one of these two: it states that function's contract,
and 137 of the 213 definitions in the 15 production modules under `core/tools/` carry one. It is
not the place for reasoning about alternatives, because a caller reading the contract is not asking
that question.
