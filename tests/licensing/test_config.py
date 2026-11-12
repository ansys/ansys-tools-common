# Copyright (C) 2025 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for the licensing config module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from ansys.tools.common.exceptions import LicenseFileParseError
from ansys.tools.common.licensing import (
    AnsyslmdConfig,
    LicensePreferences,
    find_ansyslmd_ini,
    find_license_preferences_xml,
    parse_ansyslmd_ini,
    parse_license_preferences_xml,
)


class TestFindAnsyslmdIni:
    """Tests for find_ansyslmd_ini function."""

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    def test_find_ansyslmd_ini_user_scope_exists_windows(self, fs, monkeypatch):
        """TC-7.1.1/TC-7.1.6: Find user-scope ini file on Windows."""
        monkeypatch.setenv("APPDATA", "C:\\Users\\testuser\\AppData\\Roaming")

        # Create the file
        ini_path = "C:\\Users\\testuser\\AppData\\Roaming\\.ansys_licensing\\ansyslmd.ini"
        fs.create_file(ini_path, contents="SERVER=1055@host\n")

        result = find_ansyslmd_ini(scope="user")

        assert result == ini_path

    @pytest.mark.skipif(os.name != "posix", reason="Linux-specific test")
    def test_find_ansyslmd_ini_user_scope_exists_linux(self, fs, monkeypatch):
        """TC-7.1.1/TC-7.1.7: Find user-scope ini file on Linux."""
        monkeypatch.setenv("HOME", "/home/testuser")

        # Create the file
        ini_path = "/home/testuser/.ansys_licensing/ansyslmd.ini"
        fs.create_file(ini_path, contents="SERVER=1055@host\n")

        result = find_ansyslmd_ini(scope="user")

        assert result == ini_path

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    def test_find_ansyslmd_ini_user_scope_not_exists_windows(self, fs, monkeypatch):
        """TC-7.1.2: User-scope ini doesn't exist (Windows)."""
        monkeypatch.setenv("APPDATA", "C:\\Users\\testuser\\AppData\\Roaming")

        # Don't create the file
        result = find_ansyslmd_ini(scope="user")

        assert result is None

    @pytest.mark.skipif(os.name != "posix", reason="Linux-specific test")
    def test_find_ansyslmd_ini_user_scope_not_exists_linux(self, fs, monkeypatch):
        """TC-7.1.2: User-scope ini doesn't exist (Linux)."""
        monkeypatch.setenv("HOME", "/home/testuser")

        # Don't create the file
        result = find_ansyslmd_ini(scope="user")

        assert result is None

    def test_find_ansyslmd_ini_installation_scope_exists(self, fs, monkeypatch):
        """TC-7.1.3: Find installation-scope ini."""
        if os.name == "nt":
            lic_dir = "C:\\ansys_lic"
        else:
            lic_dir = "/opt/ansys_lic"

        monkeypatch.setenv("ANSYSLIC_DIR", lic_dir)
        ini_path = str(Path(lic_dir) / "ansyslmd.ini")
        fs.create_file(ini_path, contents="SERVER=1055@host\n")

        result = find_ansyslmd_ini(scope="installation")

        assert result == ini_path

    @patch(
        "ansys.tools.common.licensing.config.get_available_ansys_installations",
        return_value={},
    )
    def test_find_ansyslmd_ini_installation_scope_no_env(self, _mock, monkeypatch):
        """TC-7.1.4: ANSYSLIC_DIR not set and no AWP_ROOT installations."""
        monkeypatch.delenv("ANSYSLIC_DIR", raising=False)

        result = find_ansyslmd_ini(scope="installation")

        assert result is None

    @pytest.mark.skipif(os.name != "posix", reason="Linux-specific test")
    @patch(
        "ansys.tools.common.licensing.config.get_available_ansys_installations",
        return_value={261: "/opt/ansys_inc/v261"},
    )
    def test_find_ansyslmd_ini_installation_scope_awp_root_fallback_linux(self, _mock, fs, monkeypatch):
        """Installation-scope falls back to AWP_ROOT-derived path on Linux."""
        monkeypatch.delenv("ANSYSLIC_DIR", raising=False)

        # Create the ini file at the AWP_ROOT-derived path
        ini_path = "/opt/ansys_inc/shared_files/licensing/ansyslmd.ini"
        fs.create_file(ini_path, contents="SERVER=1055@host\n")

        result = find_ansyslmd_ini(scope="installation")

        assert result == ini_path

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    @patch(
        "ansys.tools.common.licensing.config.get_available_ansys_installations",
        return_value={261: "C:\\Program Files\\ANSYS Inc\\v261"},
    )
    def test_find_ansyslmd_ini_installation_scope_awp_root_fallback_windows(self, _mock, fs, monkeypatch):
        """Installation-scope falls back to AWP_ROOT-derived path on Windows."""
        monkeypatch.delenv("ANSYSLIC_DIR", raising=False)

        # Create the ini file at the AWP_ROOT-derived path
        ini_path = "C:\\Program Files\\ANSYS Inc\\shared_files\\licensing\\ansyslmd.ini"
        fs.create_file(ini_path, contents="SERVER=1055@host\n")

        result = find_ansyslmd_ini(scope="installation")

        assert result == ini_path

    @pytest.mark.skipif(os.name != "posix", reason="Linux-specific test")
    @patch(
        "ansys.tools.common.licensing.config.get_available_ansys_installations",
        return_value={261: "/opt/ansys_inc/v261", 242: "/opt/ansys_inc/v242"},
    )
    def test_find_ansyslmd_ini_installation_scope_awp_root_highest_version_linux(self, _mock, fs, monkeypatch):
        """AWP_ROOT fallback checks highest version first on Linux."""
        monkeypatch.delenv("ANSYSLIC_DIR", raising=False)

        # Only create ini for v242's parent (shared_files is shared, but test
        # that highest version path is checked first by only creating one)
        ini_path = "/opt/ansys_inc/shared_files/licensing/ansyslmd.ini"
        fs.create_file(ini_path, contents="SERVER=1055@host\n")

        result = find_ansyslmd_ini(scope="installation")

        assert result == ini_path

    @patch(
        "ansys.tools.common.licensing.config.get_available_ansys_installations",
        return_value={261: "/opt/ansys_inc/v261"},
    )
    def test_find_ansyslmd_ini_installation_scope_awp_root_no_ini_file(self, _mock, fs, monkeypatch):
        """AWP_ROOT fallback returns None when ini file doesn't exist at derived path."""
        monkeypatch.delenv("ANSYSLIC_DIR", raising=False)

        # Don't create the ini file
        result = find_ansyslmd_ini(scope="installation")

        assert result is None

    def test_find_ansyslmd_ini_installation_scope_ansyslic_dir_takes_priority(self, fs, monkeypatch):
        """ANSYSLIC_DIR takes priority over AWP_ROOT-derived path."""
        if os.name == "nt":
            lic_dir = "C:\\ansys_lic"
        else:
            lic_dir = "/opt/ansys_lic"

        monkeypatch.setenv("ANSYSLIC_DIR", lic_dir)
        ini_path = str(Path(lic_dir) / "ansyslmd.ini")
        fs.create_file(ini_path, contents="SERVER=1055@primary\n")

        result = find_ansyslmd_ini(scope="installation")

        # Should use ANSYSLIC_DIR, not AWP_ROOT fallback
        assert result == ini_path

    def test_find_ansyslmd_ini_invalid_scope(self):
        """TC-7.1.5: Invalid scope parameter."""
        with pytest.raises(ValueError, match="Invalid scope: invalid"):
            find_ansyslmd_ini(scope="invalid")

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    def test_find_ansyslmd_ini_windows_no_appdata(self, fs, monkeypatch):
        """User scope returns None when APPDATA not set on Windows."""
        monkeypatch.delenv("APPDATA", raising=False)

        result = find_ansyslmd_ini(scope="user")

        assert result is None

    @pytest.mark.skipif(os.name != "posix", reason="Linux-specific test")
    def test_find_ansyslmd_ini_linux_no_home(self, fs, monkeypatch):
        """User scope returns None when HOME not set on Linux."""
        monkeypatch.delenv("HOME", raising=False)

        result = find_ansyslmd_ini(scope="user")

        assert result is None


class TestParseAnsyslmdIni:
    """Tests for parse_ansyslmd_ini function."""

    def test_parse_ansyslmd_ini_with_server(self, fs):
        """TC-7.2.1: Parse ini with SERVER line."""
        ini_content = """# Ansys License Configuration
SERVER=1055@license-server.example.com
ANSYSLI_TIMEOUT_CONN=30
"""
        if os.name == "nt":
            ini_path = "C:\\tmp\\ansyslmd.ini"
        else:
            ini_path = "/tmp/ansyslmd.ini"
        fs.create_file(ini_path, contents=ini_content)

        result = parse_ansyslmd_ini(path=ini_path)

        assert isinstance(result, AnsyslmdConfig)
        assert result.path == ini_path
        assert result.server == "1055@license-server.example.com"
        assert result.options["ANSYSLI_TIMEOUT_CONN"] == "30"

    def test_parse_ansyslmd_ini_no_server(self, fs):
        """TC-7.2.2: Parse ini without SERVER line."""
        ini_content = """# Config without server
ANSYSLI_TIMEOUT_CONN=30
ANSYSLI_TIMEOUT_COMM=60
"""
        if os.name == "nt":
            ini_path = "C:\\tmp\\ansyslmd.ini"
        else:
            ini_path = "/tmp/ansyslmd.ini"
        fs.create_file(ini_path, contents=ini_content)

        result = parse_ansyslmd_ini(path=ini_path)

        assert result.server is None
        assert result.options["ANSYSLI_TIMEOUT_CONN"] == "30"
        assert result.options["ANSYSLI_TIMEOUT_COMM"] == "60"

    def test_parse_ansyslmd_ini_multiple_options(self, fs):
        """TC-7.2.3: Parse ini with multiple options."""
        ini_content = """SERVER=1055@host
ANSYSLI_TIMEOUT_CONN=30
ANSYSLI_TIMEOUT_COMM=60
ANSYSLMD_FLEXLM_DEBUG=3
"""
        if os.name == "nt":
            ini_path = "C:\\tmp\\ansyslmd.ini"
        else:
            ini_path = "/tmp/ansyslmd.ini"
        fs.create_file(ini_path, contents=ini_content)

        result = parse_ansyslmd_ini(path=ini_path)

        assert result.server == "1055@host"
        assert len(result.options) == 3
        assert result.options["ANSYSLI_TIMEOUT_CONN"] == "30"
        assert result.options["ANSYSLI_TIMEOUT_COMM"] == "60"
        assert result.options["ANSYSLMD_FLEXLM_DEBUG"] == "3"

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    def test_parse_ansyslmd_ini_auto_find_windows(self, fs, monkeypatch):
        """TC-7.2.4: Auto-find ini when path not given (Windows)."""
        monkeypatch.setenv("APPDATA", "C:\\Users\\testuser\\AppData\\Roaming")

        ini_path = "C:\\Users\\testuser\\AppData\\Roaming\\.ansys_licensing\\ansyslmd.ini"
        fs.create_file(ini_path, contents="SERVER=1055@auto-found\n")

        result = parse_ansyslmd_ini(path=None)

        assert result.server == "1055@auto-found"

    @pytest.mark.skipif(os.name != "posix", reason="Linux-specific test")
    def test_parse_ansyslmd_ini_auto_find_linux(self, fs, monkeypatch):
        """TC-7.2.4: Auto-find ini when path not given (Linux)."""
        monkeypatch.setenv("HOME", "/home/testuser")

        ini_path = "/home/testuser/.ansys_licensing/ansyslmd.ini"
        fs.create_file(ini_path, contents="SERVER=1055@auto-found\n")

        result = parse_ansyslmd_ini(path=None)

        assert result.server == "1055@auto-found"

    def test_parse_ansyslmd_ini_file_not_found(self, fs):
        """TC-7.2.5: File doesn't exist."""
        if os.name == "nt":
            nonexistent = "C:\\nonexistent\\ansyslmd.ini"
        else:
            nonexistent = "/nonexistent/ansyslmd.ini"

        with pytest.raises(LicenseFileParseError, match="not found"):
            parse_ansyslmd_ini(path=nonexistent)

    def test_parse_ansyslmd_ini_empty_file(self, fs):
        """TC-7.2.6: Empty ini file."""
        if os.name == "nt":
            ini_path = "C:\\tmp\\empty.ini"
        else:
            ini_path = "/tmp/empty.ini"
        fs.create_file(ini_path, contents="")

        result = parse_ansyslmd_ini(path=ini_path)

        assert result.server is None
        assert result.options == {}

    def test_parse_ansyslmd_ini_comments(self, fs):
        """TC-7.2.7: Handles comments correctly."""
        ini_content = """# This is a comment
; This is also a comment
SERVER=1055@host
# Another comment
OPTION=value
"""
        if os.name == "nt":
            ini_path = "C:\\tmp\\ansyslmd.ini"
        else:
            ini_path = "/tmp/ansyslmd.ini"
        fs.create_file(ini_path, contents=ini_content)

        result = parse_ansyslmd_ini(path=ini_path)

        assert result.server == "1055@host"
        assert result.options == {"OPTION": "value"}

    def test_parse_ansyslmd_ini_case_insensitive_keys(self, fs):
        """Keys should be normalized to uppercase."""
        ini_content = """server=1055@host
Option_Name=value
"""
        if os.name == "nt":
            ini_path = "C:\\tmp\\ansyslmd.ini"
        else:
            ini_path = "/tmp/ansyslmd.ini"
        fs.create_file(ini_path, contents=ini_content)

        result = parse_ansyslmd_ini(path=ini_path)

        assert result.server == "1055@host"
        assert "OPTION_NAME" in result.options

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    @patch(
        "ansys.tools.common.licensing.config.get_available_ansys_installations",
        return_value={},
    )
    def test_parse_ansyslmd_ini_auto_find_not_found_windows(self, _mock, fs, monkeypatch):
        """Auto-find raises error when no ini found (Windows)."""
        monkeypatch.setenv("APPDATA", "C:\\Users\\testuser\\AppData\\Roaming")
        monkeypatch.delenv("ANSYSLIC_DIR", raising=False)

        # Don't create any ini files
        with pytest.raises(LicenseFileParseError, match="Could not find"):
            parse_ansyslmd_ini(path=None)

    @pytest.mark.skipif(os.name != "posix", reason="Linux-specific test")
    @patch(
        "ansys.tools.common.licensing.config.get_available_ansys_installations",
        return_value={},
    )
    def test_parse_ansyslmd_ini_auto_find_not_found_linux(self, _mock, fs, monkeypatch):
        """Auto-find raises error when no ini found (Linux)."""
        monkeypatch.setenv("HOME", "/home/testuser")
        monkeypatch.delenv("ANSYSLIC_DIR", raising=False)

        # Don't create any ini files
        with pytest.raises(LicenseFileParseError, match="Could not find"):
            parse_ansyslmd_ini(path=None)


class TestFindLicensePreferencesXml:
    """Tests for find_license_preferences_xml function."""

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    def test_find_license_preferences_xml_exists_windows(self, fs, monkeypatch):
        """TC-7.3.1/TC-7.3.4: Find existing preferences file on Windows."""
        monkeypatch.setenv("APPDATA", "C:\\Users\\testuser\\AppData\\Roaming")

        xml_path = "C:\\Users\\testuser\\AppData\\Roaming\\Ansys\\v251\\license.preferences.xml"
        fs.create_file(xml_path, contents="<Preferences></Preferences>")

        result = find_license_preferences_xml(version=251)

        assert result == xml_path

    @pytest.mark.skipif(os.name != "posix", reason="Linux-specific test")
    def test_find_license_preferences_xml_exists_linux(self, fs, monkeypatch):
        """TC-7.3.1/TC-7.3.5: Find existing preferences file on Linux."""
        monkeypatch.setenv("HOME", "/home/testuser")

        xml_path = "/home/testuser/.ansys/v251/license.preferences.xml"
        fs.create_file(xml_path, contents="<Preferences></Preferences>")

        result = find_license_preferences_xml(version=251)

        assert result == xml_path

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    def test_find_license_preferences_xml_not_exists_windows(self, fs, monkeypatch):
        """TC-7.3.2: File doesn't exist (Windows)."""
        monkeypatch.setenv("APPDATA", "C:\\Users\\testuser\\AppData\\Roaming")

        result = find_license_preferences_xml(version=251)

        assert result is None

    @pytest.mark.skipif(os.name != "posix", reason="Linux-specific test")
    def test_find_license_preferences_xml_not_exists_linux(self, fs, monkeypatch):
        """TC-7.3.2: File doesn't exist (Linux)."""
        monkeypatch.setenv("HOME", "/home/testuser")

        result = find_license_preferences_xml(version=251)

        assert result is None

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    def test_find_license_preferences_xml_float_version(self, fs, monkeypatch):
        """Float version is converted correctly (e.g., 25.1 -> 251)."""
        monkeypatch.setenv("APPDATA", "C:\\Users\\testuser\\AppData\\Roaming")

        xml_path = "C:\\Users\\testuser\\AppData\\Roaming\\Ansys\\v251\\license.preferences.xml"
        fs.create_file(xml_path, contents="<Preferences></Preferences>")

        result = find_license_preferences_xml(version=25.1)

        assert result == xml_path

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    def test_find_license_preferences_xml_no_appdata(self, fs, monkeypatch):
        """Returns None when APPDATA not set on Windows."""
        monkeypatch.delenv("APPDATA", raising=False)

        result = find_license_preferences_xml(version=251)

        assert result is None

    @pytest.mark.skipif(os.name != "posix", reason="Linux-specific test")
    def test_find_license_preferences_xml_no_home(self, fs, monkeypatch):
        """Returns None when HOME not set on Linux."""
        monkeypatch.delenv("HOME", raising=False)

        result = find_license_preferences_xml(version=251)

        assert result is None


class TestParseLicensePreferencesXml:
    """Tests for parse_license_preferences_xml function."""

    def test_parse_license_preferences_xml_full(self, fs):
        """TC-7.4.1: Parse full preferences XML."""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
<Preferences>
  <LicenseServer>1055@license-server.example.com</LicenseServer>
  <LicenseOrder>
    <Feature name="mechanical_enterprise"/>
    <Feature name="mechanical_premium"/>
    <Feature name="structural_solver"/>
  </LicenseOrder>
  <UseDefaultLicense>true</UseDefaultLicense>
</Preferences>
"""
        if os.name == "nt":
            xml_path = "C:\\tmp\\license.preferences.xml"
        else:
            xml_path = "/tmp/license.preferences.xml"
        fs.create_file(xml_path, contents=xml_content)

        result = parse_license_preferences_xml(path=xml_path)

        assert isinstance(result, LicensePreferences)
        assert result.path == xml_path
        assert result.preferred_server == "1055@license-server.example.com"
        assert result.license_order == ["mechanical_enterprise", "mechanical_premium", "structural_solver"]
        assert result.options["UseDefaultLicense"] == "true"

    def test_parse_license_preferences_xml_minimal(self, fs):
        """TC-7.4.2: Parse minimal XML with only server."""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
<Preferences>
  <LicenseServer>1055@minimal-server</LicenseServer>
</Preferences>
"""
        if os.name == "nt":
            xml_path = "C:\\tmp\\license.preferences.xml"
        else:
            xml_path = "/tmp/license.preferences.xml"
        fs.create_file(xml_path, contents=xml_content)

        result = parse_license_preferences_xml(path=xml_path)

        assert result.preferred_server == "1055@minimal-server"
        assert result.license_order == []

    def test_parse_license_preferences_xml_file_not_found(self, fs):
        """TC-7.4.4: File doesn't exist."""
        if os.name == "nt":
            nonexistent = "C:\\nonexistent\\license.preferences.xml"
        else:
            nonexistent = "/nonexistent/license.preferences.xml"

        with pytest.raises(LicenseFileParseError, match="not found"):
            parse_license_preferences_xml(path=nonexistent)

    def test_parse_license_preferences_xml_invalid_xml(self, fs):
        """TC-7.4.5: Invalid XML content."""
        if os.name == "nt":
            xml_path = "C:\\tmp\\invalid.xml"
        else:
            xml_path = "/tmp/invalid.xml"
        fs.create_file(xml_path, contents="<not valid xml")

        with pytest.raises(LicenseFileParseError, match="Invalid XML"):
            parse_license_preferences_xml(path=xml_path)

    def test_parse_license_preferences_xml_license_order(self, fs):
        """TC-7.4.6: Extracts license order correctly."""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
<Preferences>
  <LicenseOrder>
    <Feature name="feature_a"/>
    <Feature name="feature_b"/>
    <Feature name="feature_c"/>
  </LicenseOrder>
</Preferences>
"""
        if os.name == "nt":
            xml_path = "C:\\tmp\\license.preferences.xml"
        else:
            xml_path = "/tmp/license.preferences.xml"
        fs.create_file(xml_path, contents=xml_content)

        result = parse_license_preferences_xml(path=xml_path)

        assert result.license_order == ["feature_a", "feature_b", "feature_c"]

    def test_parse_license_preferences_xml_feature_text_content(self, fs):
        """License order with text content instead of name attribute."""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
<Preferences>
  <LicenseOrder>
    <Feature>text_feature_a</Feature>
    <Feature>text_feature_b</Feature>
  </LicenseOrder>
</Preferences>
"""
        if os.name == "nt":
            xml_path = "C:\\tmp\\license.preferences.xml"
        else:
            xml_path = "/tmp/license.preferences.xml"
        fs.create_file(xml_path, contents=xml_content)

        result = parse_license_preferences_xml(path=xml_path)

        assert result.license_order == ["text_feature_a", "text_feature_b"]

    def test_parse_license_preferences_xml_alternate_server_tags(self, fs):
        """Handles alternate server tag names."""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
<Preferences>
  <PreferredServer>1055@alt-server</PreferredServer>
</Preferences>
"""
        if os.name == "nt":
            xml_path = "C:\\tmp\\license.preferences.xml"
        else:
            xml_path = "/tmp/license.preferences.xml"
        fs.create_file(xml_path, contents=xml_content)

        result = parse_license_preferences_xml(path=xml_path)

        assert result.preferred_server == "1055@alt-server"

    def test_parse_license_preferences_xml_empty_preferences(self, fs):
        """Empty preferences file."""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
<Preferences>
</Preferences>
"""
        if os.name == "nt":
            xml_path = "C:\\tmp\\license.preferences.xml"
        else:
            xml_path = "/tmp/license.preferences.xml"
        fs.create_file(xml_path, contents=xml_content)

        result = parse_license_preferences_xml(path=xml_path)

        assert result.preferred_server is None
        assert result.license_order == []
        assert result.options == {}


class TestConfigModuleExports:
    """TC-7.5.2: Test that config functions are properly exported."""

    def test_find_ansyslmd_ini_exported(self):
        """find_ansyslmd_ini should be importable from licensing module."""
        from ansys.tools.common.licensing import find_ansyslmd_ini

        assert callable(find_ansyslmd_ini)

    def test_parse_ansyslmd_ini_exported(self):
        """parse_ansyslmd_ini should be importable from licensing module."""
        from ansys.tools.common.licensing import parse_ansyslmd_ini

        assert callable(parse_ansyslmd_ini)

    def test_find_license_preferences_xml_exported(self):
        """find_license_preferences_xml should be importable from licensing module."""
        from ansys.tools.common.licensing import find_license_preferences_xml

        assert callable(find_license_preferences_xml)

    def test_parse_license_preferences_xml_exported(self):
        """parse_license_preferences_xml should be importable from licensing module."""
        from ansys.tools.common.licensing import parse_license_preferences_xml

        assert callable(parse_license_preferences_xml)

    def test_ansyslmd_config_model_exported(self):
        """AnsyslmdConfig model should be importable from licensing module."""
        from ansys.tools.common.licensing import AnsyslmdConfig

        assert AnsyslmdConfig is not None

    def test_license_preferences_model_exported(self):
        """LicensePreferences model should be importable from licensing module."""
        from ansys.tools.common.licensing import LicensePreferences

        assert LicensePreferences is not None


# Absolute user-scope ansyslmd.ini path and its parent, per platform.
if os.name == "nt":
    _USER_BASE = "C:\\Users\\testuser\\AppData\\Roaming"
    _USER_INI = _USER_BASE + "\\.ansys_licensing\\ansyslmd.ini"
    _USER_ENV = "APPDATA"
else:
    _USER_BASE = "/home/testuser"
    _USER_INI = _USER_BASE + "/.ansys_licensing/ansyslmd.ini"
    _USER_ENV = "HOME"


@pytest.fixture
def user_scope(fs, monkeypatch):
    """Set up a fake user-scope location and redirect the original-value cache."""
    monkeypatch.setenv(_USER_ENV, _USER_BASE)
    # Redirect original_config cache via the env override (robust across reloads).
    cache_path = str(Path(_USER_BASE) / "ansys_tools_licensing" / "config.txt")
    monkeypatch.setenv("ANSYS_TOOLS_LICENSING_CONFIG_PATH", cache_path)
    return _USER_INI


class TestRemoveAnsyslmdIniServer:
    """Tests for remove_ansyslmd_ini_server."""

    def test_invalid_scope_raises(self):
        """An unknown scope raises ValueError."""
        from ansys.tools.common.licensing.config import remove_ansyslmd_ini_server

        with pytest.raises(ValueError):
            remove_ansyslmd_ini_server(scope="bogus")

    def test_missing_file_returns_none(self, user_scope):
        """A missing ini file returns None (nothing to remove)."""
        from ansys.tools.common.licensing.config import remove_ansyslmd_ini_server

        assert remove_ansyslmd_ini_server(scope="user") is None

    def test_removes_server_preserves_other(self, user_scope, fs):
        """Removing SERVER leaves other options intact."""
        from ansys.tools.common.licensing.config import parse_ansyslmd_ini, remove_ansyslmd_ini_server

        fs.create_file(user_scope, contents="SERVER=1055@host\n# comment\nFOO=bar\n")
        result = remove_ansyslmd_ini_server(scope="user")
        assert result == user_scope
        parsed = parse_ansyslmd_ini(user_scope)
        assert parsed.server is None
        assert parsed.options == {"FOO": "bar"}

    def test_no_server_line_is_noop(self, user_scope, fs):
        """A file without a SERVER line is returned unchanged."""
        from ansys.tools.common.licensing.config import remove_ansyslmd_ini_server

        fs.create_file(user_scope, contents="# just a comment\nFOO=bar\n")
        result = remove_ansyslmd_ini_server(scope="user")
        # File exists so path is returned, but content unchanged.
        assert result == user_scope
        assert Path(user_scope).read_text(encoding="utf-8") == "# just a comment\nFOO=bar\n"


class TestCaptureOnSet:
    """set_ansyslmd_ini must capture the pre-change original SERVER (write-once)."""

    def test_capture_existing_server_before_change(self, user_scope, fs):
        """set_ansyslmd_ini captures the existing SERVER before overwriting it."""
        from ansys.tools.common.licensing import config as oc
        from ansys.tools.common.licensing.config import set_ansyslmd_ini

        fs.create_file(user_scope, contents="SERVER=1055@orig\n")
        set_ansyslmd_ini("1055@new", scope="user")
        assert oc.get_original(oc.KEY_USER_INI) == (True, "1055@orig")

    def test_capture_none_when_no_prior_file(self, user_scope):
        """With no prior file, the captured original is None."""
        from ansys.tools.common.licensing import config as oc
        from ansys.tools.common.licensing.config import set_ansyslmd_ini

        set_ansyslmd_ini("1055@new", scope="user")
        assert oc.get_original(oc.KEY_USER_INI) == (True, None)

    def test_capture_is_write_once_across_sets(self, user_scope, fs):
        """Repeated sets keep the first captured original (write-once)."""
        from ansys.tools.common.licensing import config as oc
        from ansys.tools.common.licensing.config import set_ansyslmd_ini

        fs.create_file(user_scope, contents="SERVER=1055@orig\n")
        set_ansyslmd_ini("1055@second", scope="user")
        set_ansyslmd_ini("1055@third", scope="user")
        # Original stays the very first detected value.
        assert oc.get_original(oc.KEY_USER_INI) == (True, "1055@orig")


class TestRestoreIni:
    """End-to-end restore_ini round-trips using real (fake-fs) ini files."""

    def test_restore_value_round_trip(self, user_scope, fs):
        """restore_ini reverts a changed SERVER back to the captured original."""
        from ansys.tools.common.licensing import config as oc
        from ansys.tools.common.licensing.config import parse_ansyslmd_ini, set_ansyslmd_ini

        fs.create_file(user_scope, contents="SERVER=1055@orig\n")
        set_ansyslmd_ini("1055@changed", scope="user")
        assert parse_ansyslmd_ini(user_scope).server == "1055@changed"

        removed, value = oc.restore_ini("user")
        assert (removed, value) == (False, "1055@orig")
        assert parse_ansyslmd_ini(user_scope).server == "1055@orig"

    def test_restore_unset_removes_line(self, user_scope):
        """restore_ini removes the SERVER line when the original was unset."""
        from ansys.tools.common.licensing import config as oc
        from ansys.tools.common.licensing.config import parse_ansyslmd_ini, set_ansyslmd_ini

        # No prior file -> original captured as None.
        set_ansyslmd_ini("1055@changed", scope="user")
        removed, value = oc.restore_ini("user")
        assert (removed, value) == (True, None)
        assert parse_ansyslmd_ini(user_scope).server is None

    def test_restore_nothing_captured_raises(self, user_scope):
        """restore_ini raises when no original SERVER was captured."""
        from ansys.tools.common.exceptions import LicenseConfigError
        from ansys.tools.common.licensing import config as oc

        with pytest.raises(LicenseConfigError, match="nothing to restore"):
            oc.restore_ini("user")
