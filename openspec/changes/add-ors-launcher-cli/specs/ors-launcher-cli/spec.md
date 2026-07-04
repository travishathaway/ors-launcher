## ADDED Requirements

### Requirement: init command sets up the install directory and default config
`ors-launcher init` SHALL accept `--osm-file` (path to an existing `.osm.pbf`, required), `--install-dir`, and `--port`, and SHALL create the install directory layout (`graphs/`, `elevation_cache/`, `logs/`, `config/`) if it does not already exist.

#### Scenario: First-time init creates directories and config
- **WHEN** `ors-launcher init --osm-file /data/germany-latest.osm.pbf` is run against an install directory that doesn't exist yet
- **THEN** the directory structure is created and `config/ors-config.yml` is written, referencing the given OSM file path as `ors.engine.profile_default.build.source_file`

#### Scenario: init does not overwrite an existing config by default
- **WHEN** `ors-launcher init` is run and `config/ors-config.yml` already exists
- **THEN** the existing config file is left unchanged and the command reports that a config already exists, without erroring

### Requirement: init never downloads OSM data
`ors-launcher init` SHALL NOT perform any network download of OSM data. The OSM file path SHALL always come from the caller via `--osm-file`, and the command SHALL fail with a clear error if that path does not exist on disk.

#### Scenario: Missing OSM file is rejected before any other work
- **WHEN** `ors-launcher init --osm-file /nonexistent/file.pbf` is run
- **THEN** the command fails immediately with an error naming the missing path, without creating directories or writing a config file

### Requirement: init verifies the ORS jar is present rather than downloading it
`ors-launcher init` SHALL check for the presence of the ORS jar at its expected location and SHALL NOT attempt to download it. If the jar is missing, the command SHALL fail with an error naming the expected path.

#### Scenario: Jar missing at expected location
- **WHEN** `ors-launcher init` is run and no jar is found at the expected/configured path
- **THEN** the command fails with a clear error stating the expected jar path, and does not attempt any network request

### Requirement: init never installs or checks Java version
`ors-launcher init` SHALL NOT invoke any system package manager (e.g. `apt-get`) and SHALL NOT perform Java version detection or installation, since Java is assumed to be provided by the surrounding (conda) environment.

#### Scenario: init runs without touching system packages
- **WHEN** `ors-launcher init` is run
- **THEN** no subprocess invoking a system package manager is executed at any point

### Requirement: start creates a default config if none exists
`ors-launcher start` SHALL, if no config file exists at the expected location, perform the same default-config-creation behavior as `init` before proceeding, using whatever `--osm-file`/`--install-dir`/`--port` options were passed to `start`.

#### Scenario: start on a fresh install directory
- **WHEN** `ors-launcher start --osm-file /data/germany-latest.osm.pbf` is run against an install directory with no existing config
- **THEN** a default config is created first (identical in content to what `init` would produce), and the server then launches using that config

#### Scenario: start reuses an existing config without modification
- **WHEN** `ors-launcher start` is run and a config file already exists
- **THEN** the existing config file is loaded and validated as-is; no new default config is written

### Requirement: start validates config before launching the server
`ors-launcher start` SHALL load and validate the config file through the Pydantic schema before launching any `java` process. If validation fails, the command SHALL report the formatted validation error and SHALL NOT launch `java`.

#### Scenario: Invalid config blocks server launch
- **WHEN** `ors-launcher start` is run against a config file with an invalid field value
- **THEN** the command reports the validation error and exits without starting the `java` process

### Requirement: start launches the ORS server directly, without generating a shell script
`ors-launcher start` SHALL launch `java -jar <jar>` directly as a subprocess of the CLI process (foreground, streaming output, tee'd to the configured log file), using the JVM heap settings from the config. It SHALL NOT generate a separate shell script as an intermediate step.

#### Scenario: start launches the JVM directly
- **WHEN** `ors-launcher start` is run against a valid config
- **THEN** a `java` process is spawned directly by the CLI with the configured heap flags and `-jar` pointing at the verified jar path, and no `start-ors.sh`-equivalent file is written to disk
