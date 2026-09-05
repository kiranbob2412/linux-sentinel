import unittest

from linuxops_sentinel.checks import check_disk, check_load, check_memory, check_root_users, check_ssh_permissions
from linuxops_sentinel.config import Thresholds
from linuxops_sentinel.models import Severity, SystemSnapshot


def snapshot(**changes):
    values = dict(
        hostname="test-host",
        kernel="6.8.0",
        os_name="Linux",
        cpu_count=4,
        load_1m=1.0,
        memory_total_bytes=1000,
        memory_available_bytes=500,
        disk_total_bytes=1000,
        disk_free_bytes=500,
        uptime_seconds=3600,
        root_users=("root",),
        sshd_config_mode=0o600,
    )
    values.update(changes)
    return SystemSnapshot(**values)


class CheckTests(unittest.TestCase):
    def test_disk_warning_boundary(self):
        result = check_disk(snapshot(disk_free_bytes=190), Thresholds())
        self.assertEqual(result.severity, Severity.WARNING)
        self.assertEqual(result.check_id, "disk.root-usage")

    def test_disk_critical_boundary(self):
        result = check_disk(snapshot(disk_free_bytes=50), Thresholds())
        self.assertEqual(result.severity, Severity.CRITICAL)

    def test_missing_memory_is_unknown(self):
        result = check_memory(snapshot(memory_total_bytes=None), Thresholds())
        self.assertEqual(result.severity, Severity.UNKNOWN)

    def test_load_is_normalized_by_cpu_count(self):
        result = check_load(snapshot(load_1m=6.0, cpu_count=4), Thresholds())
        self.assertEqual(result.severity, Severity.WARNING)

    def test_extra_uid_zero_account_warns(self):
        result = check_root_users(snapshot(root_users=("root", "operator")), Thresholds())
        self.assertEqual(result.severity, Severity.WARNING)

    def test_group_writable_ssh_config_is_critical(self):
        result = check_ssh_permissions(snapshot(sshd_config_mode=0o664), Thresholds())
        self.assertEqual(result.severity, Severity.CRITICAL)


if __name__ == "__main__":
    unittest.main()