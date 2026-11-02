# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-29
- **Sources re-read:**
  - GitHub's REST API, read live on 2026-10-29 from the owner's account, which is admin on
    `<owner>/<repository>`, with a token whose scopes include `repo`.
    `repos/<owner>/<repository>` says `"private": true`.
    `repos/<owner>/<repository>/dependabot/alerts` is refused with HTTP 403, "Dependabot alerts
    are disabled for this repository". `repos/<owner>/<repository>/dependency-graph/sbom` returns
    HTTP 404 "Not Found", the result the review recorded. `orgs/kensaiapp` says
    `"plan": "free"` and `"dependency_graph_enabled_for_new_repositories": false`.
  - https://docs.github.com/en/rest/dependency-graph/sboms says of the synchronous export: "This
    operation is closing down and will not be accessible after November 13, 2026". It points to an
    asynchronous flow, `sbom/generate-report` then `sbom/fetch-report/{sbom_uuid}`. It defines 404
    only as "Resource not found".
  - https://docs.github.com/en/rest/dependabot/alerts says classic tokens need the `security_events`
    scope for the repository list. It gives no meaning for 403 beyond "Forbidden". The refusal's own
    message is what names the state.
  - https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/configuring-the-dependency-graph
    says the graph is enabled per repository under **Settings → Advanced Security**. The page about
    the graph says "Repository administrators can enable or disable the dependency graph".

## Items worked

### 3.1 — QC-40's first-review check of the dependency graph could not read the graph

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** answered
- **Why:** The feed is down, not unreadable. That turns the item from "we don't know" into the
  discrepancy QC-40 already asks the reviewer to bring back here.
  1. *Whose it is.* The edit lands in `nfdr.md` QC-40, which is this seat's. The answer commits
     nobody to anything. It says how the review moment is met and what the entry says while the feed
     is off. Two things near it are the owner's, and the answer names both without deciding them.
     Turning on Dependabot alerts and the dependency graph is a setting on the owner's repository.
     Choosing a different package feed was left to the owner in RN-54: "Choosing another feed would
     be the owner's call, so no fallback is written". Neither is a second question in the item. The
     item asks how QC-40 reads a review that cannot read the graph, so nothing here splits.
  2. *What the measurement shows.* The item says the 404 "says neither that the graph lists the
     packages nor that it lists none". Read alone, that is true. A second call settles it: the
     Dependabot alerts endpoint, read with admin access, refuses with "Dependabot alerts are disabled
     for this repository". The organization, on the free plan, enables the dependency graph for no
     new repository. Nothing reads a manifest for alerts there. So the package feed QC-40 names,
     "Dependabot alerts on the repository that holds tracker17", is off. RN-18 rested the feed on it
     without measuring the repository. When it was last on, if ever, can't be read from here.
  3. *Settled record.* The answer keeps QC-40's obligation, its 30-day window, its owner as watcher
     and its two review moments. It adds no feed, so it respects RN-54. It agrees with ADR-0013 and
     SDD § 4 RT-4, which keep `uv.lock` as the file the feed reads. It names no synchronous SBOM
     call, because GitHub closes that call after 2026-11-13. A check written against it would fail
     the same way in two weeks for a different reason.
  4. *Failure paths.* **Absent:** a call that answers neither way, for want of access or a network,
     is not a reading, and the moment stays unmet. That is why the answer names the access, an
     admin account on the repository. **Empty:** an enabled feed with no alerts returns an empty
     list. That means the feed is on with nothing open, and the graph check then confirms it reads
     `uv.lock`. **Stale:** the feed could be switched off after the first review passes. The
     every-review check of the pins against published advisories still runs, and it doesn't depend
     on the feed. **Refused:** if the owner never turns the feed on, the entry says the package feed
     is down, and package advisories reach the owner only at reviews. A stretch with no review
     leaves them unwatched, and the answer names that cost rather than hiding it.
  - *What would have tipped it.* If the owner had reserved how this repository's security settings
    are run, I'd have left the item for the owner. Nothing in the records says so. QC-40 already
    makes the reviewer the one who surfaces a down feed, so recording it is this seat's.

## Left for the owner

None this run.

## Skipped

None this run.

## Raised on this document

### 2.1 — QC-39 was rewritten by a delivery-tier commit, with no Review Note and no new version

- **What the document is owed:** A Review Note and a version line recording QC-39's move from
  "starts unmet" to "is met". It names Developer commits `79a743286` and `5eb5ec557` and the evidence
  their text cites, checked against the tree. The entry's words stay if they hold.
- **Why it is worth a cycle:** *It contradicts a document it must agree with.* Here the document
  disagrees with itself. Version 19's header and RN-54 say QC-39 starts unmet, and the entry says it
  is met, with no note between them. The constraint set changes only under provenance, and the
  delivery tier doesn't edit it (`principal_architect_global.md` § *Three seams*: "A discrepancy
  found during a change is surfaced back to you and recorded here — never patched in place").
  `git log -- products/tracker17/docs/nfdr.md` shows the two Developer commits after
  `53ad18603`, the last `product-architecture` commit. The new text looks true:
  `tests/architecture/test_pins.py:44` holds the test it names. So this asks for a record, not a
  correction. The item went into § 2 in place of the section's "None." line, because a "None." left
  above an item would be false.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
