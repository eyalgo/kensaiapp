# PRD — Trimly

**Status:** Settled
**Owner:** CPO
**Version:** 2 — folded the launch-scale and retention answers from cycle-1; nothing left unresolved — the loop is closed and the companion cleared.

> Trimly is a team link-shortener with click analytics for small marketing teams. This PRD is the
> product source of truth: the what and the why. The technical *what* (the SRS) derives from it.

---

## 1. Problem

Small marketing teams share campaign links across many channels — email, social, ads, printed QR codes.
They need branded short links and per-link click analytics, but the incumbent tools are either
consumer-grade (no team workspace, no roles) or heavyweight marketing suites that are overkill and
expensive. Teams end up with a spreadsheet of raw URLs and no idea which channel drove clicks.

## 2. Target users

- **Buyer:** a marketing manager at a company of 10–200 people.
- **Users:** the marketing team members in a shared workspace — typically 3–15 people per workspace.
- Two roles inside a workspace: **admin** (manages members and billing) and **member** (creates and
  views links).

## 3. Goals

- **G1 — Fast link creation.** A team member turns a long campaign URL into a branded short link in a
  few clicks, optionally choosing a custom slug.
- **G2 — Per-link analytics.** For every short link, the team sees total clicks, unique visitors, a
  geographic breakdown, referrers, and a clicks-over-time series.
- **G3 — Works at launch scale.** The product must comfortably serve the launch cohort: **50 workspaces**,
  each holding up to **2,000 active links**, driving an aggregate of about **200,000 redirects per day**.
- **G4 — Feels instant and dependable.** Redirects should feel instant to the end visitor, and the
  service should be dependable enough that teams trust their live campaign links to it.

## 4. Features

- **F1 — Link management.** Create, edit, and delete short links on a shared branded domain, each with an
  optional custom slug. A slug is unique within the branded domain.
- **F2 — Analytics dashboard.** Per link: total clicks, unique visitors, geographic breakdown, top
  referrers, and a time series. Analytics update as clicks arrive.
- **F3 — Workspace & members.** An admin creates a workspace, invites members, and assigns the admin or
  member role. Links belong to the workspace, not the individual.
- **F4 — Billing.** Each workspace is billed on a per-seat monthly plan through **Stripe**. Admins manage
  the subscription and payment method.
- **F5 — Permanent links.** A short link, once created, **never expires** — the redirect keeps resolving
  for as long as the workspace exists, so a link printed on physical material stays valid indefinitely.

## 5. Data & privacy

- Trimly stores **link records** (slug, destination URL, owning workspace, creator, created-at),
  **click events**, **workspace** records, and **member** records.
- Each click event stores a coarse **geography** derived from the visitor's IP via a third-party geo-IP
  provider. The raw IP address is retained no longer than **30 days**, then discarded; the coarse geo is
  kept for the life of the link.
- **Inactive links** — a link that has received no clicks for **12 months** — are **automatically purged**
  along with their click history, to keep the store lean.
- Billing data (card details) is held by Stripe, not by Trimly.

## 6. Scope

- **In:** the web application (link management, analytics dashboard, workspace/member/billing admin).
- **Out (v1):** no public/developer API, no native mobile app, no custom per-workspace domains (all links
  live on the one shared branded domain), no A/B link splitting.

## 7. Success metrics

- **Median time-to-create a link < 30 seconds** from paste to short link.
- **≥ 60% of new workspaces create at least 5 links in their first week.**

## 8. UX Notes

- Paste-to-short-link is the whole first impression: from pasting a long campaign URL to holding a
  copyable short link should take one screen and a few clicks, with the custom slug optional and out
  of the way of the people who don't want one.
- A slug collision is the common failure, and being told about it only after submitting is too late —
  the person is mid-flow with a campaign to ship.
- What a team acts on is the comparison across links; the per-link detail view is where they land
  *after* something stands out, not where they start.
- Clicks arrive continuously. A link created a minute ago has no clicks yet, and that is not an
  error — a fresh link's analytics must read as "nothing yet", never as "something broke".
- The geographic breakdown depends on a third-party lookup. When that lookup is unavailable, the
  rest of the analytics must stay readable rather than the whole view failing with it.
- Links get printed on physical material. Anything that reads as destructive — deleting a link,
  changing a live slug — must be hard to do by accident.

## 9. External dependencies

- **Stripe** — subscription billing and payment methods.
- **A geo-IP lookup provider** — coarse geography for click analytics.
- **A CDN** — fronts the redirect path so links resolve close to the visitor.
