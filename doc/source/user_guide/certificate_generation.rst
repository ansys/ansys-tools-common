.. _ref_certificate_generation:

Certificate generation utilities
################################

The certificate generation utilities provide a convenient way to generate
self-signed certificates suitable for testing gRPC applications with mutual TLS
authentication. These utilities are particularly useful for pytest fixtures and
local development environments.

.. important::
   These certificates are for **testing purposes only**. Do not use them in
   production environments. For production deployments, always use certificates
   from a trusted Certificate Authority.

.. note::
   By default, generated certificates are valid for only 24 hours. This short
   validity period is intentional for testing environments to encourage
   certificate regeneration and avoid stale credentials. You can customize
   this using the ``validity_days`` parameter if needed.

Installation
============

Install Ansys Common Tools with the ``other`` optional dependency group to
enable certificate generation:

.. tab-set::

    .. tab-item:: pip

        .. code-block:: bash

            pip install ansys-tools-common[other]

    .. tab-item:: uv

        .. code-block:: bash

            uv sync --extra other

Quick start
===========

The simplest way to generate certificates is using the
:func:`generate_test_certificates() <ansys.tools.common.utils.generate_test_certificates>`
function:

.. code-block:: python

    from ansys.tools.common.utils import generate_test_certificates
    from pathlib import Path

    # Generate certificates for localhost
    files = generate_test_certificates(output_dir=Path("certs"))

    # The following files are created:
    # - ca.key, ca.crt (Certificate Authority)
    # - server.key, server.crt (Server certificate)
    # - client.key, client.crt (Client certificate)

Pytest integration
==================

The utilities are designed to integrate seamlessly with pytest fixtures,
making it easy to set up secure testing environments:

Basic fixture
-------------

.. code-block:: python

    import pytest
    from pathlib import Path
    from ansys.tools.common.utils import generate_test_certificates


    @pytest.fixture(scope="session")
    def tls_certificates(tmp_path_factory):
        """Generate TLS certificates for testing."""
        cert_dir = tmp_path_factory.mktemp("certs")
        generate_test_certificates(output_dir=cert_dir)

        return {
            "ca_cert": cert_dir / "ca.crt",
            "ca_key": cert_dir / "ca.key",
            "server_cert": cert_dir / "server.crt",
            "server_key": cert_dir / "server.key",
            "client_cert": cert_dir / "client.crt",
            "client_key": cert_dir / "client.key",
        }


    def test_grpc_with_mtls(tls_certificates):
        """Test gRPC server with mutual TLS."""
        # Use the certificates in your test
        server_cert = tls_certificates["server_cert"]
        server_key = tls_certificates["server_key"]
        ca_cert = tls_certificates["ca_cert"]

        # Set up your gRPC server with these certificates
        # ...

Advanced usage
==============

HPC deployment with multiple servers
-------------------------------------

For HPC environments where you need certificates for multiple nodes:

.. code-block:: python

    from ansys.tools.common.utils import generate_test_certificates
    from pathlib import Path

    files = generate_test_certificates(
        servers=[
            "node01,192.0.2.1",  # Primary hostname + IP SAN
            "node02,192.0.2.2",
            "node03,192.0.2.3",
        ],
        output_dir=Path("hpc_certs"),
    )

    # This creates:
    # - ca.key, ca.crt
    # - node01.key, node01.crt (with SAN: 192.0.2.1)
    # - node02.key, node02.crt (with SAN: 192.0.2.2)
    # - node03.key, node03.crt (with SAN: 192.0.2.3)
    # - client.key, client.crt

HPC fixture example
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import pytest
    from pathlib import Path
    from ansys.tools.common.utils import generate_test_certificates


    @pytest.fixture(scope="session")
    def hpc_tls_certificates(tmp_path_factory):
        """Generate TLS certificates for HPC deployment."""
        cert_dir = tmp_path_factory.mktemp("hpc_certs")
        server_specs = [
            "node01,192.0.2.1",
            "node02,192.0.2.2",
            "node03,192.0.2.3",
        ]

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

Custom validity period
----------------------

By default, certificates are valid for 24 hours (1 day). This short validity
period is intentional for testing to ensure certificates are regenerated
frequently. You can customize this if needed:

.. code-block:: python

    from ansys.tools.common.utils import generate_test_certificates
    from pathlib import Path

    # Generate certificates valid for 1 year
    files = generate_test_certificates(output_dir=Path("certs"), validity_days=365)

Using the ``CertificateGenerator`` class
----------------------------------------

For more control over certificate generation, use the
:class:`CertificateGenerator <ansys.tools.common.utils.CertificateGenerator>`
class directly:

.. code-block:: python

    from ansys.tools.common.utils import CertificateGenerator
    from pathlib import Path

    # Initialize generator with custom parameters
    generator = CertificateGenerator(key_size=4096, validity_days=365)

    # Generate CA certificate
    ca_key, ca_cert = generator.create_ca_certificate("My Test CA")

    # Generate server certificate with SANs
    server_key, server_cert = generator.create_server_certificate(
        ca_cert, ca_key, "myserver.local", san_names=["192.168.1.100", "myserver"]
    )

    # Generate client certificate
    client_key, client_cert = generator.create_client_certificate(
        ca_cert, ca_key, "Test Client"
    )

    # Save certificates
    output_dir = Path("custom_certs")
    output_dir.mkdir(exist_ok=True)

    generator.save_private_key(server_key, output_dir / "server.key")
    generator.save_certificate(server_cert, output_dir / "server.crt")
    # ... save other certificates

Security considerations
=======================

The generated certificates have the following characteristics:

- **Self-signed:** Not validated by any certificate authority
- **Predictable parameters:** Generated with standard key sizes and algorithms
- **No revocation support:** No certificate revocation lists (CRLs) or OCSP
- **Testing only:** Intended only for local development and testing

For production deployments:

- Use certificates from a trusted Certificate Authority (CA)
- Implement proper certificate rotation and expiration policies
- Use hardware security modules (HSMs) for key management when appropriate
- Follow your organization's security policies and compliance requirements

Use cases
=========

Common use cases for these certificate utilities include:

- **Unit and integration tests:** Set up secure gRPC connections in test suites
- **Local development:** Test TLS-enabled features without external dependencies
- **CI/CD pipelines:** Generate ephemeral certificates for test environments
- **HPC testing:** Simulate multi-node secure communication
- **Documentation examples:** Provide working security examples without sharing real credentials

Related topics
==============

- :doc:`secure_grpc` - Learn about securing gRPC connections in PyAnsys
- :ref:`ref_user_guide` - Return to the user guide index
