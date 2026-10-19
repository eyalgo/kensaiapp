# SDD — sealbox

**Status:** Settled
**Owner:** CTO
**Version:** 3 — the three-seat conversation closed; the shape, the parts and the cut are settled.

> Architecture and cut for sealbox, written off the settled SRS. Read cold.

---

# Part A — What is being cut

## 1. What this design must achieve

One binary a firm's platform team installs beside their PostgreSQL (SRS C-1, C-3), holding client
documents the vendor never sees (C-2), rendering a flattened envelope inside NFR-1's 2 s budget, and
leaving an audit trail that cannot be edited after the fact (DR-3).

## 2. The shape, and what it was chosen over

**The runtime shape.**

| Shape | Right when | Wrong when | Taken? |
|---|---|---|---|
| Modular monolith — one process, packages with an enforced import direction | the deploy target is one customer host and the operator is not a platform team | one component's load must scale independently of the rest | **Taken** |
| Service split — api, renderer and signer web as three processes | one component is the bottleneck and scales on its own | there is one host and no orchestrator on it (C-1) | No |
| Serverless functions behind a managed queue | traffic is spiky and the vendor operates the runtime | the customer operates it on their own hardware (C-2) | No |

**Where the document bytes live.**

| Option | Right when | Wrong when | Taken? |
|---|---|---|---|
| PDF bytes in PostgreSQL, encrypted, as large objects | one binary and one database is the entire deployment (C-1) | documents are large or numerous enough to dominate the database | **Taken** |
| An object store — S3 or MinIO beside the binary | volumes are high and lifecycle rules do the retention work | C-1 forbids a second service on the host | No |
| The local filesystem beside the binary | the operator already backs up that volume | the backup story splits in two — a database dump would stop being a complete backup | No |

## 3. The parts, and the seams between them

| Package | Holds | May import |
|---|---|---|
| `domain/` | envelope, signer, audit event, the state machine | nothing outside `domain/` |
| `app/` | the use cases, and the port interfaces below | `domain/` |
| `store/` | the PostgreSQL adapter and at-rest encryption | `domain/`, `app/` |
| `render/` | PDF flattening and signature stamping, **in the request process** | `domain/` |
| `web/` | operator console and signer page handlers, server-rendered | `app/` |
| `cmd/` | the binary entrypoint and config load | all of the above |

**The seams** — port interfaces declared in `app/`, implemented outward: `EnvelopeStore` (persistence),
`Renderer` (flattening), `Mailer` (SMTP), `Clock` (time).

## 4. What every slice inherits

- **CN-1:** Every audit write is an INSERT into `audit_events`. The table has no UPDATE and no DELETE
  path outside erasure, and an envelope's state is derived by folding its events. *(realizes DR-3)*
- **CN-2:** Every timestamp comes from the `Clock` port. No package calls the wall clock directly.
- **CN-3:** The renderer runs inside the request process, bounded to 256 MB and 5 s. A breach fails
  that one request and leaves the process up.
- **CN-4:** The at-rest key is read once at boot from a path in the config file and is never written to
  the database or to a log. *(realizes NFR-3)*
- **CN-5:** A signer token is 32 random bytes, stored only as a hash, and stripped from log lines,
  error pages and outbound referrers. *(realizes NFR-4, NFR-5)*
- **CN-6:** Erasure deletes the document bytes, the signature images and the envelope's audit rows in
  one transaction, leaving a tombstone row carrying the envelope id and the erasure event.
  *(realizes FR-6)*

---

# Part C — The cut

## 6. The slices

- **S-1** — envelope create and store, encrypted, with the audit fold. Reached when a draft envelope
  survives a process restart.
- **S-2** — send, signer link, signer page. Reached when a signer opens a link and sees page one.
- **S-3** — signing and flattening. Reached when a two-signer envelope downloads flattened.
- **S-4** — erasure and the retention job. Reached when an erased envelope leaves nothing behind.

## 7. The order, and why

S-1 first because every later slice writes through its store seam. S-4 last because it is the only
slice that can destroy what the others produce, and it is the one the Agari's third condition names.

---

# Part D — What the cut costs, and what it cannot reach

## 9. Trade-offs taken

- **TO-1:** PDF bytes in PostgreSQL. Buys a single-file backup and C-1 compliance; costs database
  size, and a practical ceiling around 50 MB per document. Undoing it means a second `EnvelopeStore`
  adapter and a migration of every stored envelope.
- **TO-2:** Server-rendered pages, no SPA. Buys no client build toolchain and a smaller attack surface
  on the page a stranger with a link can reach; costs a full page load at each step of signing.
- **TO-3:** Envelope state folded from audit events rather than stored as a column. Buys a trail that
  cannot silently disagree with the state it explains; costs a fold on every state read, and a
  snapshot table if an envelope ever accumulates many events.

## 12. What this design is not

Not multi-tenant, not horizontally scalable, and not an operations product: there is no clustering,
no leader election, and no shared session store.

---

## SDD Review Notes

- **RN-1:** § 2's storage row was decided against C-1 rather than against a volume estimate — no
  volume figure exists for documents, only NFR-6's envelope rate. *(re: § 2)*
- **RN-2:** The `Mailer` seam exists because SMTP is operator-supplied (SRS § 5.3) and cannot be
  exercised in CI. The port is what makes the send path testable at all. *(re: § 3)*
- **RN-3:** The design fixes no runtime topology beyond the single process. C-2 puts deployment and
  uptime with the customer, so there is nothing here to design. *(re: § 4)*
- **RN-4:** NFR-2's 1.5 s signer-page budget is met by streaming the document after page one. The CDO
  accepted showing page one before the rest has arrived. *(re: § 3, `web/`)*
