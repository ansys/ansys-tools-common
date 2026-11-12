.. _rationale:

Rationale
---------
This page provides a high-level overview of the problem that the
Local Product Launcher solves.

Improvements over the status quo
''''''''''''''''''''''''''''''''

Currently, many PyAnsys libraries implement a launch function, which looks
something like this:

.. code::

    def launch_myproduct(
        # <many keyword arguments>
    ):
        # based on the arguments, figure out which launch mode should
        # be used (sub-process, docker, remote, ...)
        # and launch the product.

While this approach is reasonably simple to use, it has some disadvantages:

- It can be difficult to tell from the keyword arguments how the server is launched.
- Non-standard launch parameters must *always* be passed along to the ``launch_myproduct()``
  method. This makes examples that are generated on a continuous integration machine
  non-tranferable. Users must replace the launch parameters with what is applicable to
  their setups.
- Each product implements the local launcher separately, with some accidental differences.
  This limits code reuse.

Here's how the Local Product Launcher improves on the status quo:

- The ``launch_mode()`` method is passed as an explicit argument, and all other configuration
  is collected into a single object. The available configuration options **explicitly** depend
  on the launch mode.
- The Local Product Launcher separates **configuration** from the **launching code** by default.
  To still enable cases where multiple *different* configurations must be available at run time,
  this separation is **optional**. The full configuration can still be passed to the launching code.
- The Local Product Launcher provides a common interface for implementing the launching task
  and handles common tasks like ensuring that the product is closed when the Python process exits.

   It doesn't attempt to remove the *inherent* differences between launching different products.
   Ultimately, control over the launch is with each specific PyAnsys library through a plugin
   system.


Potential pitfalls
''''''''''''''''''

As with any attempt to standardize, there are potential pitfalls:

.. only:: html

   .. image:: https://imgs.xkcd.com/comics/standards.png
      :alt: Standards (xkcd comic)


.. only:: latex

   See https://xkcd.com/927/


Future avenues
''''''''''''''

Here are some ideas for how the Local Product Launcher could evolve:

* Add a server/daemon component that can be controlled:

  * Via the PIM API
  * From the command line

* Extend the ``helpers`` module to further ease implementing launcher plugins.

* Implement launcher plugins separate from the product PyAnsys libraries. For
  example, a ``docker-compose`` setup where all launched products share a mounted
  volume is possible.
