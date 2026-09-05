import json
import unittest
from datetime import datetime, timezone

from linuxops_sentinel.config import Thresholds
from linuxops_sentinel.models import CheckResult, ScanReport, Severity, SystemSnapshot
from linuxops_sentinel.reporting import render_html, render_json, render_table


class ReportingTests(unittest.TestCase):
    def setUp(self):
        host = SystemSnapshot(
            hostname="report-host",
            kernel="6.8.0",
            os_name="Linux",
            cpu_count=2,
            load_1m=0.4,
            memory_total_bytes=100,
            memory_available_bytes=50,
            disk_total_bytes=100,
            disk_free_bytes=50,
            uptime_seconds=60,
        )
        self.report = ScanReport(
            "1.0.0",
            datetime(2026, 9, 5, tzinfo=timezone.utc),
            host,
            (
                CheckResult("demo.ok", "Healthy", Severity.PASS, "All good."),
                CheckResult("demo.warn", "Needs attention", Severity.WARNING, "Review <this>."),
            ),
            Thresholds().as_dict(),
        )

    def test_json_is_machine_readable(self):
        payload = json.loads(render_json(self.report))
        self.assertEqual(payload["overall"], "warning")
        self.assertEqual(payload["checks"][1]["severity"], "warning")

    def test_table_contains_summary(self):
        output = render_table(self.report)
        self.assertIn("Overall: WARNING", output)
        self.assertIn("demo.warn", output)

    def test_html_escapes_messages(self):
        output = render_html(self.report)
        self.assertIn("Review &lt;this&gt;.", output)
        self.assertNotIn("Review <this>.", output)


if __name__ == "__main__":
    unittest.main()