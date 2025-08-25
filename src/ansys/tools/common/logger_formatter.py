"""Default logger formatter module."""
import logging


class CustomFormatter(logging.Formatter):
    """Custom formatter to truncate long columns."""

    def set_column_width(self, width: int):
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

    def format(self, record):
        """Format the log record, truncating the module and function names if necessary."""
        if len(record.module) > self.max_column_width:
            record.module = record.module[: self.max_column_width - 3] + "..."
        if len(record.funcName) > self.max_column_width:
            record.funcName = record.funcName[: self.max_column_width - 3] + "..."

        # Fill the module and function names with spaces to align them
        record.module = record.module.ljust(self.max_column_width)
        record.funcName = record.funcName.ljust(self.max_column_width)

        return super().format(record)


DEFAULT_FORMATTER = CustomFormatter(
    "%(asctime)s [%(levelname)-8s | %(module)s | %(funcName)s:%(lineno)-4d] > %(message)s"
)
DEFAULT_FORMATTER.set_column_width(15)
"""Default formatter for the logger."""

DEFAULT_HEADER = (
    "-" * (70 + DEFAULT_FORMATTER.max_column_width)
    + "\n"
    + f"Timestamp               [Level    | Module{' ' * (DEFAULT_FORMATTER.max_column_width - 6)} | Function{' ' * (DEFAULT_FORMATTER.max_column_width - 8)}:Line] > Message\n"  # noqa: E501
    + "-" * (70 + DEFAULT_FORMATTER.max_column_width)
    + "\n"
)
"""Default header for the log file."""