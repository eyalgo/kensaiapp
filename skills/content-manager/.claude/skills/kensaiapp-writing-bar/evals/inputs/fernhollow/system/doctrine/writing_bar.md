# Writing bar — northbay

**Status:** Draft
**Owner:** Content Manager
**Version:** 3 — the reader moved to the vendor's duty engineer, and the rules moved with it.

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

**Where a number comes from.** Every document that names a number states where the number came from,
in the same sentence — the script that produces it, or the record it was read off.

**What northbay's own subject adds.** A release record names the commit it was built from, in the
document as in the record itself — never "latest" and never a branch name
(`system/doctrine/kensaiapp_doctrine.md` § Releases). A document that names a scheduled job names its
hand-run twin in the same place (§ Scheduled work).

## 2. Deliberate absences

**Nothing is stated about how long a document may be.** A checklist and a release record have
nothing useful in common on length, and how short a checklist has to be is Way 1's business
(`system/michi.md`, `one-head`) rather than this bar's.

## 3. Review notes

- **§ 1, the reader** — the owner's override in cycle-1: the checklists are pasted into the vendor's
  incident channel, and their duty engineer acts on them with no access to the repo.
- **§ 1, no shorthand a reader outside the team would have to decode** — the reader settled in
  cycle-1; the owner confirmed the rule in cycle-3 and answered the abbreviation question there.
- **§ 1, where a number comes from** — none: the Content Manager's call, made to keep the bar coherent
  with the reader above. The duty engineer cannot open the file a number came out of.
