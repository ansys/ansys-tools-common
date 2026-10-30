# Copyright (C) 2025 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for licensing module data models (Phase 1 - T2).

Test cases:
- TC-1.1, TC-1.2: Module import tests
- TC-2.1 through TC-2.10: Dataclass tests
"""

from datetime import datetime

# =============================================================================
# TC-1.1, TC-1.2: Module Import Tests
# =============================================================================


def test_licensing_module_import():
    """TC-1.1: Test that licensing module can be imported."""
    from ansys.tools.common import licensing

    assert licensing is not None


def test_licensing_submodule_imports():
    """TC-1.2: Test that all licensing submodules can be imported."""
    from ansys.tools.common.licensing import models

    assert models is not None


def test_licensing_constants():
    """Test that licensing constants are accessible."""
    from ansys.tools.common.licensing import DEFAULT_VENDOR, VENDOR_INFO

    assert DEFAULT_VENDOR == "ansyslmd"
    assert "ansyslmd" in VENDOR_INFO
    assert "env_vars" in VENDOR_INFO["ansyslmd"]


# =============================================================================
# TC-2.1: LicenseServerStatus Dataclass Tests
# =============================================================================


def test_license_server_status_creation():
    """TC-2.1a: Test LicenseServerStatus dataclass creation."""
    from ansys.tools.common.licensing.models import LicenseServerStatus

    status = LicenseServerStatus(
        server="1055@licserver.example.com",
        vendor="ansyslmd",
        is_up=True,
        vendor_daemon_up=True,
        features={},
        raw_output="lmstat output",
    )

    assert status.server == "1055@licserver.example.com"
    assert status.vendor == "ansyslmd"
    assert status.is_up is True
    assert status.vendor_daemon_up is True
    assert status.features == {}
    assert status.raw_output == "lmstat output"


def test_license_server_status_with_features():
    """TC-2.1b: Test LicenseServerStatus with FeatureInfo dict."""
    from ansys.tools.common.licensing.models import FeatureInfo, LicenseServerStatus

    features = {
        "mechanical_enterprise": FeatureInfo(name="mechanical_enterprise", vendor="ansyslmd", total=10, in_use=3),
        "fluent_solver": FeatureInfo(name="fluent_solver", vendor="ansyslmd", total=5, in_use=5),
    }

    status = LicenseServerStatus(
        server="1055@server",
        vendor="ansyslmd",
        is_up=True,
        vendor_daemon_up=True,
        features=features,
        raw_output="",
    )

    assert len(status.features) == 2
    assert status.features["mechanical_enterprise"].name == "mechanical_enterprise"
    assert status.features["fluent_solver"].in_use == 5


# =============================================================================
# TC-2.2: FeatureInfo Dataclass Tests
# =============================================================================


def test_feature_info_creation():
    """TC-2.2a: Test FeatureInfo dataclass creation."""
    from ansys.tools.common.licensing.models import FeatureInfo

    feature = FeatureInfo(name="mechanical_enterprise", vendor="ansyslmd", total=10, in_use=3)

    assert feature.name == "mechanical_enterprise"
    assert feature.vendor == "ansyslmd"
    assert feature.total == 10
    assert feature.in_use == 3


def test_feature_info_zero_usage():
    """TC-2.2b: Test FeatureInfo with zero usage."""
    from ansys.tools.common.licensing.models import FeatureInfo

    feature = FeatureInfo(name="unused_feature", vendor="ansyslmd", total=5, in_use=0)

    assert feature.in_use == 0
    assert feature.total == 5


# =============================================================================
# TC-2.4: LicenseEnvironment Dataclass Tests
# =============================================================================


def test_license_environment_creation():
    """TC-2.4a: Test LicenseEnvironment dataclass creation."""
    from ansys.tools.common.licensing.models import LicenseEnvironment

    env = LicenseEnvironment(
        vendor="ansyslmd",
        env_vars={
            "ANSYSLMD_LICENSE_FILE": "1055@server",
            "ANSYSLI_SERVERS": None,
        },
        effective_server="1055@server",
    )

    assert env.vendor == "ansyslmd"
    assert env.env_vars["ANSYSLMD_LICENSE_FILE"] == "1055@server"
    assert env.env_vars["ANSYSLI_SERVERS"] is None
    assert env.effective_server == "1055@server"


def test_license_environment_no_server():
    """TC-2.4b: Test LicenseEnvironment with no effective server."""
    from ansys.tools.common.licensing.models import LicenseEnvironment

    env = LicenseEnvironment(vendor="ansyslmd", env_vars={}, effective_server=None)

    assert env.effective_server is None


# =============================================================================
# TC-2.5: LogEntry Dataclass Tests
# =============================================================================


def test_log_entry_creation():
    """TC-2.5a: Test LogEntry dataclass creation."""
    from ansys.tools.common.licensing.models import LogEntry

    timestamp = datetime(2026, 10, 27, 14, 30, 0)
    entry = LogEntry(
        timestamp=timestamp,
        level="ERROR",
        message="License checkout failed",
        raw_line="2026-10-27 14:30:00 ERROR License checkout failed",
    )

    assert entry.timestamp == timestamp
    assert entry.level == "ERROR"
    assert entry.message == "License checkout failed"


def test_log_entry_no_timestamp():
    """TC-2.5b: Test LogEntry with no timestamp (unparsable)."""
    from ansys.tools.common.licensing.models import LogEntry

    entry = LogEntry(timestamp=None, level="WARNING", message="Some warning", raw_line="WARNING Some warning")

    assert entry.timestamp is None
    assert entry.level == "WARNING"


# =============================================================================
# TC-2.6: LicenseLogInfo Dataclass Tests
# =============================================================================


def test_license_log_info_creation():
    """TC-2.6: Test LicenseLogInfo dataclass creation."""
    from ansys.tools.common.licensing.models import LicenseLogInfo, LogEntry

    error_entry = LogEntry(timestamp=None, level="ERROR", message="Error 1", raw_line="")
    warning_entry = LogEntry(timestamp=None, level="WARNING", message="Warning 1", raw_line="")

    log_info = LicenseLogInfo(
        path="/path/to/log",
        entries=[error_entry, warning_entry],
        errors=[error_entry],
        warnings=[warning_entry],
        checkout_events=[],
    )

    assert log_info.path == "/path/to/log"
    assert len(log_info.entries) == 2
    assert len(log_info.errors) == 1
    assert len(log_info.warnings) == 1
    assert len(log_info.checkout_events) == 0


# =============================================================================
# TC-2.7: AnsyslmdConfig Dataclass Tests
# =============================================================================


def test_ansyslmd_config_creation():
    """TC-2.7a: Test AnsyslmdConfig dataclass creation."""
    from ansys.tools.common.licensing.models import AnsyslmdConfig

    config = AnsyslmdConfig(
        path="/path/to/ansyslmd.ini",
        server="1055@licserver",
        options={"TIMEOUT": "30", "FLEXLM_TIMEOUT": "1000000"},
    )

    assert config.path == "/path/to/ansyslmd.ini"
    assert config.server == "1055@licserver"
    assert config.options["TIMEOUT"] == "30"


def test_ansyslmd_config_no_server():
    """TC-2.7b: Test AnsyslmdConfig with no server defined."""
    from ansys.tools.common.licensing.models import AnsyslmdConfig

    config = AnsyslmdConfig(path="/path/to/ansyslmd.ini", server=None, options={})

    assert config.server is None
    assert config.options == {}


# =============================================================================
# TC-2.8: LicensePreferences Dataclass Tests
# =============================================================================


def test_license_preferences_creation():
    """TC-2.8a: Test LicensePreferences dataclass creation."""
    from ansys.tools.common.licensing.models import LicensePreferences

    prefs = LicensePreferences(
        path="/path/to/license.preferences.xml",
        preferred_server="1055@server1",
        license_order=["mechanical_enterprise", "mechanical_premium"],
        options={"use_flexnet": True},
    )

    assert prefs.path == "/path/to/license.preferences.xml"
    assert prefs.preferred_server == "1055@server1"
    assert len(prefs.license_order) == 2
    assert prefs.options["use_flexnet"] is True


def test_license_preferences_empty():
    """TC-2.8b: Test LicensePreferences with minimal data."""
    from ansys.tools.common.licensing.models import LicensePreferences

    prefs = LicensePreferences(path="/path/to/prefs.xml", preferred_server=None, license_order=[], options={})

    assert prefs.preferred_server is None
    assert prefs.license_order == []
