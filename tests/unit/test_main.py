from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from ors_launcher.main import (
    _config_path,
    _default_install_dir,
    _exe_exists,
    _get_ors_exe_name,
    _install_dirs,
    cli,
)


def test_default_install_dir():
    assert _default_install_dir() == Path.cwd()


def test_install_dirs(tmp_path):
    dirs = _install_dirs(tmp_path)
    assert dirs["graphs"] == tmp_path / "graphs"
    assert dirs["elevation_cache"] == tmp_path / "elevation_cache"
    assert dirs["logs"] == tmp_path / "logs"
    assert dirs["config"] == tmp_path / "config"


def test_config_path(tmp_path):
    assert _config_path(tmp_path) == tmp_path / "config" / "ors-config.yml"


def test_get_ors_exe_name_unix():
    with patch("sys.platform", "linux"):
        assert _get_ors_exe_name() == "ors"


def test_get_ors_exe_name_windows():
    with patch("sys.platform", "win32"):
        assert _get_ors_exe_name() == "ors.bat"


def test_exe_exists_raises_when_missing():
    with patch("ors_launcher.main.shutil.which", return_value=None):
        with pytest.raises(SystemExit):
            _exe_exists("ors")


def test_init_creates_directory_layout_and_config(tmp_path):
    runner = CliRunner()
    osm = tmp_path / "region.osm.pbf"
    osm.touch()
    install_dir = tmp_path / "ors"

    with patch("ors_launcher.main._exe_exists"):
        result = runner.invoke(
            cli,
            [
                "init",
                "--osm-file",
                str(osm),
                "--install-dir",
                str(install_dir),
            ],
        )

    assert result.exit_code == 0
    assert (install_dir / "config" / "ors-config.yml").exists()
    for subdir in ("graphs", "elevation_cache", "logs", "config"):
        assert (install_dir / subdir).is_dir()


def test_init_skips_when_config_exists(tmp_path):
    runner = CliRunner()
    osm = tmp_path / "region.osm.pbf"
    osm.touch()
    install_dir = tmp_path / "ors"

    with patch("ors_launcher.main._exe_exists"):
        runner.invoke(
            cli,
            [
                "init",
                "--osm-file",
                str(osm),
                "--install-dir",
                str(install_dir),
            ],
        )
        result = runner.invoke(
            cli,
            [
                "init",
                "--osm-file",
                str(osm),
                "--install-dir",
                str(install_dir),
            ],
        )

    assert result.exit_code == 0
    assert "already exists" in result.output


def test_start_launches_server_with_existing_config(tmp_path):
    runner = CliRunner()
    osm = tmp_path / "region.osm.pbf"
    osm.touch()
    install_dir = tmp_path / "ors"

    with patch("ors_launcher.main._exe_exists"):
        runner.invoke(
            cli,
            [
                "init",
                "--osm-file",
                str(osm),
                "--install-dir",
                str(install_dir),
            ],
        )

    mock_process = MagicMock()
    mock_process.stdout = iter(["Starting ORS...\n"])
    mock_process.wait.return_value = 0

    with (
        patch("ors_launcher.main._exe_exists"),
        patch("ors_launcher.main.subprocess.Popen", return_value=mock_process),
    ):
        result = runner.invoke(
            cli,
            [
                "start",
                "--install-dir",
                str(install_dir),
            ],
        )

    assert result.exit_code == 0


def test_start_creates_config_when_missing(tmp_path):
    runner = CliRunner()
    osm = tmp_path / "region.osm.pbf"
    osm.touch()
    install_dir = tmp_path / "ors"

    mock_process = MagicMock()
    mock_process.stdout = iter([])
    mock_process.wait.return_value = 0

    with (
        patch("ors_launcher.main._exe_exists"),
        patch("ors_launcher.main.subprocess.Popen", return_value=mock_process),
    ):
        result = runner.invoke(
            cli,
            [
                "start",
                "--osm-file",
                str(osm),
                "--install-dir",
                str(install_dir),
            ],
        )

    assert result.exit_code == 0
    assert (install_dir / "config" / "ors-config.yml").exists()


def test_start_fails_without_osm_file_and_no_config(tmp_path):
    runner = CliRunner()
    install_dir = tmp_path / "ors"

    with patch("ors_launcher.main._exe_exists"):
        result = runner.invoke(
            cli,
            [
                "start",
                "--install-dir",
                str(install_dir),
            ],
        )

    assert result.exit_code == 1


def test_start_exits_on_invalid_config(tmp_path):
    runner = CliRunner()
    osm = tmp_path / "region.osm.pbf"
    osm.touch()
    install_dir = tmp_path / "ors"

    with patch("ors_launcher.main._exe_exists"):
        runner.invoke(
            cli,
            [
                "init",
                "--osm-file",
                str(osm),
                "--install-dir",
                str(install_dir),
            ],
        )

    # Overwrite the config with an invalid value to trigger a ValidationError
    config_path = install_dir / "config" / "ors-config.yml"
    config_path.write_text(
        config_path.read_text().replace("data_access: MMAP", "data_access: BOGUS")
    )

    with patch("ors_launcher.main._exe_exists"):
        result = runner.invoke(cli, ["start", "--install-dir", str(install_dir)])

    assert result.exit_code == 1
    assert "data_access" in result.stderr


def test_start_propagates_nonzero_exit_code(tmp_path):
    runner = CliRunner()
    osm = tmp_path / "region.osm.pbf"
    osm.touch()
    install_dir = tmp_path / "ors"

    with patch("ors_launcher.main._exe_exists"):
        runner.invoke(
            cli,
            [
                "init",
                "--osm-file",
                str(osm),
                "--install-dir",
                str(install_dir),
            ],
        )

    mock_process = MagicMock()
    mock_process.stdout = iter([])
    mock_process.wait.return_value = 2

    with (
        patch("ors_launcher.main._exe_exists"),
        patch("ors_launcher.main.subprocess.Popen", return_value=mock_process),
    ):
        result = runner.invoke(
            cli,
            [
                "start",
                "--install-dir",
                str(install_dir),
            ],
        )

    assert result.exit_code == 2
