# Copyright (C) 2025 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for the licensing diagnosis module."""

import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from ansys.tools.common.exceptions import LicenseServerError, LicenseToolNotFoundError
from ansys.tools.common.licensing import (
    FeatureInfo,
    LicenseServerStatus,
    check_feature,
    check_license_server_status,
    check_license_server_status_all,
)

# Sample lmstat output fixtures
LMSTAT_SERVER_UP = """lmutil - Copyright (c) 1989-2023 Flexera.

License server status: 1055@license-server.example.com
    License file(s) on license-server.example.com: /opt/ansys/license/license.lic:

license-server.example.com: license server UP (MASTER) v11.18.1

Vendor daemon status (on license-server.example.com):

    ansyslmd: UP v11.18.1
"""

LMSTAT_SERVER_DOWN = """lmutil - Copyright (c) 1989-2023 Flexera.

License server status: 1055@license-server.example.com
    Cannot connect to license server system.
    The license server manager (lmgrd) has not been started yet.
"""

LMSTAT_WITH_FEATURES = """lmutil - Copyright (c) 1989-2023 Flexera.

License server status: 1055@license-server.example.com

license-server.example.com: license server UP (MASTER) v11.18.1

Vendor daemon status:
    ansyslmd: UP v11.18.1

Feature usage info:

Users of mechanical_enterprise:  (Total of 10 licenses issued;  Total of 3 licenses in use)
  user1@host1 v25.0 (license-server/1055 101), start Tue 10/15 10:30
  user2@host2 v25.0 (license-server/1055 102), start Tue 10/15 11:00
  user3@host3 v25.0 (license-server/1055 103), start Tue 10/15 11:15

Users of structural_analysis:  (Total of 5 licenses issued;  Total of 0 licenses in use)

Users of fluent_solver:  (Total of 20 licenses issued;  Total of 15 licenses in use)
"""

LMSTAT_VENDOR_DOWN = """lmutil - Copyright (c) 1989-2023 Flexera.

License server status: 1055@license-server.example.com

license-server.example.com: license server UP (MASTER) v11.18.1

Vendor daemon status:
    ansyslmd: DOWN
"""

LMSTAT_SINGLE_FEATURE = """lmutil - Copyright (c) 1989-2023 Flexera.

License server status: 1055@license-server.example.com

license-server.example.com: license server UP (MASTER) v11.18.1

Vendor daemon status:
    ansyslmd: UP v11.18.1

Feature usage info:

Users of mechanical_enterprise:  (Total of 10 licenses issued;  Total of 3 licenses in use)
"""

LMSTAT_UNCOUNTED_FEATURE = """lmutil - Copyright (c) 1989-2023 Flexera.

License server status: 1055@license-server.example.com

license-server.example.com: license server UP (MASTER) v11.18.1

Vendor daemon status:
    ansyslmd: UP v11.18.1

Feature usage info:

Users of node_locked_feature:  (Uncounted, node-locked)
"""

LMSTAT_FEATURE_NOT_FOUND = """lmutil - Copyright (c) 1989-2023 Flexera.

License server status: 1055@license-server.example.com

license-server.example.com: license server UP (MASTER) v11.18.1

Vendor daemon status:
    ansyslmd: UP v11.18.1

Feature usage info:

"""


def _get_test_lmutil_path():
    """Get platform-appropriate test lmutil path as a tuple (path, version)."""
    if os.name == "nt":
        return ("C:\\Program Files\\ANSYS Inc\\v261\\licensingclient\\winx64\\lmutil.exe", 26.1)
    return ("/opt/ansys/v261/licensingclient/linx64/lmutil", 26.1)


class TestGetLicenseServerStatusBasic:
    """TC-16.1: Basic status tests."""

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_get_status_server_up(self, mock_run, mock_find_lmutil):
        """TC-16.1.1: Server is up and responding."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_SERVER_UP, stderr="", returncode=0)

        status = check_license_server_status_all(server="1055@license-server.example.com")

        assert isinstance(status, LicenseServerStatus)
        assert status.is_up is True

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_get_status_server_down(self, mock_run, mock_find_lmutil):
        """TC-16.1.2: Server is down."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_SERVER_DOWN, stderr="", returncode=1)

        status = check_license_server_status_all(server="1055@license-server.example.com")

        assert status.is_up is False

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_get_status_vendor_up(self, mock_run, mock_find_lmutil):
        """TC-16.1.3: Vendor daemon is up."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_SERVER_UP, stderr="", returncode=0)

        status = check_license_server_status_all(server="1055@license-server.example.com")

        assert status.vendor_daemon_up is True

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_get_status_vendor_down(self, mock_run, mock_find_lmutil):
        """TC-16.1.4: Vendor daemon is down."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_VENDOR_DOWN, stderr="", returncode=0)

        status = check_license_server_status_all(server="1055@license-server.example.com")

        assert status.vendor_daemon_up is False

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_get_status_with_features(self, mock_run, mock_find_lmutil):
        """TC-16.1.5: Status includes features."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_WITH_FEATURES, stderr="", returncode=0)

        status = check_license_server_status_all(server="1055@license-server.example.com")

        assert len(status.features) == 3
        assert "mechanical_enterprise" in status.features
        assert "structural_analysis" in status.features
        assert "fluent_solver" in status.features

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_get_status_raw_output(self, mock_run, mock_find_lmutil):
        """TC-16.1.6: Preserves raw output."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_SERVER_UP, stderr="", returncode=0)

        status = check_license_server_status_all(server="1055@license-server.example.com")

        assert LMSTAT_SERVER_UP in status.raw_output


class TestGetLicenseServerStatusServerParam:
    """TC-16.2: Server parameter tests."""

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_get_status_explicit_server(self, mock_run, mock_find_lmutil):
        """TC-16.2.1: Use explicit server."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_SERVER_UP, stderr="", returncode=0)

        status = check_license_server_status_all(server="1055@myhost")

        assert status.server == "1055@myhost"

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("ansys.tools.common.licensing.diagnosis.get_license_server")
    @patch("subprocess.run")
    def test_get_status_from_env(self, mock_run, mock_get_server, mock_find_lmutil):
        """TC-16.2.2: Use server from environment."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_get_server.return_value = "1055@env-server"
        mock_run.return_value = MagicMock(stdout=LMSTAT_SERVER_UP, stderr="", returncode=0)

        status = check_license_server_status_all(server=None)

        assert status.server == "1055@env-server"

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("ansys.tools.common.licensing.diagnosis.get_license_server")
    def test_get_status_no_server(self, mock_get_server, mock_find_lmutil):
        """TC-16.2.3: No server available."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_get_server.return_value = None

        with pytest.raises(LicenseServerError, match="No license server"):
            check_license_server_status_all(server=None)

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_get_status_server_format(self, mock_run, mock_find_lmutil):
        """TC-16.2.4: Correct port@host format in command."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_SERVER_UP, stderr="", returncode=0)

        check_license_server_status_all(server="1055@host")

        # Verify the command was called with correct server format
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "1055@host" in cmd


class TestGetLicenseServerStatusToolDiscovery:
    """TC-16.3: Tool discovery tests."""

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_get_status_finds_lmutil(self, mock_run, mock_find_lmutil):
        """TC-16.3.1: Finds lmutil automatically."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_SERVER_UP, stderr="", returncode=0)

        check_license_server_status_all(server="1055@host")

        mock_find_lmutil.assert_called_once()

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    def test_get_status_no_lmutil(self, mock_find_lmutil):
        """TC-16.3.2: lmutil not found."""
        mock_find_lmutil.return_value = ("", "")

        with pytest.raises(LicenseToolNotFoundError, match="lmutil not found"):
            check_license_server_status_all(server="1055@host")


class TestGetLicenseServerStatusOutputParsing:
    """TC-16.4: Output parsing tests."""

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_parse_lmstat_output_features(self, mock_run, mock_find_lmutil):
        """TC-16.4.1: Parse feature info."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_WITH_FEATURES, stderr="", returncode=0)

        status = check_license_server_status_all(server="1055@host")

        assert len(status.features) == 3

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_parse_lmstat_feature_in_use(self, mock_run, mock_find_lmutil):
        """TC-16.4.2: Parse in-use counts."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_WITH_FEATURES, stderr="", returncode=0)

        status = check_license_server_status_all(server="1055@host")

        mech_feature = status.features["mechanical_enterprise"]
        assert mech_feature.in_use == 3

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_parse_lmstat_feature_total(self, mock_run, mock_find_lmutil):
        """TC-16.4.3: Parse total counts."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_WITH_FEATURES, stderr="", returncode=0)

        status = check_license_server_status_all(server="1055@host")

        mech_feature = status.features["mechanical_enterprise"]
        assert mech_feature.total == 10

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_parse_lmstat_multiple_features(self, mock_run, mock_find_lmutil):
        """TC-16.4.4: Parse multiple features."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_WITH_FEATURES, stderr="", returncode=0)

        status = check_license_server_status_all(server="1055@host")

        # Verify all features parsed correctly
        fluent = status.features["fluent_solver"]
        assert fluent.total == 20
        assert fluent.in_use == 15

        structural = status.features["structural_analysis"]
        assert structural.total == 5
        assert structural.in_use == 0


class TestCheckFeature:
    """TC-16.5: check_feature tests."""

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_check_feature_available(self, mock_run, mock_find_lmutil):
        """TC-16.5.1: Feature is available."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_SINGLE_FEATURE, stderr="", returncode=0)

        info = check_feature("mechanical_enterprise", server="1055@host")

        assert info is not None
        assert isinstance(info, FeatureInfo)
        assert info.total == 10

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_check_feature_in_use(self, mock_run, mock_find_lmutil):
        """TC-16.5.2: Feature partially used."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_SINGLE_FEATURE, stderr="", returncode=0)

        info = check_feature("mechanical_enterprise", server="1055@host")

        assert info is not None
        assert info.in_use == 3

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_check_feature_exhausted(self, mock_run, mock_find_lmutil):
        """TC-16.5.3: All licenses in use."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        exhausted_output = LMSTAT_SINGLE_FEATURE.replace("Total of 3 licenses in use", "Total of 10 licenses in use")
        mock_run.return_value = MagicMock(stdout=exhausted_output, stderr="", returncode=0)

        info = check_feature("mechanical_enterprise", server="1055@host")

        assert info is not None
        assert info.in_use == info.total

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_check_feature_not_found(self, mock_run, mock_find_lmutil):
        """TC-16.5.4: Feature doesn't exist."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_FEATURE_NOT_FOUND, stderr="", returncode=0)

        info = check_feature("nonexistent_feature", server="1055@host")

        assert info is None

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_check_feature_uncounted(self, mock_run, mock_find_lmutil):
        """TC-16.5.5: Uncounted license."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_UNCOUNTED_FEATURE, stderr="", returncode=0)

        info = check_feature("node_locked_feature", server="1055@host")

        assert info is not None
        assert info.total == -1  # -1 indicates uncounted

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_check_feature_explicit_server(self, mock_run, mock_find_lmutil):
        """TC-16.5.6: Check with explicit server."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_SINGLE_FEATURE, stderr="", returncode=0)

        check_feature("mechanical_enterprise", server="1055@explicit-host")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "1055@explicit-host" in cmd


class TestPingLicenseServer:
    """TC-16.6: check_license_server_status tests."""

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_connection_success(self, mock_run, mock_find_lmutil):
        """TC-16.6.1: Connection succeeds."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_SERVER_UP, stderr="", returncode=0)

        result = check_license_server_status("1055@host")

        assert result.lmgrd_up is True
        assert result.vendor_daemon_up is True
        assert result.server == "1055@host"
        assert result.error_message is None

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_connection_failure(self, mock_run, mock_find_lmutil):
        """TC-16.6.2: Connection fails."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_SERVER_DOWN, stderr="", returncode=1)

        result = check_license_server_status("1055@host")

        assert result.lmgrd_up is False
        assert result.vendor_daemon_up is False
        assert result.error_message is not None

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_connection_timeout(self, mock_run, mock_find_lmutil):
        """TC-16.6.3: Connection times out."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="lmstat", timeout=10)

        result = check_license_server_status("1055@host", timeout=10)

        assert result.lmgrd_up is False
        assert result.vendor_daemon_up is False
        assert result.error_type == "timeout"
        assert "timed out" in result.error_message

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    def test_connection_no_lmutil(self, mock_find_lmutil):
        """TC-16.6.4: lmutil not found."""
        mock_find_lmutil.return_value = ("", "")

        result = check_license_server_status("1055@host")

        assert result.lmgrd_up is False
        assert result.vendor_daemon_up is False
        assert result.error_type == "lmutil_not_found"


class TestErrorHandling:
    """TC-16.7: Error handling tests."""

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_subprocess_error(self, mock_run, mock_find_lmutil):
        """TC-16.7.1: lmutil command fails with OSError."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.side_effect = OSError("Command not found")

        with pytest.raises(LicenseServerError, match="Failed to execute"):
            check_license_server_status_all(server="1055@host")

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_timeout_error(self, mock_run, mock_find_lmutil):
        """TC-16.7.2: Command times out."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="lmstat", timeout=30)

        with pytest.raises(LicenseServerError, match="timed out"):
            check_license_server_status_all(server="1055@host")

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_parse_error_graceful(self, mock_run, mock_find_lmutil):
        """TC-16.7.3: Unexpected output format handled gracefully."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout="Unexpected gibberish output", stderr="", returncode=0)

        # Should not raise, just return empty/default values
        status = check_license_server_status_all(server="1055@host")

        assert status.is_up is False  # Can't confirm it's up
        assert status.features == {}

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_connection_refused_error(self, mock_run, mock_find_lmutil):
        """TC-16.7.4: Connection refused error stores helpful message in status."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        connection_refused_output = """lmutil - Copyright (c) 1989-2025 Flexera. All Rights Reserved.
Flexible License Manager status on Wed 10/28/2026 12:40

[Detecting lmgrd processes...]
Error getting status: Cannot connect to license server system. (-15,10:10061 "WinSock: Connection refused")
"""
        mock_run.return_value = MagicMock(stdout=connection_refused_output, stderr="", returncode=1)

        status = check_license_server_status_all(server="1055@license-server.example.com")

        assert status.is_up is False
        assert status.error_message is not None
        assert "cannot be connected" in status.error_message

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_connection_refused_error_message_contains_server(self, mock_run, mock_find_lmutil):
        """TC-16.7.5: Connection refused error includes server name."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        connection_refused_output = """lmutil - Copyright (c) 1989-2025 Flexera. All Rights Reserved.
Error getting status: Cannot connect to license server system. (-15,10:10061 "WinSock: Connection refused")
"""
        mock_run.return_value = MagicMock(stdout=connection_refused_output, stderr="", returncode=1)

        status = check_license_server_status_all(server="1055@license-server.example.com")

        assert status.error_message is not None
        assert "license-server.example.com" in status.error_message

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_host_not_found_error(self, mock_run, mock_find_lmutil):
        """TC-16.7.6: Host not found error stores helpful DNS message in status."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        host_not_found_output = """lmutil - Copyright (c) 1989-2025 Flexera. All Rights Reserved.
Flexible License Manager status on Wed 10/28/2026 12:42

[Detecting lmgrd processes...]
Error getting status: License server machine is down or not responding. (-96,7:11001 "WinSock: Host not found (HOST_NOT_FOUND)")
"""  # noqa: E501
        mock_run.return_value = MagicMock(stdout=host_not_found_output, stderr="", returncode=1)

        status = check_license_server_status_all(server="1055@unknown-server")

        assert status.is_up is False
        assert status.error_message is not None
        assert "cannot be resolved into a valid IP address" in status.error_message

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_host_not_found_error_message_contains_server(self, mock_run, mock_find_lmutil):
        """TC-16.7.7: Host not found error includes server name and DNS hint."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        host_not_found_output = """lmutil - Copyright (c) 1989-2025 Flexera. All Rights Reserved.
Error getting status: License server machine is down or not responding. (-96,7:11001 "WinSock: Host not found (HOST_NOT_FOUND)")
"""  # noqa: E501
        mock_run.return_value = MagicMock(stdout=host_not_found_output, stderr="", returncode=1)

        status = check_license_server_status_all(server="1055@unknown-server")

        assert status.error_message is not None
        assert "unknown-server" in status.error_message
        assert "DNS" in status.error_message

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_no_error_message_when_server_up(self, mock_run, mock_find_lmutil):
        """TC-16.7.8: No error message when server is up."""
        mock_find_lmutil.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=LMSTAT_SERVER_UP, stderr="", returncode=0)

        status = check_license_server_status_all(server="1055@license-server.example.com")

        assert status.is_up is True
        assert status.error_message is None


class TestServerModuleExports:
    """TC-16.8: Test that server functions are properly exported."""

    def test_check_license_server_status_all_exported(self):
        """TC-16.8.1: check_license_server_status_all should be importable."""
        from ansys.tools.common.licensing import check_license_server_status_all

        assert callable(check_license_server_status_all)

    def test_check_feature_exported(self):
        """check_feature should be importable."""
        from ansys.tools.common.licensing import check_feature

        assert callable(check_feature)

    def test_check_license_server_status_exported(self):
        """check_license_server_status should be importable."""
        from ansys.tools.common.licensing import check_license_server_status

        assert callable(check_license_server_status)

    def test_server_functions_in_all(self):
        """Server functions should be in __all__."""
        from ansys.tools.common import licensing

        assert "check_license_server_status_all" in licensing.__all__
        assert "check_feature" in licensing.__all__
        assert "check_license_server_status" in licensing.__all__
        assert "test_license_checkout" in licensing.__all__


# Sample ansysli_util output fixtures for checkout tests
CHECKOUT_SUCCESS_OUTPUT = """ansysli_util: License checkout successful for feature: mechanical_enterprise
"""

CHECKOUT_CONNECTION_ERROR_OUTPUT = """
 ANSYS LICENSE MANAGER ERROR : Cannot connect to license server system.
 The license server manager (lmgrd) has not been started yet,
 the wrong port@host or license file is being used, or the
 port or hostname in the license file has been changed.
Feature: ansys
Server name: 65.8.70.45
License path: 1055@abc.com;1055@localhost;
FlexNet Licensing error:-15,10032

ansys CHECKOUT FAILED
"""

CHECKOUT_VENDOR_DOWN_OUTPUT = """
ANSYS LICENSE MANAGER ERROR : The desired vendor daemon is down.
 Check the lmgrd log file, or try lmreread.
Feature: ansys
Vendor:Host: 10.45.16.188
License path: 1055@10.45.16.188:
FlexNet Licensing error:-97,121

ansys CHECKOUT FAILED
"""

CHECKOUT_NOT_ON_INCLUDE_OUTPUT = """ANSYS LICENSE MANAGER ERROR : User/host not on INCLUDE list for feature.
Feature: ansys
License path: 1055@localhost;
FlexNet Licensing error:-39,147

ansys CHECKOUT FAILED
"""

CHECKOUT_ON_EXCLUDE_OUTPUT = """ANSYS LICENSE MANAGER ERROR : User/host on EXCLUDE list for feature.
Feature: ansys
License path: 1055@localhost;
FlexNet Licensing error:-38,147

ansys CHECKOUT FAILED
"""


class TestLicenseCheckout:
    """TC-16.9: test_license_checkout tests."""

    @patch("ansys.tools.common.licensing.diagnosis.find_ansysli_util")
    @patch("subprocess.run")
    def test_checkout_success(self, mock_run, mock_find_ansysli_util):
        """TC-16.9.1: Successful checkout."""
        from ansys.tools.common.licensing import test_license_checkout

        mock_find_ansysli_util.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=CHECKOUT_SUCCESS_OUTPUT, stderr="", returncode=0)

        result = test_license_checkout("mechanical_enterprise")

        assert result.success is True
        assert result.error_code is None
        assert result.error_type is None
        assert result.error_message is None
        assert result.feature == "mechanical_enterprise"

    @patch("ansys.tools.common.licensing.diagnosis.find_ansysli_util")
    @patch("subprocess.run")
    def test_checkout_connection_error(self, mock_run, mock_find_ansysli_util):
        """TC-16.9.2: Cannot connect to license server."""
        from ansys.tools.common.licensing import test_license_checkout

        mock_find_ansysli_util.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=CHECKOUT_CONNECTION_ERROR_OUTPUT, stderr="", returncode=1)

        result = test_license_checkout("ansys")

        assert result.success is False
        assert result.error_code == -15
        assert result.error_type == "connection_failed"
        assert "Cannot connect to license server" in result.error_message
        assert result.server == "65.8.70.45"
        assert "1055@abc.com" in result.license_path

    @patch("ansys.tools.common.licensing.diagnosis.find_ansysli_util")
    @patch("subprocess.run")
    def test_checkout_vendor_daemon_down(self, mock_run, mock_find_ansysli_util):
        """TC-16.9.3: Vendor daemon is down."""
        from ansys.tools.common.licensing import test_license_checkout

        mock_find_ansysli_util.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=CHECKOUT_VENDOR_DOWN_OUTPUT, stderr="", returncode=1)

        result = test_license_checkout("ansys")

        assert result.success is False
        assert result.error_code == -97
        assert result.error_type == "vendor_daemon_down"
        assert "vendor daemon" in result.error_message.lower()
        assert result.server == "10.45.16.188"

    @patch("ansys.tools.common.licensing.diagnosis.find_ansysli_util")
    @patch("subprocess.run")
    def test_checkout_not_on_include_list(self, mock_run, mock_find_ansysli_util):
        """TC-16.9.4: User not on INCLUDE list."""
        from ansys.tools.common.licensing import test_license_checkout

        mock_find_ansysli_util.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=CHECKOUT_NOT_ON_INCLUDE_OUTPUT, stderr="", returncode=1)

        result = test_license_checkout("ansys")

        assert result.success is False
        assert result.error_code == -39
        assert result.error_type == "access_denied"
        assert "INCLUDE list" in result.error_message
        assert "administrator" in result.error_message.lower()

    @patch("ansys.tools.common.licensing.diagnosis.find_ansysli_util")
    @patch("subprocess.run")
    def test_checkout_on_exclude_list(self, mock_run, mock_find_ansysli_util):
        """TC-16.9.5: User on EXCLUDE list."""
        from ansys.tools.common.licensing import test_license_checkout

        mock_find_ansysli_util.return_value = _get_test_lmutil_path()
        mock_run.return_value = MagicMock(stdout=CHECKOUT_ON_EXCLUDE_OUTPUT, stderr="", returncode=1)

        result = test_license_checkout("ansys")

        assert result.success is False
        assert result.error_code == -38
        assert result.error_type == "access_denied"
        assert "EXCLUDE list" in result.error_message
        assert "administrator" in result.error_message.lower()

    @patch("ansys.tools.common.licensing.diagnosis.find_ansysli_util")
    def test_checkout_no_ansysli_util(self, mock_find_ansysli_util):
        """TC-16.9.6: ansysli_util not found."""
        from ansys.tools.common.licensing import test_license_checkout

        mock_find_ansysli_util.return_value = ("", "")

        with pytest.raises(LicenseToolNotFoundError, match="ansysli_util not found"):
            test_license_checkout("ansys")

    @patch("ansys.tools.common.licensing.diagnosis.find_ansysli_util")
    @patch("subprocess.run")
    def test_checkout_timeout(self, mock_run, mock_find_ansysli_util):
        """TC-16.9.7: Checkout times out."""
        from ansys.tools.common.licensing import test_license_checkout

        mock_find_ansysli_util.return_value = _get_test_lmutil_path()
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ansysli_util", timeout=30)

        result = test_license_checkout("ansys")

        assert result.success is False
        assert result.error_type == "checkout_failed"
        assert "timed out" in result.error_message

    @patch("ansys.tools.common.licensing.diagnosis.find_ansysli_util")
    @patch("subprocess.run")
    def test_checkout_oserror(self, mock_run, mock_find_ansysli_util):
        """TC-16.9.8: OS error during checkout."""
        from ansys.tools.common.licensing import test_license_checkout

        mock_find_ansysli_util.return_value = _get_test_lmutil_path()
        mock_run.side_effect = OSError("Permission denied")

        result = test_license_checkout("ansys")

        assert result.success is False
        assert result.error_type == "checkout_failed"
        assert "Failed to execute" in result.error_message

    def test_checkout_result_model_exported(self):
        """LicenseCheckoutResult should be importable."""
        from ansys.tools.common.licensing import LicenseCheckoutResult

        assert LicenseCheckoutResult is not None

    def test_test_license_checkout_exported(self):
        """test_license_checkout should be importable."""
        from ansys.tools.common.licensing import test_license_checkout

        assert callable(test_license_checkout)


class TestCaptureOriginalsOnResolve:
    """get_license_server(_with_source) must capture originals (write-once, safe)."""

    def test_capture_called_on_resolve(self):
        """Resolving the server captures env and both ini-scope originals."""
        from ansys.tools.common.licensing.diagnosis import get_license_server_with_source

        with (
            patch(
                "ansys.tools.common.licensing.diagnosis.get_license_server_from_env",
                return_value="1055@envhost",
            ),
            patch("ansys.tools.common.licensing.config.capture_env_original") as mock_env,
            patch("ansys.tools.common.licensing.config.capture_ini_original") as mock_ini,
        ):
            server, source = get_license_server_with_source()

        assert server == "1055@envhost"
        assert source is None
        mock_env.assert_called_once_with()
        # Both user and installation scopes captured.
        assert {c.args[0] for c in mock_ini.call_args_list} == {"user", "installation"}

    def test_capture_still_runs_when_no_server(self):
        """Originals are captured even when no server can be resolved."""
        from ansys.tools.common.licensing.diagnosis import get_license_server_with_source

        with (
            patch(
                "ansys.tools.common.licensing.diagnosis.get_license_server_from_env",
                return_value=None,
            ),
            patch(
                "ansys.tools.common.licensing.diagnosis.find_ansyslmd_ini",
                return_value=None,
            ),
            patch("ansys.tools.common.licensing.config.capture_env_original") as mock_env,
            patch("ansys.tools.common.licensing.config.capture_ini_original") as mock_ini,
        ):
            server, source = get_license_server_with_source()

        assert (server, source) == (None, None)
        mock_env.assert_called_once_with()
        assert mock_ini.call_count == 2

    def test_capture_failure_does_not_break_resolution(self):
        """A capture failure is swallowed and does not break server resolution."""
        from ansys.tools.common.licensing.diagnosis import get_license_server_with_source

        with (
            patch(
                "ansys.tools.common.licensing.diagnosis.get_license_server_from_env",
                return_value="1055@envhost",
            ),
            patch(
                "ansys.tools.common.licensing.config.capture_env_original",
                side_effect=RuntimeError("boom"),
            ),
        ):
            # Must not raise despite capture failure.
            server, source = get_license_server_with_source()

        assert server == "1055@envhost"

    def test_get_license_server_populates_cache(self, tmp_path, monkeypatch):
        """Integration: resolving the server writes originals into config.txt."""
        from ansys.tools.common.licensing import config as oc
        from ansys.tools.common.licensing.diagnosis import get_license_server

        cache = tmp_path / "ansys_tools_licensing" / "config.txt"
        monkeypatch.setenv("ANSYS_TOOLS_LICENSING_CONFIG_PATH", str(cache))
        monkeypatch.setenv("ANSYSLMD_LICENSE_FILE", "1055@envhost")

        # Avoid touching the real filesystem for ini discovery.
        with patch("ansys.tools.common.licensing.config.find_ansyslmd_ini", return_value=None):
            server = get_license_server()

        assert server == "1055@envhost"
        assert oc.get_original(oc.KEY_ENV) == (True, "1055@envhost")
        assert oc.get_original(oc.KEY_USER_INI) == (True, None)
        assert oc.get_original(oc.KEY_INSTALL_INI) == (True, None)
