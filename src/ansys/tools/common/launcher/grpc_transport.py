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

"""Defines options for connecting to a gRPC server."""

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
import enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

import grpc

from .. import cyberchannel

__all__ = [
    "TransportMode",
    "UDSOptions",
    "WNUAOptions",
    "MTLSOptions",
    "InsecureOptions",
    "TransportOptionsType",
]

# For Python 3.10 and below, emulate the behavior of StrEnum by
# inheriting from str and enum.Enum.
# Note that this does *not* work on Python 3.11+, since the default
# Enum format method has changed and will not return the value of
# the enum member.
# When type checking, always use the Python 3.10 workaround, otherwise
# the StrEnum resolves as 'Any'.
if TYPE_CHECKING:  # pragma: no cover

    class StrEnum(str, enum.Enum):
        """String enum."""

else:
    try:
        from enum import StrEnum
    except ImportError:
        import enum

        class StrEnum(str, enum.Enum):
            """String enum."""

            pass


class TransportMode(StrEnum):
    """Enumeration of supported gRPC transport modes."""

    UDS = "uds"
    WNUA = "wnua"
    MTLS = "mtls"
    INSECURE = "insecure"


class TransportOptionsBase(ABC):
    """Base class for transport options."""

    _MODE: ClassVar[TransportMode]

    @property
    def mode(self) -> TransportMode:
        """Transport mode."""
        return self._MODE

    def create_channel(self, **extra_kwargs: Any) -> grpc.Channel:
        """Create a gRPC channel using the transport options.

        Parameters
        ----------
        extra_kwargs :
            Extra keyword arguments to pass to the channel creation function.

        Returns
        -------
        :
            gRPC channel created using the transport options.
        """
        return cyberchannel.create_channel(**self._to_cyberchannel_kwargs(), **extra_kwargs)

    @abstractmethod
    def _to_cyberchannel_kwargs(self) -> dict[str, Any]:
        """Convert transport options to cyberchannel keyword arguments.

        Returns
        -------
        :
            Dictionary of keyword arguments for cyberchannel.
        """
        pass


@dataclass(kw_only=True)
class UDSOptions(TransportOptionsBase):
    """Options for UDS transport mode."""

    _MODE = TransportMode.UDS

    uds_service: str
    uds_dir: str | Path | None = None
    uds_id: str | None = None

    def _to_cyberchannel_kwargs(self) -> dict[str, Any]:
        return asdict(self) | {"transport_mode": self.mode.value}


@dataclass(kw_only=True)
class WNUAOptions(TransportOptionsBase):
    """Options for WNUA transport mode."""

    _MODE = TransportMode.WNUA

    port: int

    def _to_cyberchannel_kwargs(self) -> dict[str, Any]:
        return asdict(self) | {"transport_mode": self.mode.value, "host": "localhost"}


@dataclass(kw_only=True)
class MTLSOptions(TransportOptionsBase):
    """Options for mTLS transport mode."""

    _MODE = TransportMode.MTLS

    certs_dir: str | Path | None = None
    host: str = "localhost"
    port: int
    allow_remote_host: bool = False

    def _to_cyberchannel_kwargs(self) -> dict[str, Any]:
        if not self.allow_remote_host:
            if self.host not in ("localhost", "127.0.0.1"):
                raise ValueError(f"Remote host '{self.host}' specified without setting 'allow_remote_host=True'.")
        res = asdict(self)
        res.pop("allow_remote_host", None)
        return res | {"transport_mode": self.mode.value}


@dataclass(kw_only=True)
class InsecureOptions(TransportOptionsBase):
    """Options for insecure transport mode."""

    _MODE = TransportMode.INSECURE

    host: str = "localhost"
    port: int
    allow_remote_host: bool = False

    def _to_cyberchannel_kwargs(self) -> dict[str, Any]:
        if not self.allow_remote_host:
            if self.host not in ("localhost", "127.0.0.1"):
                raise ValueError(f"Remote host '{self.host}' specified without setting 'allow_remote_host=True'.")
        res = asdict(self)
        res.pop("allow_remote_host", None)
        return res | {"transport_mode": self.mode.value}


TransportOptionsType = UDSOptions | WNUAOptions | MTLSOptions | InsecureOptions
