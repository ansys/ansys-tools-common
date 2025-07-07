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
"""Module for multiple plugins test."""

from dataclasses import dataclass

from click.testing import CliRunner
import pytest

from ansys.tools.common.launcher import _cli, _plugins, config, interface

from .common import check_result_config

TEST_PRODUCT_A = "PRODUCT_A"
TEST_PRODUCT_B = "PRODUCT_B"
TEST_LAUNCH_MODE_A1 = "LAUNCHER_A1"
TEST_LAUNCH_MODE_A2 = "LAUNCHER_A2"
TEST_LAUNCH_MODE_B1 = "LAUNCHER_B1"


@dataclass
class MockConfigA1:
    """Mock config."""

    field_a1: int


class MockLauncherA1(interface.LauncherProtocol[MockConfigA1]):
    """Mock launcher."""

    CONFIG_MODEL = MockConfigA1


@dataclass
class MockConfigA2:
    """Mock config."""

    field_a2: int


class MockLauncherA2(interface.LauncherProtocol[MockConfigA2]):
    """Mock launcher."""

    CONFIG_MODEL = MockConfigA2


@dataclass
class MockConfigB1:
    """Mock config."""

    field_b1: int


class MockLauncherB1(interface.LauncherProtocol[MockConfigB1]):
    """Mock launcher for testing CLI configuration for product B."""

    CONFIG_MODEL = MockConfigB1


PLUGINS = {
    TEST_PRODUCT_A: {
        TEST_LAUNCH_MODE_A1: MockLauncherA1,
        TEST_LAUNCH_MODE_A2: MockLauncherA2,
    },
    TEST_PRODUCT_B: {TEST_LAUNCH_MODE_B1: MockLauncherB1},
}


@pytest.fixture(autouse=True)
def monkeypatch_entrypoints(monkeypatch_entrypoints_from_plugins):
    """Mock entrypoints for the plugins."""
    monkeypatch_entrypoints_from_plugins(PLUGINS)


def test_cli_structure():
    """Test CLI structure."""
    command = _cli.build_cli(_plugins.get_all_plugins())
    assert "configure" in command.commands
    configure_group = command.commands["configure"]

    assert TEST_PRODUCT_A in configure_group.commands
    assert TEST_PRODUCT_B in configure_group.commands

    assert TEST_LAUNCH_MODE_A1 in configure_group.commands[TEST_PRODUCT_A].commands
    assert TEST_LAUNCH_MODE_A2 in configure_group.commands[TEST_PRODUCT_A].commands
    assert TEST_LAUNCH_MODE_B1 in configure_group.commands[TEST_PRODUCT_B].commands

    assert configure_group.commands[TEST_PRODUCT_A].commands[TEST_LAUNCH_MODE_A1].params[0].name == "field_a1"


def test_configure_single_product_launcher(temp_config_file):
    """Test configuring a single product with a single launcher."""
    cli_command = _cli.build_cli(_plugins.get_all_plugins())
    runner = CliRunner()
    result = runner.invoke(
        cli_command,
        ["configure", TEST_PRODUCT_A, TEST_LAUNCH_MODE_A1, "--field_a1=1"],
    )

    assert result.exit_code == 0
    expected_config = {
        TEST_PRODUCT_A: {
            "configs": {
                TEST_LAUNCH_MODE_A1: {"field_a1": 1},
            },
            "launch_mode": TEST_LAUNCH_MODE_A1,
        }
    }
    check_result_config(temp_config_file, expected_config)


def test_configure_two_product_launchers(temp_config_file):
    """Test configuring two different products with different launch modes."""
    cli_command = _cli.build_cli(_plugins.get_all_plugins())
    runner = CliRunner()
    result = runner.invoke(
        cli_command,
        ["configure", TEST_PRODUCT_A, TEST_LAUNCH_MODE_A1, "--field_a1=1"],
    )
    assert result.exit_code == 0
    config._reset_config()

    result = runner.invoke(
        cli_command,
        ["configure", TEST_PRODUCT_A, TEST_LAUNCH_MODE_A2, "--field_a2=2"],
    )
    assert result.exit_code == 0

    expected_config = {
        TEST_PRODUCT_A: {
            "configs": {
                TEST_LAUNCH_MODE_A1: {"field_a1": 1},
                TEST_LAUNCH_MODE_A2: {"field_a2": 2},
            },
            "launch_mode": TEST_LAUNCH_MODE_A1,
        }
    }
    check_result_config(temp_config_file, expected_config)


def test_configure_two_product_launchers_overwrite(temp_config_file):
    """Test configuring two products with overwriting configurations."""
    cli_command = _cli.build_cli(_plugins.get_all_plugins())
    runner = CliRunner()
    result = runner.invoke(
        cli_command,
        ["configure", TEST_PRODUCT_A, TEST_LAUNCH_MODE_A1, "--field_a1=1"],
    )
    assert result.exit_code == 0
    config._reset_config()

    result = runner.invoke(
        cli_command,
        ["configure", TEST_PRODUCT_A, TEST_LAUNCH_MODE_A2, "--field_a2=2", "--overwrite_default"],
    )
    assert result.exit_code == 0

    expected_config = {
        TEST_PRODUCT_A: {
            "configs": {
                TEST_LAUNCH_MODE_A1: {"field_a1": 1},
                TEST_LAUNCH_MODE_A2: {"field_a2": 2},
            },
            "launch_mode": TEST_LAUNCH_MODE_A2,
        }
    }
    check_result_config(temp_config_file, expected_config)


def test_configure_two_products(temp_config_file):
    """Test configuring two products."""
    cli_command = _cli.build_cli(_plugins.get_all_plugins())
    runner = CliRunner()
    result = runner.invoke(
        cli_command,
        ["configure", TEST_PRODUCT_A, TEST_LAUNCH_MODE_A1, "--field_a1=1"],
    )
    assert result.exit_code == 0
    config._reset_config()

    result = runner.invoke(
        cli_command,
        ["configure", TEST_PRODUCT_B, TEST_LAUNCH_MODE_B1, "--field_b1=3"],
    )
    assert result.exit_code == 0

    expected_config = {
        TEST_PRODUCT_A: {
            "configs": {
                TEST_LAUNCH_MODE_A1: {"field_a1": 1},
            },
            "launch_mode": TEST_LAUNCH_MODE_A1,
        },
        TEST_PRODUCT_B: {
            "configs": {
                TEST_LAUNCH_MODE_B1: {"field_b1": 3},
            },
            "launch_mode": TEST_LAUNCH_MODE_B1,
        },
    }
    check_result_config(temp_config_file, expected_config)
