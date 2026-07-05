"""Integration tests against a live ORS instance built from the Monaco dataset."""

import pytest

from .check_server import (
    get_directions,
    get_health,
    get_isochrones,
    get_matrix,
    get_status,
)

# Well-known Monaco landmarks as [longitude, latitude]
CASINO_MONTE_CARLO = [7.4269, 43.7393]
MONACO_VILLE = [7.4246, 43.7326]
PORT_HERCULE = [7.4268, 43.7360]

PROFILE = "foot-walking"


@pytest.mark.integration
def test_health(ors_server):
    data = get_health(ors_server)
    assert data["status"] == "ready"


@pytest.mark.integration
def test_status_has_profiles(ors_server):
    data = get_status(ors_server)
    profiles = data["profiles"]
    assert len(profiles) > 0
    assert "foot-walking" in profiles


@pytest.mark.integration
def test_directions_foot_walking(ors_server):
    data = get_directions(ors_server, PROFILE, CASINO_MONTE_CARLO, MONACO_VILLE)
    routes = data["routes"]
    assert len(routes) > 0
    summary = routes[0]["summary"]
    assert summary["distance"] > 0
    assert summary["duration"] > 0


@pytest.mark.integration
def test_isochrones(ors_server):
    data = get_isochrones(ors_server, PROFILE, PORT_HERCULE, [600, 1200])
    features = data["features"]
    assert len(features) == 2
    for feature in features:
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Polygon"
        assert feature["properties"]["value"] in (600, 1200)


@pytest.mark.integration
def test_matrix(ors_server):
    n = 3
    data = get_matrix(
        ors_server, PROFILE, [CASINO_MONTE_CARLO, MONACO_VILLE, PORT_HERCULE]
    )
    durations = data["durations"]
    distances = data["distances"]
    assert len(durations) == n
    assert all(len(row) == n for row in durations)
    assert len(distances) == n
    assert all(len(row) == n for row in distances)
    # Travel from a point to itself is always zero
    for i in range(n):
        assert durations[i][i] == 0
        assert distances[i][i] == 0
