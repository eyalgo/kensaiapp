# FDR — sealbox

**Status:** Draft
**Owner:** Principal PM
**Version:** 1 — first authoring off the settled SRS and SDD. Two items are still with the CPO (the
resend behaviour, and what an operator sees after erasure), so this document is not settled.

> The behavioural contract for sealbox: what the product does, observably, from outside.

---

## Description

sealbox turns a PDF and a list of signers into a flattened, signed envelope with an audit record,
running entirely on the buying firm's host.

---

## Rules

### Envelope lifecycle

- **R-1:** An envelope moves `draft → sent → completed` and never moves backwards. *(traces to: SRS
  § 3.1 FR-2, FR-4)*
- **R-2:** A completed envelope's PDF is byte-stable: downloading it twice yields the same file.
  *(traces to: SRS § 3.1 FR-4)*
- **R-3:** Erasing an envelope removes its document, its signature images and its audit trail, and
  leaves the envelope id resolvable as erased. *(traces to: SRS § 3.3 FR-6)*

### Signer link

- **R-4:** A signer link opens exactly once. A second open, or an open after 72 hours, shows the
  expiry page and no document content. *(traces to: SRS § 4.3 NFR-4)*
- **R-5:** A signer never sees another signer's name, address, or signature image before completion.
  *(traces to: SRS § 4.3 NFR-5)*

### Audit record

- **R-6:** The audit record attached to a completed PDF lists every actor, action and timestamp in the
  order they happened, and reading it needs no sealbox install. *(traces to: SRS § 3.2 FR-5)*

---

## Product decisions

- **PD-1:** The signed PDF is the artifact of record, not the database row. If sealbox is uninstalled,
  the firm still holds everything the signature is worth. *(traces to: agari.md, condition 2)*
- **PD-2:** **The PDF renderer is replaceable.** Which library flattens the document is not a product
  promise — a swap is invisible to a signer as long as R-2 holds. *(traces to: SDD § 3, the `Renderer`
  seam)*
- **PD-3:** **The mail path is replaceable.** An operator may point sealbox at any SMTP relay, and the
  product makes no promise about delivery beyond handing the message over. *(traces to: SRS § 5.3)*
- **PD-4:** A firm's own host is the only deployment. There is no vendor-hosted option to fall back
  to, and no telemetry leaves the box. *(traces to: SRS § 7 C-2)*

---

## Out of scope

- **OOS-1:** Bulk send and templates. *(traces to: SRS § 2)*
- **OOS-2:** Any clustering or failover behaviour. *(traces to: SDD § 12)*

---

## Examples

| Input / Scenario | Expected behaviour | Rule |
|---|---|---|
| A signer opens their link a second time | the expiry page, no document bytes | R-4 |
| An operator erases a completed envelope | the id resolves as erased; no document, image or audit row remains | R-3 |

---

## FDR Review Notes

- **RN-1:** R-2's byte-stability is stronger than anything the SRS states. It is what makes PD-2's
  renderer swap checkable from outside, and it is this document's addition. *(re: R-2)*
- **RN-2:** Two behaviours are still open with the CPO and are absent here rather than guessed: what
  a resend does to an already-issued link, and what an operator sees in place of an erased envelope.
  This is why the Status line reads Draft.
