# Copyright (C) 2025 ANSYS, Inc. and/or its affiliates.
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
"""Conftest module."""

from functools import partial
import importlib.metadata
from unittest.mock import Mock

import pytest

from ansys.tools.common.launcher import _plugins, config
from ansys.tools.common.launcher.interface import LAUNCHER_CONFIG_T, LauncherProtocol


@pytest.fixture(autouse=True)
def reset_config():
    """Reset the configuration at the start of each test."""
    config._reset_config()


def get_mock_entrypoints_from_plugins(
    target_plugins: dict[str, dict[str, LauncherProtocol[LAUNCHER_CONFIG_T]]],
):
    """Get mock entrypoints from plugins."""
    res = []
    for product_name, launchers in target_plugins.items():
        for launch_mode, launcher_kls in launchers.items():
            mock_entrypoint = Mock(spec=importlib.metadata.EntryPoint)
            mock_entrypoint.name = f"{product_name}.{launch_mode}"
            mock_entrypoint.load = Mock(return_value=launcher_kls)
            res.append(mock_entrypoint)
    return res


@pytest.fixture
def monkeypatch_entrypoints_from_plugins(monkeypatch):
    """Mock entrypoints."""

    def inner(target_plugins):
        monkeypatch.setattr(
            _plugins,
            "_get_entry_points",
            partial(get_mock_entrypoints_from_plugins, target_plugins=target_plugins),
        )

    return inner
