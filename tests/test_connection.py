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

"""Module for testing gRPC connection abstraction."""

from unittest.mock import MagicMock

import pytest

from ansys.tools.common.abstractions.connection import AbstractGRPCConnection


class MockGRPCConnection(AbstractGRPCConnection):
    """Mock implementation of AbstractGRPCConnection for testing."""

    def __init__(self, host: str, port: str) -> None:
        """Initialize the mock gRPC connection."""
        self._host = host
        self._port = port
        self._connected = False

    def connect(self) -> None:
        """Connect to the mock gRPC server."""
        self._connected = True

    def close(self) -> None:
        """Close the mock gRPC connection."""
        self._connected = False

    @property
    def service(self):
        """Service property that returns a mock gRPC stub."""
        return MagicMock()

    @property
    def is_closed(self) -> bool:
        """Status of the connection."""
        return not self._connected


@pytest.fixture
def mock_connection():
    """Fixture for creating a mock gRPC connection."""
    return MockGRPCConnection(host="localhost", port="50051")


def test_initialization(mock_connection):
    """Test initialization of the connection."""
    assert mock_connection._host == "localhost"
    assert mock_connection._port == "50051"
    assert mock_connection.is_closed


def test_connect(mock_connection):
    """Test connecting to the gRPC server."""
    mock_connection.connect()
    assert not mock_connection.is_closed


def test_close(mock_connection):
    """Test disconnecting from the gRPC server."""
    mock_connection.connect()
    mock_connection.close()
    assert mock_connection.is_closed


def test_service_property(mock_connection):
    """Test the service property."""
    service = mock_connection.service
    assert service is not None
    assert isinstance(service, MagicMock)


def test_is_closed_property(mock_connection):
    """Test the is_closed property."""
    assert mock_connection.is_closed
    mock_connection.connect()
    assert not mock_connection.is_closed
    mock_connection.close()
    assert mock_connection.is_closed
