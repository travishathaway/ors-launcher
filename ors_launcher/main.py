import os
import shutil
import subprocess
import sys
from pathlib import Path

import click
from pydantic import ValidationError
from rich.console import Console
from rich.text import Text

from .config import (
    build_default_config,
    dump_config,
    load_config,
    render_validation_error,
)
from .constants import (
    CONFIG_DIR_NAME,
    CONFIG_FILE_NAME,
    ELEVATION_CACHE_DIR_NAME,
    GRAPHS_DIR_NAME,
    LOGS_DIR_NAME,
)

console = Console()
error_console = Console(stderr=True)


def _default_install_dir() -> Path:
    return Path.cwd()


def _install_dirs(install_dir: Path) -> dict[str, Path]:
    return {
        "graphs": install_dir / GRAPHS_DIR_NAME,
        "elevation_cache": install_dir / ELEVATION_CACHE_DIR_NAME,
        "logs": install_dir / LOGS_DIR_NAME,
        "config": install_dir / CONFIG_DIR_NAME,
    }


def _config_path(install_dir: Path) -> Path:
    return install_dir / CONFIG_DIR_NAME / CONFIG_FILE_NAME


def _ensure_default_config(install_dir: Path, osm_file: Path | None, port: int) -> Path:
    """Create the installation directory layout and a default config if one
    doesn't exist yet.

    Shared by `init` and `start` so their default-creation behavior can't drift apart.
    """
    install_dir = install_dir.resolve()
    if osm_file is not None:
        osm_file = osm_file.resolve()
    dirs = _install_dirs(install_dir)
    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)

    config_path = _config_path(install_dir)
    if config_path.exists():
        return config_path

    if osm_file is None:
        error_console.print(
            "[bold red]Error:[/bold red] no config exists yet at"
            f" [cyan]{config_path}[/cyan] "
            "and no --osm-file was given to create one."
        )
        raise SystemExit(1)

    config = build_default_config(
        osm_file=osm_file,
        port=port,
        log_dir=dirs["logs"],
        elevation_cache_dir=dirs["elevation_cache"],
    )
    dump_config(config, config_path)
    return config_path


def _get_ors_exe_name():
    """Return the name of the executable to use."""
    if sys.platform == "win32":
        return "ors.bat"
    return "ors"


def _exe_exists(name):
    """Verify exe exists and exit if not"""
    if not shutil.which(name):
        error_console.print('[bold red]Command "ors" not available.[/bold red]')
        raise SystemExit(1)


@click.group()
def cli() -> None:
    """Manage a local OpenRouteService (ORS) instance."""


@cli.command()
@click.option(
    "--osm-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to an existing .osm.pbf file to route on.",
)
@click.option(
    "--install-dir",
    default=None,
    type=click.Path(file_okay=False, path_type=Path),
    help="Install directory (default: current directory)",
)
@click.option("--port", default=8080, show_default=True, help="Port ORS listens on.")
def init(osm_file: Path, install_dir: Path | None, port: int) -> None:
    """Set up the installation directory and a default ors-config.yml if one
    doesn't exist."""
    install_dir = (install_dir or _default_install_dir()).resolve()
    osm_file = osm_file.resolve()
    dirs = _install_dirs(install_dir)
    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)

    name = _get_ors_exe_name()
    _exe_exists(name)

    config_path = _config_path(install_dir)
    if config_path.exists():
        console.print(
            f"[yellow]Config already exists[/yellow] at {config_path} -- "
            " leaving it untouched."
        )
        return

    config = build_default_config(
        osm_file=osm_file,
        port=port,
        log_dir=dirs["logs"],
        elevation_cache_dir=dirs["elevation_cache"],
    )
    dump_config(config, config_path)
    console.print(f"[green]Config written[/green] to {config_path}")


@cli.command()
@click.option(
    "--osm-file",
    default=None,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to an existing .osm.pbf file; only used if a default config needs to"
    " be created.",
)
@click.option(
    "--install-dir",
    default=None,
    type=click.Path(file_okay=False, path_type=Path),
    help="Install directory (default: current directory).",
)
@click.option(
    "--port",
    default=8080,
    show_default=True,
    help="Port ORS listens on (only used if a default config needs to be created).",
)
def start(osm_file: Path | None, install_dir: Path | None, port: int) -> None:
    """Start the ORS server, creating a default config first if none exists."""
    install_dir = install_dir or _default_install_dir()
    config_path = _ensure_default_config(install_dir, osm_file, port)

    name = _get_ors_exe_name()
    _exe_exists(name)

    try:
        config = load_config(config_path)
    except ValidationError as exc:
        error_console.print("[bold red]Invalid configuration:[/bold red]")
        error_console.print(render_validation_error(exc))
        raise SystemExit(1) from exc

    log_path = Path(config.logging.file.name)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    java_cmd = [
        name,
        "-Djava.awt.headless=true",
        "-server",
        f"-Xms{config.launcher.java_xms}",
        f"-Xmx{config.launcher.java_xmx}",
        "-XX:+UseG1GC",
    ]

    console.print(f"Starting OpenRouteService on port {config.server.port}...")
    console.print(f"Config: {config_path}")
    console.print(f"Logs:   {log_path}")
    console.print(f"Health check: http://localhost:{config.server.port}/ors/v2/health")

    env = {**os.environ, "ORS_CONFIG_LOCATION": str(config_path.resolve())}

    with log_path.open("a") as log_file:
        process = subprocess.Popen(
            java_cmd,
            cwd=install_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert process.stdout is not None
        for line in process.stdout:
            text = Text.from_ansi(line)
            console.print(text, end="")
            log_file.write(text.plain)
        returncode = process.wait()

    if returncode != 0:
        sys.exit(returncode)
