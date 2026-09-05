from __future__ import annotations

import tomllib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Thresholds:
    disk_warning_percent: float = 80.0
    disk_critical_percent: float = 92.0
    memory_warning_percent: float = 85.0
    memory_critical_percent: float = 95.0
    load_warning_multiplier: float = 1.5
    load_critical_multiplier: float = 3.0
    uptime_warning_days: float = 90.0

    def as_dict(self) -> dict[str, int | float]:
        return asdict(self)


def load_thresholds(path: Path | None) -> Thresholds:
    if path is None:
        return Thresholds()
    with path.open("rb") as handle:
        data: dict[str, Any] = tomllib.load(handle)
    values = data.get("thresholds", {})
    defaults = Thresholds()
    allowed = defaults.as_dict()
    for key, value in values.items():
        if key not in allowed or not isinstance(value, (int, float)):
            raise ValueError(f"Unsupported threshold value: {key}")
        if value < 0:
            raise ValueError(f"Threshold cannot be negative: {key}")
        allowed[key] = value
    if allowed["disk_warning_percent"] >= allowed["disk_critical_percent"]:
        raise ValueError("disk_warning_percent must be lower than disk_critical_percent")
    if allowed["memory_warning_percent"] >= allowed["memory_critical_percent"]:
        raise ValueError("memory_warning_percent must be lower than memory_critical_percent")
    if allowed["load_warning_multiplier"] >= allowed["load_critical_multiplier"]:
        raise ValueError("load_warning_multiplier must be lower than load_critical_multiplier")
    return Thresholds(**allowed)