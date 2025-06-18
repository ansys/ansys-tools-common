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
"""Module for abstract launcher."""

from abc import ABC, abstractmethod


class AbstractServiceLauncher(ABC):
    """Abstract class for launching services.

    Parameters
    ----------
    host : str
        The host where the service will be launched.
    port : str
        The port where the service will be launched.
    """

    @abstractmethod
    def __init__(self, host: str, port: str) -> None:
        """Initialize the service launcher with host and port."""
        self._host = host
        self._port = port

    @abstractmethod
    def launch(self, use_docker: bool = False) -> None:
        """Launch the service.

        Parameters
        ----------
        use_docker : bool
            Whether to launch the service using Docker.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the service."""
        pass
