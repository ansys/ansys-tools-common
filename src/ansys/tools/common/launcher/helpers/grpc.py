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

"""Helpers for interacting with gRPC servers."""

import grpc  # type: ignore[import-untyped]
from grpc_health.v1.health_pb2 import HealthCheckRequest, HealthCheckResponse  # type: ignore[import-untyped]
from grpc_health.v1.health_pb2_grpc import HealthStub  # type: ignore[import-untyped]


def check_grpc_health(channel: grpc.Channel, timeout: float | None = None) -> bool:
    """Check that a gRPC server is responding to health check requests.

    Parameters
    ----------
    channel :
        Channel to the gRPC server.
    timeout :
        Timeout in seconds for the gRPC health check request.

    Returns
    -------
    bool
        ``True`` if the health check succeeds, ``False`` otherwise.
    """
    try:
        res = HealthStub(channel).Check(
            request=HealthCheckRequest(),
            timeout=timeout,
        )
        if res.status == HealthCheckResponse.ServingStatus.SERVING:
            return True
    except grpc.RpcError:
        pass
    return False
