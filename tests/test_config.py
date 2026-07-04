import pytest
from pydantic import ValidationError

from ors_launcher.config import (
    OrsLauncherConfig,
    build_default_config,
    dump_config,
    load_config,
)


def test_minimal_valid_config_parses():
    config = OrsLauncherConfig.model_validate(
        {
            "ors": {
                "engine": {
                    "profile_default": {"build": {"source_file": "germany.osm.pbf"}},
                    "profiles": {"driving-car": {"enabled": True}},
                }
            }
        }
    )

    assert config.server.port == 8080
    assert config.ors.engine.elevation.data_access == "MMAP"
    assert config.ors.engine.profiles["driving-car"].enabled is True


def test_unknown_keys_round_trip(tmp_path):
    config = OrsLauncherConfig.model_validate(
        {
            "ors": {
                "engine": {
                    "profile_default": {"build": {"source_file": "germany.osm.pbf"}},
                    "profiles": {
                        "driving-car": {
                            "enabled": True,
                            "build": {
                                "source_file": "germany.osm.pbf",
                                "encoder_options": {"turn_costs": True},
                            },
                        }
                    },
                },
                "endpoints": {"routing": {"enabled": True}},
            }
        }
    )

    path = tmp_path / "ors-config.yml"
    dump_config(config, path)
    reloaded = load_config(path)

    assert reloaded.ors.model_extra["endpoints"]["routing"]["enabled"] is True
    assert (
        reloaded.ors.engine.profiles["driving-car"].build.model_extra["encoder_options"]["turn_costs"]
        is True
    )


def test_invalid_elevation_data_access_raises():
    with pytest.raises(ValidationError, match="data_access"):
        OrsLauncherConfig.model_validate(
            {
                "ors": {
                    "engine": {
                        "elevation": {"data_access": "BOGUS"},
                        "profile_default": {"build": {"source_file": "germany.osm.pbf"}},
                        "profiles": {"driving-car": {"enabled": True}},
                    }
                }
            }
        )


def test_missing_source_file_raises():
    with pytest.raises(ValidationError, match="source_file"):
        OrsLauncherConfig.model_validate(
            {
                "ors": {
                    "engine": {
                        "profile_default": {"build": {}},
                        "profiles": {"driving-car": {"enabled": True}},
                    }
                }
            }
        )


def test_heap_settings_round_trip(tmp_path):
    config = build_default_config(
        osm_file=tmp_path / "germany.osm.pbf",
        port=8080,
        log_dir=tmp_path / "logs",
        elevation_cache_dir=tmp_path / "elevation_cache",
    )
    config.launcher.java_xms = "4g"
    config.launcher.java_xmx = "16g"

    path = tmp_path / "ors-config.yml"
    dump_config(config, path)
    reloaded = load_config(path)

    assert reloaded.launcher.java_xms == "4g"
    assert reloaded.launcher.java_xmx == "16g"
