# 上がり Agari — sealbox's "done"

*The project-level declaration: the terminus that defines when the product is done, set by the CPO.
A declaration, not a queue.*

---

**sealbox is done when one law firm runs a real client signature end to end on its own host — upload,
send, sign, download the flattened envelope with its audit record — with nobody from us on the box.**

Three conditions, together the dock:

- **The envelope completes on the customer's hardware.** The firm's own operator installs the binary,
  points it at their PostgreSQL, and sends a real engagement letter. A signature that only works on
  our laptop is not the product.
- **The signed artifact stands on its own.** The downloaded PDF carries the flattened signatures and
  the audit record, and stays readable with sealbox uninstalled. A signed document that needs our
  software to be read is not a signed document.
- **The operator can delete on request.** A client asks for their envelope to be erased, and the
  operator erases it — document, signature images, and audit trail — without a database console.

What this terminus deliberately leaves out — tracked or awaited, not conditions of done:

- **How many firms install it.** Adoption measures a shipped product; it does not decide whether it
  shipped.
- **Anything the SRS already places out of scope**, including bulk send, templates, and multi-tenant
  hosting.
- **An uptime commitment.** The customer operates the host, so uptime is theirs to hold and ours to
  stay out of.
