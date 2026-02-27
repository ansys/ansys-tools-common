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

"""Defines a function for launching Ansys products."""

from __future__ import annotations

from typing import cast

from ._plugins import get_launcher
from .config import get_config_for, get_launch_mode_for
from .interface import LAUNCHER_CONFIG_T, LauncherProtocol
from .product_instance import ProductInstance


def launch_product(
    product_name: str,
    *,
    launch_mode: str | None = None,
    config: LAUNCHER_CONFIG_T | None = None,
) -> ProductInstance:
    """Launch a product instance.

    Parameters
    ----------
    product_name : str
        Name of the product to launch.
    launch_mode : str, default: None
        Launch mode to use. The default is ``None``, in which case
        the default launched mode is used. Options available
        depend on the launcher plugin.
    config : LAUNCHER_CONFIG_T, default: None
        Configuration to use for launching the product. The default is
        ``None``, in which case the default configuration is used.

    Returns
    -------
    ProductInstance
        Object that can be used to interact with the started product.

    Raises
    ------
    TypeError
        If the type of the configuration object does not match the type
        requested by the launcher plugin.
    """
    launch_mode = get_launch_mode_for(product_name=product_name, launch_mode=launch_mode)

    # The type of the CONFIG_MODEL is checked below, so here we can cast
    # from type[LauncherProtocol[DataclassProtocol]] to type[LauncherProtocol[LAUNCHER_CONFIG_T]].
    launcher_klass = cast(
        type[LauncherProtocol[LAUNCHER_CONFIG_T]],
        get_launcher(
            product_name=product_name,
            launch_mode=launch_mode,
        ),
    )

    if config is None:
        config = get_config_for(product_name=product_name, launch_mode=launch_mode)  # type: ignore
    if not isinstance(config, launcher_klass.CONFIG_MODEL):
        raise TypeError(
            f"Incompatible config of type '{type(config)} is supplied. It needs to be '{launcher_klass.CONFIG_MODEL}'."
        )
    return ProductInstance(launcher=launcher_klass(config=config))
