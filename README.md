# ors-launcher

A CLI for configuring and running a local [OpenRouteService](https://openrouteservice.org/)
(ORS) instance.

## Install

You can install ors-launcher from using the `gis-forge` channel:

```bash
# With conda
conda create -n ors -c gis-forge openrouteservice

# With pixi
pixi workspace channel add gis-forge
pixi add gis-forge::openrouteservice
```

## Usage

If you want to first create an `ors-config.yml` file to customize it, use this workflow:

```bash
# Initialize a project
orsl init --osm-file region.osm.pbf --install-dir ./ors

# Edit ors/config/ors-config.yml to your liking...

# Start the server
orsl start --install-dir ./ors
```

If you just want to start an openrouteservice server immediately with defaults, use:

```bash
# Initializes project and starts server immediately
orsl start --install-dir ./ors --osm-file region.osm.pbf
```

## Commands

### `ors-launcher init`

Set up the installation directory (`graphs/`, `elevation_cache/`, `logs/`, `config/`) and write a
default `config/ors-config.yml` if one doesn't already exist.

```bash
ors-launcher init --osm-file /path/to/region.osm.pbf [--install-dir DIR] [--port 8080]
```

Fails with a clear error if:
- `--osm-file` doesn't exist

Running `init` again when a config already exists leaves it untouched.

### `ors-launcher start`

Start the ORS server. If no config exists yet, it creates a default one first (same behavior as
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

## Contributing

Contributions are welcome. Here are a few ways to get involved:

- **Bug reports & feature requests** — open an issue on GitHub describing the problem or idea.
  Include your OS, Python version, and the exact command and error output if reporting a bug.
- **Documentation** — improvements to this README or inline docstrings are always appreciated.
- **Code** — fork the repo, make your changes on a branch, and open a pull request. Please keep
  pull requests focused on a single fix or feature so they are easy to review.

### Development setup

This project uses [pixi](https://pixi.sh) to manage dependencies and environments.

```bash
# Clone the repo
git clone https://github.com/your-org/ors-launcher.git
cd ors-launcher

# Install pixi (if you don't have it)
curl -fsSL https://pixi.sh/install.sh | sh

# Install all dependencies (including dev tools like pytest)
pixi install -e dev

# Run the unit tests
pixi run -e dev test

# Run the integration tests (requires a working `ors` executable on PATH;
# downloads and builds graphs from the bundled Monaco dataset — takes a few minutes)
pixi run -e dev test-integration
```

