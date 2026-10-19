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

`SRS`, `SDD` and `FDR` are `products/tracker17/docs/SRS.md`, `SDD.md` and `fdr.md`. `QC-n` and `RN-n`
are entries of `products/tracker17/docs/nfdr.md`. None of the nine records in `adr/` waits on an item
here; every item lands in `nfdr.md`.

---

## 1. Open issues — questions with no answer yet

### 1.1 How long may a known critical vulnerability in a test dependency stay unfixed?
- **Lands in:** `nfdr.md` QC-40
- **Why it matters:** the quality floor for dependencies asks for a stated remediation window that
  starts when the advisory is published: "A product that names no window has an obligation nobody is
  late against" (`<CORE>/doctrine/engineering/quality_defaults.md` § Dependencies). tracker17 runs on
  no third-party package, but its test suite installs pinned packages and a browser (SDD § 4 RT-4).
  No upstream document states a window, and the number is a product call, not one this seat can
  derive. Its home is SRS § 4.3, Security & Privacy, so the answer reaches the SRS through the CTO
  before QC-40 can cite it. "No window, because the dependencies run only on the owner's machine to
  test" is also an answer, and QC-40 would then say so.
- **Answer:** <the owner fills this in>

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

### 2.1 A form submission is accepted only when the browser marks it same-origin, not merely when it is not cross-site
- **Lands in:** `nfdr.md` QC-32
- **Drafted into the records:** QC-32 refuses a form submission the browser does not mark
  `Sec-Fetch-Site: same-origin`, so a submission marked `same-site` is refused like one marked
  `cross-site`. SDD § 4 SEC-2 says "a request the browser marks as coming from another site". RN-3
  records the reading.
- **Rationale:** SRS NFR-4 says "The tracker refuses any request that does not come from its own
  pages". A site is wider than a page's origin: "the port number is ignored when determining the site"
  (https://developer.mozilla.org/en-US/docs/Glossary/Site), while `same-origin` means "same scheme,
  host and port" (https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-Fetch-Site).
  Any other program serving pages on the operator's machine — a development server on another port —
  sends `same-site`, and a check that refuses only `cross-site` lets its pages change tracker data.
  Read literally, SEC-2's "another site" would let them; read as NFR-4 requires, it does not. This
  seat records and does not re-decide the SDD, so the CTO's seat confirms the reading and, on confirm,
  restates SEC-2 to say "origin".
- **If overridden:** QC-32 refuses only `cross-site`, RN-3 records why, and the gap above stands
  against NFR-4 as a known one. No record in `adr/` moves.
- **Confirm or override:** confirm, with an addition. SEC-2's every-request scope stays too: a request
  of any kind that the browser marks `same-site` or `cross-site` is refused. A form submission must be
  marked `same-origin`, so one with no `Sec-Fetch-Site` header, or marked `none`, is refused as well.
  The layer-3 tests, and `tests/timed_run.py`, which drives actions through `web`, send `same-origin`
  on every submission. SEC-2's restatement is carried at `products/tracker17/docs/SDD_open_issues.md`
  § 2.1 (commit `86c8acfb0`). Reasoning: `products/tracker17/docs/trail/architecture/self_answer-1.md`
  § 2.1.

### 2.2 No page can be shown inside a frame
- **Lands in:** `nfdr.md` QC-33
- **Drafted into the records:** QC-33 requires every response to carry `frame-ancestors 'none'` in
  its page policy. SDD § 4 SEC-3's policy does not say it. RN-4 records the addition.
- **Rationale:** SRS NFR-4 says "A web page from any other origin, open in the operator's browser,
  cannot read, change or delete tracker data". A page that frames the tracker can lead the operator's
  own click to a submission from the tracker's own page, which the browser marks `same-origin` and
  QC-31 and QC-32 both let through. SEC-3's policy, loading "only from the tracker's own address",
  does not stop framing: "A policy that declares `default-src 'none'` still allows the resource to be
  embedded by anyone"
  (https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors).
  The directive is one more line in the policy SEC-3 already sends. On confirm, the CTO's seat adds
  it to SEC-3.
- **If overridden:** QC-33 is removed and its ID is retired, never reused. NFR-4's "cannot change"
  then holds only against requests, not against a click led from another origin, and RN-4 records
  that the gap is accepted.
- **Confirm or override:** confirm, with an addition. The policy carrying `frame-ancestors 'none'` is
  sent as a response header, because the directive "is not supported in the `<meta>` element"
  (https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors).
  QC-33's layer-3 test reads it from the header. SEC-3's addition is carried at
  `products/tracker17/docs/SDD_open_issues.md` § 2.2 (commit `86c8acfb0`). Reasoning:
  `products/tracker17/docs/trail/architecture/self_answer-1.md` § 2.2.

### 2.3 `web` imports neither `domain` nor `persistence`, and the refusal types it maps live in `errors.py`
- **Lands in:** `nfdr.md` QC-16
- **Drafted into the records:** QC-16 lets `web/` import `application` and `errors` only, and places
  the refusal types in `errors.py`. RN-5 records the reading.
- **Rationale:** SDD § 3's direction of dependence lists "`web` imports `application`" and no other
  part for `web`. SDD § 4 RT-10 has `web` receive the text lengths "through `application`". SDD § 3's
  units line says "`errors.py` holds the single base error that every typed error in every part
  derives from. No part owns more of that file than its own subclasses", which reads as each part's
  typed errors living there. But SDD § 3's `web` row does not forbid importing `domain` in words, and
  SDD § 4 OB-4 has `domain` raise the refusals `web` maps, so a competent reader could place the types
  in `domain` and let `web` import them. Two defensible answers make it a call, and it is the CTO's.
- **If overridden:** QC-16 allows `web` to import `domain`'s refusal types and nothing else of
  `domain` — or whatever the override names — and RN-5 is rewritten. ADR-0001 does not move: it
  records the SDD's direction of dependence word for word.
- **Confirm or override:** override: keep QC-16's import rule, so `web` imports `application` and
  `errors` only and never `domain`. Drop "The refusal types `web` maps live in `errors.py`". The
  refusal types live in `domain/`, as SDD § 3's `domain` row says ("It holds … one typed refusal per
  refused condition") and as its units line says ("every typed error in every part derives from" the
  base in `errors.py`). `web` reaches them through `application`, which owns SM-1, the seam that hands
  "a typed refusal" outward. `application` names them for `web` and adds none of its own. RN-5 records
  this. No SDD sentence moves. Reasoning:
  `products/tracker17/docs/trail/architecture/self_answer-1.md` § 2.3.

### 2.4 The SDD's three test layers sit on the doctrine's seven as § 9 maps them
- **Lands in:** `nfdr.md` § 9
- **Drafted into the records:** SDD § 4 TS-1's unit tests are layer 1. Its integration tests of
  `persistence` against real files are layer 2. Its integration tests of `web` with `application` in
  one process with no socket are layer 3, and their assertions on the built page are layer 4. Its
  end-to-end tests are layer 5. Layers 6 and 7 are QA-owned: layer 6 is written as plain pytest under
  `tests/architecture/` with the change that first builds the module it checks, and runs in
  `pytest tests/`; layer 7 has no producer, and SRS § 8's acceptance criteria are verified by the
  tests the SDD names and by the owner's run-throughs. RN-6 records the mapping.
- **Rationale:** `<CORE>/doctrine/engineering/testing_doctrine.md` decides layers 3 and 5 "by which
  door you enter": a test that calls `web` in one process enters inside the listener, so it is layer
  3. The same file says of layer 4, "A product with a UI does not get the exemption", so it cannot be
  omitted for want of a UI. And it says "Where QA is not active on a project, record layers 6–7 … as
  QA-role-owned, naming what verifies them instead". No upstream document maps the SDD's three layers
  onto the seven, and most of the structural entries in §§ 1–3 name layer 6, so the mapping decides
  who writes those checks and when.
- **If overridden:** § 9's table changes and every entry naming a layer follows it. An override that
  puts layer 6 elsewhere — a separate command, or no structural tests until QA runs — moves the
  `verified by:` tail of every layer-6 entry and every matching row of § 10.
- **Confirm or override:** confirm, with two additions. First, § 9's layer-1 row also takes QC-30's
  address check, which tests a constant outside `domain` with no file, socket or clock. The row
  currently scopes layer 1 to `domain`, while QC-30 names layer 1. Second, every layer-6 walk fails
  when it finds no module in the directory it walks, so a walk rooted at the wrong path cannot pass
  by finding nothing. Reasoning: `products/tracker17/docs/trail/architecture/self_answer-1.md` § 2.4.

### 2.5 Authentication and authorization: the identity half of `nfdr.md` § 3 is declared not applicable
- **Lands in:** `nfdr.md` § 3
- **Reason it does not apply:** there is one operator, on the machine the tracker runs on, and no
  part adds a user, a role or a login (SDD § 4 SEC-1; SRS C-1, NFR-7; FDR PD-16, OOS-4). The boundary
  that makes it true is QC-30: the tracker answers only on its loopback address. A listener on any
  other address, or a second operator, would change it, and either is a change to SRS C-1 and NFR-7
  first. The privilege half of § 3 is **not** declared away: it binds as QC-42 to QC-45 — which part
  may write files, open sockets, read the clock and write to the console.
- **Confirm or override:** confirm, with an addition. § 3 also names what the loopback boundary does
  not cover. Any other program on the machine, under any account, can reach the loopback address.
  QC-31 and QC-32 stop requests a browser sends for another origin's page. They do not stop a local
  program, which writes its own `Host` and `Sec-Fetch-Site`. With one operator on their own machine
  (SRS C-1, NFR-7; SDD § 4 SEC-1), that caller is already inside the machine, and the declaration says
  so in those words. Reasoning: `products/tracker17/docs/trail/architecture/self_answer-1.md` § 2.5.

## 3. Raised from downstream — an item from a seat that did not write these records

None.
