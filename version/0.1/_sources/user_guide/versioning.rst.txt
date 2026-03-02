.. ref_versioning:

User guide
==========

The fundamental object provided by ``ansys.tools.versioning`` is a decorator
named :meth:`ansys.tools.versioning.requires_version` which accepts:

* The required version as a string ``"<Major>.<Minor>.<Patch>"`` or tuple
  ``(<Major>, <Minor>, <Patch>)``.

* A version map in the form of dictionary relating the required version and its
  Ansys unified install, ``VERSION_MAP = {(<Major>, <Minor>, <Patch>): "2022R1"}``


How to use
----------
The ``requires_version`` decorator is expected to be used in all the desired
methods of a class containing a ``_server_version`` attribute. If the class in
which it is used does not contain this attribute, an ``AttributeError`` is
raised.

As an example, consider the following code declaring a generic ``Server`` class
and a ``VERSION_MAP`` dictionary


.. code-block:: python

    VERSION_MAP = {
        (0, 2, 3): "2021R1",
        (0, 4, 5): "2021R2",
        (0, 5, 1): "2022R1",
    }


    class Server:
        """A basic class for modelling a server."""

        def __init__(self, version):
            """Initializes the server."""
            self._server_version = version

        @requires_version("0.2.0", VERSION_MAP)
        def old_method(self):
            pass

        @requires_version("0.5.1", VERSION_MAP)
        def new_method(self):
            pass


Suppose that two servers are created using previous class. Each of the servers
is using a different version, meaning that some of the methods are available
while some others are not:

.. code-block:: pycon

    >>> old_server = Server("0.4.5")  # Can use "old_method" but not "new_method"
    >>> new_server = Server("0.5.5")  # Can use "old_method" and "new_method"

Executing each one of the methods it is possible to see that both instances can
execute the ``old_method`` function:

.. code-block:: pycon

    >>> for server in [old_server, new_server]:
    ...     server.old_method()
    ...

However, when trying to run ``new_method``, the old server raises a
``VersionError`` exception, indicating that a higher server version is required:

.. code-block:: pycon

    >>> new_server.new_method()
    >>> old_server.new_method()
    ansys.tools.versioning.exceptions.VersionError: Class method ``new_method`` requires server version >= 2022R1.
