# PRD — Lumen

**Status:** Settled
**Owner:** CPO
**Version:** 1 — first authoring settled everything from the product request.

> Lumen is a small team status-page product: one public page per team showing current incidents
> and a 90-day uptime history.

---

## 1. Problem

Small SaaS teams need a public status page but don't want to run one. Lumen hosts it: a public
page, an internal incident editor, done.

## 2. Target users

- **Publishers:** on-call engineers opening and updating incidents, often from a phone, under stress.
- **Readers:** the team's customers checking whether the problem is theirs.

## 3. Goals

- **G1 — Fast to update.** Opening an incident takes under a minute from a phone.
- **G2 — Instantly legible.** A reader understands current status in one glance.

## 4. Features

- **F1 — Public status page.** Current status banner, active incidents with updates, 90-day
  uptime bars per component.
- **F2 — Incident editor.** Open, update, resolve; each update timestamps and posts to the
  public page.
- **F3 — Components.** A team defines the components (API, dashboard, webhooks) readers see.

## 5. Scope

v1: one public page + the editor. No subscriptions/notifications, no custom domains, no SLA math
beyond the uptime bars.
