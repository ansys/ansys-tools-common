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

"""Module for exception testing."""

from ansys.tools.exceptions import AnsysError, AnsysLogicError, AnsysTypeError, VersionError, VersionSyntaxError


def test_ansys_error():
    """Test the base AnsysError exception."""
    try:
        raise AnsysError("This is a test error.")
    except AnsysError as e:
        assert str(e) == "This is a test error."
        assert e.message == "This is a test error."


def test_ansys_type_error():
    """Test the AnsysTypeError exception."""
    try:
        raise AnsysTypeError(expected_type="int", actual_type="str")
    except AnsysTypeError as e:
        assert str(e) == "Expected type int, but got str."
        assert e.expected_type == "int"
        assert e.actual_type == "str"

    try:
        raise AnsysTypeError(expected_type=int, actual_type=str)
    except AnsysTypeError as e:
        assert str(e) == "Expected type int, but got str."
        assert e.expected_type == "int"
        assert e.actual_type == "str"


def test_ansys_logic_error():
    """Test the AnsysLogicError exception."""
    try:
        raise AnsysLogicError("This is a logic error.")
    except AnsysLogicError as e:
        assert str(e) == "This is a logic error."
        assert e.message == "This is a logic error."


def test_version_error():
    """Test the VersionError exception."""
    try:
        raise VersionError("This is a version error.")
    except VersionError as e:
        assert str(e) == "This is a version error."
        assert e.message == "This is a version error."


def test_version_syntax_error():
    """Test the VersionSyntaxError exception."""
    try:
        raise VersionSyntaxError("This is a version syntax error.")
    except VersionSyntaxError as e:
        assert str(e) == "This is a version syntax error."
        assert e.message == "This is a version syntax error."
