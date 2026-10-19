# PRD — mailmate

**Status:** Settled
**Owner:** CPO
**Version:** 2 — folded the two owner answers (segment; retention) from cycle-1; nothing left unresolved — the loop is closed and the companion cleared.

> Product source of truth for mailmate — the shared team inbox. Read cold.

---

## Purpose

Small support teams share one `support@` mailbox and step on each other: two people answer the
same customer, triage is manual, threads get dropped. mailmate is a shared inbox that auto-sorts
incoming email into queues and lets a teammate claim a thread so each customer gets one owner.

## Problem Statement

A small team on a shared Gmail inbox can't see who is handling what. Two people reply to the same
thread; other threads sit untouched. Sorting billing vs bug vs how-to is done by hand, every time.

## Why This

The alternative today is a raw shared Gmail inbox. mailmate adds claim-to-own (no double replies)
and automatic triage into queues — neither of which a plain shared mailbox has.

## Target Users

Small **SMB support teams** on a shared `support@` mailbox — **2–10 seats**. Freelancers running
their own support are out of scope for v1.

## Core Features

- Auto-sort incoming email into queues (billing, bugs, how-to).
- Claim a thread so one teammate owns it; reassign to another.

## Billing

- Per-seat, monthly. Payments via **Stripe**.

## Data & Retention

- Store the **full thread content** of customer email. **Purge a thread 90 days after it is closed.**

## UX Notes

- The whole point is seeing **who owns what** at a glance: someone scanning a queue must tell a
  claimed thread from an unclaimed one without opening it.
- Claiming should be one action from the queue list. If a teammate has to open a thread to claim it,
  two people have already opened it.
- The case to get right is two people on the same unclaimed thread at once — the second one needs to
  find out it was just claimed without losing what they had already typed.
- A brand-new workspace has no mail yet and nothing for triage to sort. The first-run state should
  say what happens next rather than show three empty queues.
- Triage is automatic and will sometimes be wrong. Moving a thread to the right queue should feel
  ordinary, not like correcting the machine.

## Scope (In)

- Shared inbox, auto-triage into queues, claim / reassign, per-seat billing.

## Out of Scope

- Enterprise uptime-SLA commitments (the numbers would come from the infra vendor's account rep;
  not committed for v1).
