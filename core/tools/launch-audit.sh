#!/usr/bin/env bash
#
# launch-audit.sh — deterministic, pollution-proof launcher for a kaizen-audit run over one
# snapshotted evidence round of any skill, chaining fail-closed into launch-fix-author.sh.
#
# Version: 1.8.1 — launchers and launch scripts take a portable mktemp template, so they run on Linux
# Version: 1.8.0 — public-repo 0.x gates 1, 3, 4, 6 — Apache-2.0 licence lines, no satellite/product/host name or machine path shipped, no default notifier, loopback-only telemetry
# Version: 1.7.0 — the providers file lives in the instance — each instance reads its own .providers.toml, and a tracked .providers.toml.example is the template
# Version: 1.6.0 — a pinned run sees only its own skill group
# Version: 1.5.0 — the tool launchers read the central file — launch-apply-packet, launch-audit and launch-fix-author take their provider from providers.toml
# Version: 1.4.0 — a run keeps the version it started on — every launcher enters a pin of core/, .claude/ and skills/
# Version: 1.3.0 — companion-answer and kaizen-audit move to the interactive group, and the audit launcher grants that group to the run it starts
# Version: 1.2.1 — chain-definition, chain-foundation and the eight product document launchers are retired into chain-product and the skill launcher
# Version: 1.2.0 — the resolver capture no longer folds stderr into the value that becomes
#   $skill_dir (was `2>&1`; a future resolver warning on a successful exit would have landed
#   INSIDE the path). Standard error is captured to its own temp file instead, read back only for
#   the ambiguous (exit 4) message, which is what it always fed. $RESOLVER also gains an env
#   override, LAUNCH_AUDIT_RESOLVER, the seam a test needs to stand a stub resolver on this path.
# Version: 1.1.0 — the foreground watch is now told which run it is watching. This launcher
#   builds its own `watch_args` rather than delegating a detach block, so it sources the shared
#   library for one function — `capture_agent_id` — and appends --agent-id when the launch line
#   could be read. Sourcing that library has no side effect of its own. The launch output is
#   redirected to a file rather than captured through a pipe, which waits for end-of-file and
#   would block on the detached run.
# Version: 1.0.1 — comment: the retired launch-cold-read.sh is no longer a pointer anyone can follow;
#   the surviving cold-read entry is <CORE>/launchers/cold-read/launcher.sh.
#
# WHY THIS EXISTS
#   Same reason as its siblings (launch-fix-author.sh, launch-apply-packet.sh, and
#   <CORE>/launchers/cold-read/launcher.sh): a session asked to "audit this round" composes the auditor's prompt,
#   and that is the one place stray context leaks in (which findings you think matter, a prior
#   round's summary, "and while you're there…"). The prompt below is a FIXED literal — a caller
#   passes only a skill name and, optionally, a version. Nothing a caller types reaches the run.
#
#   It restates none of kaizen-audit's doctrine — what a lens is, how the auditor fan-out works,
#   what belongs in audit.md. It enforces the outputs-only input set purely by what it interpolates
#   into the fixed prompt: the skill name, the resolved round dir, the prior round dir (when one
#   exists), and the surfacing fact — never a path under the audited skill's own producing stack
#   (its SKILL.md, its authoring prompt, its templates, its loader).
#
# WHERE IT RUNS
#   In the producer satellite: the evidence it reads and the audit.md it hands off both live there.
#   Authored in the host — the upstream tip — and copied to the producer, matching system/tools/'s
#   vendored pattern (same as launch-fix-author.sh).
#
# WHICH ROUND
#   Round resolution — newest un-audited evidence/v*/, an explicit-version override, and the
#   prior round for the cross-version comparison passes — is NOT inlined here: it is pure logic,
#   worth testing on its own, and lives in the auditrun/ package beside this script (the
#   coldread/-package idiom). This script delegates to auditrun.resolve_target and converts its
#   AuditRoundError to a die() before any run launches. Bash keeps only the cheap existence
#   guards (skill dir, evidence vault) that don't need the round listing.
#
# WHY THE WATCH RUNS FOREGROUND, UNLIKE THE DETACH-AND-RETURN SIBLINGS
#   launch-fix-author.sh detaches its completion watcher and returns at once — its job ends at
#   launch. This launcher's job does not: it must ACT once
#   the run reaches a terminal state (chain into launch-fix-author.sh, or halt+notify), so it runs
#   the watch to a terminal state before returning, so its exit code reflects that outcome. There
#   is no --wait flag here
#   because there is no other mode: this launcher always needs to act after the run stops.
#
#   The chaining decision reads round_dir/audit.md — the artifact — never the watched agent's own
#   state (a `stopped` state means both a clean halt and a run that never got going; only the file
#   the run was asked to write says what happened). --keep-awake follows from the same shape: it
#   holds caffeinate ACROSS this foreground watch (there is no detached watcher PID to bind to,
#   unlike the detach-and-return siblings) — guarded by `command -v caffeinate`, noting and
#   continuing when absent (non-macOS).
#
# USAGE
#   <CORE>/tools/launch-audit.sh <skill> [version] [--dry-run] [--instance-root <dir>]
#                                 [--keep-awake] [--audit-only] [--surfaces-owner-work]
#                                                                       (run from the instance root)
#     <skill>                a skill with an evidence vault, e.g. product-prd
#     [version]              e.g. 3.17.0 — omitted means the NEWEST evidence/v*/ with no audit.md
#     --dry-run               print the exact claude command, but do not launch
#     --instance-root <dir>   override the instance root (default: cwd)
#     --keep-awake            keep the Mac awake (caffeinate) across the foreground watch
#     --audit-only             stop after the audit lands — never chain into launch-fix-author.sh
#     --surfaces-owner-work   this round's evidence surfaces the owner's own work (never inferred
#                             from the evidence itself — a caller-supplied fact only)
#
# PERMISSIONS
#   --permission-mode auto — REQUIRED. Nobody can answer a permission prompt in a --bg run, so a
#   prompt is not a pause: it is a run that stops forever. `auto` puts a classifier on each Bash
#   call; deny and ask rules still apply. NOT a bypass and NOT --dangerously-skip-permissions — see
#   ~/.claude/CLAUDE.md § Permission mode and the fuller note in
#   core/launchers/companion-self-answer/launcher.sh.
#   Use --bg, NOT -p/--print (--print never starts the session `claude agents` attaches to).
#
#   --add-dir on the dev repo covers what the run reads outside this instance: <CORE> doctrine,
#   and the kaizen-audit SKILL.md where it is a symlink into dev. kaizen-audit's own group, when
#   the skill resolves grouped, now reaches the run through the pin's plugin instead of a second
#   --add-dir this launcher used to pass.
#
# THE FAIL-CLOSED HANDOFF
#   `audit.md` present and NOT --audit-only  -> invoke launch-fix-author.sh <skill> <version>
#                                                (its own packet-exists guard is the second gate)
#   `audit.md` absent                        -> notify (when a notifier is set) + exit non-zero;
#                                                no fix-author
#   --audit-only                             -> stop after the audit even when audit.md landed;
#                                                exit zero; no fix-author
#
set -euo pipefail

# --- resolve the instance root (the caller's cwd) and cd there ------------------------
#   This tool lives in <CORE>/tools/ and is shared across instances, so it CANNOT derive its
#   instance from its own location — a centralized core serves many. The instance is the
#   caller's cwd; --instance-root overrides. The cd is load-bearing: `claude --bg` inherits
#   THIS shell's cwd, and the run resolves its paths against it.
#   HOST_ROOT is set only from a satellite: the host whose core it binds, read off the absolute
#   CORE= in the satellite's .env. From the host itself it stays empty, and nothing is added.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # <CORE>/tools — auditrun/ + the fix-author sibling sit beside this
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
WATCHER="${LAUNCH_AUDIT_WATCHER:-$SCRIPT_DIR/watch_agent.py}"
# Sourced for ONE function. This launcher's watch runs foreground and it builds its own
# `watch_args`, so it has no detach block to delegate — but the id `claude --bg` prints at launch
# is read the same way here as everywhere else, and `capture_agent_id` is where that parse lives.
# Sourcing the library has no side effect of its own (its own header states that, and
# `test_detach_watcher.py` proves it), so taking the one function costs nothing.
DETACH_LIB="${LAUNCH_AUDIT_DETACH_LIB:-$SCRIPT_DIR/detach_watcher.sh}"
NOTIFIER="${LAUNCH_AUDIT_NOTIFIER:-${KENSAIAPP_NOTIFIER:-}}"
RESOLVER="${LAUNCH_AUDIT_RESOLVER:-$SCRIPT_DIR/skill_path.py}"

# The one reader of the provider file — same real depth, and no env override: no caller may point
# a launch at another file.
PROVIDERS_TOOL="$SCRIPT_DIR/providers.py"
RUN_INTELLIGENCE="$SCRIPT_DIR/run_intelligence.py"

die() { echo "launch-audit: $*" >&2; exit 1; }

# --- args ----------------------------------------------------------------------------
skill="${1:-}"
version=""
dry_run=""
keep_awake=""
audit_only=""
surfaces_owner_work=""
for a in "${@:2}"; do
  case "$a" in
    --dry-run)               dry_run=1 ;;
    --keep-awake)            keep_awake=1 ;;
    --audit-only)            audit_only=1 ;;
    --surfaces-owner-work)   surfaces_owner_work=1 ;;
    *)                       version="$a" ;;
  esac
done
[ -n "$skill" ] || die "usage: launch-audit.sh <skill> [version] [--dry-run] [--instance-root <dir>] [--keep-awake] [--audit-only] [--surfaces-owner-work]"

# --- the provider: this launcher's entry in .providers.toml at the instance root ---
#   Read before the skill is looked at, so a launch the file cannot serve is refused before
#   anything is resolved, and a dry run is refused exactly where the launch would be. Only this
#   launcher's own entry is read: the fix author it chains into reads its own, at its own start.
#   The reader only runs Claude here: it is asked to accept `claude` and refuses any other entry
#   by name. No force is read — an exported KENSAIAPP_AGENT_PROVIDER is ignored. The key is this
#   script's own name as a literal, never derived from its basename, since the script may be run
#   from another folder. `providers.py` imports the intelligence resolver, so both are checked
#   before the reader is run.
[ -f "$PROVIDERS_TOOL" ] || die "no provider reader at $PROVIDERS_TOOL"
[ -f "$RUN_INTELLIGENCE" ] || die "no intelligence resolver at $RUN_INTELLIGENCE"
provider_err="$(mktemp "${TMPDIR:-/tmp}/launch-audit-provider.XXXXXX")"
provider="$(python3 "$PROVIDERS_TOOL" launcher launch-audit --instance-root "$INSTANCE_ROOT" --accept claude \
  2>"$provider_err")" && rc=0 || rc=$?
provider_msg="$(cat "$provider_err")"
rm -f "$provider_err"
[ "$rc" -eq 0 ] || die "${provider_msg:-could not read the provider for launch-audit}"

resolved_err="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-resolve-err.XXXXXX")"
resolved="$(python3 "$RESOLVER" "$skill" --root "$INSTANCE_ROOT" 2>"$resolved_err")" && rc=0 || rc=$?
case $rc in
  0) skill_dir="$resolved" ;;
  3) die "no skill at $INSTANCE_ROOT (is '$skill' a real skill?)" ;;
  4) die "'$skill' is ambiguous — $(cat "$resolved_err")" ;;
  *) die "usage: launch-audit.sh <skill> [version] [--dry-run] [--instance-root <dir>] [--keep-awake] [--audit-only] [--surfaces-owner-work]" ;;
esac
rm -f "$resolved_err"
evidence="$skill_dir/evidence"

[ -d "$evidence" ] || die "no evidence vault at $evidence — nothing has been audited for '$skill'"

# --- resolve the round + its prior via auditrun.resolve_target ------------------------
#   The listing, the numeric-component ordering, the un-audited/explicit-version selection, and
#   both guards (nothing-to-audit, refuse-to-overwrite) all live in auditrun/rounds.py — pure
#   logic, tested on its own. Values cross the boundary as argv (never interpolated into the
#   Python source), so nothing here can inject through a caller-supplied version string. A
#   quoted heredoc (<<'PY') keeps the script text itself free of shell expansion.
if ! resolve_out="$(python3 - "$SCRIPT_DIR" "$evidence" "$version" <<'PY'
import sys

script_dir, evidence_dir, explicit = sys.argv[1], sys.argv[2], sys.argv[3]
explicit = explicit or None
sys.path.insert(0, script_dir)
from auditrun.rounds import AuditRoundError, resolve_target

try:
    target = resolve_target(evidence_dir, explicit)
except AuditRoundError as exc:
    print(f"launch-audit: {exc}", file=sys.stderr)
    sys.exit(1)

print(target.version)
print(target.round_dir)
print(target.prior_dir or "")
PY
)"; then
  exit 1
fi

# bash 3.2 (macOS's system bash) has no `mapfile` — pull each line out by number instead. A
# trailing-newline-only line (an absent prior_dir) is indistinguishable from "no such line" once
# command substitution strips trailing newlines, which is exactly the `None` case we want.
_resolved_line() { printf '%s\n' "$resolve_out" | sed -n "${1}p"; }
version="$(_resolved_line 1)"
round_dir="$(_resolved_line 2)"
prior_dir="$(_resolved_line 3)"
audit="$round_dir/audit.md"

surfaces="no"
[ -n "$surfaces_owner_work" ] && surfaces="yes"

# --- report (READ-ONLY; never passed into the run) -----------------------------------
echo "Audit: skill '$skill' round v$version"
echo "       round: $round_dir"
[ -n "$prior_dir" ] && echo "       prior: $prior_dir"

# --- build the launch command: FIXED prompt, only launcher-derived values interpolated -
#   Names which skill, which round, which prior round (when one exists), and the caller-supplied
#   surfacing fact — nothing else. It runs the kaizen-audit SKILL (via the prompt), not an agent:
#   there is no `kaizen-audit` agent to pass to --agent — the skill fans out kensaiapp-auditor
#   itself. No path under the audited skill's own producing stack (SKILL.md, its authoring
#   prompt, templates, loader) is ever named here. The argv comes from the one adapter, never
#   assembled here (Task 18) — the pin was entered right after the CORE_DIR guard above. Its own
#   group, when kaizen-audit resolves grouped, reaches the run through the pin's plugin rather
#   than an --add-dir named here.
prompt="Run the kaizen-audit skill over the ${skill} skill's evidence round at ${round_dir}"
if [ -n "$prior_dir" ]; then
  prompt="$prompt, with the prior round at ${prior_dir} available for the cross-version comparison passes"
fi
prompt="$prompt. This run surfaces the owner's own work: ${surfaces}."

claude_cmd=(python3 "$CORE_DIR/tools/agent_run.py" --provider "$provider" --shape background
  --pin auto --instance-root "$INSTANCE_ROOT" --prompt "$prompt" --grant-skill kaizen-audit)
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
#   re-auditing the same round reuses the same fixed prompt. Captured before the launch, or the
#   new agent would be in its own exclusion set.
ids_before="$(python3 "$WATCHER" --list-ids --cwd "$INSTANCE_ROOT" 2>/dev/null || true)"

echo "Launching kaizen-audit (background)…"
# stdout is captured so the launched agent's id can be read off it, then echoed through unchanged
# so the caller still sees `claude`'s own attach/stop hints. Redirected to a FILE, never captured
# through a pipe: `$( … )` waits for end-of-file rather than for the command to exit, and
# `claude --bg` leaves a detached run holding the inherited descriptor.
launch_log="$(mktemp "${TMPDIR:-/tmp}/kensaiapp-launch-out.XXXXXX")"
"$@" >"$launch_log" 2>&1
launch_out="$(cat "$launch_log")"
rm -f "$launch_log"
printf '%s\n' "$launch_out"
agent_id=""
if [ -f "$DETACH_LIB" ]; then
  # shellcheck source=detach_watcher.sh
  source "$DETACH_LIB"
  agent_id="$(capture_agent_id "$launch_out")"
fi
echo "Launched. Watch/attach: claude agents        (interactive view — logs, stop, resume live here)"
echo "          Script it:    claude agents --json --all   (machine-readable run state)"

# --- the completion watch runs FOREGROUND — this launcher must act after the run stops -
#   Unlike the detach-and-return siblings, there is no --wait flag: acting after terminal is the
#   whole reason this launcher exists, so the watch always blocks here. Its own exit code is
#   deliberately ignored (`|| true`) — the chaining decision below reads round_dir/audit.md, the
#   artifact, never the watched agent's own state.
[ -f "$WATCHER" ] || die "no completion watcher at $WATCHER — the foreground block is load-bearing; cannot chain without it"

watch_args=(
  --name "$prompt"
  --label "audit $skill v$version"
  --cwd "$INSTANCE_ROOT"
  --exclude-ids "$ids_before"
  --reporter generic
)
# The exact handle, when the launch line could be read: given it, the watcher stops consulting
# the name entirely (`watch_agent.py:155`). Appended only when non-empty — an empty value reads
# as a falsy id there and would take this launcher off the fallback its name path still provides.
[ -n "$agent_id" ] && watch_args+=( --agent-id "$agent_id" )
[ -n "$NOTIFIER" ] && watch_args+=( --notify "$NOTIFIER" )

echo "          Watching:    foreground watch until the run stops…"
if [ -n "$keep_awake" ]; then
  if command -v caffeinate >/dev/null 2>&1; then
    echo "          Keep-awake:   caffeinate -i -s held across the foreground watch"
    caffeinate -i -s python3 "$WATCHER" "${watch_args[@]}" || true
  else
    echo "          (keep-awake: caffeinate not found — not macOS? — skipped)"
    python3 "$WATCHER" "${watch_args[@]}" || true
  fi
else
  python3 "$WATCHER" "${watch_args[@]}" || true
fi

# --- the fail-closed handoff: read the artifact, never the agent state ----------------
if [ -f "$audit" ]; then
  if [ -n "$audit_only" ]; then
    echo "Audit landed at $audit — --audit-only set, stopping before the fix author."
    exit 0
  fi
  echo "Audit landed at $audit — chaining into the fix author…"
  exec "$SCRIPT_DIR/launch-fix-author.sh" "$skill" "$version"
fi

echo "No audit at $audit — the run may not have completed the audit." >&2
exit 1
