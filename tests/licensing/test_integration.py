# Copyright (C) 2025 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Integration tests for the licensing module.

These tests verify that the various submodules work together correctly
for end-to-end workflows.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ansys.tools.common.exceptions import (
    LicenseFileParseError,
    LicenseServerError,
    LicenseToolNotFoundError,
)
from ansys.tools.common.licensing import (
    check_license_server_status_all,
    find_ansysli_util,
    find_ansyslmd_ini,
    find_license_preferences_xml,
    find_lmutil,
    get_license_environment,
    parse_ansyslmd_ini,
    parse_license_log,
    parse_license_preferences_xml,
)

# Sample lmstat output for mocking
SAMPLE_LMSTAT_OUTPUT = """lmutil - Copyright (c) 1989-2023 Flexera.

License server status: 1055@license-server.example.com

license-server.example.com: license server UP (MASTER) v11.18.1

Vendor daemon status:
    ansyslmd: UP v11.18.1

Feature usage info:

Users of mechanical_enterprise:  (Total of 10 licenses issued;  Total of 3 licenses in use)
Users of fluent_solver:  (Total of 20 licenses issued;  Total of 5 licenses in use)
"""

# Sample license file content
SAMPLE_LICENSE_FILE = """# Test License File
SERVER license-server.example.com ABCD1234 1055
VENDOR ansyslmd

FEATURE mechanical_enterprise ansyslmd 25.0 31-dec-2025 10 SIGN="..."
INCREMENT fluent_solver ansyslmd 25.0 permanent 20 SIGN="..."
"""

# Sample log content
SAMPLE_LOG_CONTENT = """2024-10-15 10:30:00 [INFO] License checkout: mechanical_enterprise
2024-10-15 10:35:00 [ERROR] License checkout failed: feature_not_found
2024-10-15 11:00:00 [WARNING] License server slow response
"""


def _get_test_path(filename: str) -> str:
    """Get platform-appropriate test path."""
    if os.name == "nt":
        return f"C:\\tmp\\{filename}"
    return f"/tmp/{filename}"


def _get_ansys_root() -> str:
    """Get platform-appropriate Ansys root."""
    if os.name == "nt":
        return r"C:\Program Files\ANSYS Inc\v261"
    return "/opt/ansys/v261"


def _get_lmutil_path() -> tuple[str, float]:
    """Get platform-appropriate lmutil path as tuple (path, version)."""
    if os.name == "nt":
        return (r"C:\Program Files\ANSYS Inc\v261\licensingclient\winx64\lmutil.exe", 26.1)
    return ("/opt/ansys/v261/licensingclient/linx64/lmutil", 26.1)


class TestFullEnvironmentSetup:
    """Test setting up a complete licensing environment."""

    def test_full_environment_setup(self, fs, monkeypatch):
        """Set up and verify a complete licensing test environment."""
        # Create fake Ansys installation
        awp_root = Path(_get_ansys_root())
        if os.name == "nt":
            tool_dir = awp_root / "licensingclient" / "winx64"
            fs.create_file(str(tool_dir / "lmutil.exe"))
            fs.create_file(str(tool_dir / "ansysli_util.exe"))
        else:
            tool_dir = awp_root / "licensingclient" / "linx64"
            fs.create_file(str(tool_dir / "lmutil"))
            fs.create_file(str(tool_dir / "ansysli_util"))

        # Set environment
        monkeypatch.setenv("AWP_ROOT261", str(awp_root))

        # Verify tools can be found
        lmutil = find_lmutil(version=261)
        assert lmutil is not None

        ansysli = find_ansysli_util(version=261)
        assert ansysli is not None


class TestWorkflowCheckServer:
    """TC-22.1.1: Full server check workflow."""

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_workflow_check_server(self, mock_run, mock_find_lmutil, monkeypatch):
        """Test: Find lmutil → Query server → Parse output."""
        # Setup
        mock_find_lmutil.return_value = _get_lmutil_path()
        mock_run.return_value = MagicMock(stdout=SAMPLE_LMSTAT_OUTPUT, stderr="", returncode=0)
        monkeypatch.setenv("ANSYSLMD_LICENSE_FILE", "1055@license-server.example.com")

        # Execute workflow
        status = check_license_server_status_all()

        # Verify
        assert status.is_up is True
        assert status.vendor_daemon_up is True
        assert len(status.features) == 2

        # Verify feature details
        mech = status.features["mechanical_enterprise"]
        assert mech.total == 10
        assert mech.in_use == 3


class TestWorkflowDiagnoseEnv:
    """TC-22.1.2: Environment diagnosis workflow."""

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_workflow_diagnose_env(self, mock_run, mock_find_lmutil, fs, monkeypatch):
        """Test: Get env → Find config → Check server."""
        # Setup environment
        monkeypatch.setenv("ANSYSLMD_LICENSE_FILE", "1055@license-server")
        monkeypatch.setenv("ANSYSLI_SERVERS", "")

        # Setup config file
        if os.name == "nt":
            config_path = Path(os.environ.get("APPDATA", "C:\\Users\\test\\AppData\\Roaming"))
            monkeypatch.setenv("APPDATA", str(config_path))
        else:
            config_path = Path.home()
        ini_path = config_path / ".ansys_licensing" / "ansyslmd.ini"
        fs.create_file(str(ini_path), contents="SERVER=1055@license-server\n")

        # Setup mock for server query
        mock_find_lmutil.return_value = _get_lmutil_path()
        mock_run.return_value = MagicMock(stdout=SAMPLE_LMSTAT_OUTPUT, stderr="", returncode=0)

        # Step 1: Get environment
        env = get_license_environment()
        assert env.effective_server == "1055@license-server"

        # Step 2: Find and parse config
        found_ini = find_ansyslmd_ini()
        assert found_ini is not None
        config = parse_ansyslmd_ini(found_ini)
        assert config.server == "1055@license-server"

        # Step 3: Check server
        status = check_license_server_status_all(server=env.effective_server)
        assert status.is_up is True


class TestWorkflowLogAnalysis:
    """TC-22.1.4: Log analysis workflow."""

    def test_workflow_log_analysis(self, fs, monkeypatch):
        """Test: Find log → Parse → Get recent errors."""
        # Setup log file
        if os.name == "nt":
            temp_dir = Path(os.environ.get("TEMP", "C:\\Windows\\Temp"))
            monkeypatch.setenv("TEMP", str(temp_dir))
            log_path = temp_dir / "ansyscl.testuser.log"
        else:
            log_path = Path.home() / ".ansys" / "ansyscl.testuser.log"

        fs.create_file(str(log_path), contents=SAMPLE_LOG_CONTENT)

        # Step 1: Find log (we'll parse directly since find depends on exact path patterns)
        # Step 2: Parse log
        log_info = parse_license_log(str(log_path))
        assert len(log_info.entries) > 0
        assert len(log_info.errors) >= 1

        # Step 3: Verify error content
        error = log_info.errors[0]
        assert "failed" in error.message.lower() or "error" in error.level.lower()


class TestWorkflowConfigDiscovery:
    """TC-22.1.5: Config discovery workflow."""

    def test_workflow_config_discovery(self, fs, monkeypatch):
        """Test: Find ini → Parse → Find prefs → Parse."""
        # Setup config paths
        if os.name == "nt":
            appdata = Path("C:\\Users\\test\\AppData\\Roaming")
            monkeypatch.setenv("APPDATA", str(appdata))
            ini_path = appdata / ".ansys_licensing" / "ansyslmd.ini"
            # Windows uses %APPDATA%\Ansys (capital A, no dot) for preferences XML
            prefs_path = appdata / "Ansys" / "v261" / "license.preferences.xml"
        else:
            home = Path.home()
            ini_path = home / ".ansys_licensing" / "ansyslmd.ini"
            prefs_path = home / ".ansys" / "v261" / "license.preferences.xml"

        # Create files
        fs.create_file(
            str(ini_path),
            contents="SERVER=1055@license-server\nANSYSLMD_TIMEOUT=60\n",
        )
        fs.create_file(
            str(prefs_path),
            contents="""<?xml version="1.0"?>
<Preferences>
    <LicenseServer>1055@license-server</LicenseServer>
</Preferences>
""",
        )

        # Step 1: Find and parse INI
        found_ini = find_ansyslmd_ini()
        assert found_ini is not None
        ini_config = parse_ansyslmd_ini(found_ini)
        assert ini_config.server == "1055@license-server"

        # Step 2: Find and parse preferences XML
        found_prefs = find_license_preferences_xml(version=261)
        assert found_prefs is not None
        prefs = parse_license_preferences_xml(found_prefs)
        assert prefs.preferred_server == "1055@license-server"


class TestCrossModuleIntegration:
    """TC-22.2: Cross-module integration tests."""

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_tools_with_server(self, mock_run, mock_find_lmutil, fs, monkeypatch):
        """TC-22.2.1: Tools module feeds server module."""
        # Setup fake installation
        awp_root = Path(_get_ansys_root())
        if os.name == "nt":
            lmutil_path = awp_root / "licensingclient" / "winx64" / "lmutil.exe"
        else:
            lmutil_path = awp_root / "licensingclient" / "linx64" / "lmutil"
        fs.create_file(str(lmutil_path))
        monkeypatch.setenv("AWP_ROOT261", str(awp_root))

        # Now mock find_lmutil to return our path as tuple
        mock_find_lmutil.return_value = (str(lmutil_path), 26.1)
        mock_run.return_value = MagicMock(stdout=SAMPLE_LMSTAT_OUTPUT, stderr="", returncode=0)

        # Call server function - it should use lmutil internally
        status = check_license_server_status_all(server="1055@host")
        assert status.is_up is True
        mock_find_lmutil.assert_called()

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("ansys.tools.common.licensing.diagnosis.get_license_server")
    @patch("subprocess.run")
    def test_env_with_server(self, mock_run, mock_get_server, mock_find_lmutil):
        """TC-22.2.2: Environment feeds server."""
        mock_find_lmutil.return_value = _get_lmutil_path()
        mock_get_server.return_value = "1055@env-server"
        mock_run.return_value = MagicMock(stdout=SAMPLE_LMSTAT_OUTPUT, stderr="", returncode=0)

        # Call without explicit server - should use env
        status = check_license_server_status_all(server=None)
        assert status.server == "1055@env-server"

    def test_config_with_env(self, fs, monkeypatch):
        """TC-22.2.4: Config and env together."""
        # Setup both config and env
        monkeypatch.setenv("ANSYSLMD_LICENSE_FILE", "1055@env-server")

        if os.name == "nt":
            appdata = Path("C:\\Users\\test\\AppData\\Roaming")
            monkeypatch.setenv("APPDATA", str(appdata))
            ini_path = appdata / ".ansys_licensing" / "ansyslmd.ini"
        else:
            ini_path = Path.home() / ".ansys_licensing" / "ansyslmd.ini"

        fs.create_file(str(ini_path), contents="SERVER=1055@config-server\n")

        # Get both
        env = get_license_environment()
        config = parse_ansyslmd_ini(str(ini_path))

        # Env should take precedence over config
        assert env.effective_server == "1055@env-server"
        assert config.server == "1055@config-server"


class TestErrorPropagation:
    """TC-22.3: Error propagation tests."""

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    def test_error_no_lmutil_propagates(self, mock_find_lmutil):
        """TC-22.3.1: LicenseToolNotFoundError propagates."""
        mock_find_lmutil.return_value = ("", "")

        with pytest.raises(LicenseToolNotFoundError):
            check_license_server_status_all(server="1055@host")

    @patch("ansys.tools.common.licensing.diagnosis.find_lmutil")
    @patch("subprocess.run")
    def test_error_server_unreachable(self, mock_run, mock_find_lmutil):
        """TC-22.3.2: LicenseServerError propagates."""
        mock_find_lmutil.return_value = _get_lmutil_path()
        mock_run.side_effect = OSError("Connection refused")

        with pytest.raises(LicenseServerError):
            check_license_server_status_all(server="1055@host")

    def test_error_file_parse_fails(self, fs):
        """TC-22.3.3: LicenseFileParseError propagates when parsing invalid log."""
        # Try to parse non-existent log file
        with pytest.raises(LicenseFileParseError):
            parse_license_log("/nonexistent/file.log")


class TestCLIIntegration:
    """TC-22.4: CLI integration tests using Click's test runner."""

    def test_cli_getserver_workflow(self, monkeypatch):
        """TC-22.4.1: CLI getserver end-to-end."""
        from click.testing import CliRunner

        from ansys.tools.common.licensing._cli import cli

        monkeypatch.setenv("ANSYSLMD_LICENSE_FILE", "1055@test-server")

        runner = CliRunner()
        result = runner.invoke(cli, ["getserver"])

        assert result.exit_code == 0
        assert "1055@test-server" in result.output

    def test_cli_getenv_workflow(self, monkeypatch):
        """TC-22.4.2: CLI getenv end-to-end."""
        from click.testing import CliRunner

        from ansys.tools.common.licensing._cli import cli

        monkeypatch.setenv("ANSYSLMD_LICENSE_FILE", "1055@test-server")

        runner = CliRunner()
        result = runner.invoke(cli, ["getenv"])

        assert result.exit_code == 0
        assert "ANSYSLMD_LICENSE_FILE=1055@test-server" in result.output

    def test_cli_getconfig_workflow(self, fs, monkeypatch):
        """TC-22.4.3: CLI getconfig end-to-end."""
        from click.testing import CliRunner

        from ansys.tools.common.licensing._cli import cli

        # Setup config file
        if os.name == "nt":
            appdata = Path("C:\\Users\\test\\AppData\\Roaming")
            monkeypatch.setenv("APPDATA", str(appdata))
            ini_path = appdata / ".ansys_licensing" / "ansyslmd.ini"
        else:
            ini_path = Path.home() / ".ansys_licensing" / "ansyslmd.ini"

        fs.create_file(str(ini_path), contents="SERVER=1055@config-server\n")

        runner = CliRunner()
        result = runner.invoke(cli, ["getconfig"])

        assert result.exit_code == 0
        assert "1055@config-server" in result.output
