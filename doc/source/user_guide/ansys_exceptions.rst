.. _ref_ansys_exceptions:

Ansys exceptions
================

Use the Ansys exceptions tool to gracefully catch and handle exceptions that might occur when using Ansys tools, thereby providing a better user experience.

After importing this tool, use the base :class:`AnsysError <ansys.tools.common.exceptions.AnsysError>` class to catch and handle exceptions related to Ansys tools, extending with your exceptions or using them directly in your programs:

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
