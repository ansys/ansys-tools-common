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

from dataclasses import dataclass

import pytest

from ansys.tools.local_product_launcher import config, launch_product

from .simple_test_launcher import SimpleLauncher, SimpleLauncherConfig

PRODUCT_NAME = "TestProduct"
LAUNCH_MODE = "direct"


@dataclass
class OtherConfig:
    int_attr: int


@pytest.fixture(autouse=True)
def monkeypatch_entrypoints(monkeypatch_entrypoints_from_plugins):
    monkeypatch_entrypoints_from_plugins({PRODUCT_NAME: {"direct": SimpleLauncher}})


def test_default_config():
    config.set_config_for(product_name=PRODUCT_NAME, launch_mode=LAUNCH_MODE, config=SimpleLauncherConfig())
    server = launch_product(PRODUCT_NAME)
    server.wait(timeout=10)
    server.stop()
    assert not server.check()


def test_explicit_config():
    server = launch_product(PRODUCT_NAME, launch_mode=LAUNCH_MODE, config=SimpleLauncherConfig())
    server.wait(timeout=10)
    server.stop()
    assert not server.check()


def test_stop_with_timeout():
    server = launch_product(PRODUCT_NAME, launch_mode=LAUNCH_MODE, config=SimpleLauncherConfig())
    server.wait(timeout=10)
    server.stop(timeout=1.0)
    assert not server.check()


def test_invalid_launch_mode_raises():
    with pytest.raises(KeyError):
        launch_product(PRODUCT_NAME, launch_mode="invalid_launch_mode", config=SimpleLauncherConfig())


def test_invalid_config_raises():
    with pytest.raises(TypeError):
        launch_product(PRODUCT_NAME, launch_mode=LAUNCH_MODE, config=OtherConfig(int_attr=3))


def test_contextmanager():
    with launch_product(PRODUCT_NAME, launch_mode=LAUNCH_MODE, config=SimpleLauncherConfig()) as server:
        server.wait(timeout=10)
        assert server.check()
    assert not server.check()
