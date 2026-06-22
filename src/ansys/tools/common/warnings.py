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
"""Warnings module."""


class AnsysWarning(Warning):
    """Base class for all warnings raised by the Ansys API.

    You can use this base class to catch all Ansys-related warnings.
    """

    def __init__(self, message: str) -> None:
        """Initialize the warning with a message."""
        super().__init__(message)


class DataNotAvailableWarning(AnsysWarning):
    """Warning raised when requested data is not yet available.

    This warning is typically issued when a property or method returns ``None``
    because the underlying data has not been computed or loaded yet.
    """


class ObjectCreationWarning(AnsysWarning):
    """Warning raised when an object is created with unavailable data.

    This warning is typically issued when an object is instantiated but some
    required data is missing, resulting in an incomplete object state.
    """


class ComputationNotPerformedWarning(AnsysWarning):
    """Warning raised when data is accessed before a required computation has run.

    This warning is typically issued when a property or method returns ``None``
    because the user has not yet called the required computation step (for
    example, ``.process()`` or ``.compute()``).
    """


class LicenseWarning(AnsysWarning):
    """Warning raised when a requested feature requires an unavailable license.

    This warning is typically issued when a feature is partially supported but
    a required license capability is not available, causing the operation to
    proceed in a degraded or limited mode.
    """


class ConnectionWarning(AnsysWarning):
    """Warning raised when a connection issue is detected but the operation continues.

    This warning is typically issued when a transient connection problem occurs
    (for example, a retry succeeded or a fallback server was used) and the
    operation was able to proceed despite the issue.
    """
