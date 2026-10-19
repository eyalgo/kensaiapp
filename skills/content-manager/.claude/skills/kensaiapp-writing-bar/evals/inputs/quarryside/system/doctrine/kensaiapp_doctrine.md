# northbay — domain doctrine

The rules that hold for release work here, whatever the tooling looks like.

## Releases

- A release is cut from a clean tree. An uncommitted change in the working directory stops the cut.
- The release record names the commit it was built from. Never "latest", never a branch name.
- A release that cannot be rolled back in one step is not ready to go out.

## Scheduled work

- Every scheduled job has a hand-run equivalent, and the equivalent is what the checklist names.
- A job that has not run successfully in thirty days is switched off rather than left failing.

## The service

- The scheduling service holds no customer data. Sample datasets may be copied freely between
  environments.
- Downtime inside the working day is announced in the team channel before it starts, never after.
