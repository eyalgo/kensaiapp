#!/usr/bin/env bash
#
# locked_python.sh — the runner kensaiapp's hooks, skills' commands and launches go through: runs a
# Python script on the Python that `.python-version` names at the root of the instance holding this
# file.
#
# Version: 1.4.0 — tests read nothing of the machine; the launcher suites run again; a violation is fixed where it is seen
# Version: 1.3.0 — the runner names hooks, skills' commands and launches as what stops without uv
# Version: 1.2.0 — prepare new pins with the host interpreter before launch
# Version: 1.1.0 — launchers run on the locked Python
# Version: 1.0.0
#
# USAGE
#   locked_python.sh <script> [args...]
#   locked_python.sh -c <code> [args...]      (inline code, as python3 -c takes it)
#   locked_python.sh - [args...] <<'PY'       (a script on stdin, as python3 - takes it)
#   stdin, stdout, stderr and the exit status are the script's.
#
#   locked_python.sh --check <launcher>
#   Runs no Python. With uv on PATH it prints nothing and exits 0; without it, it prints the
#   launch's own missing-uv message, naming the launcher, and exits 1. A launch makes this check
#   once, at its entry (`pin_enter` in pin_run.sh), before it makes a pin or starts any Python.
#
#   locked_python.sh --prepare-pin <pin-root>
#   Prepares the copied pin's separate .venv using this source host's interpreter, without
#   installing packages or downloading Python. A missing host environment uses the ordinary
#   host bootstrap first. Success is silent and leaves stdin available for the launch.
#
# WHY THIS EXISTS
#   A hook that ran on whichever `python3` the shell found first ran on a different Python on every
#   machine (3.15 through a pyenv shim here, against the 3.14 the instance pins). The settings hooks
#   and both git hook shims now name this one file, and so do skills' commands, the launchers and the
#   Python the launchers start, so the missing-uv check and the uv flags have a single home.
#
#   --no-sync, and no --locked: with --no-sync, --locked is inert (a pyproject.toml that no longer
#   matched its uv.lock still ran), so naming it would state a check this file does not make. The
#   hooks use only the standard library, so nothing needs installing; a first run may create an
#   empty .venv. --no-project is not used either: from a directory with no pyproject.toml it ran
#   the newest Python uv found, not the pinned one.
#   --project names the instance root found from this file's own location, never the working
#   directory: a git hook runs in whichever repository is committing, and that repository may hold
#   no pyproject.toml at all. --quiet keeps uv's own "Creating virtual environment" lines off
#   stderr on a first run, so a hook's output is the script's alone.
#
#   Without uv it runs no Python at all and never falls back to python3. Exit 1, because for a
#   Claude Code hook that is a non-blocking error (a session stays usable) and for a git hook any
#   non-zero refuses the commit.
#
#   THE SCRIPT'S ENVIRONMENT IS THE CALLER'S. `uv run` prepends <root>/.venv/bin to PATH and sets
#   VIRTUAL_ENV, UV and UV_RUN_RECURSION_DEPTH for the command it runs (measured 2026-10-26), so a
#   process the script started, a launched agent included, would find kensaiapp's own Python and
#   pytest first. The runner hands the caller's value of each of those four through uv under
#   KENSAIAPP_CALLER_<name> (left unset when the caller had none), and the command uv runs puts
#   them back before the interpreter starts. That command is `sh`, which finds the root's .venv
#   interpreter by the absolute path uv gave it in VIRTUAL_ENV, since the restored PATH no longer
#   leads there. The interpreter keeps its prefix without the variables: it finds it from its own
#   location.
set -euo pipefail

# The instance root is two directories above this file's own real directory.
runner_dir="$(cd -P "$(dirname "$0")" && pwd)"
root="$(cd "$runner_dir/../.." && pwd)"

# The variables `uv run` rewrites or adds for the command it runs.
uv_rewritten="PATH VIRTUAL_ENV UV UV_RUN_RECURSION_DEPTH"

# --- --check <launcher>: the launch's one look for uv, running no Python ---
if [ "${1:-}" = "--check" ]; then
  [ $# -eq 2 ] || { echo "locked_python.sh: --check takes the launcher's name and nothing else" >&2; exit 1; }
  if ! command -v uv >/dev/null 2>&1; then
    cat >&2 <<EOF
$2: uv was not found on PATH, so nothing was launched.
kensaiapp's launchers run their Python through uv, on the Python that the instance's .python-version names, and never fall back to python3.
Until uv is found, no kensaiapp launcher runs.
Install uv with one of:
  brew install uv
  curl -LsSf https://astral.sh/uv/install.sh | sh
If uv is already installed, add the directory that holds it to PATH.
Guide: https://docs.astral.sh/uv/getting-started/installation/
EOF
    exit 1
  fi
  exit 0
fi

if ! command -v uv >/dev/null 2>&1; then
  # `-c` and `-` are the two interpreter markers, not paths: basename would read `-c` as an option.
  case "${1:-}" in
    -c | -) script_name="$1" ;;
    *) script_name="$(basename "${1:-}")" ;;
  esac
  cat >&2 <<EOF
kensaiapp: uv was not found on PATH, so $script_name did not run.
kensaiapp's hooks, skills' commands and launches run on the Python the instance pins, through uv, and never fall back to python3.
Until uv is found, none of them runs, and a commit the git hooks check is refused.
Install uv with one of:
  brew install uv
  curl -LsSf https://astral.sh/uv/install.sh | sh
If uv is already installed, add the directory that holds it to PATH.
Guide: https://docs.astral.sh/uv/getting-started/installation/
EOF
  exit 1
fi

# Explicit interpreter paths avoid discovery on PATH; UV_PROJECT_ENVIRONMENT otherwise redirects
# the project environment even with --project. See https://docs.astral.sh/uv/concepts/projects/config/
# and https://docs.astral.sh/uv/concepts/python-versions/#requesting-a-version.
if [ "${1:-}" = "--prepare-pin" ]; then
  unset VIRTUAL_ENV UV_PROJECT_ENVIRONMENT UV UV_RUN_RECURSION_DEPTH
  if [ ! -x "$root/.venv/bin/python" ]; then
    uv run --quiet --no-sync --project "$root" /bin/sh -c :
  fi
  exec uv run --quiet --no-sync --python "$root/.venv/bin/python" \
    --no-python-downloads --project "$2" /bin/sh -c :
fi

# --- the root is an instance: its pyproject.toml is what uv runs the pinned Python from ---
# Without one, uv runs in no project, gives the command no VIRTUAL_ENV, and the interpreter path
# below would read `/bin/python`. A real instance and a real pin always carry it, so a root without
# one is not an instance; it is refused by name rather than failing on a path that does not exist.
if [ ! -f "$root/pyproject.toml" ]; then
  echo "kensaiapp: $root holds no pyproject.toml, so it is not a kensaiapp instance and no pinned Python can run from it." >&2
  exit 1
fi

# --- hand the caller's environment through uv, and put it back before the interpreter starts ---
for name in $uv_rewritten; do
  unset "KENSAIAPP_CALLER_$name"
  if [ -n "${!name+x}" ]; then
    export "KENSAIAPP_CALLER_$name=${!name}"
  fi
done

restore='
python="$VIRTUAL_ENV/bin/python"
if [ "${KENSAIAPP_CALLER_PATH+x}" ]; then PATH=$KENSAIAPP_CALLER_PATH; export PATH; else unset PATH; fi
if [ "${KENSAIAPP_CALLER_VIRTUAL_ENV+x}" ]; then VIRTUAL_ENV=$KENSAIAPP_CALLER_VIRTUAL_ENV; export VIRTUAL_ENV; else unset VIRTUAL_ENV; fi
if [ "${KENSAIAPP_CALLER_UV+x}" ]; then UV=$KENSAIAPP_CALLER_UV; export UV; else unset UV; fi
if [ "${KENSAIAPP_CALLER_UV_RUN_RECURSION_DEPTH+x}" ]; then UV_RUN_RECURSION_DEPTH=$KENSAIAPP_CALLER_UV_RUN_RECURSION_DEPTH; export UV_RUN_RECURSION_DEPTH; else unset UV_RUN_RECURSION_DEPTH; fi
unset KENSAIAPP_CALLER_PATH KENSAIAPP_CALLER_VIRTUAL_ENV KENSAIAPP_CALLER_UV KENSAIAPP_CALLER_UV_RUN_RECURSION_DEPTH
exec "$python" "$@"
'

exec uv run --quiet --no-sync --project "$root" /bin/sh -c "$restore" sh "$@"
