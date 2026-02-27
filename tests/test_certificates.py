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

"""Tests for the certificate generation utilities."""

import pytest


def test_certificates_import():
    """Test that certificate utilities can be imported."""
    try:
        from ansys.tools.common.utils import CertificateGenerator, generate_test_certificates

        assert CertificateGenerator is not None
        assert generate_test_certificates is not None
    except ImportError as e:
        pytest.skip(f"cryptography not available: {e}")


def test_generate_test_certificates_basic(tmp_path):
    """Test basic certificate generation."""
    try:
        from ansys.tools.common.utils import generate_test_certificates
    except ImportError:
        pytest.skip("cryptography not available")

    # Generate certificates in a temporary directory
    cert_dir = tmp_path / "certs"
    files = generate_test_certificates(output_dir=cert_dir)

    # Verify all expected files were created
    expected_files = ["ca.key", "ca.crt", "server.key", "server.crt", "client.key", "client.crt"]

    assert len(files) == len(expected_files)

    for expected_file in expected_files:
        file_path = cert_dir / expected_file
        assert file_path.exists(), f"Expected file {expected_file} was not created"
        assert file_path.stat().st_size > 0, f"File {expected_file} is empty"


def test_generate_test_certificates_multiple_servers(tmp_path):
    """Test certificate generation with multiple servers."""
    try:
        from ansys.tools.common.utils import generate_test_certificates
    except ImportError:
        pytest.skip("cryptography not available")

    cert_dir = tmp_path / "certs"
    generate_test_certificates(
        servers=["node01,192.0.2.1", "node02,192.0.2.2", "node03"],
        output_dir=cert_dir,
    )

    # Verify CA and client files exist
    assert (cert_dir / "ca.key").exists()
    assert (cert_dir / "ca.crt").exists()
    assert (cert_dir / "client.key").exists()
    assert (cert_dir / "client.crt").exists()

    # Verify server-specific files exist
    for server_name in ["node01", "node02", "node03"]:
        assert (cert_dir / f"{server_name}.key").exists()
        assert (cert_dir / f"{server_name}.crt").exists()


def test_generate_test_certificates_custom_validity(tmp_path):
    """Test certificate generation with custom validity period."""
    try:
        from ansys.tools.common.utils import generate_test_certificates
    except ImportError:
        pytest.skip("cryptography not available")

    cert_dir = tmp_path / "certs"
    files = generate_test_certificates(output_dir=cert_dir, validity_days=365)

    # Just verify files were created - we can't easily test validity without parsing certs
    assert len(files) == 6
    assert all(f.exists() for f in files)


def test_default_validity_is_24_hours(tmp_path):
    """Test that default certificate validity is 24 hours (1 day)."""
    try:
        from ansys.tools.common.utils import CertificateGenerator
    except ImportError:
        pytest.skip("cryptography not available")

    # Test default value
    generator = CertificateGenerator()
    assert generator.validity_days == 1, "Default validity should be 1 day (24 hours)"

    # Verify it can still be customized
    custom_generator = CertificateGenerator(validity_days=365)
    assert custom_generator.validity_days == 365


def test_certificate_generator_class(tmp_path):
    """Test the CertificateGenerator class directly."""
    try:
        from ansys.tools.common.utils import CertificateGenerator
    except ImportError:
        pytest.skip("cryptography not available")

    generator = CertificateGenerator(key_size=2048, validity_days=365)

    # Generate CA certificate
    ca_key, ca_cert = generator.create_ca_certificate()
    assert ca_key is not None
    assert ca_cert is not None

    # Generate server certificate
    server_key, server_cert = generator.create_server_certificate(ca_cert, ca_key, "test-server.local")
    assert server_key is not None
    assert server_cert is not None

    # Generate client certificate
    client_key, client_cert = generator.create_client_certificate(ca_cert, ca_key, "test-client")
    assert client_key is not None
    assert client_cert is not None


def test_parse_server_spec():
    """Test the parse_server_spec function."""
    try:
        from ansys.tools.common.utils.certificates import parse_server_spec
    except ImportError:
        pytest.skip("cryptography not available")

    # Single hostname
    hostname, sans = parse_server_spec("localhost")
    assert hostname == "localhost"
    assert sans == []

    # Hostname with SANs
    hostname, sans = parse_server_spec("node01,192.0.2.1,node01.local")
    assert hostname == "node01"
    assert sans == ["192.0.2.1", "node01.local"]

    # Test with spaces
    hostname, sans = parse_server_spec("node01, 192.0.2.1, node01.local")
    assert hostname == "node01"
    assert sans == ["192.0.2.1", "node01.local"]

    # Test empty spec
    with pytest.raises(ValueError, match="Server specification cannot be empty"):
        parse_server_spec("")


@pytest.fixture(scope="session")
def tls_certificates(tmp_path_factory):
    """
    Pytest fixture example: Generate TLS certificates for testing.

    This fixture generates a complete set of certificates once per test session
    and returns a dictionary with paths to all certificate files.

    Returns
    -------
    dict
        Dictionary containing paths to all certificate files

    Examples
    --------
    >>> def test_grpc_server(tls_certificates):
    ...     server_cert = tls_certificates["server_cert"]
    ...     server_key = tls_certificates["server_key"]
    ...     ca_cert = tls_certificates["ca_cert"]
    ...     # Use certificates to set up gRPC server...
    """
    try:
        from ansys.tools.common.utils import generate_test_certificates
    except ImportError:
        pytest.skip("cryptography not available")

    cert_dir = tmp_path_factory.mktemp("certs")
    generate_test_certificates(output_dir=cert_dir)

    return {
        "ca_cert": cert_dir / "ca.crt",
        "ca_key": cert_dir / "ca.key",
        "server_cert": cert_dir / "server.crt",
        "server_key": cert_dir / "server.key",
        "client_cert": cert_dir / "client.crt",
        "client_key": cert_dir / "client.key",
        "cert_dir": cert_dir,
    }


@pytest.fixture(scope="session")
def hpc_tls_certificates(tmp_path_factory):
    """
    Pytest fixture example: Generate TLS certificates for HPC deployment.

    This fixture demonstrates how to generate certificates for multiple servers
    in an HPC environment.

    Returns
    -------
    dict
        Dictionary containing paths to all certificate files including multiple servers

    Examples
    --------
    >>> def test_hpc_cluster(hpc_tls_certificates):
    ...     ca_cert = hpc_tls_certificates["ca_cert"]
    ...     node01_cert = hpc_tls_certificates["servers"]["node01"]["cert"]
    ...     # Use certificates to set up HPC cluster...
    """
    try:
        from ansys.tools.common.utils import generate_test_certificates
    except ImportError:
        pytest.skip("cryptography not available")

    cert_dir = tmp_path_factory.mktemp("hpc_certs")
    server_specs = ["node01,192.0.2.1", "node02,192.0.2.2", "node03,192.0.2.3"]

    generate_test_certificates(servers=server_specs, output_dir=cert_dir)

    result = {
        "ca_cert": cert_dir / "ca.crt",
        "ca_key": cert_dir / "ca.key",
        "client_cert": cert_dir / "client.crt",
        "client_key": cert_dir / "client.key",
        "cert_dir": cert_dir,
        "servers": {},
    }

    # Add server-specific certificates
    for spec in server_specs:
        server_name = spec.split(",")[0]
        result["servers"][server_name] = {
            "cert": cert_dir / f"{server_name}.crt",
            "key": cert_dir / f"{server_name}.key",
        }

    return result
