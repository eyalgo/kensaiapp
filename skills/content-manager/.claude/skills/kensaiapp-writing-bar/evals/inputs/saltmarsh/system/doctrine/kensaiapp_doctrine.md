# saltmarsh — domain doctrine

The rules that hold for the three services, whoever is on the rota.

## Change

- A change to a service in the working day is announced in the rota channel before it starts.
- No change ships without a rollback the on-call engineer can run alone.
- The change record names the person who made the change and the ticket that asked for it.

## On-call

- The pager is held by exactly one person at a time, and the handover is explicit — an unacknowledged
  handover is not a handover.
- An incident that crossed a shift boundary gets a written summary before the next handover.

## The services

- The parts catalogue is read-only outside business hours; a write attempt is an incident.
- The dispatch queue keeps ninety days of history. Anything older is exported before it is dropped.
