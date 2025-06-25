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
"""Conftest file."""

from copy import deepcopy

import pytest

from ansys.tools.common.versioning import requires_version

version_map = {
    (0, 2, 1): "20XYRZ",
}
"""A dictionary relating server version and their unified install versions."""


class MockupServer:
    """A testing class for modelling servers."""

    def __init__(self, server_version):
        """Initialize a server instance being known its version."""
        self._server_version = server_version

    @requires_version("0.2.1", version_map)
    def foo(self):
        """Call ``foo`` method in the server side."""
        pass

    @requires_version((0, 1, 0))
    def bar(self):
        """Call ``bar`` method in the server side."""
        pass


@pytest.fixture
def server_with_all_methods_available():
    """Mockup server with all methods available."""
    return MockupServer(server_version="1.0.0")


@pytest.fixture
def server_without_server_version_attribute(server_with_all_methods_available):
    """Mockup server without the `_server_version` attribute."""
    broken_server = deepcopy(server_with_all_methods_available)
    delattr(broken_server, "_server_version")
    return broken_server


@pytest.fixture
def server_with_outdated_foo_method():
    """Mockup server with an outdated `foo` method."""
    return MockupServer(server_version="0.2.0")


@pytest.fixture
def server_with_outdated_methods():
    """Mockup server with outdated methods."""
    return MockupServer(server_version=(0, 0, 1))
