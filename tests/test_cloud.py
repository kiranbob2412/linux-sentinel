import unittest

from linuxops_sentinel.checks import check_aws_metadata
from linuxops_sentinel.cloud import parse_aws_metadata
from linuxops_sentinel.config import Thresholds
from linuxops_sentinel.models import CloudMetadata, Severity, SystemSnapshot


class CloudTests(unittest.TestCase):
    def test_parse_metadata_creates_ec2_identity(self):
        result = parse_aws_metadata(
            {
                "instance_id": "i-123",
                "region": "ap-south-1",
                "availability_zone": "ap-south-1a",
                "instance_type": "t3.micro",
            }
        )
        self.assertTrue(result.reachable)
        self.assertEqual(result.instance_id, "i-123")
        self.assertIsNone(result.error)

    def test_missing_metadata_is_explicit(self):
        result = parse_aws_metadata({"instance_id": "i-123"})
        self.assertTrue(result.reachable)
        self.assertIn("Missing metadata fields", result.error or "")

    def test_non_ec2_host_is_unknown_not_failed(self):
        snapshot = SystemSnapshot(
            hostname="laptop",
            kernel="6.8.0",
            os_name="Linux",
            cpu_count=4,
            load_1m=0.2,
            memory_total_bytes=100,
            memory_available_bytes=80,
            disk_total_bytes=100,
            disk_free_bytes=80,
            uptime_seconds=60,
            cloud=CloudMetadata("aws", reachable=False, error="AWS IMDSv2 is not reachable"),
        )
        result = check_aws_metadata(snapshot, Thresholds())
        self.assertEqual(result.severity, Severity.UNKNOWN)


if __name__ == "__main__":
    unittest.main()