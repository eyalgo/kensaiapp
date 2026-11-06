#!/usr/bin/env python3
"""PreToolUse Bash hook — auto-approve the flow's known-safe command set.

Approves a Bash tool call ONLY when EVERY command head — across compound
operators (`&&`, `||`, `;`, `|`, `|&`, and a backgrounding `&`), inside
`$(...)`/backtick command substitutions however nested, and inside an unquoted
heredoc's body — is in a conservative safe set, and the command contains no
risky construct. Quotes, escapes, `$'...'` and line continuations are read
the way the shell reads them, by one model every scanner here shares. Any
variable assignment ahead of a command, `env` with an option, any process
substitution, and a quote left open defers the whole call. Even a head that
is in the safe set defers when its arguments make it open-ended or
destructive, or are computed (a `$` parameter, a substitution) so the hook
cannot read them: Python given code any way but a script file or a listed
module; pip doing anything but read; every `npx` call except the two pinned
`@google/design.md` invocations the design-language flow runs; an `awk` or
`sed` program that can run a command or write a file, or one read from a
file; a git subcommand off its allowed list (reads, and the changes the flows
make and git can take back), judged after git's global options, and any
global option that can run code (`-c`, `--exec-path`, `--config-env`) or that
the hook does not know; a recursive `rm`; the `find`, `rg` and `sort` options
that run a program; and any reference to credential paths (private keys,
`~/.ssh`, `~/.aws` and kin by any path, the GitHub CLI's token store,
`.git-credentials`, `.netrc`, any `.env` file but for the pinned read that lists
its key names, and a dot-file named through a glob or brace) or shell-init
dotfiles (`~/.bashrc` and kin). The names are read with quotes and backslashes
taken out, as the shell joins them; a path built from a variable or a
substitution is not, so it can still spell one of them. The process environment
is not guarded: `env | grep`, `jq -n env` and `echo "$VAR"` print it. It is kept
free of secrets by the machine's setup instead — no shell loads `~/.env` — so a
session has none to print. Otherwise the hook prints nothing and exits 0,
deferring to the normal permission flow (which may prompt).

**Nothing stands behind an "allow".** `deny` rules in a settings file would
override it, but this instance's `.claude/settings.json` carries none (checked
2026-10-28, the user-level one too), so an approval here is the last word. One
route stays open by design: a command the agent wrote to a file with the Write
tool and then runs through an approved head (`python3 script.py`, `pytest`,
`git commit` running hooks) is code this hook never reads.

This exists so a pipeline step run in a live `acceptEdits` session completes
without mid-run prompts, without `bypassPermissions` and without `claude -p`.
The defer-unknown design retains oversight for anything the flow has not been
observed to run.
"""
import sys
import json
import re
import shlex

__version__ = "1.2.0"

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

# The launch's runner, `core/tools/locked_python.sh`: a launcher runs its Python
# through it on the pinned interpreter, so it is approved on the terms a
# `python3` head is. Matched by its place under a `core/tools/` directory, so a
# file of the same name anywhere else defers.
RUNNER_SUFFIX = "/core/tools/locked_python.sh"


def _is_runner(head):
    return head.strip("\"'").endswith(RUNNER_SUFFIX)

# Process wrappers Claude Code itself strips before matching — mirror that.
WRAPPERS = {"timeout", "time", "nice", "nohup", "stdbuf", "env", "xargs"}

# Shell reserved words / structural tokens — never a command, skipped as heads.
KEYWORDS = {
    "if", "then", "elif", "else", "fi", "for", "while", "until", "do", "done",
    "case", "esac", "in", "{", "}", "[[", "]]", "!", "function", "select",
}

# Keywords that open a word-LIST header, not a command: `for X in …`,
# `select X in …`. The rest of that segment is the loop variable and its word
# list — never commands — so the whole segment yields no head. (Skipping only
# the keyword would read the loop variable `X` as a command.) `case` is not one:
# its first branch's command shares the header's segment (`case W in P) cmd ;;`),
# so `heads_from` judges what follows the pattern's `)`.
LOOP_HEADERS = {"for", "select"}

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
        \bsudo\b | \|\s*sh\b | \|\s*bash\b | \beval\b | [<>]\( |
        \bcurl\b | \bwget\b | \bshutdown\b | \breboot\b | \bdiskutil\b |
        >\s*/etc/ | >>\s*/etc/ |
        \bid_(?:rsa|dsa|ecdsa|ed25519)\b | \.ssh/ | \.git-credentials\b | \.netrc\b |
        (?:^|[\s/'"=<])\.(?:ssh|aws|gnupg|kube|docker|npmrc|pypirc|env)\b |
        \.config/(?:gh|git)\b | \bgh/hosts\.yml\b |
        (?:^|\s|/Users/[^/\s]+/|~/|\$HOME/|\$\{HOME\}/)\.[^\s/'"]*[*?\[{] |
        \$'[^']*\\[0-7xuUc] |
        (?:/|~)\.(?:bashrc|zshrc|bash_profile|zprofile|zshenv|profile|bash_login|gitconfig)\b
    )""",
    re.VERBOSE,
)


def shell_contexts(text, quotes=True, quote=None):
    """How the shell reads each character of `text`: the quote it sits in —
    None (unquoted), `'`, `"` or `$'` (ANSI-C) — and whether a backslash
    escapes it. Returns `(contexts, escaped, quote_left_open)`.

    This is the one quoting model every scanner here reads, so none of them can
    disagree with another about where a quote opens or closes. A backslash
    escapes the next character outside single quotes, inside `$'...'` too. With
    `quotes` off — an unquoted heredoc's body — every quote is literal text and
    only backslashes count. `quote` is the state a previous line left open."""
    n = len(text)
    contexts, escaped = [None] * n, [False] * n
    i = 0
    while i < n:
        ch = text[i]
        contexts[i] = quote
        if quote == "'":
            if ch == "'":
                quote = None
            i += 1
            continue
        if ch == "\\" and i + 1 < n:
            contexts[i + 1] = quote
            escaped[i + 1] = True
            i += 2
            continue
        if quote == "$'":
            if ch == "'":
                quote = None
        elif not quotes:
            pass
        elif quote == '"':
            if ch == '"':
                quote = None
        elif ch == "'":
            quote = "'"
        elif ch == '"':
            quote = '"'
        elif ch == "$" and i + 1 < n and text[i + 1] == "'":
            contexts[i + 1] = None
            quote = "$'"
            i += 2
            continue
        i += 1
    return contexts, escaped, quote


def _live(contexts, escaped, i):
    """Whether the character at `i` is one the shell acts on: unescaped, and
    outside single quotes and `$'...'`."""
    return not escaped[i] and contexts[i] in (None, '"')


# A command substitution in the text is replaced by this before the text is cut
# into commands. It is never a command and never an argument a judged head
# accepts, so a head whose argument is computed by a substitution defers.
SUBST = "\x00"


def _close_paren(text, k, quotes):
    """Index of the `)` closing a `$(` whose body starts at `k`, or None."""
    contexts, escaped, _ = shell_contexts(text[k:], quotes)
    depth = 1
    for j, ch in enumerate(text[k:]):
        if escaped[j] or contexts[j] is not None:
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return k + j
    return None


def substitutions(text, quotes=True):
    """The outermost `$(...)` and backtick substitutions the shell would run in
    `text`, as `(start, end, body)`, or None when one does not close, or — with
    `quotes` — when a quote is left open, since then the hook and the shell may
    not agree on what is quoted.

    With `quotes`, single-quoted and `$'...'` text is literal, as the shell
    reads a command line. Without it, every quote is literal text, as the shell
    reads an unquoted heredoc's body. Nested substitutions are left inside their
    body for the caller to recurse into."""
    contexts, escaped, left_open = shell_contexts(text, quotes)
    if quotes and left_open:
        return None
    spans, i, n = [], 0, len(text)
    while i < n:
        if not _live(contexts, escaped, i):
            i += 1
            continue
        if text.startswith("$(", i):
            end = _close_paren(text, i + 2, quotes)
            if end is None:
                return None
            spans.append((i, end + 1, text[i + 2:end]))
            i = end + 1
            continue
        if text[i] == "`":
            j = i + 1
            while j < n and text[j] != "`":
                j += 2 if text[j] == "\\" else 1
            if j >= n:
                return None
            spans.append((i, j + 1, text[i + 1:j]))
            i = j + 1
            continue
        i += 1
    return spans


def live_expansion(text):
    """Whether the shell would expand anything in `text`: a `$` parameter,
    arithmetic or `$'...'` outside single quotes, a backtick, a substitution
    already replaced by `SUBST`, or a process substitution outside quotes — or
    whether a quote is left open, so the hook cannot tell."""
    contexts, escaped, left_open = shell_contexts(text)
    if left_open:
        return True
    n = len(text)
    for i, ch in enumerate(text):
        if ch == SUBST:
            return True
        if not _live(contexts, escaped, i):
            continue
        if ch == "`":
            return True
        if ch == "$" and i + 1 < n and (text[i + 1].isalnum() or text[i + 1] in "_{('\"@*#?$!-"):
            return True
        if contexts[i] is None and ch in "<>" and i + 1 < n and text[i + 1] == "(":
            return True
    return False


_WORD_END = set(" \t;&|<>()")


def _heredoc_markers(line, quote):
    """Every heredoc redirect on `line` that the shell reads as one, as
    `(start, end, delimiter, quoted)`, with the quote state the line leaves
    open; None when a quoted delimiter does not close. `quote` is the state a
    previous line left open, so a `<<` inside a string that spans lines is
    text. A here-string (`<<<`) is not a heredoc."""
    contexts, escaped, left_open = shell_contexts(line, quote=quote)
    markers, i, n = [], 0, len(line)
    while i < n:
        if escaped[i] or contexts[i] is not None:
            i += 1
            continue
        if line.startswith("<<<", i):
            i += 3  # a here-string: its word follows, and no body
            continue
        if not line.startswith("<<", i):
            i += 1
            continue
        j = i + 2
        if j < n and line[j] == "-":
            j += 1
        while j < n and line[j] in " \t":
            j += 1
        word, quoted = [], False
        while j < n and line[j] not in _WORD_END:
            c = line[j]
            if c in "'\"":
                close = line.find(c, j + 1)
                if close < 0:
                    return None
                word.append(line[j + 1:close])
                quoted = True
                j = close + 1
                continue
            if c == "\\":
                quoted = True
                j += 1
                if j < n:
                    word.append(line[j])
                j += 1
                continue
            word.append(c)
            j += 1
        if word:
            markers.append((i, j, "".join(word), quoted))
        i = j
    return markers, left_open


def strip_heredocs(cmd):
    """Remove heredoc bodies (`<<EOF ... EOF`, `<<'EOF'`, `<<-EOF`) so the
    document text — e.g. a commit message — is never tokenized as commands.
    Returns None, to defer, when a delimiter or a substitution does not close,
    or a quote is left open on a heredoc's own line.

    Only a quoted delimiter (`<<'EOF'`, `<<"EOF"`, `<<\\EOF`, `<<E'O'F`) makes
    the body inert. An unquoted one leaves `$(...)` and backticks live, across
    lines and nested, so each is kept beside the command for `heads_from` to
    inspect; the prose around them is still dropped. A marker inside quotes —
    a quote opened on an earlier line included — is text, and a here-string
    (`<<<word`) carries no body: both are left alone."""
    lines = cmd.split("\n")
    out = []
    quote = None
    i = 0
    while i < len(lines):
        line = lines[i]
        found = _heredoc_markers(line, quote)
        if found is None:
            return None
        markers, quote = found
        i += 1
        if not markers:
            out.append(line)
            continue
        if quote is not None:
            return None
        kept, live, last = [], [], 0
        for start, end, delim, quoted in markers:
            kept.append(line[last:start])
            last = end
            body = []
            while i < len(lines) and lines[i].strip() != delim:
                body.append(lines[i])
                i += 1
            i += 1  # also drop the closing delimiter line
            if not quoted:
                text = "\n".join(body)
                spans = substitutions(text, quotes=False)
                if spans is None:
                    return None
                live += [text[s:e] for s, e, _ in spans]
        kept.append(line[last:])
        # keep the command on both sides of each redirect, drop the redirect,
        # keep what each body still runs
        out.append(" ".join(kept + live))
    return "\n".join(out)


ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def _split_on_operators(s):
    """Split a string into control-operator-separated segments, reading quotes
    and escapes as the shell does (`shell_contexts`), so an operator inside a
    quoted or escaped argument does not split and an escaped quote opens
    nothing. A backslash-newline joins two lines into one command, as the shell
    does. None when a quote is left open: the hook and the shell could then
    disagree about where one command ends."""
    contexts, escaped, left_open = shell_contexts(s)
    if left_open:
        return None
    segs, cur, i, n = [], [], 0, len(s)
    while i < n:
        ch = s[i]
        if (ch == "\\" and i + 1 < n and s[i + 1] == "\n"
                and not escaped[i] and contexts[i] in (None, '"')):
            i += 2  # a line continuation: the shell reads one command
            continue
        if escaped[i] or contexts[i] is not None:
            cur.append(ch); i += 1; continue
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


def _tokens(args):
    """The segment's words re-read with the shell's quoting, so a quoted path or
    program is one token. None when the quoting does not close, or when the
    shell would expand anything in them: a computed argument is one this hook
    cannot read, so a judged head never accepts one."""
    text = " ".join(args)
    if live_expansion(text):
        return None
    try:
        return shlex.split(text)
    except ValueError:
        return None


# An awk program that runs a command (`system(`, a pipe to or from one), writes a
# file (`print`/`printf` redirected), or reaches gawk's indirect calls and
# extension loading (`@`). A `>` outside a print statement is a comparison and
# passes; a `|` in a regex also defers, which costs a prompt and nothing else.
AWK_REACH = re.compile(r"\bsystem\s*\(|\||@|\bprintf?\b[^;{}]*>")


def _awk_segment_ok(args):
    """True when the awk program can neither run a command nor write a file.

    The program is the first operand after `-F`/`-v` options. A program read
    from a file (`-f`) is not visible here, and any other option (`--source`,
    `-e`, …) may carry one, so both defer."""
    tokens = _tokens(args)
    if tokens is None:
        return False
    i = 0
    while i < len(tokens) and tokens[i].startswith("-"):
        token = tokens[i]
        if token == "--":
            i += 1
            break
        if token in ("-F", "-v"):
            i += 2
        elif token[:2] in ("-F", "-v"):
            i += 1
        else:
            return False
    if i >= len(tokens):
        return False
    return not AWK_REACH.search(tokens[i])


# sed commands that take no argument, or only a label or a file to read.
_SED_PLAIN = set("=dDgGhHlnNpPqQxzF")
_SED_TO_LINE_END = set("aicrRbtTv:")


def _sed_skip_regex(script, i):
    """Index just past an address regex opening at `i` (`/re/` or `\\cREc`)."""
    if script[i] == "\\":
        i += 1
    if i >= len(script):
        return None
    delim = script[i]
    i += 1
    while i < len(script) and script[i] != delim:
        i += 2 if script[i] == "\\" else 1
    return i + 1 if i < len(script) else None


def _sed_address(script, i):
    """Index just past an optional address at `i`, or None when it does not close."""
    n = len(script)
    if i < n and (script[i].isdigit() or script[i] == "$"):
        while i < n and (script[i].isdigit() or script[i] in "$~+"):
            i += 1
    elif i < n and script[i] in "/\\":
        i = _sed_skip_regex(script, i)
    return i


def sed_script_reaches(script):
    """Whether a sed script can run a command (`e`, the `s///e` flag) or write a
    file (`w`, `W`, the `s///w` flag). Read command by command, so an `e` or a
    `w` inside a regex or a replacement is text. A command this reader does not
    know reaches, since it might be one of those."""
    i, n = 0, len(script)
    while i < n:
        while i < n and script[i] in " \t\n;{}":
            i += 1
        if i >= n:
            return False
        i = _sed_address(script, i)
        if i is not None and i < n and script[i] == ",":
            i = _sed_address(script, i + 1)
        if i is None:
            return True
        while i < n and script[i] in " \t!":
            i += 1
        if i >= n:
            return False
        command = script[i]
        i += 1
        if command in "ewW":
            return True
        if command in "{}":
            continue
        if command in _SED_PLAIN:
            continue
        if command in _SED_TO_LINE_END:
            while i < n and script[i] != "\n" and not (command in "bt:Tv" and script[i] == ";"):
                i += 1
            continue
        if command in "sy":
            if i >= n:
                return True
            delim = script[i]
            i += 1
            for _ in range(2):
                while i < n and script[i] != delim:
                    i += 2 if script[i] == "\\" else 1
                if i >= n:
                    return True
                i += 1
            flags_start = i
            while i < n and script[i] not in ";\n}":
                i += 1
            if command == "s" and re.search(r"[ewW]", script[flags_start:i]):
                return True
            continue
        return True
    return False


def _sed_segment_ok(args):
    """True when no sed script can run a command or write a file.

    The scripts are every `-e`/`--expression` value, or else the first operand.
    A script read from a file (`-f`) is not visible here and defers. In a short
    cluster, `e` takes the rest of the cluster, or else the next token, as a
    script, and `i` takes the rest as its backup suffix."""
    tokens = _tokens(args)
    if tokens is None:
        return False
    scripts, operands = [], []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in ("--expression",):
            if i + 1 >= len(tokens):
                return False
            scripts.append(tokens[i + 1])
            i += 2
            continue
        if token.startswith("--expression="):
            scripts.append(token.split("=", 1)[1])
        elif token == "--file" or token.startswith("--file="):
            return False
        elif token.startswith("-") and not token.startswith("--") and len(token) > 1:
            for k, flag in enumerate(token[1:], start=1):
                if flag == "f":
                    return False
                if flag == "e":
                    rest = token[k + 1:]
                    if rest:
                        scripts.append(rest)
                    elif i + 1 < len(tokens):
                        scripts.append(tokens[i + 1])
                        i += 1
                    else:
                        return False
                    break
                if flag == "i":
                    if k == len(token) - 1 and i + 1 < len(tokens) and tokens[i + 1] == "":
                        i += 1  # BSD `-i ''`: the empty suffix is the option's value
                    break
        elif not token.startswith("-"):
            operands.append(token)
        i += 1
    if not scripts:
        if not operands:
            return False
        scripts = operands[:1]
    return not any(sed_script_reaches(script) for script in scripts)


# git's global options that take no value and change nothing about what runs.
GIT_FLAG_GLOBALS = {
    "--no-pager", "-P", "--bare", "--no-replace-objects", "--literal-pathspecs",
    "--glob-pathspecs", "--noglob-pathspecs", "--icase-pathspecs",
    "--no-optional-locks", "--no-lazy-fetch", "--no-advice",
}

# git's global options that take a path or a name. Each may be written
# `--opt value` or `--opt=value`.
GIT_VALUE_GLOBALS = {"-C", "--git-dir", "--work-tree", "--namespace"}

# Subcommands that read the repository and nothing else.
GIT_READ = {
    "status", "log", "show", "diff", "rev-parse", "rev-list", "ls-files", "ls-tree",
    "cat-file", "blame", "shortlog", "describe", "merge-base", "show-ref",
    "for-each-ref", "name-rev", "count-objects", "whatchanged", "grep", "help",
    "version",
}

# Options that make a reading subcommand write a file or run a program.
GIT_READ_REACH = ("--output", "--ext-diff", "-O", "--open-files-in-pager")


def _git_has(rest, *names):
    """Whether any token in `rest` is one of `names`, as itself, `name=…`, or —
    for a one-letter short option — inside a short cluster."""
    for token in rest:
        if token == "--":
            return False
        for name in names:
            if token == name or token.startswith(name + "="):
                return True
            if (len(name) == 2 and name[0] == "-" and name[1] != "-"
                    and token.startswith("-") and not token.startswith("--")
                    and name[1] in token[1:]):
                return True
    return False


def _git_subcommand_ok(sub, rest):
    """True when `git <sub> <rest>` is on the allowed list: it reads, or makes a
    change the flows make and `git` can take back (stage, commit, move, merge,
    branch, add a worktree). Every other subcommand — push, fetch, reset,
    restore, clean, rebase, bisect, submodule, config writes, … — defers."""
    if sub in GIT_READ:
        return not any(token == name or token.startswith(name + "=")
                       or (name == "-O" and token.startswith("-O"))
                       for token in rest for name in GIT_READ_REACH)
    if sub in ("add", "commit", "mv"):
        return True
    if sub == "rm":
        return not _git_has(rest, "-f", "--force")
    if sub == "merge":
        return not _git_has(rest, "--abort", "--quit")
    if sub == "switch":
        return not _git_has(rest, "-f", "--force", "--discard-changes", "-C",
                            "--force-create")
    if sub == "checkout":
        return len(rest) in (2, 3) and rest[0] == "-b" and not rest[1].startswith("-")
    if sub == "worktree":
        if rest[:1] == ["list"]:
            return True
        return rest[:1] == ["add"] and not _git_has(rest, "-f", "--force", "-B")
    if sub == "branch":
        return not _git_has(rest, "-d", "-D", "--delete", "-f", "--force", "-m", "-M",
                            "--move", "-c", "-C", "--copy", "-u", "--set-upstream-to",
                            "--unset-upstream", "--edit-description")
    if sub == "tag":
        return not _git_has(rest, "-d", "--delete", "-f", "--force")
    if sub == "stash":
        return rest[:1] in (["list"], ["show"])
    if sub == "reflog":
        return not rest or rest[0] == "show" or rest[0].startswith("-")
    if sub == "config":
        if _git_has(rest, "--get", "--get-all", "--get-regexp", "--list", "-l"):
            return not _git_has(rest, "--add", "--unset", "--unset-all", "--replace-all",
                                "--rename-section", "--remove-section", "-e", "--edit")
        operands = [token for token in rest if not token.startswith("-")]
        return len(operands) == 1 and len(operands) == len(rest)
    return False


def _git_segment_ok(args):
    """True when the subcommand git will run, found after its global options,
    is on the allowed list (`_git_subcommand_ok`).

    A global option that can make git run a command of its own choosing — `-c`
    (an alias or pager), `--exec-path`, `--config-env` — defers, and so does
    any option this hook does not know, because it might be one of those."""
    tokens = _tokens(args)
    if tokens is None:
        return False
    i = 0
    while i < len(tokens) and tokens[i].startswith("-"):
        token = tokens[i]
        name = token.split("=", 1)[0]
        if token in ("--version", "--help", "-h") and i == len(tokens) - 1:
            return True
        if token in GIT_FLAG_GLOBALS:
            i += 1
        elif token in GIT_VALUE_GLOBALS:
            i += 2
        elif name in GIT_VALUE_GLOBALS and "=" in token:
            i += 1
        else:
            return False
    if i >= len(tokens):
        return True
    return _git_subcommand_ok(tokens[i], tokens[i + 1:])


# Modules `python -m` may run unprompted: the test runners, two read-only tools,
# and pip, which is then judged as `pip` is.
PY_MODULES = {"pytest", "unittest", "json.tool", "py_compile", "pip"}

# Short options that change how the interpreter runs a script but give it no
# code of its own.
_PY_FLAGS = set("uBOEsSIqvdbRPx")


def _python_segment_ok(args):
    """True when the interpreter runs a script file, or one of `PY_MODULES`.

    Code given any other way defers: `-c` (alone or in a cluster such as
    `-uc`), `-` or no script at all (stdin, which a heredoc fills), a module
    outside the list, a script read from `/dev/stdin` or `/dev/fd/`, and any
    long option this hook does not know."""
    tokens = _tokens(args)
    if tokens is None:
        return False
    if tokens in (["--version"], ["-V"], ["--help"], ["-h"]):
        return True
    i = 0
    while i < len(tokens) and tokens[i].startswith("-"):
        token = tokens[i]
        if token == "-m":
            if i + 1 >= len(tokens) or tokens[i + 1] not in PY_MODULES:
                return False
            return tokens[i + 1] != "pip" or _pip_tokens_ok(tokens[i + 2:])
        if token in ("-W", "-X"):
            i += 2
            continue
        if token.startswith("--") or token == "-" or not set(token[1:]) <= _PY_FLAGS:
            return False
        i += 1
    if i >= len(tokens):
        return False
    script = tokens[i]
    return not (script.startswith(("<", "/dev/stdin", "/dev/fd/")))


# pip subcommands that read and change nothing.
PIP_READ = {"list", "show", "freeze", "check", "help"}
_PIP_FLAG_GLOBALS = {"-q", "-qq", "-v", "-vv", "--quiet", "--verbose", "--isolated",
                     "--no-cache-dir", "--disable-pip-version-check", "--no-color",
                     "--no-input", "--require-virtualenv"}


def _pip_tokens_ok(tokens):
    i = 0
    while i < len(tokens) and tokens[i].startswith("-"):
        if tokens[i] == "--version" and i == len(tokens) - 1:
            return True
        if tokens[i] not in _PIP_FLAG_GLOBALS:
            return False
        i += 1
    return i < len(tokens) and tokens[i] in PIP_READ


def _pip_segment_ok(args):
    """True when pip only reads: `list`, `show`, `freeze`, `check`, `help` or
    `--version`, after options that change nothing it installs."""
    tokens = _tokens(args)
    return tokens is not None and _pip_tokens_ok(tokens)


def _rm_segment_ok(args):
    """True when `rm` removes no directory tree: no `-r`/`-R`, alone, in a cluster
    or quoted, and no `--recursive`."""
    tokens = _tokens(args)
    if tokens is None:
        return False
    for token in tokens:
        if token == "--":
            return True
        if token == "--recursive":
            return False
        if token.startswith("-") and not token.startswith("--") and set(token[1:]) & set("rR"):
            return False
    return True


# `find` primaries that run a command, delete, or write a file.
FIND_REACH = {"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprint0",
              "-fprintf", "-fls"}


def _find_segment_ok(args):
    tokens = _tokens(args)
    return tokens is not None and not FIND_REACH & set(tokens)


# ripgrep options that only shape what is searched or printed. An allowed list,
# because rg has more than one option that runs a program (`--pre`,
# `--hostname-bin`, `--search-zip`'s decompressors) and may gain another.
_RG_SHORT_FLAGS = set("nNiIsSwxvFlLcoquHhbpU0P.")
_RG_SHORT_VALUES = set("egtTABCmdMEjr")
_RG_LONG_FLAGS = {
    "--line-number", "--no-line-number", "--ignore-case", "--smart-case",
    "--case-sensitive", "--word-regexp", "--line-regexp", "--invert-match",
    "--fixed-strings", "--files-with-matches", "--files-without-match", "--count",
    "--count-matches", "--only-matching", "--quiet", "--hidden", "--no-ignore",
    "--no-ignore-vcs", "--no-ignore-dot", "--no-ignore-parent", "--files", "--json",
    "--vimgrep", "--with-filename", "--no-filename", "--heading", "--no-heading",
    "--null", "--pretty", "--multiline", "--multiline-dotall", "--pcre2", "--trim",
    "--stats", "--no-messages", "--column", "--byte-offset", "--follow",
    "--passthru", "--type-list", "--version", "--help", "--unrestricted",
    "--no-config", "--sort-files", "--crlf", "--binary", "--text",
}
_RG_LONG_VALUES = {
    "--regexp", "--glob", "--iglob", "--type", "--type-not", "--after-context",
    "--before-context", "--context", "--max-count", "--max-depth", "--max-columns",
    "--max-filesize", "--encoding", "--threads", "--replace", "--sort", "--sortr",
    "--color", "--colors", "--path-separator", "--type-add", "--field-match-separator",
    "--field-context-separator", "--context-separator",
}


def _rg_segment_ok(args):
    """True when every rg option is on the allowed list: options that only shape
    what is searched or printed. Anything else — `--pre`, `--hostname-bin`,
    `--search-zip`, an option this hook does not know — defers."""
    tokens = _tokens(args)
    if tokens is None:
        return False
    i = 0
    while i < len(tokens):
        token = tokens[i]
        i += 1
        if token == "--":
            return True
        if token.startswith("--"):
            name = token.split("=", 1)[0]
            if token in _RG_LONG_FLAGS:
                continue
            if name in _RG_LONG_VALUES:
                if "=" not in token:
                    i += 1
                continue
            return False
        if token.startswith("-") and len(token) > 1:
            for k, flag in enumerate(token[1:], start=1):
                if flag in _RG_SHORT_VALUES:
                    if k == len(token) - 1:
                        i += 1  # the value is the next token
                    break
                if flag not in _RG_SHORT_FLAGS:
                    return False
    return True


def _sort_segment_ok(args):
    """`sort --compress-program` runs a program when the input spills to disk."""
    tokens = _tokens(args)
    return tokens is not None and not any(
        token.startswith("--compress-program") for token in tokens)


def _exec_segment_ok(head, args):
    """False when an otherwise-safe head is given arguments that make it run
    code we won't auto-approve, push, or discard work: inline or stdin Python,
    an `npx` call that is not one of the two pinned design.md invocations, an
    `awk` or `sed` program that can run a command or write a file, a git
    subcommand off the allowed list, a pip that installs, a recursive `rm`, and
    the `find`, `rg` and `sort` options that run a program. Scoped to one
    segment's args so unrelated `-c` flags (e.g. `grep -c`) on other commands
    never trip it."""
    base = head.rsplit("/", 1)[-1]
    if base in ("python", "python3") or _is_runner(head):
        return _python_segment_ok(args)
    if base in ("pip", "pip3"):
        return _pip_segment_ok(args)
    if base == "npx":
        return _npx_segment_ok(args)
    checks = {"awk": _awk_segment_ok, "sed": _sed_segment_ok, "git": _git_segment_ok,
              "rm": _rm_segment_ok, "find": _find_segment_ok, "rg": _rg_segment_ok,
              "sort": _sort_segment_ok}
    check = checks.get(head)
    return check(args) if check else True


def heads_from(cmd, depth=0):
    """Return the list of command-head tokens, or None to signal 'defer'."""
    if depth > 4:
        return None
    spans = substitutions(cmd)
    if spans is None:
        return None
    out = []
    # Recurse into each command substitution, then stand a placeholder in its
    # place, so the command around it sees an argument it cannot read.
    for _, _, inner in spans:
        h = heads_from(inner, depth + 1)
        if h is None:
            return None
        out += h
    body, last = [], 0
    for start, end, _ in spans:
        body += [cmd[last:start], f" {SUBST} "]
        last = end
    body = "".join(body + [cmd[last:]])

    segments = _split_on_operators(body)
    if segments is None:
        return None
    for seg in segments:
        words = seg.split()
        i = 0
        header = False
        # Skip process wrappers and shell keywords. An assignment defers the
        # whole call: it can point a safe head at other code (`PATH=`,
        # `GIT_EXEC_PATH=`, `LD_PRELOAD=`), and so can `env`'s options.
        while i < len(words):
            w = words[i]
            if w in LOOP_HEADERS:
                # `for X in …` / `select X in …` — the remainder of this
                # segment is a word list, not a command. No head here; the
                # loop body's commands live in the separate `do …` segment.
                header = True
                break
            if w == "case":
                # `case W in P) cmd` — the command after the first `)` runs.
                # With no `)` the branch starts on a later segment, whose
                # head is the pattern itself and defers. A `)` inside a
                # quoted pattern cuts early, which leaves a head that defers.
                rest = " ".join(words[i + 1:])
                if ")" not in rest:
                    header = True
                    break
                words, i = rest.split(")", 1)[1].split(), 0
                continue
            if ASSIGN.match(w):
                return None
            if w in KEYWORDS:
                i += 1
            elif w in WRAPPERS:
                if w == "env" and i + 1 < len(words) and words[i + 1].startswith("-"):
                    return None
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


# Directories a path-qualified python, pytest or pip is trusted from: the
# system's and Homebrew's, and a virtualenv's `bin/`.
TRUSTED_BIN_PREFIXES = ("/usr/bin/", "/usr/local/bin/", "/opt/homebrew/bin/",
                        "/Library/Frameworks/Python.framework/")
TRUSTED_BIN_PARTS = ("/.venv/bin/", "/venv/bin/")


def safe_head(h):
    if SUBST in h or "$" in h or "`" in h:
        return False  # a computed head names whatever its value says
    if h in SAFE or _is_runner(h):
        return True
    # An absolute path to a python, pytest or pip binary in a trusted place.
    base = h.rsplit("/", 1)[-1]
    if base in ("python", "python3", "pytest", "pip", "pip3") and (
            h.startswith(TRUSTED_BIN_PREFIXES) or any(p in h for p in TRUSTED_BIN_PARTS)):
        return True
    return False




ALLOW = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": "development-bash-approve: all sub-commands in safe set",
    }
}

# `~/.env` holds the owner's live credentials, so any command that names a
# `.env` file defers (RISKY). The one exception is the read that lists the key
# names and never a value, which the owner's rules tell a session to use; it is
# pinned verbatim, because a form judged by its parts could print values.
KEY_NAMES_READS = {
    "grep -oE '^[A-Za-z_]+=' ~/.env | cut -d= -f1",
    "grep -oE '^[A-Za-z_][A-Za-z0-9_]*=' ~/.env | cut -d= -f1",
}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return  # cannot parse input → defer
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not cmd.strip():
        return
    cmd = strip_heredocs(cmd)  # drop document bodies before any analysis
    if cmd is None:
        return  # a delimiter or a substitution that does not close → defer
    if cmd.strip() in KEY_NAMES_READS:
        print(json.dumps(ALLOW))
        return
    # Also read with quotes and backslashes taken out, so a name the shell
    # splices together (`~/.e"n"v`, `~/.\env`) is judged as the name it becomes.
    if RISKY.search(cmd) or RISKY.search(re.sub(r"[\\'\"]", "", cmd)):
        return  # risky construct → defer to a prompt
    hs = heads_from(cmd)
    if not hs:
        return  # parse trouble or no head found → defer
    if all(safe_head(h) for h in hs):
        print(json.dumps(ALLOW))


if __name__ == "__main__":
    main()
