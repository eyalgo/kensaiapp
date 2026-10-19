#!/usr/bin/env python3
"""PreToolUse Bash hook — auto-approve the flow's known-safe command set.

Approves a Bash tool call ONLY when EVERY command head — across compound
operators (`&&`, `||`, `;`, `|`, `|&`, and a backgrounding `&`) and inside
`$(...)`/backtick command substitutions — is in a conservative safe set, and
the command contains no risky construct. Even a head that is in the safe set
defers when its arguments make it open-ended or destructive: inline `python -c`
/ `python -` (stdin) code; mutating `pip` subcommands
(install/uninstall/download/wheel); every `npx` call except the two pinned
`@google/design.md` invocations the design-language flow runs; work-discarding
git (`clean`, `checkout --`,
`checkout .`, `restore`, `stash drop/clear`, `branch -D`); and any reference to
credential paths (private keys, `~/.ssh`, `~/.aws`, `.git-credentials`,
`.netrc`) or shell-init dotfiles (`~/.bashrc` and kin) are never auto-approved.
Otherwise the hook prints nothing and
exits 0, deferring to the normal permission flow (which may prompt). `deny`
rules in settings.json still override an "allow" decision, so dangerous ops
stay blocked regardless.

This exists so a pipeline step run in a live `acceptEdits` session completes
without mid-run prompts, without `bypassPermissions` and without `claude -p`.
The defer-unknown + deny-dangerous design retains oversight for anything the
flow has not been observed to run.
"""
import sys
import json
import re

__version__ = "1.0.2"

# Heads that may run with no prompt: read-only inspection + git + python/pytest
# + reversible filesystem ops. Anything not here defers to a normal prompt.
SAFE = {
    "cd", "ls", "pwd", "cat", "head", "tail", "find", "grep", "rg", "egrep",
    "fgrep", "test", "[", "sed", "awk", "printf", "echo", "wc", "sort", "uniq",
    "cut", "tr", "basename", "dirname", "realpath", "readlink", "stat", "diff",
    "tree", "file", "true", "false", "sleep", "column", "nl", "comm", "tac",
    "xxd", "od", "jq",
    "git", "python", "python3", "pytest", "pip", "pip3",
    "mkdir", "rmdir", "rm", "cp", "mv", "touch", "chmod", "ln",
    # `npx` is here ONLY because `_exec_segment_ok` refuses it first: it emits
    # an `npx` head exclusively for the two pinned invocations below. Bare
    # `npx <anything>` fetches and runs arbitrary published code and is never
    # reachable through this entry. Unlike its neighbours, whose ordinary use
    # is safe and whose few dangerous argument shapes defer, `npx`'s ordinary
    # use is the dangerous one — only the enumerated shapes pass.
    "npx",
}

# The one external toolchain this flow shells out to: the design-language
# linter `product-design`'s Step 3 runs (SKILL.md:243-248). Both shapes are
# pinned verbatim — package AND version — by the prompt that owns the
# invocation, `<CORE>/../skills/cdo/.claude/skills/product-design/prompts/rich.md:30` (schema) and `:206`
# (lint). The version pin is deliberate there: "an unpinned `npx` invocation
# silently adopts a new format version, which would change what passes the gate
# below without anyone deciding to" (`:44-46`). Matching it exactly here means a
# version bump in that prompt must be made here too — which is the same
# deliberate decision, not an accident.
NPX_PINNED_PACKAGE = "@google/design.md@0.4.0"

# Process wrappers Claude Code itself strips before matching — mirror that.
WRAPPERS = {"timeout", "time", "nice", "nohup", "stdbuf", "env", "xargs"}

# Shell reserved words / structural tokens — never a command, skipped as heads.
KEYWORDS = {
    "if", "then", "elif", "else", "fi", "for", "while", "until", "do", "done",
    "case", "esac", "in", "{", "}", "[[", "]]", "!", "function", "select",
}

# Keywords that open a word-LIST header, not a command: `for X in …`,
# `select X in …`, `case W in`. The rest of that segment is the loop variable
# and its word list — never commands — so the whole segment yields no head.
# (Skipping only the keyword would read the loop variable `X` as a command.)
LOOP_HEADERS = {"for", "select", "case"}

# Any of these in the raw command forces a defer (never auto-approve).
RISKY = re.compile(
    r"""(
        \s-exec\b | \s-delete\b |
        \brm\s+-\w*[rR] | \brm\s+--recursive\b |
        \brm\s+-[rf]*\s*/(?:\s|$) | \brm\s+-[rf]*\s*~ |
        :\(\)\s*\{ | \bmkfs\b | \bdd\s+if= | of=/dev/ | >\s*/dev/sd |
        \bchmod\s+-R\s+777\s+/ |
        \bgit\s+push\b | \bgit\s+clean\b | --force\b | --hard\b | \breset\s+--hard\b |
        \bgit\s+checkout\b[^|&;\n]*\s--\s | \bgit\s+checkout\s+\.(?:/|\s|$) |
        \bgit\s+checkout\s+-f\b | \bgit\s+restore\b |
        \bgit\s+stash\s+(?:drop|clear)\b | \bgit\s+branch\s+-D\b |
        \bpip3?\s+(?:install|uninstall|download|wheel)\b |
        \bsudo\b | \|\s*sh\b | \|\s*bash\b | \beval\b |
        \bcurl\b | \bwget\b | \bshutdown\b | \breboot\b | \bdiskutil\b |
        >\s*/etc/ | >>\s*/etc/ |
        \bid_(?:rsa|dsa|ecdsa|ed25519)\b | \.ssh/ | \.git-credentials\b | \.netrc\b |
        (?:~|\$HOME)/\.(?:ssh|aws|gnupg|kube|docker|npmrc|pypirc)\b |
        (?:/|~)\.(?:bashrc|zshrc|bash_profile|zprofile|zshenv|profile|bash_login|gitconfig)\b
    )""",
    re.VERBOSE,
)


def strip_heredocs(cmd):
    """Remove heredoc bodies (`<<EOF ... EOF`, `<<'EOF'`, `<<-EOF`) so the
    document text — e.g. a commit message — is never tokenized as commands."""
    lines = cmd.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.search(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?", line)
        if m:
            out.append(line[:m.start()])  # keep the command, drop the redirect
            delim = m.group(1)
            i += 1
            while i < len(lines) and lines[i].strip() != delim:
                i += 1
            i += 1  # also drop the closing delimiter line
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def _split_on_operators(s):
    """Split a string into control-operator-separated segments, respecting
    single/double quotes so operators inside quoted arguments don't split."""
    segs, cur, i, n, quote = [], [], 0, len(s), None
    while i < n:
        ch = s[i]
        if quote:
            cur.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < n:
                cur.append(s[i + 1]); i += 2; continue
            if ch == quote:
                quote = None
            i += 1; continue
        if ch in ('"', "'"):
            quote = ch; cur.append(ch); i += 1; continue
        if s[i:i + 2] in ("&&", "||", "|&"):
            segs.append("".join(cur)); cur = []; i += 2; continue
        if ch in (";", "|", "\n"):
            segs.append("".join(cur)); cur = []; i += 1; continue
        # A lone "&" backgrounds the preceding command AND starts a new one, so
        # it must split — otherwise a trailing command hides from the gate
        # (`sleep 0 & make deploy`). But "&" is also part of redirections
        # (`2>&1`, `>&2`, `&>file`); treat it as a separator only when it is
        # not adjacent to ">".
        if ch == "&":
            prev = cur[-1] if cur else ""
            nxt = s[i + 1] if i + 1 < n else ""
            if prev != ">" and nxt != ">":
                segs.append("".join(cur)); cur = []; i += 1; continue
        cur.append(ch); i += 1
    segs.append("".join(cur))
    return segs


def _npx_segment_ok(args):
    """True only for the two pinned `@google/design.md` invocations, matched
    token for token:

        npx @google/design.md@0.4.0 lint <one non-flag path>
        npx @google/design.md@0.4.0 spec --rules

    Everything else about an `npx` call defers, because `npx <spec>` fetches a
    package from the registry and executes it — there is no bounded local
    behaviour to reason about, only the identity of the code being fetched. So
    the specifier is matched as a literal (a different package or a different
    version is different code), it must be the FIRST argument (an `npx` flag
    ahead of it — `-p`, `--package`, `-c`, `--call`, `--node-options` — can
    change or add what executes), the subcommand is one of the two the flow
    runs, and the argument count is exact so nothing rides along unread.

    `lint`'s path argument is the one free token; it may not start with `-`, so
    it cannot smuggle a flag. A path that had to be quoted (it contains a space)
    tokenizes as two words here and defers — narrow by choice, at the cost of a
    prompt for a shape the flow does not write.

    Only a bare `npx` can be approved: `safe_head`'s path-qualified rule lists
    python/pytest/pip, not npx, so `/opt/homebrew/bin/npx …` defers even with
    pinned arguments.
    """
    if len(args) < 2 or args[0] != NPX_PINNED_PACKAGE:
        return False
    if args[1] == "lint":
        return len(args) == 3 and not args[2].startswith("-")
    if args[1] == "spec":
        return args[2:] == ["--rules"]
    return False


def _exec_segment_ok(head, args):
    """False when an otherwise-safe exec head runs open-ended inline code we
    won't auto-approve — `python -c <code>` or `python -` (read from stdin), or
    an `npx` call that is not one of the two pinned design.md invocations.
    Scoped to one segment's args so unrelated `-c` flags (e.g. `grep -c`) on
    other commands never trip it."""
    base = head.rsplit("/", 1)[-1]
    if base in ("python", "python3"):
        return not any(a == "-" or a.startswith("-c") for a in args)
    if base == "npx":
        return _npx_segment_ok(args)
    return True


def heads_from(cmd, depth=0):
    """Return the list of command-head tokens, or None to signal 'defer'."""
    if depth > 4:
        return None
    out = []

    # Neutralize backslash-escaped backticks/dollars so literal `\`` inside a
    # quoted commit message is not mistaken for a command substitution.
    scan = cmd.replace("\\`", " ").replace("\\$", " ")

    # Recurse into real command substitutions, then blank them to empty.
    for sub in re.findall(r"\$\(([^()]*)\)", scan):
        h = heads_from(sub, depth + 1)
        if h is None:
            return None
        out += h
    for sub in re.findall(r"`([^`]*)`", scan):
        h = heads_from(sub, depth + 1)
        if h is None:
            return None
        out += h
    body = re.sub(r"\$\([^()]*\)", "", scan)
    body = re.sub(r"`[^`]*`", "", body)

    for seg in _split_on_operators(body):
        words = seg.split()
        i = 0
        header = False
        # Skip leading assignments, process wrappers, and shell keywords.
        while i < len(words):
            w = words[i]
            if w in LOOP_HEADERS:
                # `for X in …` / `select X in …` / `case W in` — the remainder
                # of this segment is a word list, not a command. No head here;
                # the loop body's commands live in the separate `do …` segment.
                header = True
                break
            if ASSIGN.match(w) or w in KEYWORDS:
                i += 1
            elif w in WRAPPERS:
                i += 1
                while i < len(words) and (words[i].startswith("-") or words[i].isdigit()):
                    i += 1
            else:
                break
        if header:
            continue
        if i < len(words) and not words[i].startswith("#"):
            head = words[i]  # ignore comment-only segments (`# ...`)
            if not _exec_segment_ok(head, words[i + 1:]):
                return None  # open-ended inline code → defer the whole call
            out.append(head)
    return out


def safe_head(h):
    if h in SAFE:
        return True
    # Absolute/relative path to a python or pytest binary (e.g. a venv).
    base = h.rsplit("/", 1)[-1]
    if base in ("python", "python3", "pytest", "pip", "pip3") and "/" in h:
        return True
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return  # cannot parse input → defer
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not cmd.strip():
        return
    cmd = strip_heredocs(cmd)  # drop document bodies before any analysis
    if RISKY.search(cmd):
        return  # risky construct → defer to a prompt
    hs = heads_from(cmd)
    if not hs:
        return  # parse trouble or no head found → defer
    if all(safe_head(h) for h in hs):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "development-bash-approve: all sub-commands in safe set",
            }
        }))


if __name__ == "__main__":
    main()
