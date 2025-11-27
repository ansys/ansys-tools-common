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

"""Example launcher plugin, controlling an HTTP server."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
import subprocess
import sys

import requests

from ansys.tools.local_product_launcher.helpers.ports import find_free_ports
from ansys.tools.local_product_launcher.interface import LauncherProtocol, ServerType


# START_LAUNCHER_CONFIG
@dataclass
class LauncherConfig:
    """Defines the configuration options for the HTTP server launcher."""

    directory: str = field(default=os.getcwd())


# END_LAUNCHER_CONFIG


# START_LAUNCHER_CLS
class Launcher(LauncherProtocol[LauncherConfig]):
    """Implements launching an HTTP server."""

    CONFIG_MODEL = LauncherConfig
    SERVER_SPEC = {"main": ServerType.GENERIC}

    def __init__(self, *, config: LauncherConfig):
        """Instantiate the HTTP server launcher."""
        self._config = config

    def start(self) -> None:
        """Start the HTTP server."""
        port = find_free_ports()[0]
        self._url = f"localhost:{port}"
        self._process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "http.server",
                "--directory",
                self._config.directory,
                str(port),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )

    def stop(self, *, timeout: float | None = None) -> None:
        """Stop the HTTP server."""
        self._process.terminate()
        try:
            self._process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()

    def check(self, timeout: float | None = None) -> bool:
        """Check if the server is running."""
        try:
            # As a simple check, we try to get the main page from the
            # server. If it is accessible, we the server is running.
            # If not, we assume it is not running.
            requests.get(f"http://{self._url}")
            return True
        except requests.RequestException:
            return False

    @property
    def urls(self) -> dict[str, str]:
        """Addresses on which the server is serving content."""
        return {"main": self._url}


# END_LAUNCHER_CLS
