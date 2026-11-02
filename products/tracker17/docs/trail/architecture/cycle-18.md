# Architecture open issues — tracker17

> Companion to `adr/` and `nfdr.md`. The Principal Architect authored both records
> non-interactively; this file holds what the run could not settle from its inputs — the SRS, the SDD
> and the FDR.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-architecture`. It folds your answers into the records and drops the resolved items.
> When nothing is left open, `product-architecture` **deletes this file**: no file = the records are
> done.
>
> Your answers are never thrown away. Each time the Principal Architect folds them in, it first copies
> this file whole to `docs/trail/architecture/` — so what you decided, and why, stays readable and
> citable for good.
>
> **§ 3 is raised, not asked.** These records bind every later change, so the seats that live under
> them find gaps the authoring run could not. § 3 is where such a seat says so, against both records
> — an ADR's binding and an NFDR obligation reach the same file.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

### 2.1 QC-39 was rewritten by a delivery-tier commit, with no Review Note and no new version

> **No `product-architecture` run wrote this item.** A `companion-self-answer` run raised it on
> 2026-10-29 while answering item 3.1. It read the NFDR whole and found QC-39's text changed after
> version 19 settled, by two Developer commits, `79a743286` and `5eb5ec557`. Nothing in the NFDR
> records the change. Reasoning: `docs/trail/architecture/self_answer-22.md`.

- **Lands in:** `nfdr.md` QC-39, and a Review Note
- **Drafted into the records:** Nothing yet. The draft is that the fold records QC-39's move from
  unmet to met in a Review Note and a new version line, as each other change to an entry is
  recorded. RN-54 recorded that QC-39 started unmet, as RN-22 did for QC-62. The note names
  the two commits and the evidence the new text carries: `uv lock --check` and its `--offline` form
  exited 0, and in a fresh clone `uv sync --locked` then `uv run pytest tests/unit tests/architecture`
  exited 0. It also checks that text against the tree. On 2026-10-29,
  `tests/architecture/test_pins.py:44` holds the test the entry names. The entry's words stay if
  they hold, because they now state a true fact.
- **Rationale:** The constraint set is revised in place only under provenance, and nothing
  downstream edits it. A discrepancy found during a change comes back here to be recorded. Version
  19's header and RN-54 still say QC-39 starts unmet, and the entry now says it is met, with no note
  between them. A cold reader cannot tell that the change was authorized or who checked it. No fact
  in the entry looks false, so this is a provenance gap, not a correction. The fold on item 3.1 is
  happening anyway, so recording it costs that run one note.
- **If overridden:** QC-39 stays as the Developer wrote it, and the NFDR keeps an entry changed with
  no trace. That leaves standing the precedent that a delivery-tier run edits the constraint set
  directly.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-40's first-review check of the dependency graph could not read the graph
- **Raised by:** PM — 2026-10-29
- **Which record:** `nfdr.md` QC-40
- **Tracked by:** `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv`
- **What it blocks:** QC-40's *verified by* (`nfdr.md:386-390`) says "The first review after
  `uv.lock` is on `main` also checks that the repository's dependency graph lists the packages
  `uv.lock` fixes; where it lists none, the package feed is down". That first review has happened,
  and its check could not be made. It recorded that `gh api repos/<owner>/<repository>/dependency-graph/sbom`
  returned `Not Found (HTTP 404)`, exit 1, which says neither that the graph lists the packages nor
  that it lists none. An OSV query on the 16 registry versions `uv.lock` fixes found no advisory
  (2026-10-29), which is not the GitHub feed QC-40 names. So whether the owner's Dependabot feed for
  `uv.lock` is live is unknown, and QC-40 names no fallback for a review that cannot read the graph.
- **Where it shows:** QC-40's *verified by*, the first-review moment; no row in § 10, as QC-40 is a
  review gate (`nfdr.md:689`).
- **If a document has to be written:** none — QC-40 says how the moment is met when the graph cannot
  be read, with which access, and whether it stays owed until then.
- **Answer:** The feed is down, not unreadable, and QC-40 should say so and say how the moment is
  met. Measured 2026-10-29 from the owner's account, which is admin on the repository, with a token
  carrying `repo`: `gh api repos/<owner>/<repository>/dependabot/alerts` is refused with HTTP 403,
  "Dependabot alerts are disabled for this repository". The repository is private, and its
  organization, on GitHub's free plan, turns the dependency graph on for no new repository. So the
  404 the review recorded is that state, the review's "where it lists none" branch has fired, and this
  item is the discrepancy QC-40 asks for. QC-40 should state three things. (1) The check is made by an
  account with admin on the repository that holds tracker17. It reads the Dependabot alerts endpoint
  first, which states its own state: a list means the feed is on, and the "disabled" refusal means
  it is down. Then it checks that the dependency graph lists the packages `uv.lock` fixes, through
  the repository's dependency-graph page or GitHub's asynchronous SBOM export. The entry names no
  synchronous `dependency-graph/sbom` call, which GitHub says closes after 2026-11-13. A call that
  answers neither way, for want of access or a network, is not a reading, and the moment is not met.
  (2) The moment stays owed until a review reads the graph listing those packages, which is the
  first review after the feed is turned on. (3) Until then the entry says the package feed is down,
  not that the owner watches through two feeds. The pins are still checked against published
  advisories at every `development-design` review, the moment QC-40 already names. A stretch with no
  review leaves the packages unwatched, and that is the cost of the feed being off. Turning on
  Dependabot alerts and the dependency graph is a repository setting only the owner may change, and
  choosing another feed stays the owner's call (RN-54). Neither is written into QC-40. Reasoning:
  `docs/trail/architecture/self_answer-22.md`.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
