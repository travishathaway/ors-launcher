"""HTTP helpers and request functions for ORS integration tests."""

import json
import urllib.error
import urllib.request


def _get(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace").strip()
        raise RuntimeError(f"HTTP {exc.code} {exc.reason}\n{body}") from None


def _post(url: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace").strip()
        raise RuntimeError(f"HTTP {exc.code} {exc.reason}\n{body}") from None


def get_health(base: str) -> dict:
    return _get(f"{base}/ors/v2/health")


def get_status(base: str) -> dict:
    return _get(f"{base}/ors/v2/status")


def get_directions(base: str, profile: str, start: list, end: list) -> dict:
    return _post(
        f"{base}/ors/v2/directions/{profile}/json",
        {"coordinates": [start, end]},
    )


def get_isochrones(
    base: str, profile: str, location: list, ranges: list, range_type: str = "time"
) -> dict:
    return _post(
        f"{base}/ors/v2/isochrones/{profile}",
        {"locations": [location], "range": ranges, "range_type": range_type},
    )


def get_matrix(
    base: str, profile: str, locations: list, metrics: list | None = None
) -> dict:
    return _post(
        f"{base}/ors/v2/matrix/{profile}/json",
        {"locations": locations, "metrics": metrics or ["distance", "duration"]},
    )
