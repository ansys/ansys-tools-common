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

"""Default logger formatter module."""

import logging
from typing import Final


class PyAnsysBaseFormatter(logging.Formatter):
    """Provides a custom formatter to truncate long columns."""

    def set_column_width(self, width: int = 15):
        """Set the maximum column width for module and function names."""
        # at least 8
        if width < 8:
            raise ValueError("Column width must be at least 8 characters.")
        self._max_column_width = width

    @property
    def max_column_width(self):
        """Get the maximum column length."""
        if not hasattr(self, "_max_column_width"):
            self._max_column_width = 15
        return self._max_column_width


DEFAULT_FORMATTER: Final = PyAnsysBaseFormatter(
    "%(asctime)s [%(levelname)-8s | %(module)s | %(funcName)s:%(lineno)-4d] > %(message)s"
)
"""Default formatter for the logger."""

DEFAULT_HEADER = (
    "-" * (70 + DEFAULT_FORMATTER.max_column_width)
    + "\n"
    + f"Timestamp               [Level    | Module{' ' * (DEFAULT_FORMATTER.max_column_width - 6)} | Function{' ' * (DEFAULT_FORMATTER.max_column_width - 8)}:Line] > Message\n"  # noqa: E501
    + "-" * (70 + DEFAULT_FORMATTER.max_column_width)
    + "\n"
)
"""Default header for the log file."""
