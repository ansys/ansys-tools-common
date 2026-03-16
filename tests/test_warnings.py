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

"""Module for warnings testing."""

import warnings

import pytest

from ansys.tools.common.warnings import (
    AnsysWarning,
    ComputationNotPerformedWarning,
    ConnectionWarning,
    DataNotAvailableWarning,
    LicenseWarning,
    ObjectCreationWarning,
)


def test_ansys_warning():
    """Test the base AnsysWarning warning."""
    with pytest.warns(AnsysWarning, match="Base warning test"):
        warnings.warn(AnsysWarning("Base warning test"))


def test_ansys_warning_message_attribute():
    """Test that AnsysWarning stores the message attribute."""
    w = AnsysWarning("some message")
    assert w.message == "some message"
    assert str(w) == "some message"


def test_data_not_available_warning():
    """Test the DataNotAvailableWarning warning."""
    with pytest.warns(DataNotAvailableWarning, match="Data not available"):
        warnings.warn(DataNotAvailableWarning("Data not available"))


def test_object_creation_warning():
    """Test the ObjectCreationWarning warning."""
    with pytest.warns(ObjectCreationWarning, match="Object creation issue"):
        warnings.warn(ObjectCreationWarning("Object creation issue"))


def test_computation_not_performed_warning():
    """Test the ComputationNotPerformedWarning warning."""
    with pytest.warns(ComputationNotPerformedWarning, match="Computation not performed"):
        warnings.warn(ComputationNotPerformedWarning("Computation not performed"))


def test_license_warning():
    """Test the LicenseWarning warning."""
    with pytest.warns(LicenseWarning, match="License unavailable"):
        warnings.warn(LicenseWarning("License unavailable"))


def test_connection_warning():
    """Test the ConnectionWarning warning."""
    with pytest.warns(ConnectionWarning, match="Connection issue detected"):
        warnings.warn(ConnectionWarning("Connection issue detected"))
