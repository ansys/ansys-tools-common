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

"""Convenience CLI to save path for ansys application in configuration."""

import click

from ansys.tools.common.path.path import _save_path


@click.command()
@click.help_option("--help", "-h")
@click.argument("location")
@click.option(
    "--name",
    default=None,
    type=str,
    help='Application name. For example, "mapdl", "mechanical", or "dyna"',
)
@click.option(
    "--allow-prompt",
    is_flag=True,
    default=False,
    help="Allow prompt. Used in case a path is not given or the given path is not valid",
)
def cli(
    name: str,
    location: str,
    allow_prompt: bool,
):
    """CLI tool to store the path of a solver.

    USAGE:

    The following example demonstrates the main use of this tool:

        $ save-ansys-path --name dyna /path/to/dyna
    """
    _save_path(name, location, allow_prompt)
