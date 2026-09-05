from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    PASS = "pass"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

    @property
    def rank(self) -> int:
        return {
            Severity.PASS: 0,
            Severity.UNKNOWN: 1,
            Severity.WARNING: 2,
            Severity.CRITICAL: 3,
        }[self]


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    title: str
    severity: Severity
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    remediation: str | None = None


@dataclass(frozen=True)
class CloudMetadata:
    provider: str
    reachable: bool
    instance_id: str | None = None
    region: str | None = None
    availability_zone: str | None = None
    instance_type: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class SystemSnapshot:
    hostname: str
    kernel: str
    os_name: str
    cpu_count: int
    load_1m: float | None
    memory_total_bytes: int | None
    memory_available_bytes: int | None
    disk_total_bytes: int | None
    disk_free_bytes: int | None
    uptime_seconds: float | None
    running_services: tuple[str, ...] = ()
    service_manager_available: bool = False
    listening_ports: tuple[str, ...] = ()
    world_writable_paths: tuple[str, ...] = ()
    root_users: tuple[str, ...] = ()
    sshd_config_mode: int | None = None
    pending_updates: int | None = None
    collection_errors: tuple[str, ...] = ()
    cloud: CloudMetadata | None = None
    docker_available: bool | None = None
    docker_containers: tuple[str, ...] = ()
    docker_error: str | None = None


@dataclass(frozen=True)
class ScanReport:
    version: str
    scanned_at: datetime
    snapshot: SystemSnapshot
    checks: tuple[CheckResult, ...]
    thresholds: dict[str, int | float]
    overall_override: Severity | None = None
    counts_override: dict[str, int] | None = None

    @property
    def overall(self) -> Severity:
        if self.overall_override is not None:
            return self.overall_override
        return max((result.severity for result in self.checks), key=lambda item: item.rank, default=Severity.UNKNOWN)

    @property
    def counts(self) -> dict[str, int]:
        if self.counts_override is not None:
            return self.counts_override
        return {severity.value: sum(result.severity is severity for result in self.checks) for severity in Severity}