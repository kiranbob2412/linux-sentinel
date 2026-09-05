# Security policy

## Scope

LinuxOps Sentinel is designed for local, read-only inspection. It may be run
as an unprivileged user. Running it as root can reveal more file metadata, but
the program still does not modify the system.

## Reporting a vulnerability

Please do not open a public issue for a vulnerability that could expose host
data or allow command execution. Contact the repository owner privately with:

1. A description of the issue and affected version.
2. Reproduction steps or a minimal proof of concept.
3. The expected and observed behavior.
4. Any suggested mitigation.

Do not include passwords, private keys, access tokens, or complete production
reports in a vulnerability report.