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

"""
Certificate generation utilities for gRPC mutual TLS testing.

This module provides utilities for generating self-signed certificates suitable
for testing gRPC applications with mutual TLS authentication, including support
for HPC deployments with multiple servers.

Examples
--------
Generate certificates for a single server:

>>> from ansys.tools.common.utils import generate_test_certificates
>>> files = generate_test_certificates(output_dir="certs")

Generate certificates for multiple servers (HPC deployment):

>>> files = generate_test_certificates(servers=["node01,192.0.2.1", "node02,192.0.2.2"], output_dir="certs")

Use in pytest fixtures:

>>> import pytest
>>> from pathlib import Path
>>> from ansys.tools.common.utils import generate_test_certificates
>>>
>>> @pytest.fixture(scope="session")
... def tls_certificates(tmp_path_factory):
...     cert_dir = tmp_path_factory.mktemp("certs")
...     files = generate_test_certificates(output_dir=cert_dir)
...     return {
...         "ca_cert": cert_dir / "ca.crt",
...         "server_cert": cert_dir / "server.crt",
...         "server_key": cert_dir / "server.key",
...         "client_cert": cert_dir / "client.crt",
...         "client_key": cert_dir / "client.key",
...     }
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

    __CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    __CRYPTOGRAPHY_AVAILABLE = False


class CertificateGenerator:
    """
    Certificate generator for creating self-signed certificates for testing.

    This class encapsulates all the logic needed to generate a complete PKI
    setup including CA, server, and client certificates.

    Parameters
    ----------
    key_size : int, optional
        Size of the RSA keys in bits, by default 4096
    validity_days : int, optional
        Number of days the certificates should be valid, by default 1 (24 hours)

    Examples
    --------
    >>> from ansys.tools.common.utils.certificates import CertificateGenerator
    >>> gen = CertificateGenerator(validity_days=365)
    >>> ca_key, ca_cert = gen.create_ca_certificate()
    >>> server_key, server_cert = gen.create_server_certificate(ca_cert, ca_key, "localhost")
    """

    def __init__(self, key_size: int = 4096, validity_days: int = 1):
        """Initialize the certificate generator."""
        if not __CRYPTOGRAPHY_AVAILABLE:
            raise ImportError(
                "The 'cryptography' library is required for certificate generation. "
                "Install it with: pip install ansys-tools-common[other]"
            )
        self.key_size = key_size
        self.validity_days = validity_days

    def generate_private_key(self) -> rsa.RSAPrivateKey:
        """
        Generate an RSA private key.

        Returns
        -------
        rsa.RSAPrivateKey
            Generated RSA private key
        """
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size,
        )

    @staticmethod
    def save_private_key(key: rsa.RSAPrivateKey, filename: Path) -> None:
        """
        Save a private key to a PEM file.

        Parameters
        ----------
        key : rsa.RSAPrivateKey
            The private key to save
        filename : Path
            Path to the output file
        """
        with filename.open("wb") as f:
            f.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

    @staticmethod
    def save_certificate(cert: x509.Certificate, filename: Path) -> None:
        """
        Save a certificate to a PEM file.

        Parameters
        ----------
        cert : x509.Certificate
            The certificate to save
        filename : Path
            Path to the output file
        """
        with filename.open("wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

    def create_ca_certificate(self, common_name: str = "Test CA") -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
        """
        Create a self-signed CA certificate.

        Parameters
        ----------
        common_name : str, optional
            Common name for the CA certificate, by default "Test CA"

        Returns
        -------
        tuple[rsa.RSAPrivateKey, x509.Certificate]
            Tuple containing (ca_key, ca_cert)
        """
        ca_key = self.generate_private_key()

        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=self.validity_days))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_cert_sign=True,
                    crl_sign=True,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    content_commitment=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(ca_key, hashes.SHA256())
        )

        return ca_key, cert

    def create_server_certificate(
        self,
        ca_cert: x509.Certificate,
        ca_key: rsa.RSAPrivateKey,
        server_common_name: str,
        san_names: Optional[list[str]] = None,
    ) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
        """
        Create a server certificate signed by the CA with optional Subject Alternative Names.

        Parameters
        ----------
        ca_cert : x509.Certificate
            The CA certificate to use as issuer
        ca_key : rsa.RSAPrivateKey
            The CA private key to sign the certificate
        server_common_name : str
            The common name for the server certificate (will be used as CN and primary SAN)
        san_names : list[str], optional
            Additional Subject Alternative Names to include, by default None

        Returns
        -------
        tuple[rsa.RSAPrivateKey, x509.Certificate]
            Tuple containing (server_key, server_cert)
        """
        server_key = self.generate_private_key()

        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, server_common_name)])

        # Build SAN list - always include the CN, plus any additional names
        san_list = [x509.DNSName(server_common_name)]
        if san_names:
            for name in san_names:
                # Skip if it's the same as CN to avoid duplicates
                if name != server_common_name:
                    san_list.append(x509.DNSName(name))

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_cert.subject)
            .public_key(server_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=self.validity_days))
            .add_extension(
                x509.SubjectAlternativeName(san_list),
                critical=False,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_cert_sign=False,
                    crl_sign=False,
                    data_encipherment=False,
                    key_agreement=False,
                    content_commitment=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
                critical=False,
            )
            .sign(ca_key, hashes.SHA256())
        )

        return server_key, cert

    def create_client_certificate(
        self,
        ca_cert: x509.Certificate,
        ca_key: rsa.RSAPrivateKey,
        client_common_name: str,
    ) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
        """
        Create a client certificate signed by the CA.

        Parameters
        ----------
        ca_cert : x509.Certificate
            The CA certificate to use as issuer
        ca_key : rsa.RSAPrivateKey
            The CA private key to sign the certificate
        client_common_name : str
            The common name for the client certificate

        Returns
        -------
        tuple[rsa.RSAPrivateKey, x509.Certificate]
            Tuple containing (client_key, client_cert)
        """
        client_key = self.generate_private_key()

        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, client_common_name)])

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_cert.subject)
            .public_key(client_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=self.validity_days))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(client_common_name)]),
                critical=False,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_cert_sign=False,
                    crl_sign=False,
                    data_encipherment=False,
                    key_agreement=False,
                    content_commitment=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),
                critical=False,
            )
            .sign(ca_key, hashes.SHA256())
        )

        return client_key, cert


def parse_server_spec(server_spec: str) -> tuple[str, list[str]]:
    """
    Parse a server specification string into primary hostname and SAN list.

    Parameters
    ----------
    server_spec : str
        A comma-separated string like "node01,192.0.2.1" or just "node01"

    Returns
    -------
    tuple[str, list[str]]
        Tuple containing (primary_hostname, [additional_san_names])

    Raises
    ------
    ValueError
        If the server specification is empty or invalid
    """
    names = [name.strip() for name in server_spec.split(",") if name.strip()]
    if not names:
        raise ValueError("Server specification cannot be empty")

    primary_hostname = names[0]
    additional_sans = names[1:] if len(names) > 1 else []

    return primary_hostname, additional_sans


def generate_test_certificates(
    servers: Optional[list[str]] = None,
    client_name: str = "Test Client",
    validity_days: int = 1,
    output_dir: Optional[Path] = None,
    key_size: int = 4096,
) -> list[Path]:
    """
    Generate a complete set of test certificates for gRPC mutual TLS.

    This is a convenience function that generates all necessary certificates
    (CA, server(s), and client) and saves them to the specified directory.
    Perfect for pytest fixtures and test setup.

    Parameters
    ----------
    servers : list[str], optional
        List of server specifications in format "hostname[,san1,san2,...]".
        If None, defaults to ["localhost,127.0.0.1"]
    client_name : str, optional
        Common name for the client certificate, by default "Test Client"
    validity_days : int, optional
        Number of days the certificates should be valid, by default 1 (24 hours)
    output_dir : Path, optional
        Output directory for certificates. If None, uses current directory.
    key_size : int, optional
        Size of the RSA keys in bits, by default 4096

    Returns
    -------
    list[Path]
        List of paths to all generated certificate files

    Examples
    --------
    Basic usage:

    >>> from ansys.tools.common.utils import generate_test_certificates
    >>> files = generate_test_certificates(output_dir=Path("certs"))
    >>> print(files)
    [Path('certs/ca.key'), Path('certs/ca.crt'), ...]

    HPC deployment with multiple servers:

    >>> files = generate_test_certificates(servers=["node01,192.0.2.1", "node02,192.0.2.2"], output_dir=Path("certs"))

    Use in pytest:

    >>> @pytest.fixture(scope="session")
    ... def tls_certs(tmp_path_factory):
    ...     cert_dir = tmp_path_factory.mktemp("certs")
    ...     generate_test_certificates(output_dir=cert_dir)
    ...     return cert_dir
    """
    if not __CRYPTOGRAPHY_AVAILABLE:
        raise ImportError(
            "The 'cryptography' library is required for certificate generation. "
            "Install it with: pip install ansys-tools-common[other]"
        )

    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)

    if servers is None:
        servers = ["localhost,127.0.0.1"]

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = CertificateGenerator(key_size=key_size, validity_days=validity_days)
    generated_files = []

    # Generate CA certificate
    ca_key, ca_cert = generator.create_ca_certificate()
    ca_key_path = output_dir / "ca.key"
    ca_cert_path = output_dir / "ca.crt"
    generator.save_private_key(ca_key, ca_key_path)
    generator.save_certificate(ca_cert, ca_cert_path)
    generated_files.extend([ca_key_path, ca_cert_path])

    # Generate server certificates
    for server_spec in servers:
        primary_hostname, additional_sans = parse_server_spec(server_spec)

        # If only one server is specified, use 'server' as generic name
        if len(servers) == 1:
            filename = "server"
        else:
            filename = primary_hostname

        server_key, server_cert = generator.create_server_certificate(
            ca_cert, ca_key, primary_hostname, additional_sans
        )

        key_path = output_dir / f"{filename}.key"
        cert_path = output_dir / f"{filename}.crt"
        generator.save_private_key(server_key, key_path)
        generator.save_certificate(server_cert, cert_path)
        generated_files.extend([key_path, cert_path])

    # Generate client certificate
    client_key, client_cert = generator.create_client_certificate(ca_cert, ca_key, client_name)
    client_key_path = output_dir / "client.key"
    client_cert_path = output_dir / "client.crt"
    generator.save_private_key(client_key, client_key_path)
    generator.save_certificate(client_cert, client_cert_path)
    generated_files.extend([client_key_path, client_cert_path])

    return generated_files
