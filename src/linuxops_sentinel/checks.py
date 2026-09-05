from __future__ import annotations

from collections.abc import Callable

from .config import Thresholds
from .models import CheckResult, Severity, SystemSnapshot

Check = Callable[[SystemSnapshot, Thresholds], CheckResult]


def check_disk(snapshot: SystemSnapshot, thresholds: Thresholds) -> CheckResult:
    check_id = "disk.root-usage"
    if snapshot.disk_total_bytes is None or snapshot.disk_free_bytes is None or snapshot.disk_total_bytes == 0:
        return CheckResult(check_id, "Root filesystem usage", Severity.UNKNOWN, "Disk usage could not be collected.")
    used_percent = (1 - snapshot.disk_free_bytes / snapshot.disk_total_bytes) * 100
    severity = Severity.PASS
    if used_percent >= thresholds.disk_critical_percent:
        severity = Severity.CRITICAL
    elif used_percent >= thresholds.disk_warning_percent:
        severity = Severity.WARNING
    return CheckResult(
        check_id,
        "Root filesystem usage",
        severity,
        f"Root filesystem is {used_percent:.1f}% full.",
        {"used_percent": round(used_percent, 2), "free_bytes": snapshot.disk_free_bytes},
        "Remove or rotate old logs and artifacts; keep recovery space available.",
    )


def check_memory(snapshot: SystemSnapshot, thresholds: Thresholds) -> CheckResult:
    check_id = "memory.available"
    if snapshot.memory_total_bytes is None or snapshot.memory_available_bytes is None or snapshot.memory_total_bytes == 0:
        return CheckResult(check_id, "Available memory", Severity.UNKNOWN, "Memory data could not be collected.")
    used_percent = (1 - snapshot.memory_available_bytes / snapshot.memory_total_bytes) * 100
    severity = Severity.PASS
    if used_percent >= thresholds.memory_critical_percent:
        severity = Severity.CRITICAL
    elif used_percent >= thresholds.memory_warning_percent:
        severity = Severity.WARNING
    return CheckResult(
        check_id,
        "Available memory",
        severity,
        f"Memory utilization is {used_percent:.1f}%.",
        {"used_percent": round(used_percent, 2), "available_bytes": snapshot.memory_available_bytes},
        "Inspect memory-heavy processes and configure swap before the host starts killing workloads.",
    )


def check_load(snapshot: SystemSnapshot, thresholds: Thresholds) -> CheckResult:
    check_id = "cpu.load-1m"
    if snapshot.load_1m is None or snapshot.cpu_count < 1:
        return CheckResult(check_id, "CPU load", Severity.UNKNOWN, "CPU load could not be collected.")
    ratio = snapshot.load_1m / snapshot.cpu_count
    severity = Severity.PASS
    if ratio >= thresholds.load_critical_multiplier:
        severity = Severity.CRITICAL
    elif ratio >= thresholds.load_warning_multiplier:
        severity = Severity.WARNING
    return CheckResult(
        check_id,
        "CPU load",
        severity,
        f"1-minute load is {snapshot.load_1m:.2f} across {snapshot.cpu_count} CPU(s).",
        {"load_1m": snapshot.load_1m, "load_per_cpu": round(ratio, 2)},
        "Inspect the busiest processes with top or ps and check for blocked I/O.",
    )


def check_uptime(snapshot: SystemSnapshot, thresholds: Thresholds) -> CheckResult:
    check_id = "host.uptime"
    if snapshot.uptime_seconds is None:
        return CheckResult(check_id, "Host uptime", Severity.UNKNOWN, "Uptime could not be collected.")
    days = snapshot.uptime_seconds / 86400
    severity = Severity.WARNING if days >= thresholds.uptime_warning_days else Severity.PASS
    return CheckResult(
        check_id,
        "Host uptime",
        severity,
        f"Host has been running for {days:.1f} day(s).",
        {"uptime_days": round(days, 2)},
        "Plan a maintenance window to apply kernel and security updates.",
    )


def check_services(snapshot: SystemSnapshot, thresholds: Thresholds) -> CheckResult:
    del thresholds
    if not snapshot.service_manager_available:
        return CheckResult("services.systemd", "Service manager", Severity.UNKNOWN, "systemd service state is unavailable.")
    return CheckResult(
        "services.systemd",
        "Service manager",
        Severity.PASS,
        f"systemd is available with {len(snapshot.running_services)} running service(s).",
        {"running_services": list(snapshot.running_services)},
    )


def check_ports(snapshot: SystemSnapshot, thresholds: Thresholds) -> CheckResult:
    del thresholds
    return CheckResult(
        "network.listening-sockets",
        "Listening sockets",
        Severity.PASS,
        f"Found {len(snapshot.listening_ports)} listening socket(s).",
        {"sockets": list(snapshot.listening_ports)},
        "Review every internet-facing socket and restrict it with a firewall when it is not required.",
    )


def check_world_writable(snapshot: SystemSnapshot, thresholds: Thresholds) -> CheckResult:
    del thresholds
    if snapshot.world_writable_paths:
        return CheckResult(
            "security.world-writable",
            "World-writable directories",
            Severity.WARNING,
            f"Found {len(snapshot.world_writable_paths)} world-writable directory/directories without a sticky bit.",
            {"paths": list(snapshot.world_writable_paths)},
            "Add the sticky bit or tighten permissions after confirming application requirements.",
        )
    return CheckResult("security.world-writable", "World-writable directories", Severity.PASS, "No unsafe shared directories were found.")


def check_root_users(snapshot: SystemSnapshot, thresholds: Thresholds) -> CheckResult:
    del thresholds
    if not snapshot.root_users:
        return CheckResult("security.uid-zero", "UID 0 accounts", Severity.UNKNOWN, "The passwd database could not be inspected.")
    if len(snapshot.root_users) > 1:
        return CheckResult(
            "security.uid-zero",
            "UID 0 accounts",
            Severity.WARNING,
            f"Found {len(snapshot.root_users)} accounts with UID 0.",
            {"accounts": list(snapshot.root_users)},
            "Remove unnecessary UID 0 accounts and use narrowly scoped sudo rules.",
        )
    return CheckResult(
        "security.uid-zero",
        "UID 0 accounts",
        Severity.PASS,
        "Only the expected root account has UID 0.",
        {"accounts": list(snapshot.root_users)},
    )


def check_ssh_permissions(snapshot: SystemSnapshot, thresholds: Thresholds) -> CheckResult:
    del thresholds
    if snapshot.sshd_config_mode is None:
        return CheckResult("security.ssh-permissions", "SSH configuration permissions", Severity.UNKNOWN, "sshd_config was not found or could not be inspected.")
    if snapshot.sshd_config_mode & 0o022:
        return CheckResult(
            "security.ssh-permissions",
            "SSH configuration permissions",
            Severity.CRITICAL,
            f"sshd_config mode is {snapshot.sshd_config_mode:04o}; group/other write is enabled.",
            {"mode": oct(snapshot.sshd_config_mode)},
            "Remove group and other write permissions from sshd_config and review file ownership.",
        )
    return CheckResult(
        "security.ssh-permissions",
        "SSH configuration permissions",
        Severity.PASS,
        f"sshd_config mode is {snapshot.sshd_config_mode:04o}.",
        {"mode": oct(snapshot.sshd_config_mode)},
    )


def check_updates(snapshot: SystemSnapshot, thresholds: Thresholds) -> CheckResult:
    del thresholds
    if snapshot.pending_updates is None:
        return CheckResult("packages.pending-updates", "Pending package updates", Severity.UNKNOWN, "No supported package manager result was available.")
    if snapshot.pending_updates > 0:
        return CheckResult(
            "packages.pending-updates",
            "Pending package updates",
            Severity.WARNING,
            f"{snapshot.pending_updates} package update(s) are available.",
            {"pending_updates": snapshot.pending_updates},
            "Review the changelog and apply security updates during a maintenance window.",
        )
    return CheckResult("packages.pending-updates", "Pending package updates", Severity.PASS, "No package updates are currently pending.")


def check_aws_metadata(snapshot: SystemSnapshot, thresholds: Thresholds) -> CheckResult:
    del thresholds
    cloud = snapshot.cloud
    if cloud is None:
        return CheckResult("cloud.aws-metadata", "AWS EC2 metadata", Severity.UNKNOWN, "AWS cloud checks were not enabled.")
    if not cloud.reachable:
        return CheckResult(
            "cloud.aws-metadata",
            "AWS EC2 metadata",
            Severity.UNKNOWN,
            cloud.error or "AWS IMDSv2 is not reachable; this host may not be an EC2 instance.",
            {"provider": cloud.provider},
            "Run this check on an EC2 instance or keep cloud checks disabled for local-only scans.",
        )
    if cloud.error:
        return CheckResult(
            "cloud.aws-metadata",
            "AWS EC2 metadata",
            Severity.WARNING,
            cloud.error,
            {"provider": cloud.provider},
            "Confirm the instance exposes the expected IMDSv2 metadata fields.",
        )
    return CheckResult(
        "cloud.aws-metadata",
        "AWS EC2 metadata",
        Severity.PASS,
        f"EC2 {cloud.instance_id} is running in {cloud.region}.",
        {
            "instance_id": cloud.instance_id,
            "region": cloud.region,
            "availability_zone": cloud.availability_zone,
            "instance_type": cloud.instance_type,
        },
    )


def check_docker(snapshot: SystemSnapshot, thresholds: Thresholds) -> CheckResult:
    del thresholds
    if snapshot.docker_available is None:
        return CheckResult("containers.docker", "Docker runtime", Severity.UNKNOWN, "Container checks were not enabled.")
    if not snapshot.docker_available:
        return CheckResult(
            "containers.docker",
            "Docker runtime",
            Severity.UNKNOWN,
            snapshot.docker_error or "Docker runtime is unavailable.",
            {},
            "Start Docker or check the current user's access to the Docker socket.",
        )
    return CheckResult(
        "containers.docker",
        "Docker runtime",
        Severity.PASS,
        f"Docker is available with {len(snapshot.docker_containers)} running container(s).",
        {"containers": list(snapshot.docker_containers)},
    )


DEFAULT_CHECKS: tuple[Check, ...] = (
    check_disk,
    check_memory,
    check_load,
    check_uptime,
    check_services,
    check_ports,
    check_world_writable,
    check_root_users,
    check_ssh_permissions,
    check_updates,
)


def run_checks(snapshot: SystemSnapshot, thresholds: Thresholds, include_cloud: bool = False) -> tuple[CheckResult, ...]:
    results = [check(snapshot, thresholds) for check in DEFAULT_CHECKS]
    if include_cloud:
        results.extend((check_aws_metadata(snapshot, thresholds), check_docker(snapshot, thresholds)))
    results.extend(
        CheckResult("collector.errors", "Collector errors", Severity.WARNING, error, remediation="Review the host permissions and collector logs.")
        for error in snapshot.collection_errors
    )
    return tuple(results)