---
name: development-security
description: >-
  Security review of a change's branch, after code integrity. It runs the NFDR's dependency audit and,
  on every run, the command-line scanners osv-scanner, Semgrep CE and gitleaks. It answers every
  advisory the audit or osv-scanner reports, even in dependencies the change never touched. It takes
  an allowed fix (a bump to the fixed release, a renamed identifier, a major bump only with the suite
  green), and for an advisory the product does not reach it writes an exception in the product's
  exception record, creating the first one when there is none and using a stated default window when
  the NFDR names none, with a row in the instance upkeep register. It reads the change's code with a
  lens adapted from Anthropic's security review and the OWASP lists, with what Semgrep and gitleaks
  found as candidates, fixes a hole when no record is edited, the suite stays green and nothing is
  redesigned, and reports the rest for the PM to decide on. Forbidden moves on what the product
  reaches are gathered and asked once, at the end. It always writes a committed security report whose
  first line says clean, fixed, reported or stopped, and which says what each scanner found. Halts
  outside a senior-engineer session or the senior-engineer subagent.
when_to_use: >-
  Run on a change's branch once its code-integrity step has passed, or when asked for a security review
  of a change unit. Trigger phrases are "security review of the change", "run the security step",
  "audit the dependencies on this branch", "development-security". Do not use for proving code against
  its intent (development-code-integrity), for deciding what to do about what the review left (the
  PM's), for security review of the definition documents, or for sealing a change (tobiishi-seal).
license: MIT
metadata:
  author: Eyal Golan
  version: "1.4.0"
  created: "2026-10-23"
  category: execution
  tags: security, dependencies, advisories, review, senior-engineer, pipeline
  risk: safe
---

# Development Security

## Purpose

Review a change's branch for security before it is sealed, and **repair what may be repaired, report
the rest**:

- **Dependencies.** Every advisory the product's dependency audit or `osv-scanner` reports is answered
  on the change's branch, so the repair reaches `main` at the seal — fixed where the rules allow;
  excepted where the product does not reach it, even when its only fix is forbidden (creating the
  product's first exception record if it has none, under the NFDR's window or a stated default); a
  question for the owner where it is reached and its only fix is forbidden; or reported for the PM
  where it is reached and has no fix.
- **The scanners.** `osv-scanner`, Semgrep CE and `gitleaks` run on every run, beside the NFDR's audit
  and never in place of it. Semgrep's and `gitleaks`' findings are candidates for the code review, and
  the report says what each scanner found, including when it found nothing.
- **The code.** A hole in the change's code — or one already on `main` that its trace passes through —
  is fixed when the fix edits no ADR and no product record, keeps the suite green, and needs no
  redesign; otherwise it is reported for the PM.
- **Forbidden moves** — a fix that would edit a record, or that a record blocks, on a reached advisory
  or a hole — are gathered while everything else is done, and the run stops once at the end with all
  of them as questions for the owner.

**The PM reads what is left** — unfixed holes, reached advisories with no fix, a dependency audit that
did not run, a scanner that did not run, an exception under the default window or one the audit does
not read, anything the review could not do — and decides what to do with it. This skill does not
decide it, and nothing it leaves holds the seal.

**This file is the orchestrator.** It owns the posture gate, resolving the change's worktrees, the
order of the steps, the suite call, the report's file and verdict line, and the commits. It makes no
security judgment.

**The method is `prompts/rich.md`** — the one body this file points at. Read it in full before Step 2
and apply it, with `<CORE>/prompts/senior_engineer_repair_dependencies.md`, which its dependency half
points at and `dependency-repair` shares. Between them: the edge of a repair, which audit command runs,
the three scanners and what each one covers, the rules a repair is held to (quoted there word for
word), the order in which an advisory is answered, the exception record and the upkeep row, the code
half's scope, threat lists, three phases, confidence floor, exclusions and hole fixes, what every hole
carries, how forbidden moves wait for the end, and what the run never does all live there. None of it
is repeated here.

**Announce at start:** "I'm using the development-security skill to review this change's branch for
security."

## Posture

**Senior Engineer only.** Run in a `senior-engineer` session or as the `senior-engineer` subagent.
Invoked from anywhere else, halt at once, say the posture is wrong, and name the way in — open a
session with the `senior-engineer:` prefix, or run the `senior-engineer` subagent. The seat's contract
is `<CORE>/roles/loaders/senior_engineer_global.md`.

The gate is here because the run writes and commits with nobody answering
(`<CORE>/doctrine/setup/authoring_layers.md` § *A skill that acts unattended gates to its seat*).

## Input

**The project** — `system/projects/<project>/` — and **the change's key**. Everything else is resolved
from those two.

**A relaunch after a stop** takes up only the questions the last report listed, with the owner's
answers: everything else is already done and committed.

## The work, in order

Do all allowed work first. A forbidden move met in Step 2 or Step 3 is noted as a question and the run
carries on; the stop, if there is one, comes in Step 4.

### 1. Resolve the change

Resolve the change's path contract once, as `development-code-integrity` does:

```sh
"<CORE>/tools/locked_python.sh" "<CORE>/tools/development_path.py" resolve --format json \
  --worktree "$WORKTREE" --project <project> --key <key>
```

`$WORKTREE` is the change's instance worktree on branch `<key>`, never the main checkout. The contract
names the `code_worktree` (the product's code — the instance worktree for a product inside the
instance, the product's own worktree for one in its own repo) and the `pipeline_worktree` (the change's
records). Read the product path from `project.md`, and the product's `docs/nfdr.md` under it. A product
with no NFDR is read as one that names no audit, no window and no threat classes.

### 2. The dependencies — `prompts/rich.md` § *Half 1*

1. Find the audit command the NFDR names. **None named** → note it for the report. `osv-scanner` still runs (item 3).
2. Make `<scratch>`, a folder made with `mktemp -d` outside both worktrees. Run the audit in the `code_worktree`, over the whole resolved set, with its standard output and its standard error each captured to its own file in `<scratch>`. Give both files to `normalise`, and keep its list and the audit's output. The call is the shared file's § *The bookkeeping goes through one tool*. A command that cannot run, or output that `normalise` refuses, is not a stop: note why for the top of the report and go on to item 3.
3. **`osv-scanner`, on every run** — `prompts/rich.md` § *The three scanners*. Find every lockfile or manifest that resolves the product's own dependencies, and none that belongs to another product in the same repository. **None found** → its bullet reads `found no dependency set to scan`, and `osv-scanner` is not started. Otherwise print its version, then run it in the `code_worktree` with one `--lockfile` for each of those files, and never over a directory:

```sh
osv-scanner --version
osv-scanner scan source --format json --lockfile "<file>" \
  > "<scratch>/osv-scanner.out" 2> "<scratch>/osv-scanner.err"
```

   Exit 0 and exit 1 are both a finished scan. Give its two files to `normalise`, reading them as a scan:

```sh
"<CORE>/tools/locked_python.sh" "<CORE>/tools/security_bookkeeping.py" normalise --from osv-scanner \
  --stdout "<scratch>/osv-scanner.out" --stderr "<scratch>/osv-scanner.err"
```

   Keep its list beside the audit's. Any other exit, or output that `normalise` refuses, is a scanner that did not run: note why for the report and go on.
4. Answer every advisory in the two lists in the shared file's order — *not reached* is decided before *forbidden*. One advisory id against one package takes one answer, even when both lists hold it. Find the advisories already excepted with `find-lapsed`. Make the fixes in the `code_worktree`. Write each exception through the tool, in this order: `lapse-date` for its lapse date; `write-record entry`, or `write-record renewal`, at the record the NFDR's *Advisory exception record* line names, or `checks/deps/advisory_exceptions.toml`, which `write-record entry` creates when the product has none; then `write-upkeep` for its row in `system/upkeep.md` in the `pipeline_worktree`, which the tool creates when the instance has none. Check that the audit reads that record. A refusal from the tool is never made up for by hand: the shared file says what the report does with it. Once every advisory is answered, remove `<scratch>` (`rm -rf "<scratch>"`, in a command of its own).
5. **A major bump** is kept only on a green suite (§ *The suite*).
6. Re-run the audit after the fixes, and keep that output too: the report states what the audit says once the repairs are in.
7. Commit (§ *Commit*, the `dependencies` row).

### 3. The code — `prompts/rich.md` § *Half 2*

First run Semgrep CE and `gitleaks` — `prompts/rich.md` § *The three scanners*. Make a new `<scratch>` with `mktemp -d`, outside both worktrees. Each scanner reads the product path and every file the change's diff touches outside it, as they stand in the `code_worktree`. Print each one's version first:

```sh
semgrep --version
semgrep scan --config p/default --metrics=off --json --output "<scratch>/semgrep.json" \
  "<product path>" "<touched file>"
```

```sh
gitleaks version
gitleaks dir "<path>" --redact --no-banner --report-format json \
  --report-path "<scratch>/gitleaks-<n>.json"
```

Run `gitleaks` once for each path: the product path, and each touched file outside it. Never run `semgrep ci` or `semgrep login`, which want a token. Semgrep's run is finished when it exits 0. A `gitleaks` exit of 1 means it found something, not that it failed. Any other exit, or a report that cannot be read, is a scanner that did not run: note why for the report and go on. Read what each scanner found as candidates for the three phases below, then remove `<scratch>` (`rm -rf "<scratch>"`, in a command of its own).

Read the change's diff in the `code_worktree` — `git -C "<code_worktree>" diff main...HEAD` and every
file it touches — and apply the prompt's three phases and its sceptical pass. Fix each hole within the
edge, each kept only on a green suite (§ *The suite*), and report the rest. Commit the fixes (§ *Commit*,
the `holes` row).

### 4. Write the report, commit, and stop if a question is owed

Write `security-report.md` (§ *The report*), then check its verdict line with the tool:

```sh
"<CORE>/tools/locked_python.sh" "<CORE>/tools/security_bookkeeping.py" check-verdict \
  --report "<pipeline_worktree>/system/projects/<project>/journey/tobiishi/<key>/security-report.md"
```

Where the tool refuses the line, correct it to the bare form § *The report* gives and check again. The
report is never committed with a verdict line the tool refuses. Then commit it with any upkeep rows
(§ *Commit*, the `report` row). Where the report lists a question for the owner, the run ends
`Security: stopped`.

### The suite

A major bump and a hole fix are each kept only on a green suite run after it. Run the suite through the
gate tool, never by hand: read `<CORE>/prompts/gate_suite.md`, build its evidence file, and issue

```sh invocation
"<CORE>/tools/locked_python.sh" "<CORE>/tools/gate_suite.py" run \
  --worktree "<instance change worktree>" --project "<project>" --key "<key>" \
  --gate code-integrity --inputs "<inputs file>" \
  > "<output file>" 2> "<error file>"
```

The tool has no gate of this step's own; `code-integrity` is the step this one follows, and a gate
other than `seal` changes nothing about how the suite runs. The chain runs this skill as its `security`
step and added no `security` gate to the tool. Copy each `Environment:` line it printed
into the report as a bullet, never as a bare line. A red or refused run means the change it was proving
is undone and reported for the PM.

## The report

Write `system/projects/<project>/journey/tobiishi/<key>/security-report.md` in the
`pipeline_worktree`, beside the change's `code-integrity-report.md`, on every outcome. **Its reader is
the PM**, who decides what to do with whatever it leaves. Use exactly this shape:

```markdown
# Security report

Security: <clean | fixed | reported | stopped>

## Why the run stopped
<stopped on forbidden moves: one question per move — the reached advisory or the hole, the move it
needs, the record that forbids it, and what would be done if allowed. Stopped because the change could
not be resolved: what the resolve call said. Otherwise: none.>

## Left for the PM
<first, when it did not run: "The dependency audit did not run: <why>." Then, for each scanner that did not run: "<tool> did not run: <why>." Then every hole and advisory left unfixed, each exception under the default window ("default window used — raise it into the NFDR"), each exception the audit does not read ("wire the audit to honor the exception record"), and anything else the review could not do, one line each with where it is detailed below. Otherwise: none.>

## Dependency audit
<the command, cited to the NFDR line that names it, where it ran, and what it reported before and
after the repairs; or: skipped — the NFDR names no dependency audit; or: did not run — why.>

## Scanners
- osv-scanner: <version> — <what it found>
- Semgrep CE: <version> — <what it found>
- gitleaks: <version> — <what it found>
<exactly these three bullets, in this order. After the version each one says exactly one of: found
nothing; "<n> findings, <k> counted", then ", listed in `## Advisories`" or ", listed in `## Holes
in the code`" when one or more is counted; for osv-scanner only, found no dependency set to scan;
or did not run — why. A scanner that did not run and printed no version reads "- <tool>: did not
run — <why>". A gitleaks finding is named by file, line and rule id, never by what it matched.>

## Advisories
| Advisory | Dependency | Reported by | Answer | What was done | Commit |
|---|---|---|---|---|---|
<one row per advisory: reported by the audit · osv-scanner · both; answered fixed · excepted ·
question for the owner · reported for the PM; an existing exception that holds is a row too. One
advisory id against one package is one row. "none" when neither the audit nor osv-scanner reported
one.>

## Exceptions and upkeep rows
<each exception written, renewed or removed: the record and entry, its reason, its window and lapse
date, whether the audit reads the record, and the upkeep row. Say "record created" when the run created
the product's exception record, "default window used" when the NFDR named none, and "register created"
when it created `system/upkeep.md`. Otherwise: none.>

## Holes in the code
<each hole as `prompts/rich.md` § *What every hole carries* lists it, High first, each fixed or
reported for the PM. Otherwise: none — and the threat lists that were applied, so "none found" reads
differently from "never looked".>

## Not checked
<everything the review could not cover and why: an audit that was skipped or could not run, a scanner that did not run, a file it could not read, a suite that would not run. Otherwise: none.>
```

**The verdict line is bare**, the first line after the title, and takes one of four values,
lower-case, the first that applies:

| Value | When |
|---|---|
| `stopped` | the report lists a question for the owner, or the change could not be resolved |
| `reported` | something is left for the PM: an unfixed hole, a reached advisory with no fix, a dependency audit that did not run or that the NFDR does not name, a scanner that did not run, an exception under the default window, or one the audit does not read. `osv-scanner` is not an audit the NFDR does not name. It runs on every run, and running it does not by itself make the run `reported` |
| `fixed` | the run fixed or excepted something, and nothing is left |
| `clean` | nothing to fix, nothing left |

No heading, bullet, quote or table cell around it: a later reader takes it by its literal prefix.

## When to stop

The run ends `Security: stopped` — after all allowed work is done and committed, with the report
saying why — only when:

- one or more fixes on a reached advisory or a hole need a **forbidden move** (an ADR or a product
  record other than the exception record edited, or a fix a record blocks): every one is a question in
  the report's one list;
- the **change cannot be resolved** — no path contract for the project and key. This one stops at
  once, since nothing else can be done.

An audit that cannot run, a scanner that cannot run, a hole that cannot be fixed within the edge, a reached advisory with no fix, an NFDR that names no audit or no window, an exception the audit does not read, and a missing exception
record or upkeep register are **not** stops: they are reported for the PM, or created, and the verdict
says so. The report's *Why the run stopped* section states the reason for either stop.

## Commit

Commit through the shared builder — read `<CORE>/doctrine/governance/commit_via_builder.md` and supply
its variables: `<repo>` per commit (below), the files each commit carries, subject and body,
**`--actor senior-engineer`** (name it, never derive it), `--skill development-security`, and the
directional resolved as that file says. Never hand-write `git commit` or a trailer.

| Commit | Lands in | Carries |
|---|---|---|
| `security: <key> — dependencies` | `code_worktree` | the lockfile and pin bumps, the renamed identifiers, and the exception record's entries (or the record created). Only when Step 2 changed anything |
| `security: <key> — holes` | `code_worktree` | the hole fixes. Only when Step 3 fixed anything |
| `security: <key> — report` | `pipeline_worktree` | `security-report.md` and the `system/upkeep.md` rows (or the register created). Every run |

For a product inside the instance the two worktrees are one, and the commits land there in that order.
For a product in its own repo they are two repos, and each commit stages only its own repo's files. All
commit on the change's branch, never on `main`; the seal carries them there.

## Critical rules

- **Fix every advisory the rules allow**, on the change's branch, including one in a dependency the
  change never touched.
- **Fix a hole only within the edge** — no ADR or product record edited, the suite green, no
  redesign — and report the rest for the PM.
- **Except an unreached advisory** with no allowed fix, even when its only fix is forbidden, creating
  the product's first exception record when it has none, under the NFDR's window or the stated
  default, with an upkeep row; where the audit does not read the record, report it for the PM.
- **Never take a forbidden move** — gather every one on a reached advisory or a hole, do all other
  work, then stop once with one question per move.
- **The audit is the NFDR's**; with none named, or one that cannot run, the rest still runs and it is reported. `osv-scanner` running on every run is this skill's own departure from the shared file's audit rule (`prompts/rich.md` § *The three scanners*).
- **Run the three scanners on every run** — `osv-scanner`, Semgrep CE and `gitleaks`, beside the NFDR's audit and never in place of it. A scanner that cannot run is reported, and the rest still runs.
- **Answer `osv-scanner`'s advisories as the audit's** — the same four answers in the same order, the bookkeeping through the tool, and one answer for one advisory id against one package.
- **A Semgrep or `gitleaks` finding is a candidate**, and it counts as a hole only when the sceptical pass keeps it.
- **Never show a secret** — a `gitleaks` finding is named by file, line and rule id, and no line of the report quotes what it matched.
- **The PM decides what to do with what is left**; this skill neither decides it nor holds the seal.
- **Never call a built-in security-review command**; the lens is `prompts/rich.md`, read the same way
  on every provider.
- **Always write and commit `security-report.md`**, with its bare verdict line, on every outcome.
