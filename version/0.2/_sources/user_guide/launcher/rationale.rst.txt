.. _rationale:

Rationale
---------

This page explains the problem that the local product launcher solves.

Improvements over the current approach
'''''''''''''''''''''''''''''''''''''''

Currently, many PyAnsys libraries implement a launch function similar to the following:

.. code::

    def launch_myproduct(
        # <many keyword arguments>
    ):
        # Based on the arguments, determine which launch mode to use
        # (subprocess, docker, remote, ...) and launch the product.

While this approach is simple to use, it has some disadvantages:

- The keyword arguments make it difficult to determine how the server is launched.
- You must always pass non-standard launch parameters to the ``launch_myproduct`` function. This makes examples generated on a continuous integration machine non-transferable. Users must replace the launch parameters with those applicable to their setups.
- Each product implements the local launcher separately, introducing accidental differences. This limits code reuse.

The local product launcher improves on the current approach in the following ways:

- The ``launch_mode`` function is passed as an explicit argument, and all other configuration is collected into a single object. The available configuration options explicitly depend on the launch mode.
- By default, the local product launcher separates **configuration** from the **launching code**. However, this separation is optional to support cases where multiple different configurations must be available at runtime. You can still pass the full configuration to the launching code.
- The local product launcher provides a common interface for implementing the launching task and handles common tasks, such as ensuring that the product closes when the Python process exits. It does not attempt to remove the inherent differences between launching different products. Each specific PyAnsys library retains control over the launch through a plugin system.

Potential pitfalls
''''''''''''''''''

As with any standardization effort, there are potential pitfalls:

.. only:: html

   .. image:: https://imgs.xkcd.com/comics/standards.png
      :alt: Standards (xkcd comic)

.. only:: latex

   See https://xkcd.com/927/

Future improvements
''''''''''''''''''''

Here are some ideas for how the local product launcher could evolve:

* Add a server or daemon component that can be controlled:

  * Via the PIM API
  * From the command line

* Extend the ``helpers`` module to further simplify implementing launcher plugins.

* Implement launcher plugins separately from the product PyAnsys libraries. For example, you could create a ``docker-compose`` setup where all launched products share a mounted volume.
