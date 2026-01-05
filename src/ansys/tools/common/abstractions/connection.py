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
"""Module for abstract connection class."""

from abc import ABC, abstractmethod

try:
    import grpc
except ImportError:  # pragma: no cover
    import warnings

    warnings.warn(
        "grpc module is not available - reach out to the library maintainers to include it into their dependencies"
    )


class AbstractGRPCConnection(ABC):
    """Abstract class for managing gRPC connections.

    Parameters
    ----------
    host : str
        Host where the gRPC server is running.
    port : str
        Port where the gRPC server is listening.
    """

    @abstractmethod
    def __init__(self, host: str, port: str) -> None:
        """Initialize the gRPC connection with host and port."""
        pass  # pragma: no cover

    @abstractmethod
    def connect(self) -> None:
        """Establish a connection to the gRPC server."""
        pass  # pragma: no cover

    @abstractmethod
    def close(self) -> None:
        """Disconnect from the gRPC server."""
        pass  # pragma: no cover

    @property
    @abstractmethod
    def service(self):
        """GRPC stub for making requests."""
        pass  # pragma: no cover

    @property
    def _host(self) -> str:
        """Host for the gRPC connection."""
        return self.__host

    @_host.setter
    def _host(self, value: str) -> None:
        """Set the host for the gRPC connection."""
        self.__host = value

    @property
    def _port(self) -> str:
        """Return the port for the gRPC connection."""
        return self.__port

    @_port.setter
    def _port(self, value: str) -> None:
        """Set the port for the gRPC connection."""
        self.__port = value

    @property
    def _channel(self, options: list = None) -> grpc.Channel:
        """Return the gRPC channel."""
        return grpc.insecure_channel(f"{self._host}:{self._port}", options=options)

    @property
    def is_closed(self) -> bool:
        """Flag indicating if the connection is closed.

        Returns
        -------
        bool
            ``True`` if the connection is closed, ``False`` otherwise.
        """
        try:
            return self._channel._connectivity_state != grpc.ChannelConnectivity.READY
        except grpc.RpcError:
            return True
