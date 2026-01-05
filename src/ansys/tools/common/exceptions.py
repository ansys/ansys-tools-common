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
"""Exceptions module."""


class AnsysError(Exception):
    """Base class for all exceptions raised by the Ansys API.

    You can use this base class to catch all Ansys-related exceptions.
    """

    def __init__(self, message: str) -> None:
        """Initialize the exception with a message."""
        super().__init__(message)
        self.message = message


class ProductInstanceError(AnsysError):
    """Custom exception for ProductInstance lifecycle errors."""


class AnsysHostnameValueError(AnsysError):
    """Error raised when hostname value is not valid."""

    def __init__(self, msg):
        """Initialize the exception.

        Parameters
        ----------
        msg : str
            The message to be raised for the exception.

        """
        super().__init__(msg)


class AnsysPortValueError(AnsysError):
    """Error raised when port value is not valid."""

    def __init__(self, msg):
        """Initialize the exception.

        Parameters
        ----------
        msg : str
            The message to be raised for the exception.

        """
        super().__init__(msg)


class AnsysTypeError(AnsysError):
    """Error raised when an argument is of the wrong type.

    This exception is raised when Python-wise types would work, but internal
    Ansys-specific typing is not right.

    Parameters
    ----------
    expected_type : str | type
        Expected type of the argument.
    actual_type : str | type
        Actual type of the argument.
    """

    def __init__(self, expected_type: str | type, actual_type: str | type = None) -> None:
        """Initialize the exception with expected and actual types."""
        expected_type = expected_type if isinstance(expected_type, str) else expected_type.__name__
        actual_type = actual_type if isinstance(actual_type, str) else actual_type.__name__
        message = f"Expected type {expected_type}, but got {actual_type}."
        super().__init__(message)
        self.expected_type = expected_type
        self.actual_type = actual_type


class AnsysLogicError(AnsysError):
    """Exception raised when an unexpected logical condition occurs.

    Parameters
    ----------
    message : str
        Error message.
    """

    def __init__(self, message: str) -> None:
        """Initialize the exception with a message."""
        super().__init__(message)


class VersionSyntaxError(AnsysError):
    """An exception raised when an invalid version syntax is found."""

    def __init__(self, msg):
        """Initialize the exception.

        Parameters
        ----------
        msg : str
            Message to raise for the exception.

        """
        super().__init__(msg)


class VersionError(AnsysError):
    """An exception raised when a version is not valid."""

    def __init__(self, msg):
        """Initialize the exception.

        Parameters
        ----------
        msg : str
            Message to raise for the exception.

        """
        super().__init__(msg)
