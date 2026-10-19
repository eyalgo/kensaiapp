#!/usr/bin/env bash
#
# launch-apply-packet.sh — deterministic, pollution-proof launcher for a fix-packet apply.
#
# Version: 1.8.2 — launchers and launch scripts take a portable mktemp template, so they run on Linux
# Version: 1.8.1 — public-repo 0.x gates 1, 3, 4, 6 — Apache-2.0 licence lines, no satellite/product/host name or machine path shipped, no default notifier, loopback-only telemetry
# Version: 1.8.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 1.7.0 — the tool launchers read the central file — launch-apply-packet, launch-audit and launch-fix-author take their provider from providers.toml
# Version: 1.6.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 1.5.1 — chain-definition, chain-foundation and the eight product document launchers are retired into chain-product and the skill launcher
# Version: 1.5.0 — the run this launcher starts is now named to its watcher. `claude --bg`'s
#   launch output is redirected to a file (never a pipe capture, which waits for end-of-file and
#   would block on the detached run) and handed to the completion-watch library as
#   --launch-output; the library parses the id out of it with `capture_agent_id` and passes it to
#   the watcher as --agent-id, the exact handle that stops the name being consulted at all. The
#   output is still echoed through unchanged. A launch line that cannot be read yields no id and
#   the watch falls back to --name exactly as before.
# Version: 1.4.0 — the hand-copied detach-and-return tail is gone: this launcher `source`s
#   the shared completion-watch home at <CORE>/tools/detach_watcher.sh and calls
#   `detach_completion_watcher` with its own values. Same behaviour, one exception the move
#   carries deliberately: the else branch now names WHICH half is missing — an unfindable
#   watcher is a launcher bug and an unset notifier is ordinary configuration, and reporting
#   the second when the first is true sends the reader to the wrong end. $DETACH_LIB is the
#   second core-relative path this file resolves and has no env override, so its default is
#   its only path. The poll knob named below keeps its own name and keeps working: it is
#   handed to the library as --keepawake-poll-seconds rather than renamed, which is what made
#   this a refactor instead of a rewrite of nine documented interfaces.
# Version: 1.3.0 — --keep-awake no longer waits on a bare pid number: the watcher's pid is paired
#   with the start time it had when this launcher spawned it, and a detached poller releases
#   caffeinate the moment a live process at that number stops matching both — never the lifetime
#   of whatever unrelated process the kernel later reissues the number to. An internal knob,
#   LAUNCH_PACKET_KEEPAWAKE_POLL_SECONDS (default 5), sets how often that identity is re-checked.
# Version: 1.2.2 — comment: repoint the retired launch-cold-read.sh to the surviving cold-read entry.
# Version: 1.2.1 — comment: the fix-author is step 4 (audit instance) and has its own launcher now;
#   this launcher is step 5, the apply, in dev. Was: "other half of this step / no launcher yet."
# Version: 1.2.0 — add --keep-awake: a detached caffeinate bound to the completion watcher, so the
#   Mac stays awake for exactly the run's duration.
#
# WHY THIS EXISTS
#   Same reason as <CORE>/launchers/cold-read/launcher.sh: a session asked to "spawn
#   the fixer and apply the packet" *composes* the subagent's prompt, and that is the one
#   place stray context leaks in (the audit's findings, a prior round's summary, "and also
#   fix X"). The prompt below is a FIXED literal — a caller passes only the packet path.
#   Nothing a caller types reaches the run.
#
#   It is short because it can be. `kaizen-fixer` loads
#   <CORE>/doctrine/kaizen/fix_packet.md when it is handed a packet, and that file owns every
#   field, the State gate, and what to do when an anchor does not match. A launcher that
#   restated any of it would be a second copy free to drift.
#
#   The deciding half — what the fix IS — is step 4's `kaizen-fix-author`, which has its own
#   launcher (launch-fix-author.sh) and runs in the audit instance. This launcher is step 5: the
#   apply, in dev.
#
# USAGE
#   <CORE>/tools/launch-apply-packet.sh <packet-path> [--dry-run]   (run from the instance root)
#     <packet-path>  a fix_packet.md (absolute, or relative to the instance repo)
#     --dry-run      print the exact claude command, but do not launch
#     --keep-awake   keep the Mac awake (caffeinate) for the run's duration; needs a notifier/watcher
#
# THE STATE GATE
#   Refuses to launch a packet not marked `State: approved`. The fixer checks this itself —
#   fix_packet.md § State owns the rule and the reason. Checking here too is duplicated
#   ENFORCEMENT, not a duplicated fact: it fails in a second instead of spending an agent on
#   a run that must stop. An unapproved packet is a draft that happens to be executable.
#
# PERMISSIONS
#   --permission-mode auto — REQUIRED. The fixer edits files and commits through
#   commit_builder.py; nobody can answer a permission prompt in a --bg run, so a prompt is not
#   a pause, it is a run that stops forever. `auto` puts a classifier on each Bash call; deny
#   and ask rules still apply. NOT a bypass and NOT --dangerously-skip-permissions — see
#   ~/.claude/CLAUDE.md § Permission mode, and the fuller note in
#   core/launchers/companion-self-answer/launcher.sh.
#   Use --bg, NOT -p/--print (--print never starts the session `claude agents` attaches to).
#
#   A packet living outside this repo (the audit vault is a separate instance) is passed via
#   --add-dir so the fixer can read it. The packet is an input, never a write target.
#
# THE REPOS THE ENTRIES EDIT (1.1.0)
#   A packet is not confined to one instance. kensaiapp's roles live in two layers: each
#   instance carries its own role loader, so a packet fixing a role fixes that loader in every
#   instance the role runs in — Round 8's E15/E17 land in the producer satellite while E16/E18 land
#   in the host's copy. That duplication is architecture, not drift; the loaders do not move.
#
#   So the write targets are whatever the entries name, and only the packet knows them. This
#   reads the entries' `File:` fields, resolves each to its git root, and --add-dirs every root
#   that is not the cwd — the same shape core/launchers/skill/launcher.sh uses for an external
#   Product path, sourced from the packet instead of a project card. Nothing is hardcoded: no sibling
#   instance is named here, and a caller still passes only a path.
#
#   Only unindented `- **File:**` lines count. `## Out of scope` names its files indented, and
#   an out-of-scope entry is one the fixer must NOT edit — granting its repo would over-grant.
#
#   fix_packet.md § Committing the round owns the other half: one commit per repo, each with
#   its own --repo. This grants the access; that decides what lands.
#
set -euo pipefail

# --- resolve the instance root (the caller's cwd) and cd there ----------------------
#   This tool lives in <CORE>/tools/ and is shared across instances, so it CANNOT derive its
#   instance from its own location — a centralized core serves many. The instance is the
#   caller's cwd; --instance-root overrides. The cd is load-bearing: `claude --bg` inherits
#   THIS shell's cwd, and the fixer resolves its edit targets and its commit --repo against it.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # <CORE>/tools — the watcher sits beside this
CORE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"                      # this script lives in <CORE>/tools
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
# shellcheck source=/dev/null
source "$CORE_DIR/tools/pin_run.sh"
pin_enter "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?
INSTANCE_ROOT="$PWD"
[ "${1:-}" = "--instance-root" ] && { INSTANCE_ROOT="$2"; shift 2; }
cd "$INSTANCE_ROOT"
INSTANCE_ROOT="$PWD"   # re-resolved absolute, even when --instance-root was given relative

# NOTIFIER carries no host-global default — a core tool must not hard-code a machine-local
# notifier path (kensaiapp_structure.md § core/tools); it comes from KENSAIAPP_NOTIFIER (or the
# override), and the ping is skipped when unset. WATCHER sits beside this script in <CORE>/tools.
WATCHER="${LAUNCH_PACKET_WATCHER:-$SCRIPT_DIR/watch_agent.py}"
NOTIFIER="${LAUNCH_PACKET_NOTIFIER:-${KENSAIAPP_NOTIFIER:-}}"

# The shared completion-watch home — the second core-relative path this launcher resolves,
# at the same real depth as WATCHER above. No env override: unlike $WATCHER, no test or
# caller ever wants a stub in its place, only the real file at its real relative depth.
DETACH_LIB="$SCRIPT_DIR/detach_watcher.sh"

# The one reader of the provider file — same real depth, and no env override: no caller may point
# a launch at another file.
PROVIDERS_TOOL="$SCRIPT_DIR/providers.py"
RUN_INTELLIGENCE="$SCRIPT_DIR/run_intelligence.py"

die() { echo "launch-apply-packet: $*" >&2; exit 1; }

# --- args --------------------------------------------------------------------------
packet_arg="${1:-}"
dry_run=""
keep_awake=""
for arg in "${@:2}"; do
  case "$arg" in
    --dry-run)    dry_run=1 ;;
    --keep-awake) keep_awake=1 ;;
  esac
done
[ -n "$packet_arg" ] || die "usage: launch-apply-packet.sh <packet-path> [--dry-run] [--keep-awake]"

# --- the provider: this launcher's entry in .providers.toml at the instance root ---
#   Read before the packet is looked at, so a launch the file cannot serve is refused before
#   anything is resolved, and a dry run is refused exactly where the launch would be.
#   The reader only runs Claude here: it is asked to accept `claude` and refuses any other entry
#   by name. No force is read — an exported KENSAIAPP_AGENT_PROVIDER is ignored. The key is this
#   script's own name as a literal, never derived from its basename, since the script may be run
#   from another folder. `providers.py` imports the intelligence resolver, so both are checked
#   before the reader is run.
[ -f "$PROVIDERS_TOOL" ] || die "no provider reader at $PROVIDERS_TOOL"
[ -f "$RUN_INTELLIGENCE" ] || die "no intelligence resolver at $RUN_INTELLIGENCE"
provider_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-apply-packet-provider.XXXXXX")"
provider="$(python3 "$PROVIDERS_TOOL" launcher launch-apply-packet --instance-root "$INSTANCE_ROOT" --accept claude \
  2>"$provider_err")" && rc=0 || rc=$?
provider_msg="$(cat "$provider_err")"
rm -f "$provider_err"
[ "$rc" -eq 0 ] || die "${provider_msg:-could not read the provider for launch-apply-packet}"

case "$packet_arg" in
  "~"/*) packet="${HOME}/${packet_arg#\~/}" ;;
  /*)    packet="$packet_arg" ;;
  *)     packet="$INSTANCE_ROOT/$packet_arg" ;;
esac
[ -f "$packet" ] || die "no packet at $packet"

# --- the State gate: refuse anything not approved -----------------------------------
#   fix_packet.md § State owns the rule; this is the cheap enforcement of it.
state="$(grep -m1 -E '^\*\*State:\*\*' "$packet" \
  | sed -E 's/^\*\*State:\*\*[[:space:]]*//; s/[[:space:]]*$//' || true)"
[ "$state" = "approved" ] || die "packet State is '${state:-missing}', not 'approved' — the owner adjudicates before the fixer runs (fix_packet.md § State). Not launching."

# --- report the verdict (READ-ONLY; never passed into the run) -----------------------
#   The fixer reads the packet itself; these lines are just for you.
verdict="$(grep -m1 -E '^\*\*Verdict:\*\*' "$packet" \
  | sed -E 's/^\*\*Verdict:\*\*[[:space:]]*//; s/[[:space:]]*$//' || true)"
[ "$verdict" != "rebuild" ] || die "packet Verdict is 'rebuild' — it carries no entries and no fixer is spawned (fix_packet.md § The verdict comes first). Not launching."
entries="$(grep -c -E '^### E[0-9]+' "$packet" || true)"
echo "Packet: $packet"
echo "        State: $state · Verdict: ${verdict:-unstated} · entries: ${entries:-0}"

# --- derive the repos the entries edit ----------------------------------------------
#   See THE REPOS THE ENTRIES EDIT above. Unindented `- **File:**` only, so `## Out of
#   scope` (which indents its own) cannot widen the grant.
entry_files="$(grep -E '^- \*\*File:\*\*' "$packet" \
  | sed -E 's/^- \*\*File:\*\*[[:space:]]*//; s/^`//; s/`[[:space:]]*$//; s/[[:space:]]*$//' \
  | sort -u || true)"
[ -n "$entry_files" ] || die "packet names no entry files (no '- **File:**' lines) — nothing to apply. Not launching."

repos=""
while IFS= read -r f; do
  [ -n "$f" ] || continue
  case "$f" in
    "~"/*) f="${HOME}/${f#\~/}" ;;
    /*)    ;;
    *)     f="$INSTANCE_ROOT/$f" ;;      # relative: the fixer resolves against cwd, so do the same
  esac
  # dirname, not the file: an entry may name a file the fix creates, which does not exist yet.
  d="$(dirname "$f")"
  [ -d "$d" ] || die "entry names '$f', whose directory does not exist — a stale packet applies nothing. Not launching."
  root="$(git -C "$d" rev-parse --show-toplevel 2>/dev/null || true)"
  [ -n "$root" ] || die "entry names '$f', which is in no git repo — the fixer commits per repo and could not commit this. Not launching."
  case "
$repos" in *"
$root"*) ;; *) repos="$repos
$root" ;; esac
done <<EOF
$entry_files
EOF
repos="${repos#
}"

echo "        Edits land in: $(echo "$repos" | tr '\n' ' ')"

# --- build the launch command: FIXED prompt, only the packet path interpolated -------
#   It says only which packet to apply. Everything else the fixer needs — the fields, the
#   gate, what to do when an anchor does not match, how to commit — is fix_packet.md's and
#   the agent's own contract. The launcher names none of it. The argv comes from the one
#   adapter, never assembled here (Task 18) — the pin was entered right after the CORE_DIR
#   guard above.
prompt="apply the fix packet at ${packet}."
claude_cmd=(python3 "$CORE_DIR/tools/agent_run.py" --provider "$provider" --shape background
  --pin auto --instance-root "$INSTANCE_ROOT" --prompt "$prompt" --agent kaizen-fixer)

# Every repo the entries edit, except the cwd, which is already covered.
while IFS= read -r root; do
  [ -n "$root" ] || continue
  [ "$root" = "$INSTANCE_ROOT" ] || claude_cmd+=(--add-dir "$root")
done <<EOF
$repos
EOF

# The packet itself: readable, and not necessarily inside any repo it edits.
case "$packet" in
  "$INSTANCE_ROOT"/*) ;;                                                  # in-repo: covered by cwd
  *) claude_cmd+=(--add-dir "$(dirname "$packet")") ;;   # external vault: an input, never a write target
esac
claude_cmd+=(--print-argv)

claude_argv=()
while IFS= read -r -d '' a; do
  claude_argv+=("$a")
done < <("${claude_cmd[@]}")
set -- "${claude_argv[@]}"

if [ -n "$dry_run" ]; then
  echo "DRY RUN — would launch:"
  printf '  %q' "$@"; echo
  exit 0
fi

# --- snapshot existing agent ids BEFORE launching ------------------------------------
#   The launched agent is identified by (name, cwd, id-not-seen-before). Name alone is
#   ambiguous: re-applying the same packet reuses the same fixed prompt. Captured before the
#   launch, or the new agent would be in its own exclusion set.
ids_before="$(python3 "$WATCHER" --list-ids --cwd "$INSTANCE_ROOT" 2>/dev/null || true)"

echo "Launching kaizen-fixer (background)…"
# stdout is captured so the id `claude --bg` prints at launch can be read off it, then echoed
# through unchanged so the caller still sees `claude`'s own attach/stop hints. The parse is the
# completion-watch library's `capture_agent_id`, reached below via --launch-output; nothing here
# reads the line itself.
# Redirected to a FILE, never captured through a pipe. `$( … )` waits for end-of-file on the
# pipe, not for the command to exit — and `claude --bg` leaves a detached run holding the
# inherited descriptor, so a pipe capture would block this launcher for the whole run it just
# backgrounded. That is the one thing every launcher here promises not to do.
launch_log="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-launch-out.XXXXXX")"
"$@" >"$launch_log" 2>&1
launch_out="$(cat "$launch_log")"
rm -f "$launch_log"
printf '%s\n' "$launch_out"
echo "Launched. Watch/attach: claude agents        (interactive view — logs, stop, resume live here)"
echo "          Script it:    claude agents --json --all   (machine-readable run state)"

if [ -f "$DETACH_LIB" ]; then
  # shellcheck source=./detach_watcher.sh
  source "$DETACH_LIB"
  detach_completion_watcher \
    --watcher "$WATCHER" --notifier "$NOTIFIER" \
    --instance-root "$INSTANCE_ROOT" --prompt "$prompt" \
    --label "$(basename "$(dirname "$packet")")" --log-stem "packet" --reporter apply-packet \
    --head-repo "$INSTANCE_ROOT" \
    --exclude-ids "$ids_before" \
    --launch-output "$launch_out" \
    --keepawake-poll-seconds "${LAUNCH_PACKET_KEEPAWAKE_POLL_SECONDS:-5}" \
    ${keep_awake:+--keep-awake}
else
  echo "          (no completion-watch library at $DETACH_LIB — completion watch skipped)"
fi
