# CONTENT open issues — tracker17

> Companion to `CONTENT.md`. The Content Manager authored the verbal language non-interactively;
> this file holds the calls it made and wants your sign-off on — each with the reason behind it,
> and what moves underneath it if you override — plus the few things it genuinely could not
> settle.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**,
> then re-run `product-content`. It folds your answers into `CONTENT.md` and drops the resolved
> items. When nothing is left open, `product-content` **deletes this file**: no file = the verbal
> language is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git refuses
> to remove a file with uncommitted edits in it — so an uncommitted answer stops that run before
> it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the Content Manager folds them in, it first copies
> this file whole to `docs/trail/content/` — so what you decided, and why, stays readable and
> citable for good.
>
> **§ 3 comes from outside this run.** The verbal language is read by everyone who writes a string,
> and a seat downstream can find a pattern it has no rule for. It is recorded there, answered here,
> and folded by the same run.

---

## 1. Open issues

None.

## 2. Choices to confirm

None.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 Two clauses disagree on a path inside the underlying error text of a failed action
- **Raised by:** PM — 2026-10-30
- **Tracked by:** `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed`
- **What it blocks:** the wording standard for the second line the terminal prints when an action fails at a path holding a byte that is not text. Until this is settled, that line has two correct forms.
- **Where it shows:** § Grammar and mechanics, *A path the tracker prints*, says "It is one form in every place a path is written" (`CONTENT.md:135-139`). § Message patterns, Terminal messages, says the underlying error text prints "exactly as the system reported it" (`CONTENT.md:266-267`), and RN-12 lets it carry the system's text verbatim. The system's text can hold a path: `Site._report_failure('Could not save.', OSError(92, 'Illegal byte sequence', os.fsdecode(b'/tmp/caf\xe9')))` (`web/routes.py:1327-1332`) prints `OSError: [Errno 92] Illegal byte sequence: '/tmp/caf\udce9'`, which satisfies the second clause and breaks the first. RN-33's own list of what the rule does not cover leaves this case out, and RN-33 names only the ready line, the unreadable-data line and the page. The lean is that the path form wins inside the error text, and the rest of that text stays exactly as reported: the first clause says "every place", and it is the later and more specific rule. The doubt is that a developer reading the terminal may want the system's report untouched.
- **If a document has to be written:** none beyond `CONTENT.md`, through `product-content`.
- **Answer:** <the owner fills this in>

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
