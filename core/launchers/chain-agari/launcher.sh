#!/usr/bin/env bash
#
# launcher.sh (chain-agari) — the owner's one command for walking a project's PRD and then its Agari.
# Version: 1.3.0 — ollama is a provider — a launch can run on the owner's local Ollama models
# Version: 1.2.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 1.1.0 — the launchers accept hf — the seven launchers, the run tools and the structure map take hf as a Claude run aimed at Hugging Face's router
# Version: 1.0.0 — created: the PRD and the Agari walked as a chain of their own, sharing chain-product's one walk per project
#
# WHAT IT LAUNCHES
#   core/tools/chain.py's walk over the spine PRD,Agari: the project's PRD first, then its Agari,
#   which is set off the back of the PRD (core/docs/michi_agari.md, "set once, off the back of the
#   PRD"). The engine starts every document's producer and every answer run. This launcher spawns
#   no model and builds no answer step of its own.
#
#   The spine is what the walk starts on its own initiative, and it stops at the Agari. A
#   "## Launchers owed" bullet that names a document outside the spine is still walked, because
#   the engine never narrows the owed set by the spine (core/tools/chain.py § THE SPINE AND THE
#   OWED SET ARE TWO DIFFERENT THINGS, the owner's ruling of 2026-08-31).
#
# WHAT IT ASSUMES
#   Each assumption is checked before the engine runs. A missing one exits 1 with one line on
#   stderr, and nothing is started.
#   - The launcher is run from the instance root. The project card is looked up under the
#     directory it was run from, and where no card is there the launcher refuses with
#     "chain-agari: no project card at <card path> (is '<project>' a real project?)".
#   - The card, system/projects/<project>/project.md, holds a **Product path:** line. Where it
#     holds none the launcher refuses with "chain-agari: no 'Product path:' line in <card path>".
#   - This script sits under a /launchers/ ancestor, which is how it finds <CORE>. Where it sits
#     under none the launcher refuses with
#     "chain-agari: no /launchers/ ancestor above <the script's directory> — refusing to guess <CORE>".
#
# ONE WALK PER PROJECT, SHARED WITH chain-product
#   This launcher hands the engine the state file system/logs/chain-<project>-state.json, the same
#   file chain-product hands it, and the engine keeps one walk per state file
#   (core/tools/chain.py, "One chain per project at a time"). A start is therefore refused while a
#   chain-product walk is live on the project, and a chain-product start is refused while a walk
#   this launcher started is live. The refusal prints the stop command of the launcher whose walk
#   is live. A walk that has ended, under either launcher, blocks neither.
#
# THE NAME
#   The folder is chain-agari because the chain name is "agari", and the engine prints a live
#   walk's stop command as <CORE>/launchers/chain-<chain name>/launcher.sh <project> --stop
#   (core/tools/walk_stop.py § stop_command). A folder renamed without its chain name would print
#   a stop command naming a launcher that does not exist. The chain name names where the walk
#   stops, the Agari (the architect's call, 2026-10-04).
#
# USAGE
#   <CORE>/launchers/chain-agari/launcher.sh <project> [--provider claude|codex|gemini|hf|ollama]
#                                                      [--on-end <command>] [--dry-run] [--keep-awake]
#     (run from the instance root)
#     <project>     a project under system/projects/<project>/
#     --provider    force every producer and answer run onto one provider, over the one its
#                   document's own entry names in .providers.toml at the instance root.
#                   The value may also
#                   be given as --provider=<p>. An exported KENSAIAPP_AGENT_PROVIDER is the same
#                   force, and the flag wins over it. With neither, each document's runs take
#                   their provider from that document's entry in the file, and an owed item whose
#                   path names no document takes it from the file's [owed-items] entry. A launch
#                   whose entry is missing is refused, naming the entry, and nothing runs on a
#                   provider the file did not name. The force is kept on the walk's state, so it
#                   holds for every run the walk starts after this script has exited.
#     --on-end <command>
#                   a command the walk runs once when it ends, however it ends, with how it ended
#                   appended as its last argument. This launcher only carries it to the engine,
#                   and core/tools/chain.py runs it. It takes the next argument as its value, and
#                   a missing or empty value is refused.
#     --dry-run     print the four start lines and the exact engine command a start would run,
#                   then exit without starting anything
#     --keep-awake  keep the machine awake while the walk lasts. The flag is handed to the engine,
#                   which passes it to every launcher the walk runs, because this script exits
#                   seconds after the first run is launched. Each of those launchers holds the
#                   machine awake for as long as its run's completion watcher lives
#                   (core/tools/detach_process_watcher.sh), so this script starts no caffeinate
#                   of its own.
#
#   <CORE>/launchers/chain-agari/launcher.sh <project> --stop
#     --stop        stop the project's live walk, whichever of this launcher and chain-product
#                   started it. The engine stops the run the walk is waiting on, its watcher
#                   first, and signals a process only while its pid still has the start time
#                   recorded at launch. It ends the walk `stopped`, keeps its state file and runs
#                   the walk's --on-end command with `stopped`. A stop takes no other flag, and
#                   the launcher exits with the engine's status.
#
set -euo pipefail

# --- resolve the instance root (the caller's cwd) and cd there ----------------------
#   CORE_DIR strips this script's own resolved directory at the /launchers/ boundary, so it
#   reaches <CORE> from any nesting depth rather than by counting a fixed number of levels. The
#   instance is the caller's cwd: this launcher derives no instance identity of its own.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # <CORE>/launchers/chain-agari
INSTANCE_ROOT="$PWD"
cd "$INSTANCE_ROOT"
CORE_DIR="${SCRIPT_DIR%/launchers/*}"
[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "chain-agari: no /launchers/ ancestor above $SCRIPT_DIR — refusing to guess <CORE>" >&2; exit 1; }
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
# shellcheck source=/dev/null
source "$CORE_DIR/tools/pin_run.sh"
pin_enter "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?

# The engine's own CLI entry point. A test points this at a recording fake, so the real chain.py,
# which would launch a real producer for a missing document, is never reached from the suite.
CHAIN_SCRIPT="${LAUNCH_CHAIN_AGARI_SCRIPT:-$CORE_DIR/tools/chain.py}"

# KENSAIAPP_NOTIFIER is resolved here and passed to the engine as a parameter: chain.py's own
# notifier port reads no environment for it. An unset notifier is skipped, never an error.
NOTIFIER="${KENSAIAPP_NOTIFIER:-}"

# The spine and the chain name are literals, not composed from an argument and not read from the
# caller's environment. The suite pins both, so changing either is a test change. The folder is
# chain-<chain name> because the engine prints a live walk's stop command from that name.
SPINE="PRD,Agari"
CHAIN_NAME="agari"

die() { echo "chain-agari: $*" >&2; exit 1; }

# --- args --------------------------------------------------------------------------
project="${1:-}"
dry_run=""
keep_awake=""
on_end=""
stop=""
other_flag=""
# The force: the flag, else an exported KENSAIAPP_AGENT_PROVIDER, else none. The engine sets the
# variable for each run it launches and keeps the force on its state, so nothing here exports it.
provider="${KENSAIAPP_AGENT_PROVIDER:-}"
[ $# -eq 0 ] || shift
while [ $# -gt 0 ]; do
  case "$1" in
    --stop)       stop=1 ;;
    --dry-run)    dry_run=1; other_flag=1 ;;
    --keep-awake) keep_awake=1; other_flag=1 ;;
    --provider)   [ $# -ge 2 ] || die "--provider needs claude, codex, gemini, hf or ollama"
                  provider="$2"; other_flag=1; shift ;;
    --provider=*) provider="${1#--provider=}"; other_flag=1 ;;
    --on-end)     { [ $# -ge 2 ] && [ -n "$2" ]; } || die "--on-end needs a command"
                  on_end="$2"; other_flag=1; shift ;;
    --*)          die "unknown flag: $1" ;;
    *)            die "unexpected argument: $1" ;;
  esac
  shift
done
[ -n "$project" ] || die "usage: <CORE>/launchers/chain-agari/launcher.sh <project> [--provider claude|codex|gemini|hf|ollama] [--on-end <command>] [--dry-run] [--keep-awake] | <project> --stop"
case "$provider" in ""|claude|codex|gemini|hf|ollama) ;; *) die "provider must be claude, codex, gemini, hf or ollama (got '$provider')" ;; esac

project_md="$INSTANCE_ROOT/system/projects/$project/project.md"
[ -f "$project_md" ] || die "no project card at $project_md (is '$project' a real project?)"

# --- resolve the Product path (strip the '**Product path:**' label + trailing comment)
raw_path="$(grep -m1 -E '^\*\*Product path:\*\*' "$project_md" \
  | sed -E 's/^\*\*Product path:\*\*[[:space:]]*//; s/[[:space:]]*<!--.*$//; s/[[:space:]]*$//' || true)"
[ -n "$raw_path" ] || die "no 'Product path:' line in $project_md"   # `|| true` above: pipefail would otherwise exit before this guard reports

# absolute / ~ → external; otherwise relative to the instance repo -------------------
case "$raw_path" in
  "~"/*) product_path="${HOME}/${raw_path#\~/}" ;;
  /*)    product_path="$raw_path" ;;
  *)     product_path="$INSTANCE_ROOT/$raw_path" ;;
esac

# The state file is the one chain-product hands the engine, and the engine keeps one walk per
# state file, so the two launchers share one walk per project. This script never reads it.
log_dir="$INSTANCE_ROOT/system/logs"
state_path="$log_dir/chain-$project-state.json"

# --- the owner's brake: handed to the engine, which stops the walk's runs and ends it --------
#   --stop stands alone. Another flag beside it names a start, and a start beside a stop means
#   neither, so it is refused before the engine runs.
if [ -n "$stop" ]; then
  [ -z "$other_flag" ] || die "usage: <CORE>/launchers/chain-agari/launcher.sh <project> --stop — a stop takes no other flag"
  set -- python3 "$CHAIN_SCRIPT" --stop "$state_path"
  [ -n "$NOTIFIER" ] && set -- "$@" --notifier "$NOTIFIER"
  "$@" && rc=0 || rc=$?
  exit "$rc"
fi
shim_path="$log_dir/chain-$project.sh"

echo "chain-agari: project=$project"
echo "chain-agari: product path=$product_path"
echo "chain-agari: spine=$SPINE"
if [ -n "$provider" ]; then
  echo "chain-agari: provider=$provider (forced on every document)"
else
  echo "chain-agari: provider=each document's own"
fi

# --- hand the walk to the engine, through its --start CLI ---------------------------
#   set -- / "$@" is the corpus's own way of building a command so --dry-run can print
#   exactly what would run.
set -- python3 "$CHAIN_SCRIPT" --start "$state_path" \
  --instance-root "$INSTANCE_ROOT" --product-path "$product_path" \
  --project "$project" --core-dir "$CORE_DIR" --shim-path "$shim_path" \
  --spine "$SPINE" --chain-name "$CHAIN_NAME"
[ -n "$NOTIFIER" ] && set -- "$@" --notifier "$NOTIFIER"
[ -n "$keep_awake" ] && set -- "$@" --keep-awake
[ -n "$on_end" ] && set -- "$@" --on-end "$on_end"
[ -n "$provider" ] && set -- "$@" --provider "$provider"

if [ -n "$dry_run" ]; then
  echo "DRY RUN — would run:"
  printf '  %q' "$@"; echo
  exit 0
fi

"$@"
