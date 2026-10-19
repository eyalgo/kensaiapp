# NFDR — sealbox

**Status:** Draft
**Owner:** Principal Architect
**Version:** 1 — first authoring off the settled SRS and SDD and the Draft FDR. Three items are with
the owner in `architecture_open_issues.md`.

> The NFDR is the product's **standing obligations, consolidated and verifiable**: every quality
> constraint a change is checked against, derived from the SRS, the SDD, the FDR and the ADR — never
> invented here. It is updated in place with versioning (unlike the ADRs, which supersede).

---

## 1. Structural integrity

### 1.1 Architectural invariants

- **QC-1:** `domain/` depends on nothing outside itself — no port, no adapter, no framework.
  — *verified by:* structural check (test layer 6) *(traces to: ADR-0001)*

### 1.2 Forbidden imports

- **QC-2:** `domain/` must not import from: `app/`, `store/`, `render/`, `web/`, `cmd/`.
  `app/` must not import from: `store/`, `render/`, `web/`, `cmd/`. `store/`, `render/` and `web/`
  must not import from each other. `cmd/` may import anything.
  — *verified by:* structural check (test layer 6) *(traces to: ADR-0001; SDD § 3)*

### 1.3 Layer isolation

- **QC-3:** `domain/` owns no I/O of any kind. `store/` owns all database I/O, `render/` owns all
  temporary-file I/O, `web/` owns all HTTP I/O, and `cmd/` owns console I/O and config reads. No other
  package opens a file, a socket or the console.
  — *verified by:* structural check (test layer 6) *(traces to: ADR-0001; SDD § 3)*

### 1.4 Replaceability

- **QC-4:** Swapping PostgreSQL byte storage for any other `EnvelopeStore` implementation touches
  `store/` only; no other package changes.
  — *verified by:* review at development-design when a change touches `store/`
  *(traces to: ADR-0002; SDD § 9 TO-1)*
- **QC-6:** Swapping the PDF flattening library touches `render/` only, and the swapped renderer still
  produces a byte-stable download.
  — *verified by:* golden-file test at layer 5 (`go test ./render/... -run Golden`)
  *(traces to: FDR PD-2; SDD § 3, the `Renderer` seam)*

## 2. Security

Trust boundaries: the operator console behind the firm's own auth; the signer page, reachable by
anyone holding a link; the SMTP relay, operator-supplied and outside our control.

- **QC-5:** `audit_events` has no UPDATE path and no DELETE path outside the erasure transaction.
  — *verified by:* repository test at layer 5 (`go test ./store/... -run AuditAppendOnly`)
  *(traces to: ADR-0003; SRS § 6 DR-3)*
- **QC-7:** The at-rest encryption key is never persisted to the database and never written to a log
  line. — *verified by:* layer-5 test asserting the key material is absent from every table and from
  captured log output *(traces to: SRS § 4.3 NFR-3; SDD § 4 CN-4)*
- **QC-8:** A signer token never appears in a log line, an error page body, or an outbound `Referer`
  header. — *verified by:* layer-5 test over captured log output and rendered error pages
  *(traces to: SRS § 4.3 NFR-4, NFR-5; SDD § 4 CN-5)*

## 3. Privacy, data retention & compliance

- **QC-9:** A signed envelope and its audit trail are deleted once the configured retention term has
  elapsed; the reference deployment ships that term at **7 years**.
  — *verified by:* layer-5 test over the retention job with a clock stub
  *(traces to: SRS § 6 DR-2)*
- **QC-10:** Erasure removes the document bytes, the signature images and the envelope's audit rows in
  one transaction, leaving only a tombstone. — *verified by:* layer-5 test asserting no row in any
  table still references the erased envelope *(traces to: FDR R-3; SDD § 4 CN-6)*

## 4. Performance & capacity

- **QC-11:** Flattening a 20-page envelope completes in under 2 s at p95 on the reference host.
  — *verified by:* review bar at development-design when a change touches `render/`. **No load
  harness exists** for this product and no layer-5 timing test is wired, so this is a class-2
  downgrade and is stated as one. *(traces to: SRS § 4.1 NFR-1)*
- **QC-12:** A render is bounded to 256 MB and 5 s; a breach fails that request and leaves the process
  running. — *verified by:* layer-5 test feeding an oversized document
  *(traces to: SDD § 4 CN-3)*

## 5. Availability & reliability

**Not applicable.** sealbox is deployed and operated by the customer on the customer's host, and the
vendor commits no uptime target (SRS § 7 C-2). The design fixes no runtime topology beyond the single
process (SDD Review Note RN-3), and the FDR excludes clustering and failover behaviour (OOS-2). There
is no service we operate, so there is no availability obligation to bind. Confirmed as a choice in
`architecture_open_issues.md` § 2.2.

## 6. Observability & monitoring

**Open — no obligation is stated here yet.** The SRS carries no observability requirement (§ 4 has
performance, security and scalability subsections and no observability one), so there is no upstream
fact to trace an entry to, and this run will not invent one. The gap is with the owner as open issue
1.1 in `architecture_open_issues.md`, and it is an **SRS** gap: § 4.5 is the section that should state
the floor.

## 7. Operational constraints

**Not applicable.** Nothing here exceeds the execution context the project card already carries — see
`project.md` for execution type, test command and parallelism.

## 8. Test strategy

The layer set is `<CORE>/doctrine/engineering/testing_doctrine.md`; this table is sealbox's
realization of it.

| Level | Scope | Tool | Where it lives |
|---|---|---|---|
| 1 | domain units | `go test` | `domain/*_test.go` |
| 2 | use cases over fake ports | `go test` | `app/*_test.go` |
| 5 | adapters against a real PostgreSQL | `go test` + testcontainers | `store/*_test.go`, `render/*_test.go` |
| 6 | structural checks — import direction, layer isolation | `go-arch-lint` | `arch.yml` |

- **Layers 3 and 4 are omitted:** there is one process and one external service (SMTP) behind a port,
  so a contract layer would test the fake and an integration layer would repeat layer 5.
- **Layers 6–7 are QA-role ATDD work.** QA is not active on sealbox; layer 6 is realized above as a
  structural check, and layer 7 is recorded as QA-owned with the Agari's end-to-end condition standing
  in for it until QA is active.

## 9. Verification map

| QC | Check | Command / layer | Gated at |
|---|---|---|---|
| QC-1 | domain has no outward dependency | `go-arch-lint check` (layer 6) | development-implementation |
| QC-2 | import direction | `go-arch-lint check` (layer 6) | development-implementation |
| QC-3 | layer isolation and I/O ownership | `go-arch-lint check` (layer 6) | development-implementation |
| QC-5 | audit append-only | `go test ./store/... -run AuditAppendOnly` | development-implementation |
| QC-6 | renderer swap stays byte-stable | `go test ./render/... -run Golden` | development-implementation |
| QC-7 | key absent from database and logs | `go test ./store/... -run KeyNotPersisted` | development-implementation |
| QC-8 | token absent from logs and referrers | `go test ./web/... -run TokenNotLeaked` | development-implementation |
| QC-9 | retention job deletes on term | `go test ./app/... -run Retention` | development-implementation |
| QC-10 | erasure leaves only a tombstone | `go test ./app/... -run Erasure` | development-implementation |
| QC-12 | render bounded at 256 MB / 5 s | `go test ./render/... -run Bounds` | development-implementation |

---

## NFDR Review Notes

- **RN-1:** QC-3 states I/O ownership per package, which the SDD's § 3 table implies but never spells
  out. Added because a delivery session reading only the SDD would put file I/O in `render/` and
  console I/O anywhere. *(re: QC-3; source: SDD § 3)*
- **RN-2:** QC-11 is a class-2 downgrade: NFR-1 is a p95 figure and this product has no load harness.
  Stated as a review bar with the missing harness named, rather than silently dropped.
  *(re: QC-11; source: SRS § 4.1 NFR-1)*
- **RN-3:** The FDR was read at **Status: Draft**. QC-6 and QC-10 trace to it anyway — it is the best
  statement of the product's behaviour that exists — and this note is where a later reader learns the
  source was still moving. *(re: QC-6, QC-10; source: docs/fdr.md, Draft)*
- **RN-4:** QC-9's 7-year figure is this run's draft, not an upstream fact: DR-2 fixes no default and
  the SRS cycle-1 trail asks the constraint set to propose one. It is with the owner as choice 2.1.
  *(re: QC-9; source: docs/trail/srs/cycle-1.md § 1.1)*
