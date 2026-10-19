# PRD — mailmate

**Status:** Draft
**Owner:** CPO
**Version:** 1 — initial draft from the raw brief; two product questions still open

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

- [OPEN — see companion 1.1] Small support teams on a shared `support@` mailbox; exact segment
  not yet pinned.

## Core Features

- Auto-sort incoming email into queues (billing, bugs, how-to).
- Claim a thread so one teammate owns it; reassign to another.

## Scope (In)

- Shared inbox, auto-triage into queues, claim / reassign.

## Out of Scope

- [OPEN — see companion 1.2] Retention of customers' email content — not yet decided.

## Open Questions

- [OPEN: which segment exactly — freelancers vs SMB support teams? → companion 1.1]
- [OPEN: what do we store of customers' email content, and for how long? → companion 1.2]
