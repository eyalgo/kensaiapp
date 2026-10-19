#!/usr/bin/env bash
# pin_run.sh — the shared launcher entry
# Version: 1.1.0 — a build-idea start takes a new pin when the host changed
# Version: 1.0.0 — created 2026-09-22, alongside the pin itself (core/tools/pin.py)
#
# Sourced, not executed — every `launcher.sh` and `launch-*.sh` sources this file and calls
# `pin_enter <core_dir> <script path> "$@"` right after deriving `CORE_DIR` and its guard, before
# anything else reads `CORE_DIR`. `build-idea` alone calls `pin_enter_renewing`, the same call with
# the same arguments, which differs at two places below.
#
# `pin_enter` decides the pin in force for this launch, in order:
#   1. `CORE_DIR` already lies in a pin (a `pin.json` sits beside it) → use it.
#   2. Otherwise, `KENSAIAPP_PIN` names a pin whose source is this host → use it. A missing pin
#      prints why to stderr and returns non-zero.
#   3. Otherwise, with `--dry-run` among the caller's own arguments → make nothing.
#   4. Otherwise → make a new pin of `CORE_DIR/..`.
#
# `pin_enter_renewing` runs the same four rules and differs at rules 1 and 2, the two places
# `pin_enter` would inherit. There it first runs `core/tools/pin_host_changed.py` on the pin, which
# owns what "changed" means, and on `changed` makes a new pin of the pin's source host instead —
# `Pin: a new pin of <host>` and nothing made under `--dry-run`. A pin whose host is gone is kept,
# with one line on stderr naming the host; a comparison that fails stops the launch. The
# comparison is skipped at rule 1 on the re-exec continuation, the pin's copy of a launch that
# already decided, so one launch makes at most one pin and prints one `Pin:` line.
#
# It prints `Pin: <root> (new)`, `Pin: <root> (inherited)` or `Pin: a new pin of <host root>` —
# once per launch: the pin's copy a re-exec lands in does not print the line a second time.
# When the running script is not already the pin's own copy, it `exec`s that copy with the same
# arguments and cwd — the pin's copy derives `CORE_DIR` again, finds itself in the pin at rule 1,
# and continues. Otherwise it exports the pin's run environment (`KENSAIAPP_PIN`, the
# `GIT_CONFIG_*` triple) and returns.
#
# Bash 3.2 throughout — no `mapfile`, no `${var@Q}`, no associative arrays.

# Whether `--dry-run` is among the caller's own arguments.
_pin_dry_run_requested() {
  local arg
  for arg in "$@"; do
    if [ "${arg}" = "--dry-run" ]; then
      return 0
    fi
  done
  return 1
}

# The one body behind both public names — the four rules live here once, so `pin_enter`'s output
# cannot drift from `pin_enter_renewing`'s. `mode` is `plain` or `renewing`.
_pin_enter_as() {
  local mode="$1"
  local core_dir="$2"
  local script_path="$3"
  shift 3

  local pin_root=""
  local pin_mode=""
  local announced=""
  local host_root

  if [ -f "${core_dir}/../pin.json" ]; then
    pin_root="$(cd "${core_dir}/.." && pwd -P)"
    pin_mode="(inherited)"
    # The re-exec below hands this marker to the pin's own copy of the same launch, which
    # already printed its `Pin:` line — one line per launch (CP-103/104). Cleared here, before
    # anything is started, so a launcher this run starts still prints its own line.
    if [ "${KENSAIAPP_PIN_ANNOUNCED:-}" = "${pin_root}" ]; then
      announced=1
    fi
    unset KENSAIAPP_PIN_ANNOUNCED
  else
    host_root="$(cd "${core_dir}/.." && pwd -P)"

    local resolve_out resolve_rc
    resolve_out="$(python3 "${core_dir}/tools/pin.py" resolve --core "${core_dir}" 2>&1)"
    resolve_rc=$?

    if [ "${resolve_rc}" -eq 3 ]; then
      echo "${resolve_out}" >&2
      return "${resolve_rc}"
    fi

    if [ -n "${resolve_out}" ]; then
      local candidate_root candidate_source
      candidate_root="$(printf '%s\n' "${resolve_out}" | sed -n 's/^pin=//p')"
      candidate_source="$(printf '%s\n' "${resolve_out}" | sed -n 's/^source=//p')"
      if [ "${candidate_source}" = "${host_root}" ]; then
        pin_root="${candidate_root}"
        pin_mode="(inherited)"
      fi
    fi

    if [ -z "${pin_root}" ]; then
      if _pin_dry_run_requested "$@"; then
        echo "Pin: a new pin of ${host_root}"
        return 0
      fi

      pin_root="$(python3 "${core_dir}/tools/pin.py" make --host "${host_root}")"
      pin_mode="(new)"
    fi
  fi

  # Where `pin_enter` would inherit, `pin_enter_renewing` asks first — and never on the re-exec
  # continuation, which belongs to the start that already decided.
  if [ "${mode}" = "renewing" ] && [ "${pin_mode}" = "(inherited)" ] && [ -z "${announced}" ]; then
    # Captured with an explicit status and not under `set -e`, which is suspended anyway where a
    # launcher writes `pin_enter_renewing … || exit $?`. The comparator's own stderr passes through.
    local check_out check_rc=0 verdict source_host
    check_out="$(python3 -B "${core_dir}/tools/pin_host_changed.py" --pin "${pin_root}")" || check_rc=$?
    if [ "${check_rc}" -ne 0 ]; then
      return "${check_rc}"
    fi
    verdict="$(printf '%s\n' "${check_out}" | sed -n 's/^verdict=//p')"
    source_host="$(printf '%s\n' "${check_out}" | sed -n 's/^host=//p')"

    case "${verdict}" in
      unchanged)
        ;;
      host-gone)
        echo "pin_enter_renewing: the host ${source_host} of pin ${pin_root} is gone — keeping the pin" >&2
        ;;
      changed)
        if _pin_dry_run_requested "$@"; then
          echo "Pin: a new pin of ${source_host}"
          return 0
        fi
        pin_root="$(python3 "${core_dir}/tools/pin.py" make --host "${source_host}")"
        pin_mode="(new)"
        ;;
      *)
        echo "pin_enter_renewing: pin_host_changed.py answered '${verdict}' for ${pin_root}" >&2
        return 1
        ;;
    esac
  fi

  if [ -z "${announced}" ]; then
    echo "Pin: ${pin_root} ${pin_mode}"
  fi

  local rel_path="${script_path#${core_dir}/}"
  local pin_script="${pin_root}/core/${rel_path}"

  local script_real pin_script_real
  script_real="$(cd "$(dirname "${script_path}")" && pwd -P)/$(basename "${script_path}")"
  pin_script_real="$(cd "$(dirname "${pin_script}")" && pwd -P)/$(basename "${pin_script}")"

  if [ "${script_real}" != "${pin_script_real}" ]; then
    KENSAIAPP_PIN_ANNOUNCED="$(cd "${pin_root}" && pwd -P)"
    export KENSAIAPP_PIN_ANNOUNCED
    exec "${pin_script}" "$@"
  fi

  local env_line key value
  while IFS= read -r env_line; do
    if [ -n "${env_line}" ]; then
      key="${env_line%%=*}"
      value="${env_line#*=}"
      export "${key}=${value}"
    fi
  done < <(python3 "${core_dir}/tools/pin.py" env --pin "${pin_root}")

  return 0
}

pin_enter() {
  _pin_enter_as plain "$@"
}

pin_enter_renewing() {
  _pin_enter_as renewing "$@"
}
