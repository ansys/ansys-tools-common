Securing gRPC connections
#########################

The PyAnsys ecosystem enables now various transport modes for securing gRPC connections.
This page reviews the available transport modes, and how to use them.

Supported transport modes
=========================

PyAnsys supports the following transport modes for gRPC connections:

- **Mutual TLS (mTLS).** This mode allows secure connections using TLS
  encryption and client/server certificates. It is recommended for production
  use, especially when transmitting sensitive data. Works both locally and over
  the network.

- **Unix Domain Sockets (UDS).** This mode allows connections over a local
  socket file. UDS is only supported for local inter-process communication
  (IPC) on a machine running Linux.

- **Windows Named User Authentication (WNUA).** This mode allows secure local
  connections on Windows machines through user authentication. It is only
  supported in Windows.

- **Insecure.** This mode allows connections without any encryption or
  authentication. It is NOT recommended for production use, but can be useful
  for testing or development purposes.


The ``cyberchannel`` module
============================

The ``cyberchannel`` module eases the transition to secure gRPC. It is meant to
be used by client applications to create gRPC channels with the server.

This module implements all transport modes described above. It also abstracts
away the details of connection setup and certificate handling, making it easier
to connect clients to gRPC servers in different environments.

Example usage
-------------

.. code-block:: python

    from cyberchannel import create_channel
    import hello_pb2_grpc

    channel = create_channel(
        host="localhost", port=50051,                               # Channel details
        transport_mode="mtls", certs_dir="path/to/certs",           # Security details
        grpc_options=[                                              # Extra details
            ('grpc.max_receive_message_length', 50 * 1024 * 1024)
        ],
    )
    stub = hello_pb2_grpc.GreeterStub(channel)

API reference
-------------

.. list-table::
    :header-rows: 1
    :widths: 20 80

    * - Function
      - Description
    * - ``create_channel(...)``
      - Main entry point for users.
    * - ``verify_transport_mode(...)``
      - Check if selected transport mode is valid. If not, it raises an error.
    * - ``verify_uds_socket(...)``
      - Check if UDS socket file exists.

Environment variables
---------------------

.. list-table::
   :header-rows: 1
   :widths: 20 60 20

   * - Variable
     - Description
     - Default
   * - ``ANSYS_GRPC_CERTIFICATES``
     - Path to folder containing ``ca.crt``, ``client.crt``, and ``client.key``
       for mTLS connections. If not set, defaults to a local ``./certs``
       directory.
     - ``./certs``

Generating certificates for mTLS
================================

`OpenSSL <https://www.openssl.org/>`__ can be used to generate the necessary
certificates for mTLS. The following files are required for both the server and
the client:

=====  =======================  =========================================
Side   Required Files           Purpose
=====  =======================  =========================================
Server server.crt               Server identity
       server.key               Server private key
       ca.crt                   To verify client certificates
Client client.crt               Client identity
       client.key               Client private key
       ca.crt                   To verify server certificates
=====  =======================  =========================================

These files can be generated using `OpenSSL <https://www.openssl.org/>`__.

Generate a certificate authority
--------------------------------

.. code-block:: bash

    # Generate private key for CA
    openssl genrsa -out ca.key 4096

    # Generate self-signed CA certificate
    openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out ca.crt \
        -subj "/CN=MyRootCA"

Generate the server certificate
-------------------------------

.. code-block:: bash

    # Generate server private key
    openssl genrsa -out server.key 4096

    # Generate a certificate signing request (CSR) for the server
    openssl req -new -key server.key -out server.csr \
        -subj "/CN=localhost"

    # Generate server certificate signed by the CA
    openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
        -out server.crt -days 365 -sha256

Generate the client certificate
-------------------------------

.. code-block:: bash

    # Generate client private key
    openssl genrsa -out client.key 4096

    # Generate a certificate signing request (CSR) for the client
    openssl req -new -key client.key -out client.csr \
        -subj "/CN=grpc-client"

    # Generate client certificate signed by the CA
    openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
        -out client.crt -days 365 -sha256

Verify certificates
-------------------

.. code-block:: bash

    # Verify server certificate
    openssl verify -CAfile ca.crt server.crt

    # Verify client certificate
    openssl verify -CAfile ca.crt client.crt
