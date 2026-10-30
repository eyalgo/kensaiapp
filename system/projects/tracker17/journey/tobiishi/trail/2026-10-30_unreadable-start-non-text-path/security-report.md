# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit — `products/tracker17/docs/nfdr.md` QC-40, "no audit command exists for this product: the Python packet names none and tracker17 installs none". No advisory was answered on this branch; the package feed QC-40 relies on is recorded there as down. Detailed under *Dependency audit*.

## Dependency audit
skipped — the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` § 2 QC-40 reads "No command can measure a window, and no audit command exists for this product: the Python packet names none and tracker17 installs none", and § 10's rows carry no audit command. By the shared rules no command was invented and no tool reached for. The change moves no pin and adds no dependency: its diff touches `products/tracker17/main.py`, `products/tracker17/web/pages.py` and three test modules only (`git diff --stat main...HEAD`).

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none | — | — | the NFDR names no audit, so none ran | — |

## Exceptions and upkeep rows
none

## Holes in the code
none.

Threat lists applied: the product is code that serves and processes input (a loopback HTTP server over saved data), so the OWASP Top 10:2025 list and Anthropic's five categories were read over the change's two production files, with the NFDR's four trust boundaries (§ 2 B-1 to B-4) and § 3 as the model. The agentic list does not apply: the product holds no skill, prompt or launcher.

What was traced:

- **The path's entry.** The location reaches `main.start` from the operator's own command line and is made absolute at `main.py:126`. A command-line value is trusted (the sceptical pass's exclusions), and nothing a request carries reaches either new line of code.
- **The page (B-3, QC-36).** `web/pages.py:2650` `_shown_location` rewrites only characters in U+DC80–U+DCFF into `\xNN` (lowercase hex, no `<`, `&` or `"` produced), and its result still enters the page through the one `_escape` (`web/pages.py:455`, `html.escape(..., quote=True)`) at `web/pages.py:2677`. The order — escape the surrogates, then HTML-escape — cannot bypass the escape, and `<`, `&` and `"` in a path stay escaped (spec CP-761, proven by the integrity report's `a<b>&\xe9` case). No new way of putting a value into a page was added.
- **The site (B-1, QC-7, QC-31, QC-32).** `web/routes.py:1335` `UnreadableSite` is unchanged: the page is built once at start, every request still passes `_refused_before_routing`, a `POST` body is never read, and no request reaches the saved data (SD-4, QC-51; the integrity report's unchanged-bytes checks).
- **The console line.** `main.py:188` `_unreadable_line` now formats the location through `main._shown_location` (`main.py:164`), the same function the ready line already used; it writes to standard output only, from `main.py`, so QC-45 holds. A terminal control character inside a directory name is written as it was before the change and is the operator's own name: no concrete attack, confidence below the floor.
- **Not new attack surface.** No new route, header, file write, socket, import or dependency; the diff is two display functions and docstrings (the integrity report's task-2 checks against the merge base).

## Not checked
- The dependency audit, because the NFDR names none (above).
- The suite was not run by this step: nothing was fixed or bumped, so there was no fix to keep on a green run. The integrity report's green run on this tree (`a139300f1`) stands as the last suite result.
