# Copyright (C) 2025 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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

"""Command-line interface for Ansys licensing utilities.

.. deprecated:: 0.6
    The old concatenated command names (``getserver``, ``setserver``, and so
    on) are still accepted for backward compatibility but emit a
    :class:`DeprecationWarning`. Migrate to the kebab-case equivalents listed
    below.

This module provides a CLI for querying license server status, checking
feature availability, and inspecting license configuration.

The following commands are available:

``get-server``
    Show the current effective license server.
``set-server``
    Set the license server (with subcommands for different targets). Includes a
    ``restore`` subgroup (``set-server restore env`` / ``set-server restore
    config``) that reverts the license server to its originally detected value.
``check-server``
    Check connectivity to a license server.
``get-env``
    Show license-related environment variables.
``get-config``
    Show license configuration files.
``get-features``
    Show all available license features.
``check-feature``
    Check the status of a specific license feature.
``checkout``
    Test checkout of a license feature.
"""

import dataclasses
import json
import logging
import os
import re
from typing import Any
import warnings

import click

from ansys.tools.common.exceptions import (
    LicenseConfigError,
    LicenseError,
    LicenseServerError,
    LicenseToolNotFoundError,
)
from ansys.tools.common.licensing import DEFAULT_VENDOR
from ansys.tools.common.licensing.config import (
    capture_env_original,
    find_ansyslmd_ini,
    parse_ansyslmd_ini,
    restore_env,
    restore_ini,
    set_ansyslmd_ini,
)
from ansys.tools.common.licensing.diagnosis import (
    check_feature,
    check_license_server_status,
    get_license_features,
    get_license_server,
    get_license_server_with_source,
    test_license_checkout,
)
from ansys.tools.common.licensing.vars import (
    detect_shell,
    get_awp_root_versions,
    get_license_vars,
    get_shell_rc_file,
    set_env_unix,
    set_env_windows,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Backward-compatible alias support for kebab-case command migration
# ---------------------------------------------------------------------------

# Maps old concatenated names to canonical kebab-case names.
_COMMAND_ALIASES: dict[str, str] = {
    "getserver": "get-server",
    "setserver": "set-server",
    "checkserver": "check-server",
    "getenv": "get-env",
    "getconfig": "get-config",
    "getfeatures": "get-features",
    "checkfeature": "check-feature",
}


class _AliasGroup(click.Group):
    """Click group that transparently resolves deprecated command aliases.

    Old concatenated command names (e.g. ``getserver``) are accepted but
    emit a :class:`DeprecationWarning` directing the caller to the new
    kebab-case name (``get-server``).
    """

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        # Try the canonical name first (fast path).
        rv = super().get_command(ctx, cmd_name)
        if rv is not None:
            return rv

        # Fall back to the alias map.
        canonical = _COMMAND_ALIASES.get(cmd_name)
        if canonical is not None:
            warnings.warn(
                f"Command '{cmd_name}' is deprecated. Use '{canonical}' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return super().get_command(ctx, canonical)

        return None

    def list_commands(self, ctx: click.Context) -> list[str]:
        # Only expose canonical kebab-case names in --help output.
        return super().list_commands(ctx)


# Backward-compatible private aliases. These names are referenced by existing
# tests (e.g. patching ``ansys.tools.common.licensing._cli._set_env_windows``)
# and by the CLI commands below via this module's namespace.
_set_env_windows = set_env_windows
_set_env_unix = set_env_unix
_detect_shell = detect_shell
_get_shell_rc_file = get_shell_rc_file


def _dataclass_to_dict(obj: Any) -> dict[str, Any]:
    """Convert a dataclass instance to a dictionary, handling nested dataclasses."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        result = {}
        for field in dataclasses.fields(obj):
            value = getattr(obj, field.name)
            result[field.name] = _dataclass_to_dict(value)
        return result
    elif isinstance(obj, list):
        return [_dataclass_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    else:
        # Handle datetime and other non-serializable types
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return obj


def _echo_json(data: Any) -> None:
    """Emit *data* as pretty-printed JSON to stdout.

    If *data* is a dataclass instance it is converted via
    ``_dataclass_to_dict`` first.
    """
    if dataclasses.is_dataclass(data) and not isinstance(data, type):
        data = _dataclass_to_dict(data)
    click.echo(json.dumps(data, indent=2))


def _output(data: Any, as_json: bool, text_fn: Any) -> None:
    """Output *data* as JSON or formatted text.

    Parameters
    ----------
    data : Any
        Structured data (dict or dataclass) for JSON output.
    as_json : bool
        If ``True``, emit JSON via ``_echo_json``. Otherwise call *text_fn*.
    text_fn : callable
        Zero-argument callable that emits human-readable text via ``click.echo``.
    """
    if as_json:
        _echo_json(data)
    else:
        text_fn()


# Pattern: port@hostname where port is a number and hostname is non-empty
_SERVER_FORMAT_RE = re.compile(r"^\d+@\S+$")


def _validate_server_format(server: str) -> None:
    """Validate that a server string is in port@hostname format.

    Parameters
    ----------
    server : str
        The server string to validate.

    Raises
    ------
    click.BadParameter
        If the server string is not in the expected format.
    """
    if not _SERVER_FORMAT_RE.match(server):
        raise click.BadParameter(
            f"Invalid server format: '{server}'. Expected format: port@hostname (e.g., 1055@license-server).",
            param_hint="'SERVER'",
        )


@click.group(cls=_AliasGroup)
@click.version_option(package_name="ansys-tools-common")
def cli() -> None:
    """Ansys licensing utilities CLI.

    Query license server status, check feature availability, and inspect
    license configuration.
    """
    pass


@cli.command("get-server")
@click.option("--vendor", "-v", default=DEFAULT_VENDOR, help="Vendor daemon name")
@click.option("--json", "as_json", is_flag=True, help="Output in JSON format")
def getserver_cmd(vendor: str, as_json: bool) -> None:
    """Show the current effective license server used by Ansys applications.

    Displays the license server that will be used based on the priority order:

    1. ANSYSLMD_LICENSE_FILE environment variable
    2. ANSYSLI_SERVERS environment variable
    3. SERVER value from user ansyslmd.ini
    4. SERVER value from installation ansyslmd.ini
    """
    logger.debug("CLI command: getserver (vendor=%s)", vendor)
    server, source = get_license_server_with_source(vendor=vendor)

    def _text() -> None:
        if server:
            click.echo(f"Effective License Server: {server}")
            if source:
                click.echo(f"Source: {source}")
            else:
                click.echo("Source: Environment variable")
        else:
            click.echo("No license server configured.")
            click.echo("Set ANSYSLMD_LICENSE_FILE or configure ansyslmd.ini.")

    _output(
        {
            "server": server,
            "source": source,
            "source_type": "environment" if source is None and server else "config_file" if source else "none",
        },
        as_json,
        _text,
    )


# ============================================================================
# setserver command group
# ============================================================================


@cli.group("set-server")
def setserver_group() -> None:
    r"""Set the license server configuration.

    Use one of the subcommands to specify where to store the license server::

      env    - Set ANSYSLMD_LICENSE_FILE as persistent environment variable
      config - Set SERVER in ansyslmd.ini configuration file
    """
    pass


@setserver_group.command("env")
@click.argument("server")
@click.option(
    "--scope",
    "-s",
    type=click.Choice(["user", "system"]),
    default="user",
    help="Set for current user or system-wide (system requires admin)",
)
@click.option(
    "--shell",
    type=click.Choice(["auto", "bash", "zsh", "sh", "csh", "tcsh", "fish"]),
    default="auto",
    help="Shell type for rc file on Linux/macOS (default: auto-detect)",
)
@click.option("--json", "as_json", is_flag=True, help="Output in JSON format")
def setserver_env_cmd(server: str, scope: str, shell: str, as_json: bool) -> None:
    r"""Set ANSYSLMD_LICENSE_FILE as a persistent environment variable.

    SERVER: License server in port@host format (e.g., 1055@license-server)

    This persistently sets the environment variable so it survives reboots.

    On Windows::

      --scope user   : Sets in HKEY_CURRENT_USER (default)
      --scope system : Sets in HKEY_LOCAL_MACHINE (requires admin)

    On Linux/macOS, this adds an export to the appropriate shell rc file based
    on the --shell option::

      auto (default) - Detects from $SHELL environment variable
      bash           - ~/.bashrc
      zsh            - ~/.zshrc
      sh             - ~/.profile
      csh/tcsh       - ~/.cshrc
      fish           - ~/.config/fish/config.fish

    System scope on Linux/macOS is not supported (use /etc/environment
    manually).
    """
    _validate_server_format(server)

    # Capture the pre-change original ANSYSLMD_LICENSE_FILE value (write-once).
    capture_env_original()

    try:
        if os.name == "nt":
            rc_file = _set_env_windows(server, scope)
        else:
            if scope == "system":
                raise LicenseConfigError(
                    "System-wide environment variables on Linux/macOS must be set manually. "
                    "Edit /etc/environment or use your distribution's mechanism."
                )
            rc_file = _set_env_unix(server, shell)

        if as_json:
            result = {
                "success": True,
                "server": server,
                "target": "env",
                "scope": scope,
                "rc_file": rc_file,
                "message": f"ANSYSLMD_LICENSE_FILE set persistently for {scope}",
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Set ANSYSLMD_LICENSE_FILE={server}")
            click.echo(f"Scope: {scope}")
            click.echo(f"Config file: {rc_file}")
            click.echo("")
            click.echo("This change is persistent and will survive reboots.")
            if os.name == "nt":
                click.echo("Note: You may need to restart applications or open a new terminal to see the change.")
            else:
                click.echo(f"Note: Run 'source {rc_file}' or open a new terminal to apply.")

    except LicenseConfigError as e:
        if as_json:
            result = {
                "success": False,
                "server": server,
                "target": "env",
                "scope": scope,
                "error": str(e),
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@setserver_group.command("config")
@click.argument("server")
@click.option(
    "--scope",
    "-s",
    type=click.Choice(["user", "installation"]),
    default="user",
    help="Config scope: user (~/.ansys_licensing/) or installation ($ANSYSLIC_DIR/)",
)
@click.option("--json", "as_json", is_flag=True, help="Output in JSON format")
def setserver_config_cmd(server: str, scope: str, as_json: bool) -> None:
    r"""Set SERVER in ansyslmd.ini configuration file.

    SERVER: License server in port@host format (e.g., 1055@license-server)

    Creates or updates the ansyslmd.ini file with the specified license server.

    Scopes::

      user         - User config at ~/.ansys_licensing/ansyslmd.ini (default)
      installation - Installation config at $ANSYSLIC_DIR/ansyslmd.ini
                     (may require admin privileges)
    """
    _validate_server_format(server)

    try:
        config_path = set_ansyslmd_ini(server=server, scope=scope)

        if as_json:
            result = {
                "success": True,
                "server": server,
                "target": "config",
                "scope": scope,
                "path": config_path,
                "message": f"SERVER set in {scope} ansyslmd.ini",
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Set SERVER={server}")
            click.echo(f"Config file: {config_path}")
            click.echo(f"Scope: {scope}")

    except LicenseConfigError as e:
        if as_json:
            result = {
                "success": False,
                "server": server,
                "target": "config",
                "scope": scope,
                "error": str(e),
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


# ============================================================================
# set-server restore subcommand group
# ============================================================================


@setserver_group.group("restore")
def setserver_restore_group() -> None:
    r"""Restore the license server to its originally detected value.

    The original value is the one captured the first time it was detected by the
    licensing utilities (stored in the licensing config.txt). Use a subcommand to
    choose what to restore::

      env    - Restore ANSYSLMD_LICENSE_FILE to its original value (or remove it)
      config - Restore SERVER in ansyslmd.ini to its original value (or remove it)
    """
    pass


@setserver_restore_group.command("env")
@click.option(
    "--scope",
    "-s",
    type=click.Choice(["user", "system"]),
    default="user",
    help="Restore for current user or system-wide (system requires admin)",
)
@click.option(
    "--shell",
    type=click.Choice(["auto", "bash", "zsh", "sh", "csh", "tcsh", "fish"]),
    default="auto",
    help="Shell type for rc file on Linux/macOS (default: auto-detect)",
)
@click.option("--json", "as_json", is_flag=True, help="Output in JSON format")
def setserver_restore_env_cmd(scope: str, shell: str, as_json: bool) -> None:
    r"""Restore ANSYSLMD_LICENSE_FILE to its originally detected value.

    If the variable was set when first detected, it is restored to that value.
    If it was unset when first detected, the persistent variable is removed.
    """
    logger.debug("CLI command: set-server restore env (scope=%s)", scope)
    try:
        removed, value = restore_env(scope=scope, shell=shell)

        if as_json:
            result: dict[str, Any] = {
                "success": True,
                "target": "env",
                "action": "restore",
                "scope": scope,
                "removed": removed,
                "server": value,
            }
            click.echo(json.dumps(result, indent=2))
        else:
            if removed:
                click.echo("Removed ANSYSLMD_LICENSE_FILE (original was unset).")
            else:
                click.echo(f"Restored ANSYSLMD_LICENSE_FILE={value}")
            click.echo(f"Scope: {scope}")
            click.echo("")
            click.echo("This change is persistent and will survive reboots.")
            if os.name == "nt":
                click.echo("Note: You may need to restart applications or open a new terminal to see the change.")
            else:
                click.echo("Note: Open a new terminal or re-source your shell rc file to apply.")

    except LicenseConfigError as e:
        if as_json:
            result = {
                "success": False,
                "target": "env",
                "action": "restore",
                "scope": scope,
                "error": str(e),
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@setserver_restore_group.command("config")
@click.option(
    "--scope",
    "-s",
    type=click.Choice(["user", "installation"]),
    default="user",
    help="Config scope: user (~/.ansys_licensing/) or installation ($ANSYSLIC_DIR/)",
)
@click.option("--json", "as_json", is_flag=True, help="Output in JSON format")
def setserver_restore_config_cmd(scope: str, as_json: bool) -> None:
    r"""Restore SERVER in ansyslmd.ini to its originally detected value.

    If a SERVER was configured when first detected, it is restored to that value.
    If none was configured, the SERVER line is removed from the ansyslmd.ini file.
    """
    logger.debug("CLI command: set-server restore config (scope=%s)", scope)
    try:
        removed, value = restore_ini(scope)

        if as_json:
            result: dict[str, Any] = {
                "success": True,
                "target": "config",
                "action": "restore",
                "scope": scope,
                "removed": removed,
                "server": value,
            }
            click.echo(json.dumps(result, indent=2))
        else:
            if removed:
                click.echo(f"Removed SERVER from {scope} ansyslmd.ini (original was unset).")
            else:
                click.echo(f"Restored SERVER={value} in {scope} ansyslmd.ini")
            click.echo(f"Scope: {scope}")

    except LicenseConfigError as e:
        if as_json:
            result = {
                "success": False,
                "target": "config",
                "action": "restore",
                "scope": scope,
                "error": str(e),
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command("check-server")
@click.argument("server")
@click.option("--vendor", "-v", default=DEFAULT_VENDOR, help="Vendor daemon name")
@click.option("--timeout", "-t", default=10, type=int, help="Timeout in seconds")
@click.option("--json", "as_json", is_flag=True, help="Output in JSON format")
def checkserver_cmd(server: str, vendor: str, timeout: int, as_json: bool) -> None:
    """Check connectivity to a license server.

    SERVER: License server in port@host format (e.g., 1055@license-server)

    Tests license server connectivity and shows detailed status including:
    - License server manager (lmgrd) status
    - Vendor daemon status
    - Version information if available
    - Error messages for troubleshooting if connection fails
    """
    logger.debug("CLI command: checkserver %s (vendor=%s, timeout=%d)", server, vendor, timeout)
    _validate_server_format(server)
    result = check_license_server_status(server, vendor=vendor, timeout=timeout)

    def _text() -> None:
        click.echo(f"Server: {result.server}")
        click.echo("-" * 50)

        # lmgrd status
        lmgrd_status = "UP" if result.lmgrd_up else "DOWN"
        lmgrd_line = f"  License Manager (lmgrd): {lmgrd_status}"
        if result.lmgrd_version:
            lmgrd_line += f" ({result.lmgrd_version})"
        click.echo(lmgrd_line)

        # Vendor daemon status
        vendor_status = "UP" if result.vendor_daemon_up else "DOWN"
        vendor_line = f"  Vendor Daemon ({result.vendor}): {vendor_status}"
        if result.vendor_daemon_version:
            vendor_line += f" ({result.vendor_daemon_version})"
        click.echo(vendor_line)

        # Error message if any
        if result.error_message:
            click.echo("")
            click.echo(f"Error: {result.error_message}")

        # Exit with error code if server is not fully up
        if not result.lmgrd_up or not result.vendor_daemon_up:
            raise SystemExit(1)

    _output(
        {
            "server": result.server,
            "vendor": result.vendor,
            "lmgrd_up": result.lmgrd_up,
            "vendor_daemon_up": result.vendor_daemon_up,
            "lmgrd_version": result.lmgrd_version,
            "vendor_daemon_version": result.vendor_daemon_version,
            "error_type": result.error_type,
            "error_message": result.error_message,
        },
        as_json,
        _text,
    )


@cli.command("get-env")
@click.option("--vendor", "-v", default=DEFAULT_VENDOR, help="Vendor daemon name")
@click.option("--json", "as_json", is_flag=True, help="Output in JSON format")
def getenv_cmd(vendor: str, as_json: bool) -> None:
    """Show all Ansys license-related environment variables.

    Displays the values of license-related environment variables including
    ANSYSLMD_LICENSE_FILE, ANSYSLI_SERVERS, ANSYSLIC_DIR, and AWP_ROOT variables.
    """
    env_vars = get_license_vars(vendor=vendor)

    # Get AWP_ROOTxxx variables for installed Ansys versions
    awp_versions = get_awp_root_versions()
    awp_vars: dict[str, str] = {}
    for ver, path in awp_versions.items():
        # Handle negative version numbers (student editions)
        if ver < 0:
            awp_vars[f"AWP_ROOT{abs(ver)} (Student)"] = path
        else:
            awp_vars[f"AWP_ROOT{ver}"] = path

    def _text() -> None:
        click.echo("License Environment Variables:")
        click.echo("-" * 50)
        for name, value in env_vars.items():
            if value:
                click.echo(f"  {name}={value}")
            else:
                click.echo(f"  {name}: (not set)")

        # Show AWP_ROOT variables if any are found
        if awp_vars:
            click.echo("")
            click.echo("Ansys Installation Paths (AWP_ROOT):")
            click.echo("-" * 50)
            for name, path in sorted(awp_vars.items()):
                click.echo(f"  {name}={path}")

    _output({**env_vars, **awp_vars}, as_json, _text)


@cli.command("get-config")
@click.option("--json", "as_json", is_flag=True, help="Output in JSON format")
def getconfig_cmd(as_json: bool) -> None:
    """Show license configuration files and the one in effect.

    Displays both user-scope and installation-scope ansyslmd.ini files,
    indicating which one is currently in effect based on priority.
    """
    results: dict[str, Any] = {
        "user_config": None,
        "installation_config": None,
        "effective_config": None,
    }

    # Check user-scope config
    user_ini_path = find_ansyslmd_ini(scope="user")
    if user_ini_path:
        try:
            user_config = parse_ansyslmd_ini(user_ini_path)
            results["user_config"] = _dataclass_to_dict(user_config)
        except LicenseError:
            results["user_config"] = {"path": user_ini_path, "error": "Failed to parse"}

    # Check installation-scope config
    install_ini_path = find_ansyslmd_ini(scope="installation")
    if install_ini_path:
        try:
            install_config = parse_ansyslmd_ini(install_ini_path)
            results["installation_config"] = _dataclass_to_dict(install_config)
        except LicenseError:
            results["installation_config"] = {"path": install_ini_path, "error": "Failed to parse"}

    # Determine which config is in effect (user takes priority if it has a server)
    if results["user_config"] and results["user_config"].get("server"):
        results["effective_config"] = "user"
    elif results["installation_config"] and results["installation_config"].get("server"):
        results["effective_config"] = "installation"
    else:
        results["effective_config"] = None

    if as_json:
        _echo_json(results)
    else:
        click.echo("License Configuration Files:")
        click.echo("=" * 60)

        # User config
        click.echo("\n[User Config]")
        if results["user_config"]:
            if "error" in results["user_config"]:
                click.echo(f"  Path: {results['user_config']['path']}")
                click.echo(f"  Error: {results['user_config']['error']}")
            else:
                click.echo(f"  Path: {results['user_config']['path']}")
                click.echo(f"  Server: {results['user_config'].get('server') or '(not set)'}")
                if results["user_config"].get("options"):
                    click.echo("  Options:")
                    for k, v in results["user_config"]["options"].items():
                        click.echo(f"    {k}={v}")
        else:
            click.echo("  (not found)")

        # Installation config
        click.echo("\n[Installation Config]")
        if results["installation_config"]:
            if "error" in results["installation_config"]:
                click.echo(f"  Path: {results['installation_config']['path']}")
                click.echo(f"  Error: {results['installation_config']['error']}")
            else:
                click.echo(f"  Path: {results['installation_config']['path']}")
                click.echo(f"  Server: {results['installation_config'].get('server') or '(not set)'}")
                if results["installation_config"].get("options"):
                    click.echo("  Options:")
                    for k, v in results["installation_config"]["options"].items():
                        click.echo(f"    {k}={v}")
        else:
            click.echo("  (not found)")

        # Effective config
        click.echo("\n" + "-" * 60)
        if results["effective_config"]:
            click.echo(f"Effective Config: {results['effective_config']} (has SERVER defined)")
        else:
            click.echo("Effective Config: None (no SERVER defined in any config file)")


@cli.command("get-features")
@click.option("--server", "-s", help="License server in port@host format (uses effective server if not specified)")
@click.option("--vendor", "-v", default=DEFAULT_VENDOR, help="Vendor daemon name")
@click.option("--timeout", "-t", default=30, type=int, help="Timeout in seconds")
@click.option("--json", "as_json", is_flag=True, help="Output in JSON format")
def getfeatures_cmd(
    server: str | None,
    vendor: str,
    timeout: int,
    as_json: bool,
) -> None:
    """Show all available license features from the server.

    Lists all license features available on the server along with their
    total count and current usage.
    """
    logger.debug("CLI command: getfeatures (server=%s, vendor=%s)", server, vendor)
    try:
        # Determine effective server if not specified
        effective_server = server or get_license_server(vendor=vendor)
        if not effective_server:
            click.echo("Error: No license server specified and none found in configuration.", err=True)
            click.echo("Use --server option or configure ANSYSLMD_LICENSE_FILE.", err=True)
            raise SystemExit(1)

        features = get_license_features(
            server=effective_server,
            vendor=vendor,
            timeout=timeout,
        )

        def _text() -> None:
            click.echo(f"License Features from {effective_server}:")
            click.echo("=" * 60)
            if not features:
                click.echo("  No features found (server may be down or have no features)")
            else:
                # Sort features alphabetically
                for name in sorted(features.keys()):
                    f = features[name]
                    if f.total == -1:
                        click.echo(f"  {f.name}: uncounted (unlimited)")
                    else:
                        available = f.total - f.in_use
                        click.echo(f"  {f.name}: {available}/{f.total} available ({f.in_use} in use)")
                click.echo(f"\nTotal: {len(features)} features")

        _output(
            {
                "server": effective_server,
                "features": {name: _dataclass_to_dict(f) for name, f in features.items()},
            },
            as_json,
            _text,
        )

    except LicenseToolNotFoundError as e:
        logger.error("getfeatures failed: %s", e)
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except LicenseServerError as e:
        logger.error("getfeatures failed: %s", e)
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command("check-feature")
@click.argument("feature")
@click.option("--server", "-s", help="License server in port@host format (uses effective server if not specified)")
@click.option("--vendor", "-v", default=DEFAULT_VENDOR, help="Vendor daemon name")
@click.option("--timeout", "-t", default=30, type=int, help="Timeout in seconds")
@click.option("--json", "as_json", is_flag=True, help="Output in JSON format")
def checkfeature_cmd(
    feature: str,
    server: str | None,
    vendor: str,
    timeout: int,
    as_json: bool,
) -> None:
    """Check the status of a specific license feature.

    FEATURE: License feature name to check (e.g., mechanical_enterprise, fluent_solver)

    Queries the license server to show the availability and usage of the specified feature.
    """
    logger.debug("CLI command: checkfeature %s (server=%s, vendor=%s)", feature, server, vendor)
    try:
        # Determine effective server if not specified
        effective_server = server or get_license_server(vendor=vendor)
        if not effective_server:
            click.echo("Error: No license server specified and none found in configuration.", err=True)
            raise SystemExit(1)

        info = check_feature(
            feature=feature,
            server=effective_server,
            vendor=vendor,
            timeout=timeout,
        )

        if info:
            json_data: dict[str, Any] = {
                "server": effective_server,
                "found": True,
                "feature": _dataclass_to_dict(info),
            }
        else:
            json_data = {
                "server": effective_server,
                "found": False,
                "feature": feature,
            }

        def _text() -> None:
            if info:
                click.echo(f"Feature: {info.name}")
                click.echo(f"Server: {effective_server}")
                if info.total == -1:
                    click.echo("Status: Uncounted (unlimited)")
                else:
                    available = info.total - info.in_use
                    status = "AVAILABLE" if available > 0 else "EXHAUSTED"
                    click.echo(f"Total Licenses: {info.total}")
                    click.echo(f"In Use: {info.in_use}")
                    click.echo(f"Available: {available}")
                    click.echo(f"Status: {status}")
            else:
                click.echo(f"Feature '{feature}' not found on server {effective_server}")
                raise SystemExit(1)

        _output(json_data, as_json, _text)

    except LicenseError as e:
        logger.error("checkfeature '%s' failed: %s", feature, e)
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command("checkout")
@click.argument("feature")
@click.option("--timeout", "-t", default=30, type=int, help="Timeout in seconds")
@click.option("--json", "as_json", is_flag=True, help="Output in JSON format")
def checkout_cmd(
    feature: str,
    timeout: int,
    as_json: bool,
) -> None:
    """Test checkout of a license feature.

    FEATURE: License feature name to test checkout (e.g., mechanical_enterprise, ansys)

    Performs a test license checkout using ansysli_util to verify that the current
    user/host can successfully checkout the specified license feature. This is useful
    for diagnosing licensing issues before running an Ansys application.
    """
    logger.debug("CLI command: checkout %s (timeout=%d)", feature, timeout)
    try:
        result = test_license_checkout(
            feature=feature,
            timeout=timeout,
        )

        def _text() -> None:
            click.echo(f"Feature: {result.feature}")
            if result.success:
                click.echo("Result: SUCCESS")
                if result.server:
                    click.echo(f"Server: {result.server}")
                if result.license_path:
                    click.echo(f"License Path: {result.license_path}")
            else:
                click.echo("Result: FAILED")
                if result.error_type:
                    click.echo(f"Error Type: {result.error_type}")
                if result.error_code:
                    click.echo(f"Error Code: {result.error_code}")
                if result.error_message:
                    click.echo(f"Message: {result.error_message}")
                if result.server:
                    click.echo(f"Server: {result.server}")
                raise SystemExit(1)

        _output(result, as_json, _text)

    except LicenseToolNotFoundError as e:
        logger.error("checkout '%s' failed: %s", feature, e)
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
