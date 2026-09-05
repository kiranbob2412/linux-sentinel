# Architecture

LinuxOps Sentinel follows a small, explicit pipeline:

```text
host files + safe commands
          |
          v
     collectors.py
          |
          v
    SystemSnapshot (immutable input)
          |
          v
       checks.py
          |
          v
     CheckResult list
          |
          v
 reporters.py -> terminal | JSON | HTML
```

When `scan --cloud` is explicitly enabled, two optional collectors are added:
AWS EC2 IMDSv2 metadata and Docker runtime state. They never run on the
default local scan, never request AWS credentials, and report `UNKNOWN` when a
machine is not an EC2 host or Docker is unavailable.

## Boundaries

### Collection is read-only

Collectors read `/proc`, `/etc/passwd`, selected file metadata, and
filesystem statistics. External commands are executed with `shell=False`,
short timeouts, and captured output. The AWS collector uses IMDSv2 token
authentication only; it does not ask for or handle AWS access keys. The tool
never runs a command supplied by the user and never performs a state-changing
action.

### Policy is separate from collection

Checks receive a `SystemSnapshot` instead of reaching into the host. This
makes threshold behavior deterministic and lets tests cover high-risk cases
such as full disks, excessive load, and unsafe permissions.

### Reports are portable

The JSON report is the stable machine contract. HTML and terminal output are
views over the same report object; they do not run new checks or make different
decisions.

## Severity model

`PASS` means the measured value is within its configured boundary.
`WARNING` means operator attention is recommended. `CRITICAL` means the host
has a condition that can cause immediate service impact or is a strong
security signal. `UNKNOWN` means the host did not expose enough information;
the scanner fails explicitly instead of silently treating missing data as safe.

## Extending a check

1. Add the smallest required field to `SystemSnapshot`.
2. Collect it in `collectors.py` with a bounded, read-only operation.
3. Add a pure check function in `checks.py`.
4. Register the function in `DEFAULT_CHECKS`.
5. Add boundary tests and one report assertion.
6. Document the remediation and any privilege requirement.

## Terraform lab boundary

The Terraform folder is intentionally separate from the scanner. It provides
one small EC2 learning environment with a restricted SSH CIDR, required
IMDSv2 tokens, and first-boot report generation. It is not intended to be a
general-purpose VPC module or a production landing zone.