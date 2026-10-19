"""The placement guards (exit 2) and the never-overwrite guard (exit 3).

Intent source: project-stamp SKILL.md "Run it" — `--placement` is required;
internal defaults the path, external requires an absolute path; the script guards
internal-with-absolute / external-with-relative / external-without-path with a
clear message (exit 2); and it is create-if-missing, never overwrite (exit 3).
"""

from pathlib import Path

_EXEC = ("--execution-type", "headless", "--test-command", "pytest tests/")


def test_missing_placement_is_rejected(run):
    result = run("demo", *_EXEC)
    assert result.returncode != 0  # --placement is required


def test_external_without_path_exits_2(run):
    result = run("demo", "--placement", "external", *_EXEC)
    assert result.returncode == 2, result.stderr


def test_external_with_relative_path_exits_2(run):
    result = run("demo", "--placement", "external",
                 "--product-path", "some/rel/path", *_EXEC)
    assert result.returncode == 2, result.stderr


def test_internal_with_absolute_path_exits_2(run):
    result = run("demo", "--placement", "internal",
                 "--product-path", "/abs/product", *_EXEC)
    assert result.returncode == 2, result.stderr


def test_overwrite_guard_exits_3_and_changes_nothing(run):
    proj = Path(run.root) / "system" / "projects" / "demo"
    proj.mkdir(parents=True)
    sentinel = proj / "SENTINEL.txt"
    sentinel.write_text("do not touch", encoding="utf-8")

    result = run("demo", "--placement", "internal", *_EXEC)

    assert result.returncode == 3, result.stderr
    assert sentinel.read_text(encoding="utf-8") == "do not touch"
    # nothing else was created inside the existing project folder
    assert list(proj.iterdir()) == [sentinel]
