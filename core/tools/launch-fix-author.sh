#!/usr/bin/env bash
#
# launch-fix-author.sh — deterministic, pollution-proof launcher for a fix-packet authoring run.
#
# Version: 1.9.1 — launchers and launch scripts take a portable mktemp template, so they run on Linux
# Version: 1.9.0 — public-repo 0.x gates 1, 3, 4, 6 — Apache-2.0 licence lines, no satellite/product/host name or machine path shipped, no default notifier, loopback-only telemetry
# Version: 1.8.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 1.7.0 — the tool launchers read the central file — launch-apply-packet, launch-audit and launch-fix-author take their provider from providers.toml
# Version: 1.6.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 1.5.1 — chain-definition, chain-foundation and the eight product document launchers are retired into chain-product and the skill launcher
# Version: 1.5.0 — the resolver capture no longer folds stderr into the value that becomes
#   $skill_dir (was `2>&1`; a future resolver warning on a successful exit would have landed
#   INSIDE the path). Standard error is captured to its own temp file instead, read back only for
#   the ambiguous (exit 4) message, which is what it always fed. $RESOLVER also gains an env
#   override, LAUNCH_AUTHOR_RESOLVER, the seam a test needs to stand a stub resolver on this path.
# Version: 1.4.0 — the run this launcher starts is now named to its watcher. `claude --bg`'s
#   launch output is redirected to a file (never a pipe capture, which waits for end-of-file and
#   would block on the detached run) and handed to the completion-watch library as
#   --launch-output; the library parses the id out of it with `capture_agent_id` and passes it to
#   the watcher as --agent-id, the exact handle that stops the name being consulted at all. The
#   output is still echoed through unchanged. A launch line that cannot be read yields no id and
#   the watch falls back to --name exactly as before.
# Version: 1.3.0 — the hand-copied detach-and-return tail is gone: this launcher `source`s
#   the shared completion-watch home at <CORE>/tools/detach_watcher.sh and calls
#   `detach_completion_watcher` with its own values. Same behaviour, one exception the move
#   carries deliberately: the else branch now names WHICH half is missing — an unfindable
#   watcher is a launcher bug and an unset notifier is ordinary configuration, and reporting
#   the second when the first is true sends the reader to the wrong end. $DETACH_LIB is the
#   second core-relative path this file resolves and has no env override, so its default is
#   its only path. The poll knob named below keeps its own name and keeps working: it is
#   handed to the library as --keepawake-poll-seconds rather than renamed, which is what made
#   this a refactor instead of a rewrite of nine documented interfaces.
# Version: 1.2.0 — --keep-awake no longer waits on a bare pid number: the watcher's pid is paired
#   with the start time it had when this launcher spawned it, and a detached poller releases
#   caffeinate the moment a live process at that number stops matching both — never the lifetime
#   of whatever unrelated process the kernel later reissues the number to. An internal knob,
#   LAUNCH_AUTHOR_KEEPAWAKE_POLL_SECONDS (default 5), sets how often that identity is re-checked.
# Version: 1.1.1 — comment: repoint the retired launch-cold-read.sh to the surviving cold-read entry.
# Version: 1.1.0 — add --keep-awake: a detached caffeinate bound to the completion watcher, so the
#   Mac stays awake for exactly the run's duration.
#
# WHY THIS EXISTS
#   Same reason as <CORE>/launchers/cold-read/launcher.sh and launch-apply-packet.sh: a session
#   asked to "spawn the fix author on the round's audit" *composes* the subagent's prompt, and that is
#   the one place stray context leaks in (a prior round's summary, which findings you think matter,
#   "and while you're there…"). The prompt below is a FIXED literal — a caller passes only a skill name
#   and optionally a version. Nothing a caller types reaches the run.
#
#   It is one sentence long because it can be. `kaizen-fix-author` reads
#   <CORE>/doctrine/kaizen/fix_packet.md, which owns what a packet contains, what makes it fit to act
#   on, and the fix-or-rebuild call. A launcher restating any of that would be a second copy free to
#   drift.
#
# WHERE IT RUNS
#   In the producer satellite: the audits it reads and the packet it commits both live there. (Its
#   sibling launch-apply-packet.sh runs in the host, because the fixer edits SKILL.md, which from the
#   producer is a symlink.) Authored in the host — the upstream tip — and copied to the producer,
#   matching system/tools/'s vendored pattern.
#
# USAGE
#   <CORE>/tools/launch-fix-author.sh <skill> [version] [--settle] [--dry-run]   (run from the instance root)
#     <skill>     a skill with an evidence vault, e.g. product-prd
#     [version]   e.g. 3.17.0 — omitted means the NEWEST evidence/v*/ that has an audit.md
#     --settle    fold the owner's answers into a packet they have already answered
#     --dry-run   print the exact claude command, but do not launch
#     --keep-awake  keep the Mac awake (caffeinate) for the run's duration; needs a notifier/watcher
#
# TWO MODES, ONE AGENT
#   Default: author a packet from the round's audit. Refuses if a packet already exists — overwriting
#   one would destroy an owner adjudication.
#
#   --settle: the second half of the same job. The owner answered in `owner_answers.md` beside the
#   packet, and an answer usually changes the packet (a conditional entry applies or is withdrawn, the
#   projection and tallies move). That is deciding work, so it is the author's — not the fixer's, which
#   applies verbatim. The same packet-exists guard is INVERTED rather than dropped: default dies when
#   the packet is there, --settle dies when it is not.
#
# PERMISSIONS
#   --permission-mode auto — REQUIRED. Nobody can answer a permission prompt in a --bg run, so a prompt
#   is not a pause: it is a run that stops forever. `auto` puts a classifier on each Bash call; deny and
#   ask rules still apply. NOT a bypass and NOT --dangerously-skip-permissions — see
#   ~/.claude/CLAUDE.md § Permission mode and the fuller note in
#   core/launchers/companion-self-answer/launcher.sh.
#   Use --bg, NOT -p/--print (--print never starts the session `claude agents` attaches to).
#
#   --add-dir on the dev repo covers what the run reads outside this instance: <CORE> doctrine, and
#   SKILL.md where it is a symlink into dev. Not a write risk — kaizen-fix-author has no Edit tool.
#
set -euo pipefail

# --- resolve the instance root (the caller's cwd) and cd there ------------------------
#   This tool lives in <CORE>/tools/ and is shared across instances, so it CANNOT derive its
#   instance from its own location — a centralized core serves many. The instance is the
#   caller's cwd; --instance-root overrides. The cd is load-bearing: `claude --bg` inherits
#   THIS shell's cwd, and the run resolves its paths and its commit --repo against it.
#   HOST_ROOT is set only from a satellite: the host whose core it binds, read off the absolute
#   CORE= in the satellite's .env. From the host itself it stays empty, and nothing is added.
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
# HOST_ROOT is the instance whose core this one binds: the parent of the absolute `CORE=` in the
# instance's own `.env` (shared_core_instance.md § What is shared). An instance that carries its own
# core binds it relatively, or not at all, and is its own host, so nothing is added for it.
HOST_ROOT=""
core_binding="$(python3 "$SCRIPT_DIR/env_file.py" "$INSTANCE_ROOT/.env" CORE 2>/dev/null || true)"
case "$core_binding" in
  /*) HOST_ROOT="$(cd "$core_binding/.." 2>/dev/null && pwd || echo "")" ;;
esac

# NOTIFIER carries no host-global default — a core tool must not hard-code a machine-local
# notifier path (kensaiapp_structure.md § core/tools); it comes from KENSAIAPP_NOTIFIER (or the
# override), and the ping is skipped when unset. WATCHER sits beside this script in <CORE>/tools.
WATCHER="${LAUNCH_AUTHOR_WATCHER:-$SCRIPT_DIR/watch_agent.py}"
NOTIFIER="${LAUNCH_AUTHOR_NOTIFIER:-${KENSAIAPP_NOTIFIER:-}}"
RESOLVER="${LAUNCH_AUTHOR_RESOLVER:-$SCRIPT_DIR/skill_path.py}"

# The shared completion-watch home — the second core-relative path this launcher resolves,
# at the same real depth as WATCHER above. No env override: unlike $WATCHER, no test or
# caller ever wants a stub in its place, only the real file at its real relative depth.
DETACH_LIB="$SCRIPT_DIR/detach_watcher.sh"

# The one reader of the provider file — same real depth, and no env override: no caller may point
# a launch at another file.
PROVIDERS_TOOL="$SCRIPT_DIR/providers.py"
RUN_INTELLIGENCE="$SCRIPT_DIR/run_intelligence.py"

die() { echo "launch-fix-author: $*" >&2; exit 1; }

# --- args ----------------------------------------------------------------------------
skill="${1:-}"
version=""
dry_run=""
settle=""
keep_awake=""
for a in "${@:2}"; do
  case "$a" in
    --dry-run)    dry_run=1 ;;
    --settle)     settle=1 ;;
    --keep-awake) keep_awake=1 ;;
    *) version="$a" ;;
  esac
done
[ -n "$skill" ] || die "usage: launch-fix-author.sh <skill> [version] [--settle] [--dry-run] [--keep-awake]"

# --- the provider: this launcher's entry in .providers.toml at the instance root ---
#   Read before the skill is looked at and above the --settle split, so one entry governs both
#   modes, a launch the file cannot serve is refused before anything is resolved, and a dry run is
#   refused exactly where the launch would be.
#   The reader only runs Claude here: it is asked to accept `claude` and refuses any other entry
#   by name. No force is read — an exported KENSAIAPP_AGENT_PROVIDER is ignored. The key is this
#   script's own name as a literal, never derived from its basename, since the script may be run
#   from another folder. `providers.py` imports the intelligence resolver, so both are checked
#   before the reader is run.
[ -f "$PROVIDERS_TOOL" ] || die "no provider reader at $PROVIDERS_TOOL"
[ -f "$RUN_INTELLIGENCE" ] || die "no intelligence resolver at $RUN_INTELLIGENCE"
provider_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-fix-author-provider.XXXXXX")"
provider="$(python3 "$PROVIDERS_TOOL" launcher launch-fix-author --instance-root "$INSTANCE_ROOT" --accept claude \
  2>"$provider_err")" && rc=0 || rc=$?
provider_msg="$(cat "$provider_err")"
rm -f "$provider_err"
[ "$rc" -eq 0 ] || die "${provider_msg:-could not read the provider for launch-fix-author}"

resolved_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-resolve-err.XXXXXX")"
resolved="$(python3 "$RESOLVER" "$skill" --root "$INSTANCE_ROOT" 2>"$resolved_err")" && rc=0 || rc=$?
case $rc in
  0) skill_dir="$resolved" ;;
  3) die "no skill at $INSTANCE_ROOT (is '$skill' a real skill?)" ;;
  4) die "'$skill' is ambiguous — $(cat "$resolved_err")" ;;
  *) die "usage: launch-fix-author.sh <skill> [version] [--settle] [--dry-run] [--keep-awake]" ;;
esac
rm -f "$resolved_err"
evidence="$skill_dir/evidence"
[ -d "$evidence" ] || die "no evidence vault at $evidence — nothing has been audited for '$skill'"

# --- resolve the version -------------------------------------------------------------
#   No version given: the newest evidence/v*/ that actually holds an audit.md. Sorted numerically by
#   component (python3, not `sort -V`, which is GNU and unreliable on macOS) so v3.17.0 beats v3.4.0 —
#   a lexical sort gets that pair backwards, which is the whole reason this is not a one-line `ls | tail`.
if [ -z "$version" ]; then
  version="$(python3 -c "
import os,re,sys
root=sys.argv[1]
cand=[]
for d in os.listdir(root):
    m=re.fullmatch(r'v(\d+)\.(\d+)\.(\d+)', d)
    if m and os.path.isfile(os.path.join(root,d,'audit.md')):
        cand.append((tuple(int(g) for g in m.groups()), d[1:]))
print(max(cand)[1] if cand else '')
" "$evidence")"
  [ -n "$version" ] || die "no evidence/v*/ under $evidence holds an audit.md — audit a round first"
fi
version="${version#v}"

round_dir="$evidence/v$version"
audit="$round_dir/audit.md"
packet="$round_dir/fix_packet.md"
answers="$round_dir/owner_answers.md"

[ -f "$audit" ] || die "no audit at $audit — that round has not been audited"

# --- the packet guard, one condition read both ways ----------------------------------
#   Default: a packet may already be approved, or already applied. Overwriting one silently would
#   destroy an owner adjudication. Overriding is deleting the file yourself: deliberate, not a flag.
#   --settle: the same fact, inverted — there is nothing to settle without one.
packet_state() {
  grep -m1 -E '^\*\*State:\*\*' "$1" | sed -E 's/^\*\*State:\*\*[[:space:]]*//; s/[[:space:]]*$//' || true
}

if [ -z "$settle" ]; then
  if [ -f "$packet" ]; then
    st="$(packet_state "$packet")"
    die "a packet already exists at $packet (State: ${st:-unstated}). If the owner has answered it, settle it: --settle. Delete it yourself only if you mean to re-author from scratch — this will not overwrite one."
  fi
else
  [ -f "$packet" ] || die "no packet at $packet — nothing to settle. Author one first (drop --settle)."
  [ -f "$answers" ] || die "no owner answers at $answers — settling folds the owner's answers in, so there is nothing to do without them. Stamp one from <CORE>/templates/owner_answers_template.md."
  st="$(packet_state "$packet")"
  [ "$st" = "awaiting-owner" ] || die "packet State is '${st:-missing}', not 'awaiting-owner' — settling an approved packet would re-open a gate the owner already closed (fix_packet.md § State). Not launching."
fi

# --- report (READ-ONLY; never passed into the run) -----------------------------------
#   The run reads the audit itself; these lines are just for you.
if [ -n "$settle" ]; then
  entries="$(grep -c -E '^### E[0-9]+' "$packet" || true)"
  calls="$(grep -c -E '^### A[0-9]+' "$answers" || true)"
  echo "Fix author (settle): skill '$skill' round v$version"
  echo "            packet:  $packet (${entries:-0} entries, State: awaiting-owner)"
  echo "            answers: $answers (${calls:-0} adjudications answered)"
else
  findings="$(grep -c -E '^- \*\*(SG|CL)-' "$audit" || true)"
  echo "Fix author: skill '$skill' round v$version"
  echo "            audit:  $audit (${findings:-?} findings)"
  echo "            packet: $packet (to be written)"
fi

# --- build the launch command: FIXED prompt, only launcher-derived values interpolated -
#   It says which skill, which audit, and where the packet goes. Everything else — what a packet holds,
#   the State gate, the fix-or-rebuild call — is fix_packet.md's, which the agent's contract makes it
#   read. The launcher names none of it. The argv comes from the one adapter, never assembled here
#   (Task 18) — the pin was entered right after the CORE_DIR guard above.
if [ -n "$settle" ]; then
  prompt="settle the fix packet at ${packet} against the owner's answers at ${answers}."
else
  prompt="author the fix packet for the ${skill} skill from the audit at ${audit}. write it to ${packet}."
fi
claude_cmd=(python3 "$CORE_DIR/tools/agent_run.py" --provider "$provider" --shape background
  --pin auto --instance-root "$INSTANCE_ROOT" --prompt "$prompt" --agent kaizen-fix-author)
[ -n "$HOST_ROOT" ] && [ "$HOST_ROOT" != "$INSTANCE_ROOT" ] && claude_cmd+=(--add-dir "$HOST_ROOT")
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

# --- snapshot existing agent ids BEFORE launching -------------------------------------
#   The launched agent is identified by (name, cwd, id-not-seen-before). Name alone is ambiguous:
#   re-authoring the same round reuses the same fixed prompt. Captured before the launch, or the new
#   agent would be in its own exclusion set.
ids_before="$(python3 "$WATCHER" --list-ids --cwd "$INSTANCE_ROOT" 2>/dev/null || true)"

echo "Launching kaizen-fix-author (background)…"
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
    --label "$skill v$version" --log-stem "author-${skill}-v${version}" --reporter fix-author \
    --artifact-path "$packet" \
    --exclude-ids "$ids_before" \
    --launch-output "$launch_out" \
    --keepawake-poll-seconds "${LAUNCH_AUTHOR_KEEPAWAKE_POLL_SECONDS:-5}" \
    ${keep_awake:+--keep-awake}
else
  echo "          (no completion-watch library at $DETACH_LIB — completion watch skipped)"
fi
