## ADDED Requirements

### Requirement: Pydantic models represent the managed config subset
The system SHALL provide Pydantic models covering exactly: `server.port`; `ors.engine.elevation.preprocessed`/`data_access`/`cache_path`/`cache_clear`/`provider`; `ors.engine.profile_default.build.source_file`/`elevation`; `ors.engine.profiles.<name>.enabled` and an optional per-profile `build.source_file` override; `logging.file.name` and `logging.level.root`. Fields not in this list SHALL NOT be required by the schema.

#### Scenario: Minimal valid config parses successfully
- **WHEN** a config file sets only `ors.engine.profile_default.build.source_file` and `ors.engine.profiles.driving-car.enabled: true`
- **THEN** the model validates successfully, filling in documented defaults for every other modeled field

### Requirement: Unmodeled upstream keys pass through unchanged
Every model in the schema SHALL allow extra fields (`extra="allow"`) so that upstream ORS keys not covered by this schema (e.g. `ext_storages`, `encoder_options`, `preparation`, `ors.endpoints.*`, `ors.cors`) are preserved when a config file is loaded and re-serialized, rather than being rejected or silently dropped.

#### Scenario: Hand-edited advanced key is preserved
- **WHEN** a user manually adds `ors.engine.profiles.driving-car.build.encoder_options.turn_costs: true` to an existing config file
- **THEN** loading and re-saving that config file through the schema preserves the `encoder_options` block unchanged

#### Scenario: Unknown top-level section does not fail validation
- **WHEN** a config file includes an `ors.endpoints` section not covered by the modeled schema
- **THEN** the config loads successfully and the `ors.endpoints` content is retained on save

### Requirement: Validation errors are field-specific and human-readable
When a modeled field fails validation (wrong type, invalid enum value, missing required field), the system SHALL surface the exact field path and the reason, formatted for terminal display, rather than allowing the raw exception to propagate unformatted.

#### Scenario: Invalid elevation data_access value
- **WHEN** a config file sets `ors.engine.elevation.data_access: BOGUS` (not `MMAP` or `RAM_STORE`)
- **THEN** the system reports a validation error naming the field `ors.engine.elevation.data_access` and the allowed values, before any attempt to launch ORS

#### Scenario: Missing required source_file
- **WHEN** a config file omits `ors.engine.profile_default.build.source_file` entirely
- **THEN** the system reports a validation error naming the missing field rather than letting ORS fail later during graph build

### Requirement: JVM heap settings are modeled as a non-upstream extension
The schema SHALL include a launcher-specific section (e.g. `launcher.java_xms` / `launcher.java_xmx`) for JVM heap sizing that is not part of the upstream ORS schema, clearly distinguished (e.g. via a dedicated top-level key and generated-file comments) from the modeled upstream ORS fields.

#### Scenario: Heap settings round-trip
- **WHEN** a config file sets `launcher.java_xms: 2g` and `launcher.java_xmx: 12g`
- **THEN** the schema validates these values and they are available to the launch process, while remaining absent from what would be passed to ORS as its own configuration content
