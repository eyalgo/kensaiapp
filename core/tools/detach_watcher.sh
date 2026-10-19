#!/usr/bin/env bash
#
# detach_watcher.sh — the one home for the completion-watch detach-and-return block.
#
# Version: 1.11.1 — the neutrality check reads fixtures and .claude/, declares platform names, and repairs fixture hits itself; the ratify launcher is deleted
# Version: 1.11.0 — the three chains run Claude as a detached claude -p process, not claude --bg
# Version: 1.10.0 — enable provider-neutral unattended execution with Codex
# Version: 1.9.4 — the launchers suite passes in a full run — cases no longer depend on test order, run length or load
# Version: 1.9.3 — ad-hoc-implementation retires, and ad-hoc-flow — the launcher and workflow that ran it — retires with it
# Version: 1.9.2 — chain-definition, chain-foundation and the eight product document launchers are retired into chain-product and the skill launcher
# Version: 1.9.1 — the vendor-neutrality check reaches the whole vendored layer, keys its allowlist on text, and reads the live journey
# Version: 1.9.0 — the chain reads the run it made — five fixes off its first live run
# Version: 1.8.0 — the chain runs itself — a general engine, entered once per tier
# Version: 1.7.1 — `capture_agent_id` reads the id from the third field instead of the last. A
#   launcher passing `-n` puts the session NAME last, so the parse handed the watcher a name and
#   the watch died at its appear deadline while the run ran on unwatched. `$3` is the id whether
#   or not `-n` is present.
#
# Version: 1.7.0 — two flags pass through to the watcher for a caller whose run ends its turn
#   many times on purpose: `--multi-turn` and `--done-when-exists <path>`. Both are appended only
#   when set, exactly like `--keep-awake`, and this file enforces neither the pairing rule nor the
#   path's shape — `watch_agent.py` owns its own argument rules and a library that re-checked them
#   would be a second copy free to drift. Added for `product-sdd`, whose runner is the fleet's only
#   multi-turn run today.
#
# Version: 1.6.0 — the parse that turns a launch into an id now lives here too, as the public
#   `capture_agent_id`, and `--launch-output` lets a caller hand over the raw output and never
#   own a copy of it. It came from `launch-skill-evals`, which had the fleet's only copy and used
#   it for its round lock; that launcher now calls this one, so the repo has exactly one place
#   where a `backgrounded` line is read (`core/tools/test_agent_id_handover.py` proves that from
#   disk rather than asserting it). Two ways in, because the callers are two shapes: a launcher
#   that wants the id only for its watcher passes `--launch-output` and parses nothing; one that
#   needs the value for something else — a round lock, a hand-built `watch_args` — calls
#   `capture_agent_id` itself and passes `--agent-id`, which wins over any parse this file would
#   have done.
# Version: 1.5.0 — the library can now forward the one handle the watcher says it prefers:
#   --agent-id is accepted and passed straight through to `watch_agent.py`, which declares it
#   "the exact handle" and stops consulting the name entirely when it has one
#   (`watch_agent.py:155`). Optional, like --head-repo and --noun beside it, and appended to the
#   watcher's argv only when non-empty — so the sixteen callers that pass nothing get the argv
#   they get today, unchanged, and stay on the name-then-candidate-set fallback. Capturing the id
#   at the launch is each launcher's own work; this file is only what was between them.
# Version: 1.4.0 — the fan-out caller shape this header has always declared is now actually
#   served: `DETACH_WATCHER_START` is published beside `DETACH_WATCHER_PID`, so a caller that
#   binds one keep-awake across N watchers can build the same identity-keyed release this
#   library performs, instead of re-reading `ps` afterwards and racing the reissue the pairing
#   exists to close. `core/launchers/cold-read/launcher.sh` was the one file still writing the
#   tail by hand; it now calls this one, and no `.sh` in the repo carries a copy.
# Version: 1.3.0 — every launcher that hand-copied this block now calls it, and one optional
#   flag is what made that a pure refactor: --keepawake-poll-seconds lets a migrating caller
#   hand in its own already-documented LAUNCH_<X>_KEEPAWAKE_POLL_SECONDS rather than have its
#   knob renamed out from under its suite. Fifteen callers, up from six.
# Version: 1.2.0 — --keep-awake no longer binds a bare pid number, dropping caffeinate's own
#   wait flag entirely: the watcher's pid is paired with the start time it had when this library
#   spawned it, and a detached poller releases caffeinate the moment a live process at that number
#   stops matching both — never the lifetime of whatever unrelated process the kernel later
#   reissues the number to. Six launchers source this file and carry no caffeinate of their own,
#   so all six inherit the release without being edited.
# Version: 1.1.0
#
# WHY THIS EXISTS
#   Every owner-run launcher that backgrounds a `claude --bg` run needs the same ~25-line
#   tail: create the log dir, name a timestamped log file, `nohup`-detach `watch_agent.py`,
#   print the same two report lines, and — with --keep-awake — hold the machine awake for
#   as long as that watcher lives. Eleven launchers hand-copied that block when this file
#   was written — a duplication recorded in the launchers project's own trail — and a fix to
#   it (the two-condition `else` bug below) has already had to be applied once with nowhere
#   to apply it a second time. This file gives the block one home. It is
#   **sourced**, never run directly — a launcher `source`s it and calls `detach_completion_watcher`.
#   `capture_agent_id` is the second function it exposes, for the two callers that need the id
#   before the detach call is reached; every other caller uses `--launch-output` and never names
#   it.
#
#   Fifteen callers are wired onto this home, measured 2026-08-22 with
#   `grep -rln 'detach_watcher.sh' core/launchers/*/launcher.sh core/tools/launch-*.sh`:
#   `experience-visual`, `experience-voice`, `kensaiapp-writing-bar`, `product-content`,
#   `product-design`, `project-agari` (here since 2026-08-03), and the nine the fleet-wide
#   migration brought over — `ad-hoc-flow`, `launch-eval-fix`, `launch-product-prd`,
#   `launch-skill-evals`, `product-srs`, `product-uxd`, `ratify`, and the two flat scripts
#   `core/tools/launch-apply-packet.sh` and `core/tools/launch-fix-author.sh`. None of the
#   fifteen carries a `caffeinate` of its own, so each inherits this file's keep-awake
#   outright — which is why a fix here reaches all of them without one being edited
#   (`core/tools/test_detach_watcher.py` proves that rather than asserting it, and
#   `core/tools/test_keep_awake_binding.py` proves from disk that no copy is left).
#
#   `core/launchers/cold-read/launcher.sh` is the sixteenth, and the only one that does not
#   pass `--keep-awake`: it binds ONE keep-awake across N watchers, so it calls this function
#   once per reader for the spawn, the log and the report, collects the identity pair each
#   call publishes, and runs its own poller over the set. That is the whole of what a fan-out
#   caller keeps. No `.sh` in the repo carries a copy of the block any more, and
#   `test_keep_awake_binding.py` exempts nothing.
#
#   Sourcing this file still has no side effect on its own (see the last behaviour below).
#
# THE CONTRACT
#   detach_completion_watcher \
#     --watcher "<resolved watcher path>" --notifier "<resolved notifier path>" \
#     --instance-root "<instance root>" --prompt "<the launched agent's fixed prompt>" \
#     --label "<human label>" --log-stem "<log filename stem>" --reporter "<reporter name>" \
#     --exclude-ids "<comma-separated ids captured before launch>" \
#     [--artifact-path "<path the reporter reads>" | --product-path "<same, older spelling>"] \
#     [--head-repo "<repo whose HEAD advancing means the run committed>"] \
#     [--agent-id "<the id `claude --bg` printed at launch>"] \
#     [--launch-output "<the launch's own stdout, for this file to read the id out of>"] \
#     [--multi-turn] \
#     [--done-when-exists "<path the run creates when it is finished>"] \
#     [--noun "<what stops — default 'run'>"] \
#     [--keepawake-poll-seconds "<seconds>"] \
#     [--keep-awake]
#
#   Every value but one is a flag the caller (a launcher) has already resolved — this
#   library reads no other caller configuration from the environment and no doctrine of
#   its own, so a launcher's own `LAUNCH_<X>_WATCHER` / `LAUNCH_<X>_NOTIFIER` naming stays
#   exactly where it is today. The one exception is `DETACH_WATCHER_ON_COMPLETE` (below),
#   read directly because no launcher is edited to relay it.
#
#   A second environment variable it reads is NOT caller configuration:
#   `DETACH_WATCHER_KEEPAWAKE_POLL_SECONDS` (default 5) is how often the keep-awake poller
#   re-checks the watcher's identity — an internal knob a test overrides to poll faster than
#   a real run needs, not a documented flag.
#
#   --keepawake-poll-seconds is that same interval as a flag, and it exists for exactly one
#   reason: each launcher that hand-copied this block and documents the knob does so in its
#   OWN `LAUNCH_<X>_KEEPAWAKE_POLL_SECONDS` header line, and two suites set it by that name
#   (`core/launchers/ad-hoc-flow/test_ad_hoc_flow.py` until 2026-09-18, and `product-srs`'s until 2026-09-17).
#   Renaming every one of those documented interfaces to unify one internal knob would have made the
#   migration a rewrite; passing the caller's already-resolved value in keeps it a refactor.
#   A caller that passes nothing gets the environment default above, unchanged — which is
#   why the six callers that predate the flag needed no edit for it.
#
#   Required: --watcher --notifier --instance-root --prompt --label --log-stem --reporter
#   --exclude-ids. A call missing one dies naming which — a bug in the calling launcher, not
#   a runtime condition, so it fails loudly rather than degrading. `--exclude-ids ""` is a
#   legal *value* (no agents existed before this launch, the common first-run case) and is
#   never confused with the flag having been omitted: the parser tracks which flags were
#   actually seen, not whether their values are non-empty.
#
#   --artifact-path and --product-path are aliases for the one thing the watcher reads
#   (`watch_agent.py`'s `parse_args` declares both, on the same `--artifact-path`/`--product-path`
#   line, for the same dest — cited by flag name, not by line: a line number here has drifted
#   twice already) — pass whichever spelling the caller already uses and it reaches the watcher
#   under that same spelling, verbatim. They are mutually exclusive: giving both dies naming the
#   conflict.
#
#   --head-repo is pure pass-through to the watcher (`watch_agent.py`'s `parse_args` declares
#   it, same reason for citing the flag rather than a line); this library resolves nothing
#   about it and does not default it when omitted.
#
#   --agent-id is pure pass-through too, and it is the one flag here that changes which run the
#   watcher believes it is watching. `watch_agent.py:155` calls it "the exact handle: given this,
#   the name is not consulted at all. Preferred over --name" — so a caller that captured the id
#   `claude --bg` printed at launch hands it in and the watcher stops guessing. A caller that
#   could not capture one passes nothing (or an empty value, which is the same thing here) and
#   gets today's behaviour: --name, then the --cwd + --exclude-ids candidate set. The flag is
#   appended to the watcher's argv ONLY when non-empty — an empty `--agent-id ""` on that line
#   would read as a falsy id inside the watcher and take the caller off the fallback entirely,
#   which is why the emptiness test is here and not left to each launcher.
#
#   --launch-output is the same thing for a caller that would rather not hold a parse. Give it
#   the launch's own stdout and this file reads the id out of it with `capture_agent_id` (below,
#   and public — the two launchers that need the id for something besides the watch call it
#   directly). The two flags do not compete: an explicit --agent-id is a value the CALLER decided
#   on, so it wins and no parse is run. Output with no `backgrounded` line in it yields nothing,
#   which is the ordinary "could not capture one" case and reaches the same fallback as passing
#   neither flag.
#
#   --name is still sent alongside it. The watcher ignores the name once it has an id
#   (`watch_agent.py:268-271`), so keeping both makes an id-passing caller's argv a superset of
#   what it sends today rather than a rewrite, and nothing downstream has to branch.
#
#   --multi-turn and --done-when-exists are pure pass-through too, for a caller whose run ends
#   its turn many times on purpose (`watch_agent.py --multi-turn`). --multi-turn is appended
#   only when set, exactly like --keep-awake; --done-when-exists is appended only when
#   non-empty, exactly like --agent-id, for the same reason — an empty value on that line would
#   read as a falsy path inside the watcher. **This library does not re-implement the watcher's
#   own rule that --multi-turn requires --done-when-exists** — both are passed through as given,
#   and `watch_agent.py` is what refuses the combination and where that refusal lands in the
#   log, so a later reader does not add a second copy of the check here.
#
#   --noun names what the caller reports stopping — "run" by default, so the seven callers
#   that already say "run" (and the two already-migrated callers) pass nothing. It is
#   interpolated only into the two lines that name it ("Notifying: when the <noun> stops"
#   and "Keep-awake: … held until the <noun> stops"); the else branch's messages never
#   name a noun and --noun does not add one there.
#
#   `DETACH_WATCHER_ON_COMPLETE` reaches `watch_agent.py --on-complete` with NO flag of its
#   own on this function's contract: the owner's design is that no launcher is edited to
#   relay it, so a caller exports the variable before invoking a launcher and this library
#   reads it straight off the environment, the same way it already reads
#   `DETACH_WATCHER_KEEPAWAKE_POLL_SECONDS` above, and appends it only when non-empty for
#   the same reason as --agent-id and its siblings. Unset, the watcher's argv is
#   byte-identical to today's.
#
#   --artifact-path (or --product-path), --head-repo, --agent-id, --launch-output,
#   --multi-turn, --done-when-exists, --noun, --keepawake-poll-seconds and --keep-awake are
#   optional. `DETACH_WATCHER_ON_COMPLETE` is optional too, read from the environment
#   rather than passed.
#
# WHAT THIS FUNCTION RETURNS
#   `DETACH_WATCHER_PID` and `DETACH_WATCHER_START` — two caller-visible (non-local)
#   variables, both set on every call that passes the required-flag guard: on the happy path
#   the backgrounded watcher's pid and the start time it had at that moment, and on the else
#   branch both empty. They are one value in two parts and must be read as a pair. The pid
#   alone is not a handle — the kernel reissues pid numbers, which is the whole reason this
#   library's own release keys on the pair — so publishing the pid without the start time
#   would hand a fan-out caller a half-identity it could only complete by running `ps` after
#   the fact, inside exactly the window the pairing closes.
#
#   A fan-out caller invokes this function once per reader and reads both after each call:
#   the per-reader spawn, log naming and reporting still live here; only the "there are N of
#   them" shape — the array of pairs and the one poller over it — is the caller's own.
#   `core/launchers/cold-read/launcher.sh` is that caller, and it passes no `--keep-awake`,
#   because the hold it wants spans the set rather than any one member of it.
#
# THE TWO BRANCHES
#   `[ -x notifier ] && [ -f watcher ]` → the happy path: detach the watcher, log both
#   streams, print the two report lines every sibling block prints today, and (with
#   --keep-awake) start one detached `caffeinate -i -s` plus the poller that releases it
#   when the watcher's identity — its pid AND the start time it had when spawned here —
#   stops matching. `caffeinate -w` is deliberately not used: it waits on a pid number,
#   which the kernel reissues, and the hold then rides an unrelated process.
#
#   Else → the fix, carried from the start rather than bolted on later: check
#   `[ -f watcher ]` and `[ -x notifier ]` INDEPENDENTLY, and name whichever half is
#   actually missing — never assume the notifier when the watcher is the missing one. Both
#   report if both are missing.
#
#   Neither branch ever `die`s or returns non-zero: a missing notifier or watcher is
#   ordinary configuration, and this function's whole reason to exist is that notification
#   must never fail the caller's primary launch. The one exception is the missing-required-
#   flag case above, which is a caller bug, not a runtime condition.
#

capture_agent_id() {
  # The one parse of `claude --bg`'s own launch line, for the whole fleet. Takes the launch
  # output as its single argument and echoes the id, or nothing.
  #
  # `claude --bg` prints `backgrounded · <id>`, ANSI-wrapped even when stdout is not a TTY —
  # which is why the escapes come off before the line is read at all: without the strip, the
  # trailing reset sequence rides along on the last field and the id never matches the agent
  # list. This is `launch-skill-evals`' parse, which was the fleet's only copy and had been
  # proven in production for weeks before it moved here.
  #
  # Nothing found is a supported answer, not an error. A launcher whose capture comes back
  # empty passes nothing on and its watcher runs the fallback chain, exactly as every launcher
  # does today.
  # The id is whatever follows `backgrounded · `, taken by ANCHORING ON THAT TEXT rather than on
  # a field index. Two things move the index and neither is under this file's control: the line
  # may carry Claude Code's tree glyph (`  \u23bf  backgrounded \u00b7 <id>`), and a launcher passing
  # `-n` appends the session NAME (`backgrounded \u00b7 <id> \u00b7 <name>`).
  #
  # `$NF` used to work because neither shape existed. The first `-n` launch put the name last, so
  # the parse returned a name, the watcher polled for an agent id that never existed, and it quit
  # at its appear deadline saying the run may not have started — while the run was healthy and
  # merely unwatched. Measured 2026-08-26 on `product-sdd`. `$3` is no better: the glyph shifts it
  # onto the separator, which the suite catches.
  printf '%s\n' "${1:-}" \
    | sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' \
    | sed -n 's/.*backgrounded \xc2\xb7 \([^ ]*\).*/\1/p' | tail -1
}

detach_identity_keep_awake() {
  local watched_pid="$1"
  local watched_start="$2"
  local noun="${3:-run}"
  local poll_seconds="${4:-${DETACH_WATCHER_KEEPAWAKE_POLL_SECONDS:-5}}"

  if command -v caffeinate >/dev/null 2>&1; then
    # A bare pid NUMBER is not a handle on a process. Once the watched process exits and the
    # kernel reissues that number, `caffeinate -w <pid>` holds until whatever unrelated
    # process now answers to it exits too. Pair the pid with the start time it had when the
    # caller spawned it, and keep caffeinate open only while a live process answers to both.
    local keepawake_pid
    nohup caffeinate -i -s >/dev/null 2>&1 &
    keepawake_pid=$!
    nohup bash -c '
      watched_pid="$1"; watched_start="$2"; keepawake_pid="$3"; poll_seconds="$4"
      while :; do
        current="$(ps -o lstart= -p "$watched_pid" 2>/dev/null || true)"
        [ -n "$current" ] && [ "$current" = "$watched_start" ] || break
        sleep "$poll_seconds"
      done
      kill "$keepawake_pid" 2>/dev/null
    ' bash "$watched_pid" "$watched_start" "$keepawake_pid" "$poll_seconds" \
      >/dev/null 2>&1 &
    echo "          Keep-awake:   caffeinate -i -s held until the $noun stops"
  else
    echo "          (keep-awake: caffeinate not found — not macOS? — skipped)"
  fi
}

detach_watch_log_file() {
  # The one name a completion watcher's log takes, for both detach homes:
  # `<instance>/system/logs/watch-<stem>-<UTC YYYYMMDD-HHMMSS>.log`. `chain_usage.py` reads a run's
  # side of the cycle and its order off exactly this name (`_NAME_STAMP`), so a second spelling
  # of it would be a run that reader never finds. Echoes the path, having made its directory.
  local instance_root="$1" log_stem="$2"
  mkdir -p "$instance_root/system/logs"
  printf '%s\n' "$instance_root/system/logs/watch-${log_stem}-$(date -u +%Y%m%d-%H%M%S).log"
}

detach_completion_watcher() {
  local watcher="" notifier="" instance_root="" prompt="" label="" log_stem="" reporter=""
  local exclude_ids="" artifact_path="" product_path="" head_repo="" noun="run" keep_awake=""
  local document_stem=""
  local poll_seconds="" agent_id="" launch_output="" multi_turn="" done_when_exists=""
  # Space-delimited record of which required flags were actually passed — distinct from
  # whether their values are non-empty, so a legal `--exclude-ids ""` is never mistaken for
  # the flag never having been given at all.
  local given=""

  while [ $# -gt 0 ]; do
    case "$1" in
      --watcher)        watcher="$2";       given="$given --watcher";       shift 2 ;;
      --notifier)       notifier="$2";      given="$given --notifier";      shift 2 ;;
      --instance-root)  instance_root="$2"; given="$given --instance-root"; shift 2 ;;
      --prompt)         prompt="$2";        given="$given --prompt";        shift 2 ;;
      --label)          label="$2";         given="$given --label";        shift 2 ;;
      --log-stem)       log_stem="$2";      given="$given --log-stem";     shift 2 ;;
      --reporter)       reporter="$2";      given="$given --reporter";     shift 2 ;;
      --exclude-ids)    exclude_ids="$2";   given="$given --exclude-ids";  shift 2 ;;
      --artifact-path)  artifact_path="$2"; shift 2 ;;
      --document-stem)  document_stem="$2"; shift 2 ;;
      --product-path)   product_path="$2";  shift 2 ;;
      --head-repo)      head_repo="$2";     shift 2 ;;
      --agent-id)       agent_id="$2";      shift 2 ;;
      --launch-output)  launch_output="$2"; shift 2 ;;
      --multi-turn)     multi_turn=1; shift ;;
      --done-when-exists) done_when_exists="$2"; shift 2 ;;
      --noun)           noun="$2";          shift 2 ;;
      --keepawake-poll-seconds) poll_seconds="$2"; shift 2 ;;
      --keep-awake)     keep_awake=1; shift ;;
      *)
        echo "detach_completion_watcher: unrecognized argument: $1" >&2
        return 1
        ;;
    esac
  done

  local flag
  for flag in --watcher --notifier --instance-root --prompt --label --log-stem --reporter --exclude-ids; do
    case " $given " in
      *" $flag "*) ;;
      *)
        echo "detach_completion_watcher: missing required $flag" >&2
        return 1
        ;;
    esac
  done

  if [ -n "$artifact_path" ] && [ -n "$product_path" ]; then
    echo "detach_completion_watcher: --artifact-path and --product-path are mutually exclusive" >&2
    return 1
  fi

  # The caller's own --agent-id is authoritative: it is a value that caller decided on, not one
  # inferred here. Only when it gave none is the raw launch output parsed.
  if [ -z "$agent_id" ] && [ -n "$launch_output" ]; then
    agent_id="$(capture_agent_id "$launch_output")"
  fi

  if [ -x "$notifier" ] && [ -f "$watcher" ]; then
    local log_file
    log_file="$(detach_watch_log_file "$instance_root" "$log_stem")"

    local -a watcher_args=(
      --name "$prompt"
      --label "$label"
      --cwd "$instance_root"
      --reporter "$reporter"
    )
    # Appended only when non-empty, and that is the whole of what sixteen unedited callers
    # rest on: an unconditional append would hand the watcher `--agent-id ""`, which reads as
    # a falsy id there and would silently take every caller off the fallback chain.
    [ -n "$agent_id" ]      && watcher_args+=( --agent-id "$agent_id" )
    [ -n "$artifact_path" ] && watcher_args+=( --artifact-path "$artifact_path" )
    [ -n "$document_stem" ] && watcher_args+=( --document-stem "$document_stem" )
    [ -n "$product_path" ]  && watcher_args+=( --product-path "$product_path" )
    [ -n "$head_repo" ]     && watcher_args+=( --head-repo "$head_repo" )
    [ -n "$multi_turn" ]    && watcher_args+=( --multi-turn )
    [ -n "$done_when_exists" ] && watcher_args+=( --done-when-exists "$done_when_exists" )
    # No flag on this contract carries this one: no launcher is edited to relay it, so
    # the caller exports it before invoking a launcher and this library reads it straight
    # off the environment, appended only when non-empty for the same reason as the flags
    # above it.
    [ -n "${DETACH_WATCHER_ON_COMPLETE:-}" ] && \
      watcher_args+=( --on-complete "$DETACH_WATCHER_ON_COMPLETE" )
    watcher_args+=( --exclude-ids "$exclude_ids" --notify "$notifier" )

    nohup python3 "$watcher" "${watcher_args[@]}" >>"$log_file" 2>&1 &
    local watcher_pid=$!
    DETACH_WATCHER_PID="$watcher_pid"
    # The other half of the identity, captured here rather than inside the --keep-awake branch
    # below: a fan-out caller collects it on calls that pass no --keep-awake at all, and it is
    # the half nobody else can safely re-derive. Every moment between the spawn and this read is
    # a moment the pid could already have been reissued, so it is taken as early as the pid is
    # knowable, and the keep-awake below reuses this value rather than reading `ps` a second time.
    local keepawake_start
    keepawake_start="$(ps -o lstart= -p "$watcher_pid" 2>/dev/null || true)"
    DETACH_WATCHER_START="$keepawake_start"
    echo "          Notifying:    when the $noun stops → $(basename "$notifier")"
    echo "          Watcher log:  $log_file"

    if [ -n "$keep_awake" ]; then
      detach_identity_keep_awake "$watcher_pid" "$keepawake_start" "$noun" "$poll_seconds"
    fi
  else
    DETACH_WATCHER_PID=""
    DETACH_WATCHER_START=""
    # Independent checks, independent messages — the fix, from the start. An absent
    # notifier is ordinary configuration (KENSAIAPP_NOTIFIER unset); an absent watcher
    # means the caller could not resolve its own path to shared machinery — a bug in the
    # launcher, not the environment. Conflating them sends the reader to the wrong end.
    [ -f "$watcher" ]  || echo "          (no watcher at $watcher — completion watch skipped)"
    [ -x "$notifier" ] || echo "          (no notifier at $notifier — completion watch skipped)"
    if [ -n "$keep_awake" ]; then
      echo "          (keep-awake needs a completion watcher — set KENSAIAPP_NOTIFIER — not staying awake)"
    fi
  fi

  return 0
}
