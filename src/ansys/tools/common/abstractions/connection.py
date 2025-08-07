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
"""Module for abstract connection class."""

from abc import ABC, abstractmethod
import atexit
import random
from typing import Optional
import warnings

from ..exceptions import AnsysHostnameValueError, AnsysPortValueError

try:
    import grpc
except ImportError:  # pragma: no cover
    warnings.warn(
        "grpc module is not available - reach out to the library maintainers to include it into their dependencies"
    )


class AbstractGRPCConnection(ABC):
    """Abstract class for managing gRPC connections.

    Parameters
    ----------
    host : str
        The host where the gRPC server is running.
    port : str
        The port where the gRPC server is listening.
    """

    def __init__(self, host: str, port: str, **config) -> None:
        """Initialize the gRPC connection with host and port."""
        self._host = host
        self._port = port or str(random.randint(0, 65535))
        self._config = config

        # Validate properties using setters
        self.host = host
        self.port = port

        # Gracefully stop the server at exit if desired
        if self.stop_service_on_exit:
            atexit.register(self.service_stop)
        else:
            atexit.unregister(self.service_stop)
        atexit.register(self.close)

    @property
    def host(self) -> str:
        """Return the host for the gRPC connection."""
        return self._host

    @host.setter
    def host(self, value: str) -> None:
        """Set the host for the gRPC connection."""
        if value not in ["127.0.0.1", "localhost"]:
            if not self.allow_remote_host:
                raise AnsysHostnameValueError(
                    "Remote host connections are not permitted by default. "
                    "To enable connections to hosts other than localhost, set the "
                    "`allow_remote_host` property to `True`. "
                )
            warnings.warn(
                "Allowing remote access can expose the server to unauthorized "
                "connections and may transmit data over an unencrypted channel "
                "if the server is not properly configured."
            )
        self._host = value

    @property
    def port(self) -> str:
        """Return the port for the gRPC connection."""
        return self._port

    @port.setter
    def port(self, value: str) -> None:
        """Set the port for the gRPC connection."""
        port_value = int(value)
        if port_value < 0 or port_value > 65535:
            raise AnsysPortValueError("Port number must be in range from 0 to 65535")
        self._port = value

    @property
    def config(self) -> dict:
        """Return the configuration for the gRPC connection."""
        return self._config

    @config.setter
    def config(self, value: dict) -> None:
        """Return the configuration for the gRPC connection."""
        self._config = value

    @property
    def allow_remote_host(self) -> bool:
        """Return whether connections from remote hosts are allowed. Default is ``False``.

        .. warning::

            Remote host connections are not permitted by default.

            To enable connections to hosts other than localhost, set the
            ``allow_remote_host`` property to ``True``.

            Allowing remote access can expose the server to unauthorized
            connections and may transmit data over an unencrypted channel if
            the server is not properly configured.

        """
        return self._config.get("allow_remote_host", False)

    @allow_remote_host.setter
    def allow_remote_host(self, value: bool):
        """Set whether connections from remote hosts are allowed."""
        self._config["allow_remote_host"] = value

    @property
    def stop_service_on_exit(self) -> bool:
        """Return ``True`` if service must stop when the client disconnects. Returns ``False`` otherwise."""
        return self._config.get("stop_service_on_exit", True)

    @stop_service_on_exit.setter
    def stop_service_on_exit(self, value: bool):
        """Set whether the server must close when the client disconnects."""
        self._config["stop_service_on_exit"] = value

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
        """Return the gRPC stub for making requests."""
        pass  # pragma: no cover

    @abstractmethod
    def service_stop(self):
        """Stop the service."""
        pass  # pragma: no cover

    @property
    def channel_options(self) -> Optional[list]:
        """Return channel options."""
        return self._config.get("channel_options", None)

    @property
    def channel(self) -> grpc.Channel:
        """Return the gRPC channel."""
        return grpc.insecure_channel(f"{self.host}:{self.port}", options=self.channel_options)

    @property
    def is_closed(self) -> bool:
        """Check if the connection is closed.

        Returns
        -------
        bool
            True if the connection is closed, False otherwise.
        """
        try:
            return (
                self.channel._channel.check_connectivity_state(try_to_connect=False) != grpc.ChannelConnectivity.READY
            )
        except grpc.RpcError:
            self.close
            return True
