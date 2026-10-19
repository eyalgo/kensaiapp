# Change request — 2026-10-11_readme-linux-setup-and-git

---

**Request:** Bring the README's "Running the tests" section up to what SDD v7 gives it (`docs/SDD.md:677-686`, § 6 S-1 *Artifact*, § 4 RT-4). For Linux, the section names `python -m playwright install --with-deps chromium` in place of `python -m playwright install chromium`, says that this command runs the package manager and asks for administrator rights, says the tracker and `pytest tests/` need none of it, and names the Linux systems the pinned library's documentation lists (including Debian 12). The section also says the full suite needs the copy to be a Git repository with `git` on the path, and says what the one test that otherwise fails checks: that Git ignores the saved data. It replaces the current closing paragraph about a copy that isn't a Git repository, which says the test fails but not that `git` is needed. This is reached-when 9 of station `2026-10-08_setup-instructions`; reached-when 1 to 8 stay true. The README text must keep `docs/CONTENT.md` § Grammar and mechanics (no sentence over 20 words, none saying "today", "yesterday", "tomorrow", "now", "ago" or "recently"), so reached-when 8's grep still matches nothing. Sizing: one section of one file, one honest merge. Must not be weakened: no change to `main.py`, tests, other headings, commands or `docs/`; "How it's built" and "The documents" stay as they are, and the start prints and serves what it does today.
**Category:** bug
**Behaviour:** changing
**Classified because:** station reached-when 9 and `docs/SDD.md:677-686` state content the README lacks (`grep -n -F -e '--with-deps' -e 'Debian 12' products/tracker17/README.md` matches nothing), a violated stated contract; it adds instructions a reader acts on, so it is not text only reworded.

---

**Sealed:** 2026-10-11 — accepted; merged to `main` via `--no-ff`.
