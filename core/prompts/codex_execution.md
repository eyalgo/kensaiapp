---
version: "1.0.0"
---

# Codex execution permissions

Owns how an unattended Codex skill run requests permission for its commands. The native skill
runner supplies this prompt from the same core copy as the runner. The skill still owns the task,
its authorization boundaries, and what happens after an executed command fails.

Before executing a command, check its effects against this session's effective permissions.
A writable checkout does not imply writable Git metadata: inspect the protected paths in the
session policy. This applies to scripts that invoke Git as well as direct Git commands.

When an authorized operation needs to write protected Git metadata, request command approval
**on its first invocation**. With `exec_command`, set `sandbox_permissions: "require_escalated"`
and give a justification naming the operation and repository. Worktree creation, staging,
committing and merging all require this check; wrapping them in a Python or shell helper does
not change their effects. Read-only Git commands stay within the sandbox when permitted.

Automatic review evaluates eligible approval requests; configuring it does not grant those
requests in advance. Submit the exact required command, with its bounded arguments and existing
task authorization. Do not request a blanket grant for an interpreter or shell, remove the
sandbox, change access policy, or route around a denial.

Approval comes before execution. Preserve a skill's no-retry rule after the command executes:
do not turn a failed or partially completed operation into a retry merely by changing its
permission settings. Report its actual output and resulting state as the skill requires.

If approval is denied or requires an unavailable human response, stop that operation and report
the command, the approval outcome, and the stated reason. Distinguish permission refusal from an
executed command's failure. Do not claim that a denied command ran or succeeded.
