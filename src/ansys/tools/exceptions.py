class AnsysError(Exception):
    """Base class for all exceptions raised by the Ansys API.

    Can be used to catch all Ansys-related exceptions."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AnsysTypeException(AnsysError):
    """Exception raised when python wise types would work, but internal
    Ansys specific typing is not right.

    Parameters
    ----------
    expected_type : str
        The expected type of the argument.
    actual_type : str
        The actual type of the argument.
    """

    def __init__(self, expected_type: str = None, actual_type: str = None) -> None:
        """Initialize the exception with expected and actual types."""
        if expected_type is not None and actual_type is not None:
            message = f"Expected type {expected_type}, but got {actual_type}."
        else:
            message = "Ansys type used is not compatible."
        super().__init__(message)
        self.expected_type = expected_type
        self.actual_type = actual_type

class AnsysLogicError(AnsysError):
    """Exception raised when an unexpected logical condition occurs.

    Parameters
    ----------
    message : str
        The error message.
    """

    def __init__(self, message: str) -> None:
        """Initialize the exception with a message."""
        super().__init__(message)
        self.message = message
