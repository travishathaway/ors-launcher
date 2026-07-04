## Why

`setup-ors.sh` is a 380-line bash script that installs and configures a local OpenRouteService (ORS) instance. It hand-generates `ors-config.yml` via a heredoc (no validation — a typo surfaces as an opaque Spring Boot failure deep into JVM startup), downloads an OSM region from Geofabrik on every run (the OSM file is now always supplied manually), and downloads the ORS jar and auto-installs Java via `apt-get` (both are being moved to bundled conda dependencies instead). A proper Python CLI with a validated config schema replaces this with clearer errors, no redundant downloads, and a package shape (`ors-launcher/`) that can be distributed as its own conda package independent of `ems_germany_analysis`.

## What Changes

- Add a new standalone package `ors-launcher/` (own `pyproject.toml`, not a member of the root `pixi.toml` workspace) with a `click` + `rich` CLI, distinct from the existing `emsde` CLI in `ems_germany_analysis`.
- Add two commands: `ors-launcher init` and `ors-launcher start`.
  - `init` creates the install directory layout (`graphs/`, `elevation_cache/`, `logs/`, `config/`), verifies the ORS jar is present at the expected location (no download — jar is provided externally/bundled), and writes a default `ors-config.yml` if one doesn't already exist, using the `--osm-file` path the caller supplies.
  - `start` loads and validates the existing `ors-config.yml`; if it doesn't exist yet, runs the same default-creation logic `init` uses first. It then launches `java -jar <jar>` directly via `subprocess` in the foreground (heap size flags, log tee'ing) — no longer generates a second `start-ors.sh` shell script as an intermediate artifact.
- **BREAKING (behavior change from the bash script)**: OSM data is never downloaded. The caller must always point `init`/`start` at an existing `.osm.pbf` file via `--osm-file`.
- **BREAKING**: Java is no longer auto-installed via `apt-get`, and the ORS jar is no longer downloaded from GitHub releases. Both are assumed to already be present (Java bundled via conda; jar verified at an expected path, error if missing).
- Add a Pydantic-modeled schema for the subset of `ors-config.yml` this tool manages (`server.port`, `ors.engine.elevation`, `ors.engine.profile_default.build.source_file`/`elevation`, `ors.engine.profiles.<name>.enabled`, `logging.level`), targeting the current upstream ORS config shape (e.g. per-profile `graph_path`, not the older `graphs_root_path` the bash script used). Every model allows extra fields (`extra="allow"`) so hand-added advanced upstream keys (`ext_storages`, `encoder_options`, etc.) round-trip through load/dump without being rejected.
- Add one non-upstream key to our own config file for JVM heap sizing (`java_xms`/`java_xmx` or similar), since heap size is a launch flag, not part of ORS's own schema — read by `start`, ignored by ORS itself.

## Capabilities

### New Capabilities
- `ors-config-schema`: Pydantic models representing the managed subset of `ors-config.yml`, with validation, defaults, YAML load/dump, and passthrough of unmodeled upstream keys.
- `ors-launcher-cli`: The `init`/`start` Click commands — directory setup, jar presence verification, default config creation, config loading with friendly validation errors, and launching the ORS JVM process.

### Modified Capabilities
(none — no existing `openspec/specs/` capabilities exist yet in this repo)

## Impact

- New directory `ors-launcher/` at the repo root: own `pyproject.toml`, `README.md`, source package, tests — independent of `ems_germany_analysis`'s dependencies and not added to the root `pixi.toml` workspace.
- `setup-ors.sh` becomes obsolete and should be removed once the CLI covers its functionality (tracked as a task, not done implicitly).
- New dependencies (in `ors-launcher/pyproject.toml` only): `click`, `rich`, `pydantic`, a YAML library (e.g. `pyyaml` or `ruamel.yaml`).
- No changes to `ems_germany_analysis`, its `emsde` CLI, or the root `pixi.toml`/`pyproject.toml`.
