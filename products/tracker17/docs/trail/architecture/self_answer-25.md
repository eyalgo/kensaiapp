# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-30
- **Sources re-read:**
  - GitHub's REST API, read live on 2026-10-30 from an account with `"admin": true` on
    `kensaiapp/<the instance KensaiApp is developed in>`, with a token whose scopes include `repo`.
    `repos/kensaiapp/<the instance KensaiApp is developed in>` says `"private": true`.
    `repos/kensaiapp/<the instance KensaiApp is developed in>/dependabot/alerts` is refused with HTTP 403, "Dependabot alerts
    are disabled for this repository". `repos/kensaiapp/<the instance KensaiApp is developed in>/vulnerability-alerts` answers
    HTTP 404, "Vulnerability alerts are disabled". `.../dependency-graph/sbom/generate-report` answers
    HTTP 404 "Not Found", and so does `.../dependency-graph/sbom`.
    `orgs/kensaiapp` says `"plan": "free"` and `"dependency_graph_enabled_for_new_repositories": false`.
    The GraphQL field `dependencyGraphManifests` on the repository says `totalCount: 0`.
  - The same `generate-report` call on two controls, same account, same day:
    `repos/cli/cli/...` answered HTTP 201 with an `sbom_url`, and
    `repos/kensaiapp/does-not-exist/...` answered HTTP 404 with the same body this repository gets.
  - https://docs.github.com/en/rest/dependency-graph/sboms defines 404 on all three SBOM endpoints as
    "Resource not found" and nothing more. It says the synchronous call "will not be accessible after
    November 13, 2026". It names no "graph not enabled" condition.
  - https://github.blog/changelog/2026-04-14-sbom-exports-are-now-computed-asynchronously describes
    the flow and does not mention 404 or whether the graph must be on.
  - https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/configuring-the-dependency-graph
    says the graph is enabled per repository under Settings, Advanced Security. It does not say whether
    it is off by default on a private repository.

## Items worked

### 3.1 — QC-40 names an SBOM export that answers 404, and says nothing about what that answer means

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** answered
- **Why:** QC-40 should say a 404 from the export, while the alerts endpoint refuses as disabled, is
  the expected answer of a feed that is down. It should not name a cause. The item arrived with no
  draft, so this is decided from scratch.
  1. *Whose it is.* The edit lands in `nfdr.md` QC-40, which is this seat's, and it binds nobody
     outside the document. Turning the graph on is a setting on the owner's repository, and the
     owner's answer in `trail/architecture/cycle-18.md` § 3.1 already says so. The item states that as
     a fact and does not ask it, so it is no second question and nothing splits.
  2. *The item's framing holds, and its question is smaller than it looks.* It is right that the 404
     is neither of the failures QC-40 names: the account has admin and the network answered. It asks
     which of three causes the 404 means. GitHub does not say. Its page defines 404 only as "Resource
     not found", and a repository that does not exist gets the same body. So "the graph is off" is the
     strongest reading and is still an inference: the free-plan organization turns the graph on for no
     new repository, the alerts are disabled, the manifests count is 0, and the address answers 201 on
     a public repository. No private repository with the graph on was available to compare, and that
     is the one check that would have made it a measurement. It does not have to be measured, because
     every remaining cause gives the review the same result: the graph has not been read listing the
     packages, so QC-40's own sentence keeps the moment owed. What the entry lacks is only the sentence
     that stops a reviewer treating that as a new finding. Without it the same item returns at each
     review, as this one followed `cycle-18.md` § 3.1 by one day.
  3. *"No other reading without a browser."* The item is right that the entry names none, and none is
     owed. The alerts refusal already says the feed is down, and that is the entry's first step. The
     graph check only has something to read once the owner turns the graph on, and then the export
     should answer. GraphQL's manifest count is another reading, but I would not write it in: it was
     not asked for, and it reads manifests rather than the packages `uv.lock` fixes.
  4. *Settled record.* The sentence keeps QC-40's obligation, window, watcher, review moments and
     class. It keeps "want of access or a network", which still covers the case it was written for, and
     it adds no feed, so it respects RN-54. RN-56 rested "that state" on the synchronous call's 404;
     today's measurement finds the same on the asynchronous call, so RN-56 stands. No ADR mentions the
     dependency graph or Dependabot, so no record moves. The SDD's mentions (`SDD.md:2869`, `:2976`)
     concern the same feed and are unaffected.
  5. *Failure paths.* **Absent:** a token that cannot see a private repository may also get a 404, so
     the sentence is bound to "that account" and to the alerts endpoint's refusal in the same review,
     which comes from a call that reached the repository. **Empty:** the graph on but listing none of
     the packages is already "stays owed", and RN-54 says a miss comes back here. **Stale:** the export
     address could move, and a 404 from an old address would read the same. While the feed is down that
     changes nothing. **Concurrent:** not applicable, since a review only reads. **Refused:** if the
     owner never turns the graph on, the moment stays owed for good and packages stay watched only at
     reviews, the cost RN-56 already names.
  6. *Not taken.* A 404 while the alerts endpoint answers a list, and a 201 or a still-preparing fetch,
     cite no occurrence: not until they occur. The entry's "stays owed until a review reads the graph
     listing those packages" already holds them.
  - *What would have tipped it.* If a private repository with the graph on also answered 404, the
     export would be no reading at all, and QC-40 would have to name another. That would be a change
     to which reading the entry requires. I could not test it from here.

  **Note on the item's text.** Its slot was empty rather than an angle-bracketed placeholder, and I
  read that as unanswered. Its quoted call and output match today's measurement.

## Left for the owner

None this run.

One thing near item 3.1 is the owner's and the item did not ask it, so it is no verdict here. QC-40's
graph moment cannot end until the dependency graph and Dependabot alerts are turned on for the
repository, or another feed is chosen (RN-54). Until then package advisories reach the owner only at
reviews. I would turn both on: the entry already names that cost, and today's answer does not reduce it.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
