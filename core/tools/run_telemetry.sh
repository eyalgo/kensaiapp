#!/usr/bin/env bash
#
# run_telemetry.sh — every instrumented launcher's telemetry tagging, over the telemetry package's
# `turn-on`.
#
# Version: 1.1.1 — delete the seven old telemetry files and their seven tests, and move everything that pointed at them
# Version: 1.1.0 — the other six launchers run on the package's turn-on
# Version: 1.0.0 — the skill launcher takes its run's telemetry settings from the package's turn-on instead of instrument_run.sh
#
# WHY THIS EXISTS
#   The package that publishes and receives this machine's telemetry already knows how to write the
#   five `OTEL_*` keys for one run, derive the instance and generate the run id (`turn-on --print`).
#   This file is the thin layer between that command and the launchers that call it. It takes a
#   launcher's `key=value` arguments, derives the arm and the product, prints a line for each value
#   it refuses, and hands the launch six exports and the settings document the launcher passes to
#   its spawn.
#
#   This file is **sourced**, never run directly — a launcher `source`s it and calls
#   `run_telemetry`. Sourcing defines the function and nothing else: no output, no subprocess, no
#   export, and no shell option set (a sourced `set -e` would change the shell that sourced it).
#
# THE CONTRACT
#   run_telemetry [key=value ...]
#
#   **The arguments.** Eight keys are accepted: `project`, `document`, `skill`,
#   `target_instance`, `provider`, `model`, `effort` and `source`. Each `key=value` is stamped
#   `kensai.<key>`, in the caller's own argument order. An empty value attaches nothing for its
#   key, and no line names it. A value `OTEL_RESOURCE_ATTRIBUTES` cannot carry is one holding
#   whitespace, a double quote, a comma, a semicolon, a backslash or an `=`. An argument with no
#   `=`, a key outside the eight, and such a value are each refused with one line naming it, and
#   every other argument still goes out.
#
#   **The product.** `project=<p>` also reads `system/projects/<p>/project.md` under the working
#   directory. When the card's first `**Product path:**` line names a path, that path's basename
#   is stamped `kensai.product`, right after `kensai.project`. A missing card, line or path, or a
#   basename `OTEL_RESOURCE_ATTRIBUTES` cannot carry, attaches no `kensai.product`, and no line
#   names it.
#
#   **The arm.** The arm is `INSTRUMENT_RUN_ARM` when that is set and non-empty. Otherwise it is
#   the basename of the calling launcher's own directory: the launcher's absolute `$SCRIPT_DIR`,
#   or the calling file's directory when the launcher has none. An arm that cannot be derived
#   (empty, `.`, `..` or `/`) or that `OTEL_RESOURCE_ATTRIBUTES` cannot carry is refused with one
#   line, and no `kensai.arm` is attached. The run id is attached all the same.
#
#   **The chain tags.** `INSTRUMENT_RUN_WALK_ID`, `INSTRUMENT_RUN_CHAIN`, `INSTRUMENT_RUN_ROLE`
#   and `INSTRUMENT_RUN_AUDIT_TARGET` are environment variables the chain engines set before a
#   launch, never a launcher flag. They are stamped `kensai.walk_id`, `kensai.chain`,
#   `kensai.role` and `kensai.audit_target`, each when it holds a value
#   `OTEL_RESOURCE_ATTRIBUTES` can carry. An empty or refused one is dropped, and no line names it.
#
#   **What the package adds.** The package generates `kensai.run_id`, a fresh lowercase UUID per
#   call, and derives `kensai.instance` from the caller's working directory. A worktree names the
#   same instance as the checkout it was cut from. Outside a git repository no instance is
#   attached. An instance name `OTEL_RESOURCE_ATTRIBUTES` cannot carry is left off, and no line
#   names it. A `%` in an argument value, the arm, the product or a chain tag is carried as
#   `%000025`, so `model=50%` becomes `kensai.model=50%000025`. An instance name holding `%` is
#   carried as written.
#
#   **The refusal lines** are printed only on an instrumented run, ahead of its one `Telemetry:`
#   line, which names the attributes and the endpoint.
#
#   **The six exports.** An instrumented run exports `CLAUDE_CODE_ENABLE_TELEMETRY`,
#   `OTEL_METRICS_EXPORTER`, `OTEL_LOGS_EXPORTER`, `OTEL_EXPORTER_OTLP_PROTOCOL`,
#   `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_RESOURCE_ATTRIBUTES`, with the package's values and
#   the attributes in the order **Attribute order** states. An uninstrumented run exports none of
#   them.
#
#
#   **The command.** It is one executable, named by a bare name and run from
#   `$HOME/.kensaiapp/venv/bin/` and nowhere else. When the invoking environment holds
#   `KENSAIAPP_TELEMETRY_COMMAND`, its value is the name, even when it is empty. An empty name reads
#   as unconfigured, so setting the variable empty switches telemetry off for one launch. Otherwise
#   the name is what `telemetry_command.py`, beside this file, answers for the core this file sits
#   in, and that tool reads it from the setting on the core's source host. A resolver that is
#   missing or fails answers nothing, and the run goes uninstrumented as unconfigured. Nothing here
#   names a command, searches PATH, evaluates shell text, imports the package or activates a venv.
#   It is invoked once, from the caller's working directory (which is where the package derives the
#   instance):
#     <command> turn-on --print --endpoint-file <file> --prefix kensai --label key=value ...
#   `<file>` is `INSTRUMENT_RUN_ENDPOINT_FILE`, else `$HOME/.claude/tools/otel-receiver/endpoint`.
#
#   **Never fails the caller.** An unconfigured, missing, failing or garbled command, and an
#   endpoint the package declines, each leave the run uninstrumented with one stdout line naming the
#   cause; every branch returns 0. The settings then carry `KENSAIAPP_CONTEXT_CAP` alone when it is
#   exported and non-empty, and nothing otherwise.
#
#   **Settings.** `INSTRUMENT_RUN_SETTINGS` is cleared on entry, so a value inherited from whatever
#   started the caller is never this run's. The settings document and the six exports are built from
#   the same validated package output; the package's text is data and is never evaluated or
#   forwarded, and the package's own `Telemetry:` line is consumed so exactly one is printed.
#
#   **Attribute order.** The package puts the run id and instance ahead of every label. The pairs it
#   returns are reordered, never decoded or re-encoded: arm, run id, instance, then the labels in
#   the caller's order with the product right after its project and the chain/role tags last.
#

# The only eight keys the key=value arguments accept, space-padded so a `case` membership test never
# matches part of a longer key.
_RUN_TELEMETRY_ACCEPTED_KEYS=" project document skill target_instance provider model effort source "

# The bridge to the package. Bash 3.2 cannot hold a JSON document, argv-based subprocess control or
# an ordered pair list, so this crosses to python3 (shell/toolchain.md), with every value as argv
# and no apostrophe anywhere in the source below. It prints one tab-separated protocol line per
# fact, and the shell reads those lines as data:
#   SETTINGS<TAB><compact settings json>
#   EXPORT<TAB><name><TAB><value>          (the six telemetry exports)
#   ENDPOINT<TAB>none|malformed|remote     (the package declined the endpoint)
#   FAIL<TAB>start | status<TAB><n> | unusable
# `cap` mode prints only the context-cap settings, when the cap is exported and non-empty.
_RUN_TELEMETRY_BRIDGE='
import json
import os
import subprocess
import sys

BASE_KEYS = (
    "CLAUDE_CODE_ENABLE_TELEMETRY",
    "OTEL_METRICS_EXPORTER",
    "OTEL_LOGS_EXPORTER",
    "OTEL_EXPORTER_OTLP_PROTOCOL",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
)
ATTRIBUTES_KEY = "OTEL_RESOURCE_ATTRIBUTES"
CAP_KEY = "KENSAIAPP_CONTEXT_CAP"
TIMEOUT_SECONDS = 120


def cap_env():
    cap = os.environ.get(CAP_KEY, "")
    return {CAP_KEY: cap} if cap else {}


def settings_line(env):
    return "SETTINGS\t" + json.dumps({"env": env}, separators=(",", ":"))


# Only the characters that would break the protocol below: a tab splits a line into fields and a
# newline or carriage return splits it into lines. Every other character the package returns is
# carried.
def carriable(text):
    return not any(ch in text for ch in "\t\n\r")


def endpoint_cause(stderr):
    if "no published telemetry endpoint at " in stderr:
        return "none"
    if "is unreadable or malformed" in stderr:
        return "malformed"
    if "is not on this machine (loopback only)" in stderr:
        return "remote"
    return None


def normalized(stdout):
    document = json.loads(stdout)
    env = document["env"]
    if not isinstance(env, dict):
        return None
    for key in BASE_KEYS + (ATTRIBUTES_KEY,):
        if not isinstance(env.get(key), str) or not carriable(env[key]):
            return None
    pairs = env[ATTRIBUTES_KEY].split(",")
    split = [pair.split("=", 1) for pair in pairs]
    if any(len(item) != 2 or not item[0] for item in split):
        return None
    arm = [p for p, item in zip(pairs, split) if item[0] == "kensai.arm"]
    run_id = [p for p, item in zip(pairs, split) if item[0] == "kensai.run_id"]
    instance = [p for p, item in zip(pairs, split) if item[0] == "kensai.instance"]
    if len(run_id) != 1:
        return None
    rest = [
        p for p, item in zip(pairs, split)
        if item[0] not in ("kensai.arm", "kensai.run_id", "kensai.instance")
    ]
    return {key: env[key] for key in BASE_KEYS}, ",".join(arm + run_id + instance + rest)


def run(command, endpoint_file, labels):
    argv = [command, "turn-on", "--print", "--endpoint-file", endpoint_file, "--prefix", "kensai"]
    for label in labels:
        argv += ["--label", label]
    try:
        done = subprocess.run(
            argv, stdin=subprocess.DEVNULL, capture_output=True, timeout=TIMEOUT_SECONDS
        )
    except subprocess.TimeoutExpired:
        print("FAIL\tunusable")
        return
    except OSError:
        print("FAIL\tstart")
        return
    if done.returncode != 0:
        print("FAIL\tstatus\t" + str(done.returncode))
        return
    try:
        stdout = done.stdout.decode("utf-8")
        stderr = done.stderr.decode("utf-8", errors="replace")
    except UnicodeDecodeError:
        print("FAIL\tunusable")
        return
    if not stdout.strip():
        cause = endpoint_cause(stderr)
        print("ENDPOINT\t" + cause if cause else "FAIL\tunusable")
        return
    try:
        result = normalized(stdout)
    except (ValueError, KeyError, TypeError, AttributeError):
        result = None
    if result is None:
        print("FAIL\tunusable")
        return
    base, attributes = result
    env = dict(base)
    env.update(cap_env())
    env[ATTRIBUTES_KEY] = attributes
    print(settings_line(env))
    for key in BASE_KEYS:
        print("EXPORT\t" + key + "\t" + base[key])
    print("EXPORT\t" + ATTRIBUTES_KEY + "\t" + attributes)


mode = sys.argv[1]
if mode == "cap":
    if cap_env():
        print(settings_line(cap_env()))
else:
    run(sys.argv[2], sys.argv[3], sys.argv[4:])
'

# A value OTEL_RESOURCE_ATTRIBUTES cannot carry — whitespace, a double quote, a comma, a semicolon,
# a backslash or an `=`. Every value this file hands the package passes it first, so the package is
# never asked to carry such a value.
_run_telemetry_value_unexportable() {
  case "$1" in
    *[[:space:]]*|*'"'*|*,*|*';'*|*'\'*|*'='*) return 0 ;;
    *) return 1 ;;
  esac
}

# The product a project names, read from that project's card under the working directory: the
# basename of the first path token on the first `**Product path:**` line. Echoes nothing when the
# card, the line or a path is absent.
_run_telemetry_derive_product() {
  local project_md="system/projects/$1/project.md"
  [ -r "$project_md" ] || return 0
  local line
  line="$(grep -m1 '^\*\*Product path:\*\*' "$project_md" 2>/dev/null || true)"
  [ -n "$line" ] || return 0
  local rest="${line#\*\*Product path:\*\*}"
  local path
  # `read` splits on whitespace without expanding a glob, so the trailing HTML comment is never part
  # of the path.
  read -r path _ <<EOF || true
$rest
EOF
  [ -n "$path" ] || return 0
  basename "$path"
}

# The command's name when the invoking environment holds none: what `telemetry_command.py`
# answers for the core this file sits in. The resolver is found from this file's own physical
# location, never from the caller's working directory, because a launcher cd's to its instance
# root and a pinned core is not beside it. Prints the name, or nothing when the resolver is
# missing, fails or answers anything but one line — the caller then reads the absent name as
# unconfigured. The resolver's diagnostics are discarded: the launch must not carry them.
_run_telemetry_discover() {
  local tools_dir resolver answer
  tools_dir="$( { cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd -P; } || true )"
  [ -n "$tools_dir" ] || return 0
  resolver="$tools_dir/telemetry_command.py"
  [ -f "$resolver" ] || return 0
  answer="$(python3 "$resolver" --core "$(dirname "$tools_dir")" 2>/dev/null)" || return 0
  case "$answer" in
    *$'\n'*) return 0 ;;
  esac
  printf '%s' "$answer"
}

# Prints the uninstrumented line for one cause and leaves the settings at the context cap alone (or
# unset). The cap is not telemetry: a chain developer run is held to it whether or not a receiver is
# published, and --settings is its only route into a backgrounded session.
_run_telemetry_uninstrumented() {
  echo "          ($1 — run uninstrumented)"
  local cap_settings
  cap_settings="$(python3 -c "$_RUN_TELEMETRY_BRIDGE" cap 2>/dev/null || true)"
  cap_settings="${cap_settings#SETTINGS$'\t'}"
  [ -n "$cap_settings" ] || return 0
  INSTRUMENT_RUN_SETTINGS="$cap_settings"
  export INSTRUMENT_RUN_SETTINGS
}

# The arm: INSTRUMENT_RUN_ARM when non-empty, else the calling launcher's own directory. $1 is the
# calling file, resolved by run_telemetry before this file's own frames are added. Sets
# _run_telemetry_arm_value to the arm, or to nothing when it is refused, and appends the refusal
# line to _run_telemetry_notices — a subshell would lose that line, so nothing is echoed.
_run_telemetry_arm() {
  local arm caller_dir
  _run_telemetry_arm_value=""
  if [ -n "${INSTRUMENT_RUN_ARM:-}" ]; then
    arm="$INSTRUMENT_RUN_ARM"
  else
    # $SCRIPT_DIR is the only answer resolved at the right moment: every launcher takes it
    # absolutely before it cd's to the instance root, where the caller's own path may already read
    # `.`.
    caller_dir="${SCRIPT_DIR:-}"
    case "$caller_dir" in
      /*) ;;
      *) caller_dir="$( { cd "$(dirname "$1")" 2>/dev/null && pwd; } || true )" ;;
    esac
    if [ -n "$caller_dir" ]; then
      arm="$(basename "$caller_dir")"
    else
      arm=""
    fi
  fi
  case "$arm" in
    ""|.|..|/)
      _run_telemetry_notices+=("          (kensai.arm could not be derived from the calling launcher's directory — arm not attached)")
      return 0
      ;;
    *[[:space:]]*)
      _run_telemetry_notices+=("          (kensai.arm '$arm' contains whitespace — OTEL_RESOURCE_ATTRIBUTES cannot carry one; arm not attached)")
      return 0
      ;;
  esac
  if _run_telemetry_value_unexportable "$arm"; then
    _run_telemetry_notices+=("          (kensai.arm '$arm' contains a character OTEL_RESOURCE_ATTRIBUTES cannot carry — arm not attached)")
    return 0
  fi
  _run_telemetry_arm_value="$arm"
}

# Collects the labels in the order **Attribute order** in the header states, and the refusal lines
# to print, into _run_telemetry_labels and _run_telemetry_notices. $1 is the calling file.
_run_telemetry_collect() {
  local caller="$1"
  shift
  _run_telemetry_arm "$caller"
  [ -z "$_run_telemetry_arm_value" ] || _run_telemetry_labels+=("arm=$_run_telemetry_arm_value")

  local kv key value product
  for kv in "$@"; do
    case "$kv" in
      *=*) ;;
      *)
        _run_telemetry_notices+=("          (telemetry argument '$kv' has no '=' — expected key=value; not attached)")
        continue
        ;;
    esac
    key="${kv%%=*}"
    value="${kv#*=}"
    case "$_RUN_TELEMETRY_ACCEPTED_KEYS" in
      *" $key "*) ;;
      *)
        _run_telemetry_notices+=("          (unknown telemetry key '$key' — only project, document, skill, target_instance, provider, model, effort and source are accepted)")
        continue
        ;;
    esac
    [ -n "$value" ] || continue
    if _run_telemetry_value_unexportable "$value"; then
      _run_telemetry_notices+=("          (kensai.$key '$value' contains a character OTEL_RESOURCE_ATTRIBUTES cannot carry — not attached)")
      continue
    fi
    _run_telemetry_labels+=("$key=$value")
    if [ "$key" = "project" ]; then
      product="$(_run_telemetry_derive_product "$value")"
      if [ -n "$product" ] && ! _run_telemetry_value_unexportable "$product"; then
        _run_telemetry_labels+=("product=$product")
      fi
    fi
  done

  # The chain walk and the responsible role: environment variables the chain engines set, never a
  # documented launcher flag. A refused or empty one is dropped silently.
  local tag name
  for tag in walk_id:INSTRUMENT_RUN_WALK_ID chain:INSTRUMENT_RUN_CHAIN \
    role:INSTRUMENT_RUN_ROLE audit_target:INSTRUMENT_RUN_AUDIT_TARGET; do
    name="${tag#*:}"
    value="${!name:-}"
    if [ -n "$value" ] && ! _run_telemetry_value_unexportable "$value"; then
      _run_telemetry_labels+=("${tag%%:*}=$value")
    fi
  done
}

_run_telemetry_main() {
  local caller="$1"
  shift
  # A value inherited from whatever started this launcher is not this run's — clear it first.
  unset INSTRUMENT_RUN_SETTINGS

  # Membership decides, not truth: a variable that is set but empty is the caller's explicit
  # answer, and it reads as unconfigured without asking the resolver.
  local name
  if [ -n "${KENSAIAPP_TELEMETRY_COMMAND+set}" ]; then
    name="$KENSAIAPP_TELEMETRY_COMMAND"
  else
    name="$(_run_telemetry_discover)"
  fi
  if [ -z "$name" ]; then
    _run_telemetry_uninstrumented "no telemetry command configured in KENSAIAPP_TELEMETRY_COMMAND"
    return 0
  fi
  case "$name" in
    .*|-*|*[!A-Za-z0-9._-]*)
      _run_telemetry_uninstrumented "KENSAIAPP_TELEMETRY_COMMAND is not a plain command name (name only, no path or arguments)"
      return 0
      ;;
  esac
  local command_path="${HOME:-}/.kensaiapp/venv/bin/$name"
  if [ ! -f "$command_path" ] || [ ! -x "$command_path" ]; then
    _run_telemetry_uninstrumented "no runnable telemetry command at $command_path"
    return 0
  fi

  local endpoint_file="${INSTRUMENT_RUN_ENDPOINT_FILE:-${HOME:-}/.claude/tools/otel-receiver/endpoint}"

  _run_telemetry_labels=()
  _run_telemetry_notices=()
  _run_telemetry_collect "$caller" "$@"

  local result
  result="$(python3 -c "$_RUN_TELEMETRY_BRIDGE" run "$command_path" "$endpoint_file" \
    ${_run_telemetry_labels[@]+"${_run_telemetry_labels[@]}"} 2>/dev/null || true)"

  local kind first second settings="" status="" detail=""
  local export_names=() export_values=()
  while IFS=$'\t' read -r kind first second; do
    case "$kind" in
      SETTINGS) settings="$first" ;;
      EXPORT)
        export_names+=("$first")
        export_values+=("$second")
        ;;
      ENDPOINT) status="endpoint"; detail="$first" ;;
      FAIL) status="fail"; detail="$first:$second" ;;
    esac
  done <<EOF
$result
EOF

  if [ "$status" = "endpoint" ]; then
    case "$detail" in
      none) _run_telemetry_uninstrumented "no published telemetry endpoint at $endpoint_file" ;;
      malformed) _run_telemetry_uninstrumented "telemetry endpoint at $endpoint_file is unreadable or malformed" ;;
      *) _run_telemetry_uninstrumented "telemetry endpoint at $endpoint_file is not on this machine (loopback only)" ;;
    esac
    return 0
  fi
  if [ "$status" = "fail" ]; then
    case "$detail" in
      start:*) _run_telemetry_uninstrumented "telemetry command at $command_path could not be started" ;;
      status:*) _run_telemetry_uninstrumented "telemetry command at $command_path exited with status ${detail#status:}" ;;
      *) _run_telemetry_uninstrumented "telemetry command at $command_path did not print a usable settings document" ;;
    esac
    return 0
  fi
  if [ -z "$settings" ] || [ "${#export_names[@]}" -ne 6 ]; then
    _run_telemetry_uninstrumented "telemetry command at $command_path did not print a usable settings document"
    return 0
  fi

  local notice index
  for index in 0 1 2 3 4 5; do
    export "${export_names[$index]}=${export_values[$index]}"
  done
  INSTRUMENT_RUN_SETTINGS="$settings"
  export INSTRUMENT_RUN_SETTINGS
  for notice in ${_run_telemetry_notices[@]+"${_run_telemetry_notices[@]}"}; do
    echo "$notice"
  done
  echo "          Telemetry:    ${OTEL_RESOURCE_ATTRIBUTES} → ${OTEL_EXPORTER_OTLP_ENDPOINT}"
}

run_telemetry() {
  # The calling file is read here, before this file's own frames sit above it.
  local _run_telemetry_labels=() _run_telemetry_notices=() _run_telemetry_arm_value=""
  _run_telemetry_main "${BASH_SOURCE[1]:-}" "$@" || true
  return 0
}
