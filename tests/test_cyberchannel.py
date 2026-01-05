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
"""Tests for cyberchannel."""

import os
from pathlib import Path
import tempfile

import pytest

from ansys.tools.common import cyberchannel


def test_version_tuple():
    """Test version tuple."""
    assert cyberchannel.version_tuple("1.2.3") == (1, 2, 3)
    assert cyberchannel.version_tuple("1.2.3.4") == (1, 2, 3, 4)
    assert cyberchannel.version_tuple("1.0.0") == (1, 0, 0)


def test_cyberchannel_functions():
    """Test cyberchannel functions."""
    assert cyberchannel.check_grpc_version()
    assert cyberchannel.is_uds_supported()
    uds_path = cyberchannel.determine_uds_folder()
    uds_path.mkdir(parents=True, exist_ok=True)
    assert uds_path.is_dir()
    assert uds_path.exists()
    uds_path.rmdir()
    cyberchannel.verify_transport_mode(transport_mode="insecure", mode="local")
    with pytest.raises(ValueError):
        cyberchannel.verify_transport_mode(transport_mode="invalid_mode", mode="mode1")


def test_cyberchannel_insecure():
    """Test cyberchannel insecure."""
    ch = cyberchannel.create_insecure_channel(host="localhost", port=12345)
    assert ch is not None
    assert ch._channel.target().decode() == "dns:///localhost:12345"
    assert not ch.close()


@pytest.mark.skipif(os.name != "nt", reason="WNUA is only supported on Windows.")
def test_cyberchannel_wnua():
    """Test cyberchannel wnua."""
    ch = cyberchannel.create_wnua_channel(host="localhost", port=12345)
    assert ch is not None
    assert ch._channel.target().decode() == "dns:///localhost:12345"
    assert not ch.close()


def test_cyberchannel_uds():
    """Test cyberchannel uds."""
    uds_file = Path(tempfile.gettempdir()) / "test_uds.sock"
    with uds_file.open("w"):
        pass
    ch = cyberchannel.create_uds_channel(uds_fullpath=uds_file)
    assert ch is not None
    assert ch._channel.target().decode() == f"unix:{uds_file}"
    assert not ch.close()

    ch = cyberchannel.create_uds_channel("service_name")
    assert ch is not None
    assert ch._channel.target().decode() == f"unix:{cyberchannel.determine_uds_folder() / 'service_name.sock'}"
    assert not ch.close()
