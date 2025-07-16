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
"""Simple launcher for testing module."""

import dataclasses
import pathlib
import subprocess
import sys

import grpc

from ansys.tools.common.launcher.helpers.grpc import check_grpc_health
from ansys.tools.common.launcher.helpers.ports import find_free_ports
from ansys.tools.common.launcher.interface import (
    METADATA_KEY_DOC,
    LauncherProtocol,
    ServerType,
)

SCRIPT_PATH = pathlib.Path(__file__).parent / "simple_test_server.py"
SERVER_KEY = "main"


@dataclasses.dataclass
class SimpleLauncherConfig:
    """Configuration for the SimpleLauncher."""

    script_path: str = dataclasses.field(
        default=str(SCRIPT_PATH),
        metadata={METADATA_KEY_DOC: "Location of the server Python script."},
    )


class SimpleLauncher(LauncherProtocol[SimpleLauncherConfig]):
    """Simple launcher for testing."""

    CONFIG_MODEL = SimpleLauncherConfig
    SERVER_SPEC = {SERVER_KEY: ServerType.GRPC}

    def __init__(self, *, config: SimpleLauncherConfig):
        """Initialize the SimpleLauncher with the given configuration."""
        self._script_path = config.script_path
        self._process: subprocess.Popen[str]
        self._url: str

    def start(self):
        """Start the service."""
        port = find_free_ports()[0]
        self._url = f"localhost:{port}"
        self._process = subprocess.Popen(
            [
                sys.executable,
                self._script_path,
                str(port),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )

    def stop(self, *, timeout=None):
        """Stop the service."""
        self._process.terminate()
        try:
            self._process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()

    def check(self, *, timeout: float | None = None) -> bool:
        """Check if the server is responding to requests."""
        channel = grpc.insecure_channel(self.urls[SERVER_KEY])
        return check_grpc_health(channel, timeout=timeout)

    @property
    def urls(self):
        """Return the URLs of the server."""
        return {SERVER_KEY: self._url}
