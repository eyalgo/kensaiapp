"""auditrun — round-resolution logic for the audit launcher (`launch-audit.sh`).

One responsibility, one module: pick which `evidence/v*/` round `launch-audit.sh` audits —
the newest un-audited round by default, or an explicit version override — and the prior round
strictly below it, for the audit's cross-version comparison passes. No launching, no `claude`,
no chaining; it reads only the evidence directory listing (`rounds.py`).
"""

__version__ = "1.0.0"
