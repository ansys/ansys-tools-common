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

"""Tests for the 'plugins' module."""

from dataclasses import dataclass

import pytest

from ansys.tools.common.launcher import _plugins, interface

TEST_PRODUCT_A = "PRODUCT_A"
TEST_PRODUCT_B = "PRODUCT_B"
TEST_LAUNCH_MODE_A1 = "LAUNCHER_A1"
TEST_LAUNCH_MODE_A2 = "LAUNCHER_A2"
TEST_LAUNCH_MODE_B1 = "LAUNCHER_B1"


@dataclass
class MockConfigA1:
    """Config mock."""

    pass


class MockLauncherA1(interface.LauncherProtocol[MockConfigA1]):
    """Launcher mock."""

    CONFIG_MODEL = MockConfigA1


@dataclass
class MockConfigA2:
    """Config mock."""

    pass


class MockLauncherA2(interface.LauncherProtocol[MockConfigA2]):
    """Launcher mock."""

    CONFIG_MODEL = MockConfigA2


@dataclass
class MockConfigB1:
    """Config mock."""

    pass


class MockLauncherB1(interface.LauncherProtocol[MockConfigB1]):
    """Launcher mock."""

    CONFIG_MODEL = MockConfigB1


PLUGINS = {
    TEST_PRODUCT_A: {
        TEST_LAUNCH_MODE_A1: MockLauncherA1,
        TEST_LAUNCH_MODE_A2: MockLauncherA2,
    },
    TEST_PRODUCT_B: {TEST_LAUNCH_MODE_B1: MockLauncherB1},
}


@pytest.fixture
def monkeypatch_entrypoints(monkeypatch_entrypoints_from_plugins):
    """Mock the entry points for the launcher plugins."""
    monkeypatch_entrypoints_from_plugins(PLUGINS)


def test_get_all_plugins(monkeypatch_entrypoints):
    """Test getting all plugins."""
    assert _plugins.get_all_plugins() == PLUGINS


@pytest.mark.parametrize(
    "product_name,launch_mode,expected_config_model",
    [
        (TEST_PRODUCT_A, TEST_LAUNCH_MODE_A1, MockConfigA1),
        (TEST_PRODUCT_A, TEST_LAUNCH_MODE_A2, MockConfigA2),
        (TEST_PRODUCT_B, TEST_LAUNCH_MODE_B1, MockConfigB1),
    ],
)
def test_get_config_model(monkeypatch_entrypoints, product_name, launch_mode, expected_config_model):
    """Test getting a config model returns expected class for the given product and launch mode."""
    assert _plugins.get_config_model(product_name=product_name, launch_mode=launch_mode) == expected_config_model


@pytest.mark.parametrize(
    "product_name,launch_mode,expected_launcher",
    [
        (TEST_PRODUCT_A, TEST_LAUNCH_MODE_A1, MockLauncherA1),
        (TEST_PRODUCT_A, TEST_LAUNCH_MODE_A2, MockLauncherA2),
        (TEST_PRODUCT_B, TEST_LAUNCH_MODE_B1, MockLauncherB1),
    ],
)
def test_get_launcher(monkeypatch_entrypoints, product_name, launch_mode, expected_launcher):
    """Test that getting a launcher returns the expected class for the given product and launch mode."""
    assert _plugins.get_launcher(product_name=product_name, launch_mode=launch_mode) == expected_launcher


def test_get_launcher_inexistent():
    """Test that getting a launcher for a non-existent product or launch mode raises error."""
    with pytest.raises(KeyError) as exc:
        _plugins.get_launcher(product_name="does_not_exist", launch_mode="does_not_exist")
    assert "No plugin found" in str(exc.value)
