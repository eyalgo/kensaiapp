"""The external-only Claude Code directory grant.

Intent source: project-stamp SKILL.md "External products: the directory grant
is set automatically" — for an **external** product the script merges the product
path into `permissions.additionalDirectories` in `.claude/settings.local.json`
(never clobbering the allow list / other keys, creating the file/key if absent,
no-op if already present). An **internal** product needs no grant.
"""

import json
from pathlib import Path

_EXEC = ("--execution-type", "headless", "--test-command", "pytest tests/")


def _settings_local(root):
    return Path(root) / ".claude" / "settings.local.json"


def _external_product(tmp_path):
    product = tmp_path / "external-product"
    product.mkdir()
    return product


def test_external_grant_added_to_additional_directories(run, tmp_path):
    product = _external_product(tmp_path)
    result = run("demo", "--placement", "external",
                 "--product-path", str(product), *_EXEC)
    assert result.returncode == 0, result.stderr
    data = json.loads(_settings_local(run.root).read_text(encoding="utf-8"))
    assert str(product) in data["permissions"]["additionalDirectories"]


def test_external_grant_merges_without_clobbering(run, tmp_path):
    settings = _settings_local(run.root)
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(
        json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}, "other": 1}),
        encoding="utf-8",
    )
    product = _external_product(tmp_path)

    result = run("demo", "--placement", "external",
                 "--product-path", str(product), *_EXEC)

    assert result.returncode == 0, result.stderr
    data = json.loads(settings.read_text(encoding="utf-8"))
    assert data["permissions"]["allow"] == ["Bash(ls:*)"]  # untouched
    assert data["other"] == 1  # untouched
    assert str(product) in data["permissions"]["additionalDirectories"]


def test_internal_adds_no_grant(run):
    result = run("demo", "--placement", "internal", *_EXEC)
    assert result.returncode == 0, result.stderr
    # an internal (relative) product needs no directory grant
    assert not _settings_local(run.root).exists()


def test_external_warns_when_product_not_a_git_repo(run, tmp_path):
    # a plain dir, not a git repo — the two-repo flow needs one
    product = _external_product(tmp_path)
    result = run("demo", "--placement", "external",
                 "--product-path", str(product), *_EXEC)
    assert result.returncode == 0, result.stderr  # non-fatal: pointer still scaffolds
    assert "not a git repo" in result.stdout
    assert "git init" in result.stdout


def test_external_ok_when_product_is_a_git_repo(run, tmp_path):
    product = _external_product(tmp_path)
    (product / ".git").mkdir()  # looks like a git repo
    result = run("demo", "--placement", "external",
                 "--product-path", str(product), *_EXEC)
    assert result.returncode == 0, result.stderr
    assert "product repo OK" in result.stdout
    assert "not a git repo" not in result.stdout
