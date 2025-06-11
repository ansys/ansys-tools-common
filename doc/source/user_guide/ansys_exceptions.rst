.. ref_ansys_exceptions:

=======================================================
``ansys-exceptions``: A tool to handle Ansys exceptions
=======================================================

The Ansys exceptions tool provides a way to handle exceptions that may occur when using Ansys tools.
It allows you to catch specific exceptions and handle them gracefully, providing a better user experience.

How to use
----------

You can use the `AnsysException` class to catch exceptions related to Ansys tools.

For example, you can use it to extend your exceptions or use them directly on your programs:

.. code:: pycon

   >>> from ansys.tools.exceptions import AnsysError
   >>> from ansys.tools.exceptions import AnsysTypeError
   >>> from ansys.tools.exceptions import AnsysLogicError
   >>> raise AnsysError("An error occurred in Ansys tools.")
    AnsysError: An error occurred in Ansys tools.
   >>> raise AnsysTypeError("An invalid type was provided.")
   AnsysTypeError: An invalid type was provided.
   >>> raise AnsysLogicError("A logic error occurred in Ansys tools.")
   AnsysLogicError: A logic error occurred in Ansys tools.
