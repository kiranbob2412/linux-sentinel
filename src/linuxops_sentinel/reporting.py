from __future__ import annotations

import html
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import CheckResult, ScanReport, Severity


def _json_value(report: ScanReport) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "scanner_version": report.version,
        "scanned_at": report.scanned_at.isoformat(),
        "overall": report.overall.value,
        "counts": report.counts,
        "thresholds": report.thresholds,
        "host": {
            "hostname": report.snapshot.hostname,
            "kernel": report.snapshot.kernel,
            "os": report.snapshot.os_name,
            "cpu_count": report.snapshot.cpu_count,
            "uptime_seconds": report.snapshot.uptime_seconds,
            "listening_ports": list(report.snapshot.listening_ports),
            "running_services": list(report.snapshot.running_services),
        },
        "cloud": asdict(report.snapshot.cloud) if report.snapshot.cloud else None,
        "docker": {
            "available": report.snapshot.docker_available,
            "containers": list(report.snapshot.docker_containers),
            "error": report.snapshot.docker_error,
        },
        "checks": [asdict(check) | {"severity": check.severity.value} for check in report.checks],
    }


def render_json(report: ScanReport) -> str:
    return json.dumps(_json_value(report), indent=2, sort_keys=True) + "\n"


def _label(result: CheckResult) -> str:
    return result.severity.value.upper().ljust(8)


def render_table(report: ScanReport) -> str:
    counts = report.counts
    lines = [
        f"LinuxOps Sentinel {report.version}",
        f"Host: {report.snapshot.hostname} ({report.snapshot.os_name} {report.snapshot.kernel})",
        f"Scanned: {report.scanned_at.isoformat()}",
        "",
        f"Overall: {report.overall.value.upper()}",
        "Checks: "
        + "  ".join(f"{severity.value} {counts[severity.value]}" for severity in Severity),
        "",
    ]
    for result in report.checks:
        lines.append(f"{_label(result)} {result.check_id:<28} {result.message}")
        if result.remediation and result.severity in (Severity.WARNING, Severity.CRITICAL):
            lines.append(f"         Remediation: {result.remediation}")
    return "\n".join(lines) + "\n"


def render_html(report: ScanReport) -> str:
    cards = []
    for result in report.checks:
        evidence = html.escape(json.dumps(result.details, sort_keys=True))
        remediation = (
            f"<p class='remediation'><strong>Remediation:</strong> {html.escape(result.remediation)}</p>"
            if result.remediation and result.severity in (Severity.WARNING, Severity.CRITICAL)
            else ""
        )
        cards.append(
            f"<article class='check {result.severity.value}'>"
            f"<div class='check-head'><span class='badge'>{result.severity.value.upper()}</span>"
            f"<code>{html.escape(result.check_id)}</code></div>"
            f"<h2>{html.escape(result.title)}</h2><p>{html.escape(result.message)}</p>"
            f"<details><summary>Evidence</summary><pre>{evidence}</pre></details>{remediation}</article>"
        )
    overall = report.overall.value
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>LinuxOps Sentinel — {html.escape(report.snapshot.hostname)}</title>
<style>
:root {{ color-scheme: dark; font-family: system-ui, sans-serif; background: #10141b; color: #e6edf3; }}
body {{ max-width: 1050px; margin: 0 auto; padding: 36px 20px; }}
header {{ border-bottom: 1px solid #303947; padding-bottom: 24px; margin-bottom: 24px; }}
h1 {{ margin: 0 0 8px; font-size: clamp(1.8rem, 4vw, 3rem); }}
.meta {{ color: #9da9b8; }} .overview {{ display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin: 20px 0; }}
.overall, .badge {{ border-radius: 999px; padding: 5px 10px; font-weight: 700; letter-spacing: .06em; }}
.overall {{ background: #253044; color: #8bd5ff; }} .overall.warning, .badge.warning {{ color:#ffd166; background:#48391b; }}
.overall.critical, .badge.critical {{ color:#ff8b8b; background:#4a2228; }} .badge.pass {{ color:#83e6ad; background:#1d3e31; }}
.badge.unknown {{ color:#b9c3d0; background:#303947; }} code, pre {{ color:#b9c3d0; }}
.checks {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap:14px; }}
.check {{ background:#171d27; border:1px solid #303947; border-left:4px solid #83e6ad; border-radius:10px; padding:18px; }}
.check.warning {{ border-left-color:#ffd166; }} .check.critical {{ border-left-color:#ff8b8b; }} .check.unknown {{ border-left-color:#8894a5; }}
.check-head {{ display:flex; justify-content:space-between; gap:10px; align-items:center; }} h2 {{ font-size:1.05rem; margin-bottom:8px; }}
.check p {{ color:#b8c3d0; line-height:1.5; }} summary {{ cursor:pointer; color:#8bd5ff; }} pre {{ white-space:pre-wrap; overflow:auto; }}
.remediation {{ border-top:1px solid #303947; padding-top:12px; font-size:.93rem; }}
</style></head><body>
<header><h1>LinuxOps Sentinel</h1>
<div class="meta">{html.escape(report.snapshot.hostname)} · {html.escape(report.snapshot.os_name)} {html.escape(report.snapshot.kernel)} · {html.escape(report.scanned_at.isoformat())}</div>
<div class="overview"><span class="overall {overall}">OVERALL: {overall.upper()}</span>
<span>{report.counts["pass"]} passed</span><span>{report.counts["warning"]} warnings</span>
<span>{report.counts["critical"]} critical</span><span>{report.counts["unknown"]} unknown</span></div></header>
<main class="checks">{"".join(cards)}</main>
</body></html>"""


def write_report(report: ScanReport, output: Path, format_name: str) -> None:
    renderer = {"json": render_json, "html": render_html, "table": render_table}[format_name]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(renderer(report), encoding="utf-8")


def new_report(version: str, snapshot: Any, checks: tuple[CheckResult, ...], thresholds: dict[str, int | float]) -> ScanReport:
    return ScanReport(version, datetime.now().astimezone(), snapshot, checks, thresholds)