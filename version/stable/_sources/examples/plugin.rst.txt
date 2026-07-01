Define the HTTP server launcher plugin
--------------------------------------

This example shows the launcher plugin that is used to start the Python HTTP server.
The full source is available in the `examples/local_launcher/example_httpserver_plugin directory <https://github.com/ansys/ansys-tools-common/tree/main/examples/local_launcher/example_httpserver_plugin>`_
on GitHub.

While this example explains some aspects of the code, for information on how
to create a plugin for the Local Product Launcher, see :ref:`plugin_creation`.

Launcher code
~~~~~~~~~~~~~

The ``LauncherConfig`` class determines which options are available to the user when configuring the launcher. It exposes
a single option ``directory``, which determines which directory the server is to serve files from.

.. include:: ../../../examples/local_launcher/example_httpserver_plugin/src/example_httpserver_plugin/launcher.py
    :literal:
    :start-after: # START_LAUNCHER_CONFIG
    :end-before: # END_LAUNCHER_CONFIG


The ``Launcher`` class actually starts the server. It needs to fulfill the interface defined by the
:class:`.LauncherProtocol` class. Namely, this interface consists of these endpoints:

- The ``start`` and ``stop`` methods for starting and stopping the server.
- The ``check`` method for checking if the server is running.
- The ``urls`` property for getting the URLs that the the server is serving requests on.

.. include:: ../../../examples/local_launcher/example_httpserver_plugin/src/example_httpserver_plugin/launcher.py
    :literal:
    :start-after: # START_LAUNCHER_CLS
    :end-before: # END_LAUNCHER_CLS

The local product launcher uses this minimal interface to construct a :class:`.ProductInstance` class,
which adds some additional functionality on top. For example, the ``ProductInstance`` class automatically
stops the server when the Python process terminates.


Entrypoint configuration
~~~~~~~~~~~~~~~~~~~~~~~~

Besides the launcher code, the plugin must be registered by adding an entrypoint to
the ``pyproject.toml`` file, as described in :ref:`entrypoint`. In this example,
``flit`` is used as a build tool. Thus, the ``pyproject.toml`` file looks like this:

.. include:: ../../../examples/local_launcher/example_httpserver_plugin/pyproject.toml
    :literal:

Two entrypoints for the local product launcher are defined:

- ``direct``: A launch mode that users can configure.
- ``__fallback__``: A fallback mode that is used if no configuration is available.

Both entrypoints use the same launcher class.
