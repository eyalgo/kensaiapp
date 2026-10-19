# 上がり Agari — Trimly's "done"

*The project-level declaration: the terminus that defines when the product is done, set by the CPO.
A declaration, not a queue.*

---

**Trimly is done when the launch cohort is live on it — 50 workspaces running their real campaign
links on the shared branded domain, with analytics they act on and subscriptions that renew.**

Three conditions, together the dock:

- **Links work and keep working.** A team creates a branded short link in a few clicks, optionally
  with a custom slug, and every link created keeps resolving indefinitely. Permanence is a promise
  printed on physical material — it is part of done, not a later hardening.
- **The analytics are trusted.** Per link, the team sees total clicks, unique visitors, geography,
  referrers, and a time series, updating as clicks arrive — trusted enough that a team reads them to
  decide where a campaign goes next.
- **Workspaces are paying.** Admins manage members, roles, and a per-seat monthly subscription
  through Stripe, and at least one renewal has run without intervention.

What this terminus deliberately leaves out — tracked or awaited, not conditions of done:

- **The success-metric bars** — time-to-create and first-week activation. They measure how well a
  shipped product performs; they do not decide whether it shipped.
- **Growth past the launch cohort.** Done is the cohort live, not the market.
- **Anything the PRD already places out of scope for v1** — the public/developer API, a native
  mobile app, per-workspace custom domains, and A/B link splitting.
