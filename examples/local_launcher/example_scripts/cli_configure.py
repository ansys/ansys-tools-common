# Copyright (C) 2022 - 2025 ANSYS, Inc. and/or its affiliates.
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

"""
Configure the launcher from the command line
--------------------------------------------

This example shows how to configure the ``example_httpserver`` plugin from the command line.
It consists mostly of command-line interactions. With the exception of interactive commands,
this example can be run when downloaded as a Jupyter notebook. The interactive commands and
their outputs are simply shown as text.

The configuration contains only a single value, ``directory``, which specifies the
where the HTTP server is to serve files from.

"""

# %%
# To see the list of launch modes for the ``example_httpserver`` product, run
# this code:
#
# .. code-block:: bash
#
#   %%bash
#   ansys-launcher configure example_httpserver
#
# Here is the output:
#
# ::
#
#   Usage: ansys-launcher configure example_httpserver [OPTIONS] COMMAND [ARGS]...
#
#   Options:
#   --help  Show this message and exit.
#
#   Commands:
#   direct

# %%
# Interactive configuration
# ~~~~~~~~~~~~~~~~~~~~~~~~~
#
# To interactively specify the available configuration options, run
# this command:
#
# .. code-block:: bash
#
#   ansys-launcher configure example_httpserver direct
#
# The preceding command might result in a session like this:
#
# ::
#
#   directory:
#    [<current-working-directory>]: /path/to/directory
#
#   Updated /home/<your_username>/.config/ansys_tools_local_product_launcher/config.json

# %%
# Non-interactive configuration
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Alternatively, you can specify the configuration fully from the command line (non-interactively):
#
# .. code-block:: bash
#
#   %%bash
#   ansys-launcher configure example_httpserver direct --directory /path/to/directory
