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

### 1.1 Does the bar say anything about how a document names a person?
- **Why it matters:** the checklists name whoever was on the rota the week they were written, and the
  duty engineer reading one has no way to tell whether that person is still the one to go to.
- **What was searched:** `system/doctrine/kensaiapp_doctrine.md` (nothing on wording), the checklists
  themselves (four of them name a person by first name), and the vendor's incident channel, where the
  same first names appear with no role beside them.
- **Answer:** Name the role, never the person — "the duty engineer", not "Priya". The rota turns over
  every week, so a personal name in a document we hand outside the team is wrong within seven days of
  being written. Where a specific person really is the only one who can do a step, that is a defect in
  the tooling and the document says so.

## 2. Choices to confirm

### 2.1 A release record names the commit it was built from, never "latest" and never a branch name
- **Written into the writing bar:** "A release record names the commit it was built from, in the
  document as in the record itself — never 'latest' and never a branch name."
- **Grounds:** `system/doctrine/kensaiapp_doctrine.md` § Releases.
- **Confirm or override:** confirm
