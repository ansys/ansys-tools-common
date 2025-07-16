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
"""Module for testing plugins."""

from dataclasses import dataclass, field

from click.testing import CliRunner
import pytest

from ansys.tools.common.launcher import _cli, interface

from .common import check_result_config


@dataclass
class MockConfig:
    """Mock configuration for testing CLI."""

    int_field: int
    str_field: str
    json_field: dict[str, str]
    optional_field: str | None = None
    noprompt_field: str = field(metadata={interface.METADATA_KEY_NOPROMPT: True}, default="noprompt_value")


class MockLauncher(interface.LauncherProtocol[MockConfig]):
    """Mock launcher for testing CLI configuration."""

    CONFIG_MODEL = MockConfig


TEST_PRODUCT = "my_product"
TEST_LAUNCH_MODE = "my_launcher"

EXPECTED_CONFIG = {
    TEST_PRODUCT: {
        "configs": {
            TEST_LAUNCH_MODE: {
                "int_field": 1,
                "str_field": "value",
                "json_field": {"a": "b"},
                "optional_field": None,
                "noprompt_field": "noprompt_value",
            }
        },
        "launch_mode": TEST_LAUNCH_MODE,
    }
}


@pytest.fixture
def mock_plugins():
    """Mock plugin for testing CLI."""
    return {TEST_PRODUCT: {TEST_LAUNCH_MODE: MockLauncher}}


def test_cli_no_plugins():
    """Test that the CLI is built correctly with no plugins."""
    command = _cli.build_cli(dict())
    runner = CliRunner()
    result = runner.invoke(command, ["configure"])
    assert result.exit_code == 0
    assert "No plugins" in result.output


def test_cli_mock_plugin(mock_plugins):
    """Test that the CLI is built correctly with a mock plugin."""
    command = _cli.build_cli(mock_plugins)
    assert "configure" in command.commands
    configure_group = command.commands["configure"]

    assert len(configure_group.commands) == 1
    assert TEST_PRODUCT in configure_group.commands

    product_group = configure_group.commands[TEST_PRODUCT]
    assert TEST_LAUNCH_MODE in product_group.commands

    launcher_command = product_group.commands[TEST_LAUNCH_MODE]
    assert len(launcher_command.params) == 6
    assert [p.name for p in launcher_command.params] == [
        "int_field",
        "str_field",
        "json_field",
        "optional_field",
        "noprompt_field",
        "overwrite_default",
    ]


@pytest.mark.parametrize(
    ["commands", "prompts"],
    [
        (
            [
                "configure",
                TEST_PRODUCT,
                TEST_LAUNCH_MODE,
                "--int_field=1",
                "--str_field=value",
                '--json_field={"a": "b"}',
            ],
            [""],
        ),
        (["configure", "my_product", "my_launcher", "--str_field=value"], ["1", '{"a": "b"}', ""]),
        (["configure", "my_product", "my_launcher", "--int_field=1"], ["value", '{"a": "b"}', ""]),
        (["configure", "my_product", "my_launcher", '--json_field={"a": "b"}'], ["1", "value", ""]),
        (
            [
                "configure",
                "my_product",
                "my_launcher",
            ],
            ["1", "value", '{"a": "b"}', ""],
        ),
        (["configure", "my_product", "my_launcher"], ["1", "value", '{"a": "b"}', ""]),
        (
            ["configure", "my_product", "my_launcher", "--noprompt_field"],
            ["noprompt_value", "1", "value", '{"a": "b"}', ""],
        ),
        (
            ["configure", "my_product", "my_launcher", "--noprompt_field=noprompt_value"],
            ["1", "value", '{"a": "b"}', ""],
        ),
    ],
)
def test_run_cli(temp_config_file, mock_plugins, commands, prompts):
    """Test running the CLI."""
    cli_command = _cli.build_cli(mock_plugins)
    runner = CliRunner()
    result = runner.invoke(
        cli_command,
        commands,
        input=("\n".join(prompts) + "\n") if prompts else None,
    )

    assert result.exit_code == 0, result.output
    check_result_config(temp_config_file, EXPECTED_CONFIG)


def test_run_cli_throws_on_incorrect_type(temp_config_file, mock_plugins):
    """Test that the CLI throws an error when a field is given an incorrect type."""
    cli_command = _cli.build_cli(mock_plugins)
    runner = CliRunner()
    result = runner.invoke(
        cli_command,
        ["configure", TEST_PRODUCT, TEST_LAUNCH_MODE, "--int_field=TEXT", "--str_field=value"],
    )
    assert result.exit_code != 0
