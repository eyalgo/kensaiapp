# 上がり Agari — mailmate's "done"

*The project-level declaration: the terminus that defines when the product is done, set by the CPO.
A declaration, not a queue.*

---

**mailmate is done when a paying SMB support team runs its whole support day inside it — one
customer, one owner, no double replies — for a full billing cycle.**

Three conditions, together the dock:

- **The shared inbox does its job.** Incoming email auto-sorts into the queues, a teammate can claim
  a thread to own it, and reassignment works. A claimed thread is visibly owned to everyone on the
  team — that visibility is the product, not a nicety.
- **The team is a paying customer.** Per-seat monthly billing charges through Stripe and renews once
  without manual intervention. A product that cannot take money is not shipped.
- **Retention is honoured in production.** Thread content is stored and closed threads purge at 90
  days, running on real data rather than as an implemented-but-unexercised path.

What this terminus deliberately leaves out — tracked or awaited, not conditions of done:

- **The adoption and retention numbers.** They measure how well a shipped product performs; they do
  not decide whether it shipped.
- **Seat-count growth beyond the first team.** The product is proven by one team using it fully, not
  by many teams using it partly.
- **Anything the PRD already places out of scope**, including enterprise uptime-SLA commitments and
  the freelancer segment.
