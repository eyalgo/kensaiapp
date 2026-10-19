"""Contract tests for `coldread/manifest.py` — parse + validate the stack manifest.

`stack.json` is the ordered substance set (data), beside a skill's SKILL.md. This module turns it
into a validated `Stack`, or a typed `ManifestError` the entry converts to a die() before any link
launches. Validation is the launcher's containment rule applied EARLY: every path relative, and
resolving to a file under the instance root — so a renamed prompt breaks the chain loudly at entry,
not silently at link 2 four hours in.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # core/tools on path

from coldread.manifest import ManifestError, Stack, load_stack


def _make_root(tmp_path, *, skill="product-prd", manifest=None, substance_files=("a.md", "b.md")):
    """Build a fake instance root with a skill dir + real substance files, and write stack.json."""
    root = tmp_path / "inst"
    skill_dir = root / ".claude" / "skills" / skill
    skill_dir.mkdir(parents=True)
    for rel in substance_files:
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("content\n")
    if manifest is not None:
        (skill_dir / "stack.json").write_text(json.dumps(manifest))
    return str(root), str(skill_dir)


# --- the happy path ----------------------------------------------------------


def test_valid_manifest_loads_ordered_substance(tmp_path):
    root, skill_dir = _make_root(
        tmp_path,
        manifest={"version": 1, "substance": ["a.md", "b.md"]},
    )
    stack = load_stack(skill_dir, root=root)
    assert isinstance(stack, Stack)
    assert stack.substance == ("a.md", "b.md")


def test_order_is_preserved_as_declared(tmp_path):
    root, skill_dir = _make_root(
        tmp_path,
        manifest={"version": 1, "substance": ["b.md", "a.md"]},
    )
    stack = load_stack(skill_dir, root=root)
    assert stack.substance == ("b.md", "a.md")   # position IS run order


def test_a_single_entry_stack_is_valid(tmp_path):
    root, skill_dir = _make_root(
        tmp_path,
        manifest={"version": 1, "substance": ["a.md"]},
        substance_files=("a.md",),
    )
    assert load_stack(skill_dir, root=root).substance == ("a.md",)


def test_root_is_derived_from_skill_dir_when_not_passed(tmp_path):
    """skill_dir is <root>/.claude/skills/<skill>; root is derivable, so the chain need not pass it."""
    root, skill_dir = _make_root(
        tmp_path,
        manifest={"version": 1, "substance": ["a.md", "b.md"]},
    )
    stack = load_stack(skill_dir)   # no explicit root
    assert stack.substance == ("a.md", "b.md")


# --- root derivation, grouped layout -----------------------------------------
# `_derive_root` must delegate to `skill_path.instance_root`, so a skill living only under the
# grouped layout (`skills/<group>/.claude/skills/<name>`) still derives correctly when `root` is
# omitted. This is the only way to reach `_derive_root` at all — both real callers of `load_stack`
# (`chain.py` and the cold-read launcher) always pass `root=` explicitly.


def _make_grouped_root(tmp_path, *, group="g", skill="thing", manifest=None,
                        substance_files=("a.md", "b.md")):
    """Build a fake instance root whose skill lives ONLY under the grouped layout — no flat
    `.claude/skills/<skill>` at all — with real substance files at the (top) instance root."""
    root = tmp_path / "inst"
    skill_dir = root / "skills" / group / ".claude" / "skills" / skill
    skill_dir.mkdir(parents=True)
    for rel in substance_files:
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("content\n")
    if manifest is not None:
        (skill_dir / "stack.json").write_text(json.dumps(manifest))
    return str(root), str(skill_dir)


def test_root_is_derived_from_a_grouped_skill_dir_when_not_passed(tmp_path):
    root, skill_dir = _make_grouped_root(
        tmp_path,
        manifest={"version": 1, "substance": ["a.md", "b.md"]},
    )
    assert not (Path(root) / ".claude" / "skills").exists()

    stack = load_stack(skill_dir)   # no explicit root — must derive through skill_path

    assert stack.substance == ("a.md", "b.md")


def test_explicit_root_wins_over_derivation_for_a_flat_skill(tmp_path):
    root, skill_dir = _make_root(
        tmp_path,
        manifest={"version": 1, "substance": ["a.md", "b.md"]},
    )
    stack = load_stack(skill_dir, root=root)
    assert stack.substance == ("a.md", "b.md")


def test_explicit_root_wins_over_derivation_for_a_grouped_skill(tmp_path):
    root, skill_dir = _make_grouped_root(
        tmp_path,
        manifest={"version": 1, "substance": ["a.md", "b.md"]},
    )
    stack = load_stack(skill_dir, root=root)
    assert stack.substance == ("a.md", "b.md")


def test_derive_root_still_returns_a_str(tmp_path):
    from coldread import manifest as manifest_module

    root, skill_dir = _make_root(tmp_path, manifest=None)
    result = manifest_module._derive_root(skill_dir)

    assert isinstance(result, str)
    assert result == root


def test_a_grouped_skills_missing_substance_file_still_raises_at_entry(tmp_path):
    root, skill_dir = _make_grouped_root(
        tmp_path,
        manifest={"version": 1, "substance": ["a.md", "gone.md"]},
        substance_files=("a.md",),   # gone.md never created
    )
    with pytest.raises(ManifestError):
        load_stack(skill_dir)   # no explicit root — derivation must still land the refusal


def test_a_grouped_skills_escaping_substance_path_still_raises_at_entry(tmp_path):
    # The containment refusal must fire from a grouped skill directory too, off the derived root.
    root, skill_dir = _make_grouped_root(
        tmp_path,
        manifest={"version": 1, "substance": ["../outside.md"]},
    )
    (Path(root).parent / "outside.md").write_text("outside\n")

    with pytest.raises(ManifestError):
        load_stack(skill_dir)   # no explicit root — derivation must still land the refusal


def test_derive_root_docstring_does_not_restate_the_launchers_fact():
    # The station: rewording `_derive_root`'s justification "must not replace one copy of the
    # launcher's fact with another" (single_source.md § The rule). A fresh sentence about what
    # the launcher passes is the same defect as the sentence about what it hardcodes.
    from coldread import manifest as manifest_module

    doc = manifest_module._derive_root.__doc__ or ""

    assert "launcher" not in doc.lower()


def test_no_docstring_in_manifest_states_what_the_launcher_hardcodes():
    import inspect
    from coldread import manifest as manifest_module

    source = inspect.getsource(manifest_module)
    assert "hardcodes" not in source


# --- typed refusals ----------------------------------------------------------


def test_missing_manifest_raises(tmp_path):
    root, skill_dir = _make_root(tmp_path, manifest=None)   # no stack.json written
    with pytest.raises(ManifestError):
        load_stack(skill_dir, root=root)


def test_bad_json_raises(tmp_path):
    root, skill_dir = _make_root(tmp_path, manifest={"version": 1, "substance": ["a.md"]})
    (Path(skill_dir) / "stack.json").write_text("{not json")
    with pytest.raises(ManifestError):
        load_stack(skill_dir, root=root)


def test_missing_version_raises(tmp_path):
    root, skill_dir = _make_root(tmp_path, manifest={"substance": ["a.md"]})
    with pytest.raises(ManifestError):
        load_stack(skill_dir, root=root)


def test_unknown_version_raises(tmp_path):
    root, skill_dir = _make_root(tmp_path, manifest={"version": 2, "substance": ["a.md"]})
    with pytest.raises(ManifestError):
        load_stack(skill_dir, root=root)


def test_missing_substance_raises(tmp_path):
    root, skill_dir = _make_root(tmp_path, manifest={"version": 1})
    with pytest.raises(ManifestError):
        load_stack(skill_dir, root=root)


def test_empty_substance_raises(tmp_path):
    root, skill_dir = _make_root(tmp_path, manifest={"version": 1, "substance": []})
    with pytest.raises(ManifestError):
        load_stack(skill_dir, root=root)


def test_substance_not_a_list_raises(tmp_path):
    root, skill_dir = _make_root(tmp_path, manifest={"version": 1, "substance": "a.md"})
    with pytest.raises(ManifestError):
        load_stack(skill_dir, root=root)


def test_a_non_string_entry_raises(tmp_path):
    root, skill_dir = _make_root(tmp_path, manifest={"version": 1, "substance": ["a.md", 7]})
    with pytest.raises(ManifestError):
        load_stack(skill_dir, root=root)


def test_an_empty_string_entry_raises(tmp_path):
    root, skill_dir = _make_root(tmp_path, manifest={"version": 1, "substance": ["a.md", ""]})
    with pytest.raises(ManifestError):
        load_stack(skill_dir, root=root)


def test_an_absolute_path_raises(tmp_path):
    root, skill_dir = _make_root(tmp_path, manifest={"version": 1, "substance": ["/etc/passwd"]})
    with pytest.raises(ManifestError):
        load_stack(skill_dir, root=root)


def test_a_nonexistent_path_raises_at_entry_not_at_link_2(tmp_path):
    """A renamed/removed substance file breaks the chain loudly at entry — the whole point."""
    root, skill_dir = _make_root(
        tmp_path,
        manifest={"version": 1, "substance": ["a.md", "gone.md"]},
        substance_files=("a.md",),   # gone.md never created
    )
    with pytest.raises(ManifestError):
        load_stack(skill_dir, root=root)


def test_a_path_escaping_the_root_raises(tmp_path):
    """Containment, like --file: a ../ path that resolves outside root is refused even if it exists."""
    root, skill_dir = _make_root(tmp_path, manifest={"version": 1, "substance": ["a.md"]})
    outside = tmp_path / "outside.md"
    outside.write_text("x\n")
    (Path(skill_dir) / "stack.json").write_text(
        json.dumps({"version": 1, "substance": ["../outside.md"]})
    )
    with pytest.raises(ManifestError):
        load_stack(skill_dir, root=root)
