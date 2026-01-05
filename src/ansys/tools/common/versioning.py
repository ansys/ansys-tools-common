# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""A module containing various utilities."""

from typing import Iterable, Optional, Union

from ansys.tools.common.exceptions import VersionError, VersionSyntaxError


def sanitize_version_string(version_string):
    """Sanitize a version string number by adding additional zeros.

    Parameters
    ----------
    version_string : str
        A string representing a semantic version.

    Returns
    -------
    str
        A string representing a semantic version.

    Examples
    --------
    >>> sanitize_version_string("0")
    '0.0.0'
    >>> sanitize_version_string("1.2")
    '1.2.0'
    >>> sanitize_version_string("0.3.4")
    '0.3.4'

    """
    version_list = version_string.split(".")
    while len(version_list) < 3:
        version_list.append("0")
    return ".".join(version_list)


def sanitize_version_tuple(version_tuple):
    """Sanitize a version number by adding additional zeros.

    Parameters
    ----------
    version_tuple : tuple
        A tuple representing a semantic version.

    Returns
    -------
    tuple
        A tuple representing a semantic version.

    Examples
    --------
    >>> sanitize_version_tuple((0,))
    (0, 0, 0)
    >>> sanitize_version_tuple((1, 2))
    (1, 2, 0)
    >>> sanitize_version_tuple((0, 3, 4))
    (0, 3, 4)

    """
    version_list = list(version_tuple)
    version_list = [VersionNumber(num) for num in version_list]
    while len(version_list) < 3:
        version_list.append(VersionNumber(0))
    return tuple(version_list)


def version_string_as_tuple(version_string):
    """Convert a semantic version string into a tuple.

    Parameters
    ----------
    version_string : str
        A string representing a semantic version.

    Returns
    -------
    version_tuple : tuple
        A tuple representing a semantic version.

    Examples
    --------
    >>> version_string_as_tuple("0.3.4")
    (0, 3, 4)
    >>> version_string_as_tuple("1.2")
    (1, 2, 0)


    """
    try:
        # Check version string numbers are numeric by converting to integers
        version_tuple = tuple(map(VersionNumber, version_string.split(".")))

    except ValueError:
        raise VersionSyntaxError(
            "Version string can only contain positive integers following <MAJOR>.<MINOR>.<PATCH> versioning."
        )

    return SemanticVersion(sanitize_version_tuple(version_tuple))


def version_tuple_as_string(version_tuple):
    """Convert a semantic version tuple into a string.

    Parameters
    ----------
    version_tuple : tuple
        A tuple representing a semantic version.

    Returns
    -------
    str
        A string representing a semantic version.

    Examples
    --------
    >>> version_tuple_as_string((0, 3, 4))
    '0.3.4'
    >>> version_tuple_as_string((1, 2))
    '1.2.0'

    """
    try:
        # Check version numbers are positive integers
        if not all(
            (isinstance(num, int) and num >= 0) or (isinstance(num, str) and "dev" in num and len(num) <= 6)
            for num in version_tuple
        ):
            raise ValueError

    except ValueError:
        raise VersionSyntaxError(
            "Version string can only contain positive integers following <MAJOR>.<MINOR>.<PATCH> versioning "
            "or a string containing 'dev' and a number of characters less than 6."
        )

    version_string = ".".join(tuple(map(str, version_tuple)))
    return sanitize_version_string(version_string)


def server_meets_version(server_version, required_version):
    """Check if server meets the required version.

    Parameters
    ----------
    server_version : str, tuple, obj
        A string or tuple representing the server version.
        If it is an object different from the previous ones, it must have a '_server_version' attribute.

    required_version : str, tuple
        A string or tuple representing the version to be meet.

    Returns
    -------
    bool
        ``True`` if server version meets required version, ``False`` if not.

    Raises
    ------
    ValueError
        If the 'server_version' object does not have '_server_version' attribute.

    Examples
    --------
    >>> server_version, required_version = "1.2.0", "1.3.0"
    >>> server_meets_version(server_version, required_version)
    False
    >>> server_version, required_version = (1, 2, 0), (1, 3, 0)
    >>> server_meets_version(server_version, required_version)
    False
    >>> server_version, required_version = "2.3.0", "1.3.0"
    >>> server_meets_version(server_version, required_version)
    True
    >>> server_version, required_version = (2, 3, 0), (1, 3, 0)
    >>> server_meets_version(server_version, required_version)
    True
    >>> server_version, required_version = (0, 0, 0), (0, 0, 0)
    >>> server_meets_version(server_version, required_version)
    True
    >>> class MyServer:
            def __init__(self):
                self._server_version = "1.2.0"
    >>> server = MyServer()
    >>> server_version, required_version = server, "1.3.0"
    >>> server_meets_version(server, required_version)

    """
    # If the 'server_version' object is not a string, let's check for
    # '_server_version' attribute
    if not isinstance(server_version, (str, tuple)):
        if hasattr(server_version, "_server_version"):
            server_version = server_version._server_version
        else:
            raise ValueError("The 'server_version' object must be a string or have a '_server_version' attribute.")

    # Sanitize server and required version inputs
    server_version, required_version = [
        (version_string_as_tuple(version) if isinstance(version, str) else sanitize_version_tuple(version))
        for version in [server_version, required_version]
    ]

    for ith_num, (server_version_number, required_version_number) in enumerate(
        zip(server_version, required_version), start=1
    ):
        # Keep comparing if both numbers are the same
        if server_version_number == required_version_number and ith_num != 3:
            continue

        # If all numbers are the same, server and required version are exactly
        # the same
        elif server_version_number == required_version_number and ith_num == 3:
            return True

        # If a server version number is higher, the iteration stops
        elif server_version_number > required_version_number:
            return True

        # If a version number is lower, stop the iteration
        elif server_version_number < required_version_number:
            return False


def requires_version(version, version_map=None):
    """Ensure the method called matches a certain version.

    Parameters
    ----------
    version : str, tuple
        A string or tuple representing the minimum required version.
    version_map : dict, optional
        A dictionary relating server version and ANSYS unified install version.

    Raises
    ------
    AttributeError
        Decorated class method requires ``_server_version`` attribute.
    VersionError
        Decorated class method is not supported by server version.

    """

    def decorator(func):
        # Sanitize input version
        min_version = (
            sanitize_version_tuple(version) if isinstance(version, tuple) else version_string_as_tuple(version)
        )

        def wrapper(self, *args, **kwargs):
            """Call the original function."""
            # Check that the object has a '_server_version' attribute
            if not hasattr(self, "_server_version"):
                raise AttributeError("Decorated class method must have ``_server_version`` attribute.")

            # Raise exceptions if server version is not valid
            if not server_meets_version(self._server_version, min_version):
                # Provide a generic version error message
                if not version_map:
                    raise VersionError(
                        f"Class method ``{func.__name__}`` requires "
                        + f"server version >= {version_tuple_as_string(min_version)}."
                    )

                # Provide a better error message if version_map is provided
                raise VersionError(
                    f"Class method ``{func.__name__}`` requires" + f" server version >= {version_map[min_version]}."
                )

            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class VersionMeta:
    """Provides a metaclass for version comparison.

    Implements modifications to magic methods.
    """

    def __le__(self, __x: Union[str, int]) -> bool:
        """Less equal.

        If compared against a string that contains ``dev``, it always evaluates to ``True``.
        If compared against an integer, it performs a classic 'less equal' operation.
        """
        if isinstance(__x, str):
            if "dev" in __x and isinstance(self, str) and "dev" in self:
                raise ValueError("Two 'dev' versions cannot be compared against.")
            elif "dev" in __x:
                return True
            else:
                raise VersionSyntaxError("Invalid version string")
        else:
            return super().__le__(__x)

    def __lt__(self, __x: Union[str, int]) -> bool:
        """Less than.

        If compared against a string which contains ``dev``, it always evaluates to ``True``.
        If compared against an integer, it performs a classic 'less than' operation.
        """
        if isinstance(__x, str):
            if "dev" in __x and isinstance(self, str) and "dev" in self:
                raise ValueError("Two 'dev' versions cannot be compared against.")
            elif "dev" in __x:
                return True
            else:
                raise VersionSyntaxError("Invalid version string")
        else:
            return super().__lt__(__x)

    def __ge__(self, __x: Union[str, int]) -> bool:
        """Greater equal.

        If compared against a string that contains ``dev``, it always evaluates to ``False``.
        If compared against an integer, it performs a classic 'greater equal' operation.
        """
        if isinstance(__x, str):
            if "dev" in __x and isinstance(self, str) and "dev" in self:
                raise ValueError("Two 'dev' versions cannot be compared against.")
            elif "dev" in __x:
                return False
            else:
                raise VersionSyntaxError("Invalid version string")
        else:
            return super().__ge__(__x)

    def __gt__(self, __x: Union[str, int]) -> bool:
        """Greater than.

        If compared against a string that contains ``dev``, it always evaluates to ``False``.
        If compared against an integer, it performs a classic 'greater than' operation.
        """
        if isinstance(__x, str):
            if "dev" in __x and isinstance(self, str) and "dev" in self:
                raise ValueError("Two 'dev' versions cannot be compared against.")
            elif "dev" in __x:
                return False
            else:
                raise VersionSyntaxError("Version string is invalid.")
        else:
            return super().__gt__(__x)

    def __eq__(self, __x: object) -> bool:
        """Equal method.

        If compared against a string that contains ''dev``, it always evaluates to ``False``.
        If compared against an integer, it performs a classic 'equal' operation.
        """
        if isinstance(self, str) and isinstance(__x, str) and "dev" in self and "dev" in __x:
            return str(self) == str(__x)

        elif isinstance(__x, str):
            return False
        else:
            return super().__eq__(__x)

    def __ne__(self, __x: object) -> bool:
        """Not equal.

        If compared against a string that contains ``dev``, it always evaluates to not
        'equal' operation (``True``). If compared against an integer, it performs a classic 'not equal' operation.
        """
        if isinstance(__x, str):
            return not self.__eq__(__x)
        else:
            return super().__ne__(__x)

    def __hash__(self) -> int:
        """Call the underlying __hash__ method."""
        return super().__hash__()


class SemanticVersion(tuple):
    """
    Provides a class for semantic versioning.

    It is a subclass of a tuple and can be instantiated from a string or a tuple.

    You can use ``dev`` in the patch version, but nowhere else.

    """

    def __new__(
        cls: type,
        __iterable: Optional[Iterable] = None,
        major: Optional[Union[int, str]] = None,
        minor: Optional[Union[int, str]] = None,
        patch: Optional[Union[int, str]] = None,
    ):
        """Provide a construct class.

        Parameters
        ----------
        cls : type
            Class type.
        __iterable : Iterable[str, int], default: None
            Iterable with major, minor. and patch numbers as a string or integer.
        major : VersionNumber, default: None
            Major version digit.
        minor : VersionNumber, default: None
            Minor version digit.
        patch : VersionNumber, default: Noneptional
            Patch version digit.

        Returns
        -------
        Myint, Mystr
            Depending on the input, the output is a ``Myint`` or ``Mystr`` class.

        """
        if __iterable is None:
            if major and minor and patch:
                __iterable = (major, minor, patch)
            else:
                raise VersionSyntaxError("Semantic version must have three components: (major, minor, patch).")

        if isinstance(__iterable, str):
            __iterable = __iterable.split(".")

            if not all(valid_version_string(each) for each in __iterable):
                raise VersionSyntaxError(
                    "Semantic version does not allow characters" + "other than numbers, 'dev', and dots."
                )

        if len(__iterable) != 3:
            raise VersionSyntaxError("Semantic version must have three components: (major, minor, patch).")

        if not valid_semantic_version(__iterable):
            raise VersionSyntaxError(
                "Semantic version format is incorrect. Only integers are allowed. For a"
                + " patch, also a string containing 'dev' is allowed."
            )

        __iterable = tuple(VersionNumber(i) for i in __iterable)
        return super().__new__(cls, __iterable)

    @property
    def major(self):
        """Major version number."""
        return self[0]

    @property
    def minor(self):
        """Minor version number."""
        return self[1]

    @property
    def patch(self):
        """Patch version number."""
        return self[2]

    def as_string(self):
        """Version as string."""
        return ".".join(str(i) for i in self)

    def as_tuple(self):
        """Version as tuple."""
        return tuple(self)

    def as_list(self):
        """Version as list."""
        return list(self)

    def as_dict(self):
        """Version as dictionary."""
        return {"major": self.major, "minor": self.minor, "patch": self.patch}


class Mystr(VersionMeta, str):
    """Provides the custom class to hold strings for versioning."""

    pass


class Myint(VersionMeta, int):
    """Provides the custom class to hold integers for versioning."""

    pass


class VersionNumber:
    """Provides the class for version comparison.

    This class can be instantiated from a string or an integer.
    The constructor chooses the corresponding class.

    Any combination of ``dev`` and integers are considered as a string.
    ``dev`` is considered as the highest version number possible.

    Examples
    --------
    >>> from ansys.tools.versioning.utils import VersionNumber
    >>> VersionNumber(1)
    1
    >>> VersionNumber("dev")
    'dev'
    >>> VersionNumber(1) <= VersionNumber("dev")
    True
    >>> VersionNumber(99999) >= VersionNumber("dev")
    False
    >>> VersionNumber("dev") == VersionNumber("dev1")
    False
    >>> VersionNumber("dev") != VersionNumber("dev1")
    True
    """

    def __new__(cls, value: Union[str, int]) -> Union[Mystr, Myint]:
        """Create and return a new object.

        Parameters
        ----------
        value : str or int
            Version value to store.

        Returns
        -------
        Mystr, Myint
           Subclass of a string or integer depending on the value.
        """
        if isinstance(value, str):
            if value.strip().isdigit():
                return Myint(int(value.strip()))
            else:
                if valid_version_string(value):
                    return Mystr(value)
                else:
                    raise ValueError(
                        "This version is not allowed. Only 'dev' is allowed with any combination of numbers."
                    )
        elif isinstance(value, int):
            return Myint(value)


def valid_version_string(version):
    """Check if the version string is valid."""
    if isinstance(version, str) and _valid_version_string(version):
        return True
    elif isinstance(version, int):
        return True
    else:
        return False


def _valid_version_string(version):
    version = version.lower()

    first_test = version.replace("dev", "").replace(".", "").isdigit() or version == "dev"
    second_test = version.startswith("dev") if "dev" in version else True

    if first_test and second_test:
        return True
    else:
        return False


def valid_semantic_version(iterable):
    """Check if a semantic version is valid."""
    valid_major_minor = all(
        isinstance(each, int) or (isinstance(each, str) and each.isdigit()) for each in iterable[:2]
    )
    valid_patch = valid_version_string(iterable[2])

    if valid_major_minor and valid_patch:
        return True
    else:
        return False
