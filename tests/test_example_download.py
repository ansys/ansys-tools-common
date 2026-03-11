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
"""Tests for example downloads."""

from pathlib import Path
from unittest.mock import patch

import pytest
import requests

from ansys.tools.common.example_download import download_manager


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


def test_download_file():
    """Test downloading a file from the example repository."""
    filename = "11_blades_mode_1_ND_0.csv"
    directory = "pymapdl/cfx_mapping"

    # Download the file
    local_path_str = download_manager.download_file(filename, directory, force=True)
    local_path = Path(local_path_str)
    assert local_path.is_file()
    assert [local_path_str] == download_manager._downloads_list

    download_manager.clear_download_cache()
    assert not Path.is_file(local_path)


def test_download_file_git_based(tmp_path):
    """Test downloading a file from the example repository using Git."""
    filename = "11_blades_mode_1_ND_0.csv"
    directory = "pymapdl/cfx_mapping"

    # Download the file
    local_path_str = download_manager._download_file_git_based(filename, directory, destination=str(tmp_path))
    local_path = Path(local_path_str)
    assert local_path.is_file()

    # Assert that no subprocess call is made, meaning the directory was not re-downloaded
    with patch("subprocess.run") as mock_subprocess:
        local_path2 = download_manager._download_file_git_based(filename, directory, destination=str(tmp_path))
        mock_subprocess.assert_not_called()
        assert local_path2 == local_path_str


def test_download_file_http_based(tmp_path):
    """Test downloading a file from the example repository using HTTP."""
    filename = "11_blades_mode_1_ND_0.csv"
    directory = "pymapdl/cfx_mapping"

    # Download the file
    local_path_str = download_manager._download_file_http_based(filename, directory, destination=str(tmp_path))
    local_path = Path(local_path_str)
    assert local_path.is_file()

    # Assert that write_bytes was not called, meaning the directory was not re-downloaded
    with patch.object(Path, "write_bytes") as mock_write:
        local_path2 = download_manager._download_file_http_based(filename, directory, destination=str(tmp_path))
        mock_write.assert_not_called()
        assert local_path2 == local_path_str


def test_download_directory():
    """Test downloading a directory from the example repository."""
    # Directory containing other directories
    directory = "pyadditive/calibration_input"
    expected_files = {
        "cantilever_p.stl",
        "cantilever_s.stl",
        "crossed_walls_p.stl",
        "double_arches_p.stl",
        "four_pillars_p.stl",
        "thin_wall_p.stl",
    }

    # Download the directory
    local_path_str = download_manager.download_directory(directory, force=True)
    local_path = Path(local_path_str)
    assert local_path.is_dir()
    assert expected_files == set(map(lambda s: Path(s).name, download_manager._downloads_list))

    download_manager.clear_download_cache()
    assert not Path.is_file(local_path)


def test_download_directory_git_based(tmp_path):
    """Test downloading a directory from the example repository using Git."""
    # Directory containing other directories
    directory = "pyadditive"

    # Download the directory
    local_path_str = download_manager._download_directory_git_based(directory, destination=str(tmp_path))
    local_path = Path(local_path_str)
    assert local_path.is_dir()

    # Assert that no subprocess call is made, meaning the directory was not re-downloaded
    with patch("subprocess.run") as mock_subprocess:
        local_path2 = download_manager._download_directory_git_based(directory, destination=str(tmp_path))
        mock_subprocess.assert_not_called()
        assert local_path2 == local_path_str


def test_download_directory_http_based(tmp_path):
    """Test downloading a directory from the example repository using HTTP."""
    # Directory containing other directories
    directory = "pyadditive"

    # Download the directory
    try:
        local_path_str = download_manager._download_directory_http_based(directory, destination=str(tmp_path))
    except requests.exceptions.HTTPError as e:
        if "rate limit" in str(e).lower():
            pytest.skip("GitHub API rate limit exceeded (set GITHUB_TOKEN to avoid this)")
        raise

    local_path = Path(local_path_str)
    assert local_path.is_dir()

    # Assert that write_bytes was not called, meaning the directory was not re-downloaded
    with patch.object(Path, "write_bytes") as mock_write:
        local_path2 = download_manager._download_directory_http_based(directory, destination=str(tmp_path))
        mock_write.assert_not_called()
        assert local_path2 == local_path_str
