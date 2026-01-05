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

"""Interface definitions for implementing a local product launcher.

A plugin for the local product launcher must implement the :class:`LauncherProtocol` class and register it.
"""

from enum import Enum, auto
from typing import Any, ClassVar, Protocol, TypeVar

__all__ = [
    "DataclassProtocol",
    "FALLBACK_LAUNCH_MODE_NAME",
    "LAUNCHER_CONFIG_T",
    "LauncherProtocol",
    "METADATA_KEY_DOC",
    "METADATA_KEY_NOPROMPT",
    "ServerType",
]

METADATA_KEY_DOC = "launcher_doc"
"""Key used in the :py:class:`dataclasses.Field` ``metadata`` for the option description."""

METADATA_KEY_NOPROMPT = "launcher_noprompt"
"""
Key used in the :py:class:`dataclasses.Field` ``metadata`` to skip prompting for the option by default.
"""

FALLBACK_LAUNCH_MODE_NAME = "__fallback__"


class DataclassProtocol(Protocol):
    """Provides the ``Protocol`` class for Python dataclasses."""

    __dataclass_fields__: ClassVar[dict[str, Any]]


LAUNCHER_CONFIG_T = TypeVar("LAUNCHER_CONFIG_T", bound=DataclassProtocol)
# This docstring is commented-out because numpydoc causes the documentation build to fail when
# it is included.
# """Type variable for launcher configuration objects."""


class ServerType(Enum):
    """Defines which protocols the server supports.

    The ``ServerType`` class is used as values in the :attr:`LauncherProtocol.SERVER_SPEC`
    attribute to define the capabilities of the servers started with a given product and launch method.
    """

    GENERIC = auto()
    """Generic server, which responds at a given URL and port.

    The generic server type can be used for any server. It does not
    include information about which protocol should be used.
    """

    GRPC = auto()
    """Server that can be accessed via gRPC.

    Servers of this type are accessible via the :attr:`.ProductInstance.channels`
    attribute.
    """


class LauncherProtocol(Protocol[LAUNCHER_CONFIG_T]):
    """Provides the interface for managing a local product instance.

    A plugin to the local product launcher must implement the interface defined in this class.

    To check for compatibility, you should derive from this
    class. For example ``MyLauncher(LauncherProtocol[MyConfigModel])``.
    Check the resulting code with `Mypy <https://mypy.readthedocs.io>`_.

    The ``__init__`` method should accept exactly one keyword-only
    parameter: ``config``. Note that this is `not enforced by
    Mypy <https://bugs.python.org/issue44807>`_.

    Parameters
    ----------
    config :
        Configuration options used to start the product. This parameter must be an instance of ``CONFIG_MODEL``.
    """

    CONFIG_MODEL: type[LAUNCHER_CONFIG_T]
    """Defines the configuration options for the launcher.

    The configuration options that this launcher accepts, specified
    as a :py:func:`dataclass <dataclasses.dataclass>`. Note that
    the ``default`` and ``metadata[METADATA_KEY_DOC]`` of the
    fields are used in the configuration CLI, if available.
    """

    SERVER_SPEC: dict[str, ServerType]
    """Defines the server types that are started.

    Examples
    --------
    This code defines a server that is accessible via a URL
    at the ``"MAIN"`` key and a server accessible via gRPC
    at the ``"FILE_TRANSFER"`` key.

    .. code:: python

        SERVER_SPEC = {"MAIN": ServerType.GENERIC, "FILE_TRANSFER": ServerType.GRPC}

    The :attr:`.ProductInstance.urls` attribute then has keys
    ``{"MAIN", "FILE_TRANSFER"}``, whereas the
    :attr:`.ProductInstance.channels` attribute has only the
    key ``"FILE_TRANSFER"``.
    """

    def __init__(self, *, config: LAUNCHER_CONFIG_T):
        pass  # pragma: no cover

    def start(self) -> None:
        """Start the product instance."""

    def stop(self, *, timeout: float | None = None) -> None:
        """Stop the product instance.

        Parameters
        ----------
        timeout :
            Time after which the instance can be forcefully stopped.
            The timeout should be interpreted as a hint to the implementation.
            It is *not required* to trigger a force-shutdown, but the stop *must* return within a finite time.
        """

    def check(self, *, timeout: float | None = None) -> bool:
        """Check if the product instance is responding to requests.

        Parameters
        ----------
        timeout :
            Timeout in seconds for the check.
            The timeout should be interpreted as a hint to the implementation.
            It is *not required* to return within the given time,
            but the check *must* return within a finite time,
            meaning it must not hang indefinitely.

        Returns
        -------
        bool
            Whether the product instance is responding.
        """

    @property
    def urls(self) -> dict[str, str]:
        """Dictionary of URLs that the server is listening on.

        The keys of the returned dictionary must correspond
        to the keys defined in the
        :attr:`.LauncherProtocol.SERVER_SPEC` attribute.
        """
