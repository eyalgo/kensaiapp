"""A skeleton tree may carry no placeholder token but the one the launcher substitutes.

WHY THIS EXISTS, AND WHY IT IS A TEST RATHER THAN A CHECK IN THE LAUNCHER
    `core/launchers/product-skeleton/launcher.sh` copies these trees into a product, substituting
    one token. It used to also scan every copied file and refuse the run on a placeholder-shaped
    token it did not know. That check was in the wrong place: **the trees are ours.** They are
    vendored under `core/templates/skeleton-templates/`, authored in this repo, and reviewed in
    this repo — so the scan was a check on our own artifacts, executed on the owner's machine at
    copy time, which is the last moment anything can be done about it and long after the bad tree
    shipped.

    It also could not tell code from a placeholder, and every shape tried made that worse in a
    different way. `<project>` refused `Vec<String>` and `Option<T>`, and `<head>` in
    `typescript/index.html` forced an exemption by file extension which then let a genuine stray
    token through in that one file type. `{{project}}` refused Python's and Rust's literal-brace
    escape, and silently rewrote a format string that happened to contain it. `__PROJECT__` — the
    token the launcher substitutes today — would have to be scanned for as `__…__`, which is
    `__name__`, `__main__`, `__future__`, `__file__` and `__pycache__`, five of them in `python/`
    alone, and `__DEV__` is a live bundler convention in the two JavaScript trees.

    That last one is why no shape ever fixes this. A placeholder is only a placeholder because we
    agreed it is; a scanner has nothing to tell it apart from the identifier beside it, and each
    shape simply moves which legitimate construct it collides with.

    A test does not have that problem. It runs in CI against a known set of files, its false
    positive is a red build at authoring time rather than a refusal in front of the owner, and
    when a tree legitimately needs one of these shapes the exemption is written here, once, with
    its reason — which is a conversation a launcher cannot have with anyone.

WHAT IS SCANNED
    Exactly what the launcher copies: every file under `core/templates/skeleton-templates/<lang>/`
    except that tree's own `README.md`, which is excluded from the copy at `launcher.sh`'s
    `non_readme` filter and may therefore quote any token it likes. Content and relative path
    both, because the launcher substitutes in both.

WHAT COUNTS AS A PLACEHOLDER-SHAPED TOKEN
    Three shapes, each with its own reason, and none of them a judgement call:

    - `__UPPERCASE__` other than `__PROJECT__` — the token's own shape, so this is the rule that
      catches a tree inventing a second one. That includes `__UNIT__`, which the launcher does
      substitute, but only when the SDD carries a units table: with none, `plan_tree` runs
      `substitute()` alone, which replaces `__PROJECT__` and nothing else, so a tree carrying
      `__UNIT__` would land with it literal. Every tree here is copied on both paths. Uppercase
      only, which is what keeps `__name__`, `__main__`, `__future__`, `__file__` and
      `__pycache__` out of it. `__DEV__` and `__VERSION__`
      are a real bundler convention and would trip this: if a tree ever needs one, exempt that file
      here, with the reason, rather than widening the shape.
    - the project-stamper's tokens `<project>`, `<name>`, `<scope>` — a closed set of three exact
      strings, so no generic and no HTML tag can trip it. They are here because they are the
      shapes a tree author reaches for by mistake: `skills/interactive-product/.claude/skills/project-stamp/` substitutes
      them when it stamps a project's **management folder**, and nothing substitutes them here.
      The two are separate systems that never touch the same files.
    - `{{identifier}}` — residue from the shape the placeholder briefly had on 2026-09-02, and the
      shape a hand-written template reaches for by habit. A Python or Rust format string wanting a
      literal brace around a bare identifier (`format!("{{name}}")`) is the one legitimate
      construct this refuses; no tree has needed it, and the day one does, exempt that file here.

    A generic (`Vec<String>`, `Record<string, unknown>`) and an HTML tag (`<head>`) match none of
    the three. That is the whole point of stating shapes rather than scanning for angle brackets.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TREES = REPO / "core" / "templates" / "skeleton-templates"

# The one token the launcher substitutes, from `launcher.sh`'s `substitute()`.
SUBSTITUTED_TOKEN = "__PROJECT__"

# `__UPPERCASE__` — the substituted token's own shape. Uppercase only, so `__name__`, `__main__`,
# `__future__`, `__file__` and `__pycache__` are not tokens.
_SCREAMING = re.compile(r"__([A-Z][A-Z0-9_]*)__")
# The project-stamper's set, as exact strings rather than a shape.
_STAMPER_TOKENS = ("<project>", "<name>", "<scope>")
# `{{identifier}}` — residue from the shape the placeholder briefly had, and nothing substitutes it.
_BRACED = re.compile(r"\{\{([A-Za-z][A-Za-z0-9_]*)\}\}")


def _copied_files() -> list[Path]:
    """Every file the launcher would copy, from disk — never from a list here, so a file added to
    a tree tomorrow is covered without anyone remembering to add it."""
    if not TREES.is_dir():
        return []
    out = []
    for tree in sorted(p for p in TREES.iterdir() if p.is_dir()):
        for path in sorted(tree.rglob("*")):
            if path.is_file() and path.relative_to(tree) != Path("README.md"):
                out.append(path)
    return out


def _tokens_in(text: str) -> list[str]:
    found = [f"__{m}__" for m in _SCREAMING.findall(text) if f"__{m}__" != SUBSTITUTED_TOKEN]
    found += [t for t in _STAMPER_TOKENS if t in text]
    found += ["{{" + m + "}}" for m in _BRACED.findall(text)]
    return found


def _id(path: Path) -> str:
    return str(path.relative_to(TREES))


def test_there_are_trees_to_check():
    """Guard the guard. An empty glob would make every test below vacuously pass, and that is not
    a hypothetical: `shell/` is a declared absence holding only its own README, so the walk
    genuinely does return nothing for one of the six languages."""
    assert TREES.is_dir(), f"no skeleton trees at {TREES}"
    assert _copied_files(), f"no copied files found under {TREES}"


def test_the_substituted_token_is_actually_used_by_a_tree():
    """The other half of the guard: if no tree carried the token, the rules below would be
    checking that nothing contains anything, and a migration that renamed the token everywhere
    except in the launcher would pass."""
    carriers = [
        p
        for p in _copied_files()
        if SUBSTITUTED_TOKEN in p.read_text(encoding="utf-8", errors="replace")
        or SUBSTITUTED_TOKEN in str(p)
    ]
    assert carriers, (
        f"no tree file carries {SUBSTITUTED_TOKEN} in its content or its path — either the token "
        "changed and this file was not updated with it, or the trees stopped naming the product "
        "at all"
    )


@pytest.mark.parametrize("path", _copied_files(), ids=_id)
def test_a_copied_file_carries_no_placeholder_token_the_launcher_will_not_substitute(path: Path):
    hits = _tokens_in(path.read_text(encoding="utf-8", errors="replace"))

    assert not hits, (
        f"{_id(path)} carries {sorted(set(hits))}, which the skeleton launcher does not "
        f"substitute — it would be copied into a product verbatim. The one token a tree may "
        f"carry is {SUBSTITUTED_TOKEN}."
    )


@pytest.mark.parametrize("path", _copied_files(), ids=_id)
def test_a_copied_files_path_carries_no_placeholder_token_the_launcher_will_not_substitute(path: Path):
    """Paths as well as contents: the launcher substitutes in both, so a directory named
    `crates/{{scope}}/` lands as a directory of that name just as surely as a line of text does."""
    rel = str(path.relative_to(TREES.parent))
    hits = _tokens_in(rel)

    assert not hits, (
        f"the path {rel} carries {sorted(set(hits))}, which the skeleton launcher does not "
        f"substitute — the directory would land in the product named exactly that."
    )
