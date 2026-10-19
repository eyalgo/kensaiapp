# `<CORE>/templates/` — the stamping shapes

Every file here is a shape some part of kensaiapp turns into a real file. This README says what
format a template must be in, and how to tell which one applies to the template you are adding.

## The rule — a template's format follows its consumer

**Two different things read templates, and they need opposite formats.**

| Consumer | What it does | So the template is | Cost of getting it wrong |
|---|---|---|---|
| **A model** — the `product-*` definition skills, `project-stamp`'s document steps, the PM and Principal PM authoring journey items from `journey-templates/` | reads the template, understands it, and writes a fresh document | prose plus guidance — `<!-- -->` blocks addressed to the model, a `version:` frontmatter, whatever explains the shape. None of it survives, because the model never copies it. | one wrong document, once, in front of a reviewer |
| **A script** — `spawn_satellite.py`, `project-stamp`'s `stamp_project.py`, the `product-skeleton` launcher | copies the bytes and substitutes tokens | **the file itself.** Content only, with that script's own placeholder tokens (step 2 below). Nothing to strip, nothing to unwrap, no frontmatter, no comment blocks. | a function in the script, forever |

That asymmetry is the whole rule. A model-facing template costs nothing to document, because
documenting it is how it works. A script-facing template that carries documentation has to have the
documentation *removed by code* — and that code lives in the spawner, gets a name, gets a test, and
gets read by everyone after you.

**Which consumer is mine?** Look at what creates the file. If a skill's prose tells a model to author
the document, it is model-facing. If a line of Python names your template and writes the result, it is
script-facing.

## Adding a script-facing template

1. **Write the file you want to land**, exactly. If the stamped result should start with `# Foo`, the
   template starts with `# Foo`.
2. **Use the token set of the script that will read your template.** There is no single set, and
   that is not drift. Three scripts copy templates, and each substitutes its own closed set over
   its own files, never reading another's:

   | The script | What it stamps | Its tokens |
   |---|---|---|
   | `<CORE>/tools/spawn_satellite.py` (`:390`, `:557-559`) | a fresh instance's tree | `<instance>`, plus `<role>` and `<Role Title>` in a role overlay |
   | `skills/interactive-product/.claude/skills/project-stamp/scripts/stamp_project.py` (`:106`) | a **project's management folder**, `system/projects/<name>/` | `<project>`, `<name>`, `<scope>` |
   | `<CORE>/launchers/product-skeleton/launcher.sh` (`substitute()`) | a **product's own code**, from `skeleton-templates/<language>/` | `__PROJECT__` |

   The substitution is a plain string replace in all three. **A template belongs to exactly one of
   them**, so the question is never "which convention does this repo use" but "which script reads
   this file". The three sets never meet: no file is stamped by two of them, and none of the three
   would recognise another's token if it found one.

   **That has been read as drift twice, and repaired towards agreement twice — each time by writing
   a sentence that was false.** Two skeleton-tree READMEs claimed the launcher's token was "this
   instance's one substitution convention, the one `stamp_project.py` already uses", with a line
   citation to a helper that has only ever known the three in row two. Agreement is not available:
   the sets differ because the *files* differ, which is the next paragraph.

   **Why the skeleton launcher's is spelled unlike the two above it.** Its templates are a product's
   real source files, so its token has to survive as a directory name on every filesystem and be
   invalid syntax in every language a tree is written in. `crates/<project>/` makes a repository
   un-checkoutable on Windows, which forbids `<` and `>` in a filename. `{{project}}` is the
   literal-brace escape in Python's `str.format` and in Rust's `format!`, so a tree carrying one is
   corrupted rather than copied. The other two stamp Markdown into folders nobody compiles, and neither constraint
   reaches them.
3. **Put nothing in it that must not survive.** No frontmatter, no `<!-- -->` metadata block, no prose
   about the template. If it is in the file, it is in the instance.
4. **Document it in the manifest instead** — `<CORE>/doctrine/setup/kensaiapp_structure.md`
   § Templates layer, which enumerates every template and what it stamps into. That is where the
   description belongs, and the enumeration entry is required anyway: the manifest is what Audit is
   defined against, so a template missing from it is a gap in the shipped set — invisible today, since
   Audit has no executor yet, and invisible *permanently* if nobody adds the line now.
5. **Point into core with `<CORE>`**, never a bare relative path — a shared-core satellite has no core
   directory of its own, so only the token resolves for every instance.

## Adding a model-facing template

Same manifest entry (step 4 above), same `<CORE>` rule (step 5). Otherwise document it inside itself
as freely as helps — that is the format working as intended.

## Where this is not true yet

Of the thirteen templates `spawn_satellite.py` copies, **nine are already in the script-facing format**.
Four are not, and the spawner absorbs the difference:

- `role-templates/overlay_template.md`, `pm_overlay_template.md`, `cross_role_template.md` — carry
  model-facing frontmatter and `<!-- -->` metadata. `_strip_template_metadata`, `_split_frontmatter`,
  `_HTML_COMMENT_RE` and three near-identical stamper functions exist for these three files.
- `gitignore_template.md` — prose wrapping the real content in a code fence, so `_extract_fenced_block`
  exists to unwrap it.

Converting them and deleting that machinery is **one change, not two**: `_split_frontmatter` raises on
a template that has no frontmatter, so converting a template on its own breaks the spawn, and deleting
the stripper on its own lands metadata in the instance. Whoever does it does both halves together.

Until then, this README is what a **new** template follows — not what every existing one does.
