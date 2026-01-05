# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
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
"""Module for integration tests."""

import json
import os
from pathlib import Path

import pytest

from ansys.tools.common.path import (
    clear_configuration,
    find_mapdl,
    get_available_ansys_installations,
    save_mapdl_path,
)
from ansys.tools.common.path.path import CONFIG_FILE

skip_if_not_ansys_local = pytest.mark.skipif(
    os.environ.get("ANSYS_LOCAL", "").upper() != "TRUE", reason="Skipping on CI"
)


@skip_if_not_ansys_local
def test_find_mapdl():
    """Test that the function finds the MAPDL executable and returns its path and version."""
    bin_file, ver = find_mapdl()
    assert Path(bin_file).is_file()
    assert ver != ""


@skip_if_not_ansys_local
def test_get_available_ansys_installation():
    """Test that the function returns a list of available Ansys installations."""
    assert get_available_ansys_installations()


@skip_if_not_ansys_local
@pytest.mark.linux
def test_save_mapdl_path():
    """Test saving the MAPDL path to the configuration file."""
    config_path = Path(CONFIG_FILE)

    # Backup existing config content if the config file exists
    old_config = config_path.read_text() if config_path.is_file() else None

    # Find the MAPDL executable path for version 222
    path, _ = find_mapdl(version=222)

    # Save the found MAPDL path to the config
    assert save_mapdl_path(path, allow_prompt=False)

    # Verify that the config file contains the correct mapdl path
    config_data = json.loads(config_path.read_text())
    assert config_data == {"mapdl": "/ansys_inc/v222/ansys/bin/ansys222"}

    # Test saving None path does not overwrite the saved config
    assert save_mapdl_path(None, allow_prompt=False)
    config_data = json.loads(config_path.read_text())
    assert config_data == {"mapdl": "/ansys_inc/v222/ansys/bin/ansys222"}

    # Clear all configurations after the test
    clear_configuration("all")

    # Restore original config if it existed before the test
    if old_config is not None:
        config_path.write_text(old_config)
