.. ref_versioning:

Ansys versioning tool
=====================

Use the Ansys versioning tool to enforce version requirements for methods in classes. The :meth:`requires_version <ansys.tools.versioning.requires_version>` decorator specifies the required version and version map. This decorator accepts the following:

* The required version as a string (``"<Major>.<Minor>.<Patch>"``) or
  a tuple (``(<Major>, <Minor>, <Patch>)``)
* A version map in the form of dictionary relating the required version to
  its Ansys unified install, such as ``VERSION_MAP = {(<Major>, <Minor>, <Patch>): "2022R1"}``

The ``requires_version`` decorator is expected to be used in all the desired
methods of a class containing a ``_server_version`` attribute. If the class in which the decorator is used does not contain this attribute, an ``AttributeError`` is raised.

The following example declares a generic ``Server`` class and a ``VERSION_MAP`` dictionary:

.. code-block:: python

    VERSION_MAP = {
        (0, 2, 3): "2021R1",
        (0, 4, 5): "2021R2",
        (0, 5, 1): "2022R1",
    }


    class Server:
        """A basic class for modeling a server."""

        def __init__(self, version):
            """Initializes the server."""
            self._server_version = version

        @requires_version("0.2.0", VERSION_MAP)
        def old_method(self):
            pass

        @requires_version("0.5.1", VERSION_MAP)
        def new_method(self):
            pass

Suppose you create two servers using the previous class. Each server uses a different version, meaning that some methods are available while others are not:

.. code-block:: pycon

    >>> old_server = Server("0.4.5")  # Can use "old_method" but not "new_method"
    >>> new_server = Server("0.5.5")  # Can use "old_method" and "new_method"

If you execute each of the methods, both instances execute ``old_method`` without any issues:

.. code-block:: pycon

    >>> for server in [old_server, new_server]:
    ...     server.old_method()
    ...

However, when you run ``new_method``, the old server raises a
``VersionError`` exception, indicating that it requires a higher server version:

.. code-block:: pycon

    >>> new_server.new_method()
    >>> old_server.new_method()
    ansys.tools.versioning.exceptions.VersionError: Class method ``new_method`` requires server version >= 2022R1.
