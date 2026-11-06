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

"""Data models and types for the licensing module.

This module defines the dataclasses, enums, and facade classes used
throughout the licensing module for structured data representation:

- :class:`LicenseErrorType` — Enum of categorized license error types.
- :class:`FeatureInfo` — License feature usage information.
- :class:`LicenseServerStatus` — Full server status with features.
- :class:`ServerTestResult` — Quick connectivity test result.
- :class:`LicenseCheckoutResult` — Test checkout result.
- :class:`LicenseEnvironment` — Environment variable snapshot.
- :class:`LicenseServer` — High-level facade for server operations.
- :class:`LogEntry`, :class:`LicenseLogInfo` — Log parsing models.
- :class:`AnsyslmdConfig`, :class:`LicensePreferences` — Config file models.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class LicenseErrorType(str, Enum):
    """Categorized license error types for programmatic handling.

    Since this enum extends ``str``, values can be compared directly
    against plain strings for backward compatibility::

        result.error_type == "connection_refused"  # still works
        result.error_type == LicenseErrorType.CONNECTION_REFUSED  # preferred

    Attributes
    ----------
    CONNECTION_REFUSED : str
        Server refused connection (lmgrd not running, wrong port, firewall).
    HOST_NOT_FOUND : str
        DNS resolution failed for the license server hostname.
    TIMEOUT : str
        Connection timed out — server may be unreachable or overloaded.
    SERVER_DOWN : str
        License server is not responding (generic).
    EXECUTION_ERROR : str
        Failed to execute the licensing tool (OS-level error).
    LMUTIL_NOT_FOUND : str
        The lmutil executable was not found on this machine.
    VENDOR_DAEMON_DOWN : str
        lmgrd is up but the vendor daemon (e.g., ansyslmd) is down.
    CONNECTION_FAILED : str
        Cannot connect to license server during checkout (FlexNet error -15).
    ACCESS_DENIED : str
        User/host access is restricted by an options file (errors -38, -39).
    CHECKOUT_FAILED : str
        Generic checkout failure not covered by a more specific type.
    """

    # Server connectivity errors
    CONNECTION_REFUSED = "connection_refused"
    HOST_NOT_FOUND = "host_not_found"
    TIMEOUT = "timeout"
    SERVER_DOWN = "server_down"
    EXECUTION_ERROR = "execution_error"

    # Tool errors
    LMUTIL_NOT_FOUND = "lmutil_not_found"

    # Vendor daemon errors
    VENDOR_DAEMON_DOWN = "vendor_daemon_down"

    # Checkout errors
    CONNECTION_FAILED = "connection_failed"
    ACCESS_DENIED = "access_denied"
    CHECKOUT_FAILED = "checkout_failed"


@dataclass
class FeatureInfo:
    """Information about a license feature from server status.

    Attributes
    ----------
    name : str
        The feature name (e.g., "mechanical_enterprise").
    vendor : str
        The vendor daemon name (e.g., "ansyslmd").
    total : int
        Total number of licenses available for this feature.
    in_use : int
        Number of licenses currently in use.
    """

    name: str
    vendor: str
    total: int
    in_use: int


@dataclass
class LicenseServerStatus:
    """Status information from a license server query.

    Attributes
    ----------
    server : str
        The license server address in "port@host" format.
    vendor : str
        The vendor daemon name (e.g., "ansyslmd").
    is_up : bool
        Whether the license server (lmgrd) is responding.
    vendor_daemon_up : bool
        Whether the vendor daemon is running.
    features : dict[str, FeatureInfo]
        Dictionary mapping feature names to their info for O(1) lookup.
    raw_output : str
        The raw output from lmstat for debugging purposes.
    lmgrd_version : str | None
        The FlexLM license manager (lmgrd) version (e.g., "v11.18.1").
        None if the version could not be parsed.
    vendor_daemon_version : str | None
        The vendor daemon version (e.g., "v11.18.1").
        None if the version could not be parsed.
    error_message : str | None
        A user-friendly error message if a connection error was detected.
        None if no error occurred or the server is up.
    """

    server: str
    vendor: str
    is_up: bool
    vendor_daemon_up: bool
    features: dict[str, FeatureInfo]
    raw_output: str
    lmgrd_version: str | None = None
    vendor_daemon_version: str | None = None
    error_message: str | None = None


@dataclass
class LicenseEnvironment:
    """License-related environment variable information.

    Attributes
    ----------
    vendor : str
        The vendor daemon name (e.g., "ansyslmd").
    env_vars : dict[str, str | None]
        Dictionary of environment variable names to their values.
        Value is None if the variable is not set.
    effective_server : str | None
        The server that will actually be used based on priority rules.
        None if no server is configured.
    config_file : str | None
        Path to the config file if the effective_server came from
        ansyslmd.ini, or None if it came from an environment variable.
    """

    vendor: str
    env_vars: dict[str, str | None]
    effective_server: str | None
    config_file: str | None = None


@dataclass
class LogEntry:
    """A single entry from a license log file.

    Attributes
    ----------
    timestamp : datetime | None
        The timestamp of the log entry, or None if unparsable.
    level : str
        The log level (e.g., "ERROR", "WARNING", "INFO").
    message : str
        The log message content.
    raw_line : str
        The original raw line from the log file.
    """

    timestamp: datetime | None
    level: str
    message: str
    raw_line: str


@dataclass
class LicenseLogInfo:
    """Parsed information from a license log file.

    Attributes
    ----------
    path : str
        Path to the log file.
    entries : list[LogEntry]
        All parsed log entries.
    errors : list[LogEntry]
        Filtered list of error entries only.
    warnings : list[LogEntry]
        Filtered list of warning entries only.
    checkout_events : list[LogEntry]
        License checkout/checkin events.
    """

    path: str
    entries: list[LogEntry]
    errors: list[LogEntry]
    warnings: list[LogEntry]
    checkout_events: list[LogEntry]


@dataclass
class AnsyslmdConfig:
    """Parsed ansyslmd.ini configuration file.

    Attributes
    ----------
    path : str
        Path to the configuration file.
    server : str | None
        The SERVER= value, or None if not defined.
    options : dict[str, str]
        Other key-value pairs from the config file.
    """

    path: str
    server: str | None
    options: dict[str, str]


@dataclass
class LicensePreferences:
    """Parsed license.preferences.xml file.

    Attributes
    ----------
    path : str
        Path to the preferences file.
    preferred_server : str | None
        The preferred license server, or None if not set.
    license_order : list[str]
        Ordered list of preferred license features.
    options : dict[str, Any]
        Other preferences from the XML file.
    """

    path: str
    preferred_server: str | None
    license_order: list[str]
    options: dict[str, Any]


@dataclass
class ServerTestResult:
    """Result of a license server connectivity test.

    Attributes
    ----------
    server : str
        The license server address that was tested in "port@host" format.
    vendor : str
        The vendor daemon name (e.g., "ansyslmd").
    lmgrd_up : bool
        Whether the license server manager (lmgrd) is responding.
    vendor_daemon_up : bool
        Whether the vendor daemon is running.
    lmgrd_version : str | None
        The FlexLM license manager (lmgrd) version (e.g., "v11.18.1").
        None if the version could not be parsed or server is down.
    vendor_daemon_version : str | None
        The vendor daemon version (e.g., "v11.18.1").
        None if the version could not be parsed or daemon is down.
    error_message : str | None
        A user-friendly error message if a connection error was detected.
        None if no error occurred.
    error_type : LicenseErrorType | None
        A categorized error type for programmatic handling.
        See :class:`LicenseErrorType` for possible values.
        None if no error.
    raw_output : str
        The raw output from lmstat for debugging purposes.
    """

    server: str
    vendor: str
    lmgrd_up: bool
    vendor_daemon_up: bool
    lmgrd_version: str | None = None
    vendor_daemon_version: str | None = None
    error_message: str | None = None
    error_type: LicenseErrorType | None = None
    raw_output: str = ""


@dataclass
class LicenseCheckoutResult:
    """Result of a test license checkout attempt.

    Attributes
    ----------
    feature : str
        The feature name that was tested (e.g., "mechanical_enterprise").
    success : bool
        Whether the checkout was successful.
    error_code : int | None
        The FlexNet error code if checkout failed, or None if successful.
        Common error codes:

        - -15: Cannot connect to license server
        - -97: Vendor daemon is down
        - -38: User/host on EXCLUDE list
        - -39: User/host not on INCLUDE list
    error_type : LicenseErrorType | None
        A categorized error type for programmatic handling.
        See :class:`LicenseErrorType` for possible values.
        Common checkout error types: ``CONNECTION_FAILED``,
        ``VENDOR_DAEMON_DOWN``, ``ACCESS_DENIED``, ``CHECKOUT_FAILED``.
        None if successful.
    error_message : str | None
        A user-friendly error message describing the failure,
        or None if the checkout was successful.
    license_path : str | None
        The license path that was used for the checkout attempt.
    server : str | None
        The server name extracted from the error output.
    raw_output : str
        The raw output from ansysli_util for debugging purposes.
    """

    feature: str
    success: bool
    error_code: int | None
    error_type: LicenseErrorType | None
    error_message: str | None
    license_path: str | None
    server: str | None
    raw_output: str


class LicenseServer:
    """High-level facade for license server operations.

    Wraps the procedural functions in :mod:`~ansys.tools.common.licensing.diagnosis`
    behind an object that remembers *server*, *vendor*, and *version* so callers
    don't have to pass them repeatedly.

    This is a **pure facade** — it delegates every call to the existing
    procedural API without adding new logic.

    Parameters
    ----------
    server : str
        License server in ``"port@host"`` format (e.g., ``"1055@license-server"``).
    vendor : str, optional
        Vendor daemon name. Default is ``"ansyslmd"``.
    version : int | float | None, optional
        Ansys version for tool discovery. ``None`` uses the latest installed.

    Examples
    --------
    >>> from ansys.tools.common.licensing import LicenseServer
    >>> ls = LicenseServer("1055@license-server")
    >>> status = ls.check_status()
    >>> print(status.lmgrd_up)
    True

    >>> # Resolve from environment / config automatically
    >>> ls = LicenseServer.from_environment()
    >>> features = ls.get_features()
    """

    def __init__(
        self,
        server: str,
        vendor: str = "ansyslmd",
        version: int | float | None = None,
    ) -> None:
        self.server = server
        self.vendor = vendor
        self.version = version

    @classmethod
    def from_environment(cls, vendor: str = "ansyslmd", **kwargs: Any) -> "LicenseServer":
        """Create a ``LicenseServer`` from the effective environment/config.

        Resolves the license server using the standard priority:
        env vars → user config → installation config.

        Parameters
        ----------
        vendor : str, optional
            Vendor daemon name. Default is ``"ansyslmd"``.
        **kwargs
            Forwarded to the ``LicenseServer`` constructor (e.g., ``version``).

        Returns
        -------
        LicenseServer
            A new instance bound to the resolved server.

        Raises
        ------
        LicenseServerError
            If no license server can be determined.
        """
        from ansys.tools.common.exceptions import LicenseServerError
        from ansys.tools.common.licensing.diagnosis import get_license_server

        server = get_license_server(vendor=vendor)
        if server is None:
            raise LicenseServerError(
                "No license server configured. Set ANSYSLMD_LICENSE_FILE or configure ansyslmd.ini."
            )
        return cls(server=server, vendor=vendor, **kwargs)

    def check_status(self, timeout: int = 10) -> "ServerTestResult":
        """Test connectivity to this license server.

        Parameters
        ----------
        timeout : int, optional
            Timeout in seconds. Default is 10.

        Returns
        -------
        ServerTestResult
            Detailed connectivity test result.
        """
        from ansys.tools.common.licensing.diagnosis import check_license_server_status

        return check_license_server_status(self.server, vendor=self.vendor, timeout=timeout, version=self.version)

    def get_features(self, timeout: int = 30) -> dict[str, "FeatureInfo"]:
        """Get all license features from this server.

        Parameters
        ----------
        timeout : int, optional
            Timeout in seconds. Default is 30.

        Returns
        -------
        dict[str, FeatureInfo]
            Dictionary mapping feature names to their info.
        """
        from ansys.tools.common.licensing.diagnosis import get_license_features

        return get_license_features(server=self.server, vendor=self.vendor, timeout=timeout, version=self.version)

    def check_feature(self, feature: str, timeout: int = 30) -> "FeatureInfo | None":
        """Check availability of a specific license feature.

        Parameters
        ----------
        feature : str
            The feature name to check (e.g., ``"mechanical_enterprise"``).
        timeout : int, optional
            Timeout in seconds. Default is 30.

        Returns
        -------
        FeatureInfo | None
            Feature information if found, ``None`` if not available.
        """
        from ansys.tools.common.licensing.diagnosis import check_feature

        return check_feature(
            feature,
            server=self.server,
            vendor=self.vendor,
            timeout=timeout,
            version=self.version,
        )

    def test_checkout(self, feature: str, timeout: int = 30) -> "LicenseCheckoutResult":
        """Test checkout of a license feature.

        Parameters
        ----------
        feature : str
            The feature name to test (e.g., ``"mechanical_enterprise"``).
        timeout : int, optional
            Timeout in seconds. Default is 30.

        Returns
        -------
        LicenseCheckoutResult
            Result containing success status and error details.
        """
        from ansys.tools.common.licensing.diagnosis import test_license_checkout

        return test_license_checkout(feature, timeout=timeout, version=self.version)

    def __repr__(self) -> str:
        """Return a string representation of this ``LicenseServer``."""
        return f"LicenseServer(server={self.server!r}, vendor={self.vendor!r})"
