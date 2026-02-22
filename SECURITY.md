# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.14.x  | :white_check_mark: |
| < 0.14  | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Orga, please report it responsibly.

**Do NOT open a public issue for security vulnerabilities.**

Instead, please email **tonic6101@gmail.com** with:

- A description of the vulnerability
- Steps to reproduce the issue
- The potential impact
- Any suggested fix (optional)

### What to Expect

- **Acknowledgement:** Within 48 hours of your report
- **Status update:** Within 7 days with an initial assessment
- **Resolution:** We aim to release a fix within 30 days for confirmed vulnerabilities

### Scope

The following are in scope:

- SQL injection, XSS, CSRF bypasses
- Authentication or authorization flaws
- Remote code execution
- Data exposure or leakage
- Server-Side Request Forgery (SSRF)

The following are out of scope:

- Vulnerabilities in the Frappe Framework itself (report to [Frappe Security](https://github.com/frappe/frappe/security))
- Social engineering attacks
- Denial of service attacks
- Issues requiring physical access

### Recognition

We appreciate responsible disclosure. With your permission, we will acknowledge security researchers in our release notes.

## Security Features

Orga includes several built-in security measures:

- **Parameterized SQL queries** throughout the codebase
- **SSRF protection** on webhook URLs (blocks private IPs, cloud metadata endpoints)
- **HTML sanitization** with whitelist approach for user-generated content
- **Role-based access control** with Frappe's permission system
- **CSRF protection** via Frappe's token-based system
- **Input validation** on all API endpoints with sort injection prevention
