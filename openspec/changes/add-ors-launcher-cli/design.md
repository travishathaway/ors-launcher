## Context

`setup-ors.sh` (repo root) is the current mechanism for standing up a local OpenRouteService (ORS) instance: it checks for Java, downloads the ORS jar from GitHub releases, downloads an OSM region from Geofabrik, hand-writes `ors-config.yml` via a bash heredoc, and hand-writes a `start-ors.sh` launcher script.

Two things are changing the environment this tool runs in:
- The OSM `.pbf` file will always be supplied manually going forward — no more Geofabrik downloads.
- This tool is going to be packaged and distributed as its own conda package, where Java and the ORS jar arrive as bundled/pre-provided dependencies rather than being fetched by the tool itself.

There is no official JSON Schema or OpenAPI spec for `ors-config.yml` — it's Spring Boot configuration, documented in prose across the openrouteservice docs site. The reference config on the `openrouteservice` GitHub repo's main branch was used as ground truth for this design. Notably, the current upstream shape differs from what `setup-ors.sh` generates today: the script writes a top-level `ors.engine.graphs_root_path`, a key that no longer appears anywhere in the current reference config. Graph storage is now expressed per-profile via `profile_default.build.graph_path` (default `"graphs"`). This design targets the **current/latest** upstream shape, not the older shape the bash script assumed.

## Goals / Non-Goals

**Goals:**
- Replace `setup-ors.sh` with a Python CLI (`ors-launcher`) exposing `init` and `start` commands.
- Validate `ors-config.yml` against a Pydantic schema before ORS ever sees it, turning config typos into precise, field-level errors instead of opaque Spring-Boot startup failures.
- Support hand-edited advanced upstream keys we don't model (round-trip via passthrough) without the tool rejecting the file.
- Ship as a standalone, independently distributable package (`ors-launcher/`), decoupled from `ems_germany_analysis`.

**Non-Goals:**
- Modeling the full upstream ORS config surface (endpoints, cors, messages, ext_storages, encoder_options, preparation methods, etc.). Only the fields the tool itself generates/manages are modeled; everything else passes through untyped.
- Downloading OSM data. The caller always supplies `--osm-file`.
- Auto-installing Java or downloading the ORS jar. Both are assumed present (bundled via conda / provided externally); `init` verifies the jar exists and fails clearly if not.
- Publishing the conda package itself (packaging/distribution mechanics are out of scope for this change; only the Python package structure that would support it is in scope).

## Decisions

### 1. Standalone package, not a root pixi workspace member
`ors-launcher/` gets its own `pyproject.toml` and is *not* added as a member of the root `pixi.toml` `[workspace]`. This matches the stated goal of eventually shipping it as its own conda-forge package, independent of `ems_germany_analysis`'s dependency set (postgres, quarto, etc. are irrelevant to a JVM-launcher tool). Trade-off: two independent dependency resolutions/lockfiles to maintain instead of one, but that's the correct shape for a package meant to be distributed separately.

### 2. Narrow Pydantic schema with `extra="allow"` passthrough
Model only: `server.port`, `ors.engine.elevation.*`, `ors.engine.profile_default.build.source_file`/`elevation`, `ors.engine.profiles.<name>.enabled` (+ optional per-profile `build.source_file` override), `logging.level`/`logging.file.name`. Every model sets `model_config = ConfigDict(extra="allow")`.

Alternative considered: model the entire upstream schema (endpoints, cors, ext_storages, encoder_options, preparation/CH/LM tuning, etc.) for maximum validation coverage. Rejected for this change — that surface is large, changes across ORS versions, and the tool has no need to *generate* those fields; a hand-editing user gets passthrough instead of rejection, which is enough for the "readable errors" goal without taking on a large schema-maintenance burden.

### 3. One extra, non-upstream config key for JVM heap sizing
JVM heap (`-Xms`/`-Xmx`) isn't part of ORS's own config schema — it's a `java` launch flag. Per the decision to bake launcher-level settings into the config file (rather than requiring flags on every `start` invocation), the tool's config file includes a small additional top-level section (e.g. `launcher.java_xms` / `launcher.java_xmx`) that ORS itself ignores but `start` reads to build the `java` command line. This makes our config file a strict superset of the real upstream file — documented clearly so it isn't mistaken for an upstream key when cross-referencing ORS docs.

### 4. `start` launches `java` directly via `subprocess`, no generated shell script
The bash script's `start-ors.sh` heredoc-generation step is dropped. `start` builds the `java -jar ...` argv itself and runs it in the foreground (`subprocess.run` / `Popen` with streamed stdout), tee-ing to the configured log file. This removes an intermediate artifact and matches "proper CLI tool" — the launch logic lives in versioned Python, not in a string template.

### 5. `init`'s default-config creation logic is shared with `start`
`start` must create a default config if none exists (per requirement). Rather than duplicating "write default config" logic in both commands, it lives in one internal function that both `init` and `start` call; `init` is the explicit, discoverable entry point, `start` calls the same function as a fallback so behavior can't drift between the two commands.

### 6. Jar presence verification, not download
`init` checks for the jar at an expected path (e.g. an `--ors-jar` option or a conventional location under the install dir) and raises a clear `rich`-formatted error naming the expected path if it's missing, rather than attempting any network fetch.

## Risks / Trade-offs

- **[Risk]** Upstream ORS changes its config schema again (as it already has, dropping `graphs_root_path`) → **Mitigation**: the narrow-scope + `extra="allow"` design means only the small modeled subset can go stale; passthrough keys are unaffected either way, and the modeled subset is small enough to update quickly if it drifts.
- **[Risk]** No official schema to validate against means the Pydantic model could still be subtly wrong (a field this design assumes is optional might actually be required by a specific ORS version, or vice versa) → **Mitigation**: the model was built from the actual reference `ors-config.yml` on the `openrouteservice` main branch plus its docs pages, cross-checked field by field; this is now the design's ground truth of record if a mismatch needs debugging later.
- **[Risk]** Removing Java/jar auto-provisioning breaks the tool if used outside the conda-packaged context it now assumes → **Mitigation**: `init` fails fast with a clear message naming the missing prerequisite (Java on PATH, jar at expected path) rather than failing silently or deep into `start`.
- **[Trade-off]** The config file now contains one key (JVM heap) that isn't part of ORS's own schema. Documented explicitly in the generated file's comments so a reader diffing against upstream docs isn't confused by it.

## Open Questions

- Exact default value/flag name for the jar's expected location (`--ors-jar PATH` vs. a fixed path under the install dir vs. an environment variable) — left to `tasks.md` / implementation to settle against whatever the conda packaging actually produces.
- Default `--install-dir` — whether to keep the bash script's `$HOME/openrouteservice` default or switch to `platformdirs.user_data_dir(...)` (the convention already used elsewhere in this repo's `ems_germany_analysis/report.py`, but this is a separate standalone package so it isn't obligated to match).
