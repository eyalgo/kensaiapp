---
version: "1.0.3"
---

# Shell — errors and logging

How a shell file here fails, and what it says while it works. How code is named and shaped the rest of
the time is `conventions.md`, per `languages/README.md` § The seven concerns.

Every measurement below was taken on 2026-08-23 over the twenty tracked bash files, except the four
restated on 2026-10-03 over the twenty-three that remain after the SDD runner's launcher was removed
(`git ls-files '*.sh' 'core/githooks/*'`) — each says so where it stands.

## `die` is the failure surface, and it has one shape

```sh
die() { echo "<identity>: $*" >&2; exit 1; }
```

**Sixteen of the twenty-three files define it (2026-10-03), and all sixteen definitions are
byte-identical apart from the identity string** — normalising the message away,
`git grep -h '^die()'` collapses to exactly one line. The identity is the file's own short name: `product-content:`, `cold-read:`, `launch-audit:`.

Three properties, all load-bearing:

- **The message goes to stderr.** `>&2` on every one. Ordinary output goes to stdout, so stderr is
  read as the failure channel: outside `die`, seven lines in the corpus use it, and six are failures
  too — two round-lock refusals, the library's three `return 1` messages, and one
  `echo … >&2; exit 1` pair at `core/tools/launch-audit.sh`. The seventh is the exception worth
  copying: `core/launchers/launch-skill-evals/launcher.sh` puts a *warning* there —
  "(could not read the agent id from the launch output — the next launch will NOT be blocked)" — a
  condition that does not end this run but changes what the next one does.
- **It exits 1.** The corpus uses exactly two exit values, `exit 0` (18 occurrences) and `exit 1` (19).
  There is no third status, and nothing encodes a reason in a number.
- **The prefix says which file is speaking.** A launcher's output is read in a terminal beside the
  output of whatever it launched, so an unprefixed error names nothing.

## A library returns; a script exits

`core/tools/detach_watcher.sh` defines no `die`. It reports on the same channel and with the same shape
— `echo "detach_completion_watcher: missing required $flag" >&2` — and then **`return 1`**, three times,
never `exit`. The prefix is the *function's* name rather than the file's, because the caller's own
identity is already on the line above.

**Its contract is that ordinary configuration never fails the caller**, and it states that itself:
"Neither branch ever `die`s or returns non-zero: a missing notifier or watcher is ordinary
configuration, and this function's whole reason to exist is that notification must never fail the
caller's primary launch. The one exception is the missing-required-flag case above, which is a caller
bug, not a runtime condition." That is the split to copy — **a caller's bug returns non-zero; an absent
piece of the environment does not.**

**A git hook adds no error surface of its own.** `core/githooks/commit-msg` and
`core/githooks/pre-commit` each `exec` a Python checker and let its status stand, saying so in the
header: "Performs no checking itself: execs the pure checker with git's message-file argument and exits
with the checker's exit code."

## A guard reports; it does not merely fail

**The form is `[ <condition> ] || die "<what was wrong, in resolved terms>"`** — 146 lines
carry `|| die` across the twenty-three tracked bash files (2026-10-03, `git grep -c -F '|| die'`
summed). The message names the value that failed, not the check that failed:

```sh
[ -f "$project_md" ] || die "no project card at $project_md (is '$project' a real project?)"
```

**`set -euo pipefail` would otherwise take the report away, so the corpus disarms the command and puts
the check on the next line.** Under `pipefail` a `grep` that matches nothing ends the script inside the
command substitution, before any guard can run — so the substitution carries `|| true` and the guard
follows it. `core/launchers/chain-product/launcher.sh` writes the reason on the guard line itself:
"`|| true` above: pipefail would otherwise exit before this guard reports". `2>/dev/null || true`
appears on 20 lines across the twenty-three tracked bash files (2026-10-03,
`git grep -c -F '2>/dev/null || true'` summed), always in that role.

**A precondition on the environment is checked before anything is launched, not where it is used.** The
skill launcher refuses at the top, once for each program the skill's `Requires:` names —
`command -v "$program" >/dev/null 2>&1 || die "$program not found on PATH — …"` — because the run it
starts is unattended and would otherwise reach the missing program with nobody there to answer.

## An optional tail is reported and skipped, never fatal

Once the primary action has happened, a later step that fails must not be reported as the primary action
failing. Three launchers state the rule in the same words (2026-10-03,
`git grep -l -F 'reported and skipped, never fatal' -- 'core/launchers/*/launcher.sh'`) above the
completion-watch block: "A missing
library is reported and skipped, never fatal — the primary run has already launched by the time this
block runs."

The skipped-step line is parenthesised, indented, and says which thing was missing:

```
          (no completion-watch library at $DETACH_LIB — completion watch skipped)
          (keep-awake: caffeinate not found — not macOS? — skipped)
```

**Each condition is checked and named independently.** `core/tools/detach_watcher.sh` carries the
canonical case and its reason: "An absent notifier is ordinary configuration (`KENSAIAPP_NOTIFIER`
unset); an absent watcher means the caller could not resolve its own path to shared machinery — a bug in
the launcher, not the environment. Conflating them sends the reader to the wrong end." The code is two
lines, one per condition, so both report when both are missing.

## There is no level ladder, and that is the answer rather than a gap

Nothing here emits a severity. `logger`, `syslog` and a `date`-stamped message line appear nowhere in
the corpus. What a shell file emits is three things:

1. **Human progress, to stdout, via `echo`.** The report block is a fixed two-column shape — a label
   padded to a common width, then the value: `Notifying:    when the $noun stops → …`,
   `Watcher log:  $log_file`, `Keep-awake:   caffeinate -i -s held until the $noun stops`. Continuation
   and secondary lines are indented ten spaces so the block reads as one thing.
2. **A failure, to stderr, via `die`** (§ above) — and, rarely, a warning that changes what a later
   run will do.
3. **The exact command, machine-shaped, under `--dry-run`.** `printf '  %q' "$@"` — the one place
   output is escaped for a machine rather than composed for a person, and the reason `--dry-run` is
   trustworthy is that it prints the same `$@` the real launch runs.

**The only file a shell script here writes is the detached watcher's log**, and one file owns that:
`core/tools/detach_watcher.sh` creates `system/logs/` and names the log
`watch-${log_stem}-$(date -u +%Y%m%d-%H%M%S).log`, UTC. The script itself writes no log of its own, and
nothing is emitted as JSON or any other structured form.

**A shell file that wants more than this has reached the boundary in `toolchain.md`** — the work crosses
to `python3`, which is where structured output and anything resembling a level ladder belong.
