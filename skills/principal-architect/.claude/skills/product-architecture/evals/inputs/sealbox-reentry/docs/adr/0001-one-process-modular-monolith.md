# ADR-0001: Ship sealbox as one process with enforced package boundaries

**Status:** Accepted
**Date:** 2026-08-24

## Context

sealbox is installed by the buying firm's platform team on a single host beside their PostgreSQL
(SRS C-1, C-3), and the firm operates it themselves (C-2). There is no orchestrator on that host and
nobody on it from us, so every process the design adds is a process the customer has to supervise.

## Decision

sealbox is a single binary. Its internal structure is a set of packages with an enforced import
direction — `domain/` imports nothing, `app/` holds the ports, and `store/`, `render/`, `web/` and
`cmd/` sit outside them.

## Alternatives ruled out

- **A service split — api, renderer and signer web as three processes** — lost because rendering does
  not need to scale separately at NFR-6's volumes, and three processes need a supervisor the customer
  host does not have.
- **Serverless functions behind a managed queue** — lost on C-2: the customer operates the runtime, so
  a cloud-managed one is not available to be operated.

## Consequences

Deployment is a file copy and a migration. Render load and request load share a CPU budget, so a heavy
render is felt by concurrent signers. Undoing this means extracting a package across a network
boundary and giving the customer a second thing to run.

## Traces to

SDD § 2, the runtime-shape table (Taken row); SRS § 7 C-1, C-2, C-3.

## Binds

QC-1, QC-2, QC-3
