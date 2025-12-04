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
import tempfile

from ansys.tools.common.launcher.grpc_transport import UDSOptions
from ansys.tools.common.launcher.helpers.grpc import check_grpc_health
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
    transport_options = UDSOptions(
        uds_service="simple_test_service",
    )


class SimpleLauncher(LauncherProtocol[SimpleLauncherConfig]):
    """Simple launcher for testing."""

    CONFIG_MODEL = SimpleLauncherConfig
    SERVER_SPEC = {SERVER_KEY: ServerType.GRPC}

    def __init__(self, *, config: SimpleLauncherConfig):
        """Initialize the SimpleLauncher with the given configuration."""
        self._script_path = config.script_path
        self._transport_options = config.transport_options
        if self._transport_options.mode != "uds":
            raise ValueError("Only UDS transport mode is supported by SimpleLauncher.")
        self._process: subprocess.Popen[str]
        self._url: str
        if self._transport_options.uds_dir is None:
            self._tmp_dir = tempfile.TemporaryDirectory()
            self._transport_options.uds_dir = self._tmp_dir.name

        self._uds_dir = self._transport_options.uds_dir
        self._uds_file = pathlib.Path(self._transport_options.uds_dir) / "simple_test_service.sock"
        self._url = f"unix:{self._uds_file}"

    def start(self):
        """Start the service."""
        self._process = subprocess.Popen(
            [
                sys.executable,
                self._script_path,
                str(self._uds_dir),
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
        # If the server failed to so, remove the UDS file. Graceful
        # shutdown on Windows does not appear to work reliably.
        self._uds_file.unlink(missing_ok=True)

    def check(self, *, timeout: float | None = None) -> bool:
        """Check if the server is responding to requests."""
        channel = self._transport_options.create_channel()
        return check_grpc_health(channel, timeout=timeout)

    @property
    def transport_options(self):
        """Return the transport options of the server."""
        return {SERVER_KEY: self._transport_options}
