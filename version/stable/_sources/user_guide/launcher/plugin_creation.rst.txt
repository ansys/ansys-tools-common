.. _plugin_creation:

Launcher plugin creation
------------------------

This page explains how to create a plugin for the local product launcher. The plugin in the example launches Ansys Composite PrepPost (ACP) as a subprocess.

The local product launcher defines the interface that a plugin must satisfy in the :mod:`.interface` module.

.. note::

    To simplify the example, the plugin business logic is kept minimal.

.. TODO: once merged to main, link to some real plugins in the preceding note.

Create configuration
''''''''''''''''''''

To start, you must create the user-definable configuration for the launcher. Because
ACP should be run as a subprocess, the path to the server binary must be defined.

This configuration is defined as a :py:func:`dataclass <dataclasses.dataclass>`:

.. code:: python

    from dataclasses import dataclass


    @dataclass
    class DirectLauncherConfig:
        binary_path: str

The configuration class defines a single ``binary_path`` option of type :py:class:`str`.

Define launcher
'''''''''''''''

Next, you must define the launcher itself. The full launcher code follows. Because
there's quite a lot going on in this code, descriptions of each part are provided.

.. code:: python

    from typing import Optional
    import subprocess

    from ansys.tools.common.launcher.interface import LauncherProtocol, ServerType
    from ansys.tools.common.launcher.helpers.ports import find_free_ports
    from ansys.tools.common.launcher.helpers.grpc import check_grpc_health


    class DirectLauncher(LauncherProtocol[LauncherConfig]):
        CONFIG_MODEL = DirectLauncherConfig
        SERVER_SPEC = {"main": ServerType.GRPC}

        def __init__(self, *, config: DirectLaunchConfig):
            self._config = config
            self._url: str
            self._process: subprocess.Popen[str]

        def start(self) -> None:
            port = find_free_ports()[0]
            self._url = f"localhost:{port}"
            self._process = subprocess.Popen(
                [
                    self._config.binary_path,
                    f"--server-address=0.0.0.0:{port}",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )

        def stop(self, *, timeout: Optional[float] = None) -> None:
            self._process.terminate()
            try:
                self._process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()

        def check(self, timeout: Optional[float] = None) -> bool:
            channel = grpc.insecure_channel(self.urls[ServerKey.MAIN])
            return check_grpc_health(channel=channel, timeout=timeout)

        @property
        def urls(self) -> dict[str, str]:
            return {"main": self._url}


The launcher class inherits from ``LauncherProtocol[LauncherConfig]``. This isn't a requirement, but it means a type checker like `Mypy <https://mypy.readthedocs.io>`_ can verify that the :class:`.LauncherProtocol` interface is fulfilled.

Next, setting ``CONFIG_MODEL = DirectLauncherConfig`` connects the launcher to the configuration class.

The subsequent line, ``SERVER_SPEC = {"main": ServerType.GRPC}``, defines which kind of servers the
product starts. Here, there's only a single server, which is accessible via gRPC. The keys in this dictionary can be chosen arbitrarily, but they should be consistent across the launcher implementation.
Ideally, use the key to convey some meaning. For example, ``"main"`` could refer to the main interface
to your product and ``file_transfer`` could refer to an additional service for file upload and download.

The ``__init__`` method must accept exactly one keyword-only argument, ``config``, which contains the
configuration instance. In this example, the configuration is stored in the ``_config`` attribute.
For the ``_url`` and ``_process`` attributes, only the type is declared for the benefits of the type checker

.. code:: python

    def __init__(self, *, config: DirectLaunchConfig):
        self._config = config
        self._url: str
        self._process: subprocess.Popen[str]

The core of the launcher implementation is in the ``start`` and ``stop`` methods:

.. code:: python

    def start(self) -> None:
        port = find_free_ports()[0]
        self._url = f"localhost:{port}"
        self._process = subprocess.Popen(
            [
                self._config.binary_path,
                f"--server-address=0.0.0.0:{port}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )

The :meth:`start<.LauncherProtocol.start>` method selects an available port using the
:func:`.find_free_ports` function. It then starts the server as a subprocess. Note that here, the server output is simply discarded. In a real launcher, you should add the option to redirect it (for example to a file).
The ``_url`` attribute keeps track of the URL and port that the server should be accessible on.

The :meth:`start<.LauncherProtocol.stop>` method terminates the subprocess:

.. code:: python

    def stop(self, *, timeout: Optional[float] = None) -> None:
        self._process.terminate()
        try:
            self._process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()

If your product is prone to ignoring ``SIGTERM``, you might want to add a timeout to the
:py:meth:`.wait <subprocess.Popen.wait>` method and retry with the
:py:meth:`.kill <subprocess.Popen.kill>` method instead of the
:py:meth:`.terminate <subprocess.Popen.terminate>` method.

Next, you must provide a way to verify that the product has successfully launched. This is implemented
in the :meth:`check <.LauncherProtocol.check>` method. Because the server implements gRPC health checking, the
:func:`.check_grpc_health` helper can be used for this purpose:

.. code:: python

    def check(self, timeout: Optional[float] = None) -> bool:
        channel = grpc.insecure_channel(self.urls["main"])
        return check_grpc_health(channel=channel, timeout=timeout)


Finally, the ``_url`` attribute stored in the :meth:`start <.LauncherProtocol.start>` method must
be made available in the :attr:`urls <.LauncherProtocol.urls>` property:

.. code:: python

    @property
    def urls(self) -> dict[str, str]:
        return {"main": self._url}

Note that the return value for the ``urls`` property should adhere to the schema defined in ``SERVER_SPEC``.

.. _entrypoint:

Register entrypoint
'''''''''''''''''''

Having defined all the necessary components for a local product launcher plugin, you can now register the
plugin, which makes it available. You do this through the Python `entrypoints mechanism <https://packaging.python.org/specifications/entry-points/>`_.

You define the entrypoint in your package's build configuration. The exact syntax depends on which packaging tool you use:

.. .. grid:: 1
..     :gutter: 3

.. tab-set::

    .. tab-item:: Setuptools

        Setuptools can accept its configuration in one of three ways. Choose the one that applies to your project:

        In a ``pyproject.toml`` file:

        .. code:: toml

            [project.entry-points."ansys.tools.common.launcher"]
            "ACP.direct" = "<your.module.name>:DirectLauncher"

        In a ``setup.cfg`` file:

        .. code:: cfg

            [options.entry_points]
            ansys.tools.common.launcher =
                ACP.direct = <your.module.name>:DirectLauncher

        In a ``setup.py`` file:

        .. code:: python

            from setuptools import setup

            setup(
                # ...,
                entry_points={
                    "ansys.tools.common.launcher": [
                        "ACP.direct = <your.module.name>:DirectLauncher"
                    ]
                }
            )


        For more information, see the `Entry Points for Plugins <https://setuptools.pypa.io/en/latest/userguide/entry_point.html#entry-points-for-plugins>`_ in the Setuptools documentation.

    .. tab-item:: Flit

        In a ``pyproject.toml`` file:

        .. code:: toml

            [project.entry-points."ansys.tools.common.launcher"]
            "ACP.direct" = "<your.module.name>:DirectLauncher"

        For more information, see the `Entry points sections <https://flit.pypa.io/en/stable/pyproject_toml.html#pyproject-project-entrypoints>`_ in the Flit documentation.

    .. tab-item:: Poetry

        In a ``pyproject.toml`` file:

        .. code:: toml

            [tool.poetry.plugins."ansys.tools.common.launcher"]
            "ACP.direct" = "<your.module.name>:DirectLauncher"

        For more information, see the `plugins <https://python-poetry.org/docs/pyproject#plugins>`_ in the Poetry documentation.

In all cases, ``ansys.tools.common.launcher`` is an identifier specifying that the entrypoint defines a local product launcher plugin. It must be kept the same.

The entrypoint itself has two parts:

- The entrypoint name ``ACP.direct`` consists of two parts: ``ACP`` is the product name, and ``direct`` is the launch mode identifier. The name must be of this format and contain exactly one dot ``.`` separating the two parts.
- The entrypoint value ``<your.module.name>:DirectLauncher`` defines where the launcher implementation is located. In other words, it must load the launcher class:

  .. code::

      from <your.module.name> import DirectLauncher


For the entrypoints to update, you must re-install your package (even if it was installed with the ``pip install -e`` command).

Add command-line default and description
''''''''''''''''''''''''''''''''''''''''

With the three preceding parts, you've successfully created a local product launcher plugin. :octicon:`rocket`

You can now improve the usability of the command line by adding a default and a description to the configuration class.

To do so, edit the ``DirectLaunchConfig`` class, using the :py:func:`dataclasses.field` function to enrich
the ``binary_path``:

* The default value is specified as the ``default`` argument.
* The description is given in the ``metadata`` dictionary, using the special key :py:obj:`METADATA_KEY_DOC <.interface.METADATA_KEY_DOC>`.

.. code:: python

    import os
    import dataclasses
    from typing import Union

    from ansys.tools.common.path import get_available_ansys_installations
    from ansys.tools.common.launcher.interface import METADATA_KEY_DOC


    def get_default_binary_path() -> str:
        try:
            installations = get_available_ansys_installations()
            ans_root = installations[max(installations)]
            binary_path = os.path.join(ans_root, "ACP", "acp_grpcserver")
            if os.name == "nt":
                binary_path += ".exe"
            return binary_path
        except (RuntimeError, FileNotFoundError):
            return ""


    @dataclasses.dataclass
    class DirectLaunchConfig:
        binary_path: str = dataclasses.field(
            default=get_default_binary_path(),
            metadata={METADATA_KEY_DOC: "Path to the ACP gRPC server executable."},
        )


For the default value, use the :py:func:`get_available_ansys_installations <path.get_available_ansys_installations>`
helper to find the Ansys installation directory.

Now, when running ``ansys-launcher configure ACP direct``, users can see and accept the default value if they want.

.. note::

    If the default value is ``None``, it is converted to the string ``default`` for command-line interface. This allows implementing more complicated default behaviors that may not be expressible when the command-line interface is run.

Add a fallback launch mode
''''''''''''''''''''''''''

If you want to provide a fallback launch mode that can be used without any configuration, you can add an entrypoint with the special name ``<product>.__fallback__``.

For example, to make ``DirectLauncher`` the fallback for ACP, add this entry point:

.. code:: toml

    [project.entry-points."ansys.tools.common.launcher"]
    "ACP.__fallback__" = "<your.module.name>:DirectLauncher"

The fallback launch mode is used with its default configuration. This means that the configuration class must have default values for all its fields.


Hide advanced options
'''''''''''''''''''''

If your launcher plugin has advanced options, you can skip prompting the user for them by default.
This is done by setting the special key :py:obj:`METADATA_KEY_NOPROMPT <.interface.METADATA_KEY_NOPROMPT>`
to ``True`` in the ``metadata`` dictionary:

.. code:: python

    import dataclasses

    from ansys.tools.common.launcher.interface import METADATA_KEY_NOPROMPT


    @dataclasses.dataclass
    class DirectLaunchConfig:
        # <...>
        environment_variables: dict[str, str] = field(
            default={},
            metadata={
                METADATA_KEY_DOC: "Extra environment variables to define when launching the server.",
                METADATA_KEY_NOPROMPT: True,
            },
        )
