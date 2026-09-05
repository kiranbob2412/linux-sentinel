# Changelog

## 1.1.0 — 2026-09-05

### Added

- Opt-in `--cloud` mode for AWS EC2 IMDSv2 metadata and Docker readiness.
- Cloud metadata and container details in JSON reports.
- Small Terraform EC2 lab with restricted SSH input and repository bootstrap.
- Cloud Engineer-focused documentation while keeping local scans dependency-free.

## 1.0.0 — 2026-09-05

### Added

- Read-only host collection from `/proc`, filesystem metadata, `systemd`, and
  safe package-manager probes.
- Health checks for disk, memory, load, uptime, services, sockets, permissions,
  UID 0 accounts, SSH configuration, and pending updates.
- Stable JSON schema plus terminal and self-contained HTML reports.
- Configurable thresholds and warning/critical exit policies for automation.
- Optional systemd service and daily timer.
- Installer, uninstaller, built-in unit tests, CI workflow, and architecture
  documentation.

### Safety

- External commands use argument arrays, captured output, and bounded timeouts.
- No command in the scanner mutates services, packages, permissions, or files.