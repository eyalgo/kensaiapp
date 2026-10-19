# Writing bar — northbay

**Status:** Draft
**Owner:** Content Manager
**Version:** 3 — the abbreviation rule, folded from cycle-2.

## 0. Where this sits

This is the bar for every document kensaiapp authors in northbay. How wide that runs, and what a
writing bar reaches and does not reach, belong to
`prompts/rich.md`. Read them there. This document neither
restates them nor changes them.

## 1. The bar

**Who the reader is.** The vendor's duty engineer. They act on what we write with no access to this
repo, and no way to come back with a question before they act.

**How a document opens.** The first line says what the document is for and who acts on it. A reader
who stops there still knows whether it is the one they wanted.

**How long a sentence runs.** Two short sentences beat one long one. Stacked clauses are the
problem, not length.

**No shorthand a reader outside the team would have to decode.** Where a real technical name is
needed, what it does goes in the same sentence. An abbreviation is spelled out at its first use in
every document, with the short form in brackets after it — release candidate (RC) — and the short
form alone after that.

**How the binding words bind.** *Must* is a requirement. *Should* is a requirement with a named
exception in the same paragraph — an unpromoted *should* with no exception beside it is a *must*
written weakly, and is read as one. *May* is permission and nothing more.

**How a claim declares its kind.** A fact names where it came from in the same sentence. Reasoning
says it is reasoning. A choice nobody has confirmed says so, and says who confirms it.

**What northbay's own subject adds.** A release record names the commit it was built from, in the
document as in the record itself — never "latest" and never a branch name
(`system/doctrine/kensaiapp_doctrine.md` § Releases). A document that names a scheduled job names its
hand-run twin in the same place (§ Scheduled work).

## 3. Review notes

- **§ 1, the reader** — the owner's override in cycle-1: the checklists are pasted into the vendor's
  incident channel, and their duty engineer acts on them with no access to the repo.
- **§ 1, no shorthand a reader outside the team would have to decode** — the owner's answer in
  cycle-2: spelled out at first use everywhere, short form in brackets, short form alone after that.
- **§ 1, the commit-not-"latest" rule** — `system/doctrine/kensaiapp_doctrine.md` § Releases.
