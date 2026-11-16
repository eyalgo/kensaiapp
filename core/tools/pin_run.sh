#!/usr/bin/env bash
# pin_run.sh — the shared launcher entry
# Version: 1.6.1 — a product-card launch passes its exemption whatever the argument order
# Version: 1.6.0 — the Behave starter runs on its own locked uv setup
# Version: 1.5.0 — the installed starter is committed — the Behave check commits the starter it installs
# Version: 1.4.0 — every run starts with the checks
# Version: 1.3.0 — prepare new pins with the host interpreter before launch
# Version: 1.2.0 — launchers run on the locked Python
# Version: 1.1.0 — a build-idea start takes a new pin when the host changed
# Version: 1.0.0 — created 2026-09-22, alongside the pin itself (core/tools/pin.py)
#
# Sourced, not executed — every `launcher.sh` and `launch-*.sh` sources this file and calls
# `pin_enter <core_dir> <script path> "$@"` right after deriving `CORE_DIR` and its guard, before
# anything else reads `CORE_DIR`. `build-idea` alone calls `pin_enter_renewing`, the same call with
# the same arguments, which differs at two places below.
#
# Before any of that, `pin_enter` asks `core/tools/locked_python.sh --check <launcher>` whether uv is
# on PATH, and returns its status when it is not (1, with the launch's message on stderr): a launch
# without uv makes no pin and starts no Python. Every Python this file starts runs through the same
# runner, on the Python the instance root pins, never the `python3` PATH finds first.
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
# Each new snapshot is prepared through its selected source host's locked_python.sh before
# announcement or re-exec. The pin's own first Python therefore uses an existing .venv; inherited
# pins and dry runs do not prepare again. A preparation error returns before announcing the pin.
#
# It prints `Pin: <root> (new)`, `Pin: <root> (inherited)` or `Pin: a new pin of <host root>` —
# once per launch: the pin's copy a re-exec lands in does not print the line a second time.
# When the running script is not already the pin's own copy, it `exec`s that copy with the same
# arguments and cwd — the pin's copy derives `CORE_DIR` again, finds itself in the pin at rule 1,
# and continues. Otherwise it exports the pin's run environment (`KENSAIAPP_PIN`, the
# `GIT_CONFIG_*` triple) and returns.
#
# Once the pin is decided, both entries run the start-of-run list, `pin_start_checks`, once per
# launch, in the process that carries the launch on: the pin's own copy after a re-exec, or this
# copy on the two `--dry-run` returns that make no pin. The list runs after the uv check, which
# stays outside it, and before the launcher reads its own arguments. It returns the first non-zero
# answer a check gives, so a stop leaves through the `|| exit $?` on the launcher's entry call
# before any agent starts or anything is written into a product. The list holds one check today,
# the Behave check.
#
# The Behave check reads the `**Behave:**` line of the card of the project a launch names,
# `system/projects/<project>/project.md` under the launch's instance root, and never writes to it.
# A launch names a project by its launcher's own usage: the first positional of `change`, `walk`,
# `build-idea`, `product-skeleton`, `companion-self-answer`, `product-docs` and
# `prd-and-finish-line`, the `--project` value of `cold-read`, and, for `product-card`, its one bare
# word, wherever it stands after the optional `--instance-root <dir>` pair. Every other launcher
# names none, and so does a first positional that begins `--` for the launchers that read one. A
# leading `--instance-root <dir>` pair names the instance root for the launchers that take one.
# Otherwise the instance root is the launch's working directory. `core/tools/test_start_checks.py`
# holds this table to every launcher's own usage, so a launcher that gains a project argument fails
# there until the table names it.
#
# The check is skipped, and prints and writes nothing, for:
#   - a `product-card`, `product-docs` or `prd-and-finish-line` launch, because the Behave call is
#     made in those runs (the owner's ruling, 2026-11-10);
#   - a `companion-self-answer` or `product-skeleton` launch for the project the definition launch
#     that started it named. A definition launch that passes exports
#     `KENSAIAPP_DEFINITION_RUN=<project>`, and only these two launchers, launched for that project,
#     act on it. Any other launch for that project, a `walk` included, is still checked;
#   - a launch given `--stop`, a launch that names no project, a project name that holds a `/` or
#     begins with `.`, and a project whose card does not exist. The launcher's own handling of each
#     follows.
#
# Otherwise the card's Behave value is the text after `**Behave:**`, up to an inline `<!--`,
# trimmed. The card has made the call only when it holds exactly one `**Behave:**` line and its
# value is `behave`, or `none — ` followed by a reason that is neither empty nor the literal
# `<reason>`.
# That is the test product-card applies when it copies the call from the NFDR. Then:
#   - no call made → the launch stops with status 1 and a message naming the Principal Architect's
#     `product-architecture` run, which makes the call. `--dry-run` stops the same way;
#   - `none — ` and a reason → the launch goes on, and the check prints and writes nothing;
#   - `behave`, and anything named `.behave` directly under the product folder — a folder, a
#     file or a link, a dangling link included → the check hands it to
#     `tools/install_behave_starter.py`, which only reads git there, `--dry-run` or not. When a
#     path in it is untracked, staged, modified, deleted or ignored in the git work tree holding
#     the product folder, the launch stops with status 1, one line names each such path, and
#     nothing is written. What the starter's own `.gitignore` ignores does not count. Otherwise,
#     a `.behave` committed and clean or a product folder in no work tree, the launch goes on,
#     and the check prints, writes and commits nothing. A `features` at the product folder's
#     root decides nothing;
#   - `behave`, and nothing named `.behave` there → the check hands the install to
#     `tools/install_behave_starter.py`. The tool writes every file of
#     `templates/behave-starter/`, from the core the launch runs on, into `.behave` under the
#     product folder, and commits those files and nothing else on `main`. Every other staged
#     entry stays staged and is in no commit. The tool prints one line naming the commit, and the
#     launch goes on. When git refuses the stage or the commit, the tool removes what it wrote,
#     and the launch stops with status 1 on one line quoting the refusal. Where no commit can land
#     on `main` for another reason — the product folder is in no git work tree, the work tree has
#     another branch or a detached `HEAD` checked out, or `main` has no commit yet — the tool
#     leaves the product as it found it, prints one line naming the reason, and the launch goes
#     on. An unexpected failure stops the launch with status 1. Under `--dry-run` the check writes
#     and commits nothing and says the starter would be installed and committed on `main`;
#   - `behave`, and no product folder (the card has no `Product path:` line, or the folder it names
#     does not exist) → the check creates nothing, says the starter was not installed, and the
#     launch goes on;
#   - `behave`, and a core with no `templates/behave-starter/` → the launch stops with status 1
#     and a message naming that folder.
# The product folder is the card's `Product path:`: a leading `~/` is the home directory, an
# absolute path is taken as written, and any other path is under the instance root. Every message
# goes to stderr, led by the launch's own name.
# The starter's folder is named `.behave` in every product, and the starter's README names it too.
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

# The name a launch goes by in its own messages: the folder of a `launcher.sh`, and the file's
# name without `.sh` for a flat `launch-*.sh`.
_pin_launcher_name() {
  local base
  base="$(basename "$1" .sh)"
  if [ "${base}" = "launcher" ]; then
    basename "$(dirname "$1")"
  else
    echo "${base}"
  fi
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

  # --- uv is looked for once, here, before a pin is made or any Python is started ---
  "${core_dir}/tools/locked_python.sh" --check "$(_pin_launcher_name "${script_path}")" || return $?

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
    resolve_out="$("${core_dir}/tools/locked_python.sh" "${core_dir}/tools/pin.py" resolve --core "${core_dir}" 2>&1)"
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

      pin_root="$("${core_dir}/tools/locked_python.sh" "${core_dir}/tools/pin.py" make --host "${host_root}")" || return "$?"
      "${host_root}/core/tools/locked_python.sh" --prepare-pin "${pin_root}" || return "$?"
      pin_mode="(new)"
    fi
  fi

  # Where `pin_enter` would inherit, `pin_enter_renewing` asks first — and never on the re-exec
  # continuation, which belongs to the start that already decided.
  if [ "${mode}" = "renewing" ] && [ "${pin_mode}" = "(inherited)" ] && [ -z "${announced}" ]; then
    # Captured with an explicit status and not under `set -e`, which is suspended anyway where a
    # launcher writes `pin_enter_renewing … || exit $?`. The comparator's own stderr passes through.
    local check_out check_rc=0 verdict source_host
    check_out="$("${core_dir}/tools/locked_python.sh" -B "${core_dir}/tools/pin_host_changed.py" --pin "${pin_root}")" || check_rc=$?
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
        pin_root="$("${core_dir}/tools/locked_python.sh" "${core_dir}/tools/pin.py" make --host "${source_host}")" || return "$?"
        "${source_host}/core/tools/locked_python.sh" --prepare-pin "${pin_root}" || return "$?"
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
  done < <("${core_dir}/tools/locked_python.sh" "${core_dir}/tools/pin.py" env --pin "${pin_root}")

  return 0
}

# --- the start-of-run list ---

# Whether `$1` names a launcher whose launch makes the Behave call itself.
_pin_is_definition_launcher() {
  case "$1" in
    product-card|product-docs|prd-and-finish-line) return 0 ;;
  esac
  return 1
}

# Whether `$1` names a launcher that parses a leading `--instance-root <dir>` pair.
_pin_takes_instance_root() {
  case "$1" in
    cold-read|companion-self-answer|product-card|product-skeleton|skill|launch-skill-evals|launch-eval-fix)
      return 0
      ;;
  esac
  return 1
}

# The project a launch names, or nothing: `<launcher> <the launch's own arguments>`.
_pin_launch_project() {
  local launcher="$1"
  shift
  if _pin_takes_instance_root "${launcher}" && [ "${1:-}" = "--instance-root" ]; then
    if [ "$#" -ge 2 ]; then
      shift 2
    else
      shift "$#"
    fi
  fi
  case "${launcher}" in
    change|walk|build-idea|product-skeleton|companion-self-answer|product-docs|prd-and-finish-line)
      case "${1:-}" in
        ""|--*) ;;
        *) echo "$1" ;;
      esac
      ;;
    product-card)
      # The launcher's own parse: it refuses a word that begins `-` and overwrites an empty one,
      # so the project is the first word left, wherever it stands among the flags.
      while [ "$#" -gt 0 ]; do
        case "$1" in
          ""|-*) shift ;;
          *)
            echo "$1"
            return 0
            ;;
        esac
      done
      ;;
    cold-read)
      # The launcher's own parse: each `--project <value>` pair in turn, so a repeated flag
      # leaves the last value standing, and a flag with no value is refused with its usage.
      local flagged=""
      while [ "$#" -gt 0 ]; do
        if [ "$1" = "--project" ]; then
          case "${2:-}" in
            ""|--*) return 0 ;;
          esac
          flagged="$2"
          shift 2
        else
          shift
        fi
      done
      if [ -n "${flagged}" ]; then
        echo "${flagged}"
      fi
      ;;
  esac
  return 0
}

# The instance root a launch uses: `<launcher> <cwd> <the launch's own arguments>`.
_pin_launch_instance_root() {
  local launcher="$1"
  local cwd="$2"
  shift 2
  if _pin_takes_instance_root "${launcher}" && [ "${1:-}" = "--instance-root" ] && [ -n "${2:-}" ]; then
    case "$2" in
      /*) echo "$2" ;;
      *) echo "${cwd}/$2" ;;
    esac
    return 0
  fi
  echo "${cwd}"
}

# The value of the first `**<label>:**` line of a card: the text after the label, up to an inline
# `<!--` comment, trimmed. Empty when the card has no such line.
_pin_card_value() {
  local card="$1"
  local label="$2"
  local line
  # `|| true`: pipefail would otherwise end a launch here when the card has no such line.
  line="$(grep -m1 -E "^\*\*${label}:\*\*" "${card}" || true)"
  printf '%s\n' "${line}" | sed -E "s/^\*\*${label}:\*\*[[:space:]]*//; s/[[:space:]]*<!--.*\$//; s/[[:space:]]*\$//"
}

# The folder the Behave starter is installed as, directly under the product folder: the one place
# its name is stated, used for the presence test and for the install's destination.
_PIN_BEHAVE_FOLDER=".behave"

# Whether a trimmed Behave value is a made call: `behave`, or `none — ` and a reason that is
# neither empty nor the literal `<reason>`.
_pin_behave_call_made() {
  local reason
  case "$1" in
    behave)
      return 0
      ;;
    "none — "*)
      reason="${1#none — }"
      reason="${reason#"${reason%%[![:space:]]*}"}"
      if [ -n "${reason}" ] && [ "${reason}" != "<reason>" ]; then
        return 0
      fi
      ;;
  esac
  return 1
}

# The stop for a card that has not made the call: `<launch> <project> <card> <count> <value>`.
_pin_behave_stop() {
  local launch="$1"
  local project="$2"
  local card="$3"
  local count="$4"
  local value="$5"
  local card_line
  if [ "${count}" -eq 0 ]; then
    card_line="Its card, ${card}, has no **Behave:** line."
  elif [ "${count}" -eq 1 ]; then
    card_line="Its card, ${card}, has a **Behave:** line, but its value, \"${value}\", is not a made call."
  else
    card_line="Its card, ${card}, has ${count} **Behave:** lines, and a card makes the call on exactly one."
  fi
  printf '%s\n' \
    "${launch}: project ${project} has not made its Behave call, so the launch stopped and wrote nothing into the product." \
    "${card_line}" \
    "A card makes the call on exactly one line: **Behave:** behave, or **Behave:** none — followed by the reason the product does not need Behave." \
    "The Principal Architect's product-architecture run makes the call, on the **Behave:** line of the product's NFDR § 9." \
    "product-card copies it from there onto the card. Launch again once the card holds it." >&2
}

# The real installer: `<core_dir> <the installer's own arguments>`. It runs the install tool
# through the core's `locked_python.sh`, and its status is the tool's. The check is handed this
# function, or another in a test, and runs no outside program of its own.
_pin_install_behave_starter() {
  local core_dir="$1"
  shift
  "${core_dir}/tools/locked_python.sh" "${core_dir}/tools/install_behave_starter.py" "$@"
}

# The Behave check, the list's one check: `<core_dir> <launcher> <cwd> <home> <definition_project>
# <installer> <the launch's own arguments>`.
_pin_behave_check() {
  local core_dir="$1"
  local launcher="$2"
  local cwd="$3"
  local home="$4"
  local definition_project="$5"
  local installer="$6"
  shift 6

  local project instance_root card count value raw_path product starter
  project="$(_pin_launch_project "${launcher}" "$@")"
  if [ -z "${project}" ]; then
    return 0
  fi
  case "${project}" in
    */*|.*) return 0 ;;
  esac
  if [ -n "${definition_project}" ] && [ "${definition_project}" = "${project}" ]; then
    case "${launcher}" in
      companion-self-answer|product-skeleton) return 0 ;;
    esac
  fi

  instance_root="$(_pin_launch_instance_root "${launcher}" "${cwd}" "$@")"
  card="${instance_root}/system/projects/${project}/project.md"
  if [ ! -f "${card}" ]; then
    return 0
  fi

  count="$(grep -c -E '^\*\*Behave:\*\*' "${card}" || true)"
  value=""
  if [ "${count}" -eq 1 ]; then
    value="$(_pin_card_value "${card}" "Behave")"
  fi
  if [ "${count}" -ne 1 ] || ! _pin_behave_call_made "${value}"; then
    _pin_behave_stop "${launcher}" "${project}" "${card}" "${count}" "${value}"
    return 1
  fi
  if [ "${value}" != "behave" ]; then
    return 0
  fi

  raw_path="$(_pin_card_value "${card}" "Product path")"
  if [ -z "${raw_path}" ]; then
    echo "${launcher}: the Behave starter was not installed, because the card ${card} of project ${project} has no Product path: line to name a product folder." >&2
    return 0
  fi
  case "${raw_path}" in
    "~"/*) product="${home}/${raw_path#\~/}" ;;
    /*) product="${raw_path}" ;;
    *) product="${instance_root}/${raw_path}" ;;
  esac
  if [ ! -d "${product}" ]; then
    echo "${launcher}: the Behave starter was not installed, because ${product}, the product folder of project ${project}, does not exist. No folder was created." >&2
    return 0
  fi
  starter="${core_dir}/templates/behave-starter"
  # A `.behave` already there is handed to the installer too, `--dry-run` or not: it only reads
  # git there, and stops the launch on a path in it the product's work tree has not committed.
  if [ -e "${product}/${_PIN_BEHAVE_FOLDER}" ] || [ -L "${product}/${_PIN_BEHAVE_FOLDER}" ]; then
    "${installer}" "${core_dir}" --starter "${starter}" --into "${product}/${_PIN_BEHAVE_FOLDER}" \
      --project "${project}" --launch "${launcher}"
    return $?
  fi

  if [ ! -d "${starter}" ]; then
    printf '%s\n' \
      "${launcher}: project ${project}'s card says **Behave:** behave, but the Behave starter folder ${starter} does not exist in the core this launch runs on." \
      "The starter could not be installed, so the launch stopped and wrote nothing into the product." >&2
    return 1
  fi

  if _pin_dry_run_requested "$@"; then
    echo "${launcher}: DRY RUN — would install the Behave starter as ${_PIN_BEHAVE_FOLDER} in ${product}, the product folder of project ${project}, and commit it on main." >&2
    return 0
  fi
  "${installer}" "${core_dir}" --starter "${starter}" --into "${product}/${_PIN_BEHAVE_FOLDER}" \
    --project "${project}" --launch "${launcher}"
}

# The start-of-run list. It returns 0 to let the launch go on and 1 to stop it, and it returns the
# first non-zero answer a check gives. It reads the environment only through its arguments:
# `<core_dir> <launcher> <cwd> <home> <definition_project> <installer> <the launch's own
# arguments>`. The installer is the function the Behave check runs to install the starter.
pin_start_checks() {
  local core_dir="$1"
  local launcher="$2"
  local cwd="$3"
  local home="$4"
  local definition_project="$5"
  local installer="$6"
  shift 6

  if _pin_is_definition_launcher "${launcher}"; then
    return 0
  fi
  local arg
  for arg in "$@"; do
    if [ "${arg}" = "--stop" ]; then
      return 0
    fi
  done

  _pin_behave_check "${core_dir}" "${launcher}" "${cwd}" "${home}" "${definition_project}" "${installer}" "$@" || return $?
  return 0
}

# What both public entries do once the pin is decided: `<mode> <core_dir> <script path> <the
# launch's own arguments>`. The list runs here and not inside `_pin_enter_as`, because the re-exec
# is an `exec` — code after the call runs once per launch. After a definition launch that names a
# project passes the list, the marker `KENSAIAPP_DEFINITION_RUN` carries that project to the two
# launches it starts.
_pin_enter_and_check() {
  local mode="$1"
  local core_dir="$2"
  local script_path="$3"
  shift 3

  _pin_enter_as "${mode}" "${core_dir}" "${script_path}" "$@" || return $?

  local launcher project
  launcher="$(_pin_launcher_name "${script_path}")"
  pin_start_checks "${core_dir}" "${launcher}" "${PWD}" "${HOME}" "${KENSAIAPP_DEFINITION_RUN:-}" \
    _pin_install_behave_starter "$@" || return $?

  if _pin_is_definition_launcher "${launcher}"; then
    project="$(_pin_launch_project "${launcher}" "$@")"
    if [ -n "${project}" ]; then
      KENSAIAPP_DEFINITION_RUN="${project}"
      export KENSAIAPP_DEFINITION_RUN
    fi
  fi
  return 0
}

pin_enter() {
  _pin_enter_and_check plain "$@"
}

pin_enter_renewing() {
  _pin_enter_and_check renewing "$@"
}
