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

"""License diagnosis and troubleshooting utilities.

This module provides functions to diagnose license server connectivity,
query license status, and troubleshoot licensing issues using lmutil commands.

It also provides the `get_license_server()` function which determines the
effective license server based on priority:

1. ANSYSLMD_LICENSE_FILE environment variable
2. ANSYSLI_SERVERS environment variable
3. SERVER value from user ansyslmd.ini configuration file
4. SERVER value from installation ansyslmd.ini configuration file
"""

import logging
import re
import subprocess

from ansys.tools.common.exceptions import (
    LicenseFileParseError,
    LicenseServerError,
    LicenseToolNotFoundError,
)
from ansys.tools.common.licensing.config import find_ansyslmd_ini, parse_ansyslmd_ini
from ansys.tools.common.licensing.models import (
    FeatureInfo,
    LicenseCheckoutResult,
    LicenseEnvironment,
    LicenseErrorType,
    LicenseServerStatus,
    ServerTestResult,
)
from ansys.tools.common.licensing.tools import find_ansysli_util, find_lmutil
from ansys.tools.common.licensing.vars import (
    get_awp_root_versions,
    get_license_server_from_env,
    get_license_vars,
)

# Default timeout for lmutil commands (seconds)
DEFAULT_TIMEOUT = 30

logger = logging.getLogger(__name__)


def _run_license_tool(cmd: list[str], timeout: int, tool_name: str) -> str:
    """Execute a licensing tool command and return combined stdout+stderr.

    Parameters
    ----------
    cmd : list[str]
        Command and arguments to execute.
    timeout : int
        Timeout in seconds.
    tool_name : str
        Human-readable name of the tool (for error messages).

    Returns
    -------
    str
        Combined stdout and stderr output.

    Raises
    ------
    LicenseServerError
        If the command times out or fails to execute.
    """
    try:
        logger.debug("Running %s command: %s (timeout=%ds)", tool_name, " ".join(cmd), timeout)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        output = result.stdout + result.stderr
        logger.debug("%s returned %d bytes of output", tool_name, len(output))
        return output
    except subprocess.TimeoutExpired as e:
        logger.warning("%s command timed out after %d seconds", tool_name, timeout)
        raise LicenseServerError(f"{tool_name} command timed out after {timeout} seconds") from e
    except OSError as e:
        logger.warning("Failed to execute %s: %s", tool_name, e)
        raise LicenseServerError(f"Failed to execute {tool_name}: {e}") from e


def _run_license_tool_safe(cmd: list[str], timeout: int, tool_name: str) -> tuple[str, str | None]:
    """Execute a licensing tool command, returning output and optional error.

    Unlike ``_run_license_tool``, this function does not raise on timeout
    or OS errors.  Instead it returns a tuple so callers can embed the
    error into a result dataclass.

    Parameters
    ----------
    cmd : list[str]
        Command and arguments to execute.
    timeout : int
        Timeout in seconds.
    tool_name : str
        Human-readable name of the tool (for error messages).

    Returns
    -------
    tuple[str, str | None]
        ``(raw_output, None)`` on success, or ``(partial_output, error_message)``
        on failure.
    """
    try:
        logger.debug("Running %s command: %s (timeout=%ds)", tool_name, " ".join(cmd), timeout)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        output = result.stdout + result.stderr
        logger.debug("%s returned %d bytes of output", tool_name, len(output))
        return output, None
    except subprocess.TimeoutExpired as e:
        logger.warning("%s timed out after %d seconds", tool_name, timeout)
        return str(e), f"{tool_name} timed out after {timeout} seconds"
    except OSError as e:
        logger.warning("Failed to execute %s: %s", tool_name, e)
        return str(e), f"Failed to execute {tool_name}: {e}"


# Regular expressions for parsing lmstat output
# Matches: "hostname: license server UP (MASTER) v11.18.1"
SERVER_UP_PATTERN = re.compile(r"^\s*\S+:\s*license server\s+UP", re.IGNORECASE | re.MULTILINE)

# Matches: "Cannot connect to license server" or similar down messages
SERVER_DOWN_PATTERNS = [
    re.compile(r"Cannot connect to license server", re.IGNORECASE),
    re.compile(r"license server manager.*not.*started", re.IGNORECASE),
    re.compile(r"Error getting status", re.IGNORECASE),
    re.compile(r"Connection refused", re.IGNORECASE),
]

# Matches: "vendordaemon: UP v11.18.1"
VENDOR_UP_PATTERN = re.compile(r"^\s*(\w+):\s*UP", re.IGNORECASE | re.MULTILINE)

# Matches: "vendordaemon: DOWN" or vendor not found or connection errors
VENDOR_DOWN_PATTERNS = [
    re.compile(r"^\s*(\w+):\s*DOWN", re.IGNORECASE | re.MULTILINE),
    re.compile(r"Cannot find license file", re.IGNORECASE),
    re.compile(r"No socket connection to license server manager", re.IGNORECASE),
]

# Matches: "Users of feature_name:  (Total of X licenses issued;  Total of Y licenses in use)"
FEATURE_USAGE_PATTERN = re.compile(
    r"Users of (\S+):\s*\(Total of (\d+) licenses? issued;\s*Total of (\d+) licenses? in use\)",
    re.IGNORECASE,
)

# Matches uncounted features: "Users of feature_name:  (Uncounted, node-locked)"
FEATURE_UNCOUNTED_PATTERN = re.compile(r"Users of (\S+):\s*\(Uncounted", re.IGNORECASE)

# Error patterns for connection issues
# Matches: "Cannot connect to license server system" with "Connection refused"
CONNECTION_REFUSED_PATTERN = re.compile(
    r"Cannot connect to license server system.*Connection refused", re.IGNORECASE | re.DOTALL
)

# Matches: "License server machine is down or not responding" with "Host not found"
HOST_NOT_FOUND_PATTERN = re.compile(
    r"License server machine is down or not responding.*Host not found", re.IGNORECASE | re.DOTALL
)

# Matches lmgrd version: "hostname: license server UP (MASTER) v11.18.1" or "v11.18.1"
LMGRD_VERSION_PATTERN = re.compile(r"license server\s+UP.*?(v\d+\.\d+(?:\.\d+)?)", re.IGNORECASE)

# Matches vendor daemon version: "vendordaemon: UP v11.18.1"
VENDOR_VERSION_PATTERN = re.compile(r"^\s*(\w+):\s*UP\s+(v\d+\.\d+(?:\.\d+)?)", re.IGNORECASE | re.MULTILINE)

# =============================================================================
# ansysli_util checkout error patterns
# =============================================================================

# Matches: "ANSYS LICENSE MANAGER ERROR : Cannot connect to license server system."
CHECKOUT_CONNECTION_ERROR_PATTERN = re.compile(
    r"ANSYS LICENSE MANAGER ERROR\s*:\s*Cannot connect to license server", re.IGNORECASE
)

# Matches: "ANSYS LICENSE MANAGER ERROR : The desired vendor daemon is down."
CHECKOUT_VENDOR_DOWN_PATTERN = re.compile(
    r"ANSYS LICENSE MANAGER ERROR\s*:\s*The desired vendor daemon is down", re.IGNORECASE
)

# Matches: "User/host not on INCLUDE list for feature" or "User/host on EXCLUDE list for feature"
# Also matches general access control patterns like "User/host *** list for this feature"
CHECKOUT_ACCESS_DENIED_PATTERN = re.compile(
    r"ANSYS LICENSE MANAGER ERROR\s*:\s*User/host\s+.*\s+list\s+for\s+(feature|this feature)", re.IGNORECASE
)

# Matches specific include list error
CHECKOUT_NOT_ON_INCLUDE_PATTERN = re.compile(r"User/host not on INCLUDE list", re.IGNORECASE)

# Matches specific exclude list error
CHECKOUT_ON_EXCLUDE_PATTERN = re.compile(r"User/host on EXCLUDE list", re.IGNORECASE)

# Matches: "FlexNet Licensing error:-15,10032" - extracts the error code
FLEXNET_ERROR_CODE_PATTERN = re.compile(r"FlexNet Licensing error:\s*(-?\d+)", re.IGNORECASE)

# Matches: "License path: 1055@abc.com;1055@localhost;"
LICENSE_PATH_PATTERN = re.compile(r"License path:\s*(.+?)(?:\n|$)", re.IGNORECASE)

# Matches: "Server name: 65.8.70.45" or "Vendor:Host: 10.45.16.188"
SERVER_NAME_PATTERN = re.compile(r"(?:Server name|Vendor:Host):\s*(\S+)", re.IGNORECASE)

# Matches: "CHECKOUT FAILED" at end of output
CHECKOUT_FAILED_PATTERN = re.compile(r"CHECKOUT FAILED", re.IGNORECASE)


def get_license_server(vendor: str = "ansyslmd") -> str | None:
    """Get the effective license server for a vendor.

    Determines the license server using the following priority:
    1. Environment variables (ANSYSLMD_LICENSE_FILE, then ANSYSLI_SERVERS for ansyslmd)
    2. SERVER value from user-scope ansyslmd.ini (~/.ansys_licensing/ansyslmd.ini)
    3. SERVER value from installation-scope ansyslmd.ini ($ANSYSLIC_DIR/ansyslmd.ini)

    Note: If the SERVER= line in ansyslmd.ini is commented out (starts with # or ;),
    that file is treated as if it has no server configured.

    Parameters
    ----------
    vendor : str, optional
        The vendor daemon name. Currently supported: "ansyslmd", "snpslmd".
        Default is "ansyslmd".

    Returns
    -------
    str | None
        The license server string (e.g., "1055@host") from the highest
        priority source, or None if no server is configured.

    Examples
    --------
    >>> # With ANSYSLMD_LICENSE_FILE set
    >>> import os
    >>> os.environ["ANSYSLMD_LICENSE_FILE"] = "1055@server1"
    >>> get_license_server()
    '1055@server1'

    >>> # Without env var, falls back to ansyslmd.ini
    >>> del os.environ["ANSYSLMD_LICENSE_FILE"]
    >>> get_license_server()  # Returns server from ansyslmd.ini if available
    '1055@config-server'
    """
    server, _ = get_license_server_with_source(vendor=vendor)
    return server


def get_license_server_with_source(vendor: str = "ansyslmd") -> tuple[str | None, str | None]:
    """Get the effective license server and its source.

    Similar to get_license_server(), but also returns information about
    where the server was found (environment variable or config file path).

    Parameters
    ----------
    vendor : str, optional
        The vendor daemon name. Currently supported: "ansyslmd", "snpslmd".
        Default is "ansyslmd".

    Returns
    -------
    tuple[str | None, str | None]
        A tuple of ``(server, source)``, where ``server`` is the license
        server string (or ``None`` if not found) and ``source`` is ``None``
        when the server came from an environment variable, or the
        ``ansyslmd.ini`` config file path when it came from a config file.

    Examples
    --------
    >>> server, source = get_license_server_with_source()
    >>> if source is None:
    ...     print(f"Server from environment: {server}")
    ... else:
    ...     print(f"Server from config file: {source}")
    """
    # Capture the original env / user-ini / installation-ini values (write-once)
    # the first time the license server is detected, before any later mutation.
    _capture_license_originals()

    # Priority 1: Check environment variables
    server = get_license_server_from_env(vendor=vendor)
    if server:
        logger.debug("License server resolved from environment variable: %s", server)
        return server, None  # None source indicates env var

    # Priority 2: Check user-scope ansyslmd.ini
    user_ini_path = find_ansyslmd_ini(scope="user")
    if user_ini_path:
        try:
            config = parse_ansyslmd_ini(user_ini_path)
            if config.server:
                logger.debug("License server resolved from user config %s: %s", user_ini_path, config.server)
                return config.server, user_ini_path
        except LicenseFileParseError:
            logger.debug("Failed to parse user config %s, skipping", user_ini_path)

    # Priority 3: Check installation-scope ansyslmd.ini
    install_ini_path = find_ansyslmd_ini(scope="installation")
    if install_ini_path:
        try:
            config = parse_ansyslmd_ini(install_ini_path)
            if config.server:
                logger.debug(
                    "License server resolved from installation config %s: %s",
                    install_ini_path,
                    config.server,
                )
                return config.server, install_ini_path
        except LicenseFileParseError:
            logger.debug("Failed to parse installation config %s, skipping", install_ini_path)

    logger.debug("No license server found from any source for vendor '%s'", vendor)
    return None, None


def _capture_license_originals() -> None:
    """Capture original env / user-ini / installation-ini values (write-once).

    Records the ``ANSYSLMD_LICENSE_FILE`` environment variable and the user- and
    installation-scope ``ansyslmd.ini`` ``SERVER`` values as they are first
    detected, so they can later be restored. Each item is captured only once and
    any capture failure is swallowed so it never breaks server resolution.

    The import is lazy to avoid an import cycle (``config`` imports from the
    diagnosis-related helpers indirectly), keeping module import order simple.
    """
    try:
        from ansys.tools.common.licensing.config import (
            capture_env_original,
            capture_ini_original,
        )

        capture_env_original()
        capture_ini_original("user")
        capture_ini_original("installation")
    except Exception as exc:  # noqa: BLE001 - capture must never break resolution
        logger.debug("Could not capture original license values: %s", exc)


def get_license_environment(vendor: str = "ansyslmd") -> LicenseEnvironment:
    """Get comprehensive license environment information.

    Retrieves all license-related information including:
    - Environment variables (from vars module)
    - Config file paths (ansyslmd.ini for user and installation scopes)
    - The effective license server and its source

    This is the recommended function for getting a complete picture of the
    license environment on a machine.

    Parameters
    ----------
    vendor : str, optional
        The vendor daemon name. Currently supported: "ansyslmd", "snpslmd".
        Default is "ansyslmd".

    Returns
    -------
    LicenseEnvironment
        A dataclass with the complete license environment. It holds the
        ``vendor`` daemon name, an ``env_vars`` dictionary (variable names to
        values, ``None`` if unset), the ``effective_server`` resolved by
        priority, and the ``config_file`` path when the server came from a
        config file (otherwise ``None``). See
        :class:`~ansys.tools.common.licensing.models.LicenseEnvironment` for
        details.

    Examples
    --------
    >>> env_info = get_license_environment()
    >>> print(f"Effective server: {env_info.effective_server}")
    >>> if env_info.config_file:
    ...     print(f"Server from config: {env_info.config_file}")
    >>> for var, value in env_info.env_vars.items():
    ...     print(f"{var}: {value}")
    """
    # Get license-related environment variables
    env_vars: dict[str, str | None] = get_license_vars(vendor)

    # Add AWP_ROOTxxx variables for installed Ansys versions
    awp_versions = get_awp_root_versions()
    for ver, path in awp_versions.items():
        # Handle negative version numbers (student editions)
        if ver < 0:
            env_vars[f"AWP_ROOT{abs(ver)}"] = path
        else:
            env_vars[f"AWP_ROOT{ver}"] = path

    # Determine effective server and its source using full resolution logic
    effective_server, config_file = get_license_server_with_source(vendor)

    return LicenseEnvironment(
        vendor=vendor,
        env_vars=env_vars,
        effective_server=effective_server,
        config_file=config_file,
    )


def check_license_server_status_all(
    server: str | None = None,
    vendor: str = "ansyslmd",
    timeout: int = DEFAULT_TIMEOUT,
    version: int | float | None = None,
) -> LicenseServerStatus:
    """Query license server status using lmstat.

    Parameters
    ----------
    server : str | None
        License server in "port@host" format. If None, attempts to determine
        from environment variables.
    vendor : str
        Vendor daemon name. Default is "ansyslmd".
    timeout : int
        Timeout in seconds for the lmstat command. Default is 30.
    version : int | float | None
        Ansys version for finding lmutil. If None, uses the latest available.

    Returns
    -------
    LicenseServerStatus
        Status information including server state, vendor daemon state, and features.

    Raises
    ------
    LicenseServerError
        If no server is specified and none can be determined from environment,
        or if there's an error executing lmstat.
    LicenseToolNotFoundError
        If lmutil cannot be found.

    Examples
    --------
    >>> status = check_license_server_status_all("1055@license-server")
    >>> print(f"Server up: {status.is_up}")
    >>> print(f"Vendor daemon up: {status.vendor_daemon_up}")
    >>> for name, feature in status.features.items():
    ...     print(f"  {name}: {feature.in_use}/{feature.total}")
    """
    # Determine server
    effective_server = server
    if effective_server is None:
        effective_server = get_license_server(vendor=vendor)
        if effective_server is None:
            raise LicenseServerError(
                "No license server specified and none found in environment. "
                "Set ANSYSLMD_LICENSE_FILE or ANSYSLI_SERVERS."
            )

    logger.debug("Querying full server status for %s (vendor=%s)", effective_server, vendor)

    # Find lmutil
    lmutil_path, _ = find_lmutil(version=version)
    if not lmutil_path:
        raise LicenseToolNotFoundError("lmutil not found. Ensure Ansys is installed.")

    # Build command: lmstat -a -c server
    cmd = [lmutil_path, "lmstat", "-a", "-c", effective_server]

    # Execute lmstat
    raw_output = _run_license_tool(cmd, timeout, "lmstat")

    # Check for specific connection errors and get helpful message
    error_message = _get_connection_error_message(raw_output, effective_server)

    # Parse output
    is_up = _check_server_up(raw_output)
    vendor_daemon_up = _check_vendor_up(raw_output, vendor)
    features = _parse_features(raw_output, vendor)
    lmgrd_version = _parse_lmgrd_version(raw_output)
    vendor_daemon_version = _parse_vendor_version(raw_output, vendor)

    logger.info(
        "Server %s: lmgrd=%s, %s=%s, features=%d",
        effective_server,
        "UP" if is_up else "DOWN",
        vendor,
        "UP" if vendor_daemon_up else "DOWN",
        len(features),
    )

    return LicenseServerStatus(
        server=effective_server,
        vendor=vendor,
        is_up=is_up,
        vendor_daemon_up=vendor_daemon_up,
        features=features,
        raw_output=raw_output,
        lmgrd_version=lmgrd_version,
        vendor_daemon_version=vendor_daemon_version,
        error_message=error_message,
    )


def check_feature(
    feature: str,
    server: str | None = None,
    vendor: str = "ansyslmd",
    timeout: int = DEFAULT_TIMEOUT,
    version: int | float | None = None,
) -> FeatureInfo | None:
    """Check availability of a specific license feature.

    Parameters
    ----------
    feature : str
        The feature name to check (e.g., "mechanical_enterprise").
    server : str | None
        License server in "port@host" format. If None, attempts to determine
        from environment variables.
    vendor : str
        Vendor daemon name. Default is "ansyslmd".
    timeout : int
        Timeout in seconds for the lmstat command. Default is 30.
    version : int | float | None
        Ansys version for finding lmutil. If None, uses the latest available.

    Returns
    -------
    FeatureInfo | None
        Feature information if found, None if the feature doesn't exist on the server.

    Raises
    ------
    LicenseServerError
        If no server is specified and none can be determined from environment,
        or if there's an error executing lmstat.
    LicenseToolNotFoundError
        If lmutil cannot be found.

    Examples
    --------
    >>> info = check_feature("mechanical_enterprise", "1055@license-server")
    >>> if info:
    ...     print(f"Available: {info.total - info.in_use} of {info.total}")
    """
    # Determine server
    effective_server = server
    if effective_server is None:
        effective_server = get_license_server(vendor=vendor)
        if effective_server is None:
            raise LicenseServerError("No license server specified and none found in environment.")

    # Find lmutil
    lmutil_path, _ = find_lmutil(version=version)
    if not lmutil_path:
        raise LicenseToolNotFoundError("lmutil not found. Ensure Ansys is installed.")

    # Build command: lmstat -f feature -c server
    cmd = [lmutil_path, "lmstat", "-f", feature, "-c", effective_server]

    # Execute lmstat
    raw_output = _run_license_tool(cmd, timeout, "lmstat")

    # Parse feature info from output
    features = _parse_features(raw_output, vendor)

    # Find the requested feature (case-insensitive lookup)
    # First try exact match, then case-insensitive
    if feature in features:
        return features[feature]

    # Case-insensitive fallback
    feature_lower = feature.lower()
    for name, info in features.items():
        if name.lower() == feature_lower:
            return info

    return None


def check_license_server_status(
    server: str,
    vendor: str = "ansyslmd",
    timeout: int = 10,
    version: int | float | None = None,
) -> ServerTestResult:
    """Test license server connectivity and status.

    Performs a connectivity test to check if the license server (lmgrd)
    and vendor daemon are responding. Returns detailed status information
    including error messages for troubleshooting.

    Parameters
    ----------
    server : str
        License server in "port@host" format.
    vendor : str
        Vendor daemon name. Default is "ansyslmd".
    timeout : int
        Timeout in seconds for the test. Default is 10.
    version : int | float | None
        Ansys version for finding lmutil. If None, uses the latest available.

    Returns
    -------
    ServerTestResult
        A detailed test result. It reports whether the license server manager
        (``lmgrd_up``) and the vendor daemon (``vendor_daemon_up``) are
        responding, their versions (``lmgrd_version``,
        ``vendor_daemon_version``), a user-friendly ``error_message`` and
        categorized ``error_type`` when applicable, and the ``raw_output``
        from lmstat for debugging. See
        :class:`~ansys.tools.common.licensing.models.ServerTestResult` for
        details.

    Examples
    --------
    >>> result = check_license_server_status("1055@license-server")
    >>> if result.lmgrd_up:
    ...     print("License server is up!")
    ...     if result.vendor_daemon_up:
    ...         print("Vendor daemon is also up!")
    ... else:
    ...     print(f"Server is down: {result.error_message}")
    """
    logger.debug("Checking server connectivity: %s (vendor=%s, timeout=%ds)", server, vendor, timeout)

    # Find lmutil
    lmutil_path, _ = find_lmutil(version=version)
    if not lmutil_path:
        return ServerTestResult(
            server=server,
            vendor=vendor,
            lmgrd_up=False,
            vendor_daemon_up=False,
            error_message="lmutil not found. Ensure Ansys is installed.",
            error_type=LicenseErrorType.LMUTIL_NOT_FOUND,
            raw_output="",
        )

    # Build command: lmstat -c server (quick status check)
    cmd = [lmutil_path, "lmstat", "-c", server]

    # Execute lmstat
    raw_output, exec_error = _run_license_tool_safe(cmd, timeout, "lmstat")
    if exec_error is not None:
        # Determine error type from the message
        if "timed out" in exec_error:
            error_type = LicenseErrorType.TIMEOUT
            error_message = (
                f"Connection timed out after {timeout} seconds. The server may be unreachable or heavily loaded."
            )
        else:
            error_type = LicenseErrorType.EXECUTION_ERROR
            error_message = exec_error
        return ServerTestResult(
            server=server,
            vendor=vendor,
            lmgrd_up=False,
            vendor_daemon_up=False,
            error_message=error_message,
            error_type=error_type,
            raw_output=raw_output,
        )

    # Parse the output
    lmgrd_up = _check_server_up(raw_output)
    vendor_daemon_up = _check_vendor_up(raw_output, vendor) if lmgrd_up else False
    lmgrd_version = _parse_lmgrd_version(raw_output) if lmgrd_up else None
    vendor_daemon_version = _parse_vendor_version(raw_output, vendor) if vendor_daemon_up else None

    # Determine error type and message
    error_type, error_message = _classify_server_error(raw_output, server, vendor, lmgrd_up, vendor_daemon_up)

    logger.info(
        "Server %s connectivity: lmgrd=%s, %s=%s%s",
        server,
        "UP" if lmgrd_up else "DOWN",
        vendor,
        "UP" if vendor_daemon_up else "DOWN",
        f" ({error_type.value})" if error_type else "",
    )

    return ServerTestResult(
        server=server,
        vendor=vendor,
        lmgrd_up=lmgrd_up,
        vendor_daemon_up=vendor_daemon_up,
        lmgrd_version=lmgrd_version,
        vendor_daemon_version=vendor_daemon_version,
        error_message=error_message,
        error_type=error_type,
        raw_output=raw_output,
    )


def get_license_features(
    server: str | None = None,
    vendor: str = "ansyslmd",
    timeout: int = DEFAULT_TIMEOUT,
    version: int | float | None = None,
) -> dict[str, FeatureInfo]:
    """Get license features from a server.

    This is a convenience wrapper around check_license_server_status_all() that
    returns only the features dictionary, making it easier to query available
    licenses without needing the full server status.

    Parameters
    ----------
    server : str | None
        License server in "port@host" format. If None, attempts to determine
        from environment variables.
    vendor : str
        Vendor daemon name. Default is "ansyslmd".
    timeout : int
        Timeout in seconds for the lmstat command. Default is 30.
    version : int | float | None
        Ansys version for finding lmutil. If None, uses the latest available.

    Returns
    -------
    dict[str, FeatureInfo]
        Dictionary mapping feature names to their FeatureInfo for O(1) lookup.
        Returns an empty dictionary if the server is down or unreachable.

    Raises
    ------
    LicenseServerError
        If no server is specified and none can be determined from environment,
        or if there's an error executing lmstat.
    LicenseToolNotFoundError
        If lmutil cannot be found.

    Examples
    --------
    >>> features = get_license_features("1055@license-server")
    >>> for name, info in features.items():
    ...     print(f"{name}: {info.in_use}/{info.total}")

    >>> # Check a specific feature
    >>> features = get_license_features()
    >>> if "mechanical_enterprise" in features:
    ...     info = features["mechanical_enterprise"]
    ...     print(f"Available: {info.total - info.in_use}")
    """
    status = check_license_server_status_all(server, vendor, timeout, version)
    return status.features


def _check_server_up(output: str) -> bool:
    """Check if the license server is up based on lmstat output.

    Parameters
    ----------
    output : str
        The raw lmstat output.

    Returns
    -------
    bool
        ``True`` if a positive "license server UP" indicator is found,
        ``False`` if a down indicator is found or no status is detected.
    """
    # Check for positive UP indicator
    if SERVER_UP_PATTERN.search(output):
        return True

    # Check for negative DOWN indicators
    for pattern in SERVER_DOWN_PATTERNS:
        if pattern.search(output):
            return False

    # Default to False if unclear
    return False


def _get_connection_error_message(output: str, server: str) -> str | None:
    """Check for specific connection errors and return a helpful error message.

    Parameters
    ----------
    output : str
        The raw lmstat output.
    server : str
        The license server address for error messages.

    Returns
    -------
    str | None
        A user-friendly error message if a connection error is detected,
        or None if no known error pattern is found.
    """
    # Extract server hostname from "port@host" format
    if "@" in server:
        server_name = server.split("@", 1)[1]
    else:
        server_name = server

    # Check for connection refused error
    if CONNECTION_REFUSED_PATTERN.search(output):
        return (
            f"License server {server_name} cannot be connected. "
            "Check the network connection between the local machine and the license server."
        )

    # Check for host not found / DNS error
    if HOST_NOT_FOUND_PATTERN.search(output):
        return (
            f"License server {server_name} cannot be resolved into a valid IP address. "
            "Contact IT to check for DNS issues."
        )

    return None


def _check_vendor_up(output: str, vendor: str) -> bool:
    """Check if the vendor daemon is up based on lmstat output.

    Parameters
    ----------
    output : str
        The raw lmstat output.
    vendor : str
        The vendor daemon name (e.g., ``"ansyslmd"``).

    Returns
    -------
    bool
        ``True`` if the vendor daemon is confirmed UP, ``False`` if it
        is DOWN, has no socket connection, or the server itself is down.
    """
    # Look for vendor: UP pattern
    for match in VENDOR_UP_PATTERN.finditer(output):
        if match.group(1).lower() == vendor.lower():
            return True

    # Look for vendor: DOWN pattern (explicit DOWN status)
    for pattern in VENDOR_DOWN_PATTERNS:
        if pattern.pattern.startswith(r"^\s*"):
            # Pattern captures vendor name - check if it matches our vendor
            matches = pattern.findall(output)
            if any(vendor.lower() in str(m).lower() for m in matches):
                return False
        else:
            # Pattern doesn't capture vendor name - check if error appears on vendor's line
            # Look for "vendor: <error pattern>" format
            vendor_line_pattern = re.compile(
                rf"^\s*{re.escape(vendor)}:\s*.*{pattern.pattern}",
                re.IGNORECASE | re.MULTILINE,
            )
            if vendor_line_pattern.search(output):
                return False

    # If server is down, vendor is also down
    if not _check_server_up(output):
        return False

    # Default: if no explicit status found but server is up, assume vendor is up
    # (some lmstat outputs don't explicitly list vendor status)
    return _check_server_up(output)


def _classify_server_error(
    output: str, server: str, vendor: str, lmgrd_up: bool, vendor_daemon_up: bool
) -> tuple[LicenseErrorType | None, str | None]:
    """Classify the server connection error and generate a user-friendly message.

    Parameters
    ----------
    output : str
        The raw lmstat output.
    server : str
        The license server address.
    vendor : str
        The vendor daemon name.
    lmgrd_up : bool
        Whether lmgrd is up.
    vendor_daemon_up : bool
        Whether the vendor daemon is up.

    Returns
    -------
    tuple[LicenseErrorType | None, str | None]
        A tuple of (error_type, error_message). Both are None if no error.
    """
    # If everything is up, no error
    if lmgrd_up and vendor_daemon_up:
        return None, None

    # Extract server hostname from "port@host" format
    if "@" in server:
        server_name = server.split("@", 1)[1]
    else:
        server_name = server

    # Check for connection refused error
    if CONNECTION_REFUSED_PATTERN.search(output):
        return (
            LicenseErrorType.CONNECTION_REFUSED,
            f"Cannot connect to license server {server_name}. "
            "The license server manager (lmgrd) may not be running, "
            "the port may be blocked by a firewall, or the wrong port is specified. "
            "Check network connectivity and verify the server is running.",
        )

    # Check for host not found / DNS error
    if HOST_NOT_FOUND_PATTERN.search(output):
        return (
            LicenseErrorType.HOST_NOT_FOUND,
            f"Cannot resolve hostname '{server_name}' to an IP address. "
            "Check DNS configuration or use an IP address directly. "
            "Contact IT if the hostname should be resolvable.",
        )

    # Check for generic "Cannot connect to license server" without specific reason
    for pattern in SERVER_DOWN_PATTERNS:
        if pattern.search(output):
            if "Cannot connect" in pattern.pattern:
                return (
                    LicenseErrorType.CONNECTION_REFUSED,
                    f"Cannot connect to license server {server_name}. "
                    "The server may be down, unreachable, or the port may be incorrect.",
                )

    # Server is up but vendor daemon is down
    if lmgrd_up and not vendor_daemon_up:
        # Check for "No socket connection" error
        if re.search(r"No socket connection to license server manager", output, re.IGNORECASE):
            return (
                LicenseErrorType.VENDOR_DAEMON_DOWN,
                f"License server {server_name} is up, but vendor daemon '{vendor}' has no socket "
                "connection to the license server manager (-7,10015). "
                "This may indicate the vendor daemon crashed or failed to start. "
                "Check the lmgrd log file on the license server and restart the license service.",
            )
        # Check for explicit DOWN status
        vendor_down_match = re.search(rf"^\s*{vendor}:\s*DOWN", output, re.IGNORECASE | re.MULTILINE)
        if vendor_down_match:
            return (
                LicenseErrorType.VENDOR_DAEMON_DOWN,
                f"License server {server_name} is up, but vendor daemon '{vendor}' is DOWN. "
                "Check the lmgrd log file on the license server for errors. "
                "The vendor daemon may need to be restarted.",
            )
        else:
            return (
                LicenseErrorType.VENDOR_DAEMON_DOWN,
                f"License server {server_name} is up, but vendor daemon '{vendor}' is not responding. "
                "The vendor daemon may not be configured or may have crashed.",
            )

    # Generic server down message
    if not lmgrd_up:
        return (
            LicenseErrorType.SERVER_DOWN,
            f"License server {server_name} is not responding. "
            "Verify the server address is correct and the license server is running.",
        )

    return None, None


def _parse_features(output: str, vendor: str) -> dict[str, FeatureInfo]:
    """Parse feature usage information from lmstat output.

    Parameters
    ----------
    output : str
        The raw lmstat output.
    vendor : str
        The vendor daemon name.

    Returns
    -------
    dict[str, FeatureInfo]
        Dictionary mapping feature names to their FeatureInfo for O(1) lookup.
    """
    features: dict[str, FeatureInfo] = {}

    # Parse counted features
    for match in FEATURE_USAGE_PATTERN.finditer(output):
        feature_name = match.group(1)
        total = int(match.group(2))
        in_use = int(match.group(3))
        features[feature_name] = FeatureInfo(
            name=feature_name,
            vendor=vendor,
            total=total,
            in_use=in_use,
        )

    # Parse uncounted features
    for match in FEATURE_UNCOUNTED_PATTERN.finditer(output):
        feature_name = match.group(1)
        # Skip if already parsed as counted
        if feature_name in features:
            continue
        features[feature_name] = FeatureInfo(
            name=feature_name,
            vendor=vendor,
            total=-1,  # -1 indicates uncounted
            in_use=0,  # Uncounted features don't track usage
        )

    return features


def _parse_lmgrd_version(output: str) -> str | None:
    """Parse the FlexLM license manager (lmgrd) version from lmstat output.

    Parameters
    ----------
    output : str
        The raw lmstat output.

    Returns
    -------
    str | None
        The lmgrd version string (e.g., "v11.18.1"), or None if not found.

    Examples
    --------
    >>> output = "hostname: license server UP (MASTER) v11.18.1"
    >>> _parse_lmgrd_version(output)
    'v11.18.1'
    """
    match = LMGRD_VERSION_PATTERN.search(output)
    if match:
        return match.group(1)
    return None


def _parse_vendor_version(output: str, vendor: str) -> str | None:
    """Parse the vendor daemon version from lmstat output.

    Parameters
    ----------
    output : str
        The raw lmstat output.
    vendor : str
        The vendor daemon name (e.g., "ansyslmd").

    Returns
    -------
    str | None
        The vendor daemon version string (e.g., "v11.18.1"), or None if not found.

    Examples
    --------
    >>> output = "ansyslmd: UP v11.18.1"
    >>> _parse_vendor_version(output, "ansyslmd")
    'v11.18.1'
    """
    for match in VENDOR_VERSION_PATTERN.finditer(output):
        if match.group(1).lower() == vendor.lower():
            return match.group(2)
    return None


def test_license_checkout(
    feature: str,
    timeout: int = DEFAULT_TIMEOUT,
    version: int | float | None = None,
) -> LicenseCheckoutResult:
    """Test checkout of a specific license feature using ansysli_util.

    Performs a test license checkout to verify that the current user/host
    can successfully checkout the specified license feature. This is useful
    for diagnosing licensing issues before running an Ansys application.

    Parameters
    ----------
    feature : str
        The license feature name to test (e.g., "mechanical_enterprise", "ansys").
    timeout : int
        Timeout in seconds for the checkout test. Default is 30.
    version : int | float | None
        Ansys version for finding ansysli_util. If None, uses the latest available.

    Returns
    -------
    LicenseCheckoutResult
        Result containing success status, error details, and diagnostic information.
        The ``error_type`` field is a :class:`LicenseErrorType` enum member
        categorizing the failure for programmatic handling:

        - ``LicenseErrorType.CONNECTION_FAILED``: Cannot connect to license server (error -15)
        - ``LicenseErrorType.VENDOR_DAEMON_DOWN``: Vendor daemon is not running (error -97)
        - ``LicenseErrorType.ACCESS_DENIED``: User/host on EXCLUDE list or not on INCLUDE list
          (errors -38, -39). Contact the license server administrator.
        - ``LicenseErrorType.CHECKOUT_FAILED``: Other checkout failure
        - ``None``: Checkout successful

    Raises
    ------
    LicenseToolNotFoundError
        If ansysli_util cannot be found.

    Examples
    --------
    >>> result = test_license_checkout("mechanical_enterprise")
    >>> if result.success:
    ...     print("License checkout successful!")
    ... else:
    ...     print(f"Checkout failed: {result.error_message}")
    ...     if result.error_type == LicenseErrorType.ACCESS_DENIED:
    ...         print("Contact the license server administrator.")

    >>> # Check specific error codes
    >>> result = test_license_checkout("ansys")
    >>> if result.error_code == -15:
    ...     print("Cannot connect to license server")
    >>> elif result.error_code == -97:
    ...     print("Vendor daemon is down")
    """
    logger.debug("Testing license checkout for feature '%s' (timeout=%ds)", feature, timeout)

    # Find ansysli_util
    ansysli_util_path, _ = find_ansysli_util(version=version)
    if not ansysli_util_path:
        raise LicenseToolNotFoundError("ansysli_util not found. Ensure Ansys is installed.")

    # Build command: ansysli_util -checkout feature
    cmd = [ansysli_util_path, "-checkout", feature]

    # Execute ansysli_util
    raw_output, exec_error = _run_license_tool_safe(cmd, timeout, "ansysli_util")
    if exec_error is not None:
        logger.warning("License checkout for '%s' failed: %s", feature, exec_error)
        return LicenseCheckoutResult(
            feature=feature,
            success=False,
            error_code=None,
            error_type=LicenseErrorType.CHECKOUT_FAILED,
            error_message=exec_error,
            license_path=None,
            server=None,
            raw_output=raw_output,
        )

    # Parse the output
    result = _parse_checkout_result(feature, raw_output)
    if result.success:
        logger.info("License checkout for '%s' succeeded", feature)
    else:
        logger.info(
            "License checkout for '%s' failed: %s (error_code=%s)",
            feature,
            result.error_type,
            result.error_code,
        )
    return result


def _parse_checkout_result(feature: str, raw_output: str) -> LicenseCheckoutResult:
    """Parse the output from ansysli_util -checkout command.

    Parameters
    ----------
    feature : str
        The feature name that was tested.
    raw_output : str
        The raw output from ansysli_util.

    Returns
    -------
    LicenseCheckoutResult
        Parsed result with error details.
    """
    # Extract common fields
    error_code = _extract_flexnet_error_code(raw_output)
    license_path = _extract_license_path(raw_output)
    server = _extract_server_name(raw_output)

    # Check for checkout failure
    checkout_failed = CHECKOUT_FAILED_PATTERN.search(raw_output) is not None
    has_error = "ANSYS LICENSE MANAGER ERROR" in raw_output.upper()

    # Determine success
    success = not checkout_failed and not has_error and error_code is None

    if success:
        return LicenseCheckoutResult(
            feature=feature,
            success=True,
            error_code=None,
            error_type=None,
            error_message=None,
            license_path=license_path,
            server=server,
            raw_output=raw_output,
        )

    # Determine error type and message
    error_type, error_message = _classify_checkout_error(raw_output, server, error_code)

    return LicenseCheckoutResult(
        feature=feature,
        success=False,
        error_code=error_code,
        error_type=error_type,
        error_message=error_message,
        license_path=license_path,
        server=server,
        raw_output=raw_output,
    )


def _extract_flexnet_error_code(output: str) -> int | None:
    """Extract FlexNet error code from output.

    Parameters
    ----------
    output : str
        The raw ansysli_util output.

    Returns
    -------
    int | None
        The error code (e.g., -15, -97, -38, -39) or None if not found.
    """
    match = FLEXNET_ERROR_CODE_PATTERN.search(output)
    if match:
        return int(match.group(1))
    return None


def _extract_license_path(output: str) -> str | None:
    """Extract license path from output.

    Parameters
    ----------
    output : str
        The raw ansysli_util output.

    Returns
    -------
    str | None
        The license path or None if not found.
    """
    match = LICENSE_PATH_PATTERN.search(output)
    if match:
        return match.group(1).strip()
    return None


def _extract_server_name(output: str) -> str | None:
    """Extract server name from output.

    Parameters
    ----------
    output : str
        The raw ansysli_util output.

    Returns
    -------
    str | None
        The server name or None if not found.
    """
    match = SERVER_NAME_PATTERN.search(output)
    if match:
        return match.group(1).strip()
    return None


def _classify_checkout_error(output: str, server: str | None, error_code: int | None) -> tuple[LicenseErrorType, str]:
    """Classify the checkout error and generate a user-friendly message.

    Parameters
    ----------
    output : str
        The raw ansysli_util output.
    server : str | None
        The extracted server name.
    error_code : int | None
        The extracted FlexNet error code.

    Returns
    -------
    tuple[LicenseErrorType, str]
        A tuple of (error_type, error_message).
    """
    server_str = server or "the license server"

    # Check for connection error (error -15)
    if CHECKOUT_CONNECTION_ERROR_PATTERN.search(output) or error_code == -15:
        return (
            LicenseErrorType.CONNECTION_FAILED,
            f"Cannot connect to license server {server_str}. "
            "The license server manager (lmgrd) may not be started, "
            "the wrong port@host or license file is being used, or "
            "the port or hostname in the license file has been changed. "
            "Check the network connection and license server configuration.",
        )

    # Check for vendor daemon down (error -97)
    if CHECKOUT_VENDOR_DOWN_PATTERN.search(output) or error_code == -97:
        return (
            LicenseErrorType.VENDOR_DAEMON_DOWN,
            f"The vendor daemon on {server_str} is down. "
            "Check the lmgrd log file on the license server, or contact "
            "the license server administrator to restart the vendor daemon.",
        )

    # Check for access control errors (errors -38, -39)
    if CHECKOUT_ACCESS_DENIED_PATTERN.search(output) or error_code in (-38, -39):
        if CHECKOUT_NOT_ON_INCLUDE_PATTERN.search(output) or error_code == -39:
            return (
                LicenseErrorType.ACCESS_DENIED,
                "User/host is not on the INCLUDE list for this feature. "
                "The license server has access control configured via an options file. "
                "Contact the license server administrator to add your user/host to the allowed list.",
            )
        elif CHECKOUT_ON_EXCLUDE_PATTERN.search(output) or error_code == -38:
            return (
                LicenseErrorType.ACCESS_DENIED,
                "User/host is on the EXCLUDE list for this feature. "
                "The license server has access control configured via an options file. "
                "Contact the license server administrator to remove your user/host from the exclusion list.",
            )
        else:
            # Generic access denied
            return (
                LicenseErrorType.ACCESS_DENIED,
                "User/host access is restricted for this feature. "
                "The license server has access control configured via an options file. "
                "Contact the license server administrator to check the access control settings.",
            )

    # Generic checkout failure
    return (
        LicenseErrorType.CHECKOUT_FAILED,
        f"License checkout failed for feature. "
        f"FlexNet error code: {error_code if error_code else 'unknown'}. "
        "Check the license server status and feature availability.",
    )
