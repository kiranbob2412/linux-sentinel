# LinuxOps Sentinel

**LinuxOps Sentinel** is a dependency-free Linux health and security auditing
tool for small servers, developer machines, homelabs, and small cloud VMs. It turns common
operations checks into one repeatable command that produces terminal, JSON, or
HTML output suitable for incident notes and lightweight CI gates.

> A practical Linux project built around process inspection, `/proc`, file
> permissions, `systemd`, sockets, package updates, cloud VM metadata, and automation.

## What it checks

- CPU load compared with the number of available cores
- Memory pressure from `/proc/meminfo`
- Root filesystem capacity
- Host uptime and long-running hosts
- Running `systemd` services
- Listening TCP and UDP sockets
- World-writable directories without the sticky bit
- SSH daemon configuration permissions
- Multiple UID 0 accounts
- Pending package updates on `apt` or `dnf` based systems
- Optional AWS EC2 IMDSv2 metadata and Docker readiness checks

Every finding has a stable check ID, severity, evidence, and remediation text.
The scanner is read-only: it does not restart services, change permissions, or
install packages.

## Quick start

```bash
cd linuxops-sentinel

# Run a readable scan without installing anything.
PYTHONPATH=src python3 -m linuxops_sentinel scan

# Generate a machine-readable report for automation.
PYTHONPATH=src python3 -m linuxops_sentinel scan \
  --format json \
  --output reports/latest.json

# Generate a shareable report for a ticket or review.
PYTHONPATH=src python3 -m linuxops_sentinel scan \
  --format html \
  --output reports/latest.html
```

The command exits with status `0` for a healthy host. Use
`--exit-code warning` or `--exit-code critical` to make it useful in CI and
scheduled jobs.

## Example output

```text
LinuxOps Sentinel 1.0.0
Host: devbox (Linux 6.8.0-31-generic)
Scanned: 2026-09-05T10:30:00+05:30

Overall: WARNING
Checks: 8 passed  2 warnings  0 critical  1 unknown

WARN  disk.root-usage       Root filesystem is 86.4% full
      Keep at least 15% free space for logs, package updates, and recovery.

PASS  security.ssh-permissions SSH daemon configuration permissions are safe
```

## Installation

LinuxOps Sentinel uses only the Python standard library and supports Python
3.11+.

```bash
sudo ./scripts/install.sh
linuxops-sentinel scan
```

For an AWS-hosted Linux VM, opt into the cloud-lite checks:

```bash
linuxops-sentinel scan --cloud --format json --output reports/ec2.json
```

This uses EC2 IMDSv2 only and does not require AWS access keys. On a normal
laptop, the cloud check reports `UNKNOWN` instead of making a destructive
change or pretending the machine is an EC2 instance. The same flag also checks
whether Docker is available and lists running containers.

The installer places the executable in `/usr/local/bin`, the application in
`/usr/local/share/linuxops-sentinel`, and optional `systemd` units in
`/etc/systemd/system`.

To remove it:

```bash
sudo ./scripts/uninstall.sh
```

## Scheduled systemd scan

The installer includes a daily timer. It is opt-in so an installation never
changes the host's scheduling without an explicit action.

```bash
sudo systemctl enable --now linuxops-sentinel.timer
systemctl list-timers linuxops-sentinel.timer
sudo journalctl -u linuxops-sentinel.service
```

Reports are written to `/var/log/linuxops-sentinel/report.json`. Override the
location with `--output` in a copied unit or by running the CLI directly.

## Useful commands

```bash
# Only show actionable findings.
linuxops-sentinel scan --min-severity warning

# Use a configuration file with local thresholds.
linuxops-sentinel scan --config config/sentinel.toml

# Treat warnings as a failed check in a pipeline.
linuxops-sentinel scan --format json --exit-code warning

# Inspect the CLI version.
linuxops-sentinel version
```

## Configuration

Copy `config/sentinel.example.toml` and adjust thresholds for the machine:

```toml
[thresholds]
disk_warning_percent = 80
disk_critical_percent = 92
memory_warning_percent = 85
memory_critical_percent = 95
load_warning_multiplier = 1.5
load_critical_multiplier = 3.0
uptime_warning_days = 90
```

Thresholds are intentionally explicit and are included in the JSON report
metadata so a later reader knows how the result was evaluated.

## Development

```bash
make test
make lint
make scan
```

The test suite uses Python's built-in `unittest` module, so a fresh Linux
machine does not need a package download to contribute. `make lint` runs
compile checks and shell syntax checks when ShellCheck is available.

## Cloud Engineer lab

The `terraform/` directory is a deliberately small AWS lab. It launches one
EC2 instance in an existing default-VPC subnet, attaches a restricted security
group, and uses cloud-init-style user data to clone this repository and run a
JSON scan. It is included for learning and portfolio review; it is not a
production network module.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Set ami_id, subnet_id, and your repository_url in terraform.tfvars.
terraform init
terraform fmt -check
terraform validate
terraform plan
terraform apply
terraform destroy
```

Never commit real credentials or a private key. Keep SSH ingress restricted to
your own public IP in `ssh_cidr`.

## Project timeline

The project is organized as a one-month Linux learning and delivery cycle:

| Date | Milestone |
| --- | --- |
| **05 Aug 2026** | Scope, safety rules, output contract, and repository layout |
| **12 Aug 2026** | `/proc`, filesystem, process, and host collectors |
| **19 Aug 2026** | Security checks for permissions, SSH, sockets, and UID 0 |
| **26 Aug 2026** | JSON/HTML reporting, configuration, and CI exit codes |
| **02 Sep 2026** | systemd timer, installer, tests, and operational documentation |
| **05 Sep 2026** | Cloud-lite AWS/EC2 profile, Terraform lab, final review, and GitHub-ready release |

This timeline explains the learning progression clearly when the repository is
shared. Commit dates should always reflect when work was actually performed.

## Design notes

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the data flow and safety
boundaries. The project intentionally keeps collection separate from policy:
collectors read the host, checks evaluate a snapshot, and reporters serialize
the result. That makes the risk-sensitive logic testable without mutating a
real machine.

## License

MIT. See [LICENSE](LICENSE).