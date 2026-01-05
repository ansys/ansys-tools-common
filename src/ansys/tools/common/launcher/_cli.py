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

from collections.abc import Callable, Sequence
import dataclasses
import json
import textwrap
from typing import Any, cast

import click

from ._plugins import get_all_plugins
from .config import (
    _get_config_path,
    get_config_for,
    get_launch_mode_for,
    is_configured,
    save_config,
    set_config_for,
)
from .interface import LAUNCHER_CONFIG_T, METADATA_KEY_DOC, METADATA_KEY_NOPROMPT, LauncherProtocol


def format_prompt(*, field_name: str, description: str | None) -> str:
    """Get the formatted prompt string from its field name and description."""
    prompt = f"\n{field_name}:"
    if description is not None:
        prompt += "\n" + textwrap.indent(description, " " * 4)
    prompt += "\n"
    return prompt


_OVERWRITE_DEFAULT_FLAG_NAME = "overwrite_default"
_DEFAULT_STR = "default"


def get_subcommands_from_plugins(
    *, plugins: dict[str, dict[str, type[LauncherProtocol[LAUNCHER_CONFIG_T]]]]
) -> Sequence[click.Command]:
    """Construct ``configure`` subcommands from the plugins."""
    all_product_commands: list[click.Group] = []
    for product_name, launch_mode_configs in plugins.items():
        product_command = click.Group(product_name)
        all_product_commands.append(product_command)
        for launch_mode, launcher_kls in launch_mode_configs.items():
            launcher_config_kls = launcher_kls.CONFIG_MODEL

            _config_writer_callback = config_writer_callback_factory(launcher_config_kls, product_name, launch_mode)
            launch_mode_command = click.Command(launch_mode, callback=_config_writer_callback)
            for field in dataclasses.fields(launcher_config_kls):
                option = get_option_from_field(field)
                launch_mode_command.params.append(option)

            extra_kwargs_overwrite_option = dict()
            if is_configured(product_name=product_name):
                current_launch_mode = get_launch_mode_for(product_name=product_name)
                if current_launch_mode != launch_mode:
                    extra_kwargs_overwrite_option = dict(
                        prompt=(
                            f"\nOverwrite default launch mode for {product_name} "
                            f"(currently set to '{current_launch_mode}')?"
                        ),
                        show_default=True,
                    )

            launch_mode_command.params.append(
                click.Option(
                    [f"--{_OVERWRITE_DEFAULT_FLAG_NAME}"],
                    is_flag=True,
                    **extra_kwargs_overwrite_option,  # type: ignore
                )
            )

            product_command.add_command(launch_mode_command)

    return all_product_commands


class JSONParamType(click.ParamType):
    """Implements interpreting options as JSON.

    An empty string is interpreted as ``None``.
    """

    name = "json"

    def convert(self, value: Any, param: Any, ctx: Any) -> Any:
        """Convert the string to a dictionary."""
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        if value == _DEFAULT_STR:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise ValueError(f"Cannot decode JSON value '{value}'") from e


def get_option_from_field(field: "dataclasses.Field[Any]") -> click.Option:
    """Construct a click.Option from a dataclass field.

    Convert the field type, default, and metadata to the corresponding
    click.Option.
    """
    # The annotations can be either a type or a string, depending on whether
    # deferred evaluation is used.
    type_ = {
        int: int,
        str: str,
        bool: bool,
        "int": int,
        "str": str,
        "bool": bool,
    }.get(field.type, JSONParamType())

    if field.default is not dataclasses.MISSING:
        default = field.default
        if default is None:
            default = _DEFAULT_STR
            if not isinstance(type_, JSONParamType):
                raise ValueError(f"Invalid default value 'None' for {type_} type.")
    elif field.default_factory is not dataclasses.MISSING:
        default = field.default_factory()
    else:
        default = None

    description = field.metadata.get(METADATA_KEY_DOC, None)
    prompt_required = not field.metadata.get(METADATA_KEY_NOPROMPT, False)
    return click.Option(
        [f"--{field.name}"],
        prompt=format_prompt(
            field_name=field.name,
            description=description,
        ),
        help=description,
        type=type_,
        default=default,
        prompt_required=prompt_required,
    )


def config_writer_callback_factory(
    launcher_config_kls: type[LAUNCHER_CONFIG_T], product_name: str, launch_mode: str
) -> Callable[..., None]:
    """Construct the callback for updating the configuration file."""

    def _config_writer_callback(**kwargs: dict[str, Any]) -> None:
        overwrite_default = cast(bool, kwargs.pop(_OVERWRITE_DEFAULT_FLAG_NAME, False))
        config = launcher_config_kls(**kwargs)
        set_config_for(
            product_name=product_name,
            launch_mode=launch_mode,
            config=config,
            overwrite_default=overwrite_default,
        )
        save_config()
        click.echo(f"\nUpdated {_get_config_path()}")

    return _config_writer_callback


def build_cli(plugins: dict[str, dict[str, type[LauncherProtocol[LAUNCHER_CONFIG_T]]]]) -> click.Group:
    """Build the CLI from the plugins."""
    _cli = click.Group()

    all_subcommands = get_subcommands_from_plugins(plugins=plugins)

    @_cli.group(invoke_without_command=True)
    @click.pass_context
    def configure(ctx: click.Context) -> None:
        """
        Configure the options for a specific product and launch mode.

        The available products and launch modes are determined dynamically
        from the installed plugins.

        To get a list of products:

        .. code:: bash

            ansys-launcher configure

        To get a list of launch modes for a given product:

        .. code:: bash

            ansys-launcher configure <PRODUCT_NAME>

        To configure a product launch mode:

        .. code:: bash

            ansys-launcher configure <PRODUCT_NAME> <LAUNCH_MODE>

        """
        if ctx.invoked_subcommand is None:
            if not plugins:
                click.echo("No plugins are configured.")
            else:
                click.echo(ctx.get_help())

    for subcommand in all_subcommands:
        configure.add_command(subcommand)

    @_cli.command()
    # @click.pass_context
    def list_plugins() -> None:
        """List the possible product/launch mode combinations."""
        if not plugins:
            click.echo("No plugins are configured.")
            return
        for product_name, launch_mode_configs in sorted(plugins.items()):
            click.echo(f"{product_name}")
            for launch_mode in sorted(launch_mode_configs.keys()):
                click.echo(f"    {launch_mode}")
            click.echo("")

    @_cli.command()
    def show_config() -> None:
        """Show the current configuration."""
        for product_name, launch_mode_configs in sorted(plugins.items()):
            click.echo(f"{product_name}")
            try:
                default_launch_mode = get_launch_mode_for(product_name=product_name)
                for launch_mode in sorted(launch_mode_configs.keys()):
                    if launch_mode == default_launch_mode:
                        click.echo(f"    {launch_mode} (default)")
                    else:
                        click.echo(f"    {launch_mode}")

                    if not is_configured(product_name=product_name, launch_mode=launch_mode):
                        try:
                            config = get_config_for(product_name=product_name, launch_mode=launch_mode)
                            click.echo("        No configuration is set (uses defaults).")
                        except (KeyError, RuntimeError):
                            click.echo("        No configuration is set (no defaults available).")
                            continue
                    try:
                        config = get_config_for(product_name=product_name, launch_mode=launch_mode)
                        for field in dataclasses.fields(config):
                            click.echo(f"        {field.name}: {getattr(config, field.name)}")
                    except TypeError:
                        click.echo("        No configuration is set (invalid configuration).")
            except KeyError:
                click.echo("    No configuration is set.")
            click.echo("")

    @_cli.command()
    def show_config_path() -> None:
        """Show the path to the configuration file."""
        click.echo(_get_config_path())

    return _cli


# Needs to be defined at the module level, since this is what the [tool.poetry.scripts]
# entrypoint refers to.
cli = build_cli(plugins=get_all_plugins())

if __name__ == "__main__":
    cli()
