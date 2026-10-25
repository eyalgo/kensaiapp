"""Contract tests for `product-skeleton/launcher.sh`.

**The model was the `seeds-from-product-docs` launcher**, read 2026-09-02 and removed 2026-09-25, for
the argument surface and card resolution this launcher shares with every sibling: `--instance-root`
first, one positional that is a PROJECT NAME (never a path — the shape check is the exact inverse
of the bare-word rule the `seeds-from-idea` launcher held until it was removed on 2026-10-24), the
project resolved through
`system/projects/<project>/project.md`, and its `Product path:` line read through the trailing HTML
comment exactly as every sibling reads it.

**The one design difference is the whole plan**
(`docs/proposals/product-skeleton-launcher/ad_hoc_plan.md`): every sibling launcher spawns a model
behind a fixed `claude --bg` prompt. This one spawns nothing — it reads the project's card and its
    product's settled `docs/SDD.md`, copies the language-and-kind trees under
    `core/templates/skeleton-templates/` for the units the SDD's own § 3 table names, and exits. A
    pre-units SDD retains the original language-root and part-directory behavior. No `claude`, no
    `--agent`, no `--permission-mode`, no
prompt, no completion watcher, no `--keep-awake`.

**The templates root is overridable** via `LAUNCH_PRODUCT_SKELETON_TEMPLATES_ROOT` — the same reason
`$WATCHER` is overridable on every sibling that spawns one: this suite builds its own fake trees
(the plan's own instruction, so the suite does not break every time a real tree changes) rather than
reading the real, ever-changing ones.

Isolation: the real script at its real location, an independent `tmp_path` tree standing in for a
whole instance (and its own fake skeleton-templates root, so no test ever touches
`core/templates/skeleton-templates/` for real).
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import subprocess
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent / "launcher.sh"


@pytest.fixture
def run(tmp_path, _session_pin):
    """`run(*cli_args, cwd=None) -> CompletedProcess`, invoking the real launcher with `tmp_path`
    standing in for the instance root. Helpers hang off the callable: `run.project(...)` writes a
    project card, `run.sdd(...)` writes a product's `docs/SDD.md` with a § 3 parts table,
    `run.tree(...)` builds a fake language tree under the env-overridden templates root, and
    `run.happy(...)` wires a minimal end-to-end-valid fixture for tests that need a clean run.
    `run.core_dir` is the session pin's own `core/` — every `<CORE>`-derived value (the templates
    root when not overridden) resolves there, since the launcher enters that pin before anything
    else reads `CORE_DIR` (Task 20)."""
    templates_root = tmp_path / "templates"
    templates_root.mkdir()
    home = tmp_path / "home"
    home.mkdir()

    env = dict(os.environ)
    env["HOME"] = str(home)
    env["LAUNCH_PRODUCT_SKELETON_TEMPLATES_ROOT"] = str(templates_root)

    def _run(*cli_args, cwd=None, use_env=None):
        return subprocess.run(
            [str(_SCRIPT), *cli_args],
            cwd=cwd or str(tmp_path),
            capture_output=True,
            text=True,
            env=use_env if use_env is not None else env,
        )

    def _product_root(product_path="products/thing"):
        p = Path(product_path)
        return p if p.is_absolute() else tmp_path / product_path

    def _project(
        name, product_path="products/thing", card=None, languages="pylang", slug="thing", roots=None
    ):
        project_dir = tmp_path / "system" / "projects" / name
        project_dir.mkdir(parents=True, exist_ok=True)
        if card is None:
            lines = [f"# {name}", "", f"**Product path:** {product_path}"]
            if languages is not None:
                lines.append(f"**Languages:** {languages}")
            if roots is not None:
                lines.append(f"**Language roots:** {roots}")
            if slug is not None:
                lines.append(f"**Package slug:** {slug}")
            card = "\n".join(lines) + "\n"
        (project_dir / "project.md").write_text(card)
        return project_dir

    def _sdd(
        product_path="products/thing",
        rows=(("connect-unit", "src"),),
        no_table=False,
        no_section=False,
        units=None,
    ):
        docs = _product_root(product_path) / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        if no_section:
            text = "# SDD\n\nNo § 3 at all in this document.\n"
        elif no_table:
            text = (
                "## 3. The parts, and the seams between them\n\n"
                "Prose only — no table follows.\n\n## 4. What every slice inherits\nstuff\n"
            )
        else:
            header = "| Part | Lives in | Owns | Must not own |\n|---|---|---|---|\n"
            body = "".join(f"| `{slug}` | `{lives}` | owns it | not this |\n" for slug, lives in rows)
            units_table = ""
            if units is not None:
                units_table = (
                    "**The units.**\n\n| Unit | Language | Kind |\n|---|---|---|\n"
                    + "".join(
                        f"| `{unit}` | `{language}` | `{kind}` |\n"
                        for unit, language, kind in units
                    )
                    + "\n"
                )
            text = (
                "## 3. The parts, and the seams between them\n\n**The parts.**\n\n"
                f"{header}{body}\n"
                "**The seams.**\n\n| Seam | What crosses | Owner of the contract |\n|---|---|---|\n"
                "| `connect-unit` <-> `x` | data | connect-unit |\n\n"
                f"{units_table}"
                "## 4. What every slice inherits\nstuff\n"
            )
        (docs / "SDD.md").write_text(text)
        return docs / "SDD.md"

    def _tree(lang, files=None, readme_only=False):
        lang_dir = templates_root / lang
        lang_dir.mkdir(parents=True, exist_ok=True)
        (lang_dir / "README.md").write_text(f"{lang} skeleton tree — documentation only.\n")
        if not readme_only:
            for relpath, content in (files or {}).items():
                p = lang_dir / relpath
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content)

    def _happy(name="example-product", product_path="products/thing", lang="pylang", slug="examplepkg", rows=(("connect-unit", "src"),)):
        _project(name, product_path=product_path, languages=lang, slug=slug)
        _sdd(product_path, rows=rows)
        _tree(lang, files={"main.py": "print('hi')\n", "pkg.json": '{"name": "__PROJECT__"}\n'})
        return name

    _run.root = tmp_path
    _run.templates_root = templates_root
    _run.env = env
    _run.core_dir = _session_pin.core
    _run.pin_root = _session_pin.root
    _run.product_root = _product_root
    _run.project = _project
    _run.sdd = _sdd
    _run.tree = _tree
    _run.happy = _happy
    return _run


def _files_under(root: Path):
    if not root.exists():
        return set()
    return {str(p.relative_to(root)) for p in root.rglob("*")}


# --- the pin (Task 20): the launcher enters it before anything else reads CORE_DIR -------------


def test_dry_run_prints_the_pin_line(run):
    run.happy("example-product")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert re.search(r"^Pin: .+\(inherited\)$", result.stdout, re.MULTILINE)


def test_units_table_builds_each_rust_crate_from_one_product_frame(run):
    run.project("example-product", languages="Rust", slug="example-product", roots="Rust=wrong-place")
    run.sdd(
        rows=(("reader", "crates/example-product-reader"), ("app", "crates/example-product-app")),
        units=(
            ("crates/example-product-reader", "Rust", "crate"),
            ("crates/example-product-app", "Rust", "crate"),
        ),
    )
    run.tree("rust/product", files={"Cargo.toml": '[workspace]\nmembers = ["crates/*"]\n'})
    run.tree(
        "rust/crate",
        files={"Cargo.toml": '[package]\nname = "__UNIT__"\n', "src/lib.rs": ""},
    )

    result = run("example-product")

    product = run.product_root()
    assert result.returncode == 0, result.stderr
    assert (product / "Cargo.toml").read_text() == '[workspace]\nmembers = ["crates/*"]\n'
    assert (product / "crates/example-product-reader/Cargo.toml").read_text() == (
        '[package]\nname = "example-product-reader"\n'
    )
    assert (product / "crates/example-product-app/Cargo.toml").read_text() == (
        '[package]\nname = "example-product-app"\n'
    )
    assert not (product / "wrong-place").exists()


def test_units_table_places_package_frame_at_its_unit(run):
    run.project("example-product", languages="TypeScript", slug="example-product")
    run.sdd(
        rows=(("renderer", "app-ui"),),
        units=(("app-ui", "TypeScript", "package"),),
    )
    run.tree(
        "typescript/package",
        files={"package.json": '{"name":"__UNIT__","product":"__PROJECT__"}\n'},
    )

    result = run("example-product")

    product = run.product_root()
    assert result.returncode == 0, result.stderr
    assert (product / "app-ui/package.json").read_text() == (
        '{"name":"app-ui","product":"example-product"}\n'
    )
    assert not (product / "package.json").exists()


def test_units_table_places_a_root_package_at_the_product_root(run):
    run.project("example-product", languages="TypeScript", slug="example-product")
    run.sdd(
        rows=(("renderer", ""),),
        units=(("", "TypeScript", "package"),),
    )
    run.tree("typescript/package", files={"package.json": '{"name":"__UNIT__"}\n'})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (run.product_root() / "package.json").read_text() == '{"name":"example-product"}\n'


# --- a built frame is left whole ------------------------------------------------------------------
#   Measured 2026-10-14 on a built product: the per-file guard placed `src/main.rs` beside a
#   library crate's `src/lib.rs`, turning the crate into a binary and failing the build. A frame is
#   placed whole or not at all.


def _built_rust_product(run):
    run.project("example-product", languages="Rust", slug="example-product")
    run.sdd(rows=(("reader", "crates/reader"),), units=(("crates/reader", "Rust", "crate"),))
    run.tree("rust/product", files={"Cargo.toml": "[workspace]\n", "rustfmt.toml": "edition = 1\n"})
    run.tree(
        "rust/crate",
        files={
            "Cargo.toml": "[package]\n",
            "src/lib.rs": "",
            "src/main.rs": "fn main() {}\n",
            "src/error.rs": "",
        },
    )
    product = run.product_root()
    (product / "crates/reader/src").mkdir(parents=True)
    (product / "Cargo.toml").write_text("[workspace] # mine\n")
    (product / "crates/reader/Cargo.toml").write_text("[package] # mine\n")
    (product / "crates/reader/src/lib.rs").write_text("pub fn mine() {}\n")
    return product


def test_a_unit_that_already_holds_its_frames_files_gets_none_of_the_rest(run):
    product = _built_rust_product(run)

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert not (product / "crates/reader/src/main.rs").exists()
    assert not (product / "crates/reader/src/error.rs").exists()
    assert not (product / "rustfmt.toml").exists()
    assert (product / "crates/reader/src/lib.rs").read_text() == "pub fn mine() {}\n"
    assert "already built" in result.stdout


def test_a_built_product_dry_runs_with_nothing_to_create(run):
    """product-card reads this dry run to decide whether to place anything at all."""
    _built_rust_product(run)

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "  file: " not in result.stdout
    assert "  dir: " not in result.stdout
    assert "already built (skip): crates/reader" in result.stdout


def test_a_new_unit_beside_a_built_one_still_gets_its_frame(run):
    product = _built_rust_product(run)
    run.sdd(
        rows=(("reader", "crates/reader"), ("app", "crates/app")),
        units=(("crates/reader", "Rust", "crate"), ("crates/app", "Rust", "crate")),
    )

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (product / "crates/app/src/main.rs").is_file()
    assert not (product / "crates/reader/src/main.rs").exists()


def test_a_language_root_that_already_holds_its_frames_files_gets_none_of_the_rest(run):
    """The pre-units path: a language tree is one frame, at its root."""
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("connect-unit", "src"),))
    run.tree("pylang", files={"main.py": "print(1)\n", "errors.py": "", "pkg.json": "{}\n"})
    product = run.product_root()
    (product / "main.py").write_text("print('mine')\n")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert not (product / "errors.py").exists()
    assert not (product / "pkg.json").exists()
    assert (product / "main.py").read_text() == "print('mine')\n"


def test_a_built_language_root_dry_runs_with_no_file_of_its_frame(run):
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("connect-unit", "src"),))
    run.tree("pylang", files={"main.py": "print(1)\n", "errors.py": ""})
    product = run.product_root()
    (product / "src" / "connect-unit").mkdir(parents=True)
    (product / "src" / "connect-unit" / "mine.py").write_text("")
    (product / "main.py").write_text("print('mine')\n")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "  file: " not in result.stdout
    assert "  dir: " not in result.stdout
    assert "already built (skip): ." in result.stdout


def test_a_shared_gitkeep_does_not_make_a_new_languages_frame_look_built(run):
    """Python, JavaScript and TypeScript all ship `tests/e2e/.gitkeep`. A product with one of them at
    the root that adds another must still get the new language's frame."""
    run.project("example-product", languages="pylang, jslang", slug="examplepkg")
    run.sdd("products/thing", rows=(("connect-unit", "src"),))
    run.tree("pylang", files={"main.py": "print(1)\n", "tests/e2e/.gitkeep": ""})
    run.tree("jslang", files={"main.js": "1\n", "tests/e2e/.gitkeep": ""})
    product = run.product_root()
    (product / "tests" / "e2e").mkdir(parents=True)
    (product / "tests" / "e2e" / ".gitkeep").write_text("")
    (product / "main.py").write_text("print('mine')\n")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (product / "main.js").is_file()
    assert (product / "main.py").read_text() == "print('mine')\n"


def test_units_table_refuses_when_a_lives_in_value_has_no_unit(run):
    run.project("example-product", languages="Rust", slug="example-product")
    run.sdd(
        rows=(("reader", "crates/example-product-reader"), ("app", "crates/example-product-app")),
        units=(("crates/example-product-reader", "Rust", "crate"),),
    )
    run.tree("rust/product", files={"Cargo.toml": "workspace\n"})
    run.tree("rust/crate", files={"Cargo.toml": "__UNIT__\n"})

    result = run("example-product")

    assert result.returncode != 0
    assert "crates/example-product-app" in result.stderr
    assert not (run.product_root() / "Cargo.toml").exists()
    assert not (run.product_root() / "crates").exists()


def test_directory_unit_creates_only_the_declared_directory(run):
    run.project("example-product", languages="Shell", slug="example-product")
    run.sdd(
        rows=(("acceptance", "checks"),),
        units=(("checks", "Shell", "directory"),),
    )
    run.tree("shell", readme_only=True)

    result = run("example-product")

    product = run.product_root()
    assert result.returncode == 0, result.stderr
    assert (product / "checks").is_dir()
    assert _files_under(product / "checks") == {".gitkeep"}


# --- Task 1 (behaviour 1) — the argument contract -----------------------------------------------


def test_no_args_dies_naming_the_project_as_required(run):
    result = run()

    assert result.returncode != 0
    assert "is required" in result.stderr


def test_no_args_dies_with_the_usage_line(run):
    result = run()

    assert result.returncode != 0
    assert "usage:" in result.stderr
    assert "<project>" in result.stderr


def test_instance_root_override_is_honoured(run, tmp_path_factory):
    elsewhere = tmp_path_factory.mktemp("elsewhere")
    run.happy("example-product")

    result = run("--instance-root", str(run.root), "example-product", "--dry-run", cwd=str(elsewhere))

    assert result.returncode == 0, result.stderr
    assert "example-product" in result.stdout


def test_more_than_one_positional_is_refused(run):
    run.happy("example-product")

    result = run("example-product", "other")

    assert result.returncode != 0
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}


def test_trailing_prose_after_the_project_is_refused_rather_than_ignored(run):
    run.happy("example-product")

    result = run("example-product", "and", "also", "summarise", "the", "previous", "round")

    assert result.returncode != 0


def test_unknown_flag_is_refused(run):
    run.happy("example-product")

    result = run("example-product", "--nonsense")

    assert result.returncode != 0


# --- Task 1 (behaviour 2) — a path is refused, not accepted -------------------------------------


def test_a_positional_with_a_slash_is_refused(run):
    result = run("system/projects/example-product")

    assert result.returncode != 0
    assert "looks like a path" in result.stderr
    assert "project name" in result.stderr.lower()


def test_a_positional_starting_with_a_dot_is_refused(run):
    result = run("./example-product")

    assert result.returncode != 0
    assert "looks like a path" in result.stderr


def test_a_path_shaped_positional_is_refused_even_when_it_points_at_a_real_project(run):
    """Behaviour 2 is a SHAPE rule: it never consults the filesystem, so a caller typing the card's
    own directory is refused for the shape, not for what is or is not there."""
    run.happy("example-product")

    result = run("system/projects/example-product")

    assert result.returncode != 0
    assert "looks like a path" in result.stderr


def test_a_bare_project_name_is_not_refused_as_a_path(run):
    run.project("example-product")

    result = run("example-product")

    assert "looks like a path" not in result.stderr


# --- Task 1 (behaviour 3) — the project must resolve ---------------------------------------------


def test_unknown_project_dies_naming_the_address_it_looked_at(run):
    result = run("nope")

    assert result.returncode != 0
    assert "system/projects/nope/project.md" in result.stderr


# --- Task 1 (behaviour 4) — Product path:, comment-stripped ---------------------------------------


def test_project_card_without_product_path_is_refused(run):
    run.project("example-product", card="# example-product\n\nno binding line here\n")

    result = run("example-product")

    assert result.returncode != 0
    assert "Product path" in result.stderr


def test_the_product_path_is_read_through_the_trailing_html_comment(run):
    (run.root / "system" / "projects" / "example-product").mkdir(parents=True)
    (run.root / "system" / "projects" / "example-product" / "project.md").write_text(
        "# example-product\n\n**Product path:** products/thing   <!-- set at scaffold -->\n"
        "**Languages:** pylang\n**Package slug:** examplepkg\n"
    )
    run.sdd("products/thing")
    run.tree("pylang", files={"main.py": "print(1)\n"})

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "<!--" not in result.stdout


def test_relative_product_path_resolves_under_the_instance_root(run):
    run.happy("example-product", product_path="products/thing")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert str(run.root / "products" / "thing") in result.stdout


def test_absolute_product_path_resolves_externally(run, tmp_path_factory):
    external = tmp_path_factory.mktemp("external_product")
    run.project("example-product", product_path=str(external), languages="pylang", slug="examplepkg")
    run.sdd(str(external))
    run.tree("pylang", files={"main.py": "print(1)\n"})

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert str(external) in result.stdout


def test_tilde_product_path_expands_to_home(run):
    run.project("example-product", product_path="~/products/thing", languages="pylang", slug="examplepkg")
    run.sdd(str(run.env["HOME"] + "/products/thing"))
    run.tree("pylang", files={"main.py": "print(1)\n"})

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert str(Path(run.env["HOME"]) / "products" / "thing") in result.stdout


# --- Task 1 (behaviour 5) — the three refusals fire before anything is written -------------------


def test_no_languages_line_dies_naming_the_file_and_what_is_missing(run):
    run.project("example-product", languages=None)
    run.sdd("products/thing")

    result = run("example-product")

    assert result.returncode != 0
    assert "project.md" in result.stderr
    assert "Languages" in result.stderr
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}


def test_missing_sdd_dies_naming_the_file(run):
    run.project("example-product", languages="pylang")

    result = run("example-product")

    assert result.returncode != 0
    assert "SDD.md" in result.stderr
    assert not run.product_root().exists()


def test_sdd_with_no_section_3_dies(run):
    run.project("example-product", languages="pylang")
    run.sdd("products/thing", no_section=True)

    result = run("example-product")

    assert result.returncode != 0
    assert "SDD.md" in result.stderr


def test_a_lives_in_cell_that_is_not_a_bare_path_is_refused(run):
    """A settled § 3 on disk carries ``app-core`, behind the **Sync port**` in a Lives in cell —
    prose, backticks and bold, in a column a tool joins to a slug to make a directory. Taken at
    face value it creates a directory of that name, punctuation and all, at exit 0. The template
    now fixes the cell as a bare path; this is the launcher half of that."""
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("sync-reader", "`core`, behind the **Sync port**"),))

    result = run("example-product")

    assert result.returncode != 0
    assert "Lives in" in result.stderr
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}


def test_a_lives_in_cell_escaping_the_product_root_is_refused(run):
    """`../..` in a Lives in cell wrote a directory outside the product at exit 0. The cell is
    joined to the product path, so anything that climbs out of it reaches the rest of the disk."""
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("escapee", "../../elsewhere"),))

    result = run("example-product")

    assert result.returncode != 0
    assert "Lives in" in result.stderr
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}


def test_an_unfilled_template_parts_table_is_refused_rather_than_taken_literally(run):
    """`sdd_template.md`'s own placeholder row is a well-formed table row, so it parses. Taken at
    face value it makes a directory literally named `<slug>` inside one named after the whole
    guidance sentence — a skeleton nobody asked for, on a product whose § 3 was never written.
    An angle-bracketed cell is the template speaking, not the design."""
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("<slug>", "<the module, package or crate this part belongs to>"),))

    result = run("example-product")

    assert result.returncode != 0
    assert "SDD.md" in result.stderr
    assert "<slug>" in result.stderr
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}


def test_a_part_slug_that_is_not_a_bare_kebab_case_slug_is_refused(run):
    """The `Part` column is whitelisted exactly as `Lives in` is, and for the same reason: the
    cell becomes a real directory name. `sdd_template.md` § 3 states the shape — "Lowercase letters
    and digits, single hyphens between them, and nothing else" — and names the positional label
    (`P-1`, `C-3`) as the thing a document reaches for on its own. A settled § 3 on disk is written
    in exactly that shape today."""
    run.happy("example-product", rows=(("P-1", "src"),))

    result = run("example-product")

    assert result.returncode != 0
    assert "P-1" in result.stderr
    assert "Part" in result.stderr
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}


def test_a_part_slug_with_a_space_in_it_is_refused(run):
    """A blacklist keyed on the template's `<...>` row let every other malformed cell through —
    a slug with a space became a directory with a space in its name at exit 0."""
    run.happy("example-product", rows=(("the connect unit", "src"),))

    result = run("example-product")

    assert result.returncode != 0
    assert "the connect unit" in result.stderr
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}


def test_a_partly_filled_placeholder_slug_is_refused_as_a_placeholder_not_as_a_malformed_slug(run):
    """The old blacklist matched a cell that *fullmatched* `<...>`, so `<slug>` was caught and
    `<slug>-unit` became a real directory of that name. Both are refused now, and the one that
    is still the template speaking says so — "you have not filled in the template" is a
    different problem, fixed in a different place, from "your slug is malformed"."""
    run.happy("example-product", rows=(("<slug>-unit", "src"),))

    result = run("example-product")

    assert result.returncode != 0
    assert "still carries the template's placeholder rows" in result.stderr
    assert "<slug>-unit" in result.stderr
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}


def test_a_part_slug_carrying_the_substitution_token_is_refused(run):
    """`Lives in` is checked on the SUBSTITUTED value because a module path may legitimately be
    named after the package. The slug may not, and the launcher proves it: the part directory is
    built from the RAW slug (`launcher.sh`'s `rel_dir = f"{lives_sub}/{slug}"`), so a token there
    would become a directory literally named `__PROJECT__-core`. The whitelist refuses it."""
    run.happy("example-product", rows=(("__PROJECT__-core", "src"),))

    result = run("example-product")

    assert result.returncode != 0
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}


def test_the_slugs_a_real_settled_sdd_carries_all_pass_the_whitelist(run):
    """Checked against the shape classes a settled § 3 actually carries, not against the template's
    own examples: a bare word, a two-segment name, a three-segment one, a two-character first
    segment, a digit-bearing slug, and a single character. Every class below was read off a real
    settled § 3 before being written here as a neutral name — the shape is what the whitelist sees,
    and it is all the shape that was ever load-bearing (`writing_bar.md` rule 2). `oauth2-client` is
    the one the template's prose admits by omission: kebab-case says nothing against a digit, and
    refusing it would be a shape stricter than the contract states. All create their
    directories."""
    real = (
        "io-reader", "feed-reader", "poller", "tree-model", "local-state",
        "template-renderer", "rpc-surface", "views", "end-to-end-harness",
        "oauth2-client", "s3", "a",
    )
    run.happy("example-product", rows=tuple((slug, "src") for slug in real))

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    for slug in real:
        assert (run.product_root() / "src" / slug).is_dir(), slug


def test_sdd_section_3_with_no_table_dies_naming_the_file(run):
    run.project("example-product", languages="pylang")
    run.sdd("products/thing", no_table=True)

    result = run("example-product")

    assert result.returncode != 0
    assert "SDD.md" in result.stderr
    assert "parts table" in result.stderr
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}


def test_nothing_is_created_for_any_of_the_three_refusals_even_under_a_language_that_would_have_worked(run):
    """The three refusals fire before the per-language loop ever runs — a card whose Languages:
    would otherwise resolve cleanly still creates nothing when the SDD itself is missing."""
    run.project("example-product", languages="pylang")
    run.tree("pylang", files={"main.py": "print(1)\n"})

    result = run("example-product")

    assert result.returncode != 0
    assert not run.product_root().exists()


# --- Task 1 (behaviour 6) — Package slug: supplies the substitution value ------------------------


def test_no_package_slug_dies(run):
    run.project("example-product", languages="pylang", slug=None)
    run.sdd("products/thing")
    run.tree("pylang", files={"main.py": "print(1)\n"})

    result = run("example-product")

    assert result.returncode != 0
    assert "Package slug" in result.stderr
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}


def test_the_no_package_slug_refusal_names_the_token_the_launcher_actually_substitutes(run):
    """This message is an f-string, and while the placeholder was `{{project}}` it printed
    `{project}` — a token the launcher neither substituted nor refused, told to an author who had
    not yet written the line the message is about. The assertion reads the token out of
    `substitute()` rather than restating it, so the message and the code cannot drift apart."""
    run.project("example-product", languages="pylang", slug=None)
    run.sdd("products/thing")
    run.tree("pylang", files={"main.py": "print(1)\n"})

    result = run("example-product")

    assert result.returncode != 0
    assert _substituted_token() in result.stderr, result.stderr


def test_package_slug_is_substituted_in_file_contents(run):
    run.happy("example-product", lang="pylang", slug="myslug")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    content = (run.product_root() / "pkg.json").read_text()
    assert content == '{"name": "myslug"}\n'


def test_package_slug_is_substituted_in_a_path_name(run):
    run.project("example-product", languages="rustish", slug="myslug")
    run.sdd("products/thing", rows=(("connect-unit", "crates/__PROJECT__"),))
    run.tree("rustish", files={"crates/__PROJECT__/Cargo.toml": 'name = "__PROJECT__"\n'})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (run.product_root() / "crates" / "myslug" / "Cargo.toml").is_file()
    assert not (run.product_root() / "crates" / "__PROJECT__").exists()


# --- Task 1 (behaviour 7) — one tree per declared language, three outcomes -----------------------


def test_a_language_with_a_real_tree_is_copied(run):
    run.happy("example-product", lang="pylang")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (run.product_root() / "main.py").is_file()
    assert (run.product_root() / "pkg.json").is_file()


def test_a_readme_only_language_is_skipped_and_reported_and_the_run_continues(run):
    run.project("example-product", languages="shellish, pylang", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("shellish", readme_only=True)
    run.tree("pylang", files={"main.py": "print(1)\n"})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert "shellish" in result.stdout
    assert "skipped" in result.stdout
    assert (run.product_root() / "main.py").is_file()
    assert not (run.product_root() / "README.md").exists()


def test_a_language_with_no_folder_at_all_is_fatal_naming_the_language_and_the_folder(run):
    run.project("example-product", languages="ghostlang", slug="examplepkg")
    run.sdd("products/thing")

    result = run("example-product")

    assert result.returncode != 0
    assert "ghostlang" in result.stderr
    assert str(run.templates_root / "ghostlang") in result.stderr
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}


def test_a_card_spelling_resolves_the_real_tree_lowercased(run):
    """The one case on this machine that can tell the case-fold from its absence.

    The volume is case-insensitive, so `<root>/Rust` and `<root>/rust` open the same directory
    whichever the code asks for and no placed file distinguishes them. What does distinguish them
    is the path the launcher says it looked for, which the refusal prints verbatim. Run against the
    pin's real templates root — the launcher enters the pin (Task 20) before this default is
    resolved, so what "real" means here is the pin's copy of the six trees, all lowercase, which
    is the string under test."""
    run.project("example-product", languages="Ghostlang", slug="examplepkg")
    run.sdd("products/thing")
    env = dict(run.env)
    env.pop("LAUNCH_PRODUCT_SKELETON_TEMPLATES_ROOT", None)

    result = run("example-product", use_env=env)

    assert result.returncode != 0
    assert "Ghostlang" in result.stderr, "the refusal must name the spelling the card used"
    assert str(run.core_dir / "templates" / "skeleton-templates" / "ghostlang") in result.stderr, (
        "the refusal must name the path actually looked for, and the lookup lowercases: the trees "
        "on disk are javascript, python, rust, shell, swift and typescript, while a card spells the "
        "language the way English does"
    )


def test_a_real_card_spelling_copies_the_real_tree(run):
    """The positive half, and the gap it closes: every other language case in this file runs
    against a fixture root of invented lowercase names — pylang, rustish, tslang, shellish, webby —
    so nothing here has ever asked a real tree for a real card's spelling. Dry run, because the
    product under tmp_path is not a git repo and the resolution is what is under test."""
    run.project("example-product", languages="Rust", slug="examplepkg")
    run.sdd("products/thing")
    env = dict(run.env)
    env.pop("LAUNCH_PRODUCT_SKELETON_TEMPLATES_ROOT", None)

    result = run("example-product", "--dry-run", use_env=env)

    assert result.returncode == 0, result.stderr
    for placed in ("Cargo.toml", "rustfmt.toml", "rust-toolchain.toml"):
        assert f"file: {placed}" in result.stdout, result.stdout


def test_a_real_swift_package_unit_places_the_real_tree_at_its_unit(run):
    """The Swift tree has no `package/` subtree, so a `package` unit resolves to the whole
    language tree and lands at the unit's path, with the token becoming the unit's name. Its two
    `.swiftpm` ignore entries are anchored by the slash in their middle, and the launcher re-anchors
    them under the unit; `/.build` was already rooted in the generated file, so it proves nothing on its own."""
    run.project("example-product", languages="Swift", slug="examplepkg")
    run.sdd(rows=(("shell", "app-mac"),), units=(("app-mac", "Swift", "package"),))
    env = dict(run.env)
    env.pop("LAUNCH_PRODUCT_SKELETON_TEMPLATES_ROOT", None)

    result = run("example-product", use_env=env)

    assert result.returncode == 0, result.stderr
    product = run.product_root()
    for placed in ("Package.swift", ".swift-format", "Sources/Core/CoreError.swift"):
        assert (product / "app-mac" / placed).is_file(), placed
    assert 'name: "app-mac"' in (product / "app-mac/Package.swift").read_text()
    ignore = (product / ".gitignore").read_text().splitlines()
    for entry in (
        "/app-mac/.build",
        "/app-mac/.swiftpm/configuration/registries.json",
        "/app-mac/.swiftpm/xcode/package.xcworkspace/contents.xcworkspacedata",
    ):
        assert entry in ignore, ignore


def test_multiple_languages_some_copied_some_skipped(run):
    run.project("example-product", languages="shellish, pylang, tslang", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("shellish", readme_only=True)
    run.tree("pylang", files={"main.py": "print(1)\n"})
    run.tree("tslang", files={"main.ts": "export {};\n"})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (run.product_root() / "main.py").is_file()
    assert (run.product_root() / "main.ts").is_file()
    assert "shellish" in result.stdout and "skipped" in result.stdout


# --- Task 1 (behaviour 9) — the launcher substitutes one token and inspects nothing else ---------
#
# It used to scan every copied file for a placeholder-shaped token it did not know and refuse the
# run. That check moved to `core/tools/test_skeleton_trees.py`, which holds the trees to the same
# rule at authoring time instead — the trees are ours, so a scan at the owner's copy time could
# only ever refuse something too late, and it could not tell a placeholder from ordinary code.
# The three cases below are what that scan kept getting wrong, and they are now what the launcher
# does with any file it does not understand: copies it, byte for byte.


def test_a_generic_type_parameter_is_copied_byte_for_byte(run):
    """Angle-bracket generics such as `Vec<String>` and `Option<T>` are ordinary code in three of
    the six languages (Rust, TypeScript and Swift), and the angle-bracketed placeholder this
    launcher started with refused both outright."""
    source = "fn f(v: Vec<String>) -> Option<T> { None }\n"
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("pylang", files={"lib.rs": source})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (run.product_root() / "lib.rs").read_text() == source


def test_html_markup_is_copied_byte_for_byte(run):
    """`<head>` is ordinary markup. Under the angle-bracket scan it had to be exempted by file
    extension, and that exemption then let a genuine stray token through in `.html` alone."""
    source = (
        "<!doctype html>\n<html><head><title>App</title></head>"
        "<body><script></script></body></html>\n"
    )
    run.project("example-product", languages="webby", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("webby", files={"index.html": source})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (run.product_root() / "index.html").read_text() == source


def test_a_typescript_generic_is_copied_byte_for_byte(run):
    source = "type LogContext = Record<string, unknown>;\n"
    run.project("example-product", languages="tslang", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("tslang", files={"logger.ts": source})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (run.product_root() / "logger.ts").read_text() == source


def test_a_format_string_brace_escape_is_copied_byte_for_byte(run):
    """`{{` / `}}` is the literal-brace escape in Python's `str.format` and f-strings and in
    Rust's `format!` family. While the launcher scanned for `{{…}}` a tree carrying one was
    refused at exit 1, and a tree carrying `{{project}}` inside a format string was silently
    rewritten at exit 0 — the second being a corruption the angle-bracket shape could not
    produce. The launcher no longer looks."""
    source = 'TEMPLATE = "hello {{name}} — config key {{scope}} must be quoted"\n'
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("pylang", files={"fmt.py": source})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (run.product_root() / "fmt.py").read_text() == source


def test_an_unknown_token_in_a_path_is_copied_as_that_path(run):
    """The path half of the same fact. A tree that carries a directory the launcher cannot
    substitute lands as that directory — which is why the rule over the trees exists, and why it
    checks paths as well as contents."""
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("pylang", files={"src/{{Scope}}/main.py": "pass\n"})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (run.product_root() / "src" / "{{Scope}}" / "main.py").is_file()


# --- Task 1 (behaviour 10) — a tree's own README.md is never copied -------------------------------


def test_a_trees_own_readme_is_never_copied(run):
    run.happy("example-product", lang="pylang")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert not (run.product_root() / "README.md").exists()


# --- Task 1 (behaviour 11) — one directory per part, from the SDD's parts table -------------------


def test_parts_table_rows_become_directories_holding_only_a_gitkeep(run):
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd(
        "products/thing",
        rows=(("connect-unit", "src"), ("store-unit", "src/store")),
    )
    run.tree("pylang", files={"main.py": "print(1)\n"})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    connect = run.product_root() / "src" / "connect-unit"
    store = run.product_root() / "src" / "store" / "store-unit"
    # A part carries nothing but the marker — the code that fills it does not exist yet — and the
    # marker is what lets git hold the directory at all.
    assert [p.name for p in connect.iterdir()] == [".gitkeep"]
    assert [p.name for p in store.iterdir()] == [".gitkeep"]
    assert (connect / ".gitkeep").read_text() == ""


def test_a_part_directory_survives_a_commit(run):
    """The defect this marker exists for, proven against git rather than against the filesystem:
    the first two live runs created 21 part directories and git could see one of them."""
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("connect-unit", "src"),))
    run.tree("pylang", files={"main.py": "print(1)\n"})

    assert run("example-product").returncode == 0

    product = run.product_root()
    for args in (["init"], ["add", "-A"]):
        assert subprocess.run(["git", *args], cwd=product, capture_output=True).returncode == 0
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=product, capture_output=True, text=True
    ).stdout.split()

    assert "src/connect-unit/.gitkeep" in tracked


def test_a_part_directory_that_already_holds_content_gets_no_marker(run):
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("connect-unit", "src"),))
    run.tree("pylang", files={"main.py": "print(1)\n"})
    part = run.product_root() / "src" / "connect-unit"
    part.mkdir(parents=True)
    (part / "keepme.txt").write_text("mine\n")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert not (part / ".gitkeep").exists()


def test_an_existing_but_empty_part_directory_gains_the_marker(run):
    """A product whose skeleton predates this behaviour is repaired by re-running, not by hand."""
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("connect-unit", "src"),))
    run.tree("pylang", files={"main.py": "print(1)\n"})
    (run.product_root() / "src" / "connect-unit").mkdir(parents=True)

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (run.product_root() / "src" / "connect-unit" / ".gitkeep").is_file()


def test_a_part_directory_a_tree_writes_into_gets_no_marker(run):
    """The tree's own file is what git will hold, so a second marker beside it is noise."""
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("connect-unit", "src"),))
    run.tree("pylang", files={"src/connect-unit/main.py": "print(1)\n"})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    part = run.product_root() / "src" / "connect-unit"
    assert (part / "main.py").is_file()
    assert not (part / ".gitkeep").exists()


def test_the_marker_is_listed_under_dry_run_and_written_by_neither_mode_twice(run):
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("connect-unit", "src"),))
    run.tree("pylang", files={"main.py": "print(1)\n"})

    planned = run("example-product", "--dry-run")
    assert planned.returncode == 0, planned.stderr
    assert "file: src/connect-unit/.gitkeep" in planned.stdout
    assert not run.product_root().exists() or not (
        run.product_root() / "src" / "connect-unit"
    ).exists()

    assert run("example-product").returncode == 0
    again = run("example-product", "--dry-run")

    assert again.returncode == 0, again.stderr
    assert "would create:\n" in again.stdout or "DRY RUN" in again.stdout
    assert "  file: " not in again.stdout
    assert "  dir: " not in again.stdout


def test_a_part_directory_nests_inside_a_location_the_copied_tree_already_established(run):
    run.project("example-product", languages="rustish", slug="myslug")
    run.sdd("products/thing", rows=(("connect-unit", "crates/__PROJECT__"),))
    run.tree("rustish", files={"crates/__PROJECT__/Cargo.toml": 'name = "__PROJECT__"\n'})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    part_dir = run.product_root() / "crates" / "myslug" / "connect-unit"
    assert part_dir.is_dir()
    assert (run.product_root() / "crates" / "myslug" / "Cargo.toml").is_file()


# --- Task 1 (behaviour 12) — it never overwrites ---------------------------------------------------


def test_an_existing_file_is_not_overwritten_and_is_reported(run):
    run.happy("example-product", lang="pylang")
    run.product_root().mkdir(parents=True, exist_ok=True)
    (run.product_root() / "pkg.json").write_text('{"name": "already-here"}\n')

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (run.product_root() / "pkg.json").read_text() == '{"name": "already-here"}\n'
    assert "pkg.json" in result.stdout
    assert "already exists" in result.stdout


def test_an_existing_part_directory_is_not_disturbed_and_is_reported(run):
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("connect-unit", "src"),))
    run.tree("pylang", files={"main.py": "print(1)\n"})
    (run.product_root() / "src" / "connect-unit").mkdir(parents=True)
    (run.product_root() / "src" / "connect-unit" / "keepme.txt").write_text("mine\n")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (run.product_root() / "src" / "connect-unit" / "keepme.txt").is_file()
    assert "src/connect-unit" in result.stdout
    assert "already exists" in result.stdout


def test_rerunning_on_a_product_that_already_has_its_skeleton_is_safe(run):
    run.happy("example-product", lang="pylang")

    first = run("example-product")
    second = run("example-product")

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert "already exists" in second.stdout


def test_a_second_trees_colliding_file_never_overwrites_the_first_trees(run):
    """Behaviour 12 states the invariant absolutely — *it never overwrites*. Two declared languages
    claiming the same product-root path is the ordinary multi-language case, not a defect. The first
    language declared on the card wins; the launcher must not silently replace what it has just
    written. (`.gitignore` is the one path this does not govern — see the combining section below,
    which is a deliberate exception rather than a hole in this invariant.)"""
    run.project("example-product", languages="jslang, rustish", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("jslang", files={"shared.cfg": "from-js\n"})
    run.tree("rustish", files={"shared.cfg": "from-rust\n"})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert (run.product_root() / "shared.cfg").read_text() == "from-js\n"


def test_a_second_trees_colliding_file_is_reported_rather_than_dropped_in_silence(run):
    """Behaviour 12's second half — the launcher *must say what it skipped*. A file a later tree
    could not place is exactly that, so it is reported the same way an already-present one is."""
    run.project("example-product", languages="jslang, rustish", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("jslang", files={"shared.cfg": "from-js\n"})
    run.tree("rustish", files={"shared.cfg": "from-rust\n"})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert "shared.cfg" in result.stdout
    assert "skipped" in result.stdout


def test_dry_run_lists_a_colliding_file_once_because_it_is_created_once(run):
    """Behaviour 13 — the listing is of what the run *would create*. One file is created, so it is
    listed once; listing it twice tells the reader two files land where one does."""
    run.project("example-product", languages="jslang, rustish", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("jslang", files={"shared.cfg": "from-js\n"})
    run.tree("rustish", files={"shared.cfg": "from-rust\n"})

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert result.stdout.count("file: shared.cfg") == 1


# --- .gitignore is combined, not skipped ----------------------------------------------------------
#
# The one path where "never overwrites" would lose something the product needs. A tree's
# `.gitignore` is not a frame the product might already have its own version of — it is a list of
# what that language's toolchain generates, and a product that declares the language needs every
# entry of it whether or not it already has a file at that path. Measured 2026-09-03 on the first
# two live runs: one product gained Rust and was left with no `/target`, the other gained JavaScript
# and was left with no `node_modules/`. Both files were skipped correctly and both products were
# wrong.
#
# So `.gitignore` is combined: the product's own file is kept whole and the entries it lacks are
# appended. The owner's call, 2026-09-03.


def _gitignore(run):
    return (run.product_root() / ".gitignore").read_text()


def _write_product_gitignore(run, text):
    root = run.product_root()
    root.mkdir(parents=True, exist_ok=True)
    (root / ".gitignore").write_text(text)


def test_an_entry_the_products_own_gitignore_lacks_is_appended(run):
    run.project("example-product", languages="rustish", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("rustish", files={".gitignore": "/target\n"})
    _write_product_gitignore(run, "node_modules/\n")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert "/target" in _gitignore(run)


def test_the_products_own_gitignore_is_kept_whole_and_first(run):
    """Appended, never rewritten: the product's file is its own and this launcher adds to the end
    of it. A reader who knows their file must still recognise it afterwards."""
    original = "# mine\nnode_modules/\n.DS_Store\n"
    run.project("example-product", languages="rustish", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("rustish", files={".gitignore": "/target\n"})
    _write_product_gitignore(run, original)

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert _gitignore(run).startswith(original)


def test_an_entry_the_product_already_has_is_not_duplicated(run):
    run.project("example-product", languages="rustish", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("rustish", files={".gitignore": "/target\nnode_modules/\n"})
    _write_product_gitignore(run, "node_modules/\n")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert _gitignore(run).count("node_modules/") == 1


def test_every_declared_language_contributes_its_missing_entries(run):
    """The live case: a product declaring two languages needs both toolchains' entries, and under
    the plain never-overwrite rule the second language's file was dropped entirely."""
    run.project("example-product", languages="jslang, rustish", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("jslang", files={".gitignore": "node_modules/\n"})
    run.tree("rustish", files={".gitignore": "/target\n"})
    _write_product_gitignore(run, ".DS_Store\n")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    text = _gitignore(run)
    assert "node_modules/" in text and "/target" in text


def test_a_comment_in_a_trees_gitignore_is_not_appended_as_an_entry(run):
    """Only entries carry over. The tree's own section headers describe that tree, not the product's
    file, and copying them in leaves a reader tracing a comment to a file they cannot see."""
    run.project("example-product", languages="rustish", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("rustish", files={".gitignore": "# Build output\n\n/target\n"})
    _write_product_gitignore(run, "node_modules/\n")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert "# Build output" not in _gitignore(run)
    assert "/target" in _gitignore(run)


def test_the_appended_block_says_where_the_entries_came_from(run):
    """A line that appears in someone's `.gitignore` without explanation is a line nobody dares
    delete. The block names the launcher and the language."""
    run.project("example-product", languages="rustish", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("rustish", files={".gitignore": "/target\n"})
    _write_product_gitignore(run, "node_modules/\n")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    text = _gitignore(run)
    assert "product-skeleton" in text
    assert "rustish" in text


def test_rerunning_appends_nothing_and_leaves_the_file_byte_identical(run):
    run.project("example-product", languages="rustish", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("rustish", files={".gitignore": "/target\n"})
    _write_product_gitignore(run, "node_modules/\n")

    assert run("example-product").returncode == 0
    after_first = _gitignore(run)
    assert run("example-product").returncode == 0

    assert _gitignore(run) == after_first


def test_a_product_with_no_gitignore_gets_every_declared_languages_entries(run):
    """The same loss in the fresh case: the first tree placed its file and the second tree's was
    skipped as a collision, so a new product was short its second language's entries too."""
    run.project("example-product", languages="jslang, rustish", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("jslang", files={".gitignore": "node_modules/\n"})
    run.tree("rustish", files={".gitignore": "/target\n"})

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    text = _gitignore(run)
    assert "node_modules/" in text and "/target" in text


def test_the_dry_run_names_the_entries_it_would_append_and_writes_nothing(run):
    run.project("example-product", languages="rustish", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("rustish", files={".gitignore": "/target\n"})
    _write_product_gitignore(run, "node_modules/\n")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "/target" in result.stdout
    assert _gitignore(run) == "node_modules/\n"


def test_a_gitignore_needing_nothing_is_reported_as_needing_nothing(run):
    run.project("example-product", languages="rustish", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("rustish", files={".gitignore": "/target\n"})
    _write_product_gitignore(run, "/target\n")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert ".gitignore" in result.stdout
    assert _gitignore(run) == "/target\n"


# --- Task 1 (behaviour 13) — --dry-run --------------------------------------------------------------


def test_dry_run_creates_nothing(run):
    run.happy("example-product", lang="pylang")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert not run.product_root().joinpath("main.py").exists()
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}


def test_dry_run_prints_every_file_and_every_directory_it_would_create(run):
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("connect-unit", "src"),))
    run.tree("pylang", files={"tests/e2e/probe.py": "pass\n", "pkg.json": '{"name": "__PROJECT__"}\n'})

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "DRY RUN" in result.stdout
    assert "file: pkg.json" in result.stdout
    assert "file: tests/e2e/probe.py" in result.stdout
    assert "dir: tests" in result.stdout
    assert "dir: tests/e2e" in result.stdout
    assert "dir: src/connect-unit" in result.stdout


@pytest.mark.parametrize(
    "break_it",
    [
        "bad_project",
        "path_shaped",
        "no_languages",
        "no_slug",
        "missing_sdd",
        "no_parts_table",
        "missing_language_folder",
    ],
)
def test_every_refusal_still_fires_under_dry_run(run, break_it):
    if break_it == "bad_project":
        result = run("nope", "--dry-run")
        assert "system/projects/nope/project.md" in result.stderr
    elif break_it == "path_shaped":
        result = run("some/path", "--dry-run")
        assert "looks like a path" in result.stderr
    elif break_it == "no_languages":
        run.project("example-product", languages=None)
        run.sdd("products/thing")
        result = run("example-product", "--dry-run")
        assert "Languages" in result.stderr
    elif break_it == "no_slug":
        run.project("example-product", languages="pylang", slug=None)
        run.sdd("products/thing")
        run.tree("pylang", files={"main.py": "print(1)\n"})
        result = run("example-product", "--dry-run")
        assert "Package slug" in result.stderr
    elif break_it == "missing_sdd":
        run.project("example-product", languages="pylang")
        result = run("example-product", "--dry-run")
        assert "SDD.md" in result.stderr
    elif break_it == "no_parts_table":
        run.project("example-product", languages="pylang")
        run.sdd("products/thing", no_table=True)
        result = run("example-product", "--dry-run")
        assert "parts table" in result.stderr
    elif break_it == "missing_language_folder":
        run.project("example-product", languages="ghostlang", slug="examplepkg")
        run.sdd("products/thing")
        result = run("example-product", "--dry-run")
        assert "ghostlang" in result.stderr

    assert result.returncode != 0
    assert not run.product_root().joinpath("main.py").exists()


# --- Task 1 (behaviour 14) — no model is ever spawned ------------------------------------------------


def test_the_launcher_source_spawns_no_model_and_holds_no_agent_permission_flags():
    text = _SCRIPT.read_text()
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))

    for forbidden in ("claude --bg", "--agent", "--permission-mode", "caffeinate", "watch_agent", "detach_watcher"):
        assert forbidden not in code, f"{forbidden!r} found in launcher.sh's executable code"


def test_a_full_run_never_touches_a_watcher_or_notifier(run):
    """Effect-based companion to the source check: a real end-to-end run leaves no watcher log and
    no trace of a background process."""
    run.happy("example-product", lang="pylang")

    run("example-product")

    assert not (run.root / "system" / "logs").exists()


# --- executable / syntax -----------------------------------------------------------------------------


def test_launcher_is_executable():
    assert os.access(_SCRIPT, os.X_OK), f"{_SCRIPT} is not executable"


def test_launcher_syntax_is_valid_bash():
    result = subprocess.run(["bash", "-n", str(_SCRIPT)], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


def test_the_default_templates_root_is_core_templates_skeleton_templates_when_not_overridden(run):
    """No override set — proves `CORE_DIR` resolves from the script's own location (a prefix
    strip at the `/launchers/` boundary, not a fixed number of parent steps), rather than the
    caller's instance root. The launcher enters the pin (Task 20) before this default is built, so the
    root it names is the pin's own `core/templates/skeleton-templates`."""
    run.project("example-product", languages="a-language-nobody-registered", slug="examplepkg")
    run.sdd("products/thing")
    env = dict(run.env)
    env.pop("LAUNCH_PRODUCT_SKELETON_TEMPLATES_ROOT", None)

    result = run("example-product", use_env=env)

    assert result.returncode != 0
    assert str(run.core_dir / "templates" / "skeleton-templates") in result.stderr


# --- Task 3 — the manifest names the launcher and the trees --------------------------------------

_STRUCTURE_MAP = Path(__file__).resolve().parents[2] / "doctrine" / "setup" / "kensaiapp_structure.md"


def _section(heading: str) -> str:
    text = _STRUCTURE_MAP.read_text()
    start = text.index(heading)
    end = text.index("\n### ", start + 1)
    return text[start:end]


def test_the_manifest_names_the_new_launcher_within_its_section():
    section = _section("### Owner-run launcher folder")

    assert section.count("product-skeleton") >= 1


def test_the_manifest_names_the_skeleton_templates_trees_and_the_declared_absence():
    section = _section("### Templates layer")

    assert "skeleton-templates" in section
    assert "shell" in section


def _substituted_token() -> str:
    """The token out of the launcher itself — `substitute()`'s own argument, so the two manifest
    rules below cannot both be updated to agree on a token the code does not use."""
    _, body = _halves()
    match = re.search(r"return text\.replace\(\"([^\"]+)\", package_slug\)", body)
    assert match, "launcher.sh's substitute() no longer reads `text.replace(\"<token>\", package_slug)`"
    return match.group(1)


def test_both_manifest_entries_name_the_token_the_launcher_actually_substitutes():
    """The one fact in those two entries a launcher change can silently invalidate, and it has:
    the placeholder was `<project>`, then `{{project}}`, then `__PROJECT__`, and each move left the
    manifest a revision behind while both tests above stayed green. They assert the sections exist;
    this asserts they are still true."""
    token = _substituted_token()

    for heading in ("### Owner-run launcher folder", "### Templates layer"):
        section = _section(heading)
        assert token in section, (
            f"{heading} does not name {token!r}, which is what "
            "`core/launchers/product-skeleton/launcher.sh` substitutes today"
        )


# =====================================================================================
# The two absolutes — rules over every path, and the sweep the rules keep complete
# =====================================================================================
#
# `core/doctrine/engineering/testing_doctrine.md:75` — "Layers 1–5 prove behaviour for the
# paths a test happened to walk. Layer 6 proves a property over *every* path... A guarantee
# stated as an absolute ("never writes", "never executes") wants a layer-6 rule, not only a
# layer-5 test."
#
# This launcher states exactly two absolutes: it CREATES NOTHING WHEN IT REFUSES, and it
# SPAWNS NO MODEL. An independent audit broke both on purpose and the suite stayed green at
# 58 passed — mutations M6 and M13 in
# `system/projects/launchers/docs/skeleton-branch-audit-launcher/delegate-report.md` (F1, F4).
# Both were covered only by cases someone had thought of, which is what an absolute cannot be.
#
# So each absolute gets a RULE — a property of the launcher's own structure that holds for
# every path, including a refusal added next year — and, where a rule cannot reach (a spelling
# no list enumerates, a process that only exists at runtime), an EFFECT check that watches the
# behaviour rather than the text. The per-case sweep below is still layer 5, but its
# completeness is enforced by a rule: a new `die` in the launcher with no case in the sweep
# turns the suite red.
#
# Every check here was proved to discriminate by mutation; the mutations and their results are
# in `system/projects/launchers/docs/launcher-absolutes-guarded/delegate-report.md`.

_HEREDOC_RE = re.compile(r"^python3 - .*<<'PYEOF'\n(?P<body>.*?)\n^PYEOF$", re.MULTILINE | re.DOTALL)


def _halves() -> tuple[str, str]:
    """`(bash_half, python_half)`. Fails closed: every rule below is stated in terms of this
    boundary, so if the launcher stops embedding its Python in a `<<'PYEOF'` heredoc the rules
    must be re-derived rather than quietly go on passing over a file they can no longer read."""
    text = _SCRIPT.read_text()
    match = _HEREDOC_RE.search(text)
    assert match, (
        "launcher.sh no longer embeds its Python half in a `python3 - ... <<'PYEOF'` heredoc. "
        "Every rule in this section reads the two halves through that boundary — re-derive them "
        "against the new shape rather than deleting this assertion."
    )
    return text[: match.start()], match.group("body")


def _bash_code_lines() -> list[tuple[int, str]]:
    """Executable bash lines, numbered from 1 of launcher.sh, with whole-line and trailing
    ` #` comments removed — the header block is 75 lines of prose about `claude --bg` and
    would trip every rule below on its own."""
    bash, _ = _halves()
    out = []
    for lineno, line in enumerate(bash.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        out.append((lineno, re.sub(r"\s#.*$", "", line)))
    return out


def _python_tree():
    """`(tree, parents)` for the embedded Python. The ordering rule below is only sound for
    calls at module level and outside a loop, so it establishes both rather than assuming
    them — which needs the parent links."""
    _, body = _halves()
    tree = ast.parse(body)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    return tree, parents


def _in_function(node, parents) -> str | None:
    while node in parents:
        node = parents[node]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name
        if isinstance(node, ast.Lambda):
            return "<lambda>"
    return None


def _enclosing_loops(node, parents) -> list:
    loops = []
    while node in parents:
        node = parents[node]
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            loops.append(node)
    return loops


def _die_calls(tree) -> list:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "die"
    ]


# Python's filesystem-mutation surface, split by how it is spelled. Qualified: `os.rename`.
# Unqualified: `fh.write`, `path.mkdir` — deliberately narrower, because `str.replace` and
# `list.remove` share names with `os.replace` and `os.remove` and are not writes.
_QUALIFIED_WRITE_FUNCS = frozenset(
    """makedirs mkdir rename renames replace remove removedirs unlink rmdir symlink link
    truncate chmod chown utime mknod copy copy2 copyfile copytree copymode copystat move
    rmtree make_archive unpack_archive write writelines""".split()
)
_UNQUALIFIED_WRITE_METHODS = frozenset(
    """write writelines write_text write_bytes touch mkdir makedirs unlink rmdir rename
    symlink_to hardlink_to""".split()
)
_WRITE_MODULES = frozenset({"os", "shutil", "pathlib", "tempfile"})


def _is_std_stream(node) -> bool:
    """`sys.stderr.write(...)` is output, not a write to the disk."""
    return isinstance(node, ast.Attribute) and node.attr in ("stdout", "stderr")


def _python_write_sites(tree) -> list[tuple[int, str, object]]:
    """`(lineno, what, node)` for every call in the embedded Python that can touch the disk."""
    sites = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            base = func.value.id if isinstance(func.value, ast.Name) else None
            if base in _WRITE_MODULES and func.attr in _QUALIFIED_WRITE_FUNCS:
                sites.append((node.lineno, f"{base}.{func.attr}", node))
            elif (
                base not in _WRITE_MODULES
                and func.attr in _UNQUALIFIED_WRITE_METHODS
                and not _is_std_stream(func.value)
            ):
                sites.append((node.lineno, f".{func.attr}", node))
        elif isinstance(func, ast.Name) and func.id == "open":
            mode = None
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                mode = node.args[1].value
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            if isinstance(mode, str) and set(mode) & set("wax+"):
                sites.append((node.lineno, f"open(mode={mode!r})", node))
    return sites


class _RefusalSite:
    """One `die` call in the launcher, and the literal fragments of its message — the parts a
    run actually prints, with every interpolated value removed."""

    def __init__(self, origin: str, lineno: int, chunks: tuple[str, ...]):
        self.origin = origin
        self.lineno = lineno
        self.chunks = chunks

    @property
    def key(self):
        return (self.origin, self.lineno)

    def __repr__(self):
        longest = max(self.chunks, key=len) if self.chunks else ""
        return f"{self.origin} die at line {self.lineno}: {longest.strip()[:70]!r}"


def _refusal_sites() -> list[_RefusalSite]:
    """Every refusal the launcher can raise, read out of the launcher rather than listed here —
    which is the whole point: a refusal added later appears in this list on its own."""
    bash, body = _halves()
    sites = []

    for match in re.finditer(r'die\s+"((?:[^"\\]|\\.)*)"', bash, re.DOTALL):
        chunks = tuple(
            c for c in re.split(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?", match.group(1)) if c.strip()
        )
        sites.append(_RefusalSite("bash", bash[: match.start()].count("\n") + 1, chunks))

    tree, _parents = _python_tree()
    for node in _die_calls(tree):
        if not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            chunks = (arg.value,)
        elif isinstance(arg, ast.JoinedStr):
            chunks = tuple(
                v.value for v in arg.values if isinstance(v, ast.Constant) and isinstance(v.value, str)
            )
        else:
            chunks = ()
        sites.append(_RefusalSite("python", node.lineno, chunks))

    return sites


def _snapshot(root: Path) -> dict[str, str]:
    """Every path under `root`, files by content hash — so "created nothing" also covers
    "changed nothing", and covers it everywhere in the fixture world rather than only inside
    the product root."""
    out = {}
    for path in sorted(root.rglob("*")):
        rel = str(path.relative_to(root))
        if path.is_symlink():
            out[rel] = "symlink:" + os.readlink(path)
        elif path.is_dir():
            out[rel] = "dir"
        else:
            out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


# --- Absolute 1 — it creates nothing when it refuses ---------------------------------------
#
# THE RULE. The launcher's own header (`launcher.sh:50-54`) states it for every refusal, not
# only the three the plan named: "everything is validated and planned before the first byte is
# written". In a straight-line script that is a statement about source order, and source order
# is checkable: if every `die` sits above every write, and neither is hidden inside a function
# that could be called out of order, then no refusal can fire after a byte has been written —
# for the refusals that exist today and for any added later. That is the layer-6 half.


def test_every_refusal_in_the_python_half_sits_above_every_write_it_could_reach():
    """The two-phase guarantee, as a property of the source rather than of the cases below.

    Three clauses, and all three are load-bearing — source order only implies execution order
    when nothing jumps: a write hidden in a helper can run before a later refusal, and a write
    inside a loop that also refuses runs before the NEXT iteration's refusal even though it sits
    below it in the file. That last one is how the audit's mutation M6 (an eager write at the
    foot of phase 1's per-language loop) survives a plain line-order rule."""
    tree, parents = _python_tree()
    dies = _die_calls(tree)
    writes = _python_write_sites(tree)

    # Not vacuous: a scan that has stopped seeing either half would otherwise pass silently. The
    # floor is one below the real count (8 today, 10 before the unknown-token scan moved out to
    # `core/tools/test_skeleton_trees.py`) — it exists to catch an extractor that has stopped
    # working, so it tracks the count rather than standing above it.
    assert len(dies) >= 7, f"only {len(dies)} refusals found — the `die` scan has stopped working"
    assert len(writes) >= 3, f"only {len(writes)} writes found — the write scan has stopped working"

    misplaced_dies = [(n.lineno, _in_function(n, parents)) for n in dies if _in_function(n, parents)]
    assert not misplaced_dies, (
        f"a refusal is raised inside a function ({misplaced_dies}) — source order no longer "
        "implies execution order, so the rule below cannot be trusted. Keep refusals at module "
        "level, or replace this rule with one that follows the call graph."
    )
    misplaced_writes = [
        (line, what, _in_function(node, parents))
        for line, what, node in writes
        if _in_function(node, parents)
    ]
    assert not misplaced_writes, (
        f"a write is hidden inside a function ({misplaced_writes}) — a phase-1 helper could then "
        "write before a later refusal fires, which is exactly what this rule exists to forbid."
    )

    writes_in_a_refusing_loop = [
        (line, what, loop.lineno)
        for line, what, node in writes
        for loop in _enclosing_loops(node, parents)
        if any(die in ast.walk(loop) for die in dies)
    ]
    assert not writes_in_a_refusing_loop, (
        f"a write shares a loop with a refusal ({writes_in_a_refusing_loop} — write line, what, "
        "loop line). Line order says nothing here: the loop's next iteration can refuse after "
        "this iteration has already written, which is the multi-language half-written skeleton "
        "the launcher's header exists to forbid."
    )

    last_refusal = max(n.lineno for n in dies)
    first_write = min(line for line, _what, _node in writes)
    assert last_refusal < first_write, (
        f"a write at heredoc line {first_write} precedes the last refusal at heredoc line "
        f"{last_refusal} — a refusal after that write leaves a half-written skeleton, which the "
        "launcher's header calls worse than none."
    )


def test_the_bash_half_creates_nothing_before_the_python_half_is_reached():
    """The other half of the same rule: every write in this launcher lives in the Python half,
    so the bash half — which is where the first five refusals fire — must touch nothing at all."""
    forbidden_commands = re.compile(r"\b(mkdir|touch|cp|mv|ln|rm|rmdir|tee|dd|install|rsync)\b")
    # `>&2` is not a file and neither is `/dev/null` — this rule is about creating something.
    to_a_device = re.compile(r">>?\s*/dev/\w+")
    file_redirect = re.compile(r"(?:^|\s|\s\d)>>?(?!&)")

    offenders = []
    for lineno, line in _bash_code_lines():
        if forbidden_commands.search(line) or file_redirect.search(to_a_device.sub("", line)):
            offenders.append((lineno, line.strip()))

    assert not offenders, (
        f"the bash half writes to the filesystem: {offenders}. Every refusal in the bash half "
        "fires before the Python half runs, so anything it creates is created before the run "
        "has decided whether to proceed."
    )


# THE SWEEP, and the rule that keeps it complete. The sweep is layer 5 — one case per refusal,
# each asserting the whole fixture world is byte-identical afterwards. What makes it more than
# "two more tests that pass" is the coverage rule below it, which reads the refusals out of
# launcher.sh: a refusal with no case here is a failing test, not a silent gap.


def _fix_card_without_product_path(run):
    run.project("example-product", card="# example-product\n\n**Languages:** pylang\n**Package slug:** thing\n")


def _fix_nothing(run):
    return None


def _fix_no_languages(run):
    run.project("example-product", languages=None)
    run.sdd("products/thing")


def _fix_missing_sdd(run):
    run.project("example-product", languages="pylang")
    run.tree("pylang", files={"main.py": "print(1)\n"})


def _fix_sdd_without_section_3(run):
    run.project("example-product", languages="pylang")
    run.sdd("products/thing", no_section=True)
    run.tree("pylang", files={"main.py": "print(1)\n"})


def _fix_sdd_section_3_without_a_table(run):
    run.project("example-product", languages="pylang")
    run.sdd("products/thing", no_table=True)
    run.tree("pylang", files={"main.py": "print(1)\n"})


def _fix_unfilled_parts_table(run):
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("<slug>", "<the module this part belongs to>"),))
    run.tree("pylang", files={"main.py": "print(1)\n"})


def _fix_no_package_slug(run):
    run.project("example-product", languages="pylang", slug=None)
    run.sdd("products/thing")
    run.tree("pylang", files={"main.py": "print(1)\n"})


def _fix_lives_in_is_prose(run):
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("sync-reader", "`core`, behind the **Sync port**"),))
    run.tree("pylang", files={"main.py": "print(1)\n"})


def _fix_lives_in_escapes_the_product(run):
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("escapee", "../../elsewhere"),))
    run.tree("pylang", files={"main.py": "print(1)\n"})


def _fix_part_slug_is_not_a_slug(run):
    run.project("example-product", languages="pylang", slug="examplepkg")
    run.sdd("products/thing", rows=(("P-1", "src"),))
    run.tree("pylang", files={"main.py": "print(1)\n"})


def _fix_language_without_a_tree(run):
    run.project("example-product", languages="ghostlang", slug="examplepkg")
    run.sdd("products/thing")


def _fix_a_good_language_then_one_without_a_tree(run):
    """The mid-loop refusal M6 exposed: the first language is fully planned and would have been
    written under a write-as-you-go launcher before the second language is even looked at."""
    run.project("example-product", languages="goodlang, ghostlang", slug="examplepkg")
    run.sdd("products/thing")
    run.tree("goodlang", files={"main.py": "print(1)\n", "src/app.py": "print(2)\n"})


# --- `Language roots:` — a frame lands where the card says -------------------------------------


def test_a_language_with_no_root_declared_lands_at_the_product_root(run):
    """The default, and the whole reason the field is optional. Every product written before it
    existed says nothing, and must come out exactly as it did."""
    run.happy()

    run("example-product")

    assert (run.product_root() / "main.py").is_file()


def test_a_language_given_a_root_lands_under_it_and_not_at_the_product_root(run):
    run.project("example-product", languages="tslang", slug="examplepkg", roots="tslang=ui")
    run.sdd("products/thing")
    run.tree("tslang", files={"package.json": '{"name": "__PROJECT__"}\n', "src/main.ts": "export {}\n"})

    run("example-product")

    assert (run.product_root() / "ui" / "package.json").is_file()
    assert (run.product_root() / "ui" / "src" / "main.ts").is_file()
    assert not (run.product_root() / "package.json").exists()
    # `src/` at the product root DOES exist, and not from this tree: the default SDD fixture's parts
    # table puts its parts in `src`, and a part's `Lives in` is product-root-relative by the
    # template's own definition — a part belongs to a module, not to a language. The two placements
    # compose rather than compete, so the assertion is on the tree's own file.
    assert not (run.product_root() / "src" / "main.ts").exists()


def test_one_language_is_rooted_and_the_other_is_not_in_the_same_run(run):
    """A live product's shape: a Rust host at the product root and a TypeScript renderer in its own
    directory. The defect this field exists for put both at the root."""
    run.project("example-product", languages="rustish, tslang", slug="examplepkg", roots="tslang=ui")
    run.sdd("products/thing")
    run.tree("rustish", files={"Cargo.toml": "[package]\n"})
    run.tree("tslang", files={"package.json": "{}\n"})

    run("example-product")

    assert (run.product_root() / "Cargo.toml").is_file()
    assert (run.product_root() / "ui" / "package.json").is_file()
    assert not (run.product_root() / "package.json").exists()


def test_a_root_of_dot_means_the_product_root(run):
    """A card may state the default rather than leave it implied."""
    run.project("example-product", languages="pylang", slug="examplepkg", roots="pylang=.")
    run.sdd("products/thing")
    run.tree("pylang", files={"main.py": "print(1)\n"})

    run("example-product")

    assert (run.product_root() / "main.py").is_file()


def test_two_trees_that_would_collide_at_the_root_do_not_when_one_is_rooted(run):
    """The collision machinery exists because every tree lands at the same root. Give one of them a
    root of its own and both files are written, neither skipped as claimed."""
    run.project("example-product", languages="jslang, tslang", slug="examplepkg", roots="tslang=ui")
    run.sdd("products/thing")
    run.tree("jslang", files={"package.json": '{"from": "js"}\n'})
    run.tree("tslang", files={"package.json": '{"from": "ts"}\n'})

    run("example-product")

    assert (run.product_root() / "package.json").read_text() == '{"from": "js"}\n'
    assert (run.product_root() / "ui" / "package.json").read_text() == '{"from": "ts"}\n'


def test_a_rooted_trees_leading_slash_ignore_pattern_is_reanchored(run):
    """A leading slash anchors a pattern to the directory its `.gitignore` sits in. Merged into the
    product-root file unchanged it would ignore a path nothing writes and leave the real one
    tracked. `rust/.gitignore`'s `/target` and `swift/.gitignore`'s rooted entries are the only ones
    across the six real trees."""
    run.project("example-product", languages="rustish", slug="examplepkg", roots="rustish=host")
    run.sdd("products/thing")
    run.tree("rustish", files={"Cargo.toml": "[package]\n", ".gitignore": "/target\n"})

    run("example-product")

    body = (run.product_root() / ".gitignore").read_text()
    assert "/host/target" in body
    assert not re.search(r"^/target$", body, re.MULTILINE)


def test_a_rooted_trees_middle_slash_ignore_pattern_is_reanchored(run):
    """A slash in the middle anchors a pattern exactly as a leading one does ("If there is a
    separator at the beginning or middle ... the pattern is relative to the directory level of the
    particular .gitignore file itself", git-scm.com/docs/gitignore). Merged unchanged, `a/b` from a
    tree rooted at `host/` would match `<product>/a/b` and leave `<product>/host/a/b` tracked. A
    `**/` pattern matches at any depth and stays as it is."""
    run.project("example-product", languages="rustish", slug="examplepkg", roots="rustish=host")
    run.sdd("products/thing")
    run.tree(
        "rustish",
        files={"Cargo.toml": "[package]\n", ".gitignore": "gen/out\n!gen/keep\n**/cache/x\n"},
    )

    run("example-product")

    body = (run.product_root() / ".gitignore").read_text()
    assert re.search(r"^/host/gen/out$", body, re.MULTILINE)
    assert re.search(r"^!/host/gen/keep$", body, re.MULTILINE)
    assert re.search(r"^\*\*/cache/x$", body, re.MULTILINE)
    assert not re.search(r"^gen/out$", body, re.MULTILINE)


def test_an_ordinary_ignore_pattern_is_left_alone_when_a_tree_is_rooted(run):
    """A pattern with no leading slash already matches at any depth, so re-anchoring it would be
    wrong as well as unnecessary."""
    run.project("example-product", languages="jslang", slug="examplepkg", roots="jslang=ui")
    run.sdd("products/thing")
    run.tree("jslang", files={"package.json": "{}\n", ".gitignore": "node_modules/\ndist/\n"})

    run("example-product")

    body = (run.product_root() / ".gitignore").read_text()
    assert "node_modules/" in body
    assert "dist/" in body
    assert "/ui/node_modules/" not in body
    assert "/ui/dist/" not in body


def _fix_language_root_is_not_a_pair(run):
    run.project("example-product", languages="pylang", slug="examplepkg", roots="pylang")
    run.sdd("products/thing")
    run.tree("pylang", files={"main.py": "print(1)\n"})


def _fix_language_root_names_an_undeclared_language(run):
    run.project("example-product", languages="pylang", slug="examplepkg", roots="tslang=ui")
    run.sdd("products/thing")
    run.tree("pylang", files={"main.py": "print(1)\n"})


def _fix_units_table_has_no_rows(run):
    run.project("example-product", languages="Rust", slug="example-product")
    run.sdd(rows=(("reader", "crates/reader"),), units=())


def _fix_unit_path_is_not_bare(run):
    run.project("example-product", languages="Rust", slug="example-product")
    run.sdd(rows=(("reader", "crates/reader"),), units=(("../reader", "Rust", "crate"),))


def _fix_duplicate_unit(run):
    run.project("example-product", languages="Rust", slug="example-product")
    run.sdd(
        rows=(("reader", "crates/reader"),),
        units=(("crates/reader", "Rust", "crate"), ("crates/reader", "Rust", "crate")),
    )


def _fix_unit_language_is_undeclared(run):
    run.project("example-product", languages="Rust", slug="example-product")
    run.sdd(rows=(("ui", "app-ui"),), units=(("app-ui", "TypeScript", "package"),))


def _fix_unit_kind_is_unknown(run):
    run.project("example-product", languages="Rust", slug="example-product")
    run.sdd(rows=(("reader", "crates/reader"),), units=(("crates/reader", "Rust", "bundle"),))


def _fix_buildable_unit_has_no_language(run):
    run.project("example-product", languages="Rust", slug="example-product")
    run.sdd(rows=(("reader", "crates/reader"),), units=(("crates/reader", "none", "crate"),))


def _fix_unit_has_no_lives_in(run):
    run.project("example-product", languages="Shell", slug="example-product")
    run.sdd(
        rows=(("checks", "checks"),),
        units=(("checks", "Shell", "directory"), ("fixtures", "none", "directory")),
    )


def _fix_buildable_unit_has_no_kind_tree(run):
    run.project("example-product", languages="Rust", slug="example-product")
    run.sdd(rows=(("reader", "crates/reader"),), units=(("crates/reader", "Rust", "crate"),))


# (case id, fixture, argv, a fragment of the refusal's own message)
REFUSAL_CASES = [
    ("no_positional", _fix_nothing, (), "is required — a project under"),
    ("path_shaped_positional", _fix_nothing, ("some/path",), "looks like a path"),
    ("unknown_flag", _fix_nothing, ("example-product", "--wat"), "unknown argument: "),
    ("unknown_project", _fix_nothing, ("nope",), "no project card at "),
    ("card_without_product_path", _fix_card_without_product_path, ("example-product",), "no 'Product path:' line in "),
    ("no_languages_line", _fix_no_languages, ("example-product",), "no 'Languages:' line"),
    ("missing_sdd", _fix_missing_sdd, ("example-product",), "not found — the skeleton launcher reads its § 3"),
    ("sdd_without_section_3", _fix_sdd_without_section_3, ("example-product",), "§ 3 carries no parts table"),
    ("sdd_section_3_without_a_table", _fix_sdd_section_3_without_a_table, ("example-product",), "§ 3 carries no parts table"),
    ("unfilled_parts_table", _fix_unfilled_parts_table, ("example-product",), "still carries the template's placeholder rows"),
    ("no_package_slug", _fix_no_package_slug, ("example-product",), "no 'Package slug:' line"),
    ("part_slug_is_not_a_slug", _fix_part_slug_is_not_a_slug, ("example-product",), "column must be a slug"),
    ("lives_in_is_prose", _fix_lives_in_is_prose, ("example-product",), "The column is joined to the part's slug"),
    ("lives_in_escapes_the_product", _fix_lives_in_escapes_the_product, ("example-product",), "The column is joined to the part's slug"),
    ("language_root_is_not_a_pair", _fix_language_root_is_not_a_pair, ("example-product",), "must be `<language>=<path>` pairs"),
    ("language_root_names_an_undeclared_language", _fix_language_root_names_an_undeclared_language, ("example-product",), "which `Languages:` does not declare"),
    ("units_table_has_no_rows", _fix_units_table_has_no_rows, ("example-product",), "units table has no rows"),
    ("unit_path_is_not_bare", _fix_unit_path_is_not_bare, ("example-product",), "unit path"),
    ("duplicate_unit", _fix_duplicate_unit, ("example-product",), "units table names"),
    ("unit_language_is_undeclared", _fix_unit_language_is_undeclared, ("example-product",), "which the project card does not declare"),
    ("unit_kind_is_unknown", _fix_unit_kind_is_unknown, ("example-product",), "has unknown Kind"),
    ("buildable_unit_has_no_language", _fix_buildable_unit_has_no_language, ("example-product",), "buildable unit"),
    ("unit_has_no_lives_in", _fix_unit_has_no_lives_in, ("example-product",), "one unit per distinct `Lives in` value"),
    ("buildable_unit_has_no_kind_tree", _fix_buildable_unit_has_no_kind_tree, ("example-product",), "skeleton for language"),
    ("language_without_a_tree", _fix_language_without_a_tree, ("example-product",), "no skeleton tree for language '"),
    ("good_language_then_one_without_a_tree", _fix_a_good_language_then_one_without_a_tree, ("example-product",), "no skeleton tree for language '"),
]


@pytest.mark.parametrize(
    "fixture,argv,expect", [c[1:] for c in REFUSAL_CASES], ids=[c[0] for c in REFUSAL_CASES]
)
def test_a_refusal_leaves_the_whole_tree_exactly_as_it_found_it(run, fixture, argv, expect):
    fixture(run)
    before = _snapshot(run.root)

    result = run(*argv)

    assert result.returncode != 0, f"expected a refusal, got exit 0:\n{result.stdout}"
    assert expect in result.stderr, f"refused for the wrong reason:\n{result.stderr}"
    after = _snapshot(run.root)
    assert after == before, (
        "the refusal changed the tree — created: "
        f"{sorted(set(after) - set(before))}, removed: {sorted(set(before) - set(after))}, "
        f"modified: {sorted(k for k in set(before) & set(after) if before[k] != after[k])}"
    )


def test_every_refusal_the_launcher_can_raise_has_a_case_in_the_sweep():
    """The rule that makes the sweep above worth more than the cases in it. The refusals are
    read out of `launcher.sh` — every `die` in either half — so a refusal path added later with
    no case here fails this test instead of going uncovered in silence."""
    sites = _refusal_sites()
    # 13 today; 15 before the unknown-token scan moved out to `core/tools/test_skeleton_trees.py`.
    # Same margin of one as before — the floor guards the extractor, not the launcher's size.
    assert len(sites) >= 12, (
        f"only {len(sites)} refusals found in launcher.sh — the extractor has stopped seeing "
        "them, which would make this rule pass over anything"
    )

    covered = {}
    for case_id, _fixture, _argv, expect in REFUSAL_CASES:
        hits = [site for site in sites if any(expect in chunk for chunk in site.chunks)]
        assert len(hits) == 1, (
            f"case {case_id!r} expects {expect!r}, which matches {len(hits)} refusals in "
            f"launcher.sh ({hits}). Each case must name exactly one, or this rule cannot tell "
            "which refusals are actually covered."
        )
        covered.setdefault(hits[0].key, []).append(case_id)

    uncovered = [site for site in sites if site.key not in covered]
    assert not uncovered, (
        f"{len(uncovered)} refusal(s) in launcher.sh have no case in REFUSAL_CASES: {uncovered}. "
        "Add one — 'nothing is created' is an absolute, so a refusal nobody exercises is the "
        "half of it that goes unproven."
    )


# --- Absolute 2 — it spawns no model -------------------------------------------------------
#
# Two rules and two effect checks, because the two halves of this script are not equally
# checkable. Python's process-creation surface is a closed set, so the Python half gets a real
# rule: no import and no call that could start a process, whatever it is spelled. Bash's is
# not closed — any word on a line is a command — so the bash half gets a rule over the
# constructs that detach (which is what a spawn needs) plus two runtime checks that watch for
# the effect: a PATH shim that catches a spawn by any spelling that resolves through PATH, and
# a process-group probe that catches one that outlives the run however it was invoked.


def test_the_python_half_cannot_start_a_process_at_all():
    """A closed-set rule, not a blocklist: this is Python's entire process-creation surface,
    plus the dynamic-execution builtins that would let any of it back in unseen."""
    tree, _ = _python_tree()
    forbidden_imports = {"subprocess", "multiprocessing", "pty", "asyncio", "sh", "pexpect"}
    forbidden_builtins = {"eval", "exec", "compile", "__import__"}
    offenders = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in forbidden_imports:
                    offenders.append((node.lineno, f"import {alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in forbidden_imports:
                offenders.append((node.lineno, f"from {node.module} import ..."))
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                qualified = f"{func.value.id}.{func.attr}"
                starts_a_process = func.value.id == "os" and (
                    func.attr.startswith(("exec", "spawn", "posix_spawn"))
                    or func.attr in {"system", "popen", "fork", "forkpty", "startfile"}
                )
                if starts_a_process or func.value.id in forbidden_imports:
                    offenders.append((node.lineno, qualified))
            elif isinstance(func, ast.Name) and func.id in forbidden_builtins:
                offenders.append((node.lineno, func.id))

    assert not offenders, (
        f"the embedded Python can start a process: {offenders} (heredoc line numbers). This "
        "launcher is a copier — the whole design difference from every sibling is that no model "
        "runs behind it."
    )


def test_the_bash_half_names_no_model_and_holds_no_way_to_detach_one():
    """A spawn needs two things a rule can see: the name of something to run, and — for a
    watcher — a way to leave it running. `claude` is word-bounded rather than flag-bounded, so
    `claude --print`, `claude -p` and a bare `claude` are all caught, which the six-string
    blocklist above (kept, and now subsumed) was not: audit mutation M13 inserted
    `MODEL_CMD="claude --print"` and a live `nohup ... &` and stayed green at 58 passed."""
    detachers = re.compile(
        r"\b(nohup|setsid|disown|coproc|caffeinate|osascript|screen|tmux|launchctl|crontab)\b"
    )
    background = re.compile(r"(?<![&>0-9])&(?!&)")
    agent_flags = re.compile(r"--(agent|permission-mode|keep-awake|bg)\b")

    offenders = []
    for lineno, line in _bash_code_lines():
        for what, pattern in (
            ("names `claude`", re.compile(r"\bclaude\b")),
            ("detaches a process", detachers),
            ("backgrounds a command", background),
            ("carries an agent/permission flag", agent_flags),
        ):
            if pattern.search(line):
                offenders.append((lineno, what, line.strip()))

    assert not offenders, f"the bash half can spawn a model: {offenders}"


_SPAWN_SHIMS = (
    "claude", "caffeinate", "nohup", "setsid", "osascript", "screen", "tmux", "launchctl", "open",
)


def _with_spawn_shims(run):
    """A PATH whose front holds a fake `claude` (and every detacher a watcher would use), each
    of which records that it ran. Catches a spawn by any spelling that resolves through PATH —
    which a source blocklist structurally cannot."""
    shim_dir = run.root / "spawn-shims"
    shim_dir.mkdir(exist_ok=True)
    marker = run.root / "spawn-marker.txt"
    for name in _SPAWN_SHIMS:
        script = shim_dir / name
        script.write_text(f'#!/bin/sh\necho "$0 $@" >> "{marker}"\n')
        script.chmod(0o755)
    env = dict(run.env)
    env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', '')}"
    return env, marker


def _fixture_for_mode(run, mode):
    if mode == "refusal":
        run.project("example-product", languages="ghostlang", slug="examplepkg")
        run.sdd("products/thing")
        return ("example-product",)
    run.happy("example-product", lang="pylang")
    return ("example-product", "--dry-run") if mode == "dry_run" else ("example-product",)


@pytest.mark.parametrize("mode", ["real_run", "dry_run", "refusal"])
def test_no_run_reaches_a_model_or_a_detacher_on_PATH(run, mode):
    """The `proof` run first is not ceremony: a shim that is never reached looks exactly like a
    launcher that never spawns, so the test proves the trap is armed before trusting it empty."""
    argv = _fixture_for_mode(run, mode)
    env, marker = _with_spawn_shims(run)

    proof = subprocess.run(
        ["sh", "-c", "claude --print hello; nohup true"],
        cwd=str(run.root), env=env, capture_output=True, text=True,
    )
    assert marker.exists(), (
        f"the shims are not on the launcher's PATH, so this test proves nothing: {proof.stderr}"
    )
    marker.unlink()

    run(*argv, use_env=env)

    assert not marker.exists(), (
        f"the launcher invoked something it must never invoke:\n{marker.read_text()}"
    )


def _survivors_after(argv, env, cwd, tmp) -> tuple[subprocess.CompletedProcess, bool]:
    """Run in its own process group and ask, the moment the launcher itself exits, whether
    anything is still alive in that group. A detached watcher stays in the group it inherited,
    so this catches a spawn by any spelling at all — including one the PATH shim never sees
    because it was invoked by absolute path.

    Output goes to FILES, not pipes, and the wait is on the launcher alone. With pipes, a
    background child inherits them and `communicate()` blocks until that child exits — so the
    probe would find the group empty every time and report clean over a live spawn. Measured:
    it reported clean over a plain `sleep 2 &` before this was changed."""
    out_path, err_path = tmp / "run.out", tmp / "run.err"
    with open(out_path, "w") as out_fh, open(err_path, "w") as err_fh:
        proc = subprocess.Popen(
            argv, cwd=str(cwd), env=env, stdout=out_fh, stderr=err_fh, start_new_session=True,
        )
        proc.wait(timeout=120)
    try:
        os.killpg(proc.pid, 0)
        survivors = True
    except ProcessLookupError:
        survivors = False
    except PermissionError:
        survivors = True
    return (
        subprocess.CompletedProcess(argv, proc.returncode, out_path.read_text(), err_path.read_text()),
        survivors,
    )


@pytest.mark.parametrize("spawner_line", ["sleep 5 &", "nohup sleep 5 >/dev/null 2>&1 &"])
def test_the_process_group_probe_would_catch_a_detached_child(
    tmp_path, warm_executables, spawner_line
):
    """Same guard, for the probe below: prove it reports True for a script that does background
    something — both the naive spelling that inherits the caller's file descriptors and the
    detached one — so a False from the launcher means what it says. The two scripts come from
    `warm_executables` so the probe's `wait(timeout=120)` holds no first exec of either."""
    spawner = warm_executables.link(
        tmp_path / "spawner.sh", f"#!/bin/sh\n{spawner_line}\necho done\n")
    quiet = warm_executables.link(tmp_path / "quiet.sh", "#!/bin/sh\necho done\n")

    _, spawner_survivors = _survivors_after([str(spawner)], dict(os.environ), tmp_path, tmp_path)
    _, quiet_survivors = _survivors_after([str(quiet)], dict(os.environ), tmp_path, tmp_path)

    assert spawner_survivors, "the probe cannot see a backgrounded child — it proves nothing"
    assert not quiet_survivors, "the probe reports survivors for a script that spawns nothing"


@pytest.mark.parametrize("mode", ["real_run", "dry_run", "refusal"])
def test_the_launcher_leaves_no_process_behind(run, mode, tmp_path_factory):
    argv = _fixture_for_mode(run, mode)
    scratch = tmp_path_factory.mktemp("probe")

    result, survivors = _survivors_after([str(_SCRIPT), *argv], run.env, run.root, scratch)

    assert not survivors, (
        "something the launcher started is still running after it exited — every sibling "
        f"launcher detaches a watcher, and this one must not.\nstderr: {result.stderr}"
    )


# --- the run commits, in the product's own repo ----------------------------------------------------
#
# The launcher spawns no model, so nobody was left to commit what it wrote and the owner found the
# tree sitting uncommitted after the first two live runs. It commits through the one builder
# (`<CORE>/tools/commit_builder.py`) rather than calling git itself — same trailers as every other
# commit in the fleet, with `Surface: product-skeleton` and no `Co-Authored-By:`, because no model
# authored these bytes. The owner's call, 2026-09-03.


def _init_product_repo(run, product_path="products/thing"):
    root = run.product_root(product_path)
    root.mkdir(parents=True, exist_ok=True)
    for args in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    (root / "README.md").write_text("product\n")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True, capture_output=True)
    return root


def _log(root, fmt="%B"):
    return subprocess.run(
        ["git", "-C", str(root), "log", "-1", f"--format={fmt}"], capture_output=True, text=True
    ).stdout


def test_the_run_commits_what_it_wrote_in_the_product_repo(run):
    root = _init_product_repo(run)
    run.happy("example-product", lang="pylang")

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files"], capture_output=True, text=True
    ).stdout.split()
    # What the launcher wrote is committed. The fixture's own docs/SDD.md is not, and must not be:
    # the launcher commits what it wrote, not whatever happened to be lying around.
    assert "main.py" in tracked
    assert "src/connect-unit/.gitkeep" in tracked
    assert "docs/SDD.md" not in tracked


def test_the_commit_carries_surface_product_skeleton_and_no_model(run):
    root = _init_product_repo(run)
    run.happy("example-product", lang="pylang")

    assert run("example-product").returncode == 0

    message = _log(root)
    assert "Surface: product-skeleton" in message
    assert "Co-Authored-By:" not in message
    assert "Role: Product" in message


def test_the_commit_carries_the_products_own_agari_directional(run):
    root = _init_product_repo(run)
    run.happy("example-product", lang="pylang")

    assert run("example-product").returncode == 0

    assert "Agari: example-product" in _log(root)


def test_a_dry_run_commits_nothing(run):
    root = _init_product_repo(run)
    run.happy("example-product", lang="pylang")
    head = _log(root, "%H")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert _log(root, "%H") == head


def test_a_run_that_writes_nothing_makes_no_commit(run):
    """Re-running on a product that already has its skeleton changes no file, so there is nothing to
    commit and an empty commit would be a lie about what happened."""
    root = _init_product_repo(run)
    run.happy("example-product", lang="pylang")
    assert run("example-product").returncode == 0
    head = _log(root, "%H")

    second = run("example-product")

    assert second.returncode == 0, second.stderr
    assert _log(root, "%H") == head


def test_the_commit_stages_only_what_the_launcher_wrote(run):
    """The product may hold the owner's own uncommitted work; the run must not sweep it in."""
    root = _init_product_repo(run)
    run.happy("example-product", lang="pylang")
    (root / "mine.txt").write_text("not the launcher's\n")

    assert run("example-product").returncode == 0

    status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True
    ).stdout
    assert "mine.txt" in status


def test_a_product_that_is_not_a_git_repo_still_gets_its_tree(run):
    """The tree is the job; the commit is bookkeeping on top of it. A product with no repo yet keeps
    what was written and is told the commit did not happen, rather than losing the run."""
    run.happy("example-product", lang="pylang")

    result = run("example-product")

    assert (run.product_root() / "main.py").is_file()
    assert "commit" in (result.stdout + result.stderr).lower()


def test_the_python_heredoc_is_never_nested_in_a_substitution():
    """The landmine that cost a full implementation pass, 2026-09-03.

    Inside `$( )` or `< <( )`, bash keeps parsing the body of a quoted heredoc and chokes on an ODD
    number of backticks in it. The Python half's comments carry 97. The failure passes `bash -n`
    and appears only at runtime as `bad substitution: no closing )`, which names neither the
    heredoc nor the backtick — so the obvious shape for handing the written paths back to the shell
    is a trap that looks correct and is not.

    The launcher's answer is a pipe off a brace group, which does no such re-parse. This holds it
    there: an editor reaching for `$(python3 - ... <<'PYEOF')` gets told why it will not work rather
    than discovering it from a runtime message about a paren nobody wrote."""
    text = _SCRIPT.read_text()
    opener = re.search(r"^(?P<prefix>.*)python3 - .*<<'PYEOF'$", text, re.MULTILINE)
    assert opener, "the Python half no longer opens with a `python3 - ... <<'PYEOF'` line"
    prefix = opener.group("prefix")

    assert "$(" not in prefix and "<(" not in prefix, (
        f"the Python heredoc is nested inside a substitution: {prefix!r}. Bash re-parses the "
        "heredoc body there and an odd backtick count in the Python half's comments breaks the "
        "launcher at runtime while `bash -n` still passes. Pipe off a brace group instead."
    )


def test_the_two_halves_spell_the_markers_the_same_way():
    """The path handover is a string contract across a language boundary: Python prints the marker,
    bash matches it. Nothing but this test connects the two spellings, and a mismatch would mean a
    run that writes the tree and silently commits nothing."""
    text = _SCRIPT.read_text()
    _, body = _halves()

    for marker in ("__SKELETON_PATH__", "__SKELETON_SUMMARY__"):
        assert marker in body, f"the Python half no longer emits {marker}"
        after = text[text.index("\nPYEOF") :]
        assert marker in after, f"the shell half no longer reads {marker}"


# --- characterization: the bare-path refusals no test reached (refactor sweep, 2026-09-23) ------
# The Lives in refusal is covered above; the same bare-path rule also guards a Language roots
# destination and a units-table path, and nothing exercised either. These pin today's refusal
# for each, on both halves of the rule: a path the pattern rejects, and one that climbs out.


@pytest.mark.parametrize("dest", ["../out", "ui dir"])
def test_a_language_root_that_is_not_a_bare_path_is_refused(run, dest):
    run.project("example-product", languages="tslang", slug="examplepkg", roots=f"tslang={dest}")
    run.sdd("products/thing")
    run.tree("tslang", files={"package.json": "{}\n"})

    result = run("example-product")

    assert result.returncode != 0
    assert "Language roots" in result.stderr
    assert "not a bare product-root-relative path" in result.stderr
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}


@pytest.mark.parametrize("unit", ["../escape", "crates/a b"])
def test_a_units_table_path_that_is_not_a_bare_path_is_refused(run, unit):
    run.project("example-product", languages="Rust", slug="example-product")
    # The parts row stays bare so the Lives in refusal does not fire first; the unit row alone is bad.
    run.sdd(rows=(("reader", "crates/reader"),), units=((unit, "Rust", "crate"),))
    run.tree("rust/crate", files={"Cargo.toml": "__UNIT__\n"})

    result = run("example-product")

    assert result.returncode != 0
    assert f"unit path {unit!r} must be bare and relative to the product root" in result.stderr
    assert _files_under(run.product_root()) == {"docs", "docs/SDD.md"}
