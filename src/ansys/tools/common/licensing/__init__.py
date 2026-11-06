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

"""Ansys licensing utilities module.

This module provides utilities for working with Ansys licensing (FlexLM):

- Find licensing tools (lmutil, ansysli_util) within Ansys installations
- Query license server status
- Parse licensing logs (debug logs, server logs)
- Inspect license-related environment variables
- Inspect license-related config files (ansyslmd.ini, license.preferences.xml)
"""

from ansys.tools.common.licensing.config import (
    find_ansyslmd_ini,
    find_license_preferences_xml,
    get_ansyslmd_ini_path,
    parse_ansyslmd_ini,
    parse_license_preferences_xml,
    set_ansyslmd_ini,
)
from ansys.tools.common.licensing.data import (
    ANSYS_APPLICATION_SHORT_NAMES,
    ANSYS_LICENSE_FEATURES,
    ApplicationInfo,
    get_all_application_short_names,
    get_all_feature_names,
    get_application_info,
    get_feature_description,
)
from ansys.tools.common.licensing.diagnosis import (
    check_feature,
    check_license_server_status,
    check_license_server_status_all,
    get_license_environment,
    get_license_features,
    get_license_server,
    get_license_server_with_source,
    test_license_checkout,
)
from ansys.tools.common.licensing.logs import (
    find_application_license_log,
    find_general_client_log,
    find_license_log,
    get_recent_license_errors,
    parse_license_log,
)
from ansys.tools.common.licensing.models import (
    AnsyslmdConfig,
    FeatureInfo,
    LicenseCheckoutResult,
    LicenseEnvironment,
    LicenseErrorType,
    LicenseLogInfo,
    LicensePreferences,
    LicenseServer,
    LicenseServerStatus,
    LogEntry,
)
from ansys.tools.common.licensing.tools import find_ansysli_util, find_lmutil
from ansys.tools.common.licensing.vars import (
    get_ansyslic_dir,
    get_awp_root_versions,
    get_license_server_from_env,
    get_license_vars,
)

# Default vendor daemon
DEFAULT_VENDOR = "ansyslmd"

# Vendor registry (extensible for future vendors)
VENDOR_INFO = {
    "ansyslmd": {
        "env_vars": ["ANSYSLMD_LICENSE_FILE", "ANSYSLI_SERVERS"],
        "config_file": "ansyslmd.ini",
        "description": "Ansys License Manager",
    },
    # Future:
    # "snpslmd": {
    #     "env_vars": ["SNPSLMD_LICENSE_FILE"],
    #     "config_file": "snpslmd.ini",
    #     "description": "Synopsys License Manager",
    # },
}

__all__ = [
    # Constants
    "ANSYS_APPLICATION_SHORT_NAMES",
    "ANSYS_LICENSE_FEATURES",
    "DEFAULT_VENDOR",
    "VENDOR_INFO",
    # Data models
    "AnsyslmdConfig",
    "ApplicationInfo",
    "FeatureInfo",
    "LicenseCheckoutResult",
    "LicenseEnvironment",
    "LicenseErrorType",
    "LicenseLogInfo",
    "LicensePreferences",
    "LicenseServer",
    "LicenseServerStatus",
    "LogEntry",
    # Data lookup functions
    "get_all_application_short_names",
    "get_all_feature_names",
    "get_application_info",
    "get_feature_description",
    # Tool discovery
    "find_ansysli_util",
    "find_lmutil",
    # Vars (env var inspection only)
    "get_ansyslic_dir",
    "get_awp_root_versions",
    "get_license_server_from_env",
    "get_license_vars",
    # Config
    "find_ansyslmd_ini",
    "find_license_preferences_xml",
    "get_ansyslmd_ini_path",
    "parse_ansyslmd_ini",
    "parse_license_preferences_xml",
    "set_ansyslmd_ini",
    # Logs
    "find_application_license_log",
    "find_general_client_log",
    "find_license_log",
    "get_recent_license_errors",
    "parse_license_log",
    # Diagnosis (comprehensive environment, server resolution, status & troubleshooting)
    "check_feature",
    "check_license_server_status",
    "check_license_server_status_all",
    "get_license_environment",
    "get_license_features",
    "get_license_server",
    "get_license_server_with_source",
    "test_license_checkout",
]
