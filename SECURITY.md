# Security

## Reporting a security hole

Report it privately, through this repository's
[private vulnerability reporting](https://github.com/eyalgo/kensaiapp/security/advisories/new).
Do not open a public issue.

Say what is affected, how to reproduce it, and what it lets someone do. Each report is read. KensaiApp
is maintained privately, so there is no promised timeline for a fix.

## What is in scope

The code in this repository: its hooks, launchers, tools, skills and prompts, and the instructions
they give the agents they start.

Claude Code itself, and the models it runs, are Anthropic's. Report a hole in them to Anthropic.

## Before you report

KensaiApp runs agents on your own machine, with your own Claude Code settings and credentials. Never
put an API key, a token or a password in a file in the repository, an issue or a report.
