from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .checks import run_checks
from .collectors import collect_snapshot
from .config import load_thresholds
from .reporting import new_report, render_html, render_json, render_table


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="linuxops-sentinel",
        description="Read-only Linux health and security auditing.",
    )
    subparsers = parser.add_subparsers(dest="command")
    scan = subparsers.add_parser("scan", help="collect host data and evaluate checks")
    scan.add_argument("--format", choices=("table", "json", "html"), default="table")
    scan.add_argument("--output", type=Path, help="write the report to a file")
    scan.add_argument("--root", type=Path, default=Path("/"), help=argparse.SUPPRESS)
    scan.add_argument("--config", type=Path, help="path to a TOML threshold file")
    scan.add_argument("--min-severity", choices=("pass", "unknown", "warning", "critical"), default="pass")
    scan.add_argument("--exit-code", choices=("never", "warning", "critical"), default="never")
    scan.add_argument(
        "--cloud",
        action="store_true",
        help="enable opt-in AWS EC2 IMDSv2 and Docker readiness checks",
    )
    subparsers.add_parser("version", help="show the scanner version")
    return parser


def _exit_for(report_severity: str, policy: str) -> int:
    if policy == "critical" and report_severity == "critical":
        return 1
    if policy == "warning" and report_severity in ("warning", "critical"):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "version":
        print(f"LinuxOps Sentinel {__version__}")
        return 0
    if args.command not in (None, "scan"):
        parser.error(f"unknown command: {args.command}")
    if args.command is None:
        args = parser.parse_args(["scan", *(argv or [])])
    try:
        thresholds = load_thresholds(args.config)
        snapshot = collect_snapshot(
            args.root,
            cloud_profile="aws" if args.cloud else None,
            include_containers=args.cloud,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    report = new_report(
        __version__,
        snapshot,
        run_checks(snapshot, thresholds, include_cloud=args.cloud),
        thresholds.as_dict(),
    )
    overall = report.overall
    counts = report.counts
    minimum_rank = {"pass": 0, "unknown": 1, "warning": 2, "critical": 3}[args.min_severity]
    checks = tuple(result for result in report.checks if result.severity.rank >= minimum_rank)
    report = report.__class__(report.version, report.scanned_at, report.snapshot, checks, report.thresholds, overall, counts)
    rendered = {"table": render_table, "json": render_json, "html": render_html}[args.format](report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        if args.format == "table":
            print(f"Report written to {args.output}")
    else:
        print(rendered, end="")
    return _exit_for(report.overall.value, args.exit_code)