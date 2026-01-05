# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
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
"""Module for entry point testing."""

import pkg_with_entrypoint  # type: ignore[import-not-found]

from ansys.tools.common.launcher._plugins import (
    get_all_plugins,
    get_config_model,
    get_launcher,
)
from ansys.tools.common.launcher.config import get_config_for, get_launch_mode_for


def test_plugin_found():
    """Test that the plugin is found in the plugin dictionary."""
    plugin_dict = get_all_plugins()
    assert "pkg_with_entrypoint" in plugin_dict
    assert "test_entry_point" in plugin_dict["pkg_with_entrypoint"]


def test_get_launcher():
    """Test that the launcher can be retrieved for a specific product and launch mode."""
    launcher = get_launcher(product_name="pkg_with_entrypoint", launch_mode="test_entry_point")
    assert launcher.__name__ == "Launcher"


def test_fallback():
    """Test fallback."""
    assert get_launch_mode_for(product_name="pkg_with_entrypoint") == "__fallback__"
    assert (
        get_config_for(product_name="pkg_with_entrypoint", launch_mode="__fallback__")
        == pkg_with_entrypoint.LauncherConfig()
    )
    assert get_launcher(product_name="pkg_with_entrypoint", launch_mode="__fallback__").__name__ == "Launcher"


def test_get_config_model():
    """Test that get_config_model returns the correct configuration model."""
    config_model = get_config_model(product_name="pkg_with_entrypoint", launch_mode="test_entry_point")
    assert config_model.__name__ == "LauncherConfig"


def test_get_config_for_default():
    """Test that get_config_for returns the default configuration when given a launch_mode."""
    get_config_for(product_name="pkg_with_entrypoint", launch_mode="test_entry_point")
