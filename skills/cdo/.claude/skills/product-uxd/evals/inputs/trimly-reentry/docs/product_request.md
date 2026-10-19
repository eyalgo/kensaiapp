# Product Request — trimly (raw owner brief)

## What I want to build

**Trimly** — a **team link-shortener** with click analytics for small marketing teams. Turn a long
campaign URL into a branded short link, share it across channels, and see which channel drove the
clicks. A shared **workspace** so the whole marketing team works together, not a pile of personal links.

## What I know so far

- **Who it's for:** marketing teams at small companies — a marketing manager plus 3–15 people per
  workspace.
- **Analytics:** per link — total clicks, unique visitors, where the clicks came from, referrers, over
  time. Geography from the visitor's IP via a geo-IP provider; we shouldn't hang onto raw IPs for long.
- **Billing:** per-seat monthly through **Stripe**.
- **Redirects:** these need to be quick and the service dependable — teams put live campaign links on
  this. I haven't picked target numbers.
- **Scale at launch:** figure ~50 workspaces, up to a couple thousand links each, a couple hundred
  thousand redirects a day.
- **The pitch:** lighter than a marketing suite, but a real team tool — unlike the consumer shorteners
  that have no workspace or roles.

## Not yet figured out

- Exact latency / availability numbers to commit to.
- Whether a printed link should live forever, and what to do with links nobody clicks anymore.
