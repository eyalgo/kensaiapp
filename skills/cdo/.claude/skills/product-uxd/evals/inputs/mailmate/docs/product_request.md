# Product Request — mailmate (raw owner brief)

## What I want to build

**mailmate** — a **shared team inbox** for small support teams. Incoming customer email lands
in one place and auto-sorts into queues (billing, bugs, how-to). A teammate **claims** a thread
so two people don't reply to the same customer, and can **reassign** a thread to whoever should
own it.

## What I know so far

- **Who it's for:** small teams drowning in a shared `support@` mailbox. (Freelancers running
  their own support? Small SaaS support teams? Both? — I haven't pinned this down.)
- **Billing:** charge **per seat, monthly**. Use **Stripe** for payments.
- **Enterprise:** bigger customers will ask for an **uptime SLA**. The exact numbers we'd commit
  to aren't published anywhere — I'll have to get them from our infra vendor's account rep.
- **The pitch:** better than a raw shared Gmail inbox — nobody double-replies, and triage is
  automatic instead of by hand.

## Not yet figured out

- How we'd know it's working (what to measure).
- What we store of customers' email content, and for how long.
