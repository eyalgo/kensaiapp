#!/usr/bin/env bash
# detach_process_watcher.sh — detach the structured provider-process observer.
# Version: 2.1.1 — the content seat split states what it made false, and the content step is audited
# Version: 2.1.0 — give the watcher its own session so launcher cleanup cannot lose the callback
# Version: 2.0.0 — the three chains run Claude as a detached claude -p process, not claude --bg
# Version: 1.0.0
#
# The run is a process `agent_run.py --background` detached — a Claude `--print` run or a Codex
# `exec --json` run — and `--provider` names which, so `watch_process.py` reads its log with that
# provider's inspector. The watcher's log is named by `detach_watch_log_file`, the one spelling
# `chain_usage.py` reads, and appended to rather than truncated, as the `claude --bg` watcher's is.

_detach_process_watcher_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=detach_watcher.sh
source "$_detach_process_watcher_dir/detach_watcher.sh"
unset _detach_process_watcher_dir

detach_process_watcher() {
  local watcher="" notifier="" instance_root="" label="" log_stem="" reporter="" provider=""
  local pid="" run_log="" multi_turn="" artifact_path="" head_repo="" document_stem=""
  local done_when_exists="" on_complete="${DETACH_WATCHER_ON_COMPLETE:-}"
  local keep_awake="" poll_seconds="5" poll_given=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --watcher) watcher="$2"; shift 2 ;;
      --provider) provider="$2"; shift 2 ;;
      --notifier) notifier="$2"; shift 2 ;;
      --instance-root) instance_root="$2"; shift 2 ;;
      --label) label="$2"; shift 2 ;;
      --log-stem) log_stem="$2"; shift 2 ;;
      --reporter) reporter="$2"; shift 2 ;;
      --pid) pid="$2"; shift 2 ;;
      --run-log) run_log="$2"; shift 2 ;;
      --artifact-path) artifact_path="$2"; shift 2 ;;
      --head-repo) head_repo="$2"; shift 2 ;;
      --document-stem) document_stem="$2"; shift 2 ;;
      --done-when-exists) done_when_exists="$2"; shift 2 ;;
      --on-complete) on_complete="$2"; shift 2 ;;
      --poll-seconds) poll_seconds="$2"; poll_given=1; shift 2 ;;
      --multi-turn) multi_turn=1; shift ;;
      --keep-awake) keep_awake=1; shift ;;
      *) echo "detach_process_watcher: unrecognized argument: $1" >&2; return 1 ;;
    esac
  done
  local name value
  for name in watcher provider instance_root label log_stem reporter pid run_log; do
    value="${!name}"
    [ -n "$value" ] || { echo "detach_process_watcher: --${name//_/-} is required" >&2; return 1; }
  done
  [ -f "$watcher" ] || { echo "          (no process watcher at $watcher — completion watch skipped)"; return 0; }
  local notify_target="${notifier:-/usr/bin/true}"
  [ -x "$notify_target" ] || notify_target=/usr/bin/true
  # One log per watch. The name is stamped to the second and a chain can launch several runs of one
  # skill within it (the audit fan-out), so the name is claimed with noclobber and a taken
  # one waits for the next second's stamp — never a suffix, which `chain_usage.py` would not read.
  local observer_log
  observer_log="$(detach_watch_log_file "$instance_root" "$log_stem")"
  until ( set -C; : >"$observer_log" ) 2>/dev/null; do
    if [ ! -e "$observer_log" ]; then
      echo "          (cannot create the watcher log $observer_log — completion watch skipped)"
      return 0
    fi
    sleep 1
    observer_log="$(detach_watch_log_file "$instance_root" "$log_stem")"
  done
  local -a command=(python3 "$watcher" --provider "$provider" --pid "$pid" --log "$run_log"
    --label "$label" --cwd "$instance_root" --reporter "$reporter"
    --notify "$notify_target" --poll-seconds "$poll_seconds")
  [ -z "$artifact_path" ] || command+=(--artifact-path "$artifact_path")
  [ -z "$head_repo" ] || command+=(--head-repo "$head_repo")
  [ -z "$document_stem" ] || command+=(--document-stem "$document_stem")
  [ -z "$done_when_exists" ] || command+=(--done-when-exists "$done_when_exists")
  [ -z "$multi_turn" ] || command+=(--multi-turn)
  [ -z "$on_complete" ] || command+=(--on-complete "$on_complete")
  DETACH_PROCESS_WATCHER_PID="$(python3 - "$observer_log" "${command[@]}" <<'PY'
import subprocess
import sys

try:
    with open(sys.argv[1], "ab") as log:
        process = subprocess.Popen(
            sys.argv[2:], stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
except OSError as exc:
    raise SystemExit(f"detach_process_watcher: {exc}") from None
print(process.pid)
PY
  )" || return 1
  DETACH_PROCESS_WATCHER_START="$(
    ps -o lstart= -p "$DETACH_PROCESS_WATCHER_PID" 2>/dev/null || true
  )"
  export DETACH_PROCESS_WATCHER_PID DETACH_PROCESS_WATCHER_START
  echo "          Completion watch: $observer_log"
  if [ -n "$keep_awake" ]; then
    detach_identity_keep_awake \
      "$DETACH_PROCESS_WATCHER_PID" "$DETACH_PROCESS_WATCHER_START" "run" \
      "${poll_given:+$poll_seconds}"
  fi
}
