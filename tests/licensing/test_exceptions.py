# Copyright (C) 2025 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for licensing module exceptions (Phase 1 - T3).

Test cases:
- TC-3.1 through TC-3.5: Exception hierarchy and behavior tests
"""

import pytest

# =============================================================================
# TC-3.1: LicenseError Base Exception Tests
# =============================================================================


def test_license_error_inheritance():
    """TC-3.1a: Test LicenseError inherits from AnsysError."""
    from ansys.tools.common.exceptions import AnsysError, LicenseError

    assert issubclass(LicenseError, AnsysError)


def test_license_error_raise():
    """TC-3.1b: Test LicenseError can be raised and caught."""
    from ansys.tools.common.exceptions import LicenseError

    with pytest.raises(LicenseError) as exc_info:
        raise LicenseError("Test license error")

    assert "Test license error" in str(exc_info.value)


# =============================================================================
# TC-3.2: LicenseServerError Exception Tests
# =============================================================================


def test_license_server_error_inheritance():
    """TC-3.2a: Test LicenseServerError inherits from LicenseError."""
    from ansys.tools.common.exceptions import LicenseError, LicenseServerError

    assert issubclass(LicenseServerError, LicenseError)


def test_license_server_error_raise():
    """TC-3.2b: Test LicenseServerError can be raised and caught as base class."""
    from ansys.tools.common.exceptions import LicenseError, LicenseServerError

    with pytest.raises(LicenseError):  # Can catch as base class
        raise LicenseServerError("Server unreachable")


def test_license_server_error_message():
    """TC-3.2c: Test LicenseServerError with detailed message."""
    from ansys.tools.common.exceptions import LicenseServerError

    with pytest.raises(LicenseServerError) as exc_info:
        raise LicenseServerError("Cannot connect to 1055@server: Connection refused")

    assert "1055@server" in str(exc_info.value)


# =============================================================================
# TC-3.3: LicenseToolNotFoundError Exception Tests
# =============================================================================


def test_license_tool_not_found_error_inheritance():
    """TC-3.3a: Test LicenseToolNotFoundError inherits from LicenseError."""
    from ansys.tools.common.exceptions import LicenseError, LicenseToolNotFoundError

    assert issubclass(LicenseToolNotFoundError, LicenseError)


def test_license_tool_not_found_error_raise():
    """TC-3.3b: Test LicenseToolNotFoundError can be raised."""
    from ansys.tools.common.exceptions import LicenseToolNotFoundError

    with pytest.raises(LicenseToolNotFoundError) as exc_info:
        raise LicenseToolNotFoundError("lmutil not found in any Ansys installation")

    assert "lmutil" in str(exc_info.value)


# =============================================================================
# TC-3.4: LicenseFileParseError Exception Tests
# =============================================================================


def test_license_file_parse_error_inheritance():
    """TC-3.4a: Test LicenseFileParseError inherits from LicenseError."""
    from ansys.tools.common.exceptions import LicenseError, LicenseFileParseError

    assert issubclass(LicenseFileParseError, LicenseError)


def test_license_file_parse_error_raise():
    """TC-3.4b: Test LicenseFileParseError can be raised."""
    from ansys.tools.common.exceptions import LicenseFileParseError

    with pytest.raises(LicenseFileParseError) as exc_info:
        raise LicenseFileParseError("Invalid license file format at line 5")

    assert "line 5" in str(exc_info.value)


# =============================================================================
# TC-3.5: Exception Hierarchy Tests
# =============================================================================


def test_exception_hierarchy():
    """TC-3.5: Test complete exception hierarchy."""
    from ansys.tools.common.exceptions import (
        AnsysError,
        LicenseError,
        LicenseFileParseError,
        LicenseServerError,
        LicenseToolNotFoundError,
    )

    # All license exceptions should be catchable as LicenseError
    assert issubclass(LicenseServerError, LicenseError)
    assert issubclass(LicenseToolNotFoundError, LicenseError)
    assert issubclass(LicenseFileParseError, LicenseError)

    # All should ultimately inherit from AnsysError
    assert issubclass(LicenseError, AnsysError)
    assert issubclass(LicenseServerError, AnsysError)
    assert issubclass(LicenseToolNotFoundError, AnsysError)
    assert issubclass(LicenseFileParseError, AnsysError)


def test_catch_all_license_errors():
    """Test that all license exceptions can be caught with LicenseError."""
    from ansys.tools.common.exceptions import (
        LicenseError,
        LicenseFileParseError,
        LicenseServerError,
        LicenseToolNotFoundError,
    )

    exceptions_to_test = [
        LicenseServerError("server error"),
        LicenseToolNotFoundError("tool not found"),
        LicenseFileParseError("parse error"),
    ]

    for exc in exceptions_to_test:
        with pytest.raises(LicenseError):
            raise exc


def test_catch_all_as_ansys_error():
    """Test that all license exceptions can be caught with AnsysError."""
    from ansys.tools.common.exceptions import (
        AnsysError,
        LicenseError,
        LicenseFileParseError,
        LicenseServerError,
        LicenseToolNotFoundError,
    )

    exceptions_to_test = [
        LicenseError("base license error"),
        LicenseServerError("server error"),
        LicenseToolNotFoundError("tool not found"),
        LicenseFileParseError("parse error"),
    ]

    for exc in exceptions_to_test:
        with pytest.raises(AnsysError):
            raise exc
