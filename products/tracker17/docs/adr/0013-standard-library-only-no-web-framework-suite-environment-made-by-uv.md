# ADR-0013: Run on Python's standard library alone, with no web framework and no template engine, and make the test suite's environment with uv

**Status:** Accepted
**Date:** 2026-10-29

## Context

Setup is bounded at three commands and ten minutes, with no account, key or sign-up (SRS C-2,
C-7). The SRS names no runtime and leaves it to the SDD (SRS RN-23). The predecessor whose code is
the preferred starting point requires Python 3.11 or later and has no run-time dependency (SDD
RN-3). Every package the tracker runs on is code the reader has to read or take on trust (SRS
NFR-10). The UXD had already turned down a design-system package for that reason (UXD § 9, quoted
in SDD RN-3). A fresh copy must get the same test dependency versions the suite last passed with
(SRS C-8).

ADR-0002 decided the runtime on 2026-10-06, and had the test dependencies installed into a virtual
environment made with Python's `venv`. On 2026-10-29 the owner moved the suite's environment to uv,
and SDD version 15 § 4 RT-4 settled it (SDD RN-62). ADR-0002's decision says `venv` in two places,
so this is a change of decision. This record carries ADR-0002's decision, alternatives and
consequences whole, with the environment changed.

## Decision

The tracker runs on Python 3.11 or later and imports nothing outside the Python standard library.
It uses no web framework and no template engine. `web` carries its own routing, request reading,
page building and escaping over the standard library's HTTP server, and accepts connections while
one is being served (SDD § 4 RT-6, § 11 R-4). The running tracker needs no network connection at
any point. A `python3` below 3.11 is a missing prerequisite that the setup instructions explain.

Only the tests have dependencies. They are declared in `pyproject.toml`'s `dev` group at exact
versions, and locked with everything they pull in, in one committed file, `uv.lock`, beside
`pyproject.toml`. uv makes and fills the suite's environment: `uv sync --locked` makes `.venv` and
installs the locked set, and refuses a lock file out of step with `pyproject.toml` instead of
rewriting it. Every suite command is typed through `uv run`. uv is a prerequisite of the suite and
not of the tracker: the tracker's own setup names it nowhere. The suite runs on the interpreter uv
picks for `requires-python`, which need not be the `python3` that runs the tracker. The end-to-end
layer drives Chromium.

The owner confirmed the runtime on 2026-10-06 and added that the tracker needs no network at all,
that a `python3` below 3.11 is explained by the setup instructions, and that the unchecked floor is
a named risk. The owner chose uv for the suite on 2026-10-29.

## Alternatives ruled out

- **A web framework.** It would shorten the page-building code and give routing and templates a
  reader may already know. It lost because it adds packages the reader has to read or take on trust,
  and an install step that spends part of C-7's three commands. It would also make the network
  connection of SRS FR-4 a prerequisite for running the tracker, not only for setting up the tests.
- **A template engine on its own.** Its automatic escaping is the main thing given up here. It lost
  for the same reason: it is a run-time dependency, and the tracker would no longer be runnable from
  the copy alone.
- **A suite environment made with Python's `venv` and filled from a pinned requirements file.**
  ADR-0002 took it, and it needs nothing the tracker does not. It lost to the owner's call of
  2026-10-29. uv gives one command from a fresh copy to a filled environment, with nothing to
  activate, and a lock file it refuses to drift from. It can also run the suite on any Python that
  meets the floor, which is the check SDD § 11 R-8 lacked (SDD § 9 TO-9).
- **A plain `uv sync`.** It lost because it rewrites a stale lock file instead of refusing it, and
  C-8 asks for the versions the suite last passed with. No uv setting makes `--locked` the default,
  so the flag is typed (SDD RN-62).
- **The machine's `python3` fixed as the suite's interpreter.** It lost because the floor is what
  `requires-python` states, and a uv-managed interpreter meets it as well as a system one does (SDD
  RN-62).

## Consequences

Easier: the tracker's setup is two commands. There is nothing to install, pin or audit before the
tracker runs, and every line that runs is in the copy the reader holds. The suite's setup is one
command after uv is installed.

Harder: `web` owns what a framework would have owned. Escaping is the sharpest of these: one
function puts every value into a page and escapes it (SDD § 4 SEC-4), because a page built by hand
can show typed text as markup (SDD § 11 R-3). The standard library's listener is "not recommended
for production" (SDD § 11 R-7), so the loopback-only listener and the request check carry the
security weight. The suite needs one more prerequisite than the tracker. uv has its own installer
and its own releases, and no lock file names it. Nothing checks that the code runs on 3.11 itself.
The suite runs on the newest Python uv finds that meets the floor: uv's managed 3.14.5 over the
machine's 3.15.0 in a fresh clone on 2026-10-29. The end-to-end tests start the tracker from
`sys.executable`, so they test it on that interpreter and not on the reader's `python3` (SDD § 11
R-8).

Undoing the runtime costs a rewrite of `web`'s page building and an install step in the setup
instructions. `domain`, `application` and `persistence` are untouched, because no HTML crosses
`SM-1`. Undoing the environment costs a pinned requirements file regenerated from `pyproject.toml`,
the `venv` and installer commands back in the suite's instructions, and the pins test reading that
file again. No line the tracker runs changes (SDD § 9 TO-9).

**Dependence:** CPython's `http.server`, as shipped with the machine's Python, and uv. Two of
`http.server`'s facts shape other records: it refuses a request line longer than 65,536 bytes
(`handle_one_request` on Python 3.14.7, quoted in SDD § 11 R-10), which bounds what an address can
carry (ADR-0011, ADR-0007); and its documentation names the threaded server as the answer to
browsers that pre-open sockets (SDD § 11 R-4). A later Python that changes either one reopens those
records. Three of uv's facts shape this one, each read 2026-10-29 at the page SDD § 4 RT-4 names:
`--locked` refuses a lock file out of step with the manifest; `uv run` runs a command in the
project's environment with nothing to activate; and uv uses a managed interpreter that meets
`requires-python` before the machine's `python3`, and fetches one only when no Python on the machine
meets it. A uv release that changes any of them changes
what the suite proves. uv 0.11.14 was the version used on 2026-10-29 (SDD version 15). GitHub's
reading of `uv.lock` for security alerts is a fourth platform fact, and NFDR QC-40 holds it.

## Traces to

- Supersedes `products/tracker17/docs/adr/0002-standard-library-only-no-web-framework.md`, whose
  decision, alternatives and consequences this record carries whole.
- `products/tracker17/docs/SDD.md` § 4 RT-1, RT-4, SEC-4; § 9 TO-1, TO-9; § 11 R-3, R-4, R-7, R-8,
  R-10; SDD Review Notes RN-3, RN-18, RN-62, RN-63.
- `products/tracker17/docs/trail/sdd/cycle-12.md` § 5.1 — the owner's call to move the suite to uv.
- `products/tracker17/docs/trail/architecture/cycle-17.md` § 3.1 — the owner's answer that the
  records follow RT-4 to uv.
- `products/tracker17/docs/trail/sdd/cycle-1.md` § 2.1 — the owner's answer that confirmed the
  runtime, "confirm, with four additions". The addition that the test dependencies go into a `venv`
  is the one this record replaces.
- `products/tracker17/docs/SRS.md` C-2, C-7, C-8, NFR-10, RN-23.

## Binds

QC-19, QC-36, QC-39, QC-43, QC-59, QC-60.
