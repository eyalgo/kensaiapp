#!/usr/bin/env bash
# detached_run.sh — start one unattended run as a detached process, and say where it is.
# Version: 1.2.0 — the queue runs readme-status after each close
# Version: 1.1.0 — a stop ends the wait — one shared stop that ends a live walk across chain, chain_development and build_idea, marks it ended with a reason and leaves the state file readable
# Version: 1.0.0
#
# The launch half of the process path the three chain launchers (`skill`, `companion-self-answer`,
# `product-sdd`) share, for either provider: `<CORE>/tools/agent_run.py --background` starts the
# run, and this file is the one place a launcher hands it the command, reads back its record and
# prints where the run is. The watch half is `detach_process_watcher.sh`, which a launcher sources
# separately because a missing watcher must never cost the launch.

# The variables a chain (`chain.py`, `chain_development.py`, `build_idea.py`) and `instrument_run`
# set for a LAUNCHER — its completion hook and the tags `instrument_run` has already folded into the
# run's `--settings` by the time the run starts. None of them reached a `claude --bg` session, which
# takes only a few named variables from the shell that dispatched it
# (https://code.claude.com/docs/en/agent-view.md); a detached process would inherit them, and a run that started a launcher of its
# own would then hand that launcher's watcher its parent chain's hook. So the run is started without
# them, whichever the provider. DETACHED_RUN_IDENTITY_FILE is one of them: it names the file THIS
# launch's identity is written to, so a launcher a run started would otherwise write over its
# parent's file and a stop would then signal the wrong launch. DETACHED_RUN_RESULT_FILE is the
# same kind: it names where THIS launch's watcher publishes the run's final message, so a launch
# the run started would otherwise publish over its parent's receipt.
DETACHED_RUN_WITHHELD=(DETACH_WATCHER_ON_COMPLETE INSTRUMENT_RUN_CHAIN INSTRUMENT_RUN_WALK_ID
  INSTRUMENT_RUN_ROLE INSTRUMENT_RUN_AUDIT_TARGET INSTRUMENT_RUN_SETTINGS
  DETACHED_RUN_IDENTITY_FILE DETACHED_RUN_RESULT_FILE)

# print_detached_run <agent_run.py command…>
#   The dry run: the exact provider command the launch would start, indented, or the runner's own
#   refusal and a non-zero return when it refuses the request.
print_detached_run() {
  local printed rc
  printed="$("$@" --dry-run)" && rc=0 || rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "the launch was refused (exit $rc) — nothing would launch" >&2
    return "$rc"
  fi
  printf '%s\n' "$printed" | sed 's/^/  /'
}

# start_detached_run <agent_run.py --background command…>
#   Starts the run through the provider-neutral runner with DETACHED_RUN_WITHHELD kept from it,
#   echoes the runner's one JSON record, and sets DETACHED_RUN_PID and DETACHED_RUN_SESSION_ID (the
#   Claude session the run was named with; empty for Codex). The runner detaches the run into its
#   own session with its output going to the run log, so capturing the runner's stdout waits only
#   for the runner. Returns non-zero, saying why, when the runner refuses or prints no record.
start_detached_run() {
  local withheld=() name launch_out rc record
  for name in "${DETACHED_RUN_WITHHELD[@]}"; do withheld+=(-u "$name"); done
  launch_out="$(env "${withheld[@]}" "$@")" && rc=0 || rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "the launch was refused (exit $rc) — nothing launched" >&2
    return "$rc"
  fi
  printf '%s\n' "$launch_out"
  record="$(python3 -c 'import json,sys; r = json.loads(sys.argv[1]); print(r["pid"], r["session_id"] or "")' \
    "$launch_out" 2>/dev/null)" || { echo "the launch printed no run record — nothing to watch" >&2; return 1; }
  read -r DETACHED_RUN_PID DETACHED_RUN_SESSION_ID <<<"$record"
  export DETACHED_RUN_PID DETACHED_RUN_SESSION_ID
}

# announce_detached_run <run-log>
#   The lines the owner reads to find the run: its log, and — for Claude — the session it was named
#   with, which `claude --resume` opens once the run has ended.
announce_detached_run() {
  echo "Launched. Run log: $1"
  [ -z "${DETACHED_RUN_SESSION_ID:-}" ] \
    || echo "          Session:  $DETACHED_RUN_SESSION_ID   (once the run has ended, claude --resume $DETACHED_RUN_SESSION_ID opens it)"
}

# record_detached_run_identity
#   Writes who this launch is, for the engine that asked: the run's pid (DETACHED_RUN_PID) and the
#   watcher's (DETACH_PROCESS_WATCHER_PID), each with its start time, to the file the engine named in
#   DETACHED_RUN_IDENTITY_FILE. An engine's stop reads it back and signals a process only while its
#   pid still has that start time, so a recycled pid is never signalled (`walk_stop.py`).
#   Does nothing when the engine named no file. Always returns 0: it runs after the run has
#   launched, so a record that cannot be written costs a note and never the launch.
record_detached_run_identity() {
  [ -n "${DETACHED_RUN_IDENTITY_FILE:-}" ] || return 0
  local walk_stop recorded=()
  walk_stop="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/walk_stop.py"
  [ -z "${DETACHED_RUN_PID:-}" ] || recorded+=(--run-pid "$DETACHED_RUN_PID")
  [ -z "${DETACH_PROCESS_WATCHER_PID:-}" ] \
    || recorded+=(--watcher-pid "$DETACH_PROCESS_WATCHER_PID")
  # The recorder's own stderr is dropped so a failure is one note line, whatever it said.
  python3 "$walk_stop" record "$DETACHED_RUN_IDENTITY_FILE" ${recorded[@]+"${recorded[@]}"} \
    2>/dev/null \
    || echo "(could not record the launch identity at $DETACHED_RUN_IDENTITY_FILE — a stop will find no run to stop)" >&2
  return 0
}
