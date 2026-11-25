# Copyright (C) 2025 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for the licensing CLI module."""

import json
from unittest.mock import patch

from click.testing import CliRunner
import pytest

from ansys.tools.common.exceptions import LicenseToolNotFoundError
from ansys.tools.common.licensing._cli import cli
from ansys.tools.common.licensing.models import (
    AnsyslmdConfig,
    FeatureInfo,
    LicenseCheckoutResult,
    ServerTestResult,
)


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_feature_info():
    """Mock FeatureInfo for testing."""
    return FeatureInfo(name="mechanical_enterprise", vendor="ansyslmd", total=10, in_use=3)


@pytest.fixture
def mock_features_dict():
    """Mock features dictionary for testing."""
    return {
        "mechanical_enterprise": FeatureInfo(name="mechanical_enterprise", vendor="ansyslmd", total=10, in_use=3),
        "fluent_solver": FeatureInfo(name="fluent_solver", vendor="ansyslmd", total=20, in_use=15),
    }


class TestCliHelp:
    """CLI framework tests."""

    def test_cli_help(self, runner):
        """Shows help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Ansys licensing utilities" in result.output

    def test_cli_subcommand_help(self, runner):
        """Subcommand help."""
        result = runner.invoke(cli, ["get-server", "--help"])
        assert result.exit_code == 0
        assert "effective license server" in result.output

    def test_cli_unknown_command(self, runner):
        """Unknown command."""
        result = runner.invoke(cli, ["unknown"])
        assert result.exit_code != 0


class TestGetserverCommand:
    """Tests for getserver command."""

    @patch("ansys.tools.common.licensing._cli.get_license_server_with_source")
    def test_getserver_default(self, mock_get_server, runner):
        """Getserver with defaults."""
        mock_get_server.return_value = ("1055@license-server", None)

        result = runner.invoke(cli, ["get-server"])

        assert result.exit_code == 0
        assert "1055@license-server" in result.output
        assert "Environment variable" in result.output

    @patch("ansys.tools.common.licensing._cli.get_license_server_with_source")
    def test_getserver_from_config(self, mock_get_server, runner):
        """Getserver from config file."""
        mock_get_server.return_value = ("1055@license-server", "/path/to/ansyslmd.ini")

        result = runner.invoke(cli, ["get-server"])

        assert result.exit_code == 0
        assert "1055@license-server" in result.output
        assert "/path/to/ansyslmd.ini" in result.output

    @patch("ansys.tools.common.licensing._cli.get_license_server_with_source")
    def test_getserver_none(self, mock_get_server, runner):
        """Getserver when no server configured."""
        mock_get_server.return_value = (None, None)

        result = runner.invoke(cli, ["get-server"])

        assert result.exit_code == 0
        assert "No license server configured" in result.output

    @patch("ansys.tools.common.licensing._cli.get_license_server_with_source")
    def test_getserver_json(self, mock_get_server, runner):
        """Getserver in JSON format."""
        mock_get_server.return_value = ("1055@license-server", None)

        result = runner.invoke(cli, ["get-server", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["server"] == "1055@license-server"
        assert data["source_type"] == "environment"


class TestCheckserverCommand:
    """Tests for checkserver command."""

    @patch("ansys.tools.common.licensing._cli.check_license_server_status")
    def test_checkserver_success(self, mock_check, runner):
        """Checkserver success."""
        mock_check.return_value = ServerTestResult(
            server="1055@host",
            vendor="ansyslmd",
            lmgrd_up=True,
            vendor_daemon_up=True,
            lmgrd_version="v11.18.1",
            vendor_daemon_version="v11.18.1",
        )

        result = runner.invoke(cli, ["check-server", "1055@host"])

        assert result.exit_code == 0
        assert "UP" in result.output

    @patch("ansys.tools.common.licensing._cli.check_license_server_status")
    def test_checkserver_failure(self, mock_check, runner):
        """Checkserver failure."""
        mock_check.return_value = ServerTestResult(
            server="1055@host",
            vendor="ansyslmd",
            lmgrd_up=False,
            vendor_daemon_up=False,
            error_type="connection_refused",
            error_message="Cannot connect to license server host.",
        )

        result = runner.invoke(cli, ["check-server", "1055@host"])

        assert result.exit_code == 1
        assert "DOWN" in result.output
        assert "Cannot connect" in result.output

    @patch("ansys.tools.common.licensing._cli.check_license_server_status")
    def test_checkserver_json(self, mock_check, runner):
        """Checkserver in JSON format."""
        mock_check.return_value = ServerTestResult(
            server="1055@host",
            vendor="ansyslmd",
            lmgrd_up=True,
            vendor_daemon_up=True,
            lmgrd_version="v11.18.1",
            vendor_daemon_version="v11.18.1",
        )

        result = runner.invoke(cli, ["check-server", "1055@host", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["server"] == "1055@host"
        assert data["lmgrd_up"] is True
        assert data["vendor_daemon_up"] is True

    @patch("ansys.tools.common.licensing._cli.check_license_server_status")
    def test_checkserver_with_timeout(self, mock_check, runner):
        """Checkserver with timeout option."""
        mock_check.return_value = ServerTestResult(
            server="1055@host",
            vendor="ansyslmd",
            lmgrd_up=True,
            vendor_daemon_up=True,
        )

        result = runner.invoke(cli, ["check-server", "1055@host", "--timeout", "60"])

        assert result.exit_code == 0
        mock_check.assert_called_once()
        call_args = mock_check.call_args
        assert call_args[1]["timeout"] == 60

    def test_checkserver_invalid_format_hostname_only(self, runner):
        """Checkserver rejects hostname without port."""
        result = runner.invoke(cli, ["check-server", "license-server"])

        assert result.exit_code != 0
        assert "Invalid server format" in result.output
        assert "port@hostname" in result.output

    def test_checkserver_invalid_format_missing_port(self, runner):
        """Checkserver rejects @hostname without port number."""
        result = runner.invoke(cli, ["check-server", "@license-server"])

        assert result.exit_code != 0
        assert "Invalid server format" in result.output

    def test_checkserver_invalid_format_port_only(self, runner):
        """Checkserver rejects port without hostname."""
        result = runner.invoke(cli, ["check-server", "1055@"])

        assert result.exit_code != 0
        assert "Invalid server format" in result.output

    def test_checkserver_invalid_format_no_at_sign(self, runner):
        """Checkserver rejects a bare string with no @ separator."""
        result = runner.invoke(cli, ["check-server", "1055license-server"])

        assert result.exit_code != 0
        assert "Invalid server format" in result.output

    def test_checkserver_invalid_format_reversed(self, runner):
        """Checkserver rejects hostname@port (reversed order)."""
        result = runner.invoke(cli, ["check-server", "license-server@1055"])

        assert result.exit_code != 0
        assert "Invalid server format" in result.output

    @patch("ansys.tools.common.licensing._cli.check_license_server_status")
    def test_checkserver_valid_format_accepted(self, mock_check, runner):
        """Checkserver accepts valid port@hostname format."""
        mock_check.return_value = ServerTestResult(
            server="1055@license-server",
            vendor="ansyslmd",
            lmgrd_up=True,
            vendor_daemon_up=True,
        )

        result = runner.invoke(cli, ["check-server", "1055@license-server"])

        assert result.exit_code == 0
        mock_check.assert_called_once()

    @patch("ansys.tools.common.licensing._cli.check_license_server_status")
    def test_checkserver_valid_format_ip_address(self, mock_check, runner):
        """Checkserver accepts port@ip-address format."""
        mock_check.return_value = ServerTestResult(
            server="1055@192.168.1.100",
            vendor="ansyslmd",
            lmgrd_up=True,
            vendor_daemon_up=True,
        )

        result = runner.invoke(cli, ["check-server", "1055@192.168.1.100"])

        assert result.exit_code == 0
        mock_check.assert_called_once()

    @patch("ansys.tools.common.licensing._cli.check_license_server_status")
    def test_checkserver_valid_format_fqdn(self, mock_check, runner):
        """Checkserver accepts port@fully.qualified.domain.name format."""
        mock_check.return_value = ServerTestResult(
            server="1055@license.example.com",
            vendor="ansyslmd",
            lmgrd_up=True,
            vendor_daemon_up=True,
        )

        result = runner.invoke(cli, ["check-server", "1055@license.example.com"])

        assert result.exit_code == 0
        mock_check.assert_called_once()


class TestGetenvCommand:
    """Tests for getenv command."""

    @patch("ansys.tools.common.licensing._cli.get_license_vars")
    def test_getenv_default(self, mock_get_vars, runner):
        """Getenv with defaults."""
        mock_get_vars.return_value = {
            "ANSYSLMD_LICENSE_FILE": "1055@license-server",
            "ANSYSLI_SERVERS": None,
            "ANSYSLIC_DIR": "/path/to/lic",
        }

        result = runner.invoke(cli, ["get-env"])

        assert result.exit_code == 0
        assert "ANSYSLMD_LICENSE_FILE=1055@license-server" in result.output
        assert "ANSYSLI_SERVERS: (not set)" in result.output

    @patch("ansys.tools.common.licensing._cli.get_license_vars")
    def test_getenv_json(self, mock_get_vars, runner):
        """Getenv in JSON format."""
        mock_get_vars.return_value = {
            "ANSYSLMD_LICENSE_FILE": "1055@license-server",
            "ANSYSLI_SERVERS": None,
        }

        result = runner.invoke(cli, ["get-env", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ANSYSLMD_LICENSE_FILE"] == "1055@license-server"
        assert data["ANSYSLI_SERVERS"] is None

    @patch("ansys.tools.common.licensing._cli.get_license_vars")
    def test_getenv_with_vendor(self, mock_get_vars, runner):
        """Getenv with vendor option."""
        mock_get_vars.return_value = {"ANSYSLMD_LICENSE_FILE": None}

        result = runner.invoke(cli, ["get-env", "--vendor", "ansyslmd"])

        assert result.exit_code == 0
        mock_get_vars.assert_called_with(vendor="ansyslmd")


class TestGetconfigCommand:
    """Tests for getconfig command."""

    @patch("ansys.tools.common.licensing._cli.find_ansyslmd_ini")
    @patch("ansys.tools.common.licensing._cli.parse_ansyslmd_ini")
    def test_getconfig_default(self, mock_parse, mock_find, runner):
        """Getconfig with defaults."""
        mock_find.side_effect = ["/path/to/user/ansyslmd.ini", "/path/to/install/ansyslmd.ini"]
        mock_parse.side_effect = [
            AnsyslmdConfig(path="/path/to/user/ansyslmd.ini", server="1055@user-server", options={}),
            AnsyslmdConfig(path="/path/to/install/ansyslmd.ini", server="1055@install-server", options={}),
        ]

        result = runner.invoke(cli, ["get-config"])

        assert result.exit_code == 0
        assert "User Config" in result.output
        assert "Installation Config" in result.output
        assert "1055@user-server" in result.output

    @patch("ansys.tools.common.licensing._cli.find_ansyslmd_ini")
    @patch("ansys.tools.common.licensing._cli.parse_ansyslmd_ini")
    def test_getconfig_json(self, mock_parse, mock_find, runner):
        """Getconfig in JSON format."""
        mock_find.side_effect = ["/path/to/ansyslmd.ini", None]
        mock_parse.return_value = AnsyslmdConfig(path="/path/to/ansyslmd.ini", server="1055@host", options={})

        result = runner.invoke(cli, ["get-config", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "user_config" in data
        assert "installation_config" in data
        assert "effective_config" in data

    @patch("ansys.tools.common.licensing._cli.find_ansyslmd_ini")
    def test_getconfig_none_found(self, mock_find, runner):
        """Getconfig when no config found."""
        mock_find.return_value = None

        result = runner.invoke(cli, ["get-config"])

        assert result.exit_code == 0
        assert "(not found)" in result.output


class TestGetfeaturesCommand:
    """Tests for getfeatures command."""

    @patch("ansys.tools.common.licensing._cli.get_license_server")
    @patch("ansys.tools.common.licensing._cli.get_license_features")
    def test_getfeatures_default(self, mock_get_features, mock_get_server, runner, mock_features_dict):
        """Getfeatures with defaults."""
        mock_get_server.return_value = "1055@license-server"
        mock_get_features.return_value = mock_features_dict

        result = runner.invoke(cli, ["get-features"])

        assert result.exit_code == 0
        assert "mechanical_enterprise" in result.output
        assert "fluent_solver" in result.output
        assert "7/10 available" in result.output  # 10-3

    @patch("ansys.tools.common.licensing._cli.get_license_features")
    def test_getfeatures_explicit_server(self, mock_get_features, runner, mock_features_dict):
        """Getfeatures with explicit server."""
        mock_get_features.return_value = mock_features_dict

        result = runner.invoke(cli, ["get-features", "--server", "1055@myhost"])

        assert result.exit_code == 0
        mock_get_features.assert_called_once()
        call_args = mock_get_features.call_args
        assert call_args[1]["server"] == "1055@myhost"

    @patch("ansys.tools.common.licensing._cli.get_license_server")
    @patch("ansys.tools.common.licensing._cli.get_license_features")
    def test_getfeatures_json(self, mock_get_features, mock_get_server, runner, mock_features_dict):
        """Getfeatures in JSON format."""
        mock_get_server.return_value = "1055@host"
        mock_get_features.return_value = mock_features_dict

        result = runner.invoke(cli, ["get-features", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "server" in data
        assert "features" in data
        assert "mechanical_enterprise" in data["features"]

    @patch("ansys.tools.common.licensing._cli.get_license_server")
    def test_getfeatures_no_server(self, mock_get_server, runner):
        """Getfeatures with no server configured."""
        mock_get_server.return_value = None

        result = runner.invoke(cli, ["get-features"])

        assert result.exit_code == 1
        assert "No license server specified" in result.output

    @patch("ansys.tools.common.licensing._cli.get_license_server")
    @patch("ansys.tools.common.licensing._cli.get_license_features")
    def test_getfeatures_tool_not_found(self, mock_get_features, mock_get_server, runner):
        """Getfeatures when lmutil not found."""
        mock_get_server.return_value = "1055@host"
        mock_get_features.side_effect = LicenseToolNotFoundError("lmutil not found")

        result = runner.invoke(cli, ["get-features"])

        assert result.exit_code == 1
        assert "lmutil" in result.output.lower()


class TestCheckfeatureCommand:
    """Tests for checkfeature command."""

    @patch("ansys.tools.common.licensing._cli.get_license_server")
    @patch("ansys.tools.common.licensing._cli.check_feature")
    def test_checkfeature_found(self, mock_check, mock_get_server, runner, mock_feature_info):
        """Checkfeature when feature found."""
        mock_get_server.return_value = "1055@license-server"
        mock_check.return_value = mock_feature_info

        result = runner.invoke(cli, ["check-feature", "mechanical_enterprise"])

        assert result.exit_code == 0
        assert "mechanical_enterprise" in result.output
        assert "Total Licenses: 10" in result.output
        assert "In Use: 3" in result.output
        assert "Available: 7" in result.output

    @patch("ansys.tools.common.licensing._cli.get_license_server")
    @patch("ansys.tools.common.licensing._cli.check_feature")
    def test_checkfeature_not_found(self, mock_check, mock_get_server, runner):
        """Checkfeature when feature not found."""
        mock_get_server.return_value = "1055@license-server"
        mock_check.return_value = None

        result = runner.invoke(cli, ["check-feature", "unknown_feature"])

        assert result.exit_code == 1
        assert "not found" in result.output

    @patch("ansys.tools.common.licensing._cli.check_feature")
    def test_checkfeature_explicit_server(self, mock_check, runner, mock_feature_info):
        """Checkfeature with explicit server."""
        mock_check.return_value = mock_feature_info

        result = runner.invoke(cli, ["check-feature", "mechanical_enterprise", "--server", "1055@myhost"])

        assert result.exit_code == 0
        mock_check.assert_called_once()
        call_args = mock_check.call_args
        assert call_args[1]["server"] == "1055@myhost"

    @patch("ansys.tools.common.licensing._cli.get_license_server")
    @patch("ansys.tools.common.licensing._cli.check_feature")
    def test_checkfeature_json(self, mock_check, mock_get_server, runner, mock_feature_info):
        """Checkfeature in JSON format."""
        mock_get_server.return_value = "1055@host"
        mock_check.return_value = mock_feature_info

        result = runner.invoke(cli, ["check-feature", "mechanical_enterprise", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["found"] is True
        assert data["feature"]["name"] == "mechanical_enterprise"

    @patch("ansys.tools.common.licensing._cli.get_license_server")
    @patch("ansys.tools.common.licensing._cli.check_feature")
    def test_checkfeature_uncounted(self, mock_check, mock_get_server, runner):
        """Checkfeature for uncounted feature."""
        mock_get_server.return_value = "1055@host"
        mock_check.return_value = FeatureInfo(name="unlimited_feature", vendor="ansyslmd", total=-1, in_use=0)

        result = runner.invoke(cli, ["check-feature", "unlimited_feature"])

        assert result.exit_code == 0
        assert "Uncounted" in result.output


class TestCheckoutCommand:
    """Tests for checkout command."""

    @patch("ansys.tools.common.licensing._cli.test_license_checkout")
    def test_checkout_success(self, mock_checkout, runner):
        """Checkout success."""
        mock_checkout.return_value = LicenseCheckoutResult(
            feature="mechanical_enterprise",
            success=True,
            error_code=None,
            error_type=None,
            error_message=None,
            license_path="1055@server",
            server="server.example.com",
            raw_output="checkout successful",
        )

        result = runner.invoke(cli, ["checkout", "mechanical_enterprise"])

        assert result.exit_code == 0
        assert "SUCCESS" in result.output
        assert "mechanical_enterprise" in result.output

    @patch("ansys.tools.common.licensing._cli.test_license_checkout")
    def test_checkout_failure(self, mock_checkout, runner):
        """Checkout failure."""
        mock_checkout.return_value = LicenseCheckoutResult(
            feature="mechanical_enterprise",
            success=False,
            error_code=-15,
            error_type="connection_failed",
            error_message="Cannot connect to license server",
            license_path=None,
            server="server.example.com",
            raw_output="checkout failed",
        )

        result = runner.invoke(cli, ["checkout", "mechanical_enterprise"])

        assert result.exit_code == 1
        assert "FAILED" in result.output
        assert "connection_failed" in result.output

    @patch("ansys.tools.common.licensing._cli.test_license_checkout")
    def test_checkout_json(self, mock_checkout, runner):
        """Checkout in JSON format."""
        mock_checkout.return_value = LicenseCheckoutResult(
            feature="mechanical_enterprise",
            success=True,
            error_code=None,
            error_type=None,
            error_message=None,
            license_path="1055@server",
            server="server.example.com",
            raw_output="checkout successful",
        )

        result = runner.invoke(cli, ["checkout", "mechanical_enterprise", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["feature"] == "mechanical_enterprise"
        assert data["success"] is True

    @patch("ansys.tools.common.licensing._cli.test_license_checkout")
    def test_checkout_tool_not_found(self, mock_checkout, runner):
        """Checkout when ansysli_util not found."""
        mock_checkout.side_effect = LicenseToolNotFoundError("ansysli_util not found")

        result = runner.invoke(cli, ["checkout", "mechanical_enterprise"])

        assert result.exit_code == 1
        assert "ansysli_util" in result.output.lower()

    @patch("ansys.tools.common.licensing._cli.test_license_checkout")
    def test_checkout_with_timeout(self, mock_checkout, runner):
        """Checkout with timeout option."""
        mock_checkout.return_value = LicenseCheckoutResult(
            feature="mechanical_enterprise",
            success=True,
            error_code=None,
            error_type=None,
            error_message=None,
            license_path=None,
            server=None,
            raw_output="",
        )

        result = runner.invoke(cli, ["checkout", "mechanical_enterprise", "--timeout", "60"])

        assert result.exit_code == 0
        mock_checkout.assert_called_once()
        call_args = mock_checkout.call_args
        assert call_args[1]["timeout"] == 60


class TestShellDetection:
    """Tests for shell detection helper functions."""

    def test_detect_shell_bash(self, monkeypatch):
        """Detect bash shell from $SHELL."""
        from ansys.tools.common.licensing._cli import _detect_shell

        monkeypatch.setenv("SHELL", "/bin/bash")
        assert _detect_shell() == "bash"

    def test_detect_shell_zsh(self, monkeypatch):
        """Detect zsh shell from $SHELL."""
        from ansys.tools.common.licensing._cli import _detect_shell

        monkeypatch.setenv("SHELL", "/usr/bin/zsh")
        assert _detect_shell() == "zsh"

    def test_detect_shell_fish(self, monkeypatch):
        """Detect fish shell from $SHELL."""
        from ansys.tools.common.licensing._cli import _detect_shell

        monkeypatch.setenv("SHELL", "/usr/local/bin/fish")
        assert _detect_shell() == "fish"

    def test_detect_shell_tcsh(self, monkeypatch):
        """Detect tcsh shell from $SHELL."""
        from ansys.tools.common.licensing._cli import _detect_shell

        monkeypatch.setenv("SHELL", "/bin/tcsh")
        assert _detect_shell() == "tcsh"

    def test_detect_shell_unknown_defaults_to_bash(self, monkeypatch):
        """Unknown shell defaults to bash."""
        from ansys.tools.common.licensing._cli import _detect_shell

        monkeypatch.setenv("SHELL", "/usr/bin/ksh")
        assert _detect_shell() == "bash"

    def test_detect_shell_no_shell_env_defaults_to_bash(self, monkeypatch):
        """Missing $SHELL defaults to bash."""
        from ansys.tools.common.licensing._cli import _detect_shell

        monkeypatch.delenv("SHELL", raising=False)
        assert _detect_shell() == "bash"

    def test_get_shell_rc_file_bash(self, monkeypatch):
        """Get rc file for bash shell."""
        from ansys.tools.common.licensing._cli import _get_shell_rc_file

        monkeypatch.setenv("HOME", "/home/user")
        rc_path, export_template = _get_shell_rc_file("bash")
        # Use path checking that works on all platforms
        assert rc_path.endswith(".bashrc")
        assert "home" in rc_path.lower() or "user" in rc_path.lower()
        assert "export" in export_template
        assert "ANSYSLMD_LICENSE_FILE" in export_template

    def test_get_shell_rc_file_zsh(self, monkeypatch):
        """Get rc file for zsh shell."""
        from ansys.tools.common.licensing._cli import _get_shell_rc_file

        monkeypatch.setenv("HOME", "/home/user")
        rc_path, export_template = _get_shell_rc_file("zsh")
        assert rc_path.endswith(".zshrc")
        assert "export" in export_template

    def test_get_shell_rc_file_fish(self, monkeypatch):
        """Get rc file for fish shell."""
        from ansys.tools.common.licensing._cli import _get_shell_rc_file

        monkeypatch.setenv("HOME", "/home/user")
        rc_path, export_template = _get_shell_rc_file("fish")
        assert "config.fish" in rc_path
        assert "set -gx" in export_template

    def test_get_shell_rc_file_csh(self, monkeypatch):
        """Get rc file for csh shell."""
        from ansys.tools.common.licensing._cli import _get_shell_rc_file

        monkeypatch.setenv("HOME", "/home/user")
        rc_path, export_template = _get_shell_rc_file("csh")
        assert rc_path.endswith(".cshrc")
        assert "setenv" in export_template

    def test_get_shell_rc_file_auto(self, monkeypatch):
        """Get rc file with auto-detection."""
        from ansys.tools.common.licensing._cli import _get_shell_rc_file

        monkeypatch.setenv("HOME", "/home/user")
        monkeypatch.setenv("SHELL", "/bin/zsh")
        rc_path, export_template = _get_shell_rc_file("auto")
        assert rc_path.endswith(".zshrc")

    def test_get_shell_rc_file_no_home_raises(self, monkeypatch):
        """Missing HOME raises LicenseConfigError."""
        from ansys.tools.common.exceptions import LicenseConfigError
        from ansys.tools.common.licensing._cli import _get_shell_rc_file

        monkeypatch.delenv("HOME", raising=False)
        with pytest.raises(LicenseConfigError, match="HOME"):
            _get_shell_rc_file("bash")


class TestSetserverEnvCommand:
    """Tests for setserver env command (persistent env var)."""

    @patch("ansys.tools.common.licensing._cli._set_env_windows")
    def test_setserver_env_windows(self, mock_set_env, runner, monkeypatch):
        """Setserver env on Windows sets persistent env var."""
        monkeypatch.setattr("os.name", "nt")
        mock_set_env.return_value = "HKEY_CURRENT_USER\\Environment"

        result = runner.invoke(cli, ["set-server", "env", "1055@test-server"])

        assert result.exit_code == 0
        mock_set_env.assert_called_once_with("1055@test-server", "user")
        assert "ANSYSLMD_LICENSE_FILE=1055@test-server" in result.output
        assert "persistent" in result.output.lower()

    @patch("ansys.tools.common.licensing._cli._set_env_windows")
    def test_setserver_env_windows_system_scope(self, mock_set_env, runner, monkeypatch):
        """Setserver env with system scope on Windows."""
        monkeypatch.setattr("os.name", "nt")
        mock_set_env.return_value = "HKEY_LOCAL_MACHINE\\..."

        result = runner.invoke(cli, ["set-server", "env", "1055@test-server", "--scope", "system"])

        assert result.exit_code == 0
        mock_set_env.assert_called_once_with("1055@test-server", "system")

    @patch("ansys.tools.common.licensing._cli._set_env_unix")
    def test_setserver_env_unix(self, mock_set_env, runner, monkeypatch):
        """Setserver env on Unix sets persistent env var."""
        monkeypatch.setattr("os.name", "posix")
        mock_set_env.return_value = "/home/user/.bashrc"

        result = runner.invoke(cli, ["set-server", "env", "1055@test-server"])

        assert result.exit_code == 0
        mock_set_env.assert_called_once_with("1055@test-server", "auto")
        assert "ANSYSLMD_LICENSE_FILE=1055@test-server" in result.output
        assert "persistent" in result.output.lower()

    @patch("ansys.tools.common.licensing._cli._set_env_unix")
    def test_setserver_env_unix_shell_option(self, mock_set_env, runner, monkeypatch):
        """Setserver env on Unix with explicit shell option."""
        monkeypatch.setattr("os.name", "posix")
        mock_set_env.return_value = "/home/user/.zshrc"

        result = runner.invoke(cli, ["set-server", "env", "1055@test-server", "--shell", "zsh"])

        assert result.exit_code == 0
        mock_set_env.assert_called_once_with("1055@test-server", "zsh")
        assert ".zshrc" in result.output

    def test_setserver_env_unix_system_scope_error(self, runner, monkeypatch):
        """Setserver env with system scope on Unix shows error."""
        monkeypatch.setattr("os.name", "posix")

        result = runner.invoke(cli, ["set-server", "env", "1055@test-server", "--scope", "system"])

        assert result.exit_code == 1
        assert "manually" in result.output.lower() or "error" in result.output.lower()

    @patch("ansys.tools.common.licensing._cli._set_env_windows")
    def test_setserver_env_json(self, mock_set_env, runner, monkeypatch):
        """Setserver env in JSON format."""
        monkeypatch.setattr("os.name", "nt")
        mock_set_env.return_value = "HKEY_CURRENT_USER\\Environment"

        result = runner.invoke(cli, ["set-server", "env", "1055@test-server", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["server"] == "1055@test-server"
        assert data["target"] == "env"
        assert data["scope"] == "user"
        assert "rc_file" in data

    @patch("ansys.tools.common.licensing._cli._set_env_windows")
    def test_setserver_env_error_json(self, mock_set_env, runner, monkeypatch):
        """Setserver env error in JSON format."""
        from ansys.tools.common.exceptions import LicenseConfigError

        monkeypatch.setattr("os.name", "nt")
        mock_set_env.side_effect = LicenseConfigError("Permission denied")

        result = runner.invoke(cli, ["set-server", "env", "1055@test-server", "--json"])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["success"] is False
        assert "Permission denied" in data["error"]

    def test_setserver_env_help(self, runner):
        """Setserver env shows help with shell options."""
        result = runner.invoke(cli, ["set-server", "env", "--help"])

        assert result.exit_code == 0
        assert "persistent" in result.output.lower()
        assert "--scope" in result.output
        assert "--shell" in result.output

    def test_setserver_env_invalid_format_hostname_only(self, runner):
        """Setserver env rejects hostname without port."""
        result = runner.invoke(cli, ["set-server", "env", "license-server"])

        assert result.exit_code != 0
        assert "Invalid server format" in result.output
        assert "port@hostname" in result.output

    def test_setserver_env_invalid_format_reversed(self, runner):
        """Setserver env rejects hostname@port (reversed order)."""
        result = runner.invoke(cli, ["set-server", "env", "license-server@1055"])

        assert result.exit_code != 0
        assert "Invalid server format" in result.output


class TestSetserverConfigCommand:
    """Tests for setserver config command (ansyslmd.ini)."""

    @patch("ansys.tools.common.licensing._cli.set_ansyslmd_ini")
    def test_setserver_config_user_scope(self, mock_set_ini, runner):
        """Setserver config with user scope."""
        mock_set_ini.return_value = "/home/user/.ansys_licensing/ansyslmd.ini"

        result = runner.invoke(cli, ["set-server", "config", "1055@test-server"])

        assert result.exit_code == 0
        mock_set_ini.assert_called_once_with(server="1055@test-server", scope="user")
        assert "SERVER=1055@test-server" in result.output

    @patch("ansys.tools.common.licensing._cli.set_ansyslmd_ini")
    def test_setserver_config_installation_scope(self, mock_set_ini, runner):
        """Setserver config with installation scope."""
        mock_set_ini.return_value = "/opt/ansys/licensing/ansyslmd.ini"

        result = runner.invoke(cli, ["set-server", "config", "1055@test-server", "--scope", "installation"])

        assert result.exit_code == 0
        mock_set_ini.assert_called_once_with(server="1055@test-server", scope="installation")

    @patch("ansys.tools.common.licensing._cli.set_ansyslmd_ini")
    def test_setserver_config_json(self, mock_set_ini, runner):
        """Setserver config in JSON format."""
        mock_set_ini.return_value = "/home/user/.ansys_licensing/ansyslmd.ini"

        result = runner.invoke(cli, ["set-server", "config", "1055@test-server", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["server"] == "1055@test-server"
        assert data["target"] == "config"
        assert data["scope"] == "user"
        assert data["path"] == "/home/user/.ansys_licensing/ansyslmd.ini"

    @patch("ansys.tools.common.licensing._cli.set_ansyslmd_ini")
    def test_setserver_config_error(self, mock_set_ini, runner):
        """Setserver config error."""
        from ansys.tools.common.exceptions import LicenseConfigError

        mock_set_ini.side_effect = LicenseConfigError("Permission denied")

        result = runner.invoke(cli, ["set-server", "config", "1055@test-server"])

        assert result.exit_code == 1
        assert "Permission denied" in result.output

    @patch("ansys.tools.common.licensing._cli.set_ansyslmd_ini")
    def test_setserver_config_error_json(self, mock_set_ini, runner):
        """Setserver config error in JSON format."""
        from ansys.tools.common.exceptions import LicenseConfigError

        mock_set_ini.side_effect = LicenseConfigError("Permission denied")

        result = runner.invoke(cli, ["set-server", "config", "1055@test-server", "--json"])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["success"] is False
        assert "Permission denied" in data["error"]

    def test_setserver_config_help(self, runner):
        """Setserver config shows help."""
        result = runner.invoke(cli, ["set-server", "config", "--help"])

        assert result.exit_code == 0
        assert "ansyslmd.ini" in result.output
        assert "--scope" in result.output

    def test_setserver_config_invalid_format_hostname_only(self, runner):
        """Setserver config rejects hostname without port."""
        result = runner.invoke(cli, ["set-server", "config", "license-server"])

        assert result.exit_code != 0
        assert "Invalid server format" in result.output
        assert "port@hostname" in result.output

    def test_setserver_config_invalid_format_reversed(self, runner):
        """Setserver config rejects hostname@port (reversed order)."""
        result = runner.invoke(cli, ["set-server", "config", "license-server@1055"])

        assert result.exit_code != 0
        assert "Invalid server format" in result.output


class TestSetserverGroupHelp:
    """Tests for setserver command group help."""

    def test_setserver_help(self, runner):
        """Setserver shows help with subcommands."""
        result = runner.invoke(cli, ["set-server", "--help"])

        assert result.exit_code == 0
        assert "env" in result.output
        assert "config" in result.output

    def test_setserver_no_subcommand(self, runner):
        """Setserver without subcommand shows usage error."""
        result = runner.invoke(cli, ["set-server"])

        # Click groups return exit code 2 (usage error) when no subcommand is given
        assert result.exit_code == 2
        assert "Usage" in result.output or "Missing command" in result.output


class TestJsonOutputValidity:
    """JSON output tests."""

    @patch("ansys.tools.common.licensing._cli.get_license_server_with_source")
    def test_json_getserver_structure(self, mock_get, runner):
        """Getserver JSON structure."""
        mock_get.return_value = ("1055@host", "/path/to/ini")

        result = runner.invoke(cli, ["get-server", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "server" in data
        assert "source" in data
        assert "source_type" in data

    @patch("ansys.tools.common.licensing._cli.get_license_vars")
    def test_json_getenv_structure(self, mock_get, runner):
        """Getenv JSON structure."""
        mock_get.return_value = {"ANSYSLMD_LICENSE_FILE": "1055@host"}

        result = runner.invoke(cli, ["get-env", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)
        assert "ANSYSLMD_LICENSE_FILE" in data


class TestDeprecatedAliases:
    """Old concatenated command names still work but emit DeprecationWarning."""

    @patch("ansys.tools.common.licensing._cli.get_license_server_with_source")
    def test_getserver_alias_works(self, mock_get_server, runner):
        """Old 'getserver' alias resolves to 'get-server' and succeeds."""
        mock_get_server.return_value = ("1055@host", None)

        result = runner.invoke(cli, ["getserver"])

        assert result.exit_code == 0
        assert "1055@host" in result.output

    @patch("ansys.tools.common.licensing._cli.get_license_server_with_source")
    def test_getserver_alias_emits_deprecation_warning(self, mock_get_server):
        """Old 'getserver' alias emits a DeprecationWarning."""
        import warnings as _warnings

        mock_get_server.return_value = ("1055@host", None)

        with _warnings.catch_warnings(record=True) as caught:
            _warnings.simplefilter("always")
            runner = CliRunner()
            runner.invoke(cli, ["getserver"])

        deprecation_msgs = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert any("getserver" in str(w.message) and "get-server" in str(w.message) for w in deprecation_msgs)

    @patch("ansys.tools.common.licensing._cli.get_license_vars")
    def test_getenv_alias_works(self, mock_get_vars, runner):
        """Old 'getenv' alias resolves to 'get-env' and succeeds."""
        mock_get_vars.return_value = {"ANSYSLMD_LICENSE_FILE": None}

        result = runner.invoke(cli, ["getenv"])

        assert result.exit_code == 0

    @patch("ansys.tools.common.licensing._cli.get_license_server")
    @patch("ansys.tools.common.licensing._cli.get_license_features")
    def test_getfeatures_alias_works(self, mock_features, mock_server, runner):
        """Old 'getfeatures' alias resolves to 'get-features' and succeeds."""
        mock_server.return_value = "1055@host"
        mock_features.return_value = {}

        result = runner.invoke(cli, ["getfeatures"])

        assert result.exit_code == 0

    def test_unknown_command_still_fails(self, runner):
        """A truly unknown command is not resolved by the alias map."""
        result = runner.invoke(cli, ["nonexistent"])

        assert result.exit_code != 0


class TestSetserverEnvCapture:
    """set-server env must capture the original ANSYSLMD_LICENSE_FILE first."""

    @patch("ansys.tools.common.licensing._cli.capture_env_original")
    @patch("ansys.tools.common.licensing._cli._set_env_windows")
    def test_capture_called_before_set(self, mock_set_env, mock_capture, runner, monkeypatch):
        """The original env value is captured before the new server is set."""
        monkeypatch.setattr("os.name", "nt")
        mock_set_env.return_value = "HKEY_CURRENT_USER\\Environment"

        result = runner.invoke(cli, ["set-server", "env", "1055@test-server"])

        assert result.exit_code == 0
        mock_capture.assert_called_once_with()
        mock_set_env.assert_called_once_with("1055@test-server", "user")


class TestSetserverRestoreEnv:
    """Tests for set-server restore env."""

    @patch("ansys.tools.common.licensing._cli.restore_env")
    def test_restore_value(self, mock_restore, runner):
        """Restoring a captured value prints and reports the restored server."""
        mock_restore.return_value = (False, "1055@orig")

        result = runner.invoke(cli, ["set-server", "restore", "env"])

        assert result.exit_code == 0
        mock_restore.assert_called_once_with(scope="user", shell="auto")
        assert "Restored ANSYSLMD_LICENSE_FILE=1055@orig" in result.output

    @patch("ansys.tools.common.licensing._cli.restore_env")
    def test_restore_removed(self, mock_restore, runner):
        """Restoring a captured unset removes the env variable."""
        mock_restore.return_value = (True, None)

        result = runner.invoke(cli, ["set-server", "restore", "env"])

        assert result.exit_code == 0
        assert "Removed ANSYSLMD_LICENSE_FILE" in result.output

    @patch("ansys.tools.common.licensing._cli.restore_env")
    def test_restore_json(self, mock_restore, runner):
        """--json reports the restored env server as structured output."""
        mock_restore.return_value = (False, "1055@orig")

        result = runner.invoke(cli, ["set-server", "restore", "env", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["action"] == "restore"
        assert data["server"] == "1055@orig"
        assert data["removed"] is False

    @patch("ansys.tools.common.licensing._cli.restore_env")
    def test_restore_nothing_captured(self, mock_restore, runner):
        """A missing captured env value exits non-zero with a clear message."""
        from ansys.tools.common.exceptions import LicenseConfigError

        mock_restore.side_effect = LicenseConfigError("No original ANSYSLMD_LICENSE_FILE captured; nothing to restore.")

        result = runner.invoke(cli, ["set-server", "restore", "env"])

        assert result.exit_code == 1
        assert "nothing to restore" in result.output

    @patch("ansys.tools.common.licensing._cli.restore_env")
    def test_restore_nothing_captured_json(self, mock_restore, runner):
        """A missing captured env value reports failure in --json mode."""
        from ansys.tools.common.exceptions import LicenseConfigError

        mock_restore.side_effect = LicenseConfigError("nothing to restore")

        result = runner.invoke(cli, ["set-server", "restore", "env", "--json"])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["success"] is False
        assert "error" in data


class TestSetserverRestoreConfig:
    """Tests for set-server restore config."""

    @patch("ansys.tools.common.licensing._cli.restore_ini")
    def test_restore_value(self, mock_restore, runner):
        """Restoring a captured value reports the restored SERVER."""
        mock_restore.return_value = (False, "1055@orig")

        result = runner.invoke(cli, ["set-server", "restore", "config"])

        assert result.exit_code == 0
        mock_restore.assert_called_once_with("user")
        assert "Restored SERVER=1055@orig" in result.output

    @patch("ansys.tools.common.licensing._cli.restore_ini")
    def test_restore_removed_installation(self, mock_restore, runner):
        """Restoring a captured unset removes SERVER for the installation scope."""
        mock_restore.return_value = (True, None)

        result = runner.invoke(cli, ["set-server", "restore", "config", "--scope", "installation"])

        assert result.exit_code == 0
        mock_restore.assert_called_once_with("installation")
        assert "Removed SERVER" in result.output

    @patch("ansys.tools.common.licensing._cli.restore_ini")
    def test_restore_json(self, mock_restore, runner):
        """--json reports the restored config SERVER as structured output."""
        mock_restore.return_value = (True, None)

        result = runner.invoke(cli, ["set-server", "restore", "config", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["removed"] is True
        assert data["scope"] == "user"

    @patch("ansys.tools.common.licensing._cli.restore_ini")
    def test_restore_nothing_captured(self, mock_restore, runner):
        """A missing captured config SERVER exits non-zero with a clear message."""
        from ansys.tools.common.exceptions import LicenseConfigError

        mock_restore.side_effect = LicenseConfigError(
            "No original user ansyslmd.ini SERVER captured; nothing to restore."
        )

        result = runner.invoke(cli, ["set-server", "restore", "config"])

        assert result.exit_code == 1
        assert "nothing to restore" in result.output
