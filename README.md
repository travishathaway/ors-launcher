# ors-launcher

A CLI for installing, configuring, and running a local [OpenRouteService](https://openrouteservice.org/)
(ORS) instance from a plain `ors.jar`.

This replaces the old `setup-ors.sh` bash script. It no longer downloads OSM data (you always point
it at an existing `.osm.pbf` file) and no longer auto-installs Java or downloads the ORS jar itself —
both are assumed to already be provided by the surrounding environment (e.g. bundled via a conda
package).

## Commands

### `ors-launcher init`

Sets up the install directory (`graphs/`, `elevation_cache/`, `logs/`, `config/`) and writes a
default `config/ors-config.yml` if one doesn't already exist.

```bash
ors-launcher init --osm-file /path/to/germany-latest.osm.pbf [--install-dir DIR] [--port 8080]
```

Fails with a clear error if:
- `--osm-file` doesn't exist
- the ORS jar isn't found at `<install-dir>/ors.jar`

Running `init` again when a config already exists leaves it untouched.

### `ors-launcher start`

Starts the ORS server. If no config exists yet, it creates a default one first (same behavior as
`init`), then validates the config and launches `java -jar ors.jar` in the foreground.

```bash
ors-launcher start [--osm-file /path/to/file.osm.pbf] [--install-dir DIR] [--port 8080]
```

`--osm-file` is only required here if no config exists yet and one needs to be created.

## Configuration

`config/ors-config.yml` is validated against a Pydantic schema covering the fields this tool
manages (server port, elevation settings, the default profile's source OSM file, per-profile
`enabled` flags, and log level). Any other upstream ORS keys you hand-edit into the file are
preserved as-is (not validated, not discarded) when the tool re-reads or re-writes the file.

The file also has one section that is **not** part of ORS's own configuration schema: `launcher`,
holding `java_xms`/`java_xmx` JVM heap sizes used by `start` to launch the server. ORS itself
ignores this section.

## Install

```bash
pip install -e .

# for development (adds pytest, see [dependency-groups].dev in pyproject.toml)
uv sync --group dev
```
