## 1. Package scaffolding

- [x] 1.1 Create `ors-launcher/` directory at repo root with `pyproject.toml` (own package name, `click`/`rich`/`pydantic`/YAML deps, console-script entry point `ors-launcher`)
- [x] 1.2 Add `ors-launcher/README.md` describing the tool and its `init`/`start` commands
- [x] 1.3 Add `ors-launcher/.gitignore` for Python build artifacts (or confirm root `.gitignore` already covers it)
- [x] 1.4 Create source package layout (`ors_launcher/__init__.py`, `main.py`, `config.py`, `constants.py`) and a `tests/` directory
- [x] 1.5 Confirm `ors-launcher/` is NOT added to the root `pixi.toml` `[workspace]` members

## 2. Config schema (Pydantic)

- [x] 2.1 Define `ElevationConfig` model (`preprocessed`, `data_access` [`MMAP`/`RAM_STORE`], `cache_path`, `cache_clear`, `provider` [`multi`/`cgiar`/`srtm`]), `extra="allow"`
- [x] 2.2 Define `ProfileBuildConfig` model (`source_file`, `elevation`), `extra="allow"`
- [x] 2.3 Define `ProfileConfig` model (`enabled`, optional `build` override), `extra="allow"`
- [x] 2.4 Define `ProfileDefaultConfig`, `EngineConfig` (`elevation`, `profile_default`, `profiles: dict[str, ProfileConfig]`), `extra="allow"`
- [x] 2.5 Define `ServerConfig` (`port`), `LoggingConfig` (`file.name`, `level.root`), `extra="allow"`
- [x] 2.6 Define `LauncherConfig` (non-upstream extension: `java_xms`, `java_xmx`)
- [x] 2.7 Define top-level `OrsLauncherConfig` combining `server`, `ors.engine`, `logging`, `launcher`, `extra="allow"` at every level
- [x] 2.8 Implement YAML load: parse file into the model, catch `pydantic.ValidationError`
- [x] 2.9 Implement YAML dump: serialize the model back to YAML preserving passthrough (`extra="allow"`) fields
- [x] 2.10 Implement a rich-formatted validation error renderer (field path + reason per error, not a raw traceback)
- [x] 2.11 Implement default-config construction (given `osm_file`, `install_dir`, `port` inputs, produce a valid `OrsLauncherConfig` matching what the bash script generated for `driving-car`, minus the removed OSM-download concern)
- [x] 2.12 Unit tests: minimal valid config parses; unknown/advanced keys round-trip through load+dump unchanged; invalid enum value produces a field-specific error; missing `source_file` produces a field-specific error; heap settings round-trip

## 3. CLI: init command

- [x] 3.1 Add `init` command: `--osm-file` (required, must exist), `--install-dir`, `--port`
- [x] 3.2 Validate `--osm-file` exists before any other work; fail with clear error naming the path if not
- [x] 3.3 Create install dir layout (`graphs/`, `elevation_cache/`, `logs/`, `config/`) if missing
- [x] 3.4 Verify ORS jar exists at its expected/configured location; fail with a clear error naming the expected path if missing (no download)
- [x] 3.5 If `config/ors-config.yml` already exists, leave it untouched and report that instead of erroring
- [x] 3.6 If it doesn't exist, build the default config (via 2.11) and write it
- [x] 3.7 Confirm no code path invokes a system package manager or performs Java version detection

## 4. CLI: start command

- [x] 4.1 Add `start` command: `--osm-file`, `--install-dir`, `--port` (used only if a default config must be created), plus options/env vars needed to build the `java` argv
- [x] 4.2 If no config exists at the expected location, invoke the same default-config-creation path `init` uses (reuse the function from 2.11, not a duplicate implementation)
- [x] 4.3 Load and validate the existing (or just-created) config via the schema; on validation failure, print the formatted error and exit without launching `java`
- [x] 4.4 Build the `java -jar <jar> ...` argv from the validated config (heap flags from `launcher.java_xms`/`java_xmx`, port, etc.)
- [x] 4.5 Launch the process directly via `subprocess` in the foreground, streaming stdout and tee-ing to the configured log file; no intermediate shell script generated
- [x] 4.6 Manual verification: run `init` then `start` against a real (or fixture) OSM file and confirm the JVM launches with the expected flags

## 5. Cleanup

- [x] 5.1 Remove `setup-ors.sh` from the repo root once `ors-launcher` covers its functionality
- [x] 5.2 Update root `README.md`/`NOTES.md` references to `setup-ors.sh`, if any, to point at `ors-launcher`
