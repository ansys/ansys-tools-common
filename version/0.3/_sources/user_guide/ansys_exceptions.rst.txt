.. _ref_ansys_exceptions:

Ansys exceptions
================

Ansys exceptions are a set of predefined error-handling classes designed to help developers identify, catch, and handle errors that might occur when using Ansys tools. These exceptions provide a structured way to manage errors, ensuring that your programs can gracefully recover from unexpected issues and provide meaningful feedback to users.

By using Ansys exceptions, you can improve the robustness and maintainability of your code. They allow you to differentiate between various types of errors, such as invalid input types or logical inconsistencies, and handle them appropriately.

You can import exception classes and use the predefined exceptions directly in your programs:

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

You can also extend the base exception class to define your own custom exceptions. This allows you to create error types specific to your needs:

.. code:: python

   class CustomError(AnsysError):
       """A custom exception for specific error handling."""

       pass


   raise CustomError("This is a custom error message.")
