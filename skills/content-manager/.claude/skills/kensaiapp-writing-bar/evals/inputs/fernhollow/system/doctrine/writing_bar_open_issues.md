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

## 2. Choices to confirm

### 2.1 Every document that names a number states where the number came from, in the same sentence
- **Written into the writing bar:** "Every document that names a number states where the number came
  from, in the same sentence — the script that produces it, or the record it was read off."
- **Grounds:** none: the Content Manager's call, made to keep the bar coherent with the reader in § 1.
  The duty engineer cannot open the file a number came out of, so the document has to carry it.
- **Confirm or override:** override: not every document. On a release record, yes — that is the
  number people act on, and it goes in. On a checklist, drop it; nobody reading a checklist at 3am
  needs a provenance clause hanging off every line. Keep it where the number would be acted on.

### 2.2 Deliberately absent — nothing is stated about how long a document may be
- **Reason recorded in the writing bar:** a checklist and a release record have nothing useful in
  common on length, and how short a checklist has to be is Way 1's business (`system/michi.md`,
  `one-head`) rather than this bar's.
- **Confirm or override:** confirm
