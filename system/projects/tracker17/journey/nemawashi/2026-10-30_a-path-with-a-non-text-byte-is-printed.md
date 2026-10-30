# 根回し Nemawashi seed — a saved-data path holding a non-text byte is printed, not a crash

## What it is

Serves the Way `production-grade`: tracker17 is the example app kensaiapp built (`system/satellites.md:L88`), and a start that dies with a traceback is not a finished product. When the operator's copy of tracker17 sits at a path holding a byte that is not text, the tracker cannot say where its saved data is. Both console lines raise, so the tracker does not start at all, and the unreadable-data page raises too. Measured 2026-10-30 on `products/tracker17`: `main._ready_line('127.0.0.1', 8017, Path(os.fsdecode(b'/tmp/caf\xe9/data')))` and `main._unreadable_line(...)` on the same path both give text whose `.encode('utf-8')` raises `UnicodeEncodeError`; `web.UnreadableSite(os.fsdecode(b'/tmp/caf\xe9/data'), '127.0.0.1:8017')` raises `UnicodeEncodeError` ('surrogates not allowed'). `git grep -n xe9 -- products/tracker17/tests` prints nothing: no test covers it.

Once done, the ready line, the unreadable line and the unreadable-data page each print that path in the one form `products/tracker17/docs/CONTENT.md` § *A path the tracker prints* fixes (the byte as `\xe9`, nothing else changed, no replacement mark), and a test holds each.

Why this Agari: the Agari's bars "Works" and "Simple to set up" need the tracker to start wherever the owner puts a copy (`system/projects/tracker17/agari.md`). Reasoning, not a lookup: the case is rare, and it is the only gap the four-document pass found.

## Source

Cut from `products/tracker17/docs/SDD.md` § 6 S-8 *Reached when / Behaviour*: "the console says so and names its location, and every address shows the one page that says the data could not be read, where it is"; `products/tracker17/docs/fdr.md` R-2 ("shows the local address ... and the saved data's location") and R-24, R-25 ("names its location"). The product does not do what they say on such a path, and S-8 was walked before the path rule landed (`products/tracker17/docs/CONTENT.md` § *A path the tracker prints*, read against, not drawn from). Found by `system/projects/tracker17/docs/nemawashi-refine/2026-10-11_protect-saved-data_report.md` § *The docs cut*; re-run and confirmed by this cut.

## Stations — dynamic checklist

- [ ] ready-start — a start on readable saved data at such a path prints the ready line with the path as `\xe9` and serves; a test fails today and passes after
- [ ] unreadable-start — a start on unreadable saved data at such a path prints the unreadable line and serves the unreadable-data page, each naming the path as `\xe9`; a test per surface fails today and passes after

Re-cut from `console-lines` and `unreadable-page`: split by start mode, not by surface, because an unreadable start builds the page (`UnreadableSite.__init__` encodes it) before it prints the line, so `console-lines`' "unreadable line prints and the tracker starts" could not be met until `unreadable-page` landed. The ready start is independent and lands the one path form first; the unreadable start's line and page are one S-8 behaviour and stay in one merge.

## Relation to existing work

Reopens ground walked by `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (retired); its work stands, only this path case is missing.

## Out (later / elsewhere)

No change to any document: FDR R-2, R-24 and R-25 hold as written. Not changing where the saved data lives (FDR R-16) and not the text of any message beyond the path's form.
