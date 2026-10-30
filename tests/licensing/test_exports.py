# Copyright (C) 2025 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for licensing module exports.

These tests verify that all public APIs are properly exported and accessible.
"""

import inspect


class TestModuleImports:
    """TC-20.1: Public API export tests."""

    def test_import_licensing_module(self):
        """TC-20.1.1: Module imports without error."""
        import ansys.tools.common.licensing

        assert ansys.tools.common.licensing is not None

    def test_all_functions_exported(self):
        """TC-20.1.2: All public functions accessible."""
        from ansys.tools.common.licensing import (
            check_feature,
            check_license_server_status,
            check_license_server_status_all,
            find_ansysli_util,
            find_ansyslmd_ini,
            find_license_log,
            find_license_preferences_xml,
            find_lmutil,
            get_license_environment,
            get_license_server,
            get_recent_license_errors,
            parse_ansyslmd_ini,
            parse_license_log,
            parse_license_preferences_xml,
        )

        # Verify all are callable
        assert callable(find_lmutil)
        assert callable(find_ansysli_util)
        assert callable(get_license_environment)
        assert callable(get_license_server)
        assert callable(find_ansyslmd_ini)
        assert callable(parse_ansyslmd_ini)
        assert callable(find_license_preferences_xml)
        assert callable(parse_license_preferences_xml)
        assert callable(find_license_log)
        assert callable(parse_license_log)
        assert callable(get_recent_license_errors)
        assert callable(check_license_server_status_all)
        assert callable(check_feature)
        assert callable(check_license_server_status)

    def test_all_models_exported(self):
        """TC-20.1.3: All dataclasses accessible."""
        from ansys.tools.common.licensing import (
            AnsyslmdConfig,
            FeatureInfo,
            LicenseEnvironment,
            LicenseLogInfo,
            LicensePreferences,
            LicenseServerStatus,
            LogEntry,
        )

        # Verify all are classes
        assert inspect.isclass(LicenseServerStatus)
        assert inspect.isclass(FeatureInfo)
        assert inspect.isclass(LicenseEnvironment)
        assert inspect.isclass(LogEntry)
        assert inspect.isclass(LicenseLogInfo)
        assert inspect.isclass(AnsyslmdConfig)
        assert inspect.isclass(LicensePreferences)

    def test_all_constants_exported(self):
        """TC-20.1.4: Constants accessible."""
        from ansys.tools.common.licensing import DEFAULT_VENDOR, VENDOR_INFO

        assert DEFAULT_VENDOR == "ansyslmd"
        assert isinstance(VENDOR_INFO, dict)
        assert "ansyslmd" in VENDOR_INFO

    def test_module_all_complete(self):
        """TC-20.1.5: __all__ is complete."""
        from ansys.tools.common import licensing

        expected_exports = [
            # Constants
            "DEFAULT_VENDOR",
            "VENDOR_INFO",
            # Models
            "AnsyslmdConfig",
            "FeatureInfo",
            "LicenseEnvironment",
            "LicenseLogInfo",
            "LicensePreferences",
            "LicenseServerStatus",
            "LogEntry",
            # Tools
            "find_lmutil",
            "find_ansysli_util",
            # Environment
            "get_license_environment",
            "get_license_server",
            # Config
            "find_ansyslmd_ini",
            "parse_ansyslmd_ini",
            "find_license_preferences_xml",
            "parse_license_preferences_xml",
            # Logs
            "find_license_log",
            "parse_license_log",
            "get_recent_license_errors",
            # Diagnosis
            "check_license_server_status_all",
            "check_feature",
            "check_license_server_status",
        ]

        for name in expected_exports:
            assert name in licensing.__all__, f"{name} missing from __all__"
            assert hasattr(licensing, name), f"{name} not accessible on module"


class TestExpectedExports:
    """TC-20.2: Verify specific expected exports."""

    def test_tools_exports(self):
        """Tools functions are exported."""
        from ansys.tools.common.licensing import find_ansysli_util, find_lmutil

        assert find_lmutil.__module__ == "ansys.tools.common.licensing.tools"
        assert find_ansysli_util.__module__ == "ansys.tools.common.licensing.tools"

    def test_environment_exports(self):
        """Environment functions are exported."""
        from ansys.tools.common.licensing import get_license_environment, get_license_server

        # Both are now in diagnosis module (comprehensive environment info)
        assert get_license_environment.__module__ == "ansys.tools.common.licensing.diagnosis"
        assert get_license_server.__module__ == "ansys.tools.common.licensing.diagnosis"

    def test_config_exports(self):
        """Config functions are exported."""
        from ansys.tools.common.licensing import (
            find_ansyslmd_ini,
            find_license_preferences_xml,
            parse_ansyslmd_ini,
            parse_license_preferences_xml,
        )

        assert find_ansyslmd_ini.__module__ == "ansys.tools.common.licensing.config"
        assert parse_ansyslmd_ini.__module__ == "ansys.tools.common.licensing.config"
        assert find_license_preferences_xml.__module__ == "ansys.tools.common.licensing.config"
        assert parse_license_preferences_xml.__module__ == "ansys.tools.common.licensing.config"

    def test_logs_exports(self):
        """Logs functions are exported."""
        from ansys.tools.common.licensing import (
            find_license_log,
            get_recent_license_errors,
            parse_license_log,
        )

        assert find_license_log.__module__ == "ansys.tools.common.licensing.logs"
        assert parse_license_log.__module__ == "ansys.tools.common.licensing.logs"
        assert get_recent_license_errors.__module__ == "ansys.tools.common.licensing.logs"

    def test_server_exports(self):
        """Server functions are exported."""
        from ansys.tools.common.licensing import (
            check_feature,
            check_license_server_status,
            check_license_server_status_all,
        )

        assert check_license_server_status_all.__module__ == "ansys.tools.common.licensing.diagnosis"
        assert check_feature.__module__ == "ansys.tools.common.licensing.diagnosis"
        assert check_license_server_status.__module__ == "ansys.tools.common.licensing.diagnosis"

    def test_models_are_dataclasses(self):
        """All models are dataclasses."""
        import dataclasses

        from ansys.tools.common.licensing import (
            AnsyslmdConfig,
            FeatureInfo,
            LicenseEnvironment,
            LicenseLogInfo,
            LicensePreferences,
            LicenseServerStatus,
            LogEntry,
        )

        assert dataclasses.is_dataclass(LicenseServerStatus)
        assert dataclasses.is_dataclass(FeatureInfo)
        assert dataclasses.is_dataclass(LicenseEnvironment)
        assert dataclasses.is_dataclass(LogEntry)
        assert dataclasses.is_dataclass(LicenseLogInfo)
        assert dataclasses.is_dataclass(AnsyslmdConfig)
        assert dataclasses.is_dataclass(LicensePreferences)


class TestCLIEntryPoint:
    """TC-21: CLI entry point tests."""

    def test_cli_module_importable(self):
        """TC-21.1.1: CLI module can be imported."""
        from ansys.tools.common.licensing._cli import cli

        assert cli is not None
        assert callable(cli)

    def test_cli_has_commands(self):
        """CLI exposes the expected canonical (kebab-case) commands."""
        from ansys.tools.common.licensing._cli import cli

        # cli is a click.Group, check it has commands
        assert hasattr(cli, "commands")
        commands = cli.commands

        expected_commands = [
            "get-server",
            "set-server",
            "check-server",
            "get-env",
            "get-config",
            "get-features",
            "check-feature",
            "checkout",
        ]
        for cmd_name in expected_commands:
            assert cmd_name in commands, f"Command '{cmd_name}' missing from CLI"

    def test_cli_deprecated_aliases_resolve(self):
        """Deprecated concatenated command names still resolve to canonical commands."""
        import warnings

        import click

        from ansys.tools.common.licensing._cli import _COMMAND_ALIASES, cli

        ctx = click.Context(cli)
        for alias, canonical in _COMMAND_ALIASES.items():
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                resolved = cli.get_command(ctx, alias)
            assert resolved is not None, f"Alias '{alias}' did not resolve"
            assert resolved is cli.get_command(ctx, canonical), (
                f"Alias '{alias}' did not resolve to canonical command '{canonical}'"
            )
            assert any(issubclass(w.category, DeprecationWarning) for w in caught), (
                f"Alias '{alias}' did not emit a DeprecationWarning"
            )


class TestDocstrings:
    """TC-23: Documentation tests."""

    def test_all_functions_have_docstrings(self):
        """TC-23.1.1: All public functions have docstrings."""
        from ansys.tools.common.licensing import (
            check_feature,
            check_license_server_status,
            check_license_server_status_all,
            find_ansysli_util,
            find_ansyslmd_ini,
            find_license_log,
            find_license_preferences_xml,
            find_lmutil,
            get_license_environment,
            get_license_server,
            get_recent_license_errors,
            parse_ansyslmd_ini,
            parse_license_log,
            parse_license_preferences_xml,
        )

        functions = [
            find_lmutil,
            find_ansysli_util,
            get_license_environment,
            get_license_server,
            find_ansyslmd_ini,
            parse_ansyslmd_ini,
            find_license_preferences_xml,
            parse_license_preferences_xml,
            find_license_log,
            parse_license_log,
            get_recent_license_errors,
            check_license_server_status_all,
            check_feature,
            check_license_server_status,
        ]

        for func in functions:
            assert func.__doc__ is not None, f"{func.__name__} missing docstring"
            assert len(func.__doc__) > 20, f"{func.__name__} docstring too short"

    def test_docstrings_have_parameters(self):
        """TC-23.1.2: Key docstrings include Parameters section."""
        from ansys.tools.common.licensing import (
            check_license_server_status_all,
        )

        # Check key functions have Parameters section
        assert "Parameters" in check_license_server_status_all.__doc__

    def test_docstrings_have_returns(self):
        """TC-23.1.3: Key docstrings include Returns section."""
        from ansys.tools.common.licensing import (
            check_license_server_status_all,
        )

        # Check key functions have Returns section
        assert "Returns" in check_license_server_status_all.__doc__

    def test_docstrings_have_examples(self):
        """TC-23.1.4: Key functions have examples."""
        from ansys.tools.common.licensing import (
            check_license_server_status_all,
        )

        # Check key functions have Examples section
        assert "Examples" in check_license_server_status_all.__doc__

    def test_models_have_docstrings(self):
        """All model classes have docstrings."""
        from ansys.tools.common.licensing import (
            AnsyslmdConfig,
            FeatureInfo,
            LicenseEnvironment,
            LicenseLogInfo,
            LicensePreferences,
            LicenseServerStatus,
            LogEntry,
        )

        models = [
            LicenseServerStatus,
            FeatureInfo,
            LicenseEnvironment,
            LogEntry,
            LicenseLogInfo,
            AnsyslmdConfig,
            LicensePreferences,
        ]

        for model in models:
            assert model.__doc__ is not None, f"{model.__name__} missing docstring"


class TestVendorInfo:
    """Test VENDOR_INFO structure."""

    def test_vendor_info_structure(self):
        """VENDOR_INFO has expected structure."""
        from ansys.tools.common.licensing import VENDOR_INFO

        assert "ansyslmd" in VENDOR_INFO

        ansyslmd_info = VENDOR_INFO["ansyslmd"]
        assert "env_vars" in ansyslmd_info
        assert "config_file" in ansyslmd_info
        assert "description" in ansyslmd_info

        assert isinstance(ansyslmd_info["env_vars"], list)
        assert "ANSYSLMD_LICENSE_FILE" in ansyslmd_info["env_vars"]
        assert ansyslmd_info["config_file"] == "ansyslmd.ini"
