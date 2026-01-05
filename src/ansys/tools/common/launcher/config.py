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

"""Tools for managing local product launcher configuration.

The methods in the ``config`` class manage the default configuration
for launching products. The configuration is loaded from and stored to a
``config.json`` file. By default, this file is located in the user configuration
directory (platform-dependent). Its location can be specified explicitly
with the ``ANSYS_LAUNCHER_CONFIG_PATH`` environment variable.
"""

import dataclasses
import json
import os
import pathlib
from typing import Any, cast

import platformdirs

from ._plugins import get_config_model, get_fallback_launcher, has_fallback
from .interface import FALLBACK_LAUNCH_MODE_NAME, LAUNCHER_CONFIG_T, DataclassProtocol

__all__ = [
    "get_config_for",
    "set_config_for",
    "is_configured",
    "get_launch_mode_for",
    "save_config",
]


_CONFIG_PATH_ENV_VAR_NAME = "ANSYS_LAUNCHER_CONFIG_PATH"


@dataclasses.dataclass
class _ProductConfig:
    launch_mode: str
    configs: dict[str, Any]


@dataclasses.dataclass
class _LauncherConfiguration:
    __root__: dict[str, _ProductConfig]


_CONFIG: _LauncherConfiguration | None = None


def get_launch_mode_for(*, product_name: str, launch_mode: str | None = None) -> str:
    """Get the default launch mode configured for a product.

    Parameters
    ----------
    product_name : str
        Product to retrieve the launch mode for.
    launch_mode : str, default: None
        Launch mode to use. The default is ``None``, in which case the default
        launch mode is used. If a launch mode is specified, this value is returned.

    Returns
    -------
    str or None
        Launch mode for the product.
    """
    if launch_mode is not None:
        return launch_mode
    try:
        return _get_config()[product_name].launch_mode
    except KeyError as exc:
        if has_fallback(product_name=product_name):
            return FALLBACK_LAUNCH_MODE_NAME
        raise KeyError(f"No configuration is defined for product name '{product_name}'.") from exc


def get_config_for(*, product_name: str, launch_mode: str | None) -> DataclassProtocol:
    """Get the configuration object for a given product and launch mode.

    Get the default configuration object for the product. If a
    ``launch_mode`` parameter is given, the configuration for
    this mode is returned. Otherwise, the configuration for
    the default launch mode is returned.

    Parameters
    ----------
    product_name : str
        Product to get the configuration for.
    launch_mode : str, default: None
        Launch mode for the configuration.

    Returns
    -------
    DataclassProtocol
        Configuration object.

    Raises
    ------
    KeyError
        If the requested configuration does not exist.
    TypeError
        If the configuration type does not match the type specified by
        the launcher plugin.
    """
    launch_mode = get_launch_mode_for(product_name=product_name, launch_mode=launch_mode)

    # Handle the case where the fallback launcher is used
    if launch_mode == FALLBACK_LAUNCH_MODE_NAME:
        return get_fallback_launcher(product_name=product_name).CONFIG_MODEL()
    config_class: type[DataclassProtocol] = get_config_model(product_name=product_name, launch_mode=launch_mode)
    # Handle the case where the launch mode is specified, but not configured
    if not is_configured(product_name=product_name, launch_mode=launch_mode):
        try:
            config_entry = config_class()
        except TypeError as exc:
            raise RuntimeError(
                f"Launch mode '{launch_mode}' for product '{product_name}' "
                f"does not have a default configuration and is not configured."
            ) from exc
        return config_entry

    # Handle the regular (configured) case
    config_entry = _get_config()[product_name].configs[launch_mode]
    if isinstance(config_entry, dict):
        _get_config()[product_name].configs[launch_mode] = config_class(**config_entry)
    else:
        if not isinstance(config_entry, config_class):
            raise TypeError(f"Configuration is wrong type '{type(config_entry)}'. Should be '{config_class}'.")
    return cast(DataclassProtocol, _get_config()[product_name].configs[launch_mode])


def is_configured(*, product_name: str, launch_mode: str | None = None) -> bool:
    """Check if a configuration exists for a given product and launch mode.

    Note that if only the fallback launcher/configuration is available, this method returns ``False``.

    Parameters
    ----------
    product_name :str
        Product whose configuration is checked.
    launch_mode : str, default: None
        Launch mode whose configuration is checked. The
        default is ``None``, in which case the default
        launch mode is used.
    """
    try:
        launch_mode = get_launch_mode_for(product_name=product_name, launch_mode=launch_mode)
        if launch_mode == FALLBACK_LAUNCH_MODE_NAME:
            return False
        _get_config()[product_name].configs[launch_mode]
        return True
    except KeyError:
        return False


def set_config_for(
    *,
    product_name: str,
    launch_mode: str,
    config: LAUNCHER_CONFIG_T,
    overwrite_default: bool = False,
) -> None:
    """Set the configuration for a given product and launch mode.

    Update the configuration by setting the configuration for the
    given product and launch mode.

    This method only updates the in-memory configuration. It
    does not store it to a file.

    Parameters
    ----------
    product_name : str
        Name of the product whose configuration to update.
    launch_mode : str
        Launch mode that the configuration applies to.
    config : LAUNCHER_CONFIG_T
        Configuration object.
    overwrite_default : bool, default: False
        Whether to change the default launch mode for the product
        to the value specified for the ``launch_mode`` parameter.
    """
    if is_configured(product_name=product_name):
        product_config = _get_config()[product_name]
        product_config.configs[launch_mode] = config
        if overwrite_default:
            product_config.launch_mode = launch_mode
    else:
        _get_config()[product_name] = _ProductConfig(launch_mode=launch_mode, configs={launch_mode: config})


def save_config() -> None:
    """Save the configuration to a file on disk.

    This method saves the current in-memory configuration to the ``config.json`` file.
    """
    if _CONFIG is not None:
        file_path = _get_config_path()
        # Convert to JSON before saving; in this way, errors during
        # JSON encoding will not clobber the config file.
        config_json = json.dumps(dataclasses.asdict(_CONFIG)["__root__"], indent=2)
        with file_path.open("w") as out_f:
            out_f.write(config_json)


def _get_config() -> dict[str, _ProductConfig]:
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = _load_config()
    return _CONFIG.__root__


def _load_config() -> _LauncherConfiguration:
    config_path = _get_config_path()
    if not config_path.exists():
        return _LauncherConfiguration(__root__={})
    with config_path.open() as in_f:
        return _LauncherConfiguration(__root__={key: _ProductConfig(**val) for key, val in json.load(in_f).items()})


def _reset_config() -> None:
    global _CONFIG
    _CONFIG = None


def _get_config_path() -> pathlib.Path:
    if _CONFIG_PATH_ENV_VAR_NAME in os.environ:
        config_path = pathlib.Path(os.environ[_CONFIG_PATH_ENV_VAR_NAME])
        if not config_path.parent.exists():
            raise FileNotFoundError(
                f"The directory {config_path.parent} specified in the "
                f"{_CONFIG_PATH_ENV_VAR_NAME} environment variable does not exist."
            )

    else:
        config_path_dir = pathlib.Path(platformdirs.user_config_dir("ansys_tools_local_product_launcher"))
        config_path = config_path_dir / "config.json"
        try:
            # Set up data directory
            config_path_dir.mkdir(exist_ok=True, parents=True)
        except OSError as exc:
            raise type(exc)(
                f"Unable to create config directory '{config_path_dir}'.\n"
                f"Error:\n{exc}\n\n"
                "Override the default config file path by setting the environment "
                f"variable '{_CONFIG_PATH_ENV_VAR_NAME}'."
            ) from exc
    return config_path
