from __future__ import annotations

from collections.abc import Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import CloudMetadata

IMDS_BASE = "http://169.254.169.254/latest"


def parse_aws_metadata(values: Mapping[str, str]) -> CloudMetadata:
    """Build a stable cloud model from IMDS fields without making a request."""
    required = ("instance_id", "region", "availability_zone", "instance_type")
    missing = [name for name in required if not values.get(name)]
    if missing:
        return CloudMetadata(
            provider="aws",
            reachable=True,
            instance_id=values.get("instance_id"),
            region=values.get("region"),
            availability_zone=values.get("availability_zone"),
            instance_type=values.get("instance_type"),
            error=f"Missing metadata fields: {', '.join(missing)}",
        )
    return CloudMetadata(
        provider="aws",
        reachable=True,
        instance_id=values["instance_id"],
        region=values["region"],
        availability_zone=values["availability_zone"],
        instance_type=values["instance_type"],
    )


def _request(path: str, token: str | None, method: str = "GET") -> str:
    headers = {"X-aws-ec2-metadata-token": token} if token else {}
    request = Request(f"{IMDS_BASE}/{path}", headers=headers, method=method)
    with urlopen(request, timeout=0.8) as response:
        return response.read(256).decode("utf-8").strip()


def collect_aws_metadata() -> CloudMetadata:
    """Read EC2 metadata using IMDSv2 only; credentials are never requested."""
    try:
        token = _request("api/token", None, method="PUT")
        values = {
            "instance_id": _request("meta-data/instance-id", token),
            "region": _request("meta-data/placement/region", token),
            "availability_zone": _request("meta-data/placement/availability-zone", token),
            "instance_type": _request("meta-data/instance-type", token),
        }
        return parse_aws_metadata(values)
    except (HTTPError, URLError, OSError, TimeoutError) as exc:
        return CloudMetadata(
            provider="aws",
            reachable=False,
            error=f"AWS IMDSv2 is not reachable: {type(exc).__name__}",
        )