# Self-answer report — `adr/` and `nfdr.md` (tracker17)

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md` (every item lands in `nfdr.md`)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-06
- **Sources re-read:**
  - https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-Fetch-Site — `same-origin` is "same scheme, host and port"; `same-site` is the same site "including the scheme"; `none` is "a user-originated operation", such as typing an address or opening a bookmark; "The header is only included in requests to potentially trustworthy URLs."
  - https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Secure_Contexts — an origin with a host in `127.0.0.0/8` or `localhost` is potentially trustworthy, so the browser sends the tracker the header.
  - https://developer.mozilla.org/en-US/docs/Glossary/Site — "the port number is ignored when determining the site". The page says nothing about a host that is an IP address.
  - https://html.spec.whatwg.org/multipage/browsers.html, "obtain a site" — "If origin's host's registrable domain is null, then return (origin's scheme, origin's host)." So `127.0.0.1` on another port is the same site.
  - https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors — "A policy that declares `default-src 'none'` still allows the resource to be embedded by anyone"; "This directive is not supported in the `<meta>` element"; `'none'` means "This resource may not be embedded."

Items were decided in the companion's order. Nothing was reordered.

## Items worked

### 2.1 — A form submission is accepted only when the browser marks it same-origin, not merely when it is not cross-site

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft holds for the reason it gives, and I re-read both sources at the vendor. A site
  ignores the port. For an IP-address host, the HTML standard makes the site the scheme and the host
  only. So any other program serving pages on `127.0.0.1` sends `same-site`, and a check that refuses
  only `cross-site` would let its form submissions change tracker data. SRS NFR-4 forbids that: "The
  tracker refuses any request that does not come from its own pages". The browser does send the
  header here, because loopback is a potentially trustworthy origin.
  **The addition: the draft answers a smaller question than SDD § 4 SEC-2 settles.** SEC-2 checks
  *every* request ("Every request passes one check"), and QC-32 binds only form submissions. As
  drafted, no entry carries SEC-2's refusal of a non-submission request marked `cross-site`. So the
  answer keeps both halves. Any request marked `same-site` or `cross-site` is refused. A form
  submission must be marked `same-origin`. The narrower rule cannot apply to every request: the
  operator typing the address or opening a bookmark sends `none`, and refusing that would stop the
  tracker opening.
  **Failure paths.** *Absent:* a submission with no header, from an old browser or a hand-written
  client, is refused. That is safe, because SRS NFR-13 supports Chromium only. *Refused:* the
  refusal changes nothing (QC-32 already says so). *The test harness:* the layer-3 tests, and
  `tests/timed_run.py`, which times every action through `web` (SDD § 4 TS-5), must send
  `same-origin` on every submission, or they measure refusals. That is named in the slot. *Not
  covered:* a local program that writes its own headers. It is not a browser, so no request check
  can stop it, and item 2.5's answer records that case.
  **Where the change lands.** QC-32 is this document's, and the slot confirms it. SEC-2's wording is
  the CTO's. The item itself said the CTO restates SEC-2 on confirm, and nothing else would carry
  that to the SDD, which is settled and had no companion. So it is raised as
  `products/tracker17/docs/SDD_open_issues.md` § 2.1, committed in `86c8acfb0` before this slot was
  written. I came close to a plain *confirmed*. What tipped it was SEC-2's every-request scope, which
  the draft drops without saying so.

### 2.2 — No page can be shown inside a frame

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft holds. A page that frames the tracker can lead the operator's own click to a
  submission from the tracker's own page. The browser marks that submission `same-origin`, so QC-31
  and QC-32, as confirmed in item 2.1, both let it through. SRS NFR-4's "cannot … change" would then
  fail. I re-read the MDN source: `frame-ancestors` does not fall back to `default-src`, so SEC-3's
  load-only-from-self policy leaves framing open.
  **The addition is a failure path the draft does not reach.** The same MDN page says the directive
  "is not supported in the `<meta>` element". A policy written as a tag in the page would carry the
  directive and do nothing. So the policy is sent as a response header, and QC-33's layer-3 test
  reads it from the header. SEC-3 says "served with a policy", which fits a header, but nothing
  forbade the tag until now.
  **Decided together with 2.1:** that item's same-origin rule is what makes framing the remaining
  way in, and this item closes it.
  **Where the change lands.** QC-33 is this document's, and the slot confirms it. The SEC-3 addition
  is the CTO's, as the item said. It is raised as `products/tracker17/docs/SDD_open_issues.md` § 2.2,
  in the same commit `86c8acfb0`. SEC-3 is silent here rather than wrong, and on its own that might
  not earn a cycle. But the item's confirm presupposed the CTO adding it, and once § 2.1 opens the
  SDD companion, the second item costs no extra round.

### 2.3 — `web` imports neither `domain` nor `persistence`, and the refusal types it maps live in `errors.py`

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** overridden
- **Why:** The item bundles an import rule with a placement. The import rule holds, and the
  placement is replaced. *Was:* QC-16 forbids `web` importing `domain` and puts the refusal types in
  `errors.py`. *Now:* the same import rule, with the refusal types in `domain/`, reaching `web`
  through `application`.
  **The import half holds.** SDD § 3's direction of dependence lists every import ("`web` imports
  `application` … `main` imports all four … Every part may import `errors.py`"). Reading it as
  complete is the natural reading of a list that ends by naming `main`'s four. RT-10's "through
  `application`" points the same way.
  **The placement half does not hold for the reason given.** RN-5 rests it on one sentence of SDD
  § 3's units line, "No part owns more of that file than its own subclasses". Two clearer SDD
  sentences put the refusal types in `domain/`. The `domain` row says "The rule core, as the
  directory `domain/` … It holds the entities, … and one typed refusal per refused condition". The
  same units line says "every typed error in every part derives from" the base in `errors.py`. The
  draft's own counter-reading, `web` importing `domain`, breaks the dependency list. It missed a
  third reading that keeps every SDD sentence true: the types live in `domain/`, and `application`
  hands them on. SM-1 already has `application` own the seam whose outward side carries "a typed
  refusal". Handing on a type is no rule, so QC-21's "owns no rule of its own" holds.
  **Why this is the owner's seat here and not the CTO's.** The draft sent it to the CTO because two
  readings were defensible. One reading is consistent with every SDD sentence, so the SDD needs no
  change, and the answer lands in QC-16 and RN-5 only. I came close to raising it on the SDD. What
  tipped it was finding the reading that keeps all three SDD sentences true.
  **Failure paths.** *Absent:* `domain` adds a refusal that `application` does not hand on. Then
  `web` cannot map its type, and SRS AC-12's test for that refusal, which QC-5 names, fails on the
  wrong reason. The gap is caught. *Persistence:* SM-4 has `persistence` receive refusals from
  `domain`'s constructors, and QC-15 already lets it import `domain`, so nothing moves there.
  **Reported, not corrected:** the item's "If overridden" names only the `web`-imports-`domain`
  alternative. That text is the producing skill's to correct on its fold.

### 2.4 — The SDD's three test layers sit on the doctrine's seven as § 9 maps them

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The mapping holds against both doctrine files, read at their source.
  `<CORE>/doctrine/engineering/testing_doctrine.md` decides layer 3 against layer 5 "by which door you
  enter". It says "A product with a UI does not get the exemption" from layer 4. It says "Where QA
  is not active on a project, record layers 6–7 in `docs/nfdr.md` § 9 as QA-role-owned, naming what
  verifies them instead", and § 9 does that. `<CORE>/doctrine/engineering/testing_python.md` answers
  layer 6 with "pytest, and no new dependency" under `tests/architecture/`, which keeps SDD § 4
  RT-1's standard-library-only runtime and adds no test dependency. It also has a Python product
  with a UI record its layer-4 tool in § 9, and § 9 records pytest.
  **Two additions, both from check 4.** *A self-contradiction:* § 9 scopes layer 1 to "`domain`:
  every rule, with no file and no clock". QC-30's `verified by:` names layer 1 for a test of the
  address constant that `main` passes to `web`, which is not `domain`. The row should also take
  that check, because it needs no file, socket or clock. The other fix, moving QC-30 to another
  layer, would gain nothing. *The empty case:* a layer-6 walk that finds no module passes. A walk
  rooted at the wrong directory, or run before the first slice builds the parts, would report a
  clean tree it never read. `testing_python.md` warns of the same blind spot ("A layer-6 test that
  reads a hardcoded list is a layer-1 test wearing layer 6's name"). So each walk fails when the
  directory it checks holds no module.
  **Left as it stands:** § 9's "runs in `pytest tests/`". The Python packet's own run command for
  layer 6 is `pytest tests/architecture`, which `pytest tests/` contains, so the two do not
  contradict.

### 2.5 — Authentication and authorization: the identity half of `nfdr.md` § 3 is declared not applicable

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The declaration holds, and it names its boundary, as
  `<CORE>/../skills/principal-architect/.claude/skills/product-architecture/prompts/rich.md` asks of a
  not-applicable § 3. There is one operator, no part adds a login (SDD § 4 SEC-1; SRS C-1, C-2,
  NFR-7), and QC-30 keeps the listener on loopback. The privilege half binds as QC-42 to QC-45, and
  that is right.
  **The addition is the concurrent case: a second actor on the same machine.** Loopback stops
  another machine. It does not stop another program, or another account, on this one. QC-31 and
  QC-32 stop requests a *browser* sends on behalf of another origin's page, because the browser
  writes `Host` and `Sec-Fetch-Site` and a page cannot forge them. A local program writes both
  headers itself, so the request check does not stop it. The declaration says "the only caller is
  someone already at the operator's machine". That is true, but it reads as "only the operator".
  So § 3 says in words that any program on the machine, under any account, can reach the tracker,
  and that with one operator on their own machine this is accepted.
  **Not the owner's call.** The risk was decided upstream: no login (SEC-1, SRS C-2) and one machine
  (SRS C-1). This answer only makes the record say what that decision already accepts. It decides
  no new risk. If a second account on the machine were in scope, that would be a change to SRS C-1
  and NFR-7 first, which the declaration already names.

## Left for the owner

### 1.1 — How long may a known critical vulnerability in a test dependency stay unfixed?

- **Bucket:** 1. Open issues — questions with no answer yet
- **Verdict:** left for the owner
- **Why:** The answer commits the owner's own time over a period: someone has to watch an advisory
  feed and act within the window, and the floor makes the gate name who watches. In this product
  that can only be the owner. It also turns on a plan I know exists and cannot see. The PRD says
  tracker17 is private "until the owner decides to publish it. Until then the owner is the only
  reader" (`products/tracker17/docs/PRD.md` § Assumptions), and when, or whether, that happens is
  the owner's alone. A window means something different before publishing, when only the owner
  installs the pins, than after, when strangers do.
  **Reported, not corrected: the item's routing does not hold.** It says the window's "home is SRS
  § 4.3, so the answer reaches the SRS through the CTO before QC-40 can cite it". But a doctrine
  floor exists (`<CORE>/doctrine/engineering/quality_defaults.md` § Dependencies). For that case the
  product-architecture prompt says: "apply it and cite it … you realize a floor as an entry with this
  product's own measure" (`product-architecture/prompts/rich.md` § *When upstream is silent*, case 1).
  So the window lives in QC-40 itself, citing the floor, and no SRS round is needed. That fact takes
  one branch away from the owner's choice without making it, so it belongs in the answer below and
  is not a split.
- **The answer I would have given:** No remediation window binds while tracker17 is unpublished.
  QC-40 says so in those words, with the reason. Until publishing, the owner is the only person who
  installs the test dependencies (PRD § Assumptions). They run only to test, never when the tracker
  runs (SDD § 4 RT-1, RT-4). The browser the suite drives opens only the tracker's own loopback
  pages. QC-40's existing gate stays: no pin with a known critical advisory at the moment a change
  adds or changes a test dependency, reviewed at `development-design`. QC-40 names publishing as
  what ends this. On that decision a window is set, starting when the advisory is published, with
  the owner named as the one watching the feed. *Not covered, and named:* an advisory published
  against an existing pin while changes are still being made, on a change that touches no test
  dependency, is caught by nothing until the next change that does. Before publishing, I would
  accept that.

## Skipped

None this run.

## Companions opened

- **`products/tracker17/docs/SDD_open_issues.md`** — **opened** — companion to `products/tracker17/docs/SDD.md`, landed in commit `86c8acfb0`

## Launchers owed

- **`products/tracker17/docs/SDD.md`** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
