#!/usr/bin/env bash
#
# doctor.sh — reports whether this machine has the six tools kensaiapp runs on, each at its
# minimum version: uv, git, podman, tart, gh and claude (Claude Code's command).
#
# Version: 1.0.1 — tests read nothing of the machine; the launcher suites run again; a violation is fixed where it is seen
# Version: 1.0.0 — the report, --help, and the source-safe version comparison
#
# USAGE
#   /bin/bash <CORE>/tools/doctor.sh            one line per tool on stdout; exit 0 when all six
#                                               are present, 1 when any is missing or too old
#   /bin/bash <CORE>/tools/doctor.sh --help     the minimum versions; runs no version query
#   Any other argument prints a usage message to stderr and exits 2.
#   Reports only: installs, upgrades and edits nothing, and never runs brew.
#
# WHY THIS EXISTS
#   Nothing said which tools kensaiapp needs on the machine, and nothing checked them. This file
#   holds the one ordered inventory — label, minimum version, and the evidence for that
#   minimum — and both the report and --help read it.
#
#   Bash builtins only, started as `/bin/bash <path>`: the doctor has to run on a machine that
#   lacks uv, and therefore lacks the Python uv provides. Naming the interpreter on the command
#   line means the PATH under test is never asked to find bash for us. The shebang stays
#   `#!/usr/bin/env bash` for the house convention; the restricted-PATH proof does not depend on it.
#
#   `set -euo pipefail` sits under the run-directly guard at the bottom, not at the top: this file
#   is also sourced, so a test can call _version_at_least, and a sourced `set -e` would change the
#   options of whatever sourced it (detach_watcher.sh is the other sourced file and sets none).
#
#   The first executable on the PATH the doctor was started with is the only copy queried, found
#   by walking PATH ourselves rather than with `command -v`, because a shell function, alias or
#   hash-cache entry is not an executable file. Versions are compared group by group as digit
#   strings (length, then text) because a numeric `[ -gt ]` overflows on a long group and reads a
#   leading zero as octal.

# --- the inventory: label, minimum version, and why that is the minimum --------------------------
# A minimum is the oldest release that has what kensaiapp relies on. It is not the version this
# Mac happens to have, and not raised to turn a present tool into a failure.
DOCTOR_INVENTORY=(
  # uv: core/tools/locked_python.sh:104,106,128 run `uv run --quiet --no-sync --project <root>`.
  # `uv run --no-sync` first shipped in uv 0.4.9 and `--project` in 0.4.16
  # (https://github.com/astral-sh/uv/blob/main/changelogs/0.4.x.md), so 0.4.16 is the oldest uv
  # that accepts that command line. uv.lock's revision is no reason for a higher number: uv's own
  # source says an older uv still reads a newer revision
  # (crates/uv-resolver/src/lock/mod.rs, 0.8.3).
  "uv 0.4.16"
  # git: core/launchers/skill/launcher.sh:795 and core/tools/gate_suite.py:2603 call
  # `git rev-parse --path-format=absolute`, and core/tools/chain_development.py:2467 reads
  # `%(trailers:key=Shukuba,keyonly,only)`. Neither `--path-format`
  # (Documentation/git-rev-parse.txt)
  # nor the `keyonly` trailer option (Documentation/pretty-formats.txt) is documented at git
  # v2.30.0; both are at v2.31.0 (https://github.com/git/git).
  "git 2.31.0"
  # podman: core/tools/gate_suite.py:1525 asks `podman machine inspect --format {{.State}}`.
  # `podman machine inspect` was added in 4.1.0
  # (https://github.com/containers/podman/blob/main/RELEASE_NOTES.md,
  # "A new machine command has been added, `podman machine inspect`"), and v4.1.0's own
  # docs/source/markdown/podman-machine-inspect.1.md documents `--format`.
  "podman 4.1.0"
  # tart: core/tools/gate_suite.py:1367,1549,1733 run commands in the guest with `tart exec`, and
  # :1733 uses its `-i` flag. `tart exec` was introduced in 2.27.0, 2025-05-22
  # (https://github.com/cirruslabs/tart/releases/tag/2.27.0), and `-i` is in that tag's
  # Sources/tart/Commands/Exec.swift.
  "tart 2.27.0"
  # gh: the one use of gh in this repository is `gh api repos/<owner>/<repo>`, in an archived
  # proposal's research under docs/proposals/archive/. `gh api` first appears
  # in gh v0.10.0, 2020-06-11 (https://github.com/cli/cli/releases/tag/v0.10.0, "## gh api").
  "gh 0.10.0"
  # claude: core/tools/agent_session.py:308 runs `claude agents --json --all`, and
  # core/tools/watch_agent.py:328,427 read each row's `id` and `state`. Claude Code 2.1.169 added
  # `--all` "plus new `id` and `state` fields" to `claude agents --json`
  # (https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md, 2.1.169).
  "claude 2.1.169"
)

DOCTOR_USAGE='doctor: usage: <CORE>/tools/doctor.sh [--help]'
DOCTOR_DOTTED_NUMBER='[0-9]+(\.[0-9]+)+'

# --- version comparison -------------------------------------------------------------------------

# _version_at_least <version> <floor>: 0 when version >= floor, 1 when lower. Groups are compared
# left to right as numbers; a missing group counts as 0, and leading zeros do not matter.
_version_at_least() {
  local rest_version="$1" rest_floor="$2" version_group floor_group
  while [ -n "$rest_version" ] || [ -n "$rest_floor" ]; do
    version_group="${rest_version%%.*}"
    floor_group="${rest_floor%%.*}"
    case "$rest_version" in *.*) rest_version="${rest_version#*.}" ;; *) rest_version="" ;; esac
    case "$rest_floor" in *.*) rest_floor="${rest_floor#*.}" ;; *) rest_floor="" ;; esac
    version_group="${version_group#"${version_group%%[!0]*}"}"
    floor_group="${floor_group#"${floor_group%%[!0]*}"}"
    version_group="${version_group:-0}"
    floor_group="${floor_group:-0}"
    if [ "${#version_group}" -ne "${#floor_group}" ]; then
      [ "${#version_group}" -gt "${#floor_group}" ] && return 0
      return 1
    fi
    if [ "$version_group" != "$floor_group" ]; then
      [ "$version_group" \> "$floor_group" ] && return 0
      return 1
    fi
  done
  return 0
}

# --- discovery and the version query -------------------------------------------------------------

# _find_executable <label>: sets found_path to the first executable regular file named <label>
# in PATH order. An empty PATH component means the current directory, as in a shell.
_find_executable() {
  local label="$1" remaining="${PATH-}:" directory
  while [ -n "$remaining" ]; do
    directory="${remaining%%:*}"
    remaining="${remaining#*:}"
    [ -n "$directory" ] || directory="."
    if [ -f "$directory/$label" ] && [ -x "$directory/$label" ]; then
      found_path="$directory/$label"
      return 0
    fi
  done
  return 1
}

# _read_version <executable>: sets version to the first dotted number on the first stdout line of
# `<executable> --version`. Fails when the query fails or that line holds no dotted number.
# stderr is discarded: it is never part of the answer and never part of the report.
_read_version() {
  local executable="$1" output status=0 first_line
  output="$("$executable" --version 2>/dev/null </dev/null)" || status=$?
  [ "$status" -eq 0 ] || return 1
  first_line="${output%%$'\n'*}"
  [[ "$first_line" =~ $DOCTOR_DOTTED_NUMBER ]] || return 1
  version="${BASH_REMATCH[0]}"
}

# --- the report and --help ---------------------------------------------------------------------

# _report: one line per tool, in inventory order, whatever an earlier tool returned.
# found_path and version are set by the two helpers above, in this function's scope.
_report() {
  local entry label floor found_path version gaps=0
  for entry in "${DOCTOR_INVENTORY[@]}"; do
    label="${entry%% *}"
    floor="${entry#* }"
    if ! _find_executable "$label"; then
      echo "$label: missing"
      gaps=1
    elif ! _read_version "$found_path"; then
      echo "$label: too old (version unreadable, needs $floor or later)"
      gaps=1
    elif _version_at_least "$version" "$floor"; then
      echo "$label: present ($version)"
    else
      echo "$label: too old ($version, needs $floor or later)"
      gaps=1
    fi
  done
  return "$gaps"
}

_help() {
  local entry
  echo 'usage: <CORE>/tools/doctor.sh [--help]'
  echo
  echo 'Checks whether this machine has the six tools kensaiapp runs on, each at its minimum version.'
  echo 'Prints one line per tool: present, missing or too old.'
  echo 'Each tool is named by its command, and claude is Claude Code.'
  echo 'A tool is checked where your PATH finds it first, so a tool outside your PATH is reported missing.'
  echo 'Nothing is installed, upgraded or changed.'
  echo 'Exits 0 when all six are present, 1 when any is missing or too old, and 2 for any argument other than --help.'
  echo
  echo 'Minimum versions:'
  for entry in "${DOCTOR_INVENTORY[@]}"; do
    echo "${entry%% *}: ${entry#* }"
  done
}

# Argument dispatch comes before any query: only no arguments, or exactly --help, is accepted.
doctor_main() {
  if [ "$#" -eq 0 ]; then
    _report
    return
  fi
  if [ "$#" -eq 1 ] && [ "$1" = "--help" ]; then
    _help
    return 0
  fi
  echo "$DOCTOR_USAGE" >&2
  return 2
}

# Run only when executed, never when sourced (see WHY THIS EXISTS).
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  set -euo pipefail
  doctor_main "$@"
  exit $?
fi
