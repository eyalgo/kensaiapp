#!/usr/bin/env bash
#
# launcher.sh (build-idea) — the owner's one command for the moves a shukuba-refine report leaves
# owed: it reads the report's `## Next moves` table and runs it as a queue.
# Version: 2.9.1 — the queue ends clean after a walk with no station
# Version: 2.9.0 — the close names its station and lands only in trail/; a bad Next-moves Command cell fails only its own row; journey_names owns a station's name
# Version: 2.8.2 — a build-idea queue waits on a live walk and continues when it ends — a refused hand-off waits, an ended walk releases the hold, a detached watcher wakes the queue
# Version: 2.8.1 — launchers and launch scripts take a portable mktemp template, so they run on Linux
# Version: 2.8.0 — ollama is a provider — a launch can run on the owner's local Ollama models
# Version: 2.7.2 — build-idea starts one sweep, not two — the pick waits on a queued sweep and a live walk
# Version: 2.7.1 — the companion sweep runs the chain the project card's Definition names
# Version: 2.7.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 2.6.0 — the launchers accept hf — the seven launchers, the run tools and the structure map take hf as a Claude run aimed at Hugging Face's router
# Version: 2.5.1 — a stop ends the wait — one shared stop that ends a live walk across chain, chain_development and build_idea, marks it ended with a reason and leaves the state file readable
# Version: 2.5.0 — the chain launchers state the provider truth and build-idea describe matches start
# Version: 2.4.0 — the providers file is reverted — every provider is back in code, and SDD runs on one provider again
# Version: 2.3.1 — every chain step and document reads its provider from system/providers.toml
# Version: 2.3.0 — a chain step names its provider, and --provider forces the whole walk
# Version: 2.2.0 — build-idea: the PM picks unless it can't — an empty pool halts, a live product companion runs chain-product first
# Version: 2.1.0 — build-idea runs a refine report rewritten in place, and a retired seed's nemawashi-refine report
# Version: 2.0.0 — Grok is removed — the providers are Claude, Codex and Gemini
# Version: 1.11.0 — adapt Google Gemini as fourth model provider
# Version: 1.10.0 — Grok runs as a provider, model and effort
# Version: 1.9.1 — continue build-idea through nemawashi refinement
# Version: 1.9.0 — build-idea's retire end names the Principal PM's nemawashi-refine, then the pick
# Version: 1.8.0 — build-idea launches the Scrum Master's nemawashi-retire and ends there; no live line gives the retire to the Principal PM
# Version: 1.7.0 — a build-idea start takes a new pin when the host changed
# Version: 1.6.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 1.5.0 — enable provider-neutral unattended execution with Codex
# Version: 1.4.0 — the PM drops a halted unit inside the refine — tobiishi-drop moves to the PM, the chain edits are reverted
# Version: 1.3.0 — the PM decides the drop — a halted walk runs shukuba-refine, which can name a drop row that build-idea runs as tobiishi-drop
# Version: 1.2.0 — a developer past the context cap pauses at a task boundary, and the chain relaunches a fresh one at the next task — --context-cap on chain-change and build-idea, default 250000
# Version: 1.1.0 — the refine table gains the owner's act; build-idea stops at it and names the owner's step
# Version: 1.0.0 — created 2026-09-18 under the bare-identity folder name
#   <CORE>/launchers/build-idea/ (no relocation, no prior name, so no provenance block): resolves
#   <project>, resolves the completion notifier from the environment, and hands the queue to
#   core/tools/build_idea.py's --start entry point, the way chain-change hands its walk to its
#   engine.
#
# WHY THIS EXISTS
#   shukuba-refine ends by writing a table of what its unit leaves owed — close the reached station,
#   pick a seed, cut the route, walk the next change — each with the seat whose move it is and the
#   command that starts it. Until this launcher the owner typed them, one at a time, and had to know
#   which had to wait for which: a chain started beside a still-running close finds the station
#   open and opens a change for it (2026-09-18). This reads the table and starts the commands in
#   the order its After column gives.
#
# WHY THE TABLE IS THE QUEUE
#   The After column names, for each row, the earlier rows that must have LANDED before it starts.
#   Landed is a fact read off the disk by core/tools/build_idea.py — the station's file moved from
#   the shukuba root into trail/, a seed at the seedbed root, a seed with a checklist, a sweep that ended
#   settled — and never the fact that a launcher exited, because every launcher backgrounds its
#   run and returns at once. No model decides what runs next: the kinds a row can be are a literal
#   in the engine, a row of a kind it does not hold is refused before anything starts, and a row
#   whose command is not the command its kind runs is refused alone — it never runs, the rows
#   waiting on it are blocked, and the rest still run.
#
# WHY NOTHING EDITS THE REPORT
#   The report is a record of what a refine run did, and nothing edits it after the run that wrote
#   it. The queue's progress is its own state file, system/logs/build-idea-<project>-state.json,
#   one per project — a second queue on a project whose first is still running is refused.
#
# WHERE THE LOOP CLOSES
#   chain-change's walk ends by starting this launcher with --chain-ended <end> (its WHERE THE LOOP
#   CLOSES paragraph). On sealed the queue starts from the unit that walk just sealed and refined.
#   A unit that serves no station is owed no refine, so when the walk sealed such a unit and no
#   refine report exists, this launcher starts nothing, says so, and exits 0. On any other end this
#   launcher starts nothing and says so. A halted walk, for one, left no refined unit to run. The
#   queue waits for the Scrum Master's nemawashi-retire, then runs the Principal PM's
#   nemawashi-refine for that seed. Its report feeds the same queue. The loop ends at an owner's act
#   owed, an exhausted seedbed, a failed row, a halted walk, or the next change handed to
#   chain-change, whose own end reaches this launcher again. A definition chain still walking pauses
#   the loop rather than ending it. The queue continues by itself once that walk is no longer
#   walking, unless the walk was stopped. THE PICK WAITS ONLY FOR WHAT IT CANNOT PICK WITHOUT says
#   how.
#
# WHICH PIN A START RUNS ON
#   Every other launcher keeps the pin it is inside. This one enters through pin_enter_renewing: a
#   start takes a new pin of its host when the host's core/, .claude/ or skills/ differ from the
#   pin it would inherit, and inherits it otherwise. A queue outlives the pin it started on only
#   by being started again, so the start is where the owner's edits since must be picked up — and
#   the start a walk's end makes (--chain-ended) is such a start. What "differ" means is owned by
#   core/tools/pin_host_changed.py. After the Pin: line the output is this launcher's own,
#   unchanged for every invocation.
#
# HOW TO STOP IT, AND WHERE IT STARTS AGAIN
#   <CORE>/launchers/build-idea/launcher.sh <project> --stop is the owner's brake. It stops the
#   runs in flight, each recorded failed with the stop as its reason: a skill row's launch is
#   stopped by the pid and start time recorded at launch, and a chain row is stopped through that
#   chain's own --stop. The queue ends at once, nothing new starts, and chain-change's end does not
#   restart the loop — it says so on the owner's channel and stops there. The stop persists. Asked
#   when no queue is live, it still records the stop, so one asked between two queues holds. A
#   plain start, with no flag, clears the stop and resumes the recorded queue, including
#   retirement's continuation: a row that landed is skipped, a skill row whose fact now holds on
#   disk is counted landed, and only what is still owed runs. A
#   report every row of which has landed or been handed off is refused as fully consumed. A report
#   a refine re-read wrote again with different content is not that report: the start runs its rows
#   as a new queue. And once the unit's seed has retired to trail/, the start runs that seed's
#   nemawashi-refine report — the same rows the queue would have carried had it run the retire.
#
# THE PICK WAITS ONLY FOR WHAT IT CANNOT PICK WITHOUT
#   The PM always picks unless it can't (the owner, 2026-09-30). It can't with no candidate in
#   unpicked/. It can't yet while a companion is live: any *_open_issues.md under the product's
#   docs/, or the Agari's companion, system/projects/<project>/agari_open_issues.md. The queue then
#   runs the definition chain the card's **Definition:** line names first, chain-product for full
#   and chain-agari for prd-agari, and picks once that walk ends settled. A card reading none names
#   no chain, so its pick does not wait. When a companion is live and the card's **Definition:**
#   line is missing, doubled or out of vocabulary, the pick fails, and the queue ends halted once
#   nothing else is running. The product path is read off the card here and passed to the engine. A
#   card with no product path passes none, and then only the Agari's companion can hold the pick.
#   The queue never starts a second walk of the definition chain. A sweep row it already holds,
#   waiting or launched, is what the pick waits on, and no row is added, unless that row itself
#   waits on the pick: the pick then gets its own sweep row, as before. With no such row, a
#   definition chain still walking holds the pick and no row is added. Still walking is read off
#   system/logs/chain-<project>-state.json the way chain.py's own refusal reads it. A sweep row, or
#   a row that walks the next change, whose launcher exits 4 because a walk is still walking is not
#   failed. It goes back to waiting, and the rows that wait on it stay waiting. A row that runs a
#   skill and exits 4 still fails. Either way the queue launches nothing more while the walk is
#   still walking. The queue looks at the walk again each time one of its own runs ends and each
#   time it is started. Once the walk is no longer walking, the queue launches every waiting row
#   whose After rows have landed, and a pick held for the walk checks the companions afresh. When
#   nothing the queue launched is still running, the queue ends waiting-on-a-walk, its message
#   naming the walk and the command that resumes it. It also leaves a watch on the walk behind. Once
#   the walk is no longer walking, the watch continues the queue and tells the owner so. A walk that
#   was stopped does not continue the queue: the owner is told so, and the next start resumes it.
#   The owner's stop, or a start, ends the watch. A watch that could not be started is said in the
#   waiting-on-a-walk message, and then only the next start resumes the queue. A failed row still
#   ends the queue halted, and a stop still ends it stopped.
#
# THE DEVELOPER'S CONTEXT CAP
#   --context-cap <tokens> is the context past which a developer's run pauses at a task boundary and
#   a fresh developer takes the change over. The queue records it and puts it on every chain-change
#   row it launches — that launcher alone; chain-product takes no such flag. It is passed to the
#   engine's --start only when given, so the default (250000) lives in the engine and cannot drift
#   from this launcher, and it is refused here, before the engine or its --describe runs, unless it
#   is a positive integer. A queue that is resumed keeps the cap it started with.
#
# USAGE
#   <CORE>/launchers/build-idea/launcher.sh <project> [<unit-key>] [--provider claude|codex|gemini|hf|ollama]
#                                           [--dry-run] [--keep-awake]
#                                           [--context-cap <tokens>] [--chain-ended <end>]
#   <CORE>/launchers/build-idea/launcher.sh <project> --stop
#     (run from the instance root)
#     <project>     a project under system/projects/<project>/
#     <unit-key>    the unit whose report to run, <YYYY-MM-DD>_<slug>; the sealed unit
#                   CONTEXT_PM.md names when omitted
#     --provider    force every queued skill and nested chain onto one provider, over the one a
#                   row's or a chain step's own entry names. An exported
#                   KENSAIAPP_AGENT_PROVIDER is the same force; the flag wins. With neither, each
#                   skill row runs on its own entry in .providers.toml at the instance root; a row
#                   whose entry is missing is refused, naming the entry, and nothing runs on a
#                   provider the file did not name. A row that starts a chain has no entry of
#                   its own: it is handed the queue's force alone, and the chain reads the file
#                   for its own steps.
#                   Every start states the force, a resume included; the start a chain-change
#                   walk's end makes carries it in its environment.
#     --dry-run     ask the engine what a start would run, print each row with its After and its
#                   command, then the exact engine invocation, and start nothing — or fail with the
#                   reason a start would be refused
#     --keep-awake  passed down to every launcher the queue starts rather than held here, because
#                   this script exits once the first rows are launched and the queue goes on in the
#                   detached runs; each launcher already owns the mechanism through
#                   core/tools/detach_watcher.sh
#     --context-cap <tokens>
#                   the context, in tokens, past which the developer's run pauses and a fresh one
#                   continues; a positive integer, put on every chain-change row the queue starts
#                   and kept by a resumed queue. Omitted, the engine's own default applies.
#     --chain-ended <end>
#                   what a chain-change walk passes when it ends. sealed starts the queue as the
#                   hook's own start, which a standing stop suppresses. A sealed unit that serves no
#                   station and has no refine report starts no queue: this launcher prints why and
#                   exits 0. Anything else prints that nothing was started and exits 0
#     --stop        stop the runs in flight and end the queue at once, printing what it stopped; a
#                   chain row is stopped through that chain's own --stop. Takes no unit key,
#                   --dry-run or --chain-ended, and exits with the engine's status
#
set -euo pipefail

# --- resolve the instance root (the caller's cwd) and cd there ----------------------
#   CORE_DIR strips this script's own resolved directory at the /launchers/ boundary, so it
#   reaches <CORE> from any nesting depth. The instance is the caller's cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # <CORE>/launchers/build-idea
INSTANCE_ROOT="$PWD"
cd "$INSTANCE_ROOT"
CORE_DIR="${SCRIPT_DIR%/launchers/*}"
[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "build-idea: no /launchers/ ancestor above $SCRIPT_DIR — refusing to guess <CORE>" >&2; exit 1; }
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
# shellcheck source=/dev/null
source "$CORE_DIR/tools/pin_run.sh"
pin_enter_renewing "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?

# The engine's own CLI entry point. A test points this at a recording stub so a real --start —
# which would launch real runs — is never reached from the contract half of the suite.
CHAIN_SCRIPT="${LAUNCH_BUILD_IDEA_SCRIPT:-$CORE_DIR/tools/build_idea.py}"

# Resolved HERE, from the environment, and PASSED to the engine as a parameter — the engine reads
# no environment for it, because every advance re-enters as a fresh detached process. An unset
# notifier is skipped, never an error.
NOTIFIER="${KENSAIAPP_NOTIFIER:-}"

die() { echo "build-idea: $*" >&2; exit 1; }

# --- args --------------------------------------------------------------------------
project="${1:-}"
unit_key=""
dry_run=""
keep_awake=""
context_cap=""
context_cap_given=""
chain_ended=""
stop=""
# The force: the flag, else an exported KENSAIAPP_AGENT_PROVIDER, else none. Passed to the engine
# as a parameter and kept on its state — the engine sets the variable for each run it launches,
# so nothing here exports it.
provider="${KENSAIAPP_AGENT_PROVIDER:-}"
[ $# -eq 0 ] || shift
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)     dry_run=1 ;;
    --keep-awake)  keep_awake=1 ;;
    --stop)        stop=1 ;;
    --provider)    [ $# -ge 2 ] || die "--provider needs claude, codex, gemini, hf or ollama"
                   provider="$2"; shift ;;
    --provider=*)  provider="${1#--provider=}" ;;
    --context-cap) context_cap_given=1
                   [ $# -ge 2 ] || die "--context-cap needs a value: a positive integer of tokens"
                   context_cap="$2"; shift ;;
    --chain-ended) { [ $# -ge 2 ] && [ -n "$2" ]; } || die "--chain-ended needs the end the chain reported (sealed, halted, ...)"
                   chain_ended="$2"; shift ;;
    --*)           die "unknown flag: $1" ;;
    *)             [ -z "$unit_key" ] || die "unexpected argument: $1 — the unit is named once"
                   unit_key="$1" ;;
  esac
  shift
done
[ -n "$project" ] || die "usage: <CORE>/launchers/build-idea/launcher.sh <project> [<unit-key>] [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake] [--context-cap <tokens>] [--chain-ended <end>] | <project> --stop"
case "$provider" in ""|claude|codex|gemini|hf|ollama) ;; *) die "provider must be claude, codex, gemini, hf or ollama (got '$provider')" ;; esac
if [ -n "$context_cap_given" ]; then
  case "$context_cap" in
    ""|*[!0-9]*) die "--context-cap '$context_cap' is not a positive integer of tokens" ;;
  esac
  [ "$((10#$context_cap))" -gt 0 ] || die "--context-cap '$context_cap' is not a positive integer of tokens"
fi
if [ -n "$stop" ] && { [ -n "$unit_key" ] || [ -n "$dry_run" ] || [ -n "$chain_ended" ]; }; then
  die "usage: <CORE>/launchers/build-idea/launcher.sh <project> --stop — a stop takes no unit key, --dry-run or --chain-ended"
fi

project_md="$INSTANCE_ROOT/system/projects/$project/project.md"
[ -f "$project_md" ] || die "no project card at $project_md (is '$project' a real project?)"

# --- the product path, read the way chain-product reads it; a card with none checks nothing ------
#   A pick waits for the product chain while one of the product's documents has a live companion,
#   so the engine is told where those documents are.
raw_path="$(grep -m1 -E '^\*\*Product path:\*\*' "$project_md" \
  | sed -E 's/^\*\*Product path:\*\*[[:space:]]*//; s/[[:space:]]*<!--.*$//; s/[[:space:]]*$//' || true)"
case "$raw_path" in
  "")    product_path="" ;;
  "~"/*) product_path="${HOME}/${raw_path#\~/}" ;;
  /*)    product_path="$raw_path" ;;
  *)     product_path="$INSTANCE_ROOT/$raw_path" ;;
esac

# --- a chain that did not seal left nothing to run -----------------------------------
if [ -n "$chain_ended" ] && [ "$chain_ended" != "sealed" ]; then
  echo "build-idea: the chain ended $chain_ended — nothing to start"
  exit 0
fi

log_dir="$INSTANCE_ROOT/system/logs"
state_path="$log_dir/build-idea-$project-state.json"

# --- the owner's stop: recorded by the engine, which says what it will do --------------
if [ -n "$stop" ]; then
  set -- python3 "$CHAIN_SCRIPT" --stop "$state_path" \
    --instance-root "$INSTANCE_ROOT" --project "$project"
  [ -n "$NOTIFIER" ] && set -- "$@" --notifier "$NOTIFIER"
  "$@" && rc=0 || rc=$?
  exit "$rc"
fi

echo "build-idea: project=$project"
if [ -n "$provider" ]; then
  echo "build-idea: provider=$provider (forced on every row)"
else
  echo "build-idea: provider=each row's own"
fi

# --- hand the queue to the engine, through its --start CLI ---------------------------
#   set -- / "$@" is the corpus's own way of building a command so --dry-run can print exactly
#   what would run.
set -- python3 "$CHAIN_SCRIPT" --start "$state_path" \
  --instance-root "$INSTANCE_ROOT" --project "$project" --core-dir "$CORE_DIR" --shim-dir "$log_dir"
[ -n "$unit_key" ] && set -- "$@" --key "$unit_key"
[ -n "$NOTIFIER" ] && set -- "$@" --notifier "$NOTIFIER"
[ -n "$keep_awake" ] && set -- "$@" --keep-awake
[ -n "$context_cap" ] && set -- "$@" --context-cap "$context_cap"
[ -n "$product_path" ] && set -- "$@" --product-path "$product_path"
[ -n "$provider" ] && set -- "$@" --provider "$provider"
# The walk's own end reaches this launcher with --chain-ended, and only that start is the hook's:
# the engine does nothing for it while the owner's stop stands. A start the owner types is never it.
[ -n "$chain_ended" ] && set -- "$@" --by-hook

if [ -n "$dry_run" ]; then
  # Ask the engine what a start would run before printing the command, so a dry run never reports a
  # queue the real start refuses. --describe runs the same checks --start makes, the provider-file
  # check included, and writes, launches and sends nothing. It is told the force exactly when the
  # start is (the same $provider under the same test), so a forced dry run does not read the file.
  # Its output goes to a FILE, never through a pipe, the same descriptor rule
  # core/launchers/skill/launcher.sh states at its launch.
  describe_out="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-build-idea-describe.XXXXXX")"
  describe_args=(python3 "$CHAIN_SCRIPT" --describe "$state_path"
    --instance-root "$INSTANCE_ROOT" --project "$project" --core-dir "$CORE_DIR"
    --shim-dir "$log_dir")
  [ -n "$unit_key" ] && describe_args+=(--key "$unit_key")
  [ -n "$provider" ] && describe_args+=(--provider "$provider")
  "${describe_args[@]}" >"$describe_out" 2>&1 && rc=0 || rc=$?
  describe_text="$(cat "$describe_out")"
  rm -f "$describe_out"
  [ "$rc" -eq 0 ] || die "a start would be refused — ${describe_text#build_idea: }"
  # A report whose section says "None —" has no rows, so the engine prints none; say so rather than
  # leave a DRY RUN block under silence.
  echo "${describe_text:-(no rows — the report names no next moves)}"
  echo "DRY RUN — would run:"
  printf '  %q' "$@"; echo
  exit 0
fi

"$@"
