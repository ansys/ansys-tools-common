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

"""Helpers for managing port assignment."""

from contextlib import ExitStack, closing
import socket


def find_free_ports(num_ports: int = 1) -> list[int]:
    """Find free ports on the localhost.

    .. note::

        Because there is no way to reserve a port that would still allow
        a server to connect to it, there is no guarantee that the ports
        are *still* free when eventually used.

    Parameters
    ----------
    num_ports :
        Number of free ports to obtain.
    """
    port_list = []
    with ExitStack() as context_stack:
        for _ in range(num_ports):
            sock = context_stack.enter_context(closing(socket.socket()))
            sock.bind(("", 0))
            port_list.append(sock.getsockname()[1])
    return port_list
