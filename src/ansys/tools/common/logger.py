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

"""Provides the singleton helper class for the logger."""

# logger from https://gist.github.com/huklee/cea20761dd05da7c39120084f52fcc7c
import datetime
import logging
from pathlib import Path

from ansys.tools.common.logger_formatter import DEFAULT_FORMATTER


class SingletonType(type):
    """Provides the singleton helper class for the logger."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Call to redirect new instances to the singleton instance."""
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonType, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Logger(object, metaclass=SingletonType):
    """Provides the singleton logger.

    Parameters
    ----------
    level : int, default: ``logging.ERROR``
        Output level of the logger.
    logger_name : str, default: ``"Logger"``
        Name of the logger.
    column_width : int, default: ``15``
        Maximum width of the module and function names in the log output.

    """

    _logger = None

    def __init__(self, level: int = logging.ERROR, logger_name: str = "Logger", column_width: int = 15):
        """Initialize the logger."""
        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(level)
        self._formatter = DEFAULT_FORMATTER
        self._formatter.set_column_width(column_width)

    def get_logger(self):
        """Get the logger.

        Returns
        -------
        Logger
            Logger.

        """
        return self._logger

    def set_level(self, level: int):
        """Set the logger output level.

        Parameters
        ----------
        level : int
            Output level of the logger.

        """
        self._logger.setLevel(level=level)

    def enable_output(self, stream=None):
        """Enable logger output to a given stream.

        If a stream is not specified, ``sys.stderr`` is used.

        Parameters
        ----------
        stream: TextIO, default: ``None``
            Stream to output the log output to.

        """
        # stdout
        stream_handler = logging.StreamHandler(stream)
        stream_handler.setFormatter(self._formatter)
        self._logger.addHandler(stream_handler)

    def add_file_handler(self, logs_dir: str | Path = ".log"):
        """Save logs to a file in addition to printing them to the standard output.

        Parameters
        ----------
        logs_dir : str or Path, default: ``".log"``
            Directory to save the log file to. If it does not exist, it is created.
        """
        now = datetime.datetime.now()
        logs_dir = Path(logs_dir) if isinstance(logs_dir, str) else logs_dir
        if not logs_dir.is_dir():
            logs_dir.mkdir(parents=True)
        file_handler = logging.FileHandler(logs_dir / f"log_{now.strftime('%Y%m%d_%H%M%S')}.log")
        file_handler.setFormatter(self._formatter)
        self._logger.addHandler(file_handler)

        header = (
            "-" * (70 + self._formatter.max_column_width)
            + "\n"
            + f"Timestamp               [Level    | Module{' ' * (self._formatter.max_column_width - 6)} | Function{' ' * (self._formatter.max_column_width - 8)}:Line] > Message\n"  # noqa: E501
            + "-" * (70 + self._formatter.max_column_width)
            + "\n"
        )

        # Log the header to the file
        file_handler.stream.write(header)

    def debug(self, *args, **kwargs):
        """Log a message with level DEBUG."""
        return self._logger.debug(*args, **kwargs, stacklevel=2)

    def info(self, *args, **kwargs):
        """Log a message with level INFO."""
        return self._logger.info(*args, **kwargs, stacklevel=2)

    def warning(self, *args, **kwargs):
        """Log a message with level WARNING."""
        return self._logger.warning(*args, **kwargs, stacklevel=2)

    def warn(self, *args, **kwargs):
        """Log a message with level WARNING."""
        return self._logger.warning(*args, **kwargs, stacklevel=2)

    def error(self, *args, **kwargs):
        """Log a message with level ERROR."""
        return self._logger.error(*args, **kwargs, stacklevel=2)

    def critical(self, *args, **kwargs):
        """Log a message with level CRITICAL."""
        return self._logger.critical(*args, **kwargs, stacklevel=2)

    def fatal(self, *args, **kwargs):
        """Log a message with level FATAL."""
        return self._logger.fatal(*args, **kwargs, stacklevel=2)

    def log(self, level, msg, *args, **kwargs):
        """Log a message with a specified level."""
        return self._logger.log(level, msg, *args, **kwargs, stacklevel=2)


LOGGER = Logger()
"""Global logger instance.

This is a global instance of the ``Logger`` class that can be used throughout the application.
It is initialized with default settings and can be configured as needed.
"""
