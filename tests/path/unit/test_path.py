# Copyright (C) 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Module for testing path functionalities."""

import json
import logging
import os
from pathlib import Path
import sys
from unittest.mock import patch

import platformdirs
import pyfakefs  # noqa
import pytest

from ansys.tools.common.path import (
    LOG,
    SETTINGS_DIR,
    change_default_ansys_path,
    change_default_dyna_path,
    change_default_mapdl_path,
    change_default_mechanical_path,
    clear_configuration,
    find_ansys,
    find_dyna,
    find_mapdl,
    find_mechanical,
    get_ansys_path,
    get_available_ansys_installations,
    get_dyna_path,
    get_latest_ansys_installation,
    get_mapdl_path,
    get_mechanical_path,
    save_dyna_path,
    save_mapdl_path,
    save_mechanical_path,
    version_from_path,
)
from ansys.tools.path.path import _is_float

LOG.setLevel(logging.DEBUG)

VERSIONS = [202, 211, 231]
STUDENT_VERSIONS = [201, 211]


def make_path(base, *parts):
    """Make a path from the base and parts."""
    return str(Path(base, *parts))


if sys.platform == "win32":
    ANSYS_BASE_PATH = Path("C:/Program Files/ANSYS Inc")
    STUDENT_DIR = "ANSYS Student"
    BIN_DIR = ["ansys", "bin", "winx64"]

    ANSYS_INSTALLATION_PATHS = [make_path(ANSYS_BASE_PATH, f"v{v}") for v in VERSIONS]
    ANSYS_STUDENT_INSTALLATION_PATHS = [make_path(ANSYS_BASE_PATH, STUDENT_DIR, f"v{v}") for v in STUDENT_VERSIONS]

    MAPDL_INSTALL_PATHS = [make_path(ANSYS_BASE_PATH, f"v{v}", *BIN_DIR, f"ansys{v}.exe") for v in VERSIONS]
    MAPDL_STUDENT_INSTALL_PATHS = [
        make_path(ANSYS_BASE_PATH, STUDENT_DIR, f"v{v}", *BIN_DIR, f"ansys{v}.exe") for v in STUDENT_VERSIONS
    ]

    DYNA_INSTALL_PATHS = [make_path(ANSYS_BASE_PATH, f"v{v}", *BIN_DIR, f"lsdyna{v}.exe") for v in VERSIONS]
    DYNA_STUDENT_INSTALL_PATHS = [
        make_path(ANSYS_BASE_PATH, STUDENT_DIR, f"v{v}", *BIN_DIR, f"lsdyna{v}.exe") for v in STUDENT_VERSIONS
    ]

    MECHANICAL_INSTALL_PATHS = [
        make_path(ANSYS_BASE_PATH, f"v{v}", "aisol", "bin", "winx64", "ansyswbu.exe") for v in VERSIONS
    ]
    MECHANICAL_STUDENT_INSTALL_PATHS = [
        make_path(ANSYS_BASE_PATH, STUDENT_DIR, f"v{v}", "aisol", "bin", "winx64", "ansyswbu.exe")
        for v in STUDENT_VERSIONS
    ]

else:
    ANSYS_BASE_PATH = Path("/ansys_inc")
    STUDENT_DIR = "ANSYS Student"
    BIN_DIR = ["ansys", "bin"]

    ANSYS_INSTALLATION_PATHS = [make_path(ANSYS_BASE_PATH, f"v{v}") for v in VERSIONS]
    ANSYS_STUDENT_INSTALLATION_PATHS = [make_path(ANSYS_BASE_PATH, STUDENT_DIR, f"v{v}") for v in STUDENT_VERSIONS]

    MAPDL_INSTALL_PATHS = [make_path(ANSYS_BASE_PATH, f"v{v}", *BIN_DIR, f"ansys{v}") for v in VERSIONS]
    MAPDL_STUDENT_INSTALL_PATHS = [
        make_path(ANSYS_BASE_PATH, STUDENT_DIR, f"v{v}", *BIN_DIR, f"ansys{v}") for v in STUDENT_VERSIONS
    ]

    DYNA_INSTALL_PATHS = [make_path(ANSYS_BASE_PATH, f"v{v}", *BIN_DIR, f"lsdyna{v}") for v in VERSIONS]
    DYNA_STUDENT_INSTALL_PATHS = [
        make_path(ANSYS_BASE_PATH, STUDENT_DIR, f"v{v}", *BIN_DIR, f"lsdyna{v}") for v in STUDENT_VERSIONS
    ]

    MECHANICAL_INSTALL_PATHS = [make_path(ANSYS_BASE_PATH, f"v{v}", "aisol", ".workbench") for v in VERSIONS]
    MECHANICAL_STUDENT_INSTALL_PATHS = [
        make_path(ANSYS_BASE_PATH, STUDENT_DIR, f"v{v}", "aisol", ".workbench") for v in STUDENT_VERSIONS
    ]


# Safe fallback access to the latest paths
def latest(path_list):
    """Return the latest path from a list of paths."""
    return path_list[-1] if path_list else None


LATEST_ANSYS_INSTALLATION_PATHS = latest(ANSYS_INSTALLATION_PATHS)
LATEST_MAPDL_INSTALL_PATH = latest(MAPDL_INSTALL_PATHS)
LATEST_DYNA_INSTALL_PATH = latest(DYNA_INSTALL_PATHS)
LATEST_MECHANICAL_INSTALL_PATH = latest(MECHANICAL_INSTALL_PATHS)


@pytest.fixture
def mock_filesystem(fs):
    """Mock a filesystem with Ansys installations for testing purposes."""
    for mapdl_install_path in MAPDL_INSTALL_PATHS + MAPDL_STUDENT_INSTALL_PATHS:
        fs.create_file(mapdl_install_path)
    for mechanical_install_path in MECHANICAL_INSTALL_PATHS + MECHANICAL_STUDENT_INSTALL_PATHS:
        fs.create_file(mechanical_install_path)
    for dyna_install_path in DYNA_INSTALL_PATHS + DYNA_STUDENT_INSTALL_PATHS:
        fs.create_file(dyna_install_path)
    fs.create_dir(platformdirs.user_data_dir(appname="ansys_tools_path", appauthor="Ansys"))
    return fs


@pytest.fixture
def mock_filesystem_without_student_versions(fs):
    """Mock a filesystem without student versions of Ansys installations."""
    for mapdl_install_path in MAPDL_INSTALL_PATHS:
        fs.create_file(mapdl_install_path)
    for mechanical_install_path in MECHANICAL_INSTALL_PATHS:
        fs.create_file(mechanical_install_path)
    for dyna_install_path in DYNA_INSTALL_PATHS:
        fs.create_file(dyna_install_path)
    fs.create_dir(platformdirs.user_data_dir(appname="ansys_tools_path", appauthor="Ansys"))


@pytest.fixture
def mock_filesystem_with_config(mock_filesystem):
    """Mock the filesystem with a config file for testing purposes."""
    config_path = Path(platformdirs.user_data_dir(appname="ansys_tools_path", appauthor="Ansys")) / "config.txt"
    mock_filesystem.create_file(str(config_path))
    config_content = json.dumps(
        {
            "mapdl": LATEST_MAPDL_INSTALL_PATH,
            "mechanical": LATEST_MECHANICAL_INSTALL_PATH,
            "dyna": LATEST_DYNA_INSTALL_PATH,
        }
    )
    config_path.write_text(config_content)
    return mock_filesystem


@pytest.fixture
def mock_filesystem_with_empty_config(mock_filesystem):
    """Mock the filesystem with an empty config file for testing purposes."""
    config_path = Path(platformdirs.user_data_dir(appname="ansys_tools_path", appauthor="Ansys")) / "config.txt"
    mock_filesystem.create_file(str(config_path))
    config_path.write_text("")
    return mock_filesystem


@pytest.fixture
def mock_filesystem_without_executable(fs):
    """Mock the filesystem without executable files for testing purposes."""
    fs.create_dir(ANSYS_BASE_PATH)


@pytest.fixture
def mock_empty_filesystem(fs):
    """Mock an empty filesystem for testing purposes."""
    return fs


@pytest.fixture
def mock_filesystem_with_only_old_config(mock_filesystem):
    """Mock the filesystem with an old config file that only contains the MAPDL path."""
    config1_path = Path(platformdirs.user_data_dir(appname="ansys_mapdl_core")) / "config.txt"
    mock_filesystem.create_file(str(config1_path))
    config1_path.write_text(MAPDL_INSTALL_PATHS[0])

    config2_path = Path(platformdirs.user_data_dir(appname="ansys_tools_path")) / "config.txt"
    mock_filesystem.create_file(str(config2_path))
    config2_path.write_text(
        json.dumps({"mapdl": LATEST_MAPDL_INSTALL_PATH, "mechanical": LATEST_MECHANICAL_INSTALL_PATH})
    )

    return mock_filesystem


@pytest.fixture
def mock_filesystem_with_only_oldest_config(mock_filesystem):
    """Mock the filesystem with an old config file that only contains the MAPDL path."""
    config_path = Path(platformdirs.user_data_dir(appname="ansys_mapdl_core")) / "config.txt"
    mock_filesystem.create_file(str(config_path))
    config_path.write_text(MAPDL_INSTALL_PATHS[0])


@pytest.fixture
def mock_awp_environment_variable(monkeypatch):
    """Mock the AWP_ROOT environment variables to simulate Ansys installations."""
    for awp_root_var in filter(lambda var: var.startswith("AWP_ROOT"), os.environ.keys()):
        monkeypatch.delenv(awp_root_var)
    for version, ansys_installation_path in zip(VERSIONS, ANSYS_INSTALLATION_PATHS):
        monkeypatch.setenv(f"AWP_ROOT{version}", ansys_installation_path)
    # this will replace all standard version with the student version
    for version, ansys_student_installation_path in zip(STUDENT_VERSIONS, ANSYS_STUDENT_INSTALLATION_PATHS):
        monkeypatch.setenv(f"AWP_ROOT{version}", ansys_student_installation_path)


def test_change_default_mapdl_path_file_dont_exist(mock_empty_filesystem):
    """Test changing the default MAPDL path."""
    with pytest.raises(FileNotFoundError):
        change_default_mapdl_path(MAPDL_INSTALL_PATHS[1])


def test_change_default_dyna_path_file_dont_exist(mock_empty_filesystem):
    """Test changing the default DYNA path."""
    with pytest.raises(FileNotFoundError):
        change_default_dyna_path(DYNA_INSTALL_PATHS[1])


@pytest.mark.filterwarnings("ignore", category=DeprecationWarning)
def test_change_ansys_path(mock_empty_filesystem):
    """Test changing the Ansys path."""
    with pytest.raises(FileNotFoundError):
        change_default_ansys_path(MAPDL_INSTALL_PATHS[1])


def test_change_default_mapdl_path(mock_filesystem):
    """Test changing the default MAPDL path."""
    config_path = Path(platformdirs.user_data_dir("ansys_mapdl_core")) / "config.txt"
    mock_filesystem.create_file(str(config_path))
    change_default_mapdl_path(MAPDL_INSTALL_PATHS[1])


def test_change_default_mechanical_path(mock_filesystem):
    """Test changing the default mechanical path."""
    change_default_mechanical_path(MECHANICAL_INSTALL_PATHS[1])


@pytest.mark.filterwarnings("ignore", category=DeprecationWarning)
def test_find_ansys(mock_filesystem):
    """Test finding the latest Ansys installation."""
    ansys_bin, ansys_version = find_ansys()
    # windows filesystem being case insensive we need to make a case insensive comparison
    if sys.platform == "win32":
        assert (ansys_bin.lower(), ansys_version) == (LATEST_MAPDL_INSTALL_PATH.lower(), 23.1)
    else:
        assert (ansys_bin, ansys_version) == (LATEST_MAPDL_INSTALL_PATH, 23.1)


@pytest.mark.filterwarnings("ignore", category=DeprecationWarning)
def test_find_ansys_empty_fs(mock_empty_filesystem):
    """Test finding Ansys when no installations are present."""
    ansys_bin, ansys_version = find_ansys()
    assert (ansys_bin, ansys_version) == ("", "")


def test_find_mapdl(mock_filesystem):
    """Test finding the latest MAPDL installation."""
    ansys_bin, ansys_version = find_mapdl()
    # windows filesystem being case insensive we need to make a case insensive comparison
    if sys.platform == "win32":
        assert (ansys_bin.lower(), ansys_version) == (LATEST_MAPDL_INSTALL_PATH.lower(), 23.1)
    else:
        assert (ansys_bin, ansys_version) == (LATEST_MAPDL_INSTALL_PATH, 23.1)


def test_find_specific_mapdl(mock_filesystem, mock_awp_environment_variable):
    """Test finding an specific MAPDL installation."""
    ansys_bin, ansys_version = find_mapdl(21.1)
    if sys.platform == "win32":
        assert (ansys_bin.lower(), ansys_version) == (MAPDL_INSTALL_PATHS[1].lower(), 21.1)
    else:
        assert (ansys_bin, ansys_version) == (MAPDL_INSTALL_PATHS[1], 21.1)


def test_find_mapdl_without_executable(mock_filesystem_without_executable):
    """Test finding MAPDL without executable."""
    ansys_bin, ansys_version = find_mapdl()
    assert (ansys_bin, ansys_version) == ("", "")


def test_find_mapdl_without_student(mock_filesystem_without_student_versions):
    """Test find MAPDL no student."""
    ansys_bin, ansys_version = find_mapdl()
    if sys.platform == "win32":
        assert (ansys_bin.lower(), ansys_version) == (LATEST_MAPDL_INSTALL_PATH.lower(), 23.1)
    else:
        assert (ansys_bin, ansys_version) == (LATEST_MAPDL_INSTALL_PATH, 23.1)


def test_find_dyna(mock_filesystem):
    """Test finding a dyna installation."""
    dyna_bin, dyna_version = find_dyna()
    # windows filesystem being case insensive we need to make a case insensive comparison
    if sys.platform == "win32":
        assert (dyna_bin.lower(), dyna_version) == (LATEST_DYNA_INSTALL_PATH.lower(), 23.1)
    else:
        assert (dyna_bin, dyna_version) == (LATEST_DYNA_INSTALL_PATH, 23.1)


def test_find_specific_dyna(mock_filesystem, mock_awp_environment_variable):
    """Test finding specific dyna install."""
    dyna_bin, dyna_version = find_dyna(21.1)
    if sys.platform == "win32":
        assert (dyna_bin.lower(), dyna_version) == (DYNA_INSTALL_PATHS[1].lower(), 21.1)
    else:
        assert (dyna_bin, dyna_version) == (DYNA_INSTALL_PATHS[1], 21.1)


def test_find_mechanical(mock_filesystem):
    """Test find mechanical."""
    mechanical_bin, mechanical_version = find_mechanical()
    if sys.platform == "win32":
        assert (mechanical_bin.lower(), mechanical_version) == (
            LATEST_MECHANICAL_INSTALL_PATH.lower(),
            23.1,
        )
    else:
        assert (mechanical_bin, mechanical_version) == (LATEST_MECHANICAL_INSTALL_PATH, 23.1)


def test_find_specific_mechanical(mock_filesystem, mock_awp_environment_variable):
    """Test finding specific mechanical install."""
    mechanical_bin, mechanical_version = find_mechanical(21.1)
    if sys.platform == "win32":
        assert (mechanical_bin.lower(), mechanical_version) == (
            MECHANICAL_INSTALL_PATHS[1].lower(),
            21.1,
        )
    else:
        assert (mechanical_bin, mechanical_version) == (MECHANICAL_INSTALL_PATHS[1], 21.1)


def test_inexistant_mechanical(mock_filesystem):
    """Test inexistent mechanical path."""
    with pytest.raises(ValueError):
        find_mechanical(21.6)


def test_find_mechanical_without_student(mock_filesystem_without_student_versions):
    """Test find mechanical without student versions."""
    mechanical_bin, mechanical_version = find_mechanical()
    if sys.platform == "win32":
        assert (mechanical_bin.lower(), mechanical_version) == (
            LATEST_MECHANICAL_INSTALL_PATH.lower(),
            23.1,
        )
    else:
        assert (mechanical_bin, mechanical_version) == (LATEST_MECHANICAL_INSTALL_PATH, 23.1)


@pytest.mark.win32
def test_get_available_ansys_installation_windows(mock_filesystem, mock_awp_environment_variable):
    """Test get available Ansys installations on Windows."""
    available_ansys_installations = get_available_ansys_installations()
    lowercase_available_ansys_installation = {}
    for key, value in available_ansys_installations.items():
        lowercase_available_ansys_installation[key] = value.lower()
    lowercase_ansys_installation_paths = list(
        map(str.lower, ANSYS_INSTALLATION_PATHS + ANSYS_STUDENT_INSTALLATION_PATHS)
    )
    assert lowercase_available_ansys_installation == dict(
        zip([202, 211, 231] + [-201, -211], lowercase_ansys_installation_paths)
    )


@pytest.mark.linux
def test_get_available_ansys_installation_linux(mock_filesystem):
    """Test get available Ansys installations on Linux."""
    assert get_available_ansys_installations() == dict(
        zip(
            [202, 211, 231] + [-201, -211],
            ANSYS_INSTALLATION_PATHS + ANSYS_STUDENT_INSTALLATION_PATHS,
        )
    )


@pytest.mark.filterwarnings("ignore", category=DeprecationWarning)
def test_get_ansys_path(mock_filesystem_with_config):
    """Test get the ansys path."""
    mapdl_path = get_ansys_path()
    if sys.platform == "win32":
        assert mapdl_path is not None
        assert mapdl_path.lower() == LATEST_MAPDL_INSTALL_PATH.lower()
    else:
        assert mapdl_path == LATEST_MAPDL_INSTALL_PATH


def test_get_mapdl_path(mock_filesystem_with_config):
    """Test the get_mapdl_path function to ensure it returns the correct path."""
    mapdl_path = get_mapdl_path()
    if sys.platform == "win32":
        assert mapdl_path is not None
        assert mapdl_path.lower() == LATEST_MAPDL_INSTALL_PATH.lower()
    else:
        assert mapdl_path == LATEST_MAPDL_INSTALL_PATH


def test_get_dyna_path(mock_filesystem_with_config):
    """Test get the DYNA path."""
    dyna_path = get_dyna_path()
    if sys.platform == "win32":
        assert dyna_path is not None
        assert dyna_path.lower() == LATEST_DYNA_INSTALL_PATH.lower()
    else:
        assert dyna_path == LATEST_DYNA_INSTALL_PATH


def test_get_mechanical_path(mock_filesystem_with_config):
    """Test the get_mechanical_path function to ensure it returns the correct path."""
    mechanical_path = get_mechanical_path()
    if sys.platform == "win32":
        assert mechanical_path is not None
        assert mechanical_path.lower() == LATEST_MECHANICAL_INSTALL_PATH.lower()
    else:
        assert mechanical_path == LATEST_MECHANICAL_INSTALL_PATH


def test_get_mechanical_path_custom(mock_filesystem):
    """Test that will make the function ask for the path to the installation.

    It will mock the input with LATEST_MECHANICAL_PATH.
    Doing this (even if the version and the install path don't match)
    allow to check that we can enter a path for a version not detected
    """
    with patch("builtins.input", side_effect=[LATEST_MECHANICAL_INSTALL_PATH]):
        mechanical_path = get_mechanical_path(True, version=193)
        assert mechanical_path is not None
        if sys.platform == "win32":
            assert mechanical_path.lower() == LATEST_MECHANICAL_INSTALL_PATH.lower()
        else:
            assert mechanical_path == LATEST_MECHANICAL_INSTALL_PATH
    assert get_mechanical_path(False, version=193) is None


def test_get_mechanical_specific(mock_filesystem):
    """Test the get_mechanical_path function with a specific version."""
    mechanical_path = get_mechanical_path(version=23.1)
    assert mechanical_path is not None
    if sys.platform == "win32":
        assert mechanical_path.lower() == LATEST_MECHANICAL_INSTALL_PATH.lower()
    else:
        assert mechanical_path == LATEST_MECHANICAL_INSTALL_PATH


def test_get_latest_ansys_installation(mock_filesystem):
    """Test the get_latest_ansys_installation function to ensure it returns the latest version and path correctly."""
    latest_ansys_version, latest_ansys_installation_path = get_latest_ansys_installation()
    if sys.platform == "win32":
        assert (latest_ansys_version, latest_ansys_installation_path.lower()) == (
            231,
            LATEST_ANSYS_INSTALLATION_PATHS.lower(),
        )
    else:
        assert latest_ansys_version, latest_ansys_installation_path == (
            231,
            LATEST_ANSYS_INSTALLATION_PATHS,
        )


def test_save_mapdl_path(mock_filesystem):
    """Test save MAPDL path."""
    save_mapdl_path()
    config_path = Path(SETTINGS_DIR) / "config.txt"
    with config_path.open() as file:
        json_file = json.load(file)
        json_file = {key: val.lower() for key, val in json_file.items()}
        if sys.platform == "win32":
            assert json_file == {"mapdl": LATEST_MAPDL_INSTALL_PATH.lower()}
        else:
            assert json_file == {"mapdl": LATEST_MAPDL_INSTALL_PATH}


def test_save_dyna_path(mock_filesystem):
    """Test save dyna path."""
    save_dyna_path()
    config_path = SETTINGS_DIR / "config.txt"
    with config_path.open() as file:
        json_file = json.load(file)
        json_file = {key: val.lower() for key, val in json_file.items()}
        if sys.platform == "win32":
            assert json_file == {"dyna": LATEST_DYNA_INSTALL_PATH.lower()}
        else:
            assert json_file == {"dyna": LATEST_DYNA_INSTALL_PATH}


def test_save_mechanical_path(mock_filesystem):
    """Test the save mechanical path."""
    save_mechanical_path()
    config_path = SETTINGS_DIR / "config.txt"
    with config_path.open() as file:
        json_file = json.load(file)
        json_file = {key: val.lower() for key, val in json_file.items()}
        if sys.platform == "win32":
            assert json_file == {"mechanical": LATEST_MECHANICAL_INSTALL_PATH.lower()}
        else:
            assert json_file == {"mechanical": LATEST_MECHANICAL_INSTALL_PATH}


def test_version_from_path(mock_filesystem):
    """Test the version_from_path function to ensure it correctly extracts the version from installation paths."""
    if sys.platform == "win32":
        wrong_folder = "C:\\f"
    else:
        wrong_folder = "/f"
    assert version_from_path("mapdl", MAPDL_INSTALL_PATHS[0]) == 202
    assert version_from_path("mechanical", LATEST_MECHANICAL_INSTALL_PATH) == 231
    with pytest.raises(Exception):
        version_from_path("skvbhksbvks", LATEST_MAPDL_INSTALL_PATH)
    with pytest.raises(RuntimeError):
        version_from_path("mapdl", wrong_folder)
    with pytest.raises(RuntimeError):
        version_from_path("mechanical", wrong_folder)


def test_get_latest_ansys_installation_empty_fs(mock_empty_filesystem):
    """Test that the function raises an error when no installations are found."""
    with pytest.raises(ValueError):
        get_latest_ansys_installation()


@pytest.mark.filterwarnings("ignore", category=DeprecationWarning)
def test_empty_config_file(mock_filesystem_with_empty_config):
    """Test that the config file is empty and no paths are set."""
    assert get_ansys_path() == LATEST_MAPDL_INSTALL_PATH


@pytest.mark.win32
def test_migration_old_config_file(mock_filesystem_with_only_old_config):
    """Migrate old config files to the new location on Windows."""
    old_config1_location = Path(platformdirs.user_data_dir(appname="ansys_mapdl_core")) / "config.txt"
    old_config2_location = Path(platformdirs.user_data_dir(appname="ansys_tools_path")) / "config.txt"
    new_config_location = SETTINGS_DIR / "config.txt"

    assert get_mapdl_path() == LATEST_MAPDL_INSTALL_PATH
    assert not old_config1_location.exists()
    assert not old_config2_location.exists()
    assert new_config_location.exists()


@pytest.mark.linux
def test_migration_old_config_file_linux(mock_filesystem_with_only_old_config):
    """No migration should take place on Linux, as the config is already in the correct location.

    The config path change only applied to Windows.
    """
    old_config1_location = Path(platformdirs.user_data_dir(appname="ansys_mapdl_core")) / "config.txt"
    new_config_location = SETTINGS_DIR / "config.txt"

    assert get_mapdl_path() == LATEST_MAPDL_INSTALL_PATH
    assert old_config1_location.exists()
    assert new_config_location.exists()


def test_migration_oldest_config_file(mock_filesystem_with_only_oldest_config):
    """Migrate the old config file."""
    old_config_location = Path(platformdirs.user_data_dir(appname="ansys_mapdl_core")) / "config.txt"

    # Check that get_mapdl_path correctly reads from the migrated config
    assert get_mapdl_path() == MAPDL_INSTALL_PATHS[0]

    # Confirm old config no longer exists and new config is present
    assert not old_config_location.exists()
    assert (SETTINGS_DIR / "config.txt").exists()


def test_clear_config_file(mock_filesystem_with_config):
    """Clear the config file."""
    config_file = SETTINGS_DIR / "config.txt"

    # Clear 'mapdl' key and check results
    clear_configuration("mapdl")
    content = json.loads(config_file.read_text())
    assert "mapdl" not in content
    assert "mechanical" in content and content["mechanical"] is not None

    # Clear 'mechanical' key and verify
    clear_configuration("mechanical")
    content = json.loads(config_file.read_text())
    assert "mechanical" not in content

    # Clear a key that doesn't exist ('dyna') and check config still exists
    clear_configuration("dyna")
    assert config_file.exists()
    content = json.loads(config_file.read_text())
    assert content == {}


values = [
    (11, True),
    (11.1, True),
    ("asdf", False),
    ("1234asdf", False),
]


@pytest.mark.parametrize("values", values)
def test_is_float(values):
    """Test the is_float function."""
    assert _is_float(values[0]) == values[1]
