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
"""Module for downloading examples from the PyAnsys Github ``example-data`` repository."""

from pathlib import Path
import tempfile
from threading import Lock
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests

__all__ = ["DownloadManager"]

BASE_URL = "https://github.com/ansys/example-data/raw/main"


class DownloadManagerMeta(type):
    """Provides a thread-safe implementation of ``Singleton``.

    https://refactoring.guru/design-patterns/singleton/python/example#example-1.
    """

    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        """Call to the class."""
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class DownloadManager(metaclass=DownloadManagerMeta):
    """Manages downloads of example files.

    Manages the download of example from the ``example-data``
    repository, which is at https://github.com/ansys/example-data.
    """

    def __init__(self):
        """Initialize the download manager."""
        self._downloads_list = []

    def clear_download_cache(self):
        """Remove downloaded example files from the local path."""
        for file in self._downloads_list:
            Path(file).unlink()
        self._downloads_list.clear()

    def download_file(
        self, filename: str, directory: str, destination: Optional[str] = None, force: bool = False
    ) -> str:
        """Download an example file from the ``example-data`` repository.

        Parameters
        ----------
        filename : str
            Name of the example file to download.
        directory : str
            Path under the ``example-data`` repository.
        destination : str, default: None
            Path to download the example file to. The default
            is ``None``, in which case the default path for app data
            is used.
        force : bool, default: False
            Whether to always download the example file. The default is
            ``False``, in which case if the example file is cached, it
            is reused.

        Returns
        -------
        tuple[str, str]
            Tuple containing the filepath to use and the local
            filepath of the downloaded directory. The two are
            different in case of containers.
        """
        # Convert to Path object
        destination_path = Path(destination) if destination is not None else None

        # If destination is not a dir, create it
        if destination_path is not None and not destination_path.exists():
            destination_path.mkdir(parents=True, exist_ok=True)

        # Check if it was able to create the dir, very rare case
        if destination_path is not None and not destination_path.is_dir():
            raise ValueError("Destination directory provided does not exist.")  # pragma: no cover

        url = self._get_filepath_on_default_server(filename, directory)
        local_path = self._retrieve_data(url, filename, dest=destination, force=force)

        # add path to downloaded files
        self._add_file(local_path)
        return local_path

    def _add_file(self, file_path: str):
        """Add the path for a downloaded example file to a list.

        This list keeps track of where example files are
        downloaded so that a global cleanup of these files can be
        performed when the client is closed.

        Parameters
        ----------
        file_path : str
            Local path of the downloaded example file.
        """
        if file_path not in self._downloads_list:
            self._downloads_list.append(file_path)

    def _joinurl(self, base: str, directory: str) -> str:
        """Join multiple paths to a base URL.

        Parameters
        ----------
        base : str
            Base URL to append the directory path to.
            If this URL doesn't end with '/', then it is added automatically.
        directory : str
            Directory path to append to the base URL.

        Returns
        -------
        str
            Joined URL with the base and paths.
        """
        if base[-1] != "/":
            base += "/"
        return urljoin(base, directory)

    def _get_filepath_on_default_server(self, filename: str, directory: str = None) -> str:
        """Get the full URL of the file on the default repository.

        Parameters
        ----------
        filename : str
            Name of the file to download.
        directory : str, default: None
            Path under the ``example-data`` repository.

        Returns
        -------
        str
            Full URL of the file on the default repository.
        """
        if directory:
            if directory[-1] != "/":
                directory += "/"
            return self._joinurl(BASE_URL, directory + filename)
        else:
            return self._joinurl(BASE_URL, filename)

    def _retrieve_data(self, url: str, filename: str, dest: str = None, force: bool = False) -> str:
        """Retrieve data from a URL and save it to a local file.

        Parameters
        ----------
        url : str
            URL to download the file from.
        filename : str
            Name of the file to save the downloaded content as.
        dest : str, default: None
            Destination path of the file.
        force : bool, default: False
            Whether to force downloading to avoid cached examples.

        Returns
        -------
        str
            Local path where the file was saved.
        """
        if dest is None:
            dest = tempfile.gettempdir()
        local_path = Path(dest) / Path(filename).name

        if not force and local_path.is_file():
            return str(local_path)

        parsed_url = urlparse(url)
        if parsed_url.scheme not in ("http", "https"):
            raise ValueError(f"Unsafe URL scheme: {parsed_url.scheme}")

        response = requests.get(url, timeout=60)
        response.raise_for_status()

        Path(local_path).write_bytes(response.content)

        return str(local_path)


# Create a singleton instance of DownloadManager
download_manager = DownloadManager()
