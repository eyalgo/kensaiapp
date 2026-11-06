#!/usr/bin/env bash
# Version: 1.0.0 — first fixture builder for the changelog-line evals
# Build one synthetic fixture for the changelog-line evals: a fabricated instance repository holding a
# fabricated product ("widget"), a project card, a change folder and a change worktree on the change's
# branch with real commits. Nothing here is a real product, and nothing reads the owner's home.
#
#   build_fixture.sh <empty-destination-dir> <scenario>
#
# Prints the instance root, the project name and the change key, one per line, on success.
# Scenarios: entry upgrading tests-only tests-only-removal no-changelog unreleased-none unreleased-two
#   removals last-removal already-empty no-what-left malformed-none malformed-both external
#   hook-refuses external-report-refused wrong-branch no-worktree dirty-target
set -euo pipefail

die() { echo "build_fixture: $*" >&2; exit 1; }

# A session may force a hook folder through GIT_CONFIG_* variables; the fixture is a repository of its own.
export GIT_CONFIG_COUNT=0
unset GIT_CONFIG_PARAMETERS

dest="${1:?destination dir}"
scenario="${2:?scenario}"
project=demo
day=2026-01-01   # the key is built from parts so this script names no change unit
key="${day}_demo-change"
product=products/widget

mkdir -p "$dest"
dest="$(cd "$dest" && pwd)"
[ -z "$(ls -A "$dest")" ] || die "destination $dest is not empty"

git_in() { local dir="$1"; shift; git -C "$dir" -c user.name=Fixture -c user.email=fixture@example.invalid "$@"; }
commit() { local dir="$1"; shift; git_in "$dir" add -A; git_in "$dir" commit --quiet -m "$*"; }

changelog_text() {
  cat <<'TXT'
# Changelog — `products/widget`

Each entry records a change to what a user of a fresh clone installs, runs, types or reads in the widget. It names the project the change was made under and cites the commits that made it. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.0.0] - 2025-12-01

### Added

- **demo** — The `widget` command prints a greeting. (`aaaaaaaaa`)
TXT
}

what_left_text() {
  cat <<'TXT'
# What is left to build

The widget wants these things and its code does not do them yet.

- **Wanted:** The operator can run `widget --json` and read the greeting as JSON.
  **Source:** `PRD § Core Features, **Output**`
  **Missing at:** `1111111`

- **Wanted:** The operator can set the greeting with `$WIDGET_NAME` and a `--name` flag.
  **Source:** `PRD § Core Features, **Greeting**`
  **Missing at:** `1111111`

- **Wanted:** The operator can list past greetings with `widget history`.
  **Source:** `PRD § Core Features, **History**`
  **Missing at:** `1111111`
TXT
}

repo="$dest/instance"
mkdir -p "$repo"
git_in "$repo" init --quiet -b main
# The machine's global hook path would hold the fixture to this instance's commit format. The fixture
# keeps its own hook folder, so a scenario can install a hook of its own.
mkdir -p "$repo/.git/hooks"
git_in "$repo" config core.hooksPath "$repo/.git/hooks"
mkdir -p "$repo/$product/docs" "$repo/system/projects/$project"
printf 'print("hello")\n' > "$repo/$product/widget.py"
printf '# widget\n' > "$repo/$product/README.md"

card_path="$product"
if [ "$scenario" = external ] || [ "$scenario" = external-report-refused ]; then
  ext="$dest/product-repo"
  mkdir -p "$ext/docs"
  git_in "$ext" init --quiet -b main
  mkdir -p "$ext/.git/hooks"
  git_in "$ext" config core.hooksPath "$ext/.git/hooks"
  printf 'print("hello")\n' > "$ext/widget.py"
  changelog_text > "$ext/CHANGELOG.md"
  what_left_text > "$ext/docs/what_left.md"
  commit "$ext" "widget: start"
  card_path="$ext"
fi
cat > "$repo/system/projects/$project/project.md" <<TXT
# Project Context — $project

**Product path:** $card_path
**Type:** software
**Definition:** none
**Execution type:** headless
**Package slug:** $project
**Test command:** none
TXT

if [ "$scenario" != external ] && [ "$scenario" != external-report-refused ]; then
  case "$scenario" in
    no-changelog) ;;
    unreleased-none) changelog_text | grep -v '^## \[Unreleased\]$' > "$repo/$product/CHANGELOG.md" ;;
    unreleased-two) { changelog_text; printf '\n## [Unreleased]\n'; } > "$repo/$product/CHANGELOG.md" ;;
    *) changelog_text > "$repo/$product/CHANGELOG.md" ;;
  esac
  case "$scenario" in
    no-what-left) ;;
    already-empty) printf '# What is left to build\n\nThe widget wants these things and its code does not do them yet.\n\nNothing is left to build.\n' > "$repo/$product/docs/what_left.md" ;;
    malformed-none) printf '# What is left to build\n\nThe widget wants these things and its code does not do them yet.\n' > "$repo/$product/docs/what_left.md" ;;
    malformed-both) { what_left_text; printf '\nNothing is left to build.\n'; } > "$repo/$product/docs/what_left.md" ;;
    *) what_left_text > "$repo/$product/docs/what_left.md" ;;
  esac
fi

change="$repo/system/projects/$project/journey/tobiishi/$key"
mkdir -p "$change"
printf '# Change request\n\nSee the spec.\n' > "$change/change_request.md"
printf '# Change spec — %s\n\nThe change below.\n' "$key" > "$change/change_spec.md"
printf '# Change design — %s\n\n**Publishes text:** no\n' "$key" > "$change/change_design.md"
printf '# Tech Lead instruction\n\nOne task.\n' > "$change/tl_instruction.md"
commit "$repo" "fixture: base"

if [ "$scenario" = no-worktree ]; then
  printf '%s\n%s\n%s\n' "$repo" "$project" "$key"
  exit 0
fi

# The change worktree, on the change's branch.
git_in "$repo" worktree add --quiet -b "$key" "$repo/.worktrees/$key" main
wt="$repo/.worktrees/$key"
pw="$wt/$product"
if [ "$card_path" != "$product" ]; then
  git_in "$card_path" worktree add --quiet -b "$key" "$card_path/.worktrees/$key" main
  pw="$card_path/.worktrees/$key"
fi

case "$scenario" in
  entry|no-changelog|unreleased-none|unreleased-two|already-empty|no-what-left|malformed-none|malformed-both|external|external-report-refused|hook-refuses|wrong-branch|dirty-target)
    printf 'import argparse\nprint("hello")  # --json supported\n' > "$pw/widget.py"
    printf '{"greeting": "hello"}\n' > "$pw/sample.json"
    commit "$pw" "widget: add the --json flag"
    ;;
  upgrading)
    printf 'import os\nprint(os.environ["WIDGET_GREETING"])\n' > "$pw/widget.py"
    printf 'The greeting now comes from $WIDGET_GREETING; export it before running widget.\n' > "$pw/UPGRADE_NOTE.txt"
    commit "$pw" "widget: read the greeting from WIDGET_GREETING"
    ;;
  tests-only)
    mkdir -p "$pw/tests"; printf 'def test_greeting():\n    assert True\n' > "$pw/tests/test_widget.py"
    commit "$pw" "widget: test the greeting"
    ;;
  tests-only-removal)
    mkdir -p "$pw/tests"; printf 'def test_history():\n    assert True\n' > "$pw/tests/test_history.py"
    printf 'history = []\n' > "$pw/history.py"
    commit "$pw" "widget: record greeting history"
    printf 'def show():\n    return history\n' >> "$pw/history.py"
    printf 'import history\nif __name__ == "__main__":\n    print(history.show())\n' > "$pw/widget_history.py"
    commit "$pw" "widget: add widget history command"
    ;;
  removals|last-removal)
    printf 'print("hello")  # --json supported\n' > "$pw/widget.py"
    commit "$pw" "widget: add the --json flag"
    printf 'import os\nNAME = os.environ.get("WIDGET_NAME")\n' >> "$pw/widget.py"
    commit "$pw" "widget: read WIDGET_NAME (the --name flag is not built)"
    printf 'history = []\nprint("widget history")\n' > "$pw/history.py"
    commit "$pw" "widget: add widget history"
    if [ "$scenario" = last-removal ]; then
      printf 'name flag\n' > "$pw/name_flag.txt"; commit "$pw" "widget: add the --name flag"
    fi
    ;;
esac

# Scenario adjustments that make a check meaningful.
case "$scenario" in
  hook-refuses)
    printf '#!/bin/sh\necho "fixture hook refuses every commit" >&2\nexit 1\n' > "$repo/.git/hooks/pre-commit"
    chmod +x "$repo/.git/hooks/pre-commit"
    ;;
  external-report-refused)
    mkdir -p "$repo/.git/hooks"
    printf '#!/bin/sh\necho "fixture hook refuses the report" >&2\nexit 1\n' > "$repo/.git/hooks/pre-commit"
    chmod +x "$repo/.git/hooks/pre-commit"
    ;;
  wrong-branch)
    git_in "$pw" switch --quiet -c elsewhere
    ;;
  dirty-target)
    printf '\nUncommitted note.\n' >> "$pw/CHANGELOG.md"
    ;;
esac

printf '%s\n%s\n%s\n' "$repo" "$project" "$key"
