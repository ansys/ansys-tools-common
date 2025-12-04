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
"""Module for test server."""

from concurrent import futures
import pathlib
import sys

import grpc
from grpc_health.v1 import health, health_pb2_grpc


def main(uds_dir: str):
    """Run the simple test server."""
    uds_file = pathlib.Path(uds_dir) / "simple_test_service.sock"
    if uds_file.exists():
        print(f"UDS file {uds_file} already exists.")
        sys.exit(1)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    health_pb2_grpc.add_HealthServicer_to_server(health.HealthServicer(), server)
    server.add_insecure_port(f"unix:{uds_file}")
    print(f"Starting gRPC server with UDS file {uds_file}...")
    try:
        server.start()
        server.wait_for_termination()
    finally:
        print("Shutting down gRPC server...")
        uds_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main(sys.argv[1])
