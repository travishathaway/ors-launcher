#: Name of the app, used for defaults and messages
APP_NAME = "ors-launcher"

#: Profiles enabled by a freshly generated config (all work from a plain OSM PBF file).
#: The public-transit profile (pt) is excluded because it requires separate GTFS data.
DEFAULT_PROFILES: tuple[str, ...] = (
    "driving-car",
    "cycling-regular",
    "foot-walking",
    "foot-hiking",
    "wheelchair",
)

#: Sub-directory names under the installation directory
GRAPHS_DIR_NAME = "graphs"
ELEVATION_CACHE_DIR_NAME = "elevation_cache"
LOGS_DIR_NAME = "logs"
CONFIG_DIR_NAME = "config"

#: Filenames within the installation directory
CONFIG_FILE_NAME = "ors-config.yml"
LOG_FILE_NAME = "ors.log"
