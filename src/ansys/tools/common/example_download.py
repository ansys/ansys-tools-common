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

import os
from pathlib import Path
import tempfile
from threading import Lock
import time
from urllib.parse import urljoin, urlparse

import requests

__all__ = ["DownloadManager"]

BASE_URL = "https://github.com/ansys/example-data/raw/main"
GIT_URL = "https://github.com/ansys/example-data.git"


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
        self,
        filename: str,
        directory: str,
        destination: str | Path | None = None,
        force: bool = False,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> str:
        """Download an example file from the ``example-data`` repository.

        Parameters
        ----------
        filename : str
            Name of the example file to download.
        directory : str
            Path under the ``example-data`` repository.
        destination : str | Path | None, default: None
            Path to download the example file to.
            The default is ``None``, in which case the default path for app data is used.
        force : bool, default: False
            Whether to always download the example file. The default is
            ``False``, in which case if the example file is cached, it
            is reused.
        timeout : float, default: 60.0
            Timeout in seconds for the download operation. The default is 60 seconds.
        max_retries : int, default: 3
            Maximum number of retry attempts for failed downloads.

        Returns
        -------
        str
            Local path of the downloaded example file.
        """
        # Convert to Path object
        destination_path = Path(destination).resolve() if destination is not None else None

        # If destination is not a dir, create it
        if destination_path is not None and not destination_path.exists():
            destination_path.mkdir(parents=True, exist_ok=True)

        # Check if it was able to create the dir, very rare case
        if destination_path is not None and not destination_path.is_dir():
            raise ValueError("Destination directory provided does not exist.")  # pragma: no cover

        if destination_path is None:
            destination_path = Path(tempfile.gettempdir()).resolve()

        # Try Git sparse checkout first, fallback to HTTP if it fails
        try:
            local_path = self._download_file_git_based(
                filename, directory, destination_path, force, timeout, max_retries
            )
        except Exception:
            local_path = self._download_file_http_based(
                filename, directory, destination_path, force, timeout, max_retries
            )

        # Add path to downloaded files
        self._add_file(local_path)
        return local_path

    def download_directory(
        self,
        directory: str,
        destination: str | Path | None = None,
        force: bool = False,
        github_token: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> str:
        """Download an example directory from the ``example-data`` repository.

        This method first tries to use Git sparse checkout for efficient downloading.
        If Git is not available or the operation fails, it falls back to HTTP download.

        .. warning::

            Do not execute this function with untrusted ``directory`` argument.
            Download directory tries to use Git sparse checkout, which involves
            executing Git commands with the directory as argument.

        Parameters
        ----------
        directory : str
            Path under the ``example-data`` repository.
        destination : str | Path | None, default: None
            Path to download the example file to. The default
            is ``None``, in which case the default path for app data
            is used.
        force : bool, default: False
            Whether to always download the example file. The default is
            ``False``, in which case if the example file is cached, it
            is reused.
        github_token : str | None, default: None
            GitHub personal access token for API authentication (used by HTTP fallback).
            When ``None``, falls back to ``GITHUB_TOKEN`` or ``GH_TOKEN`` environment
            variables. Using a token increases the rate limit from 60 req/h to 5000 req/h.
        timeout : float, default: 60.0
            Timeout in seconds for the download operation (used by HTTP fallback). The default is 60 seconds.
        max_retries : int, default: 3
            Maximum number of retry attempts for failed downloads.

        Returns
        -------
        str
            Local path of the downloaded example file.
        """
        # Try using Git sparse checkout first and fallback to individual file download if it fails.
        try:
            local_path = self._download_directory_git_based(directory, destination, force, timeout, max_retries)
        except Exception:
            local_path = self._download_directory_http_based(
                directory, destination, force, github_token, timeout, max_retries
            )

        # Add path to downloaded file(s)
        self._add_directory(local_path)
        return local_path

    def _download_directory_git_based(
        self,
        directory: str,
        destination: str | Path | None = None,
        force: bool = False,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> str:
        """Download an example directory using Git sparse checkout.

        .. warning::

            Do not execute this function with untrusted ``directory`` argument.

        Parameters
        ----------
        directory : str
            Path under the ``example-data`` repository.
        destination : str | Path | None, default: None
            Path to download the example directory to. The default
            is ``None``, in which case the default path for app data
            is used.
        force : bool, default: False
            Whether to always download the example directory. The default is
            ``False``, in which case if the example directory is cached, it
            is reused.
        timeout : float, default: 60.0
            Timeout in seconds for each git operation.
        max_retries : int, default: 3
            Maximum number of retry attempts for failed git operations.

        Returns
        -------
        str
            Local path of the downloaded example directory.
        """
        import re
        import shutil
        import subprocess  # nosec B404

        # Validate directory to prevent command injection
        # Only allow alphanumeric, hyphens, underscores, dots, forward slashes, and spaces
        if not re.match(r"^[a-zA-Z0-9_\-./\s]+$", directory):
            raise ValueError(f"Invalid directory name: {directory}")

        local_path = self._resolve_directory_destination(directory, destination)
        if not force and local_path.is_dir() and any(local_path.iterdir()):
            return str(local_path)

        # Clone with sparse checkout, with retry logic
        for attempt in range(max_retries):
            temp_clone = Path(tempfile.mkdtemp())
            try:
                cmd = ["git", "clone", "--depth=1", "--filter=blob:none", "--sparse", GIT_URL, str(temp_clone)]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)  # nosec B603
                cmd = ["git", "-C", str(temp_clone), "sparse-checkout", "set", directory]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)  # nosec B603

                # Move the directory to destination
                src_path = temp_clone / directory
                if src_path.exists():
                    shutil.copytree(src_path, local_path, dirs_exist_ok=True)
                return str(local_path)
            except (subprocess.TimeoutExpired, Exception) as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"Git operation failed after {max_retries} attempts: {e}") from e
            finally:
                shutil.rmtree(temp_clone, ignore_errors=True)

        raise RuntimeError("Git operation failed after all retry attempts.")

    def _download_directory_http_based(
        self,
        directory: str,
        destination: str | Path | None = None,
        force: bool = False,
        github_token: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> str:
        """Download an example directory using HTTP.

        Parameters
        ----------
        directory : str
            Path under the ``example-data`` repository.
        destination : str | Path | None, default: None
            Path to download the example directory to. The default
            is ``None``, in which case the default path for app data
            is used.
        force : bool, default: False
            Whether to always download the example directory. The default is
            ``False``, in which case if the example directory is cached, it
            is reused.
        github_token : str | None, default: None
            GitHub personal access token for API authentication.
            When ``None``, falls back to ``GITHUB_TOKEN`` or ``GH_TOKEN`` environment
            variables. Using a token increases the rate limit from 60 req/h to 5000 req/h.
        timeout : float, default: 60.0
            Timeout in seconds for the download operation. The default is 60 seconds.
        max_retries : int, default: 3
            Maximum number of retry attempts for failed downloads.

        Returns
        -------
        str
            Local path of the downloaded example directory.
        """
        local_path = self._resolve_directory_destination(directory, destination)
        if not force and local_path.is_dir() and any(local_path.iterdir()):
            return str(local_path)

        files = self._list_files(directory, github_token)
        for file in files:
            file_path = Path(file)
            self.download_file(
                str(file_path.name), file_path.parent.as_posix(), local_path, force, timeout, max_retries
            )

        return str(local_path)

    def _download_file_git_based(
        self,
        filename: str,
        directory: str,
        destination: str | Path,
        force: bool = False,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> str:
        """Download a single file using Git sparse checkout.

        .. warning::

            Do not execute this function with untrusted ``filename`` and ``directory`` arguments.

        Parameters
        ----------
        filename : str
            Name of the file to download.
        directory : str
            Path under the ``example-data`` repository.
        destination : str | Path
            Path to download the file to.
        force : bool, default: False
            Whether to always download the file. The default is
            ``False``, in which case if the file is cached, it
            is reused.
        timeout : float, default: 60.0
            Timeout in seconds for each git operation.
        max_retries : int, default: 3
            Maximum number of retry attempts for failed git operations.

        Returns
        -------
        str
            Local path of the downloaded file.
        """
        import re
        import shutil
        import subprocess  # nosec B404

        # Validate filename to prevent command injection
        # Only allow alphanumeric, hyphens, underscores, dots, spaces, and parentheses
        if not re.match(r"^[a-zA-Z0-9_\-.\s()]+$", filename):
            raise ValueError(f"Invalid filename: {filename}")

        # Validate directory to prevent command injection
        # Only allow alphanumeric, hyphens, underscores, dots, forward slashes, and spaces
        if not re.match(r"^[a-zA-Z0-9_\-./\s]+$", directory):
            raise ValueError(f"Invalid directory name: {directory}")

        local_path = Path(destination) / filename

        if not force and local_path.is_file():
            return str(local_path)

        # Build the file path in the repository
        file_path_in_repo = f"{directory}/{filename}" if directory else filename

        # NOTE: The following workflow does not use sparse-checkout, for more information
        # see https://github.com/ansys/ansys-tools-common/pull/210#discussion_r2888952765
        for attempt in range(max_retries):
            temp_clone = Path(tempfile.mkdtemp())
            try:
                # Initialize a new git repo
                subprocess.run(
                    ["git", "init"],
                    cwd=str(temp_clone),
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=timeout,
                )  # nosec B603, B607

                # Add remote origin
                subprocess.run(
                    ["git", "remote", "add", "origin", GIT_URL],
                    cwd=str(temp_clone),
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=timeout,
                )  # nosec B603, B607

                # Enable sparse checkout
                subprocess.run(
                    ["git", "config", "core.sparseCheckout", "true"],
                    cwd=str(temp_clone),
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=timeout,
                )  # nosec B603, B607

                # Write sparse-checkout pattern to .git/info/sparse-checkout
                sparse_checkout_file = temp_clone / ".git" / "info" / "sparse-checkout"
                sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)
                sparse_checkout_file.write_text(file_path_in_repo + "\n")

                # Fetch with blob filter and depth=1 (only downloads requested file)
                subprocess.run(
                    ["git", "fetch", "--filter=blob:none", "--depth=1", "origin", "main"],
                    cwd=str(temp_clone),
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=timeout,
                )  # nosec B603, B607
                subprocess.run(
                    ["git", "checkout", "main"],
                    cwd=str(temp_clone),
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=timeout,
                )  # nosec B603, B607

                # Copy the file to destination
                src_file = temp_clone / file_path_in_repo
                if src_file.exists():
                    Path(destination).mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, local_path)
                    return str(local_path)
                else:
                    raise FileNotFoundError(f"File not found in repository: {file_path_in_repo}")
            except (subprocess.TimeoutExpired, Exception) as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"Git operation failed after {max_retries} attempts: {e}") from e
            finally:
                shutil.rmtree(temp_clone, ignore_errors=True)

        raise RuntimeError("Git operation failed after all retry attempts.")

    def _download_file_http_based(
        self,
        filename: str,
        directory: str,
        destination: str | Path,
        force: bool = False,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> str:
        """Download a single file using HTTP.

        Parameters
        ----------
        filename : str
            Name of the file to download.
        directory : str
            Directory path under the default server.
        destination : str | Path
            Destination path to save the downloaded file.
        force : bool, default: False
            Whether to force downloading to avoid cached examples.
        timeout : float, default: 60.0
            Timeout in seconds for the download operation. The default is 60 seconds.
        max_retries : int, default: 3
            Maximum number of retry attempts for failed downloads.
        """
        url = self._get_filepath_on_default_server(filename, directory)
        local_path = self._retrieve_data(
            url, filename, destination, force=force, timeout=timeout, max_retries=max_retries
        )
        return local_path

    def _resolve_directory_destination(self, directory: str, destination: str | Path | None) -> Path:
        """Resolve destination path for directory downloads.

        Parameters
        ----------
        directory : str
            Path under the ``example-data`` repository.
        destination : str | Path | None
            Path to download the example directory to. When ``None``,
            the default temporary directory is used.

        Returns
        -------
        Path
            The resolved local path for the directory.
        """
        if destination is None:
            destination = Path(tempfile.gettempdir()).resolve()
        else:
            destination = Path(destination).resolve()

        return Path(destination) / Path(directory)

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

    def _add_directory(self, directory_path: str):
        """Add the path of the file(s) for a downloaded example directory to a list.

        This list keeps track of where example directories are downloaded so that a
        global cleanup of these directories can be performed when the client is closed.

        Parameters
        ----------
        directory_path : str
            Local path of the downloaded example directory.
        """
        for file in Path(directory_path).rglob("*"):
            if str(file) not in self._downloads_list:
                self._downloads_list.append(str(file))

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

    def _retrieve_data(
        self,
        url: str,
        filename: str,
        destination: str | Path,
        force: bool = False,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> str:
        """Retrieve data from a URL and save it to a local file.

        Parameters
        ----------
        url : str
            URL to download the file from.
        filename : str
            Name of the file to save the downloaded content as.
        destination : str | Path
            Destination path of the file.
        force : bool, default: False
            Whether to force downloading to avoid cached examples.
        timeout : float , default: 60.0
            Timeout in seconds for the download operation. The default is 60 seconds.
        max_retries : int, default: 3
            Maximum number of retry attempts for failed downloads.

        Returns
        -------
        str
            Local path where the file was saved.
        """
        local_path = Path(destination) / Path(filename).name

        if not force and local_path.is_file():
            return str(local_path)

        parsed_url = urlparse(url)
        if parsed_url.scheme not in ("http", "https"):
            raise ValueError(f"Unsafe URL scheme: {parsed_url.scheme}")

        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()

                Path(local_path).write_bytes(response.content)

                return str(local_path)
            except Exception as e:
                if attempt < max_retries - 1:
                    # Exponential backoff: wait 1s, 2s, 4s, etc.
                    wait_time = 2**attempt
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    raise RuntimeError(f"Failed to download file from {url} after {max_retries} attempts: {e}") from e

    def _list_files(self, folder: str, github_token: str | None = None) -> list:
        """List all files in a folder of the example-data repository.

        Parameters
        ----------
        folder : str
            The folder in the GitHub repository to list files from, e.g., "pyaedt/sbr/".
        github_token : str | None, optional
            GitHub personal access token for API authentication.
            When ``None`` (default), falls back to ``GITHUB_TOKEN`` or ``GH_TOKEN``
            environment variables. Using a token increases the rate limit from
            60 req/h (unauthenticated) to 5000 req/h (authenticated).

        Returns
        -------
        list
            A list of file paths in the specified folder.
        """
        # Adding a trailing slash to ensure we only match files in the specified folder
        # Otherwise an input of "project/folder" would also match "project/folder_diff"
        folder_prefix = folder if folder.endswith("/") else folder + "/"

        # URL to fetch the full repo tree recursively
        url = "https://api.github.com/repos/ansys/example-data/git/trees/main?recursive=1"

        # Use provided token, or fall back to environment variables
        headers = {}
        token = github_token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"

        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        tree = response.json()["tree"]

        files = []
        for item in tree:
            if item["type"] == "blob" and item["path"].startswith(folder_prefix):
                files.append(item["path"])
        return files


# Create a singleton instance of DownloadManager
download_manager = DownloadManager()
