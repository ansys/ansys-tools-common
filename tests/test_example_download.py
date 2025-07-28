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
"""Tests for example downloads."""

from pathlib import Path

import pytest
import requests

from ansys.tools.common.example_download import download_manager


def test_download():
    """Test downloading a file from the example repository."""
    filename = "11_blades_mode_1_ND_0.csv"
    directory = "pymapdl/cfx_mapping"

    # Download the file
    local_path_str = download_manager.download_file(filename, directory)
    local_path = Path(local_path_str)
    assert local_path.is_file()

    # Check that file is cached
    local_path2 = download_manager.download_file(filename, directory)

    assert local_path2 == local_path_str

    download_manager.clear_download_cache()

    assert not Path.is_file(local_path)


def test_non_existent_file():
    """Test downloading a non-existent file."""
    filename = "non_existent_file.txt"
    directory = "pymapdl/cfx_mapping"

    # Attempt to download the non-existent file
    with pytest.raises(requests.exceptions.HTTPError):
        download_manager.download_file(filename, directory)


def test_get_filepath():
    """Test getting the file path of a downloaded file."""
    filename = "11_blades_mode_1_ND_0.csv"
    directory = "pymapdl/cfx_mapping"

    # Get the file path
    filepath = download_manager._get_filepath_on_default_server(filename, directory)

    assert filepath == "https://github.com/ansys/example-data/raw/main/pymapdl/cfx_mapping/11_blades_mode_1_ND_0.csv"

    directory += "/"
    filepath = download_manager._get_filepath_on_default_server(filename, directory)

    assert filepath == "https://github.com/ansys/example-data/raw/main/pymapdl/cfx_mapping/11_blades_mode_1_ND_0.csv"

    filepath = download_manager._get_filepath_on_default_server(filename)

    assert filepath == "https://github.com/ansys/example-data/raw/main/11_blades_mode_1_ND_0.csv"


def test_destination_directory():
    """Test getting the destination directory for a downloaded file."""
    filename = "11_blades_mode_1_ND_0.csv"
    directory = "pymapdl/cfx_mapping"

    # Test directory gets created
    result = download_manager.download_file(filename, directory, destination="not_a_dir")
    assert result is not None
