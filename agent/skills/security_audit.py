"""Security audit skill — vulnerability review and audit guidance."""

from ._base import Skill

SECURITY_AUDIT = Skill(
    name="security_audit",
    tools=("Read", "Bash", "Glob", "Grep"),
    prompt_section="""\
## Security audit
Check for OWASP Top 10 and common issues:
- **Injection**: SQL/command injection via unsanitized user input; use parameterized queries
- **Auth**: broken auth, insecure session tokens, missing expiry, privilege escalation
- **XSS**: unescaped output in templates; missing Content-Security-Policy
- **IDOR**: direct object references without authorization checks
- **Secrets**: hardcoded credentials, API keys, tokens in source or logs
- **Dependency vulns**: `pip-audit`, `npm audit`, `trivy fs .` for known CVEs
- **Crypto**: weak algorithms (MD5, SHA1, DES), hardcoded IVs, improper cert validation
- **SSRF**: user-controlled URLs fetched server-side without allowlist
- Report each finding: file:line, severity (critical/high/medium/low), description, remediation
- Never commit exploit payloads or working PoCs to the repo
""",
)
