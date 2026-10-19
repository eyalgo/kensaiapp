#!/usr/bin/env bash
#
# instrument_run.sh — the one home for tagging a `claude` run with the telemetry environment.
#
# Version: 1.9.0 — public-repo 0.x gates 1, 3, 4, 6 — Apache-2.0 licence lines, no satellite/product/host name or machine path shipped, no default notifier, loopback-only telemetry
# Version: 1.8.0 — runs record provider, model, effort and source, and run_provenance.py finds them by run ID
# Version: 1.7.0 — a developer past the context cap pauses at a task boundary, and the chain relaunches a fresh one at the next task — --context-cap on chain-change and build-idea, default 250000
# Version: 1.6.0 — chain-development telemetry carries the responsible role on every run and the audited step on every audit run
# Version: 1.5.0 — a launcher-started record says which instance, product and operation it was for — instrument_run stamps them, chain.py ties a walk, and the step-name seed is parked by the owner's ruling
# Version: 1.4.0 — a run started inside a session lands on the stream — apply_telemetry_env.py writes the telemetry entry once per machine, and the suites run inside a guard that prints no secret
# Version: 1.3.0 — the backgrounded launchers are tagged too — every launcher hands its telemetry to the spawn as --settings; station 2 closes and the seed is set down
# Version: 1.2.0 — no console exporter is added, and this header records why (Task 6). The seed
#   proposed console alongside OTLP so a dead receiver could not lose an arm silently, but every
#   real caller here is a BACKGROUNDED `claude --bg` run, and a detached run's console export was
#   measured, not assumed, to answer that question.
#
#   THE PROBE, 2026-09-09. Same environment, two shapes:
#     - `claude -p "Reply with the single word: ok" --model haiku` (foreground), under
#       `OTEL_LOGS_EXPORTER=console,otlp` and the real receiver up: the console text appeared in
#       the invoking shell's own captured stdout (84 `claude_code.*` lines), and the OTLP POST
#       reached the receiver (a fresh `logs.jsonl` record, `session.id` matching the run).
#     - `claude --bg "Reply with the single word: ok" --model haiku`, identical exporters, output
#       redirected to a file exactly as every launcher here does it: the file held only the
#       `backgrounded · <id>` banner, unchanged in size (256 bytes) from the moment of launch
#       through `state: "done"` and an explicit `claude stop`. `claude logs <id>` shows the
#       session ran and answered — its transcript is a separate, PTY-managed capture the shell's
#       own redirected fd never sees. **No OTLP record reached the receiver either** — the
#       backgrounded session's exporter never fired inside the observed window, `claude stop`
#       included. Whatever a `--bg` session's own environment resolves to at export time, it is
#       not observable through the invoking shell's redirect, for either exporter shape.
#
#   THE ANSWER: no console exporter is exported at all, because there is nowhere a `--bg`
#   caller's redirect can read it back from. `check_no_export_value_contains_console` in
#   `test_instrument_run.py` asserts this on the actual exported variable VALUES, not by grepping
#   this file for the word.
#
#   THE OTLP HALF, put in words rather than silently accepted: this same probe puts the whole
#   station's live-round-trip claim (Task 1–5) partly open for a REAL `--bg` run specifically —
#   verified in the foreground shape and by the receiver's own test suite, not yet by a
#   `--bg` round trip landing a record with `state: "done"` observed first. Recorded here rather
#   than quietly worked around; `agent-usage-reads-a-run` is where a reader over the stream
#   would surface a gap this station's own scope does not reach further into.
# Version: 1.1.0 — kensai.arm and kensai.run_id are attached to the base export via
#   OTEL_RESOURCE_ATTRIBUTES: the arm from INSTRUMENT_RUN_ARM or, unset, derived from the
#   calling launcher's own directory; a whitespace-containing arm is refused rather than
#   exported, leaving the base OTLP export untouched.
# Version: 1.0.0
#
# WHY THIS EXISTS
#   Twenty-one launchers under `core/launchers/` spawn `claude`, and nothing reaches the OTLP
#   receiver (`core/tools/otel_receiver.py`) unless a person types five `OTEL_*` variables onto
#   the command line by hand — station 1's own "a real run lands" bar was exactly that
#   invocation. This file gives every launcher the same call, the way `detach_watcher.sh` gives
#   every launcher the same completion-watch tail: one function, sourced and called once before
#   the spawn, and a change here reaches all twenty-one without any of them carrying a copy.
#
#   This is **sourced**, never run directly — a launcher `source`s it and calls `instrument_run`.
#   It is unconditional, not behind a flag: the owner had already answered the question the seed
#   left open — "it wouldn't matter if we run a launcher or an agent, we'll have the
#   information." A per-run flag measures only the runs someone remembered to mark.
#
#   Sourcing this file has no side effect on its own — no function call, no output, no export —
#   the same contract `detach_watcher.sh` states for the same reason.
#
# THE CONTRACT
#   instrument_run [key=value ...]
#
#   No required arguments. A launcher sources this file and calls the function with nothing —
#   the caller sets no argument and exports no variable, and the run still arrives tagged. A
#   launcher that already holds its own subject hands it over as `key=value` pairs — see
#   *The subject* below.
#
#   **The published endpoint.** The switch is the deployment, not the caller: this file names no
#   port. It reads whatever `core/tools/otel_receiver.py --publish-endpoint` wrote, at
#   `$HOME/.claude/tools/otel-receiver/endpoint` — resolved in exactly this one place, as a plain
#   default a caller may override only through `INSTRUMENT_RUN_ENDPOINT_FILE`, an internal knob a
#   test overrides (the same shape as `DETACH_WATCHER_KEEPAWAKE_POLL_SECONDS`), never a documented
#   launcher flag. Absent, unreadable, not shaped like an `http://` / `https://` endpoint, or naming
#   a host other than loopback (`localhost`, `127.x.x.x`, `[::1]`) are all the same case: nothing
#   is exported, the call still returns 0, and one line says the run is uninstrumented.
#   `core/doctrine/setup/kensaiapp_structure.md` § *No tool may require machine state to exist*
#   is the whole of the reasoning for the absent case — a machine with no receiver installed exports
#   nothing rather than POSTing at a closed port.
#
#   **The arm.** `INSTRUMENT_RUN_ARM`, when set, wins outright. Unset, the arm is **derived**
#   from the calling launcher's own directory — the caller's own `$SCRIPT_DIR`, which every
#   launcher resolves absolutely from its own `${BASH_SOURCE[0]}` before it cd's to the instance
#   root, never a literal a launcher passes — so a launcher copied from a sibling cannot inherit
#   its parent's arm. A caller with no absolute `$SCRIPT_DIR` falls back to resolving
#   `${BASH_SOURCE[1]}`, the file that called into this function. Whichever way it was resolved,
#   a value that `OTEL_RESOURCE_ATTRIBUTES` cannot carry — whitespace — or that names no
#   directory at all — empty, `.`, `..`, `/` — is refused rather than exported: the base
#   telemetry export above still happens (the endpoint answered), but no `kensai.arm` /
#   `kensai.run_id` pair is attached to it — a bad arm must not untag the whole run, and a run
#   tagged `kensai.arm=.` is worse than one left untagged, because the stream cannot tell it
#   from a real value.
#
#   **The run id.** A fresh `uuid4` per call — `python3` is standing infrastructure across this
#   fleet already, so no new dependency is added by reaching for it here.
#
#   **The instance.** Derived, never passed: the basename of the parent of the absolute git
#   common dir (`git rev-parse --path-format=absolute --git-common-dir`), read from wherever
#   this call's caller already `cd`'d to. A worktree's common dir is its main checkout's `.git`,
#   so a worktree names the same instance as the checkout it was cut from. Outside any git
#   repository, `kensai.instance` is simply not attached — the rest of the export is unaffected.
#   A name `OTEL_RESOURCE_ATTRIBUTES` cannot carry (the same set *The subject* lists below) is
#   refused for that key alone, named on one line.
#
#   **The subject.** Each `key=value` argument is stamped `kensai.<key>`, and only eight keys are
#   accepted: `project`, `document`, `skill`, `target_instance`, and the run's provenance —
#   `provider`, `model`, `effort`, `source` (the provider the run goes through, the model and
#   effort it goes at, and whether those came from the skill's intelligence file, a tier the
#   caller named, or neither) — so a stamped run carries `kensai.provider`, `kensai.model`,
#   `kensai.effort` and `kensai.source`, the four names `core/tools/run_provenance.py` reads back
#   by run ID. A key's pair follows the ones before it in the call's own argument
#   order. The caller resolves each value itself — this file reads no intelligence file and
#   resolves no tier. An unrecognised key is refused
#   with one line naming it; the call still returns 0 and every other key still goes out. An
#   empty value attaches nothing for that key. A value `OTEL_RESOURCE_ATTRIBUTES` cannot carry —
#   whitespace, a double quote, a comma, a semicolon, a backslash or an `=` — drops that key
#   alone, named on one line, and nothing else this call would have attached. `project=<p>`
#   additionally reads `system/projects/<p>/project.md` under the working directory: when its
#   `**Product path:**` line names a path, this attaches `kensai.product=<basename of that
#   path>`, read up to the first whitespace so a trailing HTML comment is never part of it.
#   Absent either the card or the line, no `kensai.product` is attached.
#
#   **The chain walk.** `INSTRUMENT_RUN_WALK_ID` and `INSTRUMENT_RUN_CHAIN` — never a documented
#   launcher flag — are two environment variables `core/tools/chain.py` sets before it launches a
#   document, so every launch in one walk ties together. Each becomes `kensai.walk_id` /
#   `kensai.chain` when it is set and carries a value this file can export; unset or unexportable,
#   neither is stamped, and the rest of the export is unaffected.
#
#   **The direct identity.** `INSTRUMENT_RUN_ROLE` and `INSTRUMENT_RUN_AUDIT_TARGET` — never a
#   documented launcher flag — are two environment variables `core/tools/chain_development.py` sets
#   before it launches a step: every launch's responsible agent role, and, on an audit fan-out
#   launch only, the producer step that audit run covers. Each becomes `kensai.role` /
#   `kensai.audit_target` when it is set and carries a value this file can export; unset or
#   unexportable, neither is stamped, and the rest of the export is unaffected. Same shape as the
#   chain walk above, and independently refused the same way.
#
#   Every key this function attaches carries the `kensai.` prefix, which the vendor guarantees
#   cannot collide with a built-in resource attribute.
#
# WHAT THIS FUNCTION EXPORTS ON THE HAPPY PATH
#   CLAUDE_CODE_ENABLE_TELEMETRY=1
#   OTEL_METRICS_EXPORTER=otlp
#   OTEL_LOGS_EXPORTER=otlp
#   OTEL_EXPORTER_OTLP_PROTOCOL=http/json
#   OTEL_EXPORTER_OTLP_ENDPOINT=<the published endpoint>
#   OTEL_RESOURCE_ATTRIBUTES=kensai.arm=<arm>,kensai.run_id=<uuid4>[,kensai.instance=<instance>]
#     [,kensai.<key>=<value> ...][,kensai.product=<product>][,kensai.walk_id=<id>][,kensai.chain=<name>]
#     — <key> one of project, document, skill, target_instance, provider, model, effort, source,
#     in the call's own argument order, kensai.product right after the kensai.project it is
#     read from
#     [,kensai.role=<role>][,kensai.audit_target=<producer>]
#
#   Every export is a real `export`, so the process this function's caller spawns next inherits
#   all of them — the whole reason this is a shell library and not a Python helper a launcher
#   would have to capture output from.
#
# WHAT THIS FUNCTION NEVER DOES
#   It never fails its caller: every branch returns 0. A missing receiver, a malformed publish
#   file, or an invalid arm are all ordinary configuration, exactly the same split
#   `detach_watcher.sh` draws for its own optional pieces — notification must never fail a
#   launcher's primary run, and neither may this.
#

# One variable set, two consumers.
#
# Four of the five base telemetry keys never vary; only OTEL_EXPORTER_OTLP_ENDPOINT depends on
# the resolved endpoint. This array is the one place the four static pairs are written —
# instrument_run's own exports below and instrument_run_user_entry (the standalone consumer a
# settings-merge command reaches for) both build off it, so the two can never independently
# drift. `_instrument_run_settings` keeps its own key tuple below: it reads values already
# exported into THIS process's environment, which is a different question from "what are the
# five keys" — the parity `TestUserEntryLibrary`'s own test holds is between the two key SETS,
# not between the two ways of reading a value.
_INSTRUMENT_RUN_BASE_ENV_STATIC=(
  "CLAUDE_CODE_ENABLE_TELEMETRY=1"
  "OTEL_METRICS_EXPORTER=otlp"
  "OTEL_LOGS_EXPORTER=otlp"
  "OTEL_EXPORTER_OTLP_PROTOCOL=http/json"
)

# Resolves and validates the published endpoint — the one place either resolution happens.
# instrument_run and instrument_run_user_entry both call this, so the default path
# (`test_the_default_path_is_resolved_in_one_place_and_the_suite_never_touches_it` counts its one
# literal occurrence) and the http(s) validation rule live in exactly one function. Echoes the
# endpoint and returns 0 when valid; returns 1 with the human-readable reason on stderr and
# nothing on stdout otherwise — the caller decides how to report that, since instrument_run's own
# "(… — run uninstrumented)" phrasing is not what the standalone consumer wants to say.
_instrument_run_resolve_endpoint() {
  local endpoint_file="${INSTRUMENT_RUN_ENDPOINT_FILE:-$HOME/.claude/tools/otel-receiver/endpoint}"

  if [ ! -r "$endpoint_file" ]; then
    echo "no published telemetry endpoint at $endpoint_file" >&2
    return 1
  fi

  # `|| true` above the assignment: under a caller's `set -o pipefail`, `cat` failing on a
  # directory (or any other unreadable shape `[ -r ]` did not catch) would otherwise end the
  # caller's script right here instead of falling through to the malformed-endpoint case below.
  local endpoint
  endpoint="$( { cat "$endpoint_file" 2>/dev/null || true; } | head -n1 | tr -d '[:space:]')"

  case "$endpoint" in
    http://*|https://*) ;;
    *)
      echo "telemetry endpoint at $endpoint_file is unreadable or malformed" >&2
      return 1
      ;;
  esac

  # Telemetry stays on this machine: only a loopback host is exported to. A published endpoint
  # naming any other host — a typo, or a file someone else wrote — is refused like a malformed
  # one, so a run's telemetry never leaves the machine by way of this file.
  local authority="${endpoint#*://}"
  authority="${authority%%/*}"
  local loopback='^(localhost|127\.[0-9]+\.[0-9]+\.[0-9]+|\[::1\])(:[0-9]+)?$'
  if [[ ! "$authority" =~ $loopback ]]; then
    echo "telemetry endpoint at $endpoint_file is not on this machine (loopback only)" >&2
    return 1
  fi
  printf '%s' "$endpoint"
}

# Builds the base entry (the four static pairs plus the resolved endpoint) as JSON — the shape
# both instrument_run_user_entry and, by construction, a settings-merge command need. $1 is a
# validated endpoint; this never re-validates it.
_instrument_run_base_env_json() {
  python3 -c 'import json, sys
pairs = sys.argv[1:-1]
endpoint = sys.argv[-1]
env = dict(p.split("=", 1) for p in pairs)
env["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint
print(json.dumps(env, separators=(",", ":")))' "${_INSTRUMENT_RUN_BASE_ENV_STATIC[@]}" "$1"
}

# The standalone consumer: no live session, nothing already exported — just a validated
# endpoint. Called by the settings-merge command (`apply_telemetry_env.py`) through a small
# "source this file, call this function" wrapper, the same shape this file's own test suite
# uses. Prints the base entry as JSON and returns 0; prints nothing and returns 0 when there is
# no published endpoint or it is malformed — the same "ordinary configuration never fails the
# caller" contract instrument_run's own base export holds.
instrument_run_user_entry() {
  local endpoint
  endpoint="$(_instrument_run_resolve_endpoint 2>/dev/null)" || return 0
  _instrument_run_base_env_json "$endpoint"
}

# Task 7 — the same variables, as one value a launcher hands its spawn with `--settings`.
# An exported variable never reaches a `claude --bg` session and `--settings '{"env": …}'` does —
# measured 2026-09-10 over three haiku probes against the live receiver. Built from the
# exports themselves, so the two cannot disagree; $1 is the OTEL_RESOURCE_ATTRIBUTES this call
# set, or empty when it attached no arm, so a withheld arm is withheld here too.
#
# KENSAIAPP_CONTEXT_CAP rides along when it is exported and non-empty, and is left out otherwise.
# It is the developer run's context cap, read by `.claude/hooks/context_cap.py`, and it needs this
# same route for the same reason the telemetry does: an exported variable does not reach a
# `claude --bg` session. It is optional where the five telemetry keys are not — the key tuple is
# indexed, so an absent key raises inside the `python3 -c` and the settings would fall back to
# empty, taking the telemetry with them.
_instrument_run_settings() {
  INSTRUMENT_RUN_SETTINGS="$(python3 -c 'import json,os,sys; ks=("CLAUDE_CODE_ENABLE_TELEMETRY","OTEL_METRICS_EXPORTER","OTEL_LOGS_EXPORTER","OTEL_EXPORTER_OTLP_PROTOCOL","OTEL_EXPORTER_OTLP_ENDPOINT"); env={k:os.environ[k] for k in ks}; env.update({k:os.environ[k] for k in ("KENSAIAPP_CONTEXT_CAP",) if os.environ.get(k)}); env.update({"OTEL_RESOURCE_ATTRIBUTES":sys.argv[1]} if sys.argv[1] else {}); print(json.dumps({"env":env},separators=(",",":")))' "$1")" || INSTRUMENT_RUN_SETTINGS=""
  export INSTRUMENT_RUN_SETTINGS
}

# The same settings for a run left uninstrumented: the context cap alone, when it is exported and
# non-empty, and nothing at all otherwise. The cap is not telemetry — the chain's developer run is
# checked against it whether or not a receiver is published — and `--settings` is its only route
# into a `claude --bg` session, so returning early without this would drop it silently.
_instrument_run_cap_settings() {
  [ -n "${KENSAIAPP_CONTEXT_CAP:-}" ] || return 0
  INSTRUMENT_RUN_SETTINGS="$(python3 -c 'import json,os; print(json.dumps({"env":{"KENSAIAPP_CONTEXT_CAP":os.environ["KENSAIAPP_CONTEXT_CAP"]}},separators=(",",":")))')" || return 0
  export INSTRUMENT_RUN_SETTINGS
}

# A value OTEL_RESOURCE_ATTRIBUTES cannot carry — whitespace, a double quote, a comma, a
# semicolon, a backslash or an `=`. Shared by every kensai.<key> a call may attach beyond
# kensai.arm/kensai.run_id, which keep their own narrower, already-shipped check above.
_instrument_run_value_unexportable() {
  case "$1" in
    *[[:space:]]*|*'"'*|*,*|*';'*|*'\'*|*'='*) return 0 ;;
    *) return 1 ;;
  esac
}

# Task 1 — the instance this run executes in, named by the parent directory of the absolute
# git common dir. A worktree's common dir is its main checkout's `.git`, so a worktree yields
# the same name as the checkout it was cut from. Outside any git repository (or with git
# missing), echoes nothing and never fails the caller.
_instrument_run_derive_instance() {
  local common_dir
  common_dir="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || return 0
  [ -n "$common_dir" ] || return 0
  basename "$(dirname "$common_dir")"
}

# Task 2 — the product a project names, read from that project's own card under the working
# directory. $1 is the project slug (not re-validated: a slug bad enough to be refused as
# kensai.project can still name a real card on disk). Echoes the basename of the card's
# `**Product path:**` line, or nothing when the card, the line, or a carriable value is absent.
_instrument_run_derive_product() {
  local project_md="system/projects/$1/project.md"
  [ -r "$project_md" ] || return 0
  local line
  line="$(grep -m1 '^\*\*Product path:\*\*' "$project_md" 2>/dev/null || true)"
  [ -n "$line" ] || return 0
  # Read up to the first whitespace after the label, so a trailing HTML comment on the same
  # line never becomes part of the path — unquoted word-splitting on $rest does exactly that.
  local rest="${line#\*\*Product path:\*\*}"
  local path
  # shellcheck disable=SC2086
  set -- $rest
  path="${1:-}"
  [ -n "$path" ] || return 0
  basename "$path"
}

# The only eight keys `instrument_run`'s key=value arguments accept, space-padded so a `case`
# membership test never matches a substring of a longer key. The first four name the run's subject
# (Task 2 of the station that added them); the last four its provenance — the provider it went
# through, the model and effort it went at, and where those two came from.
_INSTRUMENT_RUN_ACCEPTED_KEYS=" project document skill target_instance provider model effort source "

instrument_run() {
  # A value inherited from whatever started this launcher is not this run's — clear it first.
  unset INSTRUMENT_RUN_SETTINGS

  local endpoint
  if ! endpoint="$(_instrument_run_resolve_endpoint 2>&1)"; then
    echo "          ($endpoint — run uninstrumented)"
    _instrument_run_cap_settings
    return 0
  fi

  local pair
  for pair in "${_INSTRUMENT_RUN_BASE_ENV_STATIC[@]}"; do
    export "$pair"
  done
  export OTEL_EXPORTER_OTLP_ENDPOINT="$endpoint"

  local arm
  if [ -n "${INSTRUMENT_RUN_ARM:-}" ]; then
    arm="$INSTRUMENT_RUN_ARM"
  else
    # Derived from the calling launcher's own DIRECTORY, never a literal any launcher carries
    # — so a launcher copied from a sibling cannot inherit its parent's arm.
    #
    # $SCRIPT_DIR is read first because it is the only answer resolved at the right MOMENT.
    # Every launcher opens with SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" and
    # only then cd's to the instance root, so it holds that launcher's own ABSOLUTE directory,
    # taken before the cd. ${BASH_SOURCE[1]} holds something else: the path the launcher was
    # STARTED with, which is `./launcher.sh` when it was started from inside its own folder —
    # `dirname` yields `.`, `basename .` is `.`, and the run goes out tagged `kensai.arm=.`.
    # Re-resolving that `.` here is no better, because the cd has already happened and it would
    # name the instance root instead. `test_launcher_instrumentation.py` is what holds every
    # launcher to setting SCRIPT_DIR this way, so this is a checked contract, not a hope.
    local caller_dir="${SCRIPT_DIR:-}"
    case "$caller_dir" in
      /*) ;;
      # No absolute $SCRIPT_DIR — some other caller. Resolve its path the way the corpus does,
      # with the `|| true` on the substitution and the real check on the line below.
      *) caller_dir="$( { cd "$(dirname "${BASH_SOURCE[1]:-}")" 2>/dev/null && pwd; } || true )" ;;
    esac
    if [ -n "$caller_dir" ]; then
      arm="$(basename "$caller_dir")"
    else
      arm=""
    fi
  fi

  # Every kensai.<key>=<value> pair this call assembles, in the order each source resolves:
  # arm/run_id first (unchanged from before this station), then instance, then the caller's own
  # subject, then the chain walk. A source that refuses drops only its own pair — never the
  # array — so one bad value never untags what the rest of this call got right.
  local attrs=()

  # Each refusal clears `arm`, so the one attach below is the only place a pair is added.
  case "$arm" in
    ""|.|..|/)
      echo "          (kensai.arm could not be derived from the calling launcher's directory — arm not attached)"
      arm=""
      ;;
    *[[:space:]]*)
      echo "          (kensai.arm '$arm' contains whitespace — OTEL_RESOURCE_ATTRIBUTES cannot carry one; arm not attached)"
      arm=""
      ;;
    *)
      # The same refusal every other value this call attaches gets — a comma here would split
      # the arm into a stray extra key.
      if _instrument_run_value_unexportable "$arm"; then
        echo "          (kensai.arm '$arm' contains a character OTEL_RESOURCE_ATTRIBUTES cannot carry — arm not attached)"
        arm=""
      fi
      ;;
  esac
  if [ -n "$arm" ]; then
    local run_id
    run_id="$(python3 -c 'import uuid; print(uuid.uuid4())')"
    attrs+=("kensai.arm=${arm}" "kensai.run_id=${run_id}")
  fi

  # Task 1 — the instance, derived rather than passed.
  local instance
  instance="$(_instrument_run_derive_instance)"
  if [ -n "$instance" ]; then
    # A checkout directory may carry a space or a comma — refused for this key alone, like any
    # other value this call attaches.
    if _instrument_run_value_unexportable "$instance"; then
      echo "          (kensai.instance '$instance' contains a character OTEL_RESOURCE_ATTRIBUTES cannot carry — not attached)"
    else
      attrs+=("kensai.instance=${instance}")
    fi
  fi

  # Task 2 — the caller's own subject, handed over as key=value arguments.
  local kv key value
  for kv in "$@"; do
    case "$kv" in
      *=*) ;;
      *)
        echo "          (instrument_run: argument '$kv' has no '=' — expected key=value; not attached)"
        continue
        ;;
    esac
    key="${kv%%=*}"
    value="${kv#*=}"
    case "$_INSTRUMENT_RUN_ACCEPTED_KEYS" in
      *" $key "*) ;;
      *)
        echo "          (instrument_run: unknown key '$key' — only project, document, skill, target_instance, provider, model, effort and source are accepted)"
        continue
        ;;
    esac
    [ -n "$value" ] || continue
    if _instrument_run_value_unexportable "$value"; then
      echo "          (kensai.$key '$value' contains a character OTEL_RESOURCE_ATTRIBUTES cannot carry — not attached)"
      continue
    fi
    attrs+=("kensai.$key=$value")
    if [ "$key" = "project" ]; then
      local product
      product="$(_instrument_run_derive_product "$value")"
      if [ -n "$product" ] && ! _instrument_run_value_unexportable "$product"; then
        attrs+=("kensai.product=$product")
      fi
    fi
  done

  # Task 3 — the chain walk this launch belongs to, if any: two environment variables the chain
  # sets before it launches, never a documented launcher flag.
  if [ -n "${INSTRUMENT_RUN_WALK_ID:-}" ] \
    && ! _instrument_run_value_unexportable "$INSTRUMENT_RUN_WALK_ID"; then
    attrs+=("kensai.walk_id=${INSTRUMENT_RUN_WALK_ID}")
  fi
  if [ -n "${INSTRUMENT_RUN_CHAIN:-}" ] \
    && ! _instrument_run_value_unexportable "$INSTRUMENT_RUN_CHAIN"; then
    attrs+=("kensai.chain=${INSTRUMENT_RUN_CHAIN}")
  fi

  # The run's responsible role and, on an audit run, the producer it audits: two environment
  # variables chain_development.py sets before it launches, mirroring the walk/chain shape above.
  # Each becomes kensai.role / kensai.audit_target when set and carries a value this file can
  # export; unset or unexportable, neither is stamped and the rest of the export is unaffected.
  if [ -n "${INSTRUMENT_RUN_ROLE:-}" ] \
    && ! _instrument_run_value_unexportable "$INSTRUMENT_RUN_ROLE"; then
    attrs+=("kensai.role=${INSTRUMENT_RUN_ROLE}")
  fi
  if [ -n "${INSTRUMENT_RUN_AUDIT_TARGET:-}" ] \
    && ! _instrument_run_value_unexportable "$INSTRUMENT_RUN_AUDIT_TARGET"; then
    attrs+=("kensai.audit_target=${INSTRUMENT_RUN_AUDIT_TARGET}")
  fi

  if [ ${#attrs[@]} -gt 0 ]; then
    local joined
    joined="$(IFS=,; echo "${attrs[*]}")"
    export OTEL_RESOURCE_ATTRIBUTES="$joined"
  fi

  _instrument_run_settings "${OTEL_RESOURCE_ATTRIBUTES:-}"
  if [ -n "${OTEL_RESOURCE_ATTRIBUTES:-}" ]; then
    echo "          Telemetry:    ${OTEL_RESOURCE_ATTRIBUTES} → $endpoint"
  else
    echo "          Telemetry:    OTLP → $endpoint"
  fi
  return 0
}
