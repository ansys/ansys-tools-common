# Copyright (C) 2025 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for persistent-env helpers in the licensing vars module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from ansys.tools.common.exceptions import LicenseConfigError
from ansys.tools.common.licensing import config as oc, vars as v


class TestSetEnvWindows:
    """Tests for set_env_windows."""

    def test_user_scope_success(self):
        """User scope writes to HKEY_CURRENT_USER via setx."""
        with patch("ansys.tools.common.licensing.vars.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            location = v.set_env_windows("1055@host", "user")
        assert "HKEY_CURRENT_USER" in location
        cmd = mock_run.call_args.args[0]
        assert cmd == ["setx", "ANSYSLMD_LICENSE_FILE", "1055@host"]

    def test_system_scope_uses_m_flag(self):
        """System scope uses the setx /M flag and HKEY_LOCAL_MACHINE."""
        with patch("ansys.tools.common.licensing.vars.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            location = v.set_env_windows("1055@host", "system")
        assert "HKEY_LOCAL_MACHINE" in location
        assert "/M" in mock_run.call_args.args[0]

    def test_access_denied_raises(self):
        """Access-denied output raises LicenseConfigError about Administrator rights."""
        with patch("ansys.tools.common.licensing.vars.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Access is denied")
            with pytest.raises(LicenseConfigError, match="Administrator"):
                v.set_env_windows("1055@host", "system")

    def test_timeout_raises(self):
        """A subprocess timeout raises LicenseConfigError about the timeout."""
        with patch(
            "ansys.tools.common.licensing.vars.subprocess.run",
            side_effect=subprocess.TimeoutExpired("setx", 30),
        ):
            with pytest.raises(LicenseConfigError, match="Timeout"):
                v.set_env_windows("1055@host", "user")


class TestRemoveEnvWindows:
    """Tests for remove_env_windows."""

    def test_user_scope_success(self):
        """User scope deletes the value under HKEY_CURRENT_USER."""
        with patch("ansys.tools.common.licensing.vars.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            location = v.remove_env_windows("user")
        assert "HKEY_CURRENT_USER" in location
        cmd = mock_run.call_args.args[0]
        assert cmd[:2] == ["reg", "delete"]
        assert "ANSYSLMD_LICENSE_FILE" in cmd

    def test_already_absent_is_success(self):
        """A missing registry value is treated as success, not an error."""
        with patch("ansys.tools.common.licensing.vars.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="ERROR: The system was unable to find the specified registry key or value",
            )
            # Should NOT raise.
            location = v.remove_env_windows("user")
        assert "HKEY_CURRENT_USER" in location

    def test_access_denied_raises(self):
        """Access-denied output raises LicenseConfigError about Administrator rights."""
        with patch("ansys.tools.common.licensing.vars.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Access is denied.")
            with pytest.raises(LicenseConfigError, match="Administrator"):
                v.remove_env_windows("system")


class TestDetectShell:
    """Tests for detect_shell."""

    def test_detects_zsh(self, monkeypatch):
        """SHELL ending in zsh is detected as zsh."""
        monkeypatch.setenv("SHELL", "/bin/zsh")
        assert v.detect_shell() == "zsh"

    def test_fallback_bash(self, monkeypatch):
        """detect_shell falls back to bash when SHELL is unset."""
        monkeypatch.delenv("SHELL", raising=False)
        assert v.detect_shell() == "bash"


class TestGetShellRcFile:
    """Tests for get_shell_rc_file."""

    def test_bash(self, monkeypatch):
        """Bash resolves to ~/.bashrc with an export template."""
        monkeypatch.setenv("HOME", "/home/user")
        rc_path, template = v.get_shell_rc_file("bash")
        assert rc_path.endswith(".bashrc")
        assert "export" in template

    def test_no_home_raises(self, monkeypatch):
        """A missing HOME raises LicenseConfigError mentioning HOME."""
        monkeypatch.delenv("HOME", raising=False)
        with pytest.raises(LicenseConfigError, match="HOME"):
            v.get_shell_rc_file("bash")


class TestSetEnvUnix:
    """Tests for set_env_unix (uses a real temp HOME)."""

    def test_creates_rc_file(self, tmp_path, monkeypatch):
        """set_env_unix creates the rc file with an export line."""
        monkeypatch.setenv("HOME", str(tmp_path))
        rc_path = v.set_env_unix("1055@host", "bash")
        content = (tmp_path / ".bashrc").read_text()
        assert 'export ANSYSLMD_LICENSE_FILE="1055@host"' in content
        assert rc_path.endswith(".bashrc")

    def test_replaces_existing_line(self, tmp_path, monkeypatch):
        """An existing export line is replaced while other content is preserved."""
        monkeypatch.setenv("HOME", str(tmp_path))
        rc = tmp_path / ".bashrc"
        rc.write_text('export ANSYSLMD_LICENSE_FILE="1055@old"\n# keep me\n')
        v.set_env_unix("1055@new", "bash")
        content = rc.read_text()
        assert "1055@old" not in content
        assert 'export ANSYSLMD_LICENSE_FILE="1055@new"' in content
        assert "# keep me" in content


class TestRemoveEnvUnix:
    """Tests for remove_env_unix (uses a real temp HOME)."""

    def test_removes_export_line(self, tmp_path, monkeypatch):
        """remove_env_unix strips the export line and its header comment."""
        monkeypatch.setenv("HOME", str(tmp_path))
        rc = tmp_path / ".bashrc"
        rc.write_text('# keep\n# Ansys License Server\nexport ANSYSLMD_LICENSE_FILE="1055@host"\n# tail\n')
        v.remove_env_unix("bash")
        content = rc.read_text()
        assert "ANSYSLMD_LICENSE_FILE" not in content
        assert "# Ansys License Server" not in content
        assert "# keep" in content
        assert "# tail" in content

    def test_missing_file_is_noop(self, tmp_path, monkeypatch):
        """A missing rc file is a no-op that still returns its path."""
        monkeypatch.setenv("HOME", str(tmp_path))
        # No .bashrc created; should not raise.
        rc_path = v.remove_env_unix("bash")
        assert rc_path.endswith(".bashrc")

    def test_no_line_is_noop(self, tmp_path, monkeypatch):
        """An rc file without the export line is left unchanged."""
        monkeypatch.setenv("HOME", str(tmp_path))
        rc = tmp_path / ".bashrc"
        rc.write_text("# nothing relevant here\n")
        v.remove_env_unix("bash")
        assert rc.read_text() == "# nothing relevant here\n"


@pytest.fixture
def cache_file(tmp_path, monkeypatch):
    """Redirect the original-value cache to a temporary location."""
    config_file = tmp_path / "ansys_tools_licensing" / "config.txt"
    monkeypatch.setenv("ANSYS_TOOLS_LICENSING_CONFIG_PATH", str(config_file))
    return config_file


class TestRestoreEnv:
    """Tests for config.restore_env (depends on vars helpers)."""

    def test_nothing_captured_raises(self, cache_file):
        """restore_env raises when no original value was captured."""
        with pytest.raises(LicenseConfigError, match="nothing to restore"):
            oc.restore_env()

    def test_restore_value_windows(self, cache_file, monkeypatch):
        """On Windows a captured value is restored via set_env_windows."""
        monkeypatch.setattr("os.name", "nt")
        oc.capture_original(oc.KEY_ENV, "1055@orig")
        with (
            patch("ansys.tools.common.licensing.config.set_env_windows") as mock_set,
            patch("ansys.tools.common.licensing.config.remove_env_windows") as mock_rm,
        ):
            removed, value = oc.restore_env(scope="user")
        assert (removed, value) == (False, "1055@orig")
        mock_set.assert_called_once_with("1055@orig", "user")
        mock_rm.assert_not_called()

    def test_restore_unset_windows_removes(self, cache_file, monkeypatch):
        """On Windows a captured unset is restored via remove_env_windows."""
        monkeypatch.setattr("os.name", "nt")
        oc.capture_original(oc.KEY_ENV, None)
        with (
            patch("ansys.tools.common.licensing.config.set_env_windows") as mock_set,
            patch("ansys.tools.common.licensing.config.remove_env_windows") as mock_rm,
        ):
            removed, value = oc.restore_env(scope="user")
        assert (removed, value) == (True, None)
        mock_rm.assert_called_once_with("user")
        mock_set.assert_not_called()

    def test_restore_value_unix(self, cache_file):
        """On POSIX a captured value is restored via set_env_unix."""
        # Simulate POSIX branch without faking os.name globally (which would
        # break pathlib on Windows). Patch get_original to avoid cache I/O and
        # patch the os.name seen by the config module.
        with (
            patch.object(oc, "get_original", return_value=(True, "1055@orig")),
            patch.object(oc.os, "name", "posix"),
            patch("ansys.tools.common.licensing.config.set_env_unix") as mock_set,
            patch("ansys.tools.common.licensing.config.remove_env_unix") as mock_rm,
        ):
            removed, value = oc.restore_env(shell="bash")
        assert (removed, value) == (False, "1055@orig")
        mock_set.assert_called_once_with("1055@orig", "bash")
        mock_rm.assert_not_called()

    def test_restore_unset_unix_removes(self, cache_file):
        """On POSIX a captured unset is restored via remove_env_unix."""
        with (
            patch.object(oc, "get_original", return_value=(True, None)),
            patch.object(oc.os, "name", "posix"),
            patch("ansys.tools.common.licensing.config.set_env_unix") as mock_set,
            patch("ansys.tools.common.licensing.config.remove_env_unix") as mock_rm,
        ):
            removed, value = oc.restore_env(shell="bash")
        assert (removed, value) == (True, None)
        mock_rm.assert_called_once_with("bash")
        mock_set.assert_not_called()
