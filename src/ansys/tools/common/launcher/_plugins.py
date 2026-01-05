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

from __future__ import annotations

from functools import lru_cache
import importlib.metadata
from importlib.metadata import entry_points
from typing import Any
import warnings

from .interface import FALLBACK_LAUNCH_MODE_NAME, DataclassProtocol, LauncherProtocol

LAUNCHER_ENTRY_POINT = "ansys.tools.common.launcher"
DEPRECATED_LAUNCHER_ENTRY_POINT = "ansys.tools.local_product_launcher.launcher"


def get_launcher(*, product_name: str, launch_mode: str) -> type[LauncherProtocol[DataclassProtocol]]:
    """Get the launcher plugin class for a given product and launch mode."""
    ep_name = f"{product_name}.{launch_mode}"
    for entrypoint in _get_entry_points():
        if entrypoint.name == ep_name:
            return entrypoint.load()  # type: ignore
    raise KeyError(f"No plugin found for '{ep_name}'.")


def get_config_model(*, product_name: str, launch_mode: str) -> type[DataclassProtocol]:
    """Get the configuration model class for a given product and launch mode."""
    return get_launcher(product_name=product_name, launch_mode=launch_mode).CONFIG_MODEL


def get_all_plugins(hide_fallback: bool = True) -> dict[str, dict[str, type[LauncherProtocol[Any]]]]:
    """Get mapping {"<product_name>": {"<launch_mode>": LauncherClass}} containing all launcher plugins.

    Parameters
    ----------
    hide_fallback : bool, default=True
        If True, skip launch modes marked as fallback.

    Returns
    -------
    dict[str, dict[str, type[LauncherProtocol[Any]]]]
        Mapping of product names to launch mode to launcher classes.
    """
    res: dict[str, dict[str, type[LauncherProtocol[Any]]]] = dict()
    for entry_point in _get_entry_points():
        try:
            product_name, launch_mode = entry_point.name.split(".")
        except ValueError:
            message = f"Skipping malformed entry point name: {entry_point.name}"
            warnings.warn(message)
            continue

        if hide_fallback and launch_mode == FALLBACK_LAUNCH_MODE_NAME:
            continue

        try:
            launcher_class = entry_point.load()
        except Exception as exception:
            message = f"Skipping broken plugin '{entry_point.name}': {exception}"
            warnings.warn(message)
            continue

        res.setdefault(product_name, dict())
        res[product_name][launch_mode] = launcher_class

    return res


def has_fallback(product_name: str) -> bool:
    """Return True if the given product has a fallback launcher."""
    for entry_point in _get_entry_points():
        try:
            ep_product_name, ep_launch_mode = entry_point.name.split(".")
        except ValueError:
            continue
        if product_name == ep_product_name and ep_launch_mode == FALLBACK_LAUNCH_MODE_NAME:
            return True
    return False


def get_fallback_launcher(product_name: str) -> type[LauncherProtocol[DataclassProtocol]]:
    """Get the fallback launcher plugin class for a given product."""
    ep_name = f"{product_name}.{FALLBACK_LAUNCH_MODE_NAME}"
    for entrypoint in _get_entry_points():
        if entrypoint.name == ep_name:
            return entrypoint.load()  # type: ignore
    raise KeyError(f"No plugin found for '{ep_name}'.")


@lru_cache
def _get_entry_points() -> tuple[importlib.metadata.EntryPoint, ...]:
    """Get all Local Product Launcher plugin entrypoints for launchers."""
    try:
        return entry_points(group=LAUNCHER_ENTRY_POINT) + entry_points(group=DEPRECATED_LAUNCHER_ENTRY_POINT)  # type: ignore
    except KeyError:
        return tuple()
