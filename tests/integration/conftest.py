import json
import os
import signal
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest

from ors_launcher.config import dump_config, load_config

MONACO_OSM = Path(__file__).parent.parent / "data" / "monaco.osm.pbf"
READY_POLL_INTERVAL = 5  # seconds
READY_TIMEOUT = 600  # 10 minutes


@pytest.fixture(scope="session")
def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def ors_server(tmp_path_factory, free_port):
    install_dir = tmp_path_factory.mktemp("ors-integration")

    # Create directory layout and default config via the CLI
    subprocess.run(
        [
            "ors-launcher",
            "init",
            "--osm-file",
            str(MONACO_OSM),
            "--install-dir",
            str(install_dir),
            "--port",
            str(free_port),
        ],
        check=True,
    )

    # Tune the generated config for fast test startup: small heap, one profile
    config_path = install_dir / "config" / "ors-config.yml"
    config = load_config(config_path)
    config.launcher.java_xms = "256m"
    config.launcher.java_xmx = "512m"
    for name in list(config.ors.engine.profiles.keys()):
        config.ors.engine.profiles[name].enabled = name == "foot-walking"
    dump_config(config, config_path)

    # Launch the server via the CLI. start_new_session puts ors-launcher and its
    # Java child into their own process group so we can kill both at teardown.
    process = subprocess.Popen(
        ["ors-launcher", "start", "--install-dir", str(install_dir)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    base_url = f"http://localhost:{free_port}"
    health_url = f"{base_url}/ors/v2/health"
    deadline = time.monotonic() + READY_TIMEOUT
    ready = False

    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"ors-launcher start exited early with code {process.returncode}"
            )
        try:
            with urllib.request.urlopen(health_url, timeout=5) as resp:
                data = json.loads(resp.read())
                if data.get("status") == "ready":
                    ready = True
                    break
        except Exception:
            pass
        time.sleep(READY_POLL_INTERVAL)

    if not ready:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        raise RuntimeError(f"ORS server did not become ready within {READY_TIMEOUT}s")

    yield base_url

    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait(timeout=15)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
