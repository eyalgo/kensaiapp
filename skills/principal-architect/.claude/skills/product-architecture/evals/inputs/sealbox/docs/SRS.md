# SRS — sealbox

**Status:** Settled
**Owner:** CTO
**Version:** 2 — folded the owner's cycle-1 answers (the render budget, and leaving the retention term
unfixed); nothing left unresolved — the loop is closed and the companion cleared.

> Technical source of truth for sealbox — the self-hosted document-signing service. Read cold.

---

## 1. Purpose

A small firm sends a PDF for signature and gets back a flattened, tamper-evident envelope, without
handing the client document to a third-party SaaS. sealbox runs on the firm's own host.

## 2. Scope

**In:** envelope creation from an uploaded PDF, one single-use link per signer, in-browser signing,
flattened signed-envelope download, an audit trail per envelope.

**Out:** bulk send, document templates, payment collection, native mobile apps, multi-tenant hosting.

## 3. Functional Requirements

### 3.1 Envelopes

- **FR-1:** An operator uploads a PDF and names one or more signers; the envelope is created in `draft`.
- **FR-2:** Sending an envelope issues one single-use link per signer and moves it to `sent`.
- **FR-3:** A signer opens their link, reads the document, and applies a drawn or typed signature.
- **FR-4:** When the last signer signs, the system renders a flattened signed PDF and moves the
  envelope to `completed`.

### 3.2 Audit

- **FR-5:** Every envelope exposes its audit trail — who did what, when, from which address — as a
  record attached to the completed PDF.

### 3.3 Erasure

- **FR-6:** An operator erases one envelope from the console: document bytes, signature images and
  audit trail go together, and the envelope id is left as a tombstone.

## 4. Non-Functional Requirements

### 4.1 Performance

- **NFR-1:** Rendering the flattened signed PDF for a 20-page document completes in under **2 s at
  p95** on the reference host (4 vCPU, 8 GB).
- **NFR-2:** A signer page — first page of the document visible — loads in under **1.5 s at p95** over
  a 10 Mbit link.

### 4.3 Security & Privacy

- **NFR-3:** Envelope PDFs and signature images are encrypted at rest under a key that is not stored
  in the database.
- **NFR-4:** A signer link is single-use, bound to one signer, and expires **72 hours** after issue. A
  replayed or expired link yields no document content.
- **NFR-5:** There is no signer authentication beyond possession of the link, so link secrecy is the
  entire boundary: the token never appears in a log line, an error page, or an outbound referrer.

### 4.4 Scalability

- **NFR-6:** One host serves **500 envelopes/day** and **50 concurrent signer sessions** with no
  horizontal scaling.

## 5. Interfaces

### 5.1 User Interface

An operator console and a signer page, both server-rendered. No client build step.

### 5.3 External Services

An operator-supplied SMTP relay for signer invitations. sealbox makes no other outbound call.

## 6. Data Requirements

- **DR-1:** Envelope PDFs, signature images, signer names and email addresses, and the audit trail are
  persisted.
- **DR-2:** Signed envelopes and their audit trails are retained for a **configurable** term and then
  deleted. This document fixes no default term.
- **DR-3:** An audit event, once written, is never altered — the trail is the evidence, and evidence
  that can be edited is not evidence.

## 7. Constraints

- **C-1:** One deployable artifact — a single binary plus PostgreSQL. No broker, no object store, no
  external cache.
- **C-2:** sealbox is deployed and operated **by the customer, on the customer's host**. The vendor
  runs no hosted instance and commits no uptime target.
- **C-3:** Go 1.22 and PostgreSQL 15 are fixed by the buying firms' platform teams.

## 8. Acceptance Criteria

- A 20-page envelope with two signers completes and downloads on the reference host inside NFR-1.
- An expired or reused signer link returns no document bytes.
- An erased envelope leaves no document, signature image or audit row behind.

---

## SRS Review Notes

- **RN-1:** NFR-1's 2 s budget is the owner's cycle-1 answer, not a derived figure — they set it
  against what a signer will sit through. *(re: NFR-1; source: docs/trail/srs/cycle-1.md)*
- **RN-2:** DR-2 fixes no default retention term deliberately. The owner ruled in cycle-1 that the
  term is a deployment setting and that this document should not pick a number.
  *(re: DR-2; source: docs/trail/srs/cycle-1.md)*
- **RN-3:** NFR-6's figures are the CPO's launch-scale estimate carried over from the PRD, not a
  measurement. *(re: NFR-6)*
