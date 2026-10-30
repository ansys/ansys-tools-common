# Copyright (C) 2025 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for licensing module tool discovery (Phase 2 - T4, T5).

Test cases:
- TC-4.1.x: find_lmutil tests
- TC-4.2.x: find_ansysli_util tests
- TC-4.3.x: Module export tests
"""

import os
from pathlib import Path

import pytest

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def fake_ansys_installation(fs, monkeypatch):
    """Create a fake Ansys installation with licensing tools.

    Parameters
    ----------
    fs : pyfakefs.fake_filesystem.FakeFilesystem
        The fake filesystem fixture from pyfakefs.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    callable
        A factory function to create fake installations.
    """

    def _create(version=251, include_lmutil=True, include_ansysli_util=True):
        if os.name == "nt":
            awp_root = Path(f"C:\\Program Files\\ANSYS Inc\\v{version}")
            tool_dir = awp_root / "licensingclient" / "winx64"
            lmutil_name = "lmutil.exe"
            ansysli_name = "ansysli_util.exe"
        else:
            awp_root = Path(f"/usr/ansys_inc/v{version}")
            tool_dir = awp_root / "licensingclient" / "linx64"
            lmutil_name = "lmutil"
            ansysli_name = "ansysli_util"

        fs.create_dir(str(tool_dir))

        if include_lmutil:
            fs.create_file(str(tool_dir / lmutil_name))
        if include_ansysli_util:
            fs.create_file(str(tool_dir / ansysli_name))

        monkeypatch.setenv(f"AWP_ROOT{version}", str(awp_root))
        return str(awp_root)

    return _create


@pytest.fixture
def clear_awp_env(monkeypatch):
    """Clear all AWP_ROOT environment variables."""
    # Common version numbers to clear
    versions = [251, 252, 261, 242, 241, 232, 231, 222, 221, 212, 211]
    for ver in versions:
        monkeypatch.delenv(f"AWP_ROOT{ver}", raising=False)


# =============================================================================
# TC-4.1: find_lmutil Tests
# =============================================================================


def test_find_lmutil_no_version(fake_ansys_installation):
    """TC-4.1.1: Find lmutil without specifying version - uses latest available."""
    from ansys.tools.common.licensing import find_lmutil

    fake_ansys_installation(version=251)

    path, version = find_lmutil()

    assert path != ""
    assert version == 25.1
    assert "lmutil" in path.lower()


def test_find_lmutil_specific_version(fake_ansys_installation):
    """TC-4.1.2: Find lmutil for a specific Ansys version."""
    from ansys.tools.common.licensing import find_lmutil

    fake_ansys_installation(version=251)
    fake_ansys_installation(version=242)

    path, version = find_lmutil(version=242)

    assert path != ""
    assert version == 24.2
    assert "242" in path or "v242" in path


def test_find_lmutil_float_version(fake_ansys_installation):
    """TC-4.1.3: Find lmutil using float version format (25.1 instead of 251)."""
    from ansys.tools.common.licensing import find_lmutil

    fake_ansys_installation(version=251)

    path, version = find_lmutil(version=25.1)

    assert path != ""
    assert version == 25.1


def test_find_lmutil_no_installation(fs, clear_awp_env):
    """TC-4.1.4: Return empty tuple when no Ansys installation found."""
    from ansys.tools.common.licensing import find_lmutil

    # fs fixture provides an empty fake filesystem, isolating from real installations
    path, version = find_lmutil()

    assert path == ""
    assert version == ""


def test_find_lmutil_missing_executable(fake_ansys_installation):
    """TC-4.1.5: Return empty tuple when Ansys installed but lmutil not present."""
    from ansys.tools.common.licensing import find_lmutil

    # Create installation without lmutil
    fake_ansys_installation(version=251, include_lmutil=False)

    path, version = find_lmutil()

    assert path == ""
    assert version == ""


def test_find_lmutil_correct_path_structure(fake_ansys_installation):
    """TC-4.1.6/7: Verify correct path structure for the platform."""
    from ansys.tools.common.licensing import find_lmutil

    fake_ansys_installation(version=251)

    path, _ = find_lmutil()

    assert "licensingclient" in path
    if os.name == "nt":
        assert "winx64" in path
        assert path.endswith("lmutil.exe")
    else:
        assert "linx64" in path
        assert path.endswith("lmutil")


def test_find_lmutil_multiple_installations(fake_ansys_installation):
    """TC-4.1.8: When multiple versions installed, return latest if no version specified."""
    from ansys.tools.common.licensing import find_lmutil

    fake_ansys_installation(version=241)
    fake_ansys_installation(version=251)
    fake_ansys_installation(version=242)

    path, version = find_lmutil()

    # Should return the latest version (251)
    assert version == 25.1
    assert "251" in path or "v251" in path


# =============================================================================
# TC-4.2: find_ansysli_util Tests
# =============================================================================


def test_find_ansysli_util_no_version(fake_ansys_installation):
    """TC-4.2.1: Find ansysli_util without specifying version."""
    from ansys.tools.common.licensing import find_ansysli_util

    fake_ansys_installation(version=251)

    path, version = find_ansysli_util()

    assert path != ""
    assert version == 25.1
    assert "ansysli_util" in path.lower()


def test_find_ansysli_util_specific_version(fake_ansys_installation):
    """TC-4.2.2: Find ansysli_util for a specific Ansys version."""
    from ansys.tools.common.licensing import find_ansysli_util

    fake_ansys_installation(version=251)
    fake_ansys_installation(version=242)

    path, version = find_ansysli_util(version=242)

    assert path != ""
    assert version == 24.2


def test_find_ansysli_util_not_found(fs, clear_awp_env):
    """TC-4.2.3: Return empty tuple when ansysli_util not found."""
    from ansys.tools.common.licensing import find_ansysli_util

    # fs fixture provides an empty fake filesystem, isolating from real installations
    path, version = find_ansysli_util()

    assert path == ""
    assert version == ""


def test_find_ansysli_util_correct_path_structure(fake_ansys_installation):
    """TC-4.2.4/5: Verify correct path structure for the platform."""
    from ansys.tools.common.licensing import find_ansysli_util

    fake_ansys_installation(version=251)

    path, _ = find_ansysli_util()

    assert "licensingclient" in path
    if os.name == "nt":
        assert "winx64" in path
        assert path.endswith("ansysli_util.exe")
    else:
        assert "linx64" in path
        assert path.endswith("ansysli_util")


def test_find_ansysli_util_missing_executable(fake_ansys_installation):
    """Return empty tuple when Ansys installed but ansysli_util not present."""
    from ansys.tools.common.licensing import find_ansysli_util

    # Create installation without ansysli_util
    fake_ansys_installation(version=251, include_ansysli_util=False)

    path, version = find_ansysli_util()

    assert path == ""
    assert version == ""


# =============================================================================
# TC-4.3: Module Export Tests
# =============================================================================


def test_tools_exported_from_module():
    """TC-4.3.1: Verify tool functions are exported from licensing module."""
    from ansys.tools.common.licensing import find_ansysli_util, find_lmutil

    assert callable(find_lmutil)
    assert callable(find_ansysli_util)


def test_tools_in_module_all():
    """Verify tool functions are in __all__."""
    from ansys.tools.common import licensing

    assert "find_lmutil" in licensing.__all__
    assert "find_ansysli_util" in licensing.__all__
