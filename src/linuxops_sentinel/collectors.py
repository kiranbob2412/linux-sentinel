from __future__ import annotations

import os
import platform
import re
import shutil
import socket
import stat
import subprocess
from pathlib import Path

from .cloud import collect_aws_metadata
from .models import SystemSnapshot


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _command(args: list[str], timeout: float = 3.0) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""
    return completed.returncode, completed.stdout


def _memory(proc_root: Path) -> tuple[int | None, int | None]:
    text = _read(proc_root / "meminfo")
    if text is None:
        return None, None
    values: dict[str, int] = {}
    for line in text.splitlines():
        match = re.match(r"^(MemTotal|MemAvailable):\s+(\d+)\s+kB$", line)
        if match:
            values[match.group(1)] = int(match.group(2)) * 1024
    return values.get("MemTotal"), values.get("MemAvailable")


def _load_and_uptime(proc_root: Path) -> tuple[float | None, float | None]:
    load_text = _read(proc_root / "loadavg")
    uptime_text = _read(proc_root / "uptime")
    load = None
    uptime = None
    if load_text:
        try:
            load = float(load_text.split()[0])
        except (IndexError, ValueError):
            pass
    if uptime_text:
        try:
            uptime = float(uptime_text.split()[0])
        except (IndexError, ValueError):
            pass
    return load, uptime


def _services() -> tuple[bool, tuple[str, ...]]:
    code, output = _command(
        ["systemctl", "list-units", "--type=service", "--state=running", "--no-legend", "--no-pager"]
    )
    if code == 127:
        return False, ()
    names = tuple(sorted(line.split()[0] for line in output.splitlines() if line.strip()))
    return code == 0, names


def _ports() -> tuple[str, ...]:
    code, output = _command(["ss", "-H", "-lntu"])
    if code != 0:
        return ()
    ports: set[str] = set()
    for line in output.splitlines():
        columns = line.split()
        if len(columns) >= 5:
            ports.add(f"{columns[0].lower()}:{columns[4]}")
    return tuple(sorted(ports))


def _world_writable(root: Path) -> tuple[str, ...]:
    candidates = [root / "tmp", root / "var" / "tmp", root / "dev" / "shm"]
    findings: list[str] = []
    for base in candidates:
        if not base.is_dir():
            continue
        try:
            for item in base.iterdir():
                mode = item.stat().st_mode
                if item.is_dir() and mode & stat.S_IWOTH and not mode & stat.S_ISVTX:
                    findings.append(str(item))
        except OSError:
            continue
    return tuple(sorted(findings))


def _root_users(root: Path) -> tuple[str, ...]:
    text = _read(root / "etc" / "passwd")
    if text is None:
        return ()
    names = []
    for line in text.splitlines():
        parts = line.split(":")
        if len(parts) >= 3 and parts[2] == "0":
            names.append(parts[0])
    return tuple(sorted(names))


def _sshd_mode(root: Path) -> int | None:
    path = root / "etc" / "ssh" / "sshd_config"
    try:
        return stat.S_IMODE(path.stat().st_mode)
    except OSError:
        return None


def _pending_updates() -> int | None:
    if shutil.which("apt-get"):
        code, output = _command(["apt-get", "-s", "-q", "upgrade"], timeout=8.0)
        if code == 0:
            return sum(1 for line in output.splitlines() if line.startswith("Inst "))
    if shutil.which("dnf"):
        code, output = _command(["dnf", "-q", "check-update"], timeout=8.0)
        if code in (0, 100):
            return sum(1 for line in output.splitlines() if line and not line.startswith("Last metadata"))
    return None


def _docker() -> tuple[bool | None, tuple[str, ...], str | None]:
    if shutil.which("docker") is None:
        return None, (), "docker executable not found"
    code, output = _command(["docker", "ps", "--format", "{{.Names}}|{{.Status}}"])
    if code != 0:
        return False, (), "docker daemon is unavailable or permission was denied"
    containers = tuple(sorted(line for line in output.splitlines() if line.strip()))
    return True, containers, None


def collect_snapshot(
    root: Path = Path("/"),
    cloud_profile: str | None = None,
    include_containers: bool = False,
) -> SystemSnapshot:
    root = root.resolve()
    errors: list[str] = []
    proc_root = root / "proc"
    total_memory, available_memory = _memory(proc_root)
    load, uptime = _load_and_uptime(proc_root)
    try:
        disk = shutil.disk_usage(root)
        disk_total, disk_free = disk.total, disk.free
    except OSError as exc:
        disk_total = disk_free = None
        errors.append(f"disk: {exc}")
    service_manager_available, services = _services() if root == Path("/") else (False, ())
    ports = _ports() if root == Path("/") else ()
    cloud = collect_aws_metadata() if cloud_profile == "aws" and root == Path("/") else None
    docker_available, docker_containers, docker_error = (
        _docker() if include_containers and root == Path("/") else (None, (), None)
    )
    return SystemSnapshot(
        hostname=socket.gethostname(),
        kernel=platform.release(),
        os_name=platform.system(),
        cpu_count=os.cpu_count() or 1,
        load_1m=load,
        memory_total_bytes=total_memory,
        memory_available_bytes=available_memory,
        disk_total_bytes=disk_total,
        disk_free_bytes=disk_free,
        uptime_seconds=uptime,
        running_services=services,
        service_manager_available=service_manager_available,
        listening_ports=ports,
        world_writable_paths=_world_writable(root),
        root_users=_root_users(root),
        sshd_config_mode=_sshd_mode(root),
        pending_updates=_pending_updates() if root == Path("/") else None,
        collection_errors=tuple(errors),
        cloud=cloud,
        docker_available=docker_available,
        docker_containers=docker_containers,
        docker_error=docker_error,
    )