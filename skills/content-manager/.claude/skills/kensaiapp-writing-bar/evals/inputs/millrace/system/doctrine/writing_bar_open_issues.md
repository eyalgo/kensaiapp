# Writing bar open issues — northbay

> Companion to `system/doctrine/writing_bar.md` — the bar every document authored in this instance is
> held to. The Content Manager settled that bar without stopping to interview you; this file holds the
> calls it made and wants your sign-off on, each with the reason behind it and what moves underneath
> it if you override, plus the few things it genuinely could not settle.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `kensaiapp-writing-bar`. It folds your answers in and drops the resolved items. When nothing
> is left open it **deletes this file**: no file = the writing bar is settled.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git refuses to
> remove a file with uncommitted edits in it — so an uncommitted answer stops that run before it can
> commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the Content Manager folds them in, it first copies this
> file whole to `system/doctrine/trail/writing_bar/` — so what you decided, and why, stays readable and
> citable for good.

---

## 1. Open issues

### 1.1 Should the bar require an abbreviation to be spelled out on first use in every document, or only in the ones that leave the team?
- **Why it matters:** it decides whether the bar is one rule or two, and whether a reader has to know
  which of our documents they are holding before they can tell what it owes them.
- **What was searched:** `system/doctrine/kensaiapp_doctrine.md` (it binds releases and scheduled
  work, and says nothing about wording) and the release checklists themselves, which use `RC`, `SLO`
  and `EOD` without ever expanding them.
- **Answer:**

## 2. Choices to confirm

### 2.1 A document here is read by a colleague with the repo open, and the bar turns on that
- **Written into the writing bar:** "Someone on this team of five, with the repo open beside the
  document and the person who wrote it two desks away. They can open any file this document names,
  and they can ask."
- **Grounds:** `kensaiapp.md` § *What this is about* — "everything written here is read by the four
  other people on the team, all of whom have the repo open while they read it" — and Way 1,
  `one-head` (`system/michi.md`), which asks that one person can cut a release without a conversation
  first.
- **Confirm or override:** override: the reader has moved and the bar has to move with it. Since
  March every checklist we write is pasted into the vendor's incident channel, and it is acted on by
  the vendor's duty engineer, with no access to our repo and no way to ask us anything first. Write
  the bar for that reader — the one who cannot open the file we are pointing at and cannot come back
  with a question.
