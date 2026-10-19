# SRS — Trimly

**Status:** Draft
**Owner:** CTO
**Version:** 1 — first authoring; latency and availability drafted best-effort and surfaced as choices to confirm, the link-lifetime contradiction surfaced as an open issue for the owner.

> The SRS is the technical source of truth: the system-level **what**, derived from the PRD. Updated in
> place with versioning. Stable by default — every delta traces to an owner answer/directive or an
> upstream PRD change. Every requirement traces to a PRD feature or goal.

---

## 1. Purpose

Trimly is a multi-tenant web service that turns long campaign URLs into branded short links, serves the
redirects, and reports per-link click analytics to small marketing teams working in shared workspaces.

## 2. Scope

Covers link management, redirect serving, click-analytics capture and reporting, and workspace / member /
billing administration for the web application (PRD §6 In). Excludes any public API, native mobile app,
per-workspace custom domains, and A/B splitting (PRD §6 Out).

## 3. Functional Requirements

### 3.1 Link management
- **FR-1:** A member can create a short link from a destination URL on the shared branded domain, with an
  optional custom slug. *(traces to: PRD F1)*
- **FR-2:** A slug is unique within the branded domain; a create with a taken slug is rejected. *(traces to: PRD F1)*
- **FR-3:** A member can edit a link's destination and delete a link. *(traces to: PRD F1)*
- **FR-4:** Requesting a live short link issues an HTTP redirect to its current destination. *(traces to: PRD F1, G1)*

### 3.2 Analytics
- **FR-5:** Each redirect records a click event with timestamp, coarse geography, and referrer. *(traces to: PRD F2, G2)*
- **FR-6:** Per link, the system reports total clicks, unique visitors, geographic breakdown, top
  referrers, and a clicks-over-time series. *(traces to: PRD F2, G2)*

### 3.3 Workspace, members, billing
- **FR-7:** An admin creates a workspace, invites members, and assigns the admin or member role. *(traces to: PRD F3)*
- **FR-8:** Links belong to the workspace, not the creating member. *(traces to: PRD F3)*
- **FR-9:** An admin manages a per-seat monthly subscription and payment method via Stripe. *(traces to: PRD F4)*

## 4. Non-Functional Requirements

### 4.1 Performance
- **NFR-1:** p95 redirect latency < 100 ms at the edge, under launch-scale load. *(drafted best-effort;
  the PRD (G4) asks only that redirects "feel instant" and sets no number — pending owner confirm, see
  open-issues 2.1)*

### 4.2 Availability & Reliability
- **NFR-2:** 99.9% monthly availability of the redirect path. *(drafted best-effort; the PRD (G4) asks
  only that the service be "dependable" and sets no number — pending owner confirm, see open-issues 2.2)*

### 4.3 Security & Privacy
- **NFR-3:** All traffic (redirects, dashboard, admin) is served over TLS 1.2+. *(traces to: PRD §5)*
- **NFR-4:** A visitor's raw IP address is retained no longer than 30 days, then discarded; only coarse
  geography derived from it is kept for the life of the link. *(traces to: PRD §5)*

### 4.4 Scalability
- **NFR-5:** The system serves the launch cohort — 50 workspaces, up to 2,000 active links each, ~200,000
  redirects/day (≈ 2.3 sustained redirects/second, with headroom for campaign spikes) — without
  architectural change. *(traces to: PRD G3)*

### 4.5 Observability
- **NFR-6:** Every redirect and every dashboard query emits a structured log line and latency metric,
  alertable on error rate and latency. *(traces to: PRD G2, G4)*

### 4.6 Maintainability
- **NFR-7:** The redirect path and the analytics-reporting path are separately deployable so one can scale
  without the other. *(traces to: PRD G3)*

## 5. Interfaces

### 5.1 User Interface
- A web dashboard for link management, per-link analytics, and workspace/member/billing administration. *(traces to: PRD F1, F2, F3, F4)*

### 5.2 API
- No public API in v1. *(traces to: PRD §6 Out)*

### 5.3 External Services
- **Stripe** — subscription billing and payment methods. *(traces to: PRD F4, §8)*
- **A geo-IP lookup provider** — coarse geography for click analytics. *(traces to: PRD §5, §8)*
- **A CDN** — fronts the redirect path. *(traces to: PRD §8)*

## 6. Data Requirements

- **DR-1:** Link — slug, destination URL, owning workspace, creator, created-at. *(traces to: PRD F1, §5)*
- **DR-2:** Click event — link, timestamp, coarse geography, referrer. *(traces to: PRD F2, §5)*
- **DR-3:** Workspace — name, plan, seat count. *(traces to: PRD F3, F4)*
- **DR-4:** Member — identity, owning workspace, role (admin | member). *(traces to: PRD F3)*

## 7. Constraints

- **C-1:** All links live on a single shared branded domain (no per-workspace custom domains in v1). *(traces to: PRD §6 Out)*
- **C-2:** Card data is held by Stripe, never by Trimly. *(traces to: PRD §5)*

## 8. Acceptance Criteria

- **AC-1:** Creating a link with a free slug succeeds and the link redirects to its destination; a taken
  slug is rejected. *(covers: FR-1, FR-2, FR-4)*
- **AC-2:** After N redirects from known geographies, the link's dashboard shows N clicks with the correct
  geographic breakdown and referrers. *(covers: FR-5, FR-6)*
- **AC-3:** An admin can invite a member, assign a role, and change the subscription seat count. *(covers: FR-7, FR-9)*

---

## SRS Review Notes

- **RN-1:** NFR-5 states the launch-scale bar as a derived figure — ~2.3 redirects/second is computed from
  the PRD's stated 200,000 redirects/day (G3) — *because* the PRD gives the volume but not the rate;
  the derivation is written down rather than invented. *(re: NFR-5; PRD source: G3)*
- **RN-2:** NFR-1 (p95 redirect < 100 ms) and NFR-2 (99.9% monthly availability) are best-effort drafts,
  not derivable from any PRD number — *because* the PRD (G4) sets the bars only qualitatively ("feels
  instant", "dependable"). Both are owner-taste calls, so they are surfaced as *choices to confirm*
  (open-issues 2.1, 2.2) rather than asserted as settled. *(re: NFR-1, NFR-2; PRD source: G4)*

---

## Open Questions
- [OPEN: link lifetime — PRD F5 says links "never expire", but PRD §5 says inactive links are auto-purged after 12 months. These contradict; the resolution is a product-intent call, surfaced in open-issues 1.1.]
